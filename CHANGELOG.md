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
