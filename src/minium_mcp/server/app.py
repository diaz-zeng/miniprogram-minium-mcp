"""MCP Server 应用入口。"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from minium_mcp.domain.service_context import build_service_context
from minium_mcp.server.tools import register_action_tools, register_session_tools
from minium_mcp.support.i18n import translate


def build_server(
    config_path: str | None = None,
    log_level_override: str | None = None,
) -> FastMCP:
    """构建 MCP Server 实例。"""
    context = build_service_context(
        config_path=config_path,
        log_level_override=log_level_override,
    )
    context.logger.debug(translate("server.context_built", context.language))

    server = FastMCP(
        name="minium-mcp",
        instructions=translate("server.instructions", context.language),
    )
    register_session_tools(server, context)
    register_action_tools(server, context)
    return server


def serve(
    transport: str = "stdio",
    config_path: str | None = None,
    log_level_override: str | None = None,
) -> None:
    """按约定的传输方式启动服务。"""
    if transport != "stdio":
        context = build_service_context(
            config_path=config_path,
            log_level_override=log_level_override,
        )
        raise ValueError(translate("server.transport_unsupported", context.language))

    server = build_server(
        config_path=config_path,
        log_level_override=log_level_override,
    )
    server.run()
