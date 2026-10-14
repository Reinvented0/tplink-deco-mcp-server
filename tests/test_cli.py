from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from mcp.server.mcpserver import MCPServer

from tplink_deco_mcp_server import cli


@pytest.fixture
def run(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    run = MagicMock()
    monkeypatch.setattr(MCPServer, "run", run)
    monkeypatch.setenv("DECO_HOST", "192.168.68.1")
    monkeypatch.setenv("DECO_PASSWORD", "secret")
    return run


def test_serves_stdio_by_default(run: MagicMock) -> None:
    cli.main([])

    run.assert_called_once_with("stdio")


def test_serves_streamable_http(run: MagicMock) -> None:
    cli.main(["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "9000"])  # noqa: S104 - the container binds every interface

    run.assert_called_once_with("streamable-http", host="0.0.0.0", port=9000)  # noqa: S104 - same bind address


def test_exits_when_settings_are_missing(monkeypatch: pytest.MonkeyPatch, run: MagicMock) -> None:
    monkeypatch.delenv("DECO_PASSWORD")

    with pytest.raises(SystemExit, match="DECO_HOST and DECO_PASSWORD must be set"):
        cli.main([])

    run.assert_not_called()
