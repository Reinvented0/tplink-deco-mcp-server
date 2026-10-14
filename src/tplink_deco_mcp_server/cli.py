"""Command-line entry point: read the router settings and serve over stdio or HTTP."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import TYPE_CHECKING

from .router import RouterSession, RouterSettings
from .server import SERVER_NAME, build_server

if TYPE_CHECKING:
    from collections.abc import Sequence

_LOG_LEVELS: tuple[str, ...] = ("DEBUG", "INFO", "WARNING", "ERROR")


def main(argv: Sequence[str] | None = None) -> None:
    """Run the server until the client disconnects or the process is stopped."""
    arguments = _parse_arguments(argv)
    # stdout carries the JSON-RPC stream over stdio, so every log line goes to stderr.
    logging.basicConfig(
        stream=sys.stderr,
        level=arguments.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        settings = RouterSettings.from_environment(os.environ)
    except ValueError as exception:
        sys.exit(str(exception))

    server = build_server(RouterSession(settings))
    if arguments.transport == "stdio":
        server.run("stdio")
    else:
        server.run("streamable-http", host=arguments.host, port=arguments.port)


def _parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=SERVER_NAME,
        description="MCP server for TP-Link Deco mesh routers. "
        "Reads DECO_HOST, DECO_PASSWORD, DECO_USERNAME and DECO_TIMEOUT from the environment.",
    )
    parser.add_argument("--transport", choices=("stdio", "streamable-http"), default="stdio")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind address (streamable-http).")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (streamable-http).")
    parser.add_argument("--log-level", choices=_LOG_LEVELS, default="INFO")
    return parser.parse_args(argv)
