"""动作、等待与断言服务层。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from minium_mcp.adapters.minium.runtime import MiniumRuntimeAdapter
from minium_mcp.support.artifacts import ArtifactManager

from .action_models import GestureTarget, Locator, WaitCondition
from .errors import AcceptanceError, ErrorCode
from .responses import success_response
from .session_repository import SessionRepository


@dataclass(slots=True)
class ActionService:
    """动作与断言服务。"""

    repository: SessionRepository
    runtime_adapter: MiniumRuntimeAdapter
    artifact_manager: ArtifactManager
    language: str

    def query_elements(self, session_id: str, locator: Locator) -> dict:
        session = self._require_session(session_id)
        query_state = self.runtime_adapter.query_elements(
            session.metadata,
            session.current_page_path,
            locator,
        )
        session.current_page_path = query_state["current_page_path"]
        self.repository.update(session)

        return success_response(
            self.language,
            "action.query.success",
            data={
                "session_id": session_id,
                "locator": locator.model_dump(),
                "matches": query_state["matches"],
                "count": len(query_state["matches"]),
                "current_page_path": session.current_page_path,
            },
        )

    def click(self, session_id: str, locator: Locator) -> dict:
        session = self._require_session(session_id)
        try:
            action_state = self.runtime_adapter.click_element(
                session.metadata,
                session.current_page_path,
                locator,
            )
        except AcceptanceError as error:
            raise self._attach_evidence(session, error, locator=locator)

        session.current_page_path = action_state["current_page_path"]
        self.repository.update(session)
        return success_response(
            self.language,
            "action.click.success",
            data={
                "session_id": session_id,
                "locator": locator.model_dump(),
                "current_page_path": session.current_page_path,
            },
        )

    def input_text(self, session_id: str, locator: Locator, text: str) -> dict:
        session = self._require_session(session_id)
        try:
            action_state = self.runtime_adapter.input_text(
                session.metadata,
                session.current_page_path,
                locator,
                text,
            )
        except AcceptanceError as error:
            raise self._attach_evidence(session, error, locator=locator)

        session.current_page_path = action_state["current_page_path"]
        self.repository.update(session)
        return success_response(
            self.language,
            "action.input.success",
            data={
                "session_id": session_id,
                "locator": locator.model_dump(),
                "input_text": text,
                "current_page_path": session.current_page_path,
            },
        )

    def wait_for(self, session_id: str, condition: WaitCondition) -> dict:
        session = self._require_session(session_id)
        try:
            wait_state = self.runtime_adapter.wait_for_condition(
                session.metadata,
                session.current_page_path,
                condition,
            )
        except AcceptanceError as error:
            raise self._attach_evidence(
                session,
                error,
                locator=condition.locator,
                extra_details={
                    "condition": condition.kind,
                    "expected_value": condition.expected_value,
                    "timeout_ms": condition.timeout_ms,
                },
            )

        session.current_page_path = wait_state["current_page_path"]
        self.repository.update(session)
        return success_response(
            self.language,
            "action.wait.success",
            data={
                "session_id": session_id,
                "condition": condition.model_dump(),
                "current_page_path": session.current_page_path,
            },
        )

    def touch_start(
        self,
        session_id: str,
        pointer_id: int,
        target: GestureTarget,
    ) -> dict:
        session = self._require_session(session_id)
        try:
            gesture_state = self.runtime_adapter.touch_start(
                session.metadata,
                session.current_page_path,
                pointer_id,
                target,
                session.active_pointers,
            )
        except AcceptanceError as error:
            raise self._attach_evidence(
                session,
                error,
                extra_details={
                    "pointer_id": pointer_id,
                    "target": target.model_dump(),
                    "active_pointers": session.active_pointer_summaries(),
                },
            )

        self._apply_gesture_state(session, gesture_state)
        return success_response(
            self.language,
            "action.touch_start.success",
            data=self._gesture_response_payload(session_id, gesture_state),
        )

    def touch_move(
        self,
        session_id: str,
        pointer_id: int,
        target: GestureTarget,
        duration_ms: int = 0,
        steps: int = 1,
    ) -> dict:
        session = self._require_session(session_id)
        try:
            gesture_state = self.runtime_adapter.touch_move(
                session.metadata,
                session.current_page_path,
                pointer_id,
                target,
                session.active_pointers,
                duration_ms=duration_ms,
                steps=steps,
            )
        except AcceptanceError as error:
            raise self._attach_evidence(
                session,
                error,
                extra_details={
                    "pointer_id": pointer_id,
                    "target": target.model_dump(),
                    "duration_ms": duration_ms,
                    "steps": steps,
                    "active_pointers": session.active_pointer_summaries(),
                },
            )

        self._apply_gesture_state(session, gesture_state)
        payload = self._gesture_response_payload(session_id, gesture_state)
        payload["duration_ms"] = duration_ms
        payload["steps"] = steps
        return success_response(
            self.language,
            "action.touch_move.success",
            data=payload,
        )

    def touch_end(
        self,
        session_id: str,
        pointer_id: int,
    ) -> dict:
        session = self._require_session(session_id)
        try:
            gesture_state = self.runtime_adapter.touch_end(
                session.metadata,
                session.current_page_path,
                pointer_id,
                session.active_pointers,
            )
        except AcceptanceError as error:
            raise self._attach_evidence(
                session,
                error,
                extra_details={
                    "pointer_id": pointer_id,
                    "active_pointers": session.active_pointer_summaries(),
                },
            )

        self._apply_gesture_state(session, gesture_state)
        return success_response(
            self.language,
            "action.touch_end.success",
            data=self._gesture_response_payload(session_id, gesture_state),
        )

    def touch_tap(
        self,
        session_id: str,
        pointer_id: int,
        target: GestureTarget,
    ) -> dict:
        session = self._require_session(session_id)
        try:
            gesture_state = self.runtime_adapter.touch_tap(
                session.metadata,
                session.current_page_path,
                pointer_id,
                target,
                session.active_pointers,
            )
        except AcceptanceError as error:
            raise self._attach_evidence(
                session,
                error,
                extra_details={
                    "pointer_id": pointer_id,
                    "target": target.model_dump(),
                    "active_pointers": session.active_pointer_summaries(),
                },
            )

        self._apply_gesture_state(session, gesture_state)
        return success_response(
            self.language,
            "action.touch_tap.success",
            data=self._gesture_response_payload(session_id, gesture_state),
        )

    def assert_page_path(self, session_id: str, expected_path: str) -> dict:
        session = self._require_session(session_id)
        page_state = self.runtime_adapter.get_current_page(
            session.metadata,
            session.current_page_path,
        )
        actual = page_state["current_page_path"]
        session.current_page_path = actual
        self.repository.update(session)
        if actual != expected_path:
            error = AcceptanceError(
                error_code=ErrorCode.ASSERTION_FAILED,
                message="page path mismatch",
                message_key="assert.page_path.failed",
                details={
                    "expected_value": expected_path,
                    "actual_value": actual,
                    "current_page_path": actual,
                },
            )
            raise self._attach_evidence(session, error)

        return success_response(
            self.language,
            "assert.page_path.success",
            data={
                "session_id": session_id,
                "expected_value": expected_path,
                "actual_value": actual,
            },
        )

    def assert_element_text(
        self,
        session_id: str,
        locator: Locator,
        expected_text: str,
    ) -> dict:
        session = self._require_session(session_id)
        try:
            query_state = self.runtime_adapter.query_elements(
                session.metadata,
                session.current_page_path,
                locator,
            )
        except AcceptanceError as error:
            raise self._attach_evidence(session, error, locator=locator)

        matches = query_state["matches"]
        actual_text = matches[0]["text"] if matches else None
        if actual_text != expected_text:
            error = AcceptanceError(
                error_code=ErrorCode.ASSERTION_FAILED,
                message="element text mismatch",
                message_key="assert.element_text.failed",
                details={
                    "locator": locator.model_dump(),
                    "expected_value": expected_text,
                    "actual_value": actual_text,
                    "current_page_path": query_state["current_page_path"],
                },
            )
            raise self._attach_evidence(session, error, locator=locator)

        session.current_page_path = query_state["current_page_path"]
        self.repository.update(session)
        return success_response(
            self.language,
            "assert.element_text.success",
            data={
                "session_id": session_id,
                "locator": locator.model_dump(),
                "expected_value": expected_text,
                "actual_value": actual_text,
            },
        )

    def assert_element_visible(self, session_id: str, locator: Locator) -> dict:
        session = self._require_session(session_id)
        try:
            query_state = self.runtime_adapter.query_elements(
                session.metadata,
                session.current_page_path,
                locator,
            )
        except AcceptanceError as error:
            raise self._attach_evidence(session, error, locator=locator)

        visible = bool(query_state["matches"] and query_state["matches"][0]["visible"])
        if not visible:
            error = AcceptanceError(
                error_code=ErrorCode.ASSERTION_FAILED,
                message="element not visible",
                message_key="assert.element_visible.failed",
                details={
                    "locator": locator.model_dump(),
                    "actual_value": visible,
                    "current_page_path": query_state["current_page_path"],
                },
            )
            raise self._attach_evidence(session, error, locator=locator)

        session.current_page_path = query_state["current_page_path"]
        self.repository.update(session)
        return success_response(
            self.language,
            "assert.element_visible.success",
            data={
                "session_id": session_id,
                "locator": locator.model_dump(),
                "actual_value": visible,
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

    def _attach_evidence(
        self,
        session,
        error: AcceptanceError,
        locator: Locator | None = None,
        extra_details: dict | None = None,
    ) -> AcceptanceError:
        target_path = self.artifact_manager.next_screenshot_path(session.session_id, prefix="failure")
        screenshot_state = self.runtime_adapter.capture_screenshot(
            session_metadata=session.metadata,
            target_path=target_path,
            current_page_path=session.current_page_path,
        )
        session.latest_screenshot_path = str(target_path)
        session.current_page_path = screenshot_state["current_page_path"]
        session.latest_failure_summary = error.message_key or error.message
        self.repository.update(session)

        merged_details = {
            **error.details,
            "current_page_path": session.current_page_path,
        }
        if locator is not None:
            merged_details["locator"] = locator.model_dump()
        if extra_details:
            merged_details.update(extra_details)

        return AcceptanceError(
            error_code=error.error_code,
            message=error.message,
            details=merged_details,
            artifacts=[*error.artifacts, str(target_path)],
            message_key=error.message_key,
            message_params=error.message_params,
        )

    def _apply_gesture_state(self, session, gesture_state: dict) -> None:
        session.current_page_path = gesture_state["current_page_path"]
        session.active_pointers = gesture_state["active_pointers"]
        session.latest_gesture_event = gesture_state["latest_gesture_event"]
        self.repository.update(session)

    @staticmethod
    def _gesture_response_payload(session_id: str, gesture_state: dict) -> dict[str, object]:
        return {
            "session_id": session_id,
            "pointer_id": gesture_state["pointer_id"],
            "event_type": gesture_state["event_type"],
            "resolved_target": gesture_state["resolved_target"],
            "active_pointers": gesture_state["active_pointer_summaries"],
            "current_page_path": gesture_state["current_page_path"],
            "latest_gesture_event": gesture_state["latest_gesture_event"],
        }
