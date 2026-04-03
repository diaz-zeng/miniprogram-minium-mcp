# miniprogram-minium-mcp

`miniprogram-minium-mcp` 是一个面向 AI Agent 的微信小程序验收型 MCP Server。  
它基于 Minium，把“小程序启动、页面读取、元素查询、点击、输入、等待、断言、截图、多触点交互”整理成一组适合 Agent 调用的高层工具。

它的目标不是暴露底层 Minium 驱动对象，而是提供更稳定的“验收语义”：

- 用 `session` 管理一次完整的小程序验收流程
- 用结构化 `locator` 查找页面元素
- 用高层动作完成点击、输入、等待、断言
- 在失败时返回错误码、上下文摘要和截图证据

## 适合谁用

- 想让 Codex、Claude Code、Trae 这类支持 MCP 的 Agent 直接操作微信小程序
- 想把手工回归测试变成可编排、可复用的 Agent 验收流程
- 想保留失败截图和结构化上下文，方便排查自动化问题

## 能力概览

提供这些 MCP tools：

- `miniapp_create_session`
- `miniapp_close_session`
- `miniapp_get_current_page`
- `miniapp_capture_screenshot`
- `miniapp_query_elements`
- `miniapp_click`
- `miniapp_input_text`
- `miniapp_wait_for`
- `miniapp_touch_start`
- `miniapp_touch_move`
- `miniapp_touch_end`
- `miniapp_touch_tap`
- `miniapp_assert_page_path`
- `miniapp_assert_element_text`
- `miniapp_assert_element_visible`

这些工具主要覆盖四类能力：

1. 会话管理  
   创建、读取、关闭会话，并维护当前页面和运行时上下文。

2. 页面交互  
   查询元素、点击、输入、等待条件成立。

3. 验收断言  
   断言页面路径、元素文本和元素可见性。

4. 调试取证  
   截图、结构化错误详情、失败时的上下文保留。

## 多触点能力

包含一组实验性的多触点基础原语：

- `miniapp_touch_start`：按下并保持一个触点
- `miniapp_touch_move`：移动一个已按下的触点
- `miniapp_touch_end`：释放一个已按下的触点
- `miniapp_touch_tap`：用指定触点执行一次短按点击

这组能力适合表达“两指以内”的复合交互，例如：

- 第一指按住拖动
- 第一指未松开时第二指点击
- 一段连续手势由多次 MCP 调用拼成

服务端会在会话里维护：

- `active_pointers`
- `latest_gesture_event`

这样 Agent 不需要自己拼底层 `touches` / `changedTouches` 事件数组，只需要表达“哪个触点做了什么”。

## 真实运行时兼容策略

为了提升真实小程序场景下的成功率，运行时补了几层常见兼容：

- `click`：当文本定位命中的节点不是最终可交互目标时，会继续尝试可疑祖先节点
- `input`：当定位命中容器节点或文本节点时，会继续寻找内部真实 `input` / `textarea`
- `gesture`：对部分文本命中场景，会尽量选择更合理的交互节点，避免把手势落到只负责展示的内部元素

这些兼容的目标，是提高自定义组件、组合按钮、弹窗表单和复杂包裹层场景下的真实业务成功率。

## 安装与启动

### 推荐方式：通过 `npx` 启动

如果你是作为 MCP Server 使用，推荐在 MCP 客户端里这样配置：

```toml
[mcp_servers.minium_mcp]
type = "stdio"
command = "npx"
args = ["-y", "@diaz9810/miniprogram-minium-mcp"]
enabled = true
```

如果希望通过环境变量传配置，可以这样写：

```toml
[mcp_servers.minium_mcp.env]
MINIUM_MCP_PROJECT_PATH = "/path/to/miniapp"
MINIUM_MCP_WECHAT_DEVTOOL_PATH = "/path/to/wechat-devtool-cli"
MINIUM_MCP_ARTIFACTS_DIR = "/path/to/artifacts"
MINIUM_MCP_SESSION_TIMEOUT_SECONDS = "1800"
MINIUM_MCP_RUNTIME_MODE = "real"
MINIUM_MCP_TEST_PORT = "9420"
MINIUM_MCP_LANGUAGE = "zh-CN"
```

### 开发者方式：从源码本地运行

如果你是在本仓库里开发：

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/minium-mcp
```

如果需要显式传配置文件或日志级别：

```bash
.venv/bin/minium-mcp --config ./minium-mcp.toml --log-level DEBUG
```

## 运行前提

使用前请先确认：

- 已安装微信开发者工具
- 目标小程序目录存在 `project.config.json`
- 目标 MCP 客户端支持本地 `stdio` 类型 MCP Server

项目本身的 Python 要求见 [pyproject.toml](./pyproject.toml)，要求是 `>=3.11`。  
Node.js 版本要求见 [package.json](./package.json)，要求是 `>=18`。

## 最推荐的调用方式

最推荐的主链路是：

1. 调用 `miniapp_create_session`
2. 传入 `project_path`
3. 服务自动执行微信开发者工具 `auto`
4. 服务自动 attach 到小程序运行态
5. 再继续执行查询、点击、输入、等待、断言和截图

正常情况下你不需要：

- 手动先打开微信开发者工具
- 自己记自动化端口
- 在多个目标之间手动选择 attach 对象

## 典型验收流程

下面是一条常见的调用顺序：

1. `miniapp_create_session(project_path="...")`
2. `miniapp_get_current_page(session_id="...")`
3. `miniapp_query_elements(session_id="...", locator={...})`
4. `miniapp_click(session_id="...", locator={...})`
5. `miniapp_input_text(session_id="...", locator={...}, text="...")`
6. `miniapp_wait_for(session_id="...", condition={...})`
7. `miniapp_assert_element_text(...)`
8. `miniapp_capture_screenshot(...)`
9. `miniapp_close_session(...)`

如果你是做多触点场景，常见顺序会变成：

1. `miniapp_touch_start`
2. `miniapp_touch_move`
3. `miniapp_touch_tap`
4. `miniapp_touch_end`
5. 再补充查询或断言验证业务结果

## 定位器说明

支持的 `locator.type`：

- `id`
- `css`
- `text`

推荐优先级：

1. `id`
2. `css`
3. `text`

原因很简单：

- `id` 最稳定，最适合验收自动化
- `css` 适合结构清晰的页面
- `text` 最方便，但在复杂自定义组件下，真实命中节点未必就是最终交互节点

## 多触点验证脚本

仓库内提供了一个真实运行时最小验证脚本：

- [validate_multitouch_real.py](./scripts/validate_multitouch_real.py)

通用示例：

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_multitouch_real.py \
  --project-path /path/to/miniapp \
  --devtool-path /path/to/wechat-devtool-cli \
  --start-locator-type id \
  --start-locator-value drag-anchor \
  --tap-locator-type id \
  --tap-locator-value confirm-button \
  --move-x 320 \
  --move-y 420
```

这条脚本会按顺序执行：

1. 第一指 `touch_start`
2. 第一指 `touch_move`
3. 第二指 `touch_tap`
4. 第一指 `touch_end`

如果你的业务场景需要预置 storage、自动跳页或追加业务断言，可以在脚本参数基础上扩展预设或准备逻辑。

## 配置项说明

主要配置项如下：

- `MINIUM_MCP_PROJECT_PATH`
  默认小程序项目路径
- `MINIUM_MCP_WECHAT_DEVTOOL_PATH`
  微信开发者工具 CLI 路径
- `MINIUM_MCP_ARTIFACTS_DIR`
  截图和调试产物目录
- `MINIUM_MCP_SESSION_TIMEOUT_SECONDS`
  会话超时时间，单位秒
- `MINIUM_MCP_RUNTIME_MODE`
  运行模式，支持 `real`、`auto`、`placeholder`
- `MINIUM_MCP_TEST_PORT`
  Minium 使用的自动化端口
- `MINIUM_MCP_LANGUAGE`
  输出语言，支持 `zh-CN` 或 `en`

### 运行模式

- `real`
  强制走真实 Minium 运行时
- `auto`
  推荐模式，按真实环境优先执行
- `placeholder`
  仅用于本地开发和协议调试，不连接真实小程序

### 输出语言

- 中文环境默认输出中文
- 非中文环境默认输出英文
- 也可以用 `MINIUM_MCP_LANGUAGE` 显式覆盖

## 返回结果与错误模型

服务优先返回结构化结果，而不是只给一段文本。

成功返回通常会包含：

- `ok`
- `session_id`
- `current_page_path`
- 与当前动作对应的数据字段

失败返回通常会包含：

- `error_code`
- `message`
- `details`
- `artifacts`

常见错误类型包括：

- `ENVIRONMENT_ERROR`
- `SESSION_ERROR`
- `ACTION_ERROR`
- `ASSERTION_FAILED`
- `INTERNAL_ERROR`

## 截图与调试产物

截图和调试产物默认落在：

- `artifacts/`

这些产物主要用于：

- 动作失败排查
- 断言失败取证
- 等待超时后的页面状态确认
- 多触点场景下的业务结果留档

## 能力边界

有这些明确边界：

- 这是验收型 MCP，不暴露底层 Minium 对象
- 不支持任意脚本执行
- 多触点能力收敛在“两指以内”
- 不提供通用手势 DSL 或原始事件注入接口
- 文本定位在复杂自定义组件下仍建议结合真实业务页面验证

## 常见问题

### 1. 必须手动打开微信开发者工具吗？

通常不需要。  
推荐做法是直接传 `project_path`，服务会自动走 `auto + attach`。

### 2. 为什么点击成功返回了，但页面没有变化？

常见原因有三种：

- 命中了展示节点，而不是最终交互节点
- 组件本身对自动化点击兼容性一般
- 页面还没进入可交互状态

建议优先：

1. 用 `id` 代替 `text`
2. 增加 `wait_for`
3. 结合截图和 `details` 排查

### 3. 为什么输入没有真正写进表单？

复杂自定义表单里，定位结果可能先命中容器节点。  
运行时已经补了输入回退逻辑，但如果页面结构特别复杂，仍建议给真实输入框补更稳定的 `id`。

### 4. 多触点场景怎么判断是否真的成功？

不要只看手势动作返回成功。  
更推荐在手势之后继续补一条业务断言，例如：

- 当前录入区域出现有效分值
- 某个标记数量增加
- 某个状态文本发生变化

## 开发说明

如果你是仓库维护者或贡献者，可以继续看：

- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [CHANGELOG.md](./CHANGELOG.md)

如果你关心这次多触点能力的设计与实现过程，可以看：

- [proposal.md](./openspec/changes/add-miniapp-multitouch-gestures/proposal.md)
- [design.md](./openspec/changes/add-miniapp-multitouch-gestures/design.md)
- [tasks.md](./openspec/changes/add-miniapp-multitouch-gestures/tasks.md)
