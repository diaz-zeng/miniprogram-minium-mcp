"""本地 stdio MCP Server 启动入口。"""

from __future__ import annotations

import argparse

from .server.app import serve
from .support.i18n import detect_language, translate


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    language = detect_language()
    parser = argparse.ArgumentParser(
        prog="minium-mcp",
        description=translate("cli.prog_description", language),
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio"],
        help=translate("cli.transport_help", language),
    )
    parser.add_argument(
        "--config",
        default=None,
        help=translate("cli.config_help", language),
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help=translate("cli.log_level_help", language),
    )
    return parser.parse_args()


def main() -> None:
    """CLI 主入口。"""
    args = parse_args()
    serve(
        transport=args.transport,
        config_path=args.config,
        log_level_override=args.log_level,
    )


if __name__ == "__main__":
    main()
