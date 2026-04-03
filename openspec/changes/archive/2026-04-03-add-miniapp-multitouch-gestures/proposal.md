## Why

当前验收型 MCP 只覆盖点击、输入、等待和断言，无法表达“按住不松开、持续拖动、第二指插入点击”这类多触点交互，因此无法验证依赖复合手势的小程序功能。随着小程序里拖拽、画布、标注、双指辅助交互等场景增多，我们需要在保持验收边界收敛的前提下，为 AI Agent 补齐最小可行的多触点基础能力。

## What Changes

- 新增一组面向 AI Agent 的多触点基础手势能力，覆盖 `touch_start`、`touch_move`、`touch_end`、`touch_tap` 等最小原语，用于表达“按住并移动”“第一指未松开时第二指点击”等复合交互。
- 在会话状态中新增活跃触点上下文，记录 `pointer_id`、当前坐标、按下状态和最近一次事件摘要，使多次 tool call 可以组合成连续手势。
- 为手势相关失败补充结构化取证，除截图外返回活跃触点、变更触点、目标解析结果等调试信息，便于 Agent 判断是定位问题、坐标问题还是事件时序问题。
- 明确首期手势能力边界：聚焦验收语义下的基础触点原语和两指内复合交互，不开放任意脚本注入、任意事件回放 DSL 或底层 Minium 对象透传。

## Capabilities

### New Capabilities
- `miniapp-acceptance-gestures`: 面向 AI Agent 的小程序多触点与复合手势验收能力，覆盖基础触点原语、活跃触点组合、手势失败取证与能力边界。

### Modified Capabilities
- `miniapp-acceptance-session`: 扩展会话上下文保留能力，使其能够维护活跃触点状态、最近手势事件摘要和与手势取证相关的上下文信息。

## Impact

- 新增 `openspec/specs/miniapp-acceptance-gestures/spec.md`，并修改 `openspec/specs/miniapp-acceptance-session/spec.md`。
- 影响会话与动作相关的领域模型与服务层，尤其是会话状态结构、手势状态维护、失败取证和会话清理逻辑。
- 影响 Minium 运行时适配层，需要把底层 touch 事件能力封装成稳定的高层 MCP 手势原语。
- 影响 MCP tool 注册与返回结构，需要新增手势类工具并在响应中补充活跃触点摘要。
- 需要补充占位运行时与真实运行时两类测试，覆盖单指按住、多步移动、第二指点击和失败取证等路径。
