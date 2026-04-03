# Changelog

本文件按 npm 包发布维度记录 `miniprogram-minium-mcp` 的版本变更。当前对应的 npm 包名为 `@diaz9810/miniprogram-minium-mcp`，文档重点关注对使用者可感知的能力变化、兼容性、发布入口和升级提示，而不是逐条罗列内部实现细节。

## 记录约定

- 版本遵循语义化版本与 npm 预发布标记，例如 `0.0.1-alpha.1`
- `alpha` 表示能力仍在快速迭代，接口和行为仍可能调整
- 每个版本优先按以下维度整理：
  - `Added`：新增能力
  - `Changed`：行为调整或默认值变化
  - `Fixed`：缺陷修复
  - `Packaging`：发包入口、运行方式、兼容性与分发相关变更
  - `Upgrade Notes`：升级或使用提示

## [0.1.1-beta.0] - 2026-04-03

> 发布通道：`beta`

### Added

- 新增实验性的多触点基础原语：`miniapp_touch_start`、`miniapp_touch_move`、`miniapp_touch_end`、`miniapp_touch_tap`，用于表达“两指以内”的复合交互。
- 新增会话级手势上下文，服务会维护 `active_pointers` 与 `latest_gesture_event`，并在成功或失败返回里携带结构化触点摘要。
- 新增真实运行时多触点验证脚本 `scripts/validate_multitouch_real.py`，用于在目标小程序里验证“第一指按住移动 + 第二指点击”的主链路。

### Changed

- 真实 Minium 运行时下的手势目标解析补充了更稳的交互节点选择逻辑，尽量避免把事件派发到只负责展示文本的内部节点。
- README 与使用说明同步更新，补充多触点工具的使用方式、能力边界和真实运行时验证路径。

### Fixed

- 统一了多触点成功路径、失败路径和会话读取路径中的结构化上下文字段，确保活跃触点状态在服务层与运行时之间保持一致。
- 为 Python 3.9 本地开发环境补充兼容层，使占位测试与真实验证脚本在低版本解释器下也能运行，不影响项目面向 Python 3.11 的正式要求。

### Packaging

- Python 包版本提升到 `0.1.1-beta.0`
- npm 启动壳版本提升到 `0.1.1-beta.0`
- 该版本为 `beta` 预发布，建议优先用于真实项目验证和能力灰度，而不是直接视为稳定通道替代

### Upgrade Notes

- 如果你要验证多触点场景，建议先使用仓库内验证脚本在目标小程序上跑一遍，再将新工具接入更长的 Agent 验收流程。
- 当前多触点能力仍明确收敛在“两指以内”，且文本定位在部分复杂自定义组件下仍可能需要业务页面级验证。

## [0.0.1] - 2026-04-02

> 发布通道：`latest`

### Added

- 发布首个正式版 `0.0.1`，将 `miniprogram-minium-mcp` 从 alpha 预发布阶段推进到稳定安装入口。

### Fixed

- 吸收 `0.0.1-alpha.1` 中已经验证通过的核心修复，包括真实运行时输入回退、会话过期资源释放，以及页面路径断言基于实时运行态页面执行。

### Changed

- 默认安装通道切换为正式版，`npm install @diaz9810/miniprogram-minium-mcp` 或 `npx @diaz9810/miniprogram-minium-mcp` 将优先拿到 `0.0.1`。
- `alpha` 通道继续保留给预发布版本，便于后续实验性迭代与灰度验证。

### Upgrade Notes

- 如果你此前使用的是 `0.0.1-alpha.1`，升级到 `0.0.1` 不需要额外的配置迁移。
- `latest` 应指向 `0.0.1`，`alpha` 应继续指向 `0.0.1-alpha.1`。

## [0.0.1-alpha.1] - 2026-04-02

> 发布通道：`alpha`

### Fixed

- 修复真实 Minium 运行时下的输入兼容性问题：当定位结果命中容器节点、文本节点或非最终输入节点时，服务会继续寻找真实的 `input` / `textarea` 节点再执行输入。
- 修复会话过期后的资源回收问题：过期会话现在会先走服务层统一清理，再释放底层 Minium 运行时资源，避免只删除内存记录而不关闭底层连接。
- 修复页面路径断言依赖缓存页面的问题：`miniapp_assert_page_path` 现在会先实时读取当前运行态页面，再基于实时值完成断言并更新会话上下文。

### Changed

- 补强真实运行时的输入回退链路，使 `miniapp_input_text` 在更复杂的弹窗、包裹层和文本定位场景下表现更稳定。
- 同步更新贡献文档与对外说明，补充真实运行时下点击回退、输入回退和协作提交流程相关说明。
- 统一文档中的项目名称表述为 `miniprogram-minium-mcp`，同时保留实际 npm 包名和命令名不变。

### Upgrade Notes

- 如果你通过 npm 安装或使用 `npx` 运行 `alpha` 通道，建议升级到 `0.0.1-alpha.1` 以获得更稳定的真实输入能力。
- 如果你使用本地 tarball 验证，请通过 `npx -y -p <package.tgz> minium-mcp` 的形式启动包暴露的 `bin`，不要直接把 `.tgz` 当作可执行文件。
- 当前回归结果为 `17 passed`，覆盖会话管理、真实运行时点击回退、输入回退、页面路径断言和失败取证等主链路。

## [0.0.1-alpha.0] - 2026-04-02

> 发布通道：`alpha`

### Added

- 首个 npm 预发布版本，提供 `@diaz9810/miniprogram-minium-mcp` 包名。
- 增加 `minium-mcp` 命令行入口，可通过 npm 包分发并由 `npx` 启动。
- 增加 Node.js 启动壳，用于托管 `uv`、Python 环境和最终的 Python MCP Server 启动流程。
- 增加 npm 发包基础配置与最小分发元数据。

### Packaging

- Node.js 运行时要求为 `>=18`
- 包入口为 `launcher/minium-mcp.mjs`
- 面向 `stdio` 方式启动 MCP Server

### Upgrade Notes

- 这是首个 `alpha` 版本，主要用于验证 npm 分发链路、启动壳行为和真实/占位运行时接入能力。
- 如果你计划基于该包做真实小程序验收，请优先配合最新文档中的配置约定和本地依赖前提使用。
