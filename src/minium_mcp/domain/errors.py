"""统一错误模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from minium_mcp.support.i18n import translate


class ErrorCode(StrEnum):
    """统一错误码。"""

    ENVIRONMENT_ERROR = "ENVIRONMENT_ERROR"
    SESSION_ERROR = "SESSION_ERROR"
    ACTION_ERROR = "ACTION_ERROR"
    ASSERTION_FAILED = "ASSERTION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass(slots=True)
class AcceptanceError(Exception):
    """验收流程中的结构化异常。"""

    error_code: ErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    message_key: str | None = None
    message_params: dict[str, Any] = field(default_factory=dict)

    def to_response(self, language: str = "zh-CN") -> dict[str, Any]:
        """转换为后续工具统一可返回的结构。"""
        message = self.message
        if self.message_key:
            message = translate(self.message_key, language, **self.message_params)
        return {
            "ok": False,
            "error_code": self.error_code.value,
            "message": message,
            "details": self.details,
            "artifacts": self.artifacts,
        }
