# AGENTS 指南

本文件面向在当前仓库内协作的 Agent，目标是减少无效探索、保持分层边界清晰，并让提交、测试、文档和发包行为保持一致。

## 语言与提交约定

- 所有分析、解释、交接说明、验收结论和补充文档默认使用中文。
- 优先使用中文术语、表达方式和命名说明；框架、协议、库名等社区通用英文术语可保留原文。
- 代码注释、设计说明、任务拆解说明和补充文档默认使用中文。
- Git 提交信息必须符合 Conventional Commits 规范，并使用中文描述变更内容。
- 推荐格式：
  - `feat: 增加多触点手势支持`
  - `fix: 修复真实运行时输入回退`
  - `docs: 重写 README 使用说明`

## 项目定位

`miniprogram-minium-mcp` 是一个面向 AI Agent 的微信小程序验收型 MCP Server。

这个仓库有两层交付物：

1. Python MCP 服务本体  
   负责会话、动作、断言、截图、失败取证和 Minium 运行时适配。

2. Node.js 启动壳  
   面向 npm / `npx` 分发，负责托管 Python 环境并启动 Python MCP 服务。

协作时优先把它理解成“验收型能力服务”，不是通用脚本执行器，也不是任意小程序调试代理。

## 技术栈与运行要求

- Python `>=3.11`
- Node.js `>=18`
- 官方 Python MCP SDK
- Minium 作为小程序底层驱动
- 本地 `stdio` 方式暴露 MCP 能力

注意：

- 开发和测试优先使用仓库自己的 `.venv`
- 不要为了兼容本机旧 Python 版本去降低仓库正式要求
- 如果本地环境与仓库要求不一致，优先切换到 `.venv` 而不是增加临时兼容层

## 目录边界

- `src/minium_mcp/server/`
  MCP Server 启动入口与工具注册
- `src/minium_mcp/domain/`
  会话、动作、断言、错误模型与领域服务
- `src/minium_mcp/adapters/minium/`
  Minium 适配层，负责把高层语义翻译成底层运行时调用
- `src/minium_mcp/support/`
  配置、日志、产物目录和国际化等横切能力
- `launcher/`
  npm 启动壳
- `tests/`
  单元测试与最小集成验证
- `scripts/`
  真实运行时验证脚本或辅助开发脚本
- `openspec/`
  需求、设计、任务和归档变更

协作时请尽量遵守这些边界：

- 不要把底层 Minium 细节直接泄漏到 `server/tools`
- `server/tools` 只负责参数接入和工具注册，不承担复杂业务逻辑
- 会话状态、动作编排和失败取证优先放在 `domain`
- 真实运行时差异优先收敛在 `adapters/minium/runtime.py`

## 推荐开发流程

### 1. 环境准备

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

### 2. 启动服务

```bash
.venv/bin/minium-mcp
```

如果需要显式配置：

```bash
.venv/bin/minium-mcp --config ./minium-mcp.toml --log-level DEBUG
```

### 3. 测试与验证

默认先跑：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_support.py
```

如果变更涉及真实运行时或多触点，补跑：

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_multitouch_real.py ...
```

### 4. 文档同步

涉及以下变更时，应同步检查 README / CHANGELOG / OpenSpec：

- MCP tools 增删改
- 配置项变化
- 运行方式变化
- 真实运行时行为变化
- 版本号变化

## OpenSpec 协作约定

如果工作内容来自 OpenSpec change，优先遵守这条顺序：

1. 先实现并验证 tasks
2. 如有 delta specs，先同步到 `openspec/specs/`
3. 再归档 `openspec/changes/<name>`

归档前至少确认：

- tasks 全部完成
- 主 specs 已同步
- 关键测试已跑
- README / CHANGELOG 已同步到位

## 测试与回归建议

按风险从低到高，推荐回归顺序如下：

1. `.venv` 下的语法校验
2. `tests/test_support.py`
3. 真实运行时最小验证脚本
4. 如涉及业务场景，再补一条页面级业务断言

如果是多触点能力，验收不要只看动作返回成功，最好再补一条业务结果断言，例如：

- 当前录入区域出现有效分值
- 标记数量变化
- 某个状态文本发生变化

## 发布与打包约定

- 版本号需要同时检查：
  - `pyproject.toml`
  - `package.json`
  - `CHANGELOG.md`
- 发布前先执行 `npm pack --dry-run`
- 发包默认使用 npm 官方 registry
- 发布到预发布通道时使用 `npm publish --tag beta`

注意：

- `AGENTS.md` 仅用于本地协作，不应进入 npm 包
- 任何本地调试文件、截图产物、OpenSpec 工作文件都不应误入发包内容
- 发包前建议检查 `.npmignore`

## 常见注意事项

- 不要为了临时本地环境问题，引入会降低正式版本要求的兼容代码
- 不要把 README 写成实现流水账，优先写成“能力说明 + 使用说明”
- 不要在文档里保留本地绝对路径、真实项目私有信息或一次性验证数据
- 不要把未跟踪的本地协作文件带进 npm 包
- 不要在未确认影响面的情况下直接重写已推送历史；如需改写，优先使用 `--force-with-lease`

## 交付前检查

准备提交、发版或归档前，建议至少确认：

- 工作区没有无关文件残留
- 提交信息符合中文 Conventional Commits
- 核心测试已通过
- README、CHANGELOG 和实现一致
- OpenSpec 已同步并归档
- npm dry-run 内容符合预期
