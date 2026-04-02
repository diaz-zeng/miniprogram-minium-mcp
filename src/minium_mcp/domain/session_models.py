"""会话领域模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utcnow() -> datetime:
    """统一当前 UTC 时间。"""
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class AcceptanceSession:
    """单个验收会话的内存态模型。"""

    session_id: str
    created_at: datetime = field(default_factory=utcnow)
    last_active_at: datetime = field(default_factory=utcnow)
    current_page_path: str | None = None
    latest_screenshot_path: str | None = None
    latest_failure_summary: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        """更新最近活跃时间。"""
        self.last_active_at = utcnow()

