"""动作与断言 MCP tools。"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from minium_mcp.domain.action_models import Locator, WaitCondition
from minium_mcp.domain.action_service import ActionService
from minium_mcp.domain.errors import AcceptanceError
from minium_mcp.domain.service_context import ServiceContext
from minium_mcp.support.i18n import translate


def register_action_tools(server: FastMCP, context: ServiceContext) -> None:
    """注册动作与断言 tools。"""
    service = ActionService(
        repository=context.session_repository,
        runtime_adapter=context.runtime_adapter,
        artifact_manager=context.artifact_manager,
        language=context.language,
    )

    @server.tool(
        name="miniapp_query_elements",
        description=translate("tool.query_elements.description", context.language),
    )
    def query_elements(session_id: str, locator: Locator) -> dict:
        try:
            return service.query_elements(session_id, locator)
        except AcceptanceError as error:
            return error.to_response(language=context.language)

    @server.tool(
        name="miniapp_click",
        description=translate("tool.click.description", context.language),
    )
    def click(session_id: str, locator: Locator) -> dict:
        try:
            return service.click(session_id, locator)
        except AcceptanceError as error:
            return error.to_response(language=context.language)

    @server.tool(
        name="miniapp_input_text",
        description=translate("tool.input.description", context.language),
    )
    def input_text(session_id: str, locator: Locator, text: str) -> dict:
        try:
            return service.input_text(session_id, locator, text)
        except AcceptanceError as error:
            return error.to_response(language=context.language)

    @server.tool(
        name="miniapp_wait_for",
        description=translate("tool.wait_for.description", context.language),
    )
    def wait_for(session_id: str, condition: WaitCondition) -> dict:
        try:
            return service.wait_for(session_id, condition)
        except AcceptanceError as error:
            return error.to_response(language=context.language)

    @server.tool(
        name="miniapp_assert_page_path",
        description=translate("tool.assert_page_path.description", context.language),
    )
    def assert_page_path(session_id: str, expected_path: str) -> dict:
        try:
            return service.assert_page_path(session_id, expected_path)
        except AcceptanceError as error:
            return error.to_response(language=context.language)

    @server.tool(
        name="miniapp_assert_element_text",
        description=translate("tool.assert_element_text.description", context.language),
    )
    def assert_element_text(session_id: str, locator: Locator, expected_text: str) -> dict:
        try:
            return service.assert_element_text(session_id, locator, expected_text)
        except AcceptanceError as error:
            return error.to_response(language=context.language)

    @server.tool(
        name="miniapp_assert_element_visible",
        description=translate("tool.assert_element_visible.description", context.language),
    )
    def assert_element_visible(session_id: str, locator: Locator) -> dict:
        try:
            return service.assert_element_visible(session_id, locator)
        except AcceptanceError as error:
            return error.to_response(language=context.language)
