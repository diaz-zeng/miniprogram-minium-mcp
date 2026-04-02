"""配置加载。"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tomllib
from typing import Any

from minium_mcp.support.i18n import detect_language, translate


@dataclass(slots=True)
class MiniumMcpConfig:
    """应用配置。"""

    language: str
    runtime_mode: str
    project_path: Path | None
    wechat_devtool_path: Path | None
    artifacts_dir: Path
    log_level: str
    session_timeout_seconds: int
    test_port: int


def load_config(
    config_path: str | None = None,
    log_level_override: str | None = None,
) -> MiniumMcpConfig:
    """从配置文件和环境变量加载配置。"""
    resolved_config_path = config_path or os.environ.get("MINIUM_MCP_CONFIG")
    file_values = _load_file_values(resolved_config_path)

    language = detect_language(
        explicit_language=os.environ.get("MINIUM_MCP_LANGUAGE")
        or str(file_values.get("language", "")).strip()
        or None
    )
    runtime_mode = (
        os.environ.get("MINIUM_MCP_RUNTIME_MODE")
        or str(file_values.get("runtime_mode", "auto"))
    ).strip().lower()

    project_path = _read_path(
        env_key="MINIUM_MCP_PROJECT_PATH",
        file_values=file_values,
        file_key="project_path",
    )
    wechat_devtool_path = _read_path(
        env_key="MINIUM_MCP_WECHAT_DEVTOOL_PATH",
        file_values=file_values,
        file_key="wechat_devtool_path",
    )
    artifacts_dir = _read_path(
        env_key="MINIUM_MCP_ARTIFACTS_DIR",
        file_values=file_values,
        file_key="artifacts_dir",
        default=Path.cwd() / "artifacts",
    )
    log_level = (
        log_level_override
        or os.environ.get("MINIUM_MCP_LOG_LEVEL")
        or str(file_values.get("log_level", "INFO"))
    )
    session_timeout_seconds = int(
        os.environ.get(
            "MINIUM_MCP_SESSION_TIMEOUT_SECONDS",
            file_values.get("session_timeout_seconds", 1800),
        )
    )
    test_port = int(
        os.environ.get(
            "MINIUM_MCP_TEST_PORT",
            file_values.get("test_port", 9420),
        )
    )
    return MiniumMcpConfig(
        language=language,
        runtime_mode=runtime_mode,
        project_path=project_path,
        wechat_devtool_path=wechat_devtool_path,
        artifacts_dir=artifacts_dir,
        log_level=log_level.upper(),
        session_timeout_seconds=session_timeout_seconds,
        test_port=test_port,
    )


def _load_file_values(config_path: str | None) -> dict[str, Any]:
    if not config_path:
        return {}

    path = Path(config_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(
            translate("config.file_not_found", detect_language(), path=path)
        )

    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if suffix in {".toml", ".tml"}:
        return tomllib.loads(path.read_text(encoding="utf-8"))

    raise ValueError(translate("config.unsupported_format", detect_language()))


def _read_path(
    env_key: str,
    file_values: dict[str, Any],
    file_key: str,
    default: Path | None = None,
) -> Path | None:
    raw_value = os.environ.get(env_key, file_values.get(file_key))
    if raw_value in (None, ""):
        return default
    return Path(str(raw_value)).expanduser().resolve()
