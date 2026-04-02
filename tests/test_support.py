"""基础支持模块测试。"""

from __future__ import annotations

from datetime import timedelta
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from minium_mcp.domain.action_models import Locator, WaitCondition
from minium_mcp.domain.action_service import ActionService
from minium_mcp.domain.errors import AcceptanceError
from minium_mcp.domain.session_models import utcnow
from minium_mcp.domain.session_service import SessionService
from minium_mcp.domain.session_repository import SessionRepository
from minium_mcp.adapters.minium.runtime import MiniumRuntimeAdapter
from minium_mcp.support.artifacts import ArtifactManager
from minium_mcp.support.config import MiniumMcpConfig
from minium_mcp.support.i18n import detect_language, translate


def test_artifact_manager_creates_session_dir() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ArtifactManager(Path(temp_dir))
        screenshot_path = manager.next_screenshot_path("session-1")

        assert screenshot_path.parent.exists()
        assert screenshot_path.parent.name == "session-1"
        assert screenshot_path.suffix == ".png"


def test_session_repository_create_and_delete() -> None:
    repository = SessionRepository(timeout_seconds=60)

    session = repository.create(metadata={"source": "test"})

    assert repository.get(session.session_id) is not None
    assert repository.delete(session.session_id) is True
    assert repository.get(session.session_id) is None


def test_i18n_detects_non_chinese_as_english() -> None:
    assert detect_language("en_US.UTF-8") == "en"
    assert detect_language("ja_JP.UTF-8") == "en"
    assert detect_language("zh_CN.UTF-8") == "zh-CN"


def test_i18n_translates_cli_message() -> None:
    assert "启动" in translate("cli.prog_description", "zh-CN")
    assert "Start" in translate("cli.prog_description", "en")


def test_session_service_requires_environment_for_launch() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        config = MiniumMcpConfig(
            language="zh-CN",
            runtime_mode="placeholder",
            project_path=Path(temp_dir) / "missing-project",
            wechat_devtool_path=Path(temp_dir) / "missing-devtool",
            artifacts_dir=Path(temp_dir) / "artifacts",
            log_level="INFO",
            session_timeout_seconds=60,
            test_port=9420,
        )
        service = SessionService(
            repository=SessionRepository(timeout_seconds=60),
            runtime_adapter=MiniumRuntimeAdapter(config=config),
            artifact_manager=ArtifactManager(config.artifacts_dir),
            language="zh-CN",
        )

        try:
            service.create_session(mode="launch")
        except AcceptanceError as error:
            assert error.error_code.value == "ENVIRONMENT_ERROR"
        else:
            raise AssertionError("Expected environment validation to fail")


def test_session_service_can_create_and_capture_with_placeholder_runtime() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "miniapp"
        devtool_path = temp_path / "wechat-devtool"
        artifacts_dir = temp_path / "artifacts"
        project_path.mkdir()
        devtool_path.write_text("placeholder", encoding="utf-8")

        config = MiniumMcpConfig(
            language="en",
            runtime_mode="placeholder",
            project_path=project_path,
            wechat_devtool_path=devtool_path,
            artifacts_dir=artifacts_dir,
            log_level="INFO",
            session_timeout_seconds=60,
            test_port=9420,
        )
        service = SessionService(
            repository=SessionRepository(timeout_seconds=60),
            runtime_adapter=MiniumRuntimeAdapter(config=config),
            artifact_manager=ArtifactManager(config.artifacts_dir),
            language="en",
        )

        created = service.create_session(mode="launch", initial_page_path="pages/home/index")
        session_id = created["session_id"]
        current = service.get_current_page(session_id)
        screenshot = service.capture_screenshot(session_id)

        assert created["ok"] is True
        assert created["current_page_path"] == "pages/home/index"
        assert current["current_page_path"] == "pages/home/index"
        assert Path(screenshot["artifact_paths"][0]).exists()


def test_session_service_can_launch_with_per_call_project_path() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "miniapp"
        devtool_path = temp_path / "wechat-devtool"
        artifacts_dir = temp_path / "artifacts"
        project_path.mkdir()
        devtool_path.write_text("placeholder", encoding="utf-8")

        config = MiniumMcpConfig(
            language="en",
            runtime_mode="placeholder",
            project_path=temp_path / "missing-project",
            wechat_devtool_path=devtool_path,
            artifacts_dir=artifacts_dir,
            log_level="INFO",
            session_timeout_seconds=60,
            test_port=9420,
        )
        service = SessionService(
            repository=SessionRepository(timeout_seconds=60),
            runtime_adapter=MiniumRuntimeAdapter(config=config),
            artifact_manager=ArtifactManager(config.artifacts_dir),
            language="en",
        )

        created = service.create_session(
            mode="launch",
            project_path=str(project_path),
            initial_page_path="pages/home/index",
        )

        assert created["ok"] is True
        assert created["current_page_path"] == "pages/home/index"
        assert created["environment"]["project_path"] == str(project_path.resolve())


def test_action_service_query_click_wait_and_assert() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "miniapp"
        devtool_path = temp_path / "wechat-devtool"
        artifacts_dir = temp_path / "artifacts"
        project_path.mkdir()
        devtool_path.write_text("placeholder", encoding="utf-8")

        config = MiniumMcpConfig(
            language="en",
            runtime_mode="placeholder",
            project_path=project_path,
            wechat_devtool_path=devtool_path,
            artifacts_dir=artifacts_dir,
            log_level="INFO",
            session_timeout_seconds=60,
            test_port=9420,
        )
        repository = SessionRepository(timeout_seconds=60)
        runtime = MiniumRuntimeAdapter(config=config)
        session_service = SessionService(
            repository=repository,
            runtime_adapter=runtime,
            artifact_manager=ArtifactManager(config.artifacts_dir),
            language="en",
        )
        action_service = ActionService(
            repository=repository,
            runtime_adapter=runtime,
            artifact_manager=ArtifactManager(config.artifacts_dir),
            language="en",
        )

        created = session_service.create_session(mode="launch")
        session_id = created["session_id"]

        query = action_service.query_elements(session_id, Locator(type="id", value="login-button"))
        click = action_service.click(session_id, Locator(type="id", value="login-button"))
        input_result = action_service.input_text(
            session_id,
            Locator(type="id", value="search-input"),
            "hello",
        )
        wait = action_service.wait_for(
            session_id,
            WaitCondition(kind="page_path_equals", expected_value="pages/index/index"),
        )
        assert_result = action_service.assert_element_visible(
            session_id,
            Locator(type="id", value="login-button"),
        )

        assert query["count"] == 1
        assert click["ok"] is True
        assert input_result["ok"] is True
        assert wait["ok"] is True
        assert assert_result["ok"] is True


def test_action_service_failure_attaches_artifact() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "miniapp"
        devtool_path = temp_path / "wechat-devtool"
        artifacts_dir = temp_path / "artifacts"
        project_path.mkdir()
        devtool_path.write_text("placeholder", encoding="utf-8")

        config = MiniumMcpConfig(
            language="en",
            runtime_mode="placeholder",
            project_path=project_path,
            wechat_devtool_path=devtool_path,
            artifacts_dir=artifacts_dir,
            log_level="INFO",
            session_timeout_seconds=60,
            test_port=9420,
        )
        repository = SessionRepository(timeout_seconds=60)
        runtime = MiniumRuntimeAdapter(config=config)
        session_service = SessionService(
            repository=repository,
            runtime_adapter=runtime,
            artifact_manager=ArtifactManager(config.artifacts_dir),
            language="en",
        )
        action_service = ActionService(
            repository=repository,
            runtime_adapter=runtime,
            artifact_manager=ArtifactManager(config.artifacts_dir),
            language="en",
        )

        created = session_service.create_session(mode="launch")
        session_id = created["session_id"]

        try:
            action_service.assert_element_visible(
                session_id,
                Locator(type="id", value="hidden-banner"),
            )
        except AcceptanceError as error:
            assert error.error_code.value == "ASSERTION_FAILED"
            assert error.artifacts
            assert Path(error.artifacts[0]).exists()
        else:
            raise AssertionError("Expected assertion failure with evidence")


def test_integration_smoke_chain() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "miniapp"
        devtool_path = temp_path / "wechat-devtool"
        artifacts_dir = temp_path / "artifacts"
        project_path.mkdir()
        devtool_path.write_text("placeholder", encoding="utf-8")

        config = MiniumMcpConfig(
            language="en",
            runtime_mode="placeholder",
            project_path=project_path,
            wechat_devtool_path=devtool_path,
            artifacts_dir=artifacts_dir,
            log_level="INFO",
            session_timeout_seconds=60,
            test_port=9420,
        )
        repository = SessionRepository(timeout_seconds=60)
        runtime = MiniumRuntimeAdapter(config=config)
        artifacts = ArtifactManager(config.artifacts_dir)
        session_service = SessionService(
            repository=repository,
            runtime_adapter=runtime,
            artifact_manager=artifacts,
            language="en",
        )
        action_service = ActionService(
            repository=repository,
            runtime_adapter=runtime,
            artifact_manager=artifacts,
            language="en",
        )

        created = session_service.create_session(mode="launch")
        session_id = created["session_id"]
        current = session_service.get_current_page(session_id)
        query = action_service.query_elements(session_id, Locator(type="id", value="login-button"))
        screenshot = session_service.capture_screenshot(session_id)
        asserted = action_service.assert_page_path(session_id, "pages/index/index")

        assert created["ok"] is True
        assert current["ok"] is True
        assert query["count"] == 1
        assert Path(screenshot["artifact_paths"][0]).exists()
        assert asserted["ok"] is True


def test_session_service_rejects_runtime_override_metadata() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "miniapp"
        devtool_path = temp_path / "wechat-devtool"
        artifacts_dir = temp_path / "artifacts"
        project_path.mkdir()
        devtool_path.write_text("placeholder", encoding="utf-8")

        config = MiniumMcpConfig(
            language="en",
            runtime_mode="placeholder",
            project_path=project_path,
            wechat_devtool_path=devtool_path,
            artifacts_dir=artifacts_dir,
            log_level="INFO",
            session_timeout_seconds=60,
            test_port=9420,
        )
        service = SessionService(
            repository=SessionRepository(timeout_seconds=60),
            runtime_adapter=MiniumRuntimeAdapter(config=config),
            artifact_manager=ArtifactManager(config.artifacts_dir),
            language="en",
        )

        try:
            service.create_session(mode="launch", metadata={"test_port": 9527})
        except AcceptanceError as error:
            assert error.error_code.value == "SESSION_ERROR"
            assert error.message_key == "error.runtime_boundary"
            assert error.details["blocked_keys"] == ["test_port"]
        else:
            raise AssertionError("Expected runtime override metadata to be rejected")


def test_session_service_attach_can_prepare_from_project_path() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "miniapp"
        devtool_path = temp_path / "wechat-devtool"
        artifacts_dir = temp_path / "artifacts"
        project_path.mkdir()
        devtool_path.write_text("placeholder", encoding="utf-8")

        config = MiniumMcpConfig(
            language="en",
            runtime_mode="placeholder",
            project_path=temp_path / "missing-project",
            wechat_devtool_path=devtool_path,
            artifacts_dir=artifacts_dir,
            log_level="INFO",
            session_timeout_seconds=60,
            test_port=9420,
        )
        service = SessionService(
            repository=SessionRepository(timeout_seconds=60),
            runtime_adapter=MiniumRuntimeAdapter(config=config),
            artifact_manager=ArtifactManager(config.artifacts_dir),
            language="en",
        )

        created = service.create_session(mode="attach", project_path=str(project_path))

        assert created["ok"] is True
        assert created["test_port"] == 9420
        assert created["environment"]["project_path"] == str(project_path.resolve())


def test_session_service_releases_runtime_when_expired_session_is_cleaned() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "miniapp"
        devtool_path = temp_path / "wechat-devtool"
        artifacts_dir = temp_path / "artifacts"
        project_path.mkdir()
        devtool_path.write_text("placeholder", encoding="utf-8")

        config = MiniumMcpConfig(
            language="en",
            runtime_mode="placeholder",
            project_path=project_path,
            wechat_devtool_path=devtool_path,
            artifacts_dir=artifacts_dir,
            log_level="INFO",
            session_timeout_seconds=1,
            test_port=9420,
        )
        repository = SessionRepository(timeout_seconds=1)
        runtime = MiniumRuntimeAdapter(config=config)
        service = SessionService(
            repository=repository,
            runtime_adapter=runtime,
            artifact_manager=ArtifactManager(config.artifacts_dir),
            language="en",
        )

        created = service.create_session(mode="launch")
        session_id = created["session_id"]
        session = repository.peek(session_id)
        assert session is not None
        session.last_active_at = utcnow() - timedelta(seconds=5)

        with patch.object(MiniumRuntimeAdapter, "stop_session") as mock_stop:
            try:
                service.get_current_page(session_id)
            except AcceptanceError as error:
                assert error.error_code.value == "SESSION_ERROR"
            else:
                raise AssertionError("Expected expired session access to fail")

        mock_stop.assert_called_once_with(session.metadata)
        assert repository.peek(session_id) is None


def test_runtime_adapter_real_session_prepares_automation_when_project_path_present() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "miniapp"
        devtool_path = temp_path / "wechat-devtool"
        artifacts_dir = temp_path / "artifacts"
        project_path.mkdir()
        (project_path / "project.config.json").write_text("{}", encoding="utf-8")
        devtool_path.write_text("placeholder", encoding="utf-8")

        config = MiniumMcpConfig(
            language="zh-CN",
            runtime_mode="real",
            project_path=None,
            wechat_devtool_path=devtool_path,
            artifacts_dir=artifacts_dir,
            log_level="INFO",
            session_timeout_seconds=60,
            test_port=9420,
        )
        runtime = MiniumRuntimeAdapter(config=config)

        class _FakePage:
            path = "/pages/home/index"
            renderer = "webview"

        class _FakeApp:
            def get_current_page(self) -> _FakePage:
                return _FakePage()

        class _FakeMinium:
            def __init__(self, conf):
                self.conf = conf
                self.app = _FakeApp()

        with (
            patch.object(MiniumRuntimeAdapter, "_prepare_automation_target") as mock_prepare,
            patch.dict("sys.modules", {"minium": SimpleNamespace(Minium=_FakeMinium)}),
        ):
            state = runtime.start_session(
                mode="attach",
                initial_page_path=None,
                metadata={},
                project_path=project_path,
            )

        mock_prepare.assert_called_once_with(project_path=project_path, test_port=9420)
        assert state["backend"] == "minium"
        assert state["current_page_path"] == "pages/home/index"
        assert state["test_port"] == 9420


def test_runtime_click_element_tries_text_ancestors_when_page_does_not_change() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = MiniumMcpConfig(
            language="zh-CN",
            runtime_mode="real",
            project_path=None,
            wechat_devtool_path=temp_path / "wechat-devtool",
            artifacts_dir=temp_path / "artifacts",
            log_level="INFO",
            session_timeout_seconds=60,
            test_port=9420,
        )
        runtime = MiniumRuntimeAdapter(config=config)

        class _FakeSelector:
            def __init__(self, xpath: str) -> None:
                self._xpath = xpath

            def full_selector(self) -> str:
                return self._xpath

        class _FakeElement:
            def __init__(self, xpath: str) -> None:
                self.selector = _FakeSelector(xpath)
                self.element_id = xpath
                self.id = xpath
                self._tag_name = "view"
                self.click_count = 0

            def click(self) -> None:
                self.click_count += 1

            def tap(self) -> None:
                raise AssertionError("不应在本测试中回退到 tap")

            def trigger(self, *_args, **_kwargs) -> None:
                raise AssertionError("不应在本测试中回退到 trigger")

            def dispatch_event(self, *_args, **_kwargs) -> None:
                raise AssertionError("不应在本测试中回退到 dispatch_event")

            @property
            def rect(self) -> dict[str, int]:
                return {"left": 0, "top": 0, "width": 10, "height": 10}

        class _FakePage:
            path = "/pages/home/index"

        class _FakeApp:
            def __init__(self) -> None:
                self._page = _FakePage()

            def get_current_page(self) -> _FakePage:
                return self._page

        child = _FakeElement('//*[normalize-space(string(.))="录入今日撒放"]')
        parent = _FakeElement('//*[normalize-space(string(.))="录入今日撒放"]/..')
        driver = SimpleNamespace(app=_FakeApp())

        with (
            patch.object(MiniumRuntimeAdapter, "_query_real_elements", return_value=[child]),
            patch.object(
                MiniumRuntimeAdapter,
                "_query_xpath_elements",
                side_effect=lambda _page, xpath: [parent] if xpath.endswith("/..") else [],
            ),
        ):
            state = runtime.click_element(
                session_metadata={"runtime_driver": driver},
                current_page_path="pages/home/index",
                locator=Locator(type="text", value="录入今日撒放"),
            )

        assert state["current_page_path"] == "pages/home/index"
        assert child.click_count == 1
        assert parent.click_count == 1


def test_runtime_input_text_uses_descendant_input_when_locator_hits_container() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = MiniumMcpConfig(
            language="zh-CN",
            runtime_mode="real",
            project_path=None,
            wechat_devtool_path=temp_path / "wechat-devtool",
            artifacts_dir=temp_path / "artifacts",
            log_level="INFO",
            session_timeout_seconds=60,
            test_port=9420,
        )
        runtime = MiniumRuntimeAdapter(config=config)

        class _FakeInputElement:
            def __init__(self) -> None:
                self._tag_name = "input"
                self.values: list[str] = []

            def input(self, text: str) -> None:
                self.values.append(text)

        class _FakeContainerElement:
            def __init__(self, child) -> None:
                self._tag_name = "view"
                self.element_id = "container"
                self.id = "container"
                self.selector = SimpleNamespace(full_selector=lambda: "#container")
                self._child = child

            def get_elements(self, selector: str, max_timeout: int = 0):
                assert selector == "input, textarea"
                assert max_timeout == 0
                return [self._child]

        class _FakePage:
            path = "/pages/home/index"

        class _FakeApp:
            def get_current_page(self) -> _FakePage:
                return _FakePage()

        input_child = _FakeInputElement()
        container = _FakeContainerElement(input_child)
        driver = SimpleNamespace(app=_FakeApp())

        with patch.object(MiniumRuntimeAdapter, "_query_real_elements", return_value=[container]):
            state = runtime.input_text(
                session_metadata={"runtime_driver": driver},
                current_page_path="pages/home/index",
                locator=Locator(type="id", value="record-dialog-input"),
                text="12",
            )

        assert state["current_page_path"] == "pages/home/index"
        assert input_child.values == ["12"]
