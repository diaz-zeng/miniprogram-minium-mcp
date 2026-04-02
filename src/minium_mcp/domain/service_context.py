"""服务装配上下文。"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging

from minium_mcp.adapters.minium.runtime import MiniumRuntimeAdapter
from minium_mcp.support.artifacts import ArtifactManager
from minium_mcp.support.config import MiniumMcpConfig, load_config
from minium_mcp.support.i18n import translate
from minium_mcp.support.logging import configure_logging

from .session_repository import SessionRepository
from .session_service import SessionService


@dataclass(slots=True)
class ServiceContext:
    """应用运行时依赖容器。"""

    config: MiniumMcpConfig
    logger: logging.Logger
    artifact_manager: ArtifactManager
    session_repository: SessionRepository
    runtime_adapter: MiniumRuntimeAdapter
    session_service: SessionService

    @property
    def language(self) -> str:
        """当前服务输出语言。"""
        return self.config.language


@lru_cache(maxsize=4)
def _build_cached_service_context(
    config_path: str | None,
    log_level_override: str | None,
) -> ServiceContext:
    config = load_config(config_path=config_path, log_level_override=log_level_override)
    logger = configure_logging(config.log_level)
    artifact_manager = ArtifactManager(config.artifacts_dir)
    session_repository = SessionRepository(timeout_seconds=config.session_timeout_seconds)
    runtime_adapter = MiniumRuntimeAdapter(config=config)
    session_service = SessionService(
        repository=session_repository,
        runtime_adapter=runtime_adapter,
        artifact_manager=artifact_manager,
        language=config.language,
    )

    artifact_manager.ensure_base_dir()
    logger.debug(translate("server.context_initialized", config.language))

    return ServiceContext(
        config=config,
        logger=logger,
        artifact_manager=artifact_manager,
        session_repository=session_repository,
        runtime_adapter=runtime_adapter,
        session_service=session_service,
    )


def build_service_context(
    config_path: str | None = None,
    log_level_override: str | None = None,
) -> ServiceContext:
    """构建或复用运行时上下文。"""
    return _build_cached_service_context(config_path, log_level_override)
