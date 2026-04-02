"""会话类 MCP tools。"""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from minium_mcp.domain.errors import AcceptanceError
from minium_mcp.domain.service_context import ServiceContext
from minium_mcp.support.i18n import translate


def register_session_tools(server: FastMCP, context: ServiceContext) -> None:
    """注册会话相关 tools。"""
    service = context.session_service

    @server.tool(
        name="miniapp_create_session",
        description=translate("tool.create_session.description", context.language),
    )
    def create_session(
        mode: Literal["launch", "attach"] = "launch",
        initial_page_path: str | None = None,
        metadata: dict[str, Any] | None = None,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        try:
            return service.create_session(
                mode=mode,
                initial_page_path=initial_page_path,
                metadata=metadata,
                project_path=project_path,
            )
        except AcceptanceError as error:
            return error.to_response(language=context.language)

    @server.tool(
        name="miniapp_close_session",
        description=translate("tool.close_session.description", context.language),
    )
    def close_session(session_id: str) -> dict[str, Any]:
        try:
            return service.close_session(session_id)
        except AcceptanceError as error:
            return error.to_response(language=context.language)

    @server.tool(
        name="miniapp_get_current_page",
        description=translate("tool.get_current_page.description", context.language),
    )
    def get_current_page(session_id: str) -> dict[str, Any]:
        try:
            return service.get_current_page(session_id)
        except AcceptanceError as error:
            return error.to_response(language=context.language)

    @server.tool(
        name="miniapp_capture_screenshot",
        description=translate("tool.capture_screenshot.description", context.language),
    )
    def capture_screenshot(
        session_id: str,
        prefix: str = "screenshot",
    ) -> dict[str, Any]:
        try:
            return service.capture_screenshot(session_id, prefix=prefix)
        except AcceptanceError as error:
            return error.to_response(language=context.language)
