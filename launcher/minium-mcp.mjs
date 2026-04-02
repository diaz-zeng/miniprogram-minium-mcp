#!/usr/bin/env node

import { spawn, spawnSync } from "node:child_process";
import { createWriteStream, existsSync, mkdirSync } from "node:fs";
import { chmod, copyFile, mkdtemp, readdir, rm } from "node:fs/promises";
import https from "node:https";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const packageRoot = path.resolve(__dirname, "..");

const PYTHON_REQUEST = process.env.MINIUM_MCP_PYTHON_VERSION || "3.11";
const UV_VERSION = (process.env.MINIUM_MCP_UV_VERSION || "").trim();

async function main() {
  const cacheBase = getCacheBaseDir();
  const uvInstallDir = path.join(cacheBase, "uv-bin");
  const uvDataDir = path.join(cacheBase, "uv-data");
  const uvCacheDir = path.join(cacheBase, "uv-cache");
  const uvProjectEnv = path.join(cacheBase, "project-venv");
  const uvPythonInstallDir = path.join(uvDataDir, "python");

  mkdirSync(cacheBase, { recursive: true });
  mkdirSync(uvInstallDir, { recursive: true });
  mkdirSync(uvDataDir, { recursive: true });
  mkdirSync(uvCacheDir, { recursive: true });

  const uvBin = await ensureUv(uvInstallDir);
  const env = {
    ...process.env,
    UV_CACHE_DIR: uvCacheDir,
    UV_PYTHON_INSTALL_DIR: uvPythonInstallDir,
    UV_PROJECT_ENVIRONMENT: uvProjectEnv,
    UV_SYSTEM_CERTS: process.env.UV_SYSTEM_CERTS || "1",
  };

  const uvArgs = [
    "run",
    "--project",
    packageRoot,
    "--managed-python",
    "--python",
    PYTHON_REQUEST,
    "python",
    "-m",
    "minium_mcp",
    ...process.argv.slice(2),
  ];

  const child = spawn(uvBin, uvArgs, {
    cwd: packageRoot,
    env,
    stdio: "inherit",
  });

  child.on("exit", (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
      return;
    }
    process.exit(code ?? 1);
  });

  child.on("error", (error) => {
    writeStderr(`启动 Python MCP 服务失败：${error.message}`);
    process.exit(1);
  });
}

function getCacheBaseDir() {
  const explicitDir = process.env.MINIUM_MCP_CACHE_DIR;
  if (explicitDir) {
    return path.resolve(explicitDir);
  }

  if (process.platform === "win32") {
    return path.join(
      process.env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local"),
      "minium-mcp"
    );
  }

  const xdgCacheHome = process.env.XDG_CACHE_HOME;
  if (xdgCacheHome) {
    return path.join(xdgCacheHome, "minium-mcp");
  }

  return path.join(os.homedir(), ".cache", "minium-mcp");
}

async function ensureUv(uvInstallDir) {
  if (process.env.MINIUM_MCP_USE_SYSTEM_UV === "1") {
    const systemUv = findSystemUv();
    if (systemUv) {
      return systemUv;
    }
  }

  const uvBin = path.join(uvInstallDir, process.platform === "win32" ? "uv.exe" : "uv");
  if (existsSync(uvBin)) {
    return uvBin;
  }

  writeStderr("正在准备托管 uv 运行环境...");
  await installManagedUvBinary(uvInstallDir);

  if (!existsSync(uvBin)) {
    throw new Error("uv 安装完成后未找到可执行文件");
  }
  return uvBin;
}

function findSystemUv() {
  const candidate = process.platform === "win32" ? "uv.exe" : "uv";
  const result = spawnSync(candidate, ["--version"], {
    stdio: "ignore",
  });
  if (result.status === 0) {
    return candidate;
  }
  return null;
}

async function installManagedUvBinary(uvInstallDir) {
  const tempDir = await mkdtemp(path.join(os.tmpdir(), "minium-mcp-uv-"));
  const { archiveExt, triple } = getUvTarget();
  const archivePath = path.join(tempDir, `uv.${archiveExt}`);
  const extractDir = path.join(tempDir, "extract");
  const installUrl = buildUvDownloadUrl(triple, archiveExt);

  try {
    mkdirSync(extractDir, { recursive: true });
    await downloadFile(installUrl, archivePath);
    await extractUvArchive(archivePath, extractDir, archiveExt);
    const extractedRoot = path.join(extractDir, `uv-${triple}`);
    const uvSource = path.join(
      extractedRoot,
      process.platform === "win32" ? "uv.exe" : "uv"
    );
    const uvxSource = path.join(
      extractedRoot,
      process.platform === "win32" ? "uvx.exe" : "uvx"
    );

    await copyFile(uvSource, path.join(uvInstallDir, process.platform === "win32" ? "uv.exe" : "uv"));
    if (existsSync(uvxSource)) {
      await copyFile(
        uvxSource,
        path.join(uvInstallDir, process.platform === "win32" ? "uvx.exe" : "uvx")
      );
    }

    if (process.platform !== "win32") {
      await chmod(path.join(uvInstallDir, "uv"), 0o755);
      if (existsSync(path.join(uvInstallDir, "uvx"))) {
        await chmod(path.join(uvInstallDir, "uvx"), 0o755);
      }
    }
  } finally {
    await rm(tempDir, { recursive: true, force: true });
  }
}

function getUvTarget() {
  if (process.platform === "darwin" && process.arch === "arm64") {
    return { triple: "aarch64-apple-darwin", archiveExt: "tar.gz" };
  }
  if (process.platform === "darwin" && process.arch === "x64") {
    return { triple: "x86_64-apple-darwin", archiveExt: "tar.gz" };
  }
  if (process.platform === "linux" && process.arch === "arm64") {
    return { triple: "aarch64-unknown-linux-gnu", archiveExt: "tar.gz" };
  }
  if (process.platform === "linux" && process.arch === "x64") {
    return { triple: "x86_64-unknown-linux-gnu", archiveExt: "tar.gz" };
  }
  if (process.platform === "win32" && process.arch === "arm64") {
    return { triple: "aarch64-pc-windows-msvc", archiveExt: "zip" };
  }
  if (process.platform === "win32" && process.arch === "x64") {
    return { triple: "x86_64-pc-windows-msvc", archiveExt: "zip" };
  }

  throw new Error(`当前平台暂未支持自动托管 uv：${process.platform}/${process.arch}`);
}

function buildUvDownloadUrl(triple, archiveExt) {
  const fileName = `uv-${triple}.${archiveExt}`;
  if (UV_VERSION) {
    return `https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/${fileName}`;
  }
  return `https://github.com/astral-sh/uv/releases/latest/download/${fileName}`;
}

async function extractUvArchive(archivePath, extractDir, archiveExt) {
  if (archiveExt === "tar.gz") {
    runChecked("tar", ["-xzf", archivePath, "-C", extractDir]);
    return;
  }

  if (archiveExt === "zip") {
    runChecked("powershell", [
      "-ExecutionPolicy",
      "Bypass",
      "-Command",
      `Expand-Archive -Path '${archivePath}' -DestinationPath '${extractDir}' -Force`,
    ]);
    return;
  }

  throw new Error(`不支持的 uv 压缩格式：${archiveExt}`);
}

function runChecked(command, args, options = {}) {
  const result = spawnSync(command, args, {
    stdio: ["ignore", "inherit", "inherit"],
    ...options,
  });

  if (result.status !== 0) {
    throw new Error(`${command} 执行失败，退出码为 ${result.status ?? "unknown"}`);
  }
}

async function downloadFile(url, targetPath) {
  await new Promise((resolve, reject) => {
    const request = https.get(url, (response) => {
      if (
        response.statusCode &&
        response.statusCode >= 300 &&
        response.statusCode < 400 &&
        response.headers.location
      ) {
        response.resume();
        downloadFile(response.headers.location, targetPath).then(resolve).catch(reject);
        return;
      }

      if (response.statusCode !== 200) {
        reject(new Error(`下载失败：${url} -> HTTP ${response.statusCode}`));
        return;
      }

      const file = createWriteStream(targetPath);
      response.pipe(file);
      file.on("finish", () => {
        file.close(resolve);
      });
      file.on("error", reject);
    });

    request.on("error", reject);
  });
}

function writeStderr(message) {
  process.stderr.write(`[minium-mcp] ${message}\n`);
}

main().catch((error) => {
  writeStderr(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
