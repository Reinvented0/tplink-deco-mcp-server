from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from .factories import client_device, device

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from .conftest import ToolCaller

pytestmark = pytest.mark.anyio

_GATEWAY = device()
_SATELLITE = device(mac="0C:EF:15:00:00:02", custom_nickname="Satellite", role="slave")

_ACCESS = {
    "client_list": [
        {
            "mac": "AA-BB-CC-DD-EE-01",
            "signal_level_5g": 3,
            "rssi_in_dbm_5g": 41,
            "txrate_5g": 866,
            "rxrate_5g": 780,
            "signal_level_2g": 0,
        },
        "junk",
    ]
}


async def test_maps_clients_to_their_unit(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.request.return_value = _ACCESS
    deco.get_device_list.return_value = [_GATEWAY, _SATELLITE]
    deco.get_client_list.side_effect = [
        [client_device(), client_device(mac="AA:BB:CC:DD:EE:02", online=False)],
        [
            client_device(
                mac="AA:BB:CC:DD:EE:03", name="Camera", connection_type="band2_4", client_mesh=False
            ),
            client_device(mac="AA:BB:CC:DD:EE:04", name="Pi", connection_type="wired"),
        ],
    ]

    result = await call_tool("list_client_connections")

    deco.get_client_list.assert_any_call("0C-EF-15-00-00-01")
    deco.get_client_list.assert_any_call("0C-EF-15-00-00-02")
    assert result.structured_content["result"] == [
        {
            "mac": "AA:BB:CC:DD:EE:01",
            "name": "Living Room TV",
            "ip": "192.168.68.10",
            "node_mac": "0C:EF:15:00:00:01",
            "node_name": "Living Room",
            "connection": "band5",
            "roaming_enabled": True,
            "signal_level": 3,
            "signal_strength": 41,
            "transmit_megabits_per_second": 866,
            "receive_megabits_per_second": 780,
        },
        {
            "mac": "AA:BB:CC:DD:EE:03",
            "name": "Camera",
            "ip": "192.168.68.10",
            "node_mac": "0C:EF:15:00:00:02",
            "node_name": "Satellite",
            "connection": "band2_4",
            "roaming_enabled": False,
            "signal_level": None,
            "signal_strength": None,
            "transmit_megabits_per_second": None,
            "receive_megabits_per_second": None,
        },
        {
            "mac": "AA:BB:CC:DD:EE:04",
            "name": "Pi",
            "ip": "192.168.68.10",
            "node_mac": "0C:EF:15:00:00:02",
            "node_name": "Satellite",
            "connection": "wired",
            "roaming_enabled": True,
            "signal_level": None,
            "signal_strength": None,
            "transmit_megabits_per_second": None,
            "receive_megabits_per_second": None,
        },
    ]


async def test_tolerates_a_missing_access_list(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.request.return_value = {}
    deco.get_device_list.return_value = [_GATEWAY]
    deco.get_client_list.return_value = [client_device()]

    result = await call_tool("list_client_connections")

    assert result.structured_content["result"][0]["signal_level"] is None


async def test_switches_roaming_off(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.get_client_list.side_effect = [[client_device()], [client_device(client_mesh=False)]]

    result = await call_tool("set_client_roaming", mac="aa-bb-cc-dd-ee-01", enabled=False)

    deco.request.assert_called_once_with(
        "admin/client",
        "client_list",
        {
            "operation": "write",
            "params": {
                "client_list": [
                    {
                        "mac": "AA-BB-CC-DD-EE-01",
                        "name": "TGl2aW5nIFJvb20gVFY=",
                        "user_set_name_type": True,
                        "client_mesh": False,
                    }
                ]
            },
        },
    )
    assert result.structured_content == {
        "mac": "AA:BB:CC:DD:EE:01",
        "name": "Living Room TV",
        "requested": False,
        "roaming_enabled": False,
        "applied": True,
    }


async def test_reports_a_change_the_router_ignored(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.get_client_list.return_value = [client_device()]

    result = await call_tool("set_client_roaming", mac="AA:BB:CC:DD:EE:01", enabled=False)

    assert result.structured_content["applied"] is False


async def test_refuses_an_unknown_client(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.get_client_list.return_value = [client_device()]

    result = await call_tool("set_client_roaming", mac="AA:BB:CC:DD:EE:99", enabled=True)

    assert result.is_error
    assert "Failed to find client AA:BB:CC:DD:EE:99" in result.content[0].text
    deco.request.assert_not_called()


async def test_reads_the_mesh_placement(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.request.return_value = {"support_plc": False, "location": "good", "status": "getting"}

    result = await call_tool("get_mesh_placement")

    deco.request.assert_called_once_with("admin/wireless", "bridge", {"operation": "read"})
    assert result.structured_content == {"placement": "good", "supports_powerline": False}
