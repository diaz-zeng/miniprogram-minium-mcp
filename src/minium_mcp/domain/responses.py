"""统一响应构造。"""

from __future__ import annotations

from typing import Any

from minium_mcp.support.i18n import translate


def success_response(
    language: str,
    message_key: str,
    data: dict[str, Any] | None = None,
    **message_params: Any,
) -> dict[str, Any]:
    """构造统一成功响应。"""
    payload = {
        "ok": True,
        "message": translate(message_key, language, **message_params),
    }
    if data:
        payload.update(data)
    return payload
