## ADDED Requirements

### Requirement: Server SHALL run as a local stdio MCP service
系统 SHALL 以本地 `stdio` 模式运行，并由本机进程启动 Python 实现的 MCP Server，而不是要求远程 HTTP 部署才能使用。

#### Scenario: Codex launches the server locally
- **WHEN** MCP 客户端以本地命令启动该服务
- **THEN** 服务 SHALL 通过标准输入输出提供 MCP 能力
- **THEN** 服务 SHALL 不要求预先存在远程 MCP URL

#### Scenario: Local environment is missing required dependencies
- **WHEN** 服务启动后或首次创建会话时发现 Minium、Python 依赖或微信开发者工具缺失
- **THEN** 服务 SHALL 返回结构化环境错误
- **THEN** 错误信息 SHALL 指明缺失依赖的类型和本地修复方向

### Requirement: Server SHALL create and manage acceptance sessions explicitly
系统 SHALL 提供显式的验收会话创建与关闭能力，并为每个成功创建的会话分配唯一 `session_id`，供后续动作与断言调用复用。

#### Scenario: Create a session from a project path
- **WHEN** 调用方提供本地小程序项目路径并请求创建验收会话
- **THEN** 服务 SHALL 自行完成开发者工具拉起、自动化端口准备和底层运行态附着
- **THEN** 服务 SHALL 返回唯一 `session_id`
- **THEN** 返回结果 SHALL 包含当前会话的基础状态摘要

#### Scenario: Close an active session
- **WHEN** 调用方请求关闭一个有效会话
- **THEN** 服务 SHALL 释放该会话对应的底层连接和内存资源
- **THEN** 后续针对该 `session_id` 的调用 SHALL 返回会话不可用错误

### Requirement: Session-scoped tools SHALL require a valid session identifier
所有依赖运行态上下文的页面读取、交互、等待、断言和取证工具 MUST 要求有效的 `session_id` 输入，并基于该会话执行。

#### Scenario: Call a session-scoped tool with a valid session
- **WHEN** 调用方携带有效 `session_id` 调用页面或动作类工具
- **THEN** 服务 SHALL 在该会话关联的小程序运行态上执行请求

#### Scenario: Call a session-scoped tool with an invalid session
- **WHEN** 调用方传入不存在、已关闭或已过期的 `session_id`
- **THEN** 服务 SHALL 返回 `SESSION_ERROR`
- **THEN** 错误结果 SHALL 说明会话无效的原因

### Requirement: Session state SHALL preserve acceptance context across multiple tool calls
系统 SHALL 在会话生命周期内保留验收上下文，至少包括最近页面路径、最后活跃时间、最近一次截图路径和最近一次失败摘要，以支持多轮 Agent 调用。

#### Scenario: Session context updates after successful operations
- **WHEN** 同一会话内连续执行页面读取、截图或动作操作
- **THEN** 服务 SHALL 更新该会话保存的最近上下文摘要
- **THEN** 后续工具调用 SHALL 能读取到最新的会话状态

#### Scenario: Session expires after inactivity
- **WHEN** 会话空闲超过设定超时时间
- **THEN** 服务 SHALL 自动清理该会话占用的资源
- **THEN** 后续调用 SHALL 收到会话已失效的结构化错误

### Requirement: Session management SHALL expose current page and evidence context
系统 SHALL 提供获取当前页面与基础证据上下文的能力，以便 Agent 在不执行业务动作时也能判断当前运行态。

#### Scenario: Read current page from an active session
- **WHEN** 调用方请求获取当前页面信息
- **THEN** 服务 SHALL 返回当前页面路径
- **THEN** 返回结果 SHALL 包含页面可读摘要或可用的上下文信息

#### Scenario: Capture a screenshot from an active session
- **WHEN** 调用方请求当前会话截图
- **THEN** 服务 SHALL 在本地 `artifacts/` 目录下生成截图文件
- **THEN** 返回结果 SHALL 包含截图路径和所属 `session_id`

### Requirement: Session management SHALL enforce acceptance-only boundaries
系统 MUST 将能力边界限制在验收与测试范围内，不得通过会话管理工具直接暴露底层 Minium 对象、任意脚本执行能力或任意运行态修改入口。

#### Scenario: Caller requests unsupported low-level control
- **WHEN** 调用方尝试访问未被允许的底层驱动能力或通用脚本执行能力
- **THEN** 服务 SHALL 拒绝该请求
- **THEN** 返回结果 SHALL 明确说明该能力超出验收型 MCP 的边界

### Requirement: Session-facing output SHALL support Chinese and English
系统 SHALL 对所有面向调用方的会话相关输出提供中文和英文支持，并根据运行环境语言在中文与英文之间自动选择；非中文环境 MUST 输出英文。

#### Scenario: Session output in a Chinese environment
- **WHEN** 服务运行在中文语言环境
- **THEN** 会话创建、关闭、状态读取和错误提示中的可读消息 SHALL 使用中文

#### Scenario: Session output in a non-Chinese environment
- **WHEN** 服务运行在非中文语言环境
- **THEN** 会话创建、关闭、状态读取和错误提示中的可读消息 SHALL 使用英文
- **THEN** 结构化返回字段名 SHALL 保持不变
