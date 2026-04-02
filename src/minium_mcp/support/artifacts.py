"""产物目录管理。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


class ArtifactManager:
    """管理截图和调试产物目录。"""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def ensure_base_dir(self) -> Path:
        """确保基础产物目录存在。"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        return self.base_dir

    def ensure_session_dir(self, session_id: str) -> Path:
        """确保会话目录存在。"""
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def next_screenshot_path(self, session_id: str, prefix: str = "screenshot") -> Path:
        """生成下一张截图的落盘路径。"""
        session_dir = self.ensure_session_dir(session_id)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return session_dir / f"{prefix}-{timestamp}.png"

