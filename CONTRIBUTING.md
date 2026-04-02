# Contributing

感谢你参与 `miniprogram-minium-mcp` 的开发与维护。

这份文档面向仓库贡献者，整理了当前技术栈、目录职责、本地开发方式、配置来源、已知限制与排查建议，方便后续持续迭代。若你关注 npm 包版本发布记录、升级提示和发包维度的变化，请同时参考仓库根目录下的 `CHANGELOG.md`。

## 当前技术栈

- Node.js 启动壳，面向 `npx` 分发
- Python 3.11+
- 官方 Python MCP SDK
- 本地 `stdio` 传输
- Minium 作为小程序底层驱动

## 目录约定

- `src/minium_mcp/server/`：MCP Server 启动入口与工具注册
- `src/minium_mcp/domain/`：会话、动作、断言、错误模型与领域服务
- `src/minium_mcp/adapters/minium/`：Minium 适配层
- `src/minium_mcp/support/`：配置、日志、产物目录等横切能力
- `artifacts/`：截图、日志和调试产物
- `tests/`：单元测试与最小集成验证

## 开发入口

当前仓库存在两种入口：

1. 最终用户入口：`npx` 启动壳
2. 开发者入口：本地 Python 源码启动

其中 `npx` 启动壳负责托管 `uv`、托管 Python，并最终拉起当前仓库中的 Python MCP 服务。

## 本地开发

建议优先使用虚拟环境：

```bash
python3 -m venv .venv
./.venv/bin/pip install -e ".[dev]"
```

启动服务：

```bash
./.venv/bin/minium-mcp
```

如果需要显式传配置文件或日志级别：

```bash
./.venv/bin/minium-mcp --config ./minium-mcp.toml --log-level DEBUG
```

运行测试：

```bash
./.venv/bin/python -m pytest -q
```

## 配置来源

服务支持两种配置来源：

1. 环境变量
2. 本地配置文件，使用 `--config` 指定，支持 `.json` 或 `.toml`

当前支持的主要配置项：

- `MINIUM_MCP_PROJECT_PATH`：小程序项目路径
- `MINIUM_MCP_WECHAT_DEVTOOL_PATH`：微信开发者工具 CLI 或可执行文件路径
- `MINIUM_MCP_ARTIFACTS_DIR`：截图和调试产物目录
- `MINIUM_MCP_LOG_LEVEL`：日志级别
- `MINIUM_MCP_SESSION_TIMEOUT_SECONDS`：会话超时时间，单位秒
- `MINIUM_MCP_RUNTIME_MODE`：运行模式，支持 `real`、`auto`、`placeholder`
- `MINIUM_MCP_TEST_PORT`：Minium 连接微信开发者工具时使用的测试端口
- `MINIUM_MCP_LANGUAGE`：输出语言，支持显式指定 `zh-CN` 或 `en`

如果没有显式指定 `MINIUM_MCP_LANGUAGE`，服务会根据 `LC_ALL`、`LC_MESSAGES`、`LANG` 等环境变量自动判断语言；中文环境输出中文，非中文环境统一输出英文。

## 常见环境前提

- 本机可用的 Python 版本需要满足 3.11 及以上
- 本机需要存在微信开发者工具
- 本机需要安装 `minium`
- 在 `real` 或 `auto` 模式下，需要确保小程序项目目录下存在 `project.config.json`
- 如果使用附着模式，需要确认微信开发者工具已按 `test_port` 暴露可连接运行态
- 如果在 `create_session` 时直接提供 `project_path`，服务会优先执行一次 `cli auto --project ... --auto-port ...`，再进入 Minium attach

## 当前已知限制

- 当前主链路已经支持真实 Minium 会话接入，但无真实环境时仍建议使用 `placeholder` 模式做本地协议验证
- 当前已经暴露第一批正式会话类、动作类和断言类 MCP tools
- 当前最推荐的入口是 `miniapp_create_session(project_path=\"...\")`，由服务自动完成开发者工具拉起、自动化端口准备和 attach
- 当前已移除多目标选择能力，对外统一收敛为“提供项目路径，由服务自行 auto + attach”
- 当前不会暴露底层 Minium 对象、任意脚本执行或任意运行时改写入口
- `create_session` 的 `metadata` 只允许记录验收上下文，不能覆盖底层运行时控制参数

## 排查建议

- 如果服务无法启动，先确认虚拟环境中的 `mcp` 依赖是否已安装
- 如果真实会话创建失败，先确认虚拟环境中的 `minium` 已安装且版本可用
- 如果配置不生效，优先检查环境变量名或配置文件字段名是否与文档一致
- 如果希望由服务自动拉起开发者工具，优先直接给 `miniapp_create_session` 提供 `project_path`
- 如果真实运行时连接失败，优先检查开发者工具路径、小程序项目路径、`project.config.json` 和 `MINIUM_MCP_TEST_PORT`

## 提交建议

- 优先保持 `server / domain / adapters / support` 的分层边界，不要把底层 Minium 细节直接泄漏到 MCP tool 层
- 新增真实运行时兼容逻辑时，尽量补对应测试，尤其是点击回退、输入回退、失败取证和会话生命周期场景
- 如果修改 README 中对外能力说明，通常也要同步更新这份贡献文档，避免使用说明与开发说明脱节

## 贡献流程

如果你是通过个人 Fork 参与贡献，推荐使用下面这条标准流程。

### 1. Fork 并同步上游

先 Fork 当前仓库到个人账号，再克隆你的 Fork，并添加上游仓库：

```bash
git remote add upstream <上游仓库地址>
git remote -v
```

开始开发前，先同步上游最新 `main`：

```bash
git fetch upstream
git checkout main
git merge --ff-only upstream/main
```

### 2. 创建分支

请基于最新 `main` 创建分支，避免直接在 `main` 上开发：

```bash
git checkout -b feat/<简短主题>
```

常见分支命名建议：

- `feat/<功能主题>`
- `fix/<问题主题>`
- `docs/<文档主题>`
- `refactor/<重构主题>`

### 3. 本地开发与自检

完成修改后，至少执行一次基础测试：

```bash
./.venv/bin/python -m pytest -q
```

如果变更涉及对外能力、配置项或运行方式，建议一并检查：

- `README.md` 是否仍与实现一致
- `CONTRIBUTING.md` 是否需要同步更新
- 如使用 OpenSpec 流程，相关 artifacts 是否已经同步更新

### 4. 提交与推送

请尽量保持 commit 粒度清晰，一个 commit 只表达一个明确意图：

```bash
git add <相关文件>
git commit -m "fix: 修复真实运行时输入回退"
git push origin feat/<简短主题>
```

### 5. 发起 Pull Request

请从个人 Fork 向上游仓库的 `main` 发起 Pull Request。

PR 描述建议包含：

- 修改解决了什么问题
- 核心实现思路是什么
- 是否涉及配置、行为或文档变更
- 本地验证方式和测试结果
- 是否存在已知限制或后续待办

### 6. 同步上游变更

如果开发过程中上游 `main` 有更新，建议在提交 PR 前先同步一次：

```bash
git fetch upstream
git checkout main
git merge --ff-only upstream/main
git checkout feat/<简短主题>
git rebase main
```

如果你不希望改写提交历史，也可以改用 `merge`，但请尽量保持分支历史清晰。

### 7. 处理 Review

收到 review 意见后，建议优先处理会影响正确性、兼容性、稳定性和测试覆盖的问题。修改完成后，请重新执行相关测试，再根据团队约定决定是追加 commit 还是整理历史。

### 8. 合入前检查

在 PR 合入前，建议最后确认：

- 工作区没有无关文件残留
- 文档、测试和实现保持一致
- 临时截图、日志和本地打包产物没有误提交
