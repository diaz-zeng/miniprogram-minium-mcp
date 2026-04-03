"""会话领域模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utcnow() -> datetime:
    """统一当前 UTC 时间。"""
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class PointerPosition:
    """触点当前位置。"""

    x: float
    y: float

    def to_dict(self) -> dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
        }


@dataclass(slots=True)
class ActivePointer:
    """会话内活跃触点状态。"""

    pointer_id: int
    current_position: PointerPosition
    origin_target_summary: dict[str, Any]
    status: str = "down"
    started_at: datetime = field(default_factory=utcnow)
    runtime_target: Any = None

    def to_summary(self) -> dict[str, Any]:
        return {
            "pointer_id": self.pointer_id,
            "status": self.status,
            "current_position": self.current_position.to_dict(),
            "origin_target_summary": self.origin_target_summary,
            "started_at": self.started_at.isoformat(),
        }


@dataclass(slots=True)
class AcceptanceSession:
    """单个验收会话的内存态模型。"""

    session_id: str
    created_at: datetime = field(default_factory=utcnow)
    last_active_at: datetime = field(default_factory=utcnow)
    current_page_path: str | None = None
    latest_screenshot_path: str | None = None
    latest_failure_summary: str | None = None
    latest_gesture_event: dict[str, Any] | None = None
    active_pointers: dict[int, ActivePointer] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        """更新最近活跃时间。"""
        self.last_active_at = utcnow()

    def active_pointer_summaries(self) -> list[dict[str, Any]]:
        """返回可序列化的活跃触点摘要。"""
        return [
            pointer.to_summary()
            for _, pointer in sorted(self.active_pointers.items(), key=lambda item: item[0])
        ]
