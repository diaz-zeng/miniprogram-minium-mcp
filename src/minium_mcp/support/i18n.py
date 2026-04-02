"""国际化支持。"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_LANGUAGE = "zh-CN"
FALLBACK_LANGUAGE = "en"

MESSAGE_CATALOG: dict[str, dict[str, str]] = {
    "cli.prog_description": {
        "zh-CN": "启动基于 Minium 的本地 stdio MCP Server。",
        "en": "Start the local stdio MCP Server powered by Minium.",
    },
    "cli.transport_help": {
        "zh-CN": "首期只支持本地 stdio 传输。",
        "en": "Only local stdio transport is supported in the first version.",
    },
    "cli.config_help": {
        "zh-CN": "可选的本地配置文件路径，支持 .json/.toml。",
        "en": "Optional local config file path. Supports .json and .toml.",
    },
    "cli.log_level_help": {
        "zh-CN": "可选日志级别覆盖，例如 DEBUG/INFO/WARNING。",
        "en": "Optional log level override, for example DEBUG/INFO/WARNING.",
    },
    "server.instructions": {
        "zh-CN": (
            "这是一个面向 AI Agent 的本地小程序验收型 MCP Server。"
            "首期以本地 stdio 方式运行，后续工具将围绕会话、动作、断言和取证展开。"
        ),
        "en": (
            "This is a local miniapp acceptance MCP Server for AI agents. "
            "The first version runs over local stdio and will expose tools "
            "for sessions, actions, assertions, and evidence capture."
        ),
    },
    "server.transport_unsupported": {
        "zh-CN": "当前版本只支持 stdio 传输。",
        "en": "The current version only supports stdio transport.",
    },
    "server.context_built": {
        "zh-CN": "已构建 MCP Server 运行上下文。",
        "en": "MCP Server runtime context has been built.",
    },
    "server.context_initialized": {
        "zh-CN": "服务上下文初始化完成。",
        "en": "Service context initialized.",
    },
    "error.environment_missing": {
        "zh-CN": "本地运行环境缺少必要依赖。",
        "en": "The local runtime environment is missing required dependencies.",
    },
    "error.invalid_session": {
        "zh-CN": "会话不存在、已关闭或已过期。",
        "en": "The session does not exist, has been closed, or has expired.",
    },
    "error.missing_project_path": {
        "zh-CN": "启动模式需要有效的小程序项目路径。",
        "en": "Launch mode requires a valid miniapp project path.",
    },
    "error.missing_devtool_path": {
        "zh-CN": "需要有效的微信开发者工具路径。",
        "en": "A valid WeChat DevTools path is required.",
    },
    "session.created": {
        "zh-CN": "验收会话已创建。",
        "en": "Acceptance session created.",
    },
    "session.closed": {
        "zh-CN": "验收会话已关闭。",
        "en": "Acceptance session closed.",
    },
    "session.current_page": {
        "zh-CN": "已获取当前页面信息。",
        "en": "Current page information retrieved.",
    },
    "session.screenshot_created": {
        "zh-CN": "已生成当前会话截图。",
        "en": "A screenshot was created for the current session.",
    },
    "session.placeholder_runtime": {
        "zh-CN": "当前使用占位运行时，尚未接入真实 Minium 驱动。",
        "en": "The current session uses a placeholder runtime. Real Minium integration is not connected yet.",
    },
    "session.real_runtime": {
        "zh-CN": "当前会话已接入真实 Minium 运行时。",
        "en": "The current session is connected to the real Minium runtime.",
    },
    "tool.create_session.description": {
        "zh-CN": "创建一个小程序验收会话；提供项目路径时会自动执行开发者工具 auto 并完成 attach，不再暴露多目标选择。",
        "en": "Create a miniapp acceptance session; when a project path is provided, the server will run DevTools auto and then attach, without exposing multi-target selection.",
    },
    "tool.close_session.description": {
        "zh-CN": "关闭一个已创建的验收会话。",
        "en": "Close an existing acceptance session.",
    },
    "tool.get_current_page.description": {
        "zh-CN": "读取当前会话的页面路径与页面摘要。",
        "en": "Read the current page path and summary for a session.",
    },
    "tool.capture_screenshot.description": {
        "zh-CN": "为当前会话生成一张截图并返回产物路径。",
        "en": "Capture a screenshot for the current session and return the artifact path.",
    },
    "tool.query_elements.description": {
        "zh-CN": "按结构化定位器查询元素并返回摘要。",
        "en": "Query elements with a structured locator and return summaries.",
    },
    "tool.click.description": {
        "zh-CN": "点击定位到的元素。",
        "en": "Click the element located by the locator.",
    },
    "tool.input.description": {
        "zh-CN": "向定位到的元素输入文本。",
        "en": "Input text into the element located by the locator.",
    },
    "tool.wait_for.description": {
        "zh-CN": "等待页面路径或元素条件成立。",
        "en": "Wait for a page-path or element condition to be satisfied.",
    },
    "tool.assert_page_path.description": {
        "zh-CN": "断言当前页面路径与期望值一致。",
        "en": "Assert that the current page path matches the expected value.",
    },
    "tool.assert_element_text.description": {
        "zh-CN": "断言定位元素的文本与期望值一致。",
        "en": "Assert that the located element text matches the expected value.",
    },
    "tool.assert_element_visible.description": {
        "zh-CN": "断言定位元素当前可见。",
        "en": "Assert that the located element is visible.",
    },
    "config.file_not_found": {
        "zh-CN": "配置文件不存在: {path}",
        "en": "Config file does not exist: {path}",
    },
    "config.unsupported_format": {
        "zh-CN": "配置文件仅支持 .json 或 .toml 格式。",
        "en": "Only .json and .toml config files are supported.",
    },
    "action.query.success": {
        "zh-CN": "元素查询完成。",
        "en": "Element query completed.",
    },
    "action.click.success": {
        "zh-CN": "点击动作执行成功。",
        "en": "Click action completed successfully.",
    },
    "action.input.success": {
        "zh-CN": "输入动作执行成功。",
        "en": "Input action completed successfully.",
    },
    "action.wait.success": {
        "zh-CN": "等待条件已满足。",
        "en": "The wait condition has been satisfied.",
    },
    "assert.page_path.success": {
        "zh-CN": "页面路径断言成功。",
        "en": "Page path assertion passed.",
    },
    "assert.page_path.failed": {
        "zh-CN": "页面路径断言失败。",
        "en": "Page path assertion failed.",
    },
    "assert.element_text.success": {
        "zh-CN": "元素文本断言成功。",
        "en": "Element text assertion passed.",
    },
    "assert.element_text.failed": {
        "zh-CN": "元素文本断言失败。",
        "en": "Element text assertion failed.",
    },
    "assert.element_visible.success": {
        "zh-CN": "元素可见性断言成功。",
        "en": "Element visibility assertion passed.",
    },
    "assert.element_visible.failed": {
        "zh-CN": "元素当前不可见。",
        "en": "The element is not visible.",
    },
    "error.unsupported_locator_type": {
        "zh-CN": "当前版本不支持该定位器类型。",
        "en": "This locator type is not supported in the current version.",
    },
    "error.element_not_found": {
        "zh-CN": "未找到匹配的元素。",
        "en": "No matching element was found.",
    },
    "error.element_not_interactable": {
        "zh-CN": "目标元素当前不可交互。",
        "en": "The target element is not interactable.",
    },
    "error.wait_timeout": {
        "zh-CN": "等待条件超时。",
        "en": "Waiting for the condition timed out.",
    },
    "error.minium_launch_failed": {
        "zh-CN": "接入 Minium 运行时失败。",
        "en": "Failed to connect to the Minium runtime.",
    },
    "error.devtool_auto_failed": {
        "zh-CN": "准备微信开发者工具自动化端口失败。",
        "en": "Failed to prepare the WeChat DevTools automation port.",
    },
    "error.runtime_boundary": {
        "zh-CN": "当前请求超出验收型 MCP 的能力边界。",
        "en": "The request exceeds the boundaries of the acceptance MCP.",
    },
}


def detect_language(explicit_language: str | None = None) -> str:
    """检测当前语言，中文环境返回中文，否则统一返回英文。"""
    candidate = explicit_language or _detect_from_environment()
    normalized = (candidate or "").strip().lower()

    if normalized.startswith("zh"):
        return DEFAULT_LANGUAGE
    return FALLBACK_LANGUAGE


def translate(key: str, language: str, **kwargs: Any) -> str:
    """根据语言获取消息模板。"""
    catalog = MESSAGE_CATALOG.get(key, {})
    template = catalog.get(language) or catalog.get(FALLBACK_LANGUAGE) or key
    return template.format(**kwargs)


def _detect_from_environment() -> str:
    for env_key in ("MINIUM_MCP_LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(env_key)
        if value:
            return value
    return DEFAULT_LANGUAGE
