## ADDED Requirements

### Requirement: Server SHALL support structured element querying
系统 SHALL 提供结构化元素查询能力，使用可校验的定位器对象描述目标元素，而不是要求调用方直接操作底层元素句柄。

#### Scenario: Query elements with a supported locator
- **WHEN** 调用方提供受支持的定位器对象查询元素
- **THEN** 服务 SHALL 返回可序列化的查询结果摘要
- **THEN** 查询结果 SHALL 至少包含匹配数量或首个匹配元素的关键信息

#### Scenario: Query elements with an unsupported locator type
- **WHEN** 调用方提供当前版本不支持的定位器类型
- **THEN** 服务 SHALL 返回参数校验错误
- **THEN** 错误结果 SHALL 指明支持的定位器类型范围

### Requirement: Server SHALL support core acceptance actions on queried targets
系统 SHALL 支持验收主链路所需的核心动作能力，至少包括点击、输入与基于会话的页面级读取，并在执行时使用会话上下文与结构化定位器。

#### Scenario: Click a target element successfully
- **WHEN** 调用方提供有效 `session_id` 与可点击目标定位器并发起点击
- **THEN** 服务 SHALL 在该目标元素上执行点击动作
- **THEN** 返回结果 SHALL 说明动作执行成功

#### Scenario: Input text into a target element successfully
- **WHEN** 调用方提供有效 `session_id`、目标定位器和输入文本并发起输入
- **THEN** 服务 SHALL 将文本输入到目标元素
- **THEN** 返回结果 SHALL 包含动作完成的确认信息

#### Scenario: Action target is not interactable
- **WHEN** 目标元素不存在、不可见或不可交互
- **THEN** 服务 SHALL 返回 `ACTION_ERROR`
- **THEN** 错误结果 SHALL 包含定位器摘要和失败原因

### Requirement: Server SHALL support explicit waiting for acceptance conditions
系统 SHALL 提供等待条件成立的能力，以支持页面稳定、元素出现、元素可见或其他首期支持的验收条件。

#### Scenario: Wait succeeds before timeout
- **WHEN** 调用方请求等待一个受支持的条件且该条件在超时前满足
- **THEN** 服务 SHALL 返回等待成功结果
- **THEN** 返回结果 SHALL 包含实际等待到的条件摘要

#### Scenario: Wait times out
- **WHEN** 调用方请求等待一个受支持的条件但在超时前未满足
- **THEN** 服务 SHALL 返回 `ACTION_ERROR`
- **THEN** 错误结果 SHALL 标明超时并附带可用证据

### Requirement: Server SHALL provide structured assertions for acceptance checks
系统 SHALL 提供结构化断言能力，至少覆盖页面路径、元素文本与元素存在性或可见性校验，并返回适合 Agent 继续决策的结果。

#### Scenario: Assert current page path successfully
- **WHEN** 调用方断言当前页面路径与期望值一致
- **THEN** 服务 SHALL 返回断言成功结果

#### Scenario: Assert element text successfully
- **WHEN** 调用方断言某元素文本与期望值一致
- **THEN** 服务 SHALL 返回断言成功结果
- **THEN** 返回结果 SHALL 包含被校验的实际观测值摘要

#### Scenario: Assertion fails
- **WHEN** 页面路径、元素文本或可见性断言不成立
- **THEN** 服务 SHALL 返回 `ASSERTION_FAILED`
- **THEN** 错误结果 SHALL 同时包含期望值、实际值和证据路径

### Requirement: Action and assertion failures SHALL produce evidence artifacts automatically
系统 MUST 在动作失败、等待超时或断言失败时自动执行一次基础取证，并把证据路径与调试上下文纳入返回结果。

#### Scenario: Evidence is captured on assertion failure
- **WHEN** 任一断言失败
- **THEN** 服务 SHALL 自动生成截图或其他首期定义的证据产物
- **THEN** 返回结果 SHALL 包含证据文件路径

#### Scenario: Evidence is captured on action failure
- **WHEN** 点击、输入或等待动作失败
- **THEN** 服务 SHALL 返回包含 `error_code`、`message`、`details` 和 `artifacts` 的结构化错误
- **THEN** `details` SHALL 包含页面路径、定位器摘要或超时信息中的至少一部分

### Requirement: Action results SHALL remain bounded to acceptance semantics
系统 MUST 将动作和断言能力限制在通用验收语义内，不得要求调用方理解或持有底层 Minium 特有对象，也不得提供任意脚本执行作为替代路径。

#### Scenario: Caller attempts to bypass high-level actions
- **WHEN** 调用方试图通过工具接口执行未受控的底层脚本或原生对象操作
- **THEN** 服务 SHALL 拒绝该请求
- **THEN** 返回结果 SHALL 说明该请求超出当前 MCP 的能力边界

### Requirement: Action and assertion output SHALL support Chinese and English
系统 SHALL 对动作、等待、断言及失败取证相关的可读输出提供中文和英文支持，并根据运行环境语言自动选择；非中文环境 MUST 输出英文。

#### Scenario: Action output in a Chinese environment
- **WHEN** 服务运行在中文语言环境且动作或断言完成
- **THEN** 成功消息和失败消息中的可读内容 SHALL 使用中文

#### Scenario: Action output in a non-Chinese environment
- **WHEN** 服务运行在非中文语言环境且动作或断言完成或失败
- **THEN** 成功消息和失败消息中的可读内容 SHALL 使用英文
- **THEN** `error_code`、`details`、`artifacts` 等结构化字段 SHALL 保持稳定
