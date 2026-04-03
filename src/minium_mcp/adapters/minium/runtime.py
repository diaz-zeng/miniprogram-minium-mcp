"""Minium 运行时适配器。"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
import subprocess
import time
from typing import Any, Literal

from minium_mcp.domain.action_models import GestureTarget, Locator, WaitCondition
from minium_mcp.domain.errors import AcceptanceError, ErrorCode
from minium_mcp.domain.session_models import ActivePointer, PointerPosition
from minium_mcp.support.config import MiniumMcpConfig

SessionMode = Literal["launch", "attach"]
_MAX_ACTIVE_POINTERS = 2

_PLACEHOLDER_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9o9l9x8AAAAASUVORK5CYII="
)


@dataclass(slots=True)
class MiniumRuntimeAdapter:
    """底层 Minium 运行时适配器。

    当前阶段先负责环境探测与依赖整合，后续再补会话创建、页面读取和动作能力。
    """

    config: MiniumMcpConfig

    def describe_environment(
        self,
        project_path: Path | None = None,
    ) -> dict[str, str | bool | None]:
        """输出当前运行环境摘要。"""
        resolved_project_path = project_path or self.config.project_path
        devtool_path = self.config.wechat_devtool_path
        return {
            "project_path": str(resolved_project_path) if resolved_project_path else None,
            "project_exists": bool(resolved_project_path and resolved_project_path.exists()),
            "wechat_devtool_path": str(devtool_path) if devtool_path else None,
            "wechat_devtool_exists": bool(devtool_path and devtool_path.exists()),
            "test_port": str(self.config.test_port),
        }

    def validate_environment(self) -> dict[str, str | bool | None]:
        """校验本地环境并返回摘要。"""
        return self.describe_environment()

    def start_session(
        self,
        mode: SessionMode,
        initial_page_path: str | None,
        metadata: dict[str, Any],
        project_path: Path | None = None,
    ) -> dict[str, Any]:
        """启动或附着会话。

        当前阶段先返回可工作的占位运行时状态，后续再切换到真实 Minium 实现。
        """
        environment = self.describe_environment(project_path=project_path)
        self._ensure_required_environment(mode, environment, project_path=project_path)
        if self.config.runtime_mode in {"real", "auto"}:
            return self._start_real_session(
                mode=mode,
                initial_page_path=initial_page_path,
                metadata=metadata,
                environment=environment,
                project_path=project_path,
            )
        return self._start_placeholder_session(
            initial_page_path=initial_page_path,
            metadata=metadata,
            environment=environment,
            project_path=project_path,
        )

    def stop_session(self, session_metadata: dict[str, Any]) -> None:
        """关闭会话。"""
        driver = session_metadata.get("runtime_driver")
        if driver is not None:
            try:
                driver.shutdown()
            except Exception:
                pass

    def get_current_page(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
    ) -> dict[str, Any]:
        """读取当前页面。"""
        driver = session_metadata.get("runtime_driver")
        if driver is not None:
            page = driver.app.get_current_page()
            normalized = self._normalize_page_path(getattr(page, "path", current_page_path))
            return {
                "current_page_path": normalized,
                "page_summary": {
                    "path": normalized,
                    "source": "minium-runtime",
                    "renderer": getattr(page, "renderer", None),
                },
            }
        resolved_page = current_page_path or "pages/index/index"
        return {
            "current_page_path": resolved_page,
            "page_summary": {
                "path": resolved_page,
                "source": "placeholder-runtime",
            },
        }

    def capture_screenshot(
        self,
        session_metadata: dict[str, Any],
        target_path: Path,
        current_page_path: str | None,
    ) -> dict[str, Any]:
        """生成占位截图。"""
        driver = session_metadata.get("runtime_driver")
        if driver is not None:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            driver.app.screen_shot(save_path=str(target_path))
            current_page = driver.app.get_current_page()
            return {
                "current_page_path": self._normalize_page_path(getattr(current_page, "path", current_page_path)),
                "artifact_path": str(target_path),
                "source": "minium-runtime",
            }
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(_PLACEHOLDER_PNG)
        return {
            "current_page_path": current_page_path or "pages/index/index",
            "artifact_path": str(target_path),
            "source": "placeholder-runtime",
        }

    def query_elements(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
        locator: Locator,
    ) -> dict[str, Any]:
        """查询元素。"""
        driver = session_metadata.get("runtime_driver")
        if driver is not None:
            page = driver.app.get_current_page()
            elements = self._query_real_elements(page, locator)
            return {
                "current_page_path": self._normalize_page_path(getattr(page, "path", current_page_path)),
                "matches": [self._serialize_real_element(element, locator) for element in elements],
            }
        page_path = current_page_path or "pages/index/index"
        elements = self._placeholder_elements(page_path)
        matches = [element for element in elements if self._matches(locator, element)]

        if locator.index >= len(matches):
            return {
                "current_page_path": page_path,
                "matches": [],
            }

        return {
            "current_page_path": page_path,
            "matches": [matches[locator.index]],
        }

    def click_element(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
        locator: Locator,
    ) -> dict[str, Any]:
        """点击元素。"""
        driver = session_metadata.get("runtime_driver")
        if driver is not None:
            page = driver.app.get_current_page()
            elements = self._query_real_elements(page, locator)
            element = self._require_match(elements, locator)
            before_page_path = self._normalize_page_path(getattr(page, "path", current_page_path))
            candidates = self._collect_real_click_candidates(page, element, locator)
            last_error: Exception | None = None

            for index, candidate in enumerate(candidates):
                try:
                    self._click_real_candidate(candidate)
                except Exception as exc:
                    last_error = exc
                    continue

                next_page = driver.app.get_current_page()
                next_page_path = self._normalize_page_path(
                    getattr(next_page, "path", current_page_path)
                )
                is_last_candidate = index == len(candidates) - 1
                should_continue = (
                    locator.type == "text"
                    and len(candidates) > 1
                    and next_page_path == before_page_path
                    and not is_last_candidate
                )
                if should_continue:
                    continue

                return {"current_page_path": next_page_path}

            if last_error is None:
                last_error = RuntimeError("no click candidate available")
            raise AcceptanceError(
                error_code=ErrorCode.ACTION_ERROR,
                message="element not interactable",
                message_key="error.element_not_interactable",
                details={"locator": locator.model_dump(), "cause": str(last_error)},
            ) from last_error
        query_state = self.query_elements(session_metadata, current_page_path, locator)
        match = self._require_match(query_state["matches"], locator)
        if not match["visible"] or not match["enabled"]:
            raise AcceptanceError(
                error_code=ErrorCode.ACTION_ERROR,
                message="element not interactable",
                message_key="error.element_not_interactable",
                details={"locator": locator.model_dump()},
            )
        return {"current_page_path": query_state["current_page_path"]}

    def input_text(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
        locator: Locator,
        text: str,
    ) -> dict[str, Any]:
        """向元素输入文本。"""
        driver = session_metadata.get("runtime_driver")
        if driver is not None:
            page = driver.app.get_current_page()
            elements = self._query_real_elements(page, locator)
            element = self._require_match(elements, locator)
            input_target = self._resolve_real_input_target(page, element, locator)
            try:
                input_target.input(text)
            except Exception as exc:
                raise AcceptanceError(
                    error_code=ErrorCode.ACTION_ERROR,
                    message="element not interactable",
                    message_key="error.element_not_interactable",
                    details={
                        "locator": locator.model_dump(),
                        "cause": str(exc),
                        "target_tag": getattr(input_target, "_tag_name", None),
                    },
                ) from exc
            return {
                "current_page_path": self._normalize_page_path(getattr(page, "path", current_page_path)),
            }
        _ = text
        query_state = self.query_elements(session_metadata, current_page_path, locator)
        match = self._require_match(query_state["matches"], locator)
        if not match["editable"] or not match["visible"]:
            raise AcceptanceError(
                error_code=ErrorCode.ACTION_ERROR,
                message="element not interactable",
                message_key="error.element_not_interactable",
                details={"locator": locator.model_dump()},
            )
        return {"current_page_path": query_state["current_page_path"]}

    def wait_for_condition(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
        condition: WaitCondition,
    ) -> dict[str, Any]:
        """等待条件成立。"""
        driver = session_metadata.get("runtime_driver")
        if driver is not None:
            deadline = time.time() + (condition.timeout_ms / 1000)
            while time.time() < deadline:
                page = driver.app.get_current_page()
                page_path = self._normalize_page_path(getattr(page, "path", current_page_path))
                if condition.kind == "page_path_equals" and page_path == condition.expected_value:
                    return {"current_page_path": page_path}
                if condition.kind in {"element_exists", "element_visible"}:
                    elements = self._query_real_elements(page, condition.locator)
                    if condition.kind == "element_exists" and elements:
                        return {"current_page_path": page_path}
                    if condition.kind == "element_visible" and elements:
                        summary = self._serialize_real_element(elements[0], condition.locator)
                        if summary["visible"]:
                            return {"current_page_path": page_path}
                time.sleep(0.25)
            raise AcceptanceError(
                error_code=ErrorCode.ACTION_ERROR,
                message="wait timeout",
                message_key="error.wait_timeout",
                details={
                    "condition": condition.kind,
                    "expected_value": condition.expected_value,
                    "timeout_ms": condition.timeout_ms,
                },
            )
        page_path = current_page_path or "pages/index/index"

        if condition.kind == "page_path_equals":
            if page_path == condition.expected_value:
                return {"current_page_path": page_path}
        elif condition.kind == "element_exists":
            query_state = self.query_elements(session_metadata, page_path, condition.locator)
            if query_state["matches"]:
                return {"current_page_path": page_path}
        elif condition.kind == "element_visible":
            query_state = self.query_elements(session_metadata, page_path, condition.locator)
            if query_state["matches"] and query_state["matches"][0]["visible"]:
                return {"current_page_path": page_path}

        raise AcceptanceError(
            error_code=ErrorCode.ACTION_ERROR,
            message="wait timeout",
            message_key="error.wait_timeout",
            details={
                "condition": condition.kind,
                "expected_value": condition.expected_value,
                "timeout_ms": condition.timeout_ms,
            },
        )

    def touch_start(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
        pointer_id: int,
        target: GestureTarget,
        active_pointers: dict[int, ActivePointer],
    ) -> dict[str, Any]:
        """按下并保持一个触点。"""
        if pointer_id in active_pointers:
            raise AcceptanceError(
                error_code=ErrorCode.ACTION_ERROR,
                message="pointer already active",
                message_key="error.pointer_already_active",
                details={"pointer_id": pointer_id},
            )
        if len(active_pointers) >= _MAX_ACTIVE_POINTERS:
            raise AcceptanceError(
                error_code=ErrorCode.ACTION_ERROR,
                message="pointer limit exceeded",
                message_key="error.pointer_limit_exceeded",
                details={
                    "pointer_id": pointer_id,
                    "active_pointer_ids": sorted(active_pointers.keys()),
                    "limit": _MAX_ACTIVE_POINTERS,
                },
            )

        if session_metadata.get("runtime_driver") is not None:
            return self._real_touch_start(
                session_metadata=session_metadata,
                current_page_path=current_page_path,
                pointer_id=pointer_id,
                target=target,
                active_pointers=active_pointers,
            )
        return self._placeholder_touch_start(
            current_page_path=current_page_path,
            pointer_id=pointer_id,
            target=target,
            active_pointers=active_pointers,
        )

    def touch_move(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
        pointer_id: int,
        target: GestureTarget,
        active_pointers: dict[int, ActivePointer],
        duration_ms: int = 0,
        steps: int = 1,
    ) -> dict[str, Any]:
        """移动一个已按下的触点。"""
        if pointer_id not in active_pointers:
            raise AcceptanceError(
                error_code=ErrorCode.ACTION_ERROR,
                message="pointer is not active",
                message_key="error.pointer_not_active",
                details={"pointer_id": pointer_id},
            )

        if session_metadata.get("runtime_driver") is not None:
            return self._real_touch_move(
                session_metadata=session_metadata,
                current_page_path=current_page_path,
                pointer_id=pointer_id,
                target=target,
                active_pointers=active_pointers,
                duration_ms=duration_ms,
                steps=steps,
            )
        return self._placeholder_touch_move(
            current_page_path=current_page_path,
            pointer_id=pointer_id,
            target=target,
            active_pointers=active_pointers,
            duration_ms=duration_ms,
            steps=steps,
        )

    def touch_end(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
        pointer_id: int,
        active_pointers: dict[int, ActivePointer],
    ) -> dict[str, Any]:
        """释放一个已按下的触点。"""
        if pointer_id not in active_pointers:
            raise AcceptanceError(
                error_code=ErrorCode.ACTION_ERROR,
                message="pointer is not active",
                message_key="error.pointer_not_active",
                details={"pointer_id": pointer_id},
            )

        if session_metadata.get("runtime_driver") is not None:
            return self._real_touch_end(
                session_metadata=session_metadata,
                current_page_path=current_page_path,
                pointer_id=pointer_id,
                active_pointers=active_pointers,
            )
        return self._placeholder_touch_end(
            current_page_path=current_page_path,
            pointer_id=pointer_id,
            active_pointers=active_pointers,
        )

    def touch_tap(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
        pointer_id: int,
        target: GestureTarget,
        active_pointers: dict[int, ActivePointer],
    ) -> dict[str, Any]:
        """执行一个短按点击，不保留触点。"""
        if pointer_id in active_pointers:
            raise AcceptanceError(
                error_code=ErrorCode.ACTION_ERROR,
                message="pointer already active",
                message_key="error.pointer_already_active",
                details={"pointer_id": pointer_id},
            )
        if len(active_pointers) >= _MAX_ACTIVE_POINTERS:
            raise AcceptanceError(
                error_code=ErrorCode.ACTION_ERROR,
                message="pointer limit exceeded",
                message_key="error.pointer_limit_exceeded",
                details={
                    "pointer_id": pointer_id,
                    "active_pointer_ids": sorted(active_pointers.keys()),
                    "limit": _MAX_ACTIVE_POINTERS,
                },
            )

        if session_metadata.get("runtime_driver") is not None:
            return self._real_touch_tap(
                session_metadata=session_metadata,
                current_page_path=current_page_path,
                pointer_id=pointer_id,
                target=target,
                active_pointers=active_pointers,
            )
        return self._placeholder_touch_tap(
            current_page_path=current_page_path,
            pointer_id=pointer_id,
            target=target,
            active_pointers=active_pointers,
        )

    def _real_touch_start(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
        pointer_id: int,
        target: GestureTarget,
        active_pointers: dict[int, ActivePointer],
    ) -> dict[str, Any]:
        page, page_path = self._get_real_page_and_path(session_metadata, current_page_path)
        next_active_pointers = self._clone_active_pointers(active_pointers)
        dispatch_target, resolved_target, position = self._resolve_real_gesture_target(
            page=page,
            target=target,
            active_pointers=next_active_pointers,
            pointer_id=pointer_id,
        )
        changed_touch = self._position_to_touch(position, pointer_id)
        touches = self._build_touches_payload(next_active_pointers, changed_touch=changed_touch)
        self._dispatch_real_touch_event(
            dispatch_target,
            "touchstart",
            touches=touches,
            changed_touches=[changed_touch],
        )
        next_active_pointers[pointer_id] = ActivePointer(
            pointer_id=pointer_id,
            current_position=position,
            origin_target_summary=resolved_target,
            runtime_target=dispatch_target,
        )
        return self._gesture_state(
            current_page_path=page_path,
            event_type="touch_start",
            pointer_id=pointer_id,
            resolved_target=resolved_target,
            active_pointers=next_active_pointers,
        )

    def _real_touch_move(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
        pointer_id: int,
        target: GestureTarget,
        active_pointers: dict[int, ActivePointer],
        duration_ms: int,
        steps: int,
    ) -> dict[str, Any]:
        page, page_path = self._get_real_page_and_path(session_metadata, current_page_path)
        next_active_pointers = self._clone_active_pointers(active_pointers)
        dispatch_target, resolved_target, destination = self._resolve_real_gesture_target(
            page=page,
            target=target,
            active_pointers=next_active_pointers,
            pointer_id=pointer_id,
        )
        pointer = next_active_pointers[pointer_id]
        route = self._interpolate_positions(pointer.current_position, destination, steps=max(steps, 1))
        sleep_seconds = max(duration_ms, 0) / 1000 / max(len(route), 1) if duration_ms > 0 else 0
        for position in route:
            changed_touch = self._position_to_touch(position, pointer_id)
            pointer.current_position = position
            if target.locator is not None:
                pointer.runtime_target = dispatch_target
            touches = self._build_touches_payload(next_active_pointers)
            self._dispatch_real_touch_event(
                pointer.runtime_target or dispatch_target,
                "touchmove",
                touches=touches,
                changed_touches=[changed_touch],
            )
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
        return self._gesture_state(
            current_page_path=page_path,
            event_type="touch_move",
            pointer_id=pointer_id,
            resolved_target=resolved_target,
            active_pointers=next_active_pointers,
        )

    def _real_touch_end(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
        pointer_id: int,
        active_pointers: dict[int, ActivePointer],
    ) -> dict[str, Any]:
        _page, page_path = self._get_real_page_and_path(session_metadata, current_page_path)
        next_active_pointers = self._clone_active_pointers(active_pointers)
        pointer = next_active_pointers[pointer_id]
        changed_touch = self._position_to_touch(pointer.current_position, pointer_id)
        remaining = {
            candidate_id: candidate
            for candidate_id, candidate in next_active_pointers.items()
            if candidate_id != pointer_id
        }
        touches = self._build_touches_payload(remaining)
        self._dispatch_real_touch_event(
            pointer.runtime_target,
            "touchend",
            touches=touches,
            changed_touches=[changed_touch],
        )
        next_active_pointers.pop(pointer_id, None)
        return self._gesture_state(
            current_page_path=page_path,
            event_type="touch_end",
            pointer_id=pointer_id,
            resolved_target={
                "type": "release",
                "position": pointer.current_position.to_dict(),
            },
            active_pointers=next_active_pointers,
        )

    def _real_touch_tap(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
        pointer_id: int,
        target: GestureTarget,
        active_pointers: dict[int, ActivePointer],
    ) -> dict[str, Any]:
        page, page_path = self._get_real_page_and_path(session_metadata, current_page_path)
        next_active_pointers = self._clone_active_pointers(active_pointers)
        dispatch_target, resolved_target, position = self._resolve_real_gesture_target(
            page=page,
            target=target,
            active_pointers=next_active_pointers,
            pointer_id=pointer_id,
        )
        changed_touch = self._position_to_touch(position, pointer_id)
        touches = self._build_touches_payload(next_active_pointers, changed_touch=changed_touch)
        self._dispatch_real_touch_event(
            dispatch_target,
            "touchstart",
            touches=touches,
            changed_touches=[changed_touch],
        )
        self._dispatch_real_touch_event(
            dispatch_target,
            "touchend",
            touches=self._build_touches_payload(next_active_pointers),
            changed_touches=[changed_touch],
        )
        self._dispatch_real_tap_event(dispatch_target)
        return self._gesture_state(
            current_page_path=page_path,
            event_type="touch_tap",
            pointer_id=pointer_id,
            resolved_target=resolved_target,
            active_pointers=next_active_pointers,
        )

    def _placeholder_touch_start(
        self,
        current_page_path: str | None,
        pointer_id: int,
        target: GestureTarget,
        active_pointers: dict[int, ActivePointer],
    ) -> dict[str, Any]:
        page_path = current_page_path or "pages/index/index"
        next_active_pointers = self._clone_active_pointers(active_pointers)
        resolved_target, position = self._resolve_placeholder_gesture_target(page_path, target, next_active_pointers, pointer_id)
        next_active_pointers[pointer_id] = ActivePointer(
            pointer_id=pointer_id,
            current_position=position,
            origin_target_summary=resolved_target,
        )
        return self._gesture_state(
            current_page_path=page_path,
            event_type="touch_start",
            pointer_id=pointer_id,
            resolved_target=resolved_target,
            active_pointers=next_active_pointers,
        )

    def _placeholder_touch_move(
        self,
        current_page_path: str | None,
        pointer_id: int,
        target: GestureTarget,
        active_pointers: dict[int, ActivePointer],
        duration_ms: int,
        steps: int,
    ) -> dict[str, Any]:
        _ = duration_ms
        _ = steps
        page_path = current_page_path or "pages/index/index"
        next_active_pointers = self._clone_active_pointers(active_pointers)
        resolved_target, position = self._resolve_placeholder_gesture_target(page_path, target, next_active_pointers, pointer_id)
        next_active_pointers[pointer_id].current_position = position
        return self._gesture_state(
            current_page_path=page_path,
            event_type="touch_move",
            pointer_id=pointer_id,
            resolved_target=resolved_target,
            active_pointers=next_active_pointers,
        )

    def _placeholder_touch_end(
        self,
        current_page_path: str | None,
        pointer_id: int,
        active_pointers: dict[int, ActivePointer],
    ) -> dict[str, Any]:
        page_path = current_page_path or "pages/index/index"
        next_active_pointers = self._clone_active_pointers(active_pointers)
        pointer = next_active_pointers.pop(pointer_id)
        return self._gesture_state(
            current_page_path=page_path,
            event_type="touch_end",
            pointer_id=pointer_id,
            resolved_target={
                "type": "release",
                "position": pointer.current_position.to_dict(),
            },
            active_pointers=next_active_pointers,
        )

    def _placeholder_touch_tap(
        self,
        current_page_path: str | None,
        pointer_id: int,
        target: GestureTarget,
        active_pointers: dict[int, ActivePointer],
    ) -> dict[str, Any]:
        page_path = current_page_path or "pages/index/index"
        next_active_pointers = self._clone_active_pointers(active_pointers)
        resolved_target, _position = self._resolve_placeholder_gesture_target(page_path, target, next_active_pointers, pointer_id)
        return self._gesture_state(
            current_page_path=page_path,
            event_type="touch_tap",
            pointer_id=pointer_id,
            resolved_target=resolved_target,
            active_pointers=next_active_pointers,
        )

    @staticmethod
    def _clone_active_pointers(active_pointers: dict[int, ActivePointer]) -> dict[int, ActivePointer]:
        return {
            pointer_id: ActivePointer(
                pointer_id=pointer.pointer_id,
                status=pointer.status,
                current_position=PointerPosition(
                    x=pointer.current_position.x,
                    y=pointer.current_position.y,
                ),
                origin_target_summary=dict(pointer.origin_target_summary),
                started_at=pointer.started_at,
                runtime_target=pointer.runtime_target,
            )
            for pointer_id, pointer in active_pointers.items()
        }

    def _get_real_page_and_path(
        self,
        session_metadata: dict[str, Any],
        current_page_path: str | None,
    ) -> tuple[Any, str]:
        driver = session_metadata["runtime_driver"]
        page = driver.app.get_current_page()
        return page, self._normalize_page_path(getattr(page, "path", current_page_path))

    def _resolve_real_gesture_target(
        self,
        page: Any,
        target: GestureTarget,
        active_pointers: dict[int, ActivePointer],
        pointer_id: int,
    ) -> tuple[Any, dict[str, Any], PointerPosition]:
        if target.locator is not None:
            elements = self._query_real_elements(page, target.locator)
            element = self._require_match(elements, target.locator)
            dispatch_target = self._resolve_real_gesture_dispatch_target(page, element, target.locator)
            position = self._real_element_center(element)
            return (
                dispatch_target,
                {
                    "type": "locator",
                    "locator": target.locator.model_dump(),
                    "position": position.to_dict(),
                    "tag": getattr(element, "_tag_name", None),
                    "id": getattr(element, "id", None),
                    "dispatch_tag": getattr(dispatch_target, "_tag_name", None),
                    "dispatch_id": getattr(dispatch_target, "id", None),
                },
                position,
            )
        position = PointerPosition(x=float(target.x), y=float(target.y))
        dispatch_target = self._resolve_runtime_dispatch_target(page, active_pointers, pointer_id)
        return (
            dispatch_target,
            {
                "type": "coordinates",
                "position": position.to_dict(),
            },
            position,
        )

    def _resolve_placeholder_gesture_target(
        self,
        page_path: str,
        target: GestureTarget,
        active_pointers: dict[int, ActivePointer],
        pointer_id: int,
    ) -> tuple[dict[str, Any], PointerPosition]:
        if target.locator is not None:
            query_state = self.query_elements({}, page_path, target.locator)
            match = self._require_match(query_state["matches"], target.locator)
            position = PointerPosition(
                x=float(match.get("center_x", 0)),
                y=float(match.get("center_y", 0)),
            )
            return (
                {
                    "type": "locator",
                    "locator": target.locator.model_dump(),
                    "position": position.to_dict(),
                    "id": match.get("id"),
                },
                position,
            )
        if pointer_id in active_pointers:
            active_pointers[pointer_id].current_position = PointerPosition(x=float(target.x), y=float(target.y))
        position = PointerPosition(x=float(target.x), y=float(target.y))
        return (
            {
                "type": "coordinates",
                "position": position.to_dict(),
            },
            position,
        )

    @staticmethod
    def _resolve_runtime_dispatch_target(
        page: Any,
        active_pointers: dict[int, ActivePointer],
        pointer_id: int,
    ) -> Any:
        if pointer_id in active_pointers and active_pointers[pointer_id].runtime_target is not None:
            return active_pointers[pointer_id].runtime_target
        for _, pointer in sorted(active_pointers.items(), key=lambda item: item[0]):
            if pointer.runtime_target is not None:
                return pointer.runtime_target
        return page

    def _resolve_real_gesture_dispatch_target(
        self,
        page: Any,
        element: Any,
        locator: Locator,
    ) -> Any:
        if locator.type != "text":
            return element

        candidates = self._collect_real_click_candidates(page, element, locator)
        base_identity = self._real_element_identity(element)
        base_id = getattr(element, "id", None)
        base_element_id = getattr(element, "element_id", None)
        base_rect = getattr(element, "rect", None) or {}
        base_area = max(float(base_rect.get("width", 0)) * float(base_rect.get("height", 0)), 0.0)

        better_candidates: list[tuple[float, Any]] = []
        for candidate in candidates:
            candidate_identity = self._real_element_identity(candidate)
            if candidate_identity == base_identity:
                continue
            if getattr(candidate, "id", None) == base_id:
                continue
            if getattr(candidate, "element_id", None) == base_element_id:
                continue
            rect = getattr(candidate, "rect", None) or {}
            area = max(float(rect.get("width", 0)) * float(rect.get("height", 0)), 0.0)
            if area <= 0 or area > max(base_area * 4, 20_000):
                continue
            better_candidates.append((area, candidate))

        if not better_candidates:
            return element
        better_candidates.sort(key=lambda item: item[0])
        return better_candidates[0][1]

    def _dispatch_real_touch_event(
        self,
        target: Any,
        event_type: str,
        touches: list[dict[str, float | int]],
        changed_touches: list[dict[str, float | int]],
    ) -> None:
        if callable(getattr(target, "dispatch_event", None)):
            target.dispatch_event(
                event_type,
                touches=touches,
                change_touches=changed_touches,
                detail={},
            )
            return
        if event_type == "touchstart" and callable(getattr(target, "touch_start", None)):
            target.touch_start(touches, changed_touches)
            return
        if event_type == "touchmove" and callable(getattr(target, "touch_move", None)):
            target.touch_move(touches, changed_touches)
            return
        if event_type == "touchend" and callable(getattr(target, "touch_end", None)):
            target.touch_end(changed_touches)
            return
        if callable(getattr(target, "trigger_events", None)):
            target.trigger_events(
                [
                    {
                        "type": event_type,
                        "touches": touches,
                        "changedTouches": changed_touches,
                        "interval": 0,
                    }
                ]
            )
            return
        raise AcceptanceError(
            error_code=ErrorCode.ACTION_ERROR,
            message="gesture target cannot dispatch touch event",
            message_key="error.element_not_interactable",
            details={"event_type": event_type},
        )

    def _dispatch_real_tap_event(self, target: Any) -> None:
        if callable(getattr(target, "trigger", None)):
            target.trigger("tap", {})
            return
        if callable(getattr(target, "dispatch_event", None)):
            target.dispatch_event("tap", detail={})
            return
        if callable(getattr(target, "trigger_events", None)):
            target.trigger_events([{"type": "tap", "detail": {}, "interval": 0}])
            return

    @staticmethod
    def _build_touches_payload(
        active_pointers: dict[int, ActivePointer],
        changed_touch: dict[str, float | int] | None = None,
    ) -> list[dict[str, float | int]]:
        touches = [
            MiniumRuntimeAdapter._position_to_touch(pointer.current_position, pointer.pointer_id)
            for _, pointer in sorted(active_pointers.items(), key=lambda item: item[0])
        ]
        if changed_touch is not None and all(touch["identifier"] != changed_touch["identifier"] for touch in touches):
            touches.append(changed_touch)
        return touches

    @staticmethod
    def _position_to_touch(
        position: PointerPosition,
        pointer_id: int,
    ) -> dict[str, float | int]:
        return {
            "identifier": pointer_id,
            "pageX": position.x,
            "pageY": position.y,
            "clientX": position.x,
            "clientY": position.y,
        }

    @staticmethod
    def _interpolate_positions(
        start: PointerPosition,
        destination: PointerPosition,
        steps: int,
    ) -> list[PointerPosition]:
        if steps <= 1:
            return [destination]
        positions: list[PointerPosition] = []
        for index in range(1, steps + 1):
            ratio = index / steps
            positions.append(
                PointerPosition(
                    x=start.x + ((destination.x - start.x) * ratio),
                    y=start.y + ((destination.y - start.y) * ratio),
                )
            )
        return positions

    @staticmethod
    def _gesture_state(
        current_page_path: str,
        event_type: str,
        pointer_id: int,
        resolved_target: dict[str, Any],
        active_pointers: dict[int, ActivePointer],
    ) -> dict[str, Any]:
        active_pointer_summaries = [
            pointer.to_summary()
            for _, pointer in sorted(active_pointers.items(), key=lambda item: item[0])
        ]
        return {
            "current_page_path": current_page_path,
            "event_type": event_type,
            "pointer_id": pointer_id,
            "resolved_target": resolved_target,
            "active_pointers": active_pointers,
            "active_pointer_summaries": active_pointer_summaries,
            "latest_gesture_event": {
                "event_type": event_type,
                "pointer_id": pointer_id,
                "resolved_target": resolved_target,
                "active_pointers": active_pointer_summaries,
            },
        }

    @staticmethod
    def _real_element_center(element: Any) -> PointerPosition:
        rect = getattr(element, "rect", None)
        if not rect:
            raise AcceptanceError(
                error_code=ErrorCode.ACTION_ERROR,
                message="gesture target has no rect",
                message_key="error.element_not_interactable",
                details={"cause": "missing element rect"},
            )
        return PointerPosition(
            x=float(rect["left"] + (rect["width"] / 2)),
            y=float(rect["top"] + (rect["height"] / 2)),
        )

    @staticmethod
    def is_executable(path: Path | None) -> bool:
        """判断路径是否可用。"""
        return bool(path and path.exists())

    def _ensure_required_environment(
        self,
        mode: SessionMode,
        environment: dict[str, str | bool | None],
        project_path: Path | None = None,
    ) -> None:
        devtool_path = self.config.wechat_devtool_path
        resolved_project_path = project_path or self.config.project_path

        if not self.is_executable(devtool_path):
            raise AcceptanceError(
                error_code=ErrorCode.ENVIRONMENT_ERROR,
                message="missing devtool path",
                message_key="error.missing_devtool_path",
                details=environment,
            )

        if mode == "launch" and not self.is_executable(resolved_project_path):
            raise AcceptanceError(
                error_code=ErrorCode.ENVIRONMENT_ERROR,
                message="missing project path",
                message_key="error.missing_project_path",
                details=environment,
            )
        if (
            self._uses_real_runtime()
            and resolved_project_path is not None
            and mode == "launch"
            and not (resolved_project_path / "project.config.json").exists()
        ):
            raise AcceptanceError(
                error_code=ErrorCode.ENVIRONMENT_ERROR,
                message="missing project path",
                message_key="error.missing_project_path",
                details={
                    **environment,
                    "missing_file": str(resolved_project_path / "project.config.json"),
                },
            )

    def _start_real_session(
        self,
        mode: SessionMode,
        initial_page_path: str | None,
        metadata: dict[str, Any],
        environment: dict[str, str | bool | None],
        project_path: Path | None = None,
    ) -> dict[str, Any]:
        try:
            from minium import Minium
        except Exception as exc:
            raise AcceptanceError(
                error_code=ErrorCode.ENVIRONMENT_ERROR,
                message="failed to import minium",
                message_key="error.minium_launch_failed",
                details={**environment, "cause": str(exc)},
            ) from exc

        resolved_project_path = project_path or self.config.project_path
        test_port = self.config.test_port
        if resolved_project_path is not None:
            self._prepare_automation_target(project_path=resolved_project_path, test_port=test_port)

        conf: dict[str, Any] = {
            "project_path": str(resolved_project_path) if mode == "launch" and resolved_project_path else None,
            "dev_tool_path": str(self.config.wechat_devtool_path) if self.config.wechat_devtool_path else None,
            "test_port": test_port,
            "outputs": str(self.config.artifacts_dir),
            "auto_relaunch": False,
            "debug_mode": self._to_minium_log_level(),
        }
        conf = {key: value for key, value in conf.items() if value is not None}
        try:
            driver = Minium(conf)
            app = driver.app
            if initial_page_path:
                app.navigate_to(initial_page_path)
            page = app.get_current_page()
        except Exception as exc:
            raise AcceptanceError(
                error_code=ErrorCode.ENVIRONMENT_ERROR,
                message="failed to connect to minium runtime",
                message_key="error.minium_launch_failed",
                details={**environment, "cause": str(exc), "mode": mode},
            ) from exc

        return {
            "backend": "minium",
            "connected": True,
            "current_page_path": self._normalize_page_path(getattr(page, "path", initial_page_path)),
            "environment": environment,
            "note": "real-runtime",
            "metadata": metadata,
            "runtime_driver": driver,
            "runtime_app": app,
            "test_port": test_port,
        }

    def _start_placeholder_session(
        self,
        initial_page_path: str | None,
        metadata: dict[str, Any],
        environment: dict[str, str | bool | None],
        project_path: Path | None = None,
    ) -> dict[str, Any]:
        return {
            "backend": "placeholder",
            "connected": True,
            "current_page_path": initial_page_path or "pages/index/index",
            "environment": environment,
            "note": "placeholder-runtime",
            "metadata": metadata,
            "test_port": self.config.test_port,
        }

    def _query_real_elements(self, page: Any, locator: Locator) -> list[Any]:
        if locator.type == "id":
            return page.get_elements(f"#{locator.value}", max_timeout=0, index=locator.index)
        if locator.type == "css":
            return page.get_elements(locator.value, max_timeout=0, index=locator.index)
        if locator.type == "text":
            return self._query_real_elements_by_text(page, locator)
        raise AcceptanceError(
            error_code=ErrorCode.ACTION_ERROR,
            message="unsupported locator type",
            message_key="error.unsupported_locator_type",
            details={"locator": locator.model_dump()},
        )

    def _query_real_elements_by_text(self, page: Any, locator: Locator) -> list[Any]:
        target_text = self._normalize_text(locator.value)
        exact_xpath = (
            f"//*[normalize-space(string(.))={self._to_xpath_literal(target_text)}]"
        )
        contains_xpath = (
            f"//*[contains(normalize-space(string(.)), {self._to_xpath_literal(target_text)})]"
        )

        candidates = self._query_xpath_elements(page, exact_xpath)
        if not candidates:
            candidates = self._query_xpath_elements(page, contains_xpath)

        filtered: list[tuple[str, Any]] = []
        seen_keys: set[str] = set()
        for element in candidates:
            normalized_text = self._normalize_text(self._read_element_text(element))
            if not normalized_text or target_text not in normalized_text:
                continue

            element_id = getattr(element, "id", None)
            element_tag = getattr(element, "_tag_name", None)
            dedupe_key = f"{element_id}|{element_tag}|{normalized_text}"
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            filtered.append((normalized_text, element))

        filtered.sort(key=lambda item: (item[0] != target_text, len(item[0])))
        matches = [element for _, element in filtered]
        if locator.index >= len(matches):
            return []
        return [matches[locator.index]]

    def _collect_real_click_candidates(
        self,
        page: Any,
        element: Any,
        locator: Locator,
    ) -> list[Any]:
        candidates = [element]
        if locator.type == "text":
            candidates.extend(self._query_click_ancestors(page, element))

        deduped: list[Any] = []
        seen: set[str] = set()
        for candidate in candidates:
            candidate_key = self._real_element_identity(candidate)
            if candidate_key in seen:
                continue
            seen.add(candidate_key)
            deduped.append(candidate)
        return deduped

    def _resolve_real_input_target(
        self,
        page: Any,
        element: Any,
        locator: Locator,
    ) -> Any:
        for candidate in self._collect_real_input_candidates(page, element, locator):
            if self._supports_real_input(candidate):
                return candidate
            for descendant in self._query_real_input_descendants(candidate):
                if self._supports_real_input(descendant):
                    return descendant
        raise AcceptanceError(
            error_code=ErrorCode.ACTION_ERROR,
            message="element not interactable",
            message_key="error.element_not_interactable",
            details={
                "locator": locator.model_dump(),
                "cause": "no input-capable target found",
                "tag": getattr(element, "_tag_name", None),
            },
        )

    def _collect_real_input_candidates(
        self,
        page: Any,
        element: Any,
        locator: Locator,
    ) -> list[Any]:
        candidates = [element]
        if locator.type == "text":
            candidates.extend(self._query_click_ancestors(page, element))

        deduped: list[Any] = []
        seen: set[str] = set()
        for candidate in candidates:
            candidate_key = self._real_element_identity(candidate)
            if candidate_key in seen:
                continue
            seen.add(candidate_key)
            deduped.append(candidate)
        return deduped

    @staticmethod
    def _supports_real_input(element: Any) -> bool:
        return callable(getattr(type(element), "input", None))

    @staticmethod
    def _query_real_input_descendants(element: Any) -> list[Any]:
        try:
            return element.get_elements("input, textarea", max_timeout=0)
        except TypeError:
            return element.get_elements("input, textarea")
        except Exception:
            return []

    def _query_click_ancestors(
        self,
        page: Any,
        element: Any,
        max_depth: int = 4,
    ) -> list[Any]:
        base_xpath = self._real_element_xpath(element)
        if not base_xpath:
            return []

        ancestors: list[Any] = []
        for depth in range(1, max_depth + 1):
            xpath = base_xpath + ("/.." * depth)
            for ancestor in self._query_xpath_elements(page, xpath):
                ancestors.append(ancestor)
        return ancestors

    def _click_real_candidate(self, element: Any) -> None:
        methods: list[tuple[str, Any]] = [
            ("click", lambda: element.click()),
            ("tap", lambda: element.tap()),
            ("trigger_click", lambda: element.trigger("click", {})),
            ("trigger_tap", lambda: element.trigger("tap", {})),
            ("dispatch_click", lambda: element.dispatch_event("click", detail={})),
            ("touch_sequence", lambda: self._trigger_touch_sequence(element)),
        ]
        last_error: Exception | None = None
        for _, method in methods:
            try:
                method()
                return
            except Exception as exc:
                last_error = exc
        if last_error is None:
            raise RuntimeError("no click method available")
        raise last_error

    def _trigger_touch_sequence(self, element: Any) -> None:
        rect = element.rect
        center_x = rect["left"] + (rect["width"] / 2)
        center_y = rect["top"] + (rect["height"] / 2)
        touch = {
            "identifier": 0,
            "pageX": center_x,
            "pageY": center_y,
            "clientX": center_x,
            "clientY": center_y,
        }
        element.trigger_events(
            [
                {
                    "type": "touchstart",
                    "touches": [touch],
                    "changedTouches": [touch],
                    "interval": 0,
                },
                {
                    "type": "touchend",
                    "changedTouches": [touch],
                    "interval": 0,
                },
                {"type": "tap", "detail": {}, "interval": 0},
            ]
        )

    @staticmethod
    def _real_element_identity(element: Any) -> str:
        selector = getattr(element, "selector", None)
        selector_value = None
        if selector is not None:
            full_selector = getattr(selector, "full_selector", None)
            if callable(full_selector):
                try:
                    selector_value = full_selector()
                except Exception:
                    selector_value = None
        return "|".join(
            [
                str(getattr(element, "element_id", "")),
                str(getattr(element, "id", "")),
                str(getattr(element, "_tag_name", "")),
                str(selector_value or ""),
            ]
        )

    @staticmethod
    def _real_element_xpath(element: Any) -> str | None:
        selector = getattr(element, "selector", None)
        if selector is None:
            return None
        full_selector = getattr(selector, "full_selector", None)
        if callable(full_selector):
            try:
                value = full_selector()
                if isinstance(value, str) and value.startswith("/"):
                    return value
            except Exception:
                return None
        return None

    def _query_xpath_elements(self, page: Any, xpath: str) -> list[Any]:
        try:
            return page.get_elements_by_xpath(xpath, max_timeout=0)
        except TypeError:
            return page.get_elements_by_xpath(xpath)

    @staticmethod
    def _read_element_text(element: Any) -> str:
        try:
            return str(element.inner_text or "")
        except Exception:
            return ""

    @staticmethod
    def _normalize_text(value: str | None) -> str:
        return " ".join(str(value or "").split())

    @staticmethod
    def _to_xpath_literal(value: str) -> str:
        if '"' not in value:
            return f'"{value}"'
        if "'" not in value:
            return f"'{value}'"
        parts = value.split('"')
        segments: list[str] = []
        for index, part in enumerate(parts):
            if part:
                segments.append(f'"{part}"')
            if index != len(parts) - 1:
                segments.append("'\"'")
        return f"concat({', '.join(segments)})"

    def _serialize_real_element(self, element: Any, locator: Locator) -> dict[str, Any]:
        try:
            display, visibility = element.styles(["display", "visibility"])
            visible = display != "none" and visibility != "hidden"
        except Exception:
            visible = True
        try:
            disabled_attr = element.attribute("disabled")[0]
            enabled = disabled_attr in (None, False, "false", "")
        except Exception:
            enabled = True
        try:
            text = element.inner_text
        except Exception:
            text = None
        try:
            value = element.value
        except Exception:
            value = None
        return {
            "id": getattr(element, "id", None),
            "tag": getattr(element, "_tag_name", None),
            "text": text,
            "value": value,
            "visible": visible,
            "enabled": enabled,
            "editable": getattr(element, "_tag_name", None) in {"input", "textarea"},
            "locator": locator.model_dump(),
        }

    @staticmethod
    def _normalize_page_path(path: str | None) -> str:
        if not path:
            return "pages/index/index"
        return str(path).lstrip("/")

    def _to_minium_log_level(self) -> str:
        return {
            "DEBUG": "debug",
            "INFO": "info",
            "WARNING": "warn",
            "ERROR": "error",
        }.get(self.config.log_level.upper(), "info")

    def _uses_real_runtime(self) -> bool:
        return self.config.runtime_mode in {"real", "auto"}

    def _prepare_automation_target(self, project_path: Path, test_port: int) -> None:
        command = [
            str(self.config.wechat_devtool_path),
            "auto",
            "--project",
            str(project_path),
            "--auto-port",
            str(test_port),
            "--lang",
            "zh" if self.config.language == "zh-CN" else "en",
            "--trust-project",
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
        except Exception as exc:
            raise AcceptanceError(
                error_code=ErrorCode.ENVIRONMENT_ERROR,
                message="failed to prepare devtool automation",
                message_key="error.devtool_auto_failed",
                details={
                    "project_path": str(project_path),
                    "test_port": test_port,
                    "cause": str(exc),
                },
            ) from exc

        if completed.returncode != 0:
            raise AcceptanceError(
                error_code=ErrorCode.ENVIRONMENT_ERROR,
                message="failed to prepare devtool automation",
                message_key="error.devtool_auto_failed",
                details={
                    "project_path": str(project_path),
                    "test_port": test_port,
                    "stdout": completed.stdout.strip(),
                    "stderr": completed.stderr.strip(),
                    "returncode": completed.returncode,
                },
            )
        if not self._wait_for_port(test_port, timeout_seconds=20):
            raise AcceptanceError(
                error_code=ErrorCode.ENVIRONMENT_ERROR,
                message="failed to prepare devtool automation",
                message_key="error.devtool_auto_failed",
                details={
                    "project_path": str(project_path),
                    "test_port": test_port,
                    "stdout": completed.stdout.strip(),
                    "stderr": completed.stderr.strip(),
                    "reason": "automation port is not listening",
                },
            )

    @staticmethod
    def _is_port_listening(test_port: int) -> bool:
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            return sock.connect_ex(("127.0.0.1", test_port)) == 0

    def _wait_for_port(self, test_port: int, timeout_seconds: float) -> bool:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if self._is_port_listening(test_port):
                return True
            time.sleep(0.25)
        return False

    @staticmethod
    def _placeholder_elements(page_path: str) -> list[dict[str, Any]]:
        """占位页面元素集合。"""
        return [
            {
                "id": "page-title",
                "css": ".page-title",
                "text": "Minium MCP Demo",
                "visible": True,
                "enabled": False,
                "editable": False,
                "center_x": 160,
                "center_y": 40,
                "page_path": page_path,
            },
            {
                "id": "login-button",
                "css": ".login-button",
                "text": "Login",
                "visible": True,
                "enabled": True,
                "editable": False,
                "center_x": 140,
                "center_y": 120,
                "page_path": page_path,
            },
            {
                "id": "search-input",
                "css": "#search-input",
                "text": "",
                "visible": True,
                "enabled": True,
                "editable": True,
                "center_x": 180,
                "center_y": 220,
                "page_path": page_path,
            },
            {
                "id": "hidden-banner",
                "css": ".hidden-banner",
                "text": "Hidden Banner",
                "visible": False,
                "enabled": False,
                "editable": False,
                "center_x": 160,
                "center_y": 320,
                "page_path": page_path,
            },
        ]

    @staticmethod
    def _matches(locator: Locator, element: dict[str, Any]) -> bool:
        if locator.type == "id":
            return element["id"] == locator.value
        if locator.type == "css":
            return element["css"] == locator.value
        if locator.type == "text":
            return MiniumRuntimeAdapter._normalize_text(element["text"]) == MiniumRuntimeAdapter._normalize_text(locator.value)
        return False

    @staticmethod
    def _require_match(matches: list[dict[str, Any]], locator: Locator) -> dict[str, Any]:
        if not matches:
            raise AcceptanceError(
                error_code=ErrorCode.ACTION_ERROR,
                message="element not found",
                message_key="error.element_not_found",
                details={"locator": locator.model_dump()},
            )
        return matches[0]
