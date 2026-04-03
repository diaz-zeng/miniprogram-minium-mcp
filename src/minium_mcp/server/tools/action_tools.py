"""动作与断言 MCP tools。"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from minium_mcp.domain.action_models import GestureTarget, Locator, WaitCondition
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
        name="miniapp_touch_start",
        description=translate("tool.touch_start.description", context.language),
    )
    def touch_start(session_id: str, pointer_id: int, target: GestureTarget) -> dict:
        try:
            return service.touch_start(session_id, pointer_id, target)
        except AcceptanceError as error:
            return error.to_response(language=context.language)

    @server.tool(
        name="miniapp_touch_move",
        description=translate("tool.touch_move.description", context.language),
    )
    def touch_move(
        session_id: str,
        pointer_id: int,
        target: GestureTarget,
        duration_ms: int = 0,
        steps: int = 1,
    ) -> dict:
        try:
            return service.touch_move(
                session_id=session_id,
                pointer_id=pointer_id,
                target=target,
                duration_ms=duration_ms,
                steps=steps,
            )
        except AcceptanceError as error:
            return error.to_response(language=context.language)

    @server.tool(
        name="miniapp_touch_end",
        description=translate("tool.touch_end.description", context.language),
    )
    def touch_end(session_id: str, pointer_id: int) -> dict:
        try:
            return service.touch_end(session_id, pointer_id)
        except AcceptanceError as error:
            return error.to_response(language=context.language)

    @server.tool(
        name="miniapp_touch_tap",
        description=translate("tool.touch_tap.description", context.language),
    )
    def touch_tap(session_id: str, pointer_id: int, target: GestureTarget) -> dict:
        try:
            return service.touch_tap(session_id, pointer_id, target)
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
