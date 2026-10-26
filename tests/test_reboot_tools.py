from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest
from mcp import Client

from tplink_deco_mcp_server import RouterSession, build_server

from .factories import device

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from mcp.types import CallToolResult

    from tplink_deco_mcp_server import RouterSettings

pytestmark = pytest.mark.anyio


async def _call_reboot(
    settings: RouterSettings, deco: MagicMock, macs: list[str]
) -> CallToolResult:
    router = RouterSession(replace(settings, allow_reboot=True), client_factory=lambda _: deco)
    async with Client(build_server(router)) as client:
        return await client.call_tool("reboot_deco_nodes", {"macs": macs})


async def test_reboots_known_units(settings: RouterSettings, deco: MagicMock) -> None:
    deco.get_device_list.return_value = [
        device(),
        device(mac="0C:EF:15:00:00:02", custom_nickname="Satellite"),
    ]

    result = await _call_reboot(settings, deco, ["0c-ef-15-00-00-02"])

    deco.request.assert_called_once_with(
        "admin/device",
        "system",
        {"operation": "reboot", "params": {"mac_list": [{"mac": "0C-EF-15-00-00-02"}]}},
    )
    assert result.structured_content == {"rebooting": ["Satellite"]}


async def test_refuses_a_unit_outside_the_mesh(settings: RouterSettings, deco: MagicMock) -> None:
    deco.get_device_list.return_value = [device()]

    result = await _call_reboot(settings, deco, ["AA:BB:CC:DD:EE:99"])

    assert result.is_error
    assert "not a Deco unit of this mesh" in result.content[0].text
    deco.request.assert_not_called()
