"""日志初始化。"""

from __future__ import annotations

import logging


def configure_logging(level: str) -> logging.Logger:
    """配置基础日志。"""
    normalized_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=normalized_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("minium_mcp")
    logger.setLevel(normalized_level)
    return logger

