"""会话服务层。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from minium_mcp.adapters.minium.runtime import MiniumRuntimeAdapter
from minium_mcp.support.artifacts import ArtifactManager

from .errors import AcceptanceError, ErrorCode
from .responses import success_response
from .session_repository import SessionRepository

SessionMode = Literal["launch", "attach"]
_RESERVED_SESSION_METADATA_KEYS = {
    "auto_relaunch",
    "command",
    "debug_mode",
    "dev_tool_path",
    "exec_script",
    "javascript",
    "js",
    "mode",
    "outputs",
    "project_path",
    "runtime_app",
    "runtime_backend",
    "runtime_connected",
    "runtime_driver",
    "runtime_note",
    "script",
    "test_port",
}


@dataclass(slots=True)
class SessionService:
    """会话服务。"""

    repository: SessionRepository
    runtime_adapter: MiniumRuntimeAdapter
    artifact_manager: ArtifactManager
    language: str

    def create_session(
        self,
        mode: SessionMode = "launch",
        initial_page_path: str | None = None,
        metadata: dict[str, Any] | None = None,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """创建一个验收会话。"""
        self._cleanup_expired_sessions()
        session_metadata = self._sanitize_session_metadata(metadata)
        resolved_project_path = self._resolve_project_path(project_path)
        runtime_state = self.runtime_adapter.start_session(
            mode=mode,
            initial_page_path=initial_page_path,
            metadata=session_metadata,
            project_path=resolved_project_path,
        )
        session = self.repository.create(
            metadata={
                **session_metadata,
                "mode": mode,
                "runtime_backend": runtime_state["backend"],
                "runtime_connected": runtime_state["connected"],
                "runtime_driver": runtime_state.get("runtime_driver"),
                "runtime_app": runtime_state.get("runtime_app"),
                "test_port": runtime_state.get("test_port"),
            }
        )
        session.current_page_path = runtime_state["current_page_path"]
        session.metadata["runtime_note"] = runtime_state.get("note")
        self.repository.update(session)

        return success_response(
            self.language,
            "session.created",
            data={
                "session_id": session.session_id,
                "mode": mode,
                "current_page_path": session.current_page_path,
                "environment": runtime_state["environment"],
                "runtime_backend": runtime_state["backend"],
                "runtime_note": runtime_state.get("note"),
                "test_port": runtime_state.get("test_port"),
            },
        )

    def close_session(self, session_id: str) -> dict[str, Any]:
        """关闭一个验收会话。"""
        self._cleanup_expired_sessions()
        session = self._require_session(session_id)
        self.runtime_adapter.stop_session(session.metadata)
        self.repository.delete(session.session_id)

        return success_response(
            self.language,
            "session.closed",
            data={"session_id": session_id},
        )

    def get_current_page(self, session_id: str) -> dict[str, Any]:
        """读取当前页面。"""
        session = self._require_session(session_id)
        page_state = self.runtime_adapter.get_current_page(
            session.metadata,
            session.current_page_path,
        )
        session.current_page_path = page_state["current_page_path"]
        self.repository.update(session)

        return success_response(
            self.language,
            "session.current_page",
            data={
                "session_id": session_id,
                "current_page_path": page_state["current_page_path"],
                "page_summary": page_state["page_summary"],
                "runtime_backend": session.metadata.get("runtime_backend"),
                "runtime_note": session.metadata.get("runtime_note"),
            },
        )

    def capture_screenshot(
        self,
        session_id: str,
        prefix: str = "screenshot",
    ) -> dict[str, Any]:
        """生成当前会话截图。"""
        session = self._require_session(session_id)
        target_path = self.artifact_manager.next_screenshot_path(session_id, prefix=prefix)
        screenshot_state = self.runtime_adapter.capture_screenshot(
            session_metadata=session.metadata,
            target_path=target_path,
            current_page_path=session.current_page_path,
        )
        session.latest_screenshot_path = str(target_path)
        session.current_page_path = screenshot_state["current_page_path"]
        self.repository.update(session)

        return success_response(
            self.language,
            "session.screenshot_created",
            data={
                "session_id": session_id,
                "current_page_path": session.current_page_path,
                "artifact_paths": [str(target_path)],
                "runtime_backend": session.metadata.get("runtime_backend"),
                "runtime_note": session.metadata.get("runtime_note"),
            },
        )

    def _require_session(self, session_id: str):
        self._cleanup_expired_sessions()
        session = self.repository.get(session_id)
        if session is None:
            raise AcceptanceError(
                error_code=ErrorCode.SESSION_ERROR,
                message="invalid session",
                message_key="error.invalid_session",
                details={"session_id": session_id},
            )
        return session

    def _cleanup_expired_sessions(self) -> None:
        for expired_session in self.repository.pop_expired():
            self.runtime_adapter.stop_session(expired_session.metadata)

    def _sanitize_session_metadata(
        self,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not metadata:
            return {}

        blocked_keys = sorted(
            key for key in metadata if key.lower() in _RESERVED_SESSION_METADATA_KEYS
        )
        if blocked_keys:
            raise AcceptanceError(
                error_code=ErrorCode.SESSION_ERROR,
                message="unsupported runtime override",
                message_key="error.runtime_boundary",
                details={
                    "blocked_keys": blocked_keys,
                    "reason": "session metadata cannot override runtime controls",
                },
            )
        return metadata

    @staticmethod
    def _resolve_project_path(project_path: str | None) -> Path | None:
        if project_path in (None, ""):
            return None
        return Path(project_path).expanduser().resolve()
