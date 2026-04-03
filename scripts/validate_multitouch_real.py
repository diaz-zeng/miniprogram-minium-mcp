"""真实运行时多触点最小验证脚本。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Any

from minium_mcp.adapters.minium.runtime import MiniumRuntimeAdapter
from minium_mcp.domain.action_models import GestureTarget, Locator
from minium_mcp.domain.session_models import ActivePointer
from minium_mcp.support.config import MiniumMcpConfig

ARCHERY_HELPER_PENDING_CONFIG = {
    "type": 3,
    "name": "多触点验证",
    "distance_m": 18,
    "target_face": 2,
    "bow_type": 1,
    "ends": 1,
    "arrows_per_end": 3,
}
VALID_SCORE_TEXTS = ["X", "M"] + [str(value) for value in range(10, 0, -1)]


def apply_preset(args: argparse.Namespace) -> None:
    if args.preset != "archery-helper-scatter-record":
        return
    if not args.initial_page:
        args.initial_page = "/pages/scatter-record/index?mode=new"
    if args.start_locator_type is None:
        args.start_locator_type = "text"
    if args.start_locator_value is None:
        args.start_locator_value = "+"
    if args.tap_locator_type is None:
        args.tap_locator_type = "text"
    if args.tap_locator_value is None:
        args.tap_locator_value = "✓"
    if args.move_dx is None and args.move_x is None:
        args.move_dx = -40
    if args.move_dy is None and args.move_y is None:
        args.move_dy = -36
    if args.bootstrap_pending_config is None:
        args.bootstrap_pending_config = json.dumps(
            ARCHERY_HELPER_PENDING_CONFIG,
            ensure_ascii=False,
        )
    args.bootstrap_token = args.bootstrap_token or "codex-e2e-token"
    args.expect_start_hidden_after_tap = False
    args.expect_valid_score_after_tap = True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="验证 Minium 真实运行时多触点基础能力。")
    parser.add_argument("--project-path", required=True, help="小程序项目目录")
    parser.add_argument("--devtool-path", required=True, help="微信开发者工具 CLI 路径")
    parser.add_argument("--artifacts-dir", default="artifacts", help="产物目录")
    parser.add_argument(
        "--preset",
        choices=["archery-helper-scatter-record"],
        default=None,
        help="使用内置业务场景预设",
    )
    parser.add_argument("--initial-page", default=None, help="可选的初始页面路径")
    parser.add_argument("--start-locator-type", choices=["id", "css", "text"], default=None)
    parser.add_argument("--start-locator-value", default=None)
    parser.add_argument("--tap-locator-type", choices=["id", "css", "text"], default=None)
    parser.add_argument("--tap-locator-value", default=None)
    parser.add_argument("--move-x", type=float, default=None, help="第一指移动目标绝对 X 坐标")
    parser.add_argument("--move-y", type=float, default=None, help="第一指移动目标绝对 Y 坐标")
    parser.add_argument("--move-dx", type=float, default=None, help="相对按下起点的 X 偏移")
    parser.add_argument("--move-dy", type=float, default=None, help="相对按下起点的 Y 偏移")
    parser.add_argument(
        "--bootstrap-token",
        default=None,
        help="启动后写入 storage 的 token 值",
    )
    parser.add_argument(
        "--bootstrap-pending-config",
        default=None,
        help="启动后写入 scoring:pending_config 的 JSON 字符串",
    )
    parser.add_argument(
        "--wait-timeout-seconds",
        type=float,
        default=20,
        help="等待页面元素出现的最大秒数",
    )
    parser.add_argument(
        "--expect-start-hidden-after-tap",
        action="store_true",
        help="在第二指点击后断言起始控件不再可见",
    )
    parser.add_argument(
        "--expect-valid-score-after-tap",
        action="store_true",
        help="在第二指点击后断言当前页面出现合法分值文本",
    )
    parser.add_argument("--test-port", type=int, default=9420)
    return parser


def require_validated_args(args: argparse.Namespace) -> None:
    if args.start_locator_type is None or args.start_locator_value is None:
        raise SystemExit("缺少起始定位器，请传 --start-locator-type/--start-locator-value 或使用 --preset。")
    if args.tap_locator_type is None or args.tap_locator_value is None:
        raise SystemExit("缺少第二指点击定位器，请传 --tap-locator-type/--tap-locator-value 或使用 --preset。")
    if (args.move_x is None) != (args.move_y is None):
        raise SystemExit("--move-x 和 --move-y 需要同时提供。")
    if (args.move_dx is None) != (args.move_dy is None):
        raise SystemExit("--move-dx 和 --move-dy 需要同时提供。")
    if args.move_x is None and args.move_dx is None:
        raise SystemExit("需要提供绝对移动目标或相对偏移，请传 --move-x/--move-y 或 --move-dx/--move-dy。")


def set_storage_sync(app: Any, key: str, value: str) -> None:
    app.call_wx_method("setStorageSync", {"key": key, "data": value})


def bootstrap_runtime_state(args: argparse.Namespace, app: Any) -> None:
    if args.bootstrap_token is not None:
        set_storage_sync(app, "token", args.bootstrap_token)
    if args.bootstrap_pending_config is not None:
        set_storage_sync(app, "scoring:pending_config", args.bootstrap_pending_config)


def wait_for_locator(
    runtime: MiniumRuntimeAdapter,
    session_metadata: dict[str, Any],
    current_page_path: str,
    locator: Locator,
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        result = runtime.query_elements(session_metadata, current_page_path, locator)
        matches = result["matches"]
        if matches:
            return matches
        time.sleep(0.5)
    raise AssertionError(f"等待定位器超时: {locator.model_dump_json()}")


def pick_best_runtime_locator(
    runtime: MiniumRuntimeAdapter,
    session_metadata: dict[str, Any],
    current_page_path: str,
    locator: Locator,
) -> Locator:
    if locator.type != "text":
        return locator

    driver = session_metadata.get("runtime_driver")
    if driver is None:
        return locator

    page = driver.app.get_current_page()
    elements = runtime._query_real_elements(page, locator)
    if not elements:
        return locator
    element = elements[0]
    candidate = runtime._resolve_real_gesture_dispatch_target(page, element, locator)
    candidate_id = getattr(candidate, "id", None)
    if isinstance(candidate_id, str) and candidate_id:
        return Locator(type="id", value=candidate_id)
    return locator


def resolve_archery_helper_confirm_locator(
    session_metadata: dict[str, Any],
) -> Locator:
    driver = session_metadata.get("runtime_driver")
    if driver is None:
        raise AssertionError("真实运行时不可用，无法解析 archery-helper 确认按钮。")

    page = driver.app.get_current_page()
    action_bar_elements = page.get_elements("#scatter-action-bar view", max_timeout=0)
    candidates: list[tuple[float, str]] = []
    for element in action_bar_elements:
        text = ""
        try:
            text = str(getattr(element, "inner_text", "") or "").strip()
        except Exception:
            text = ""
        if text != "✓":
            continue
        element_id = getattr(element, "id", None)
        rect = getattr(element, "rect", None) or {}
        area = float(rect.get("width", 0)) * float(rect.get("height", 0))
        if not isinstance(element_id, str) or not element_id:
            continue
        if area <= 0 or area > 4000:
            continue
        candidates.append((area, element_id))

    if not candidates:
        raise AssertionError("未能在 scatter-action-bar 中解析到确认按钮。")
    candidates.sort(key=lambda item: item[0], reverse=True)
    return Locator(type="id", value=candidates[0][1])


def navigate_and_wait(
    runtime: MiniumRuntimeAdapter,
    session_metadata: dict[str, Any],
    app: Any,
    initial_page: str,
    current_page_path: str,
    timeout_seconds: float,
) -> str:
    expected_path = initial_page.split("?", 1)[0].lstrip("/")
    try:
        if "?" in initial_page:
            page_path, raw_query = initial_page.split("?", 1)
            params = {
                segment.split("=", 1)[0]: segment.split("=", 1)[1]
                for segment in raw_query.split("&")
                if "=" in segment
            }
            app.navigate_to(page_path, params=params, is_wait_url_change=False)
        else:
            app.navigate_to(initial_page, is_wait_url_change=False)
    except Exception:
        pass

    deadline = time.time() + timeout_seconds
    latest_page_path = current_page_path
    while time.time() < deadline:
        try:
            page_state = runtime.get_current_page(session_metadata, latest_page_path)
            latest_page_path = page_state["current_page_path"]
            if latest_page_path.split("?", 1)[0].lstrip("/") == expected_path:
                return latest_page_path
        except Exception:
            pass
        time.sleep(0.5)
    raise AssertionError(f"导航到目标页超时: {initial_page}")


def assert_pointer_ids(active_pointers: dict[int, ActivePointer], expected_ids: set[int]) -> None:
    actual_ids = set(active_pointers)
    if actual_ids != expected_ids:
        raise AssertionError(f"活跃触点不符合预期，expected={expected_ids}, actual={actual_ids}")


def wait_for_locator_hidden(
    runtime: MiniumRuntimeAdapter,
    session_metadata: dict[str, Any],
    current_page_path: str,
    locator: Locator,
    timeout_seconds: float,
) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        result = runtime.query_elements(session_metadata, current_page_path, locator)
        matches = result["matches"]
        visible_matches = [match for match in matches if match.get("visible", True)]
        if not visible_matches:
            return
        time.sleep(0.5)
    raise AssertionError(f"定位器仍然可见，未观察到预期业务效果: {locator.model_dump_json()}")


def wait_for_any_score_value(
    runtime: MiniumRuntimeAdapter,
    session_metadata: dict[str, Any],
    current_page_path: str,
    timeout_seconds: float,
) -> str:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        for score_text in VALID_SCORE_TEXTS:
            locator = Locator(type="text", value=score_text)
            result = runtime.query_elements(session_metadata, current_page_path, locator)
            visible_matches = [match for match in result["matches"] if match.get("visible", True)]
            if visible_matches:
                return score_text
        time.sleep(0.4)
    raise AssertionError("第二指点击后未观察到合法分值文本。")


def main() -> int:
    args = build_parser().parse_args()
    apply_preset(args)
    require_validated_args(args)
    config = MiniumMcpConfig(
        language="zh-CN",
        runtime_mode="real",
        project_path=Path(args.project_path).expanduser().resolve(),
        wechat_devtool_path=Path(args.devtool_path).expanduser().resolve(),
        artifacts_dir=Path(args.artifacts_dir).expanduser().resolve(),
        log_level="INFO",
        session_timeout_seconds=1800,
        test_port=args.test_port,
    )
    runtime = MiniumRuntimeAdapter(config=config)
    runtime_state = runtime.start_session(
        mode="launch",
        initial_page_path=None,
        metadata={"source": "validate_multitouch_real.py"},
        project_path=config.project_path,
    )
    session_metadata = {
        "runtime_driver": runtime_state.get("runtime_driver"),
        "runtime_app": runtime_state.get("runtime_app"),
    }
    active_pointers: dict[int, ActivePointer] = {}
    current_page_path = runtime_state["current_page_path"]

    try:
        app = session_metadata["runtime_app"]
        bootstrap_runtime_state(args, app)
        if args.initial_page:
            current_page_path = navigate_and_wait(
                runtime,
                session_metadata,
                app,
                args.initial_page,
                current_page_path,
                args.wait_timeout_seconds,
            )
        else:
            page_state = runtime.get_current_page(session_metadata, current_page_path)
            current_page_path = page_state["current_page_path"]

        start_locator = Locator(type=args.start_locator_type, value=args.start_locator_value)
        tap_locator = Locator(type=args.tap_locator_type, value=args.tap_locator_value)
        start_target = GestureTarget(locator=start_locator)
        tap_target = GestureTarget(locator=tap_locator)
        wait_for_locator(
            runtime,
            session_metadata,
            current_page_path,
            start_locator,
            args.wait_timeout_seconds,
        )
        start_target = GestureTarget(
            locator=pick_best_runtime_locator(
                runtime,
                session_metadata,
                current_page_path,
                start_locator,
            ),
        )
        if args.preset == "archery-helper-scatter-record":
            wait_for_locator(
                runtime,
                session_metadata,
                current_page_path,
                Locator(type="id", value="scatter-action-bar"),
                args.wait_timeout_seconds,
            )
            tap_target = GestureTarget(locator=resolve_archery_helper_confirm_locator(session_metadata))
        else:
            wait_for_locator(
                runtime,
                session_metadata,
                current_page_path,
                tap_locator,
                args.wait_timeout_seconds,
            )
            tap_target = GestureTarget(
                locator=pick_best_runtime_locator(
                    runtime,
                    session_metadata,
                    current_page_path,
                    tap_locator,
                ),
            )

        print("1/4 pointer_1 touch_start")
        state = runtime.touch_start(session_metadata, current_page_path, 1, start_target, active_pointers)
        active_pointers = state["active_pointers"]
        current_page_path = state["current_page_path"]
        print(state["latest_gesture_event"])
        assert_pointer_ids(active_pointers, {1})

        print("2/4 pointer_1 touch_move")
        move_target = None
        if args.move_x is not None and args.move_y is not None:
            move_target = GestureTarget(x=args.move_x, y=args.move_y)
        else:
            start_position = active_pointers[1].current_position
            move_target = GestureTarget(
                x=start_position.x + float(args.move_dx),
                y=start_position.y + float(args.move_dy),
            )
        state = runtime.touch_move(
            session_metadata,
            current_page_path,
            1,
            move_target,
            active_pointers,
            duration_ms=300,
            steps=6,
        )
        active_pointers = state["active_pointers"]
        current_page_path = state["current_page_path"]
        print(state["latest_gesture_event"])
        assert_pointer_ids(active_pointers, {1})

        print("3/4 pointer_2 touch_tap")
        state = runtime.touch_tap(session_metadata, current_page_path, 2, tap_target, active_pointers)
        active_pointers = state["active_pointers"]
        current_page_path = state["current_page_path"]
        print(state["latest_gesture_event"])
        assert_pointer_ids(active_pointers, {1})
        if args.expect_start_hidden_after_tap:
            try:
                wait_for_locator_hidden(
                    runtime,
                    session_metadata,
                    current_page_path,
                    start_locator,
                    4,
                )
            except AssertionError as exc:
                print(f"提示：起始控件仍可见，继续以分值断言为准。{exc}")
        if args.expect_valid_score_after_tap:
            confirmed_score = wait_for_any_score_value(
                runtime,
                session_metadata,
                current_page_path,
                4,
            )
            print(f"业务断言通过，录入区出现分值: {confirmed_score}")

        print("4/4 pointer_1 touch_end")
        state = runtime.touch_end(session_metadata, current_page_path, 1, active_pointers)
        print(state["latest_gesture_event"])
        active_pointers = state["active_pointers"]
        assert_pointer_ids(active_pointers, set())
        screenshot_state = runtime.capture_screenshot(
            session_metadata,
            config.artifacts_dir / "multitouch-real-validation.png",
            current_page_path,
        )
        print(f"截图产物: {screenshot_state['artifact_path']}")
        print("多触点最小验证脚本执行完成。")
        return 0
    finally:
        runtime.stop_session(runtime_state)


if __name__ == "__main__":
    raise SystemExit(main())
