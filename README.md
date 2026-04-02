# minium-mcp

`minium-mcp` 是一个面向 AI Agent 的微信小程序验收型 MCP Server。  
它基于 Minium，把“小程序打开、页面读取、元素查询、点击、输入、等待、断言、截图”这些能力整理成一组适合 MCP 调用的高层工具。

当前版本的推荐使用方式很简单：

- 提供小程序项目路径
- 服务自动执行微信开发者工具 `auto`
- 自动完成 Minium attach
- 然后由 Agent 继续做验收和自动化测试

## 适合谁用

- 想让 Codex、Claude Code、Trae 这类支持 MCP 的 Agent 直接操作微信小程序
- 想把手工回归测试变成可编排的 AI 验收流程
- 想保留截图、错误上下文和结构化断言结果，方便排查失败原因

## 当前能力

当前已经提供这些 MCP tools：

- `miniapp_create_session`
- `miniapp_close_session`
- `miniapp_get_current_page`
- `miniapp_capture_screenshot`
- `miniapp_query_elements`
- `miniapp_click`
- `miniapp_input_text`
- `miniapp_wait_for`
- `miniapp_assert_page_path`
- `miniapp_assert_element_text`
- `miniapp_assert_element_visible`

这些工具的设计目标是“验收语义”，不是直接暴露底层 Minium 对象。  
也就是说，调用方拿到的是结构化结果、错误码和证据路径，而不是底层驱动句柄。

当前版本在真实运行时里还额外补了两层关键兼容：

- `click`：当文本定位命中的节点本身不是最终可交互目标时，会继续尝试其可疑祖先节点，减少“文案点到了但业务没触发”的情况
- `input`：当定位器命中的不是最终 `input/textarea`，而是它外层的容器节点时，会继续在子树里寻找真实可输入节点
- `input`：对文本定位命中的场景，会优先尝试目标元素本身，再尝试可疑祖先容器中的真实输入节点
- 这两层兼容的目标，是提升弹窗、表单、组合组件和自定义样式输入框场景下的真实业务成功率

## 已验证能力

在真实小程序项目上，当前已经验证通过的主链路包括：

- 根据 `project_path` 自动拉起微信开发者工具并连接运行态
- 获取当前页面路径
- 截图
- 查询页面文本和输入框
- 点击首页按钮打开弹窗
- 当文本节点本身不可直接点击时，自动回退到可疑祖先节点继续点击
- 向真实 `input` 节点输入内容
- 当定位到的是输入容器时，自动回退到内部真实 `input/textarea` 节点继续输入
- 当文本定位命中的不是最终输入节点时，继续在目标节点或祖先容器里寻找真实输入框
- 点击保存按钮并触发真实业务逻辑
- 通过页面数据变化验证业务动作成功

下面这些验收场景也已经通过实际回归验证：

- 启动与首页冒烟：
  基于 `project_path` 创建会话、读取当前页面、截图，并确认首页入口元素存在
- 首页点击到弹窗：
  从首页点击业务入口后，能够稳定等待到对应录入弹窗出现
- 输入回归验证：
  当定位命中真实输入框、输入容器或与输入框关联的文本节点时，仍能把数值写入最终 `input`
- 业务闭环验证：
  打开业务录入弹窗，输入数值，点击“保存”后，首页对应统计能够按预期变化
- 失败取证验证：
  在断言失败、动作失败或等待超时时，会返回结构化错误并附带证据产物
- 无效会话验证：
  会话关闭后再次调用会返回结构化 `SESSION_ERROR`

## 运行前提

使用前请先确认本机具备以下条件：

- 已安装微信开发者工具
- 小程序项目目录存在 `project.config.json`
- 目标 MCP 客户端支持本地 `stdio` 类型的 MCP Server

对最终用户来说，当前推荐方式是直接通过 `npx` 启动。  
在这种模式下：

- Python 由 launcher 托管
- `minium` 由 launcher 自动准备
- 用户不需要手动创建虚拟环境或手动安装 Python 依赖

当前版本默认面向**本地单用户环境**，不需要远程部署。

## 安装与使用

### 1. 最推荐：直接通过 `npx` 启动

如果发布为 npm 包，推荐在 MCP 客户端里这样配置：

```toml
[mcp_servers.minium_mcp]
type = "stdio"
command = "npx"
args = ["-y", "@diaz9810/miniprogram-minium-mcp"]
enabled = true
```

这条路径会由 Node 启动壳负责：

- 下载或复用托管的 `uv`
- 由 `uv` 托管 Python
- 自动安装并启动 `minium-mcp` 的 Python 服务

如果希望通过环境变量传配置，可以这样写：

```toml
[mcp_servers.minium_mcp.env]
MINIUM_MCP_PROJECT_PATH = "/path/to/miniapp"
MINIUM_MCP_WECHAT_DEVTOOL_PATH = "/Applications/wechatwebdevtools.app/Contents/MacOS/cli"
MINIUM_MCP_ARTIFACTS_DIR = "/path/to/artifacts"
MINIUM_MCP_SESSION_TIMEOUT_SECONDS = "1800"
MINIUM_MCP_RUNTIME_MODE = "real"
MINIUM_MCP_TEST_PORT = "9420"
MINIUM_MCP_LANGUAGE = "zh-CN"
```

### 2. 开发者模式：从源码本地运行

如果你是在本仓库里开发，仍然可以继续使用 Python 方式本地启动：

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/minium-mcp
```

如果需要显式传配置文件或日志级别：

```bash
.venv/bin/minium-mcp --config ./minium-mcp.toml --log-level DEBUG
```

## 最推荐的调用方式

最推荐的主链路是：

1. 调用 `miniapp_create_session`
2. 传入 `project_path`
3. 服务自动执行 `cli auto --project ... --auto-port ...`
4. 服务自动 attach 到小程序运行态
5. 再继续执行查询、点击、输入、等待和断言

也就是说，正常情况下你不需要：

- 手动先打开微信开发者工具
- 自己记自动化端口
- 在多个目标之间手动选择 attach 对象

当前版本已经把对外接口收敛为“按项目路径驱动”。

## 示例流程

下面是一条典型的验收流程：

1. `miniapp_create_session(project_path="...")`
2. `miniapp_get_current_page(session_id="...")`
3. `miniapp_query_elements(session_id="...", locator={...})`
4. `miniapp_click(session_id="...", locator={...})`
5. `miniapp_input_text(session_id="...", locator={...}, text="...")`
6. `miniapp_wait_for(session_id="...", condition={...})`
7. `miniapp_assert_element_text(...)`
8. `miniapp_capture_screenshot(...)`
9. `miniapp_close_session(...)`

## 配置项说明

当前支持的主要配置项如下：

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
  Minium 连接微信开发者工具使用的自动化端口
- `MINIUM_MCP_LANGUAGE`
  输出语言，支持 `zh-CN` 或 `en`

语言规则如下：

- 中文环境输出中文
- 非中文环境输出英文
- 也可以用 `MINIUM_MCP_LANGUAGE` 显式覆盖

运行模式说明：

- `real`
  强制走真实 Minium 运行时
- `auto`
  默认推荐模式，按真实环境路径执行
- `placeholder`
  仅用于本地开发和协议调试，不连接真实小程序

## 错误与产物

当前服务会返回结构化错误，并尽量附带排查信息。  
常见错误类型包括：

- `ENVIRONMENT_ERROR`
- `SESSION_ERROR`
- `ACTION_ERROR`
- `ASSERTION_FAILED`
- `INTERNAL_ERROR`

截图和调试产物默认落在：

- `artifacts/` 目录

动作失败、等待超时或断言失败时，服务会尽量自动补一张截图，方便继续排查。

## 当前限制

当前版本有这些边界和限制：

- 不暴露底层 Minium 对象
- 不支持任意脚本执行
- 不把 MCP 设计成远程多租户服务
- 当前重点是验收与自动化测试，不是通用调试代理
- 当前真实联调主要在 macOS 上完成，Windows 兼容性还需要继续验证

## 常见问题

### 1. 必须手动打开微信开发者工具吗？

通常不需要。  
当前推荐方式是直接提供 `project_path`，服务会自己执行 `auto + attach`。

### 1.1 必须手动安装 Python 和 `minium` 吗？

如果你走的是 `npx` 启动方式，通常不需要。  
当前 launcher 的目标就是把 Python 和 `minium` 都隐藏在启动过程里。

如果你是从源码运行，才需要自己准备 Python 环境。

### 2. 为什么明明能看到开发者工具里的“服务端口”，Minium 还是连不上？

因为微信开发者工具的“服务端口”和 Minium 使用的“自动化端口”不是一回事。  
当前服务内部会优先准备 Minium 需要的自动化端口，而不是直接拿 IDE 服务端口去连接。

### 3. 为什么有时点击成功返回了，但页面没有变化？

有些 Taro/自定义组件对自动化点击不够友好。  
当前运行时已经补了“文本节点向上寻找可交互祖先再点击”的兼容策略，但不同项目里仍然可能遇到新的点击兼容问题。

### 4. 如果失败了，应该先看哪里？

优先看这三处：

- 返回里的 `error_code`
- 返回里的 `details`
- `artifacts/` 目录下的截图

## 开发说明

如果你是仓库维护者或贡献者，可以继续看：

- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [CHANGELOG.md](./CHANGELOG.md)

如果你关心这条能力的设计来源和变更过程，可以看：

- [openspec/changes/add-minium-based-miniapp-acceptance-mcp/proposal.md](./openspec/changes/add-minium-based-miniapp-acceptance-mcp/proposal.md)
- [openspec/changes/add-minium-based-miniapp-acceptance-mcp/design.md](./openspec/changes/add-minium-based-miniapp-acceptance-mcp/design.md)
