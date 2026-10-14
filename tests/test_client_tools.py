from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from .factories import client_device

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from .conftest import ToolCaller

pytestmark = pytest.mark.anyio


async def test_lists_clients(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.get_client_list.return_value = [client_device()]

    result = await call_tool("list_clients")

    assert result.structured_content["result"] == [
        {
            "mac": "AA:BB:CC:DD:EE:01",
            "name": "Living Room TV",
            "ip": "192.168.68.10",
            "online": True,
            "network": "main",
            "connection": "band5",
            "client_type": "Television",
            "node_id": "1",
            "download_kilobytes_per_second": 200,
            "upload_kilobytes_per_second": 10,
            "high_priority": False,
        }
    ]


async def test_filters_offline_clients(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.get_client_list.return_value = [
        client_device(),
        client_device(mac="AA:BB:CC:DD:EE:02", online=False),
    ]

    everything = await call_tool("list_clients")
    online = await call_tool("list_clients", online_only=True)

    assert len(everything.structured_content["result"]) == 2
    assert [client["mac"] for client in online.structured_content["result"]] == [
        "AA:BB:CC:DD:EE:01"
    ]


async def test_updates_a_client(call_tool: ToolCaller, deco: MagicMock) -> None:
    result = await call_tool(
        "update_client", mac="aa-bb-cc-dd-ee-01", name="Bedroom TV", client_type="Television"
    )

    deco.clients.update.assert_called_once_with("aa-bb-cc-dd-ee-01", "Bedroom TV", "Television")
    assert result.content[0].text == (
        "Updated AA:BB:CC:DD:EE:01: name='Bedroom TV', client_type='Television'"
    )


async def test_renames_a_client_keeping_its_type(call_tool: ToolCaller, deco: MagicMock) -> None:
    result = await call_tool("update_client", mac="AA:BB:CC:DD:EE:01", name="Bedroom TV")

    deco.clients.update.assert_called_once_with("AA:BB:CC:DD:EE:01", "Bedroom TV", None)
    assert result.content[0].text == "Updated AA:BB:CC:DD:EE:01: name='Bedroom TV'"


async def test_removes_a_client(call_tool: ToolCaller, deco: MagicMock) -> None:
    result = await call_tool("remove_client", mac="AA:BB:CC:DD:EE:01")

    deco.clients.remove.assert_called_once_with("AA:BB:CC:DD:EE:01")
    assert result.content[0].text == "Removed AA:BB:CC:DD:EE:01 from the client list."


async def test_rejects_a_malformed_mac(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.clients.remove.side_effect = ValueError("Failed to parse MAC address: 'tv'")

    result = await call_tool("remove_client", mac="tv")

    assert result.is_error
    assert "Failed to parse MAC address: 'tv'" in result.content[0].text
