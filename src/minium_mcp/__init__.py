"""minium-mcp 包入口。"""

def build_server(*args, **kwargs):
    """延迟导入 MCP 相关模块，避免纯领域层使用时强依赖 mcp 包。"""
    from .server.app import build_server as _build_server

    return _build_server(*args, **kwargs)


__all__ = ["build_server"]
