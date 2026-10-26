from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest
from mcp import Client
from starlette.testclient import TestClient

from tplink_deco_mcp_server import build_server

if TYPE_CHECKING:
    from tplink_deco_mcp_server import RouterSession

_READ_ONLY_TOOLS = {
    "list_deco_nodes",
    "get_router_performance",
    "get_system_log",
    "read_router_form",
    "get_speedtest_result",
    "list_client_connections",
    "get_mesh_placement",
    "get_internet_status",
    "get_wifi_configuration",
    "list_clients",
    "list_blocked_clients",
    "list_address_reservations",
}
_WRITE_TOOLS = {
    "start_speedtest",
    "set_client_roaming",
    "update_client",
    "remove_client",
    "block_client",
    "unblock_client",
    "add_address_reservation",
    "update_address_reservation",
    "remove_address_reservation",
}


@pytest.mark.anyio
async def test_publishes_every_tool_with_its_annotations(router: RouterSession) -> None:
    async with Client(build_server(router)) as client:
        tools = (await client.list_tools()).tools

    assert {tool.name for tool in tools} == _READ_ONLY_TOOLS | _WRITE_TOOLS
    for tool in tools:
        assert tool.title
        assert tool.description
        assert not tool.description.startswith(" ")
        assert tool.annotations is not None
        assert tool.annotations.read_only_hint is (tool.name in _READ_ONLY_TOOLS)


@pytest.mark.anyio
async def test_announces_instructions(router: RouterSession) -> None:
    async with Client(build_server(router)) as client:
        instructions = client.instructions
        server_info = client.server_info

    assert instructions is not None
    assert "list_clients" in instructions
    assert server_info is not None
    assert server_info.name == "tplink-deco-mcp-server"


def test_serves_a_health_endpoint(router: RouterSession) -> None:
    app = build_server(router).streamable_http_app()

    with TestClient(app) as http:
        response = http.get("/healthz")

    assert response.status_code == 200
    assert response.text == "ok"


@pytest.mark.anyio
async def test_publishes_reboot_only_when_allowed(router: RouterSession) -> None:
    async with Client(build_server(router)) as client:
        default_tools = {tool.name for tool in (await client.list_tools()).tools}

    allowed = type(router)(replace(router.settings, allow_reboot=True))
    async with Client(build_server(allowed)) as client:
        reboot = next(
            tool for tool in (await client.list_tools()).tools if tool.name == "reboot_deco_nodes"
        )

    assert "reboot_deco_nodes" not in default_tools
    assert reboot.annotations is not None
    assert reboot.annotations.destructive_hint is True
