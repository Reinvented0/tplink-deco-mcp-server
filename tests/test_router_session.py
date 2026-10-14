from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from tplink_deco_api import ApiError, AuthenticationError, DecoClient, TransportError

from tplink_deco_mcp_server import RouterSession

if TYPE_CHECKING:
    from tplink_deco_mcp_server import RouterSettings


class _Factory:
    def __init__(self, *clients: MagicMock) -> None:
        self._clients = list(clients)
        self.opened = 0

    def __call__(self, _settings: RouterSettings) -> DecoClient:
        self.opened += 1
        return self._clients.pop(0)


def _client() -> MagicMock:
    return MagicMock(spec=DecoClient)


def test_reuses_the_session_between_calls(settings: RouterSettings) -> None:
    client = _client()
    factory = _Factory(client)
    session = RouterSession(settings, client_factory=factory)

    session.run("read", lambda deco: deco.get_performance())
    session.run("read", lambda deco: deco.get_performance())

    assert factory.opened == 1
    client.login.assert_called_once_with()
    assert client.get_performance.call_count == 2


def test_logs_in_again_when_the_router_drops_the_session(settings: RouterSettings) -> None:
    first, second = _client(), _client()
    first.get_performance.side_effect = [None, ApiError(-1)]
    second.get_performance.return_value = "fresh"
    factory = _Factory(first, second)
    session = RouterSession(settings, client_factory=factory)
    session.run("read", lambda deco: deco.get_performance())

    result = session.run("read", lambda deco: deco.get_performance())

    assert result == "fresh"
    assert factory.opened == 2


def test_does_not_retry_a_genuine_failure(settings: RouterSettings) -> None:
    client = _client()
    client.get_performance.side_effect = [None, TransportError("boom", status_code=500)]
    factory = _Factory(client)
    session = RouterSession(settings, client_factory=factory)
    session.run("read", lambda deco: deco.get_performance())

    with pytest.raises(ToolError, match="Failed to read performance: boom"):
        session.run("read performance", lambda deco: deco.get_performance())

    assert factory.opened == 1


def test_drops_the_session_after_a_failure(settings: RouterSettings) -> None:
    broken, healthy = _client(), _client()
    broken.get_performance.side_effect = TimeoutError()
    factory = _Factory(broken, healthy)
    session = RouterSession(settings, client_factory=factory)

    with pytest.raises(ToolError, match="did not answer within 5s"):
        session.run("read performance", lambda deco: deco.get_performance())
    session.run("read performance", lambda deco: deco.get_performance())

    assert factory.opened == 2
    healthy.get_performance.assert_called_once_with()


def test_reports_rejected_credentials(settings: RouterSettings) -> None:
    client = _client()
    client.login.side_effect = AuthenticationError("Failed to login")
    session = RouterSession(settings, client_factory=_Factory(client))

    with pytest.raises(ToolError, match="the router rejected the credentials"):
        session.run("list clients", lambda deco: deco.get_client_list())


def test_turns_invalid_input_into_a_tool_error(settings: RouterSettings) -> None:
    client = _client()
    client.clients.remove.side_effect = ValueError("Failed to parse MAC address: 'x'")
    factory = _Factory(client, _client())
    session = RouterSession(settings, client_factory=factory)

    with pytest.raises(ToolError, match="Failed to parse MAC address"):
        session.run("remove client", lambda deco: deco.clients.remove("x"))
    session.run("read", lambda deco: deco.get_performance())

    assert factory.opened == 1
