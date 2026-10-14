"""Shared fixtures: a mocked SDK client behind a real session and MCP server."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from mcp import Client
from tplink_deco_api import AddressReservationService, ClientService, DecoClient

from tplink_deco_mcp_server import RouterSession, RouterSettings, build_server

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from mcp.types import CallToolResult

    type ToolCaller = Callable[..., Awaitable[CallToolResult]]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def settings() -> RouterSettings:
    return RouterSettings(host="192.168.68.1", password="secret", timeout_seconds=5)


@pytest.fixture
def deco() -> MagicMock:
    client = MagicMock(spec=DecoClient)
    client.clients = MagicMock(spec=ClientService)
    client.address_reservations = MagicMock(spec=AddressReservationService)
    return client


@pytest.fixture
def router(settings: RouterSettings, deco: MagicMock) -> RouterSession:
    return RouterSession(settings, client_factory=lambda _settings: deco)


@pytest.fixture
def call_tool(router: RouterSession) -> ToolCaller:
    server = build_server(router)

    async def call(tool_name: str, /, **arguments: object) -> CallToolResult:
        async with Client(server) as client:
            return await client.call_tool(tool_name, arguments)

    return call
