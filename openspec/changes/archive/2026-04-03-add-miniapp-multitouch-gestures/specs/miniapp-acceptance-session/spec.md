## MODIFIED Requirements

### Requirement: Session state SHALL preserve acceptance context across multiple tool calls
系统 SHALL 在会话生命周期内保留验收上下文，至少包括最近页面路径、最后活跃时间、最近一次截图路径、最近一次失败摘要，以及手势场景所需的活跃触点状态和最近一次手势事件摘要，以支持多轮 Agent 调用。

#### Scenario: Session context updates after successful operations
- **WHEN** 同一会话内连续执行页面读取、截图、动作操作或手势操作
- **THEN** 服务 SHALL 更新该会话保存的最近上下文摘要
- **THEN** 后续工具调用 SHALL 能读取到最新的页面状态、截图路径及最近一次手势事件摘要

#### Scenario: Session context tracks active pointers across gesture calls
- **WHEN** 调用方在同一会话中先后执行 `touch_start`、`touch_move`、`touch_tap` 或 `touch_end`
- **THEN** 服务 SHALL 维护与这些调用对应的活跃触点集合
- **THEN** 后续手势调用 SHALL 基于该会话中保留的活跃触点状态继续执行

#### Scenario: Session expires after inactivity
- **WHEN** 会话空闲超过设定超时时间
- **THEN** 服务 SHALL 自动清理该会话占用的资源和活跃触点状态
- **THEN** 后续调用 SHALL 收到会话已失效的结构化错误
