from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from .factories import client_device, device, internet_status, performance, wan_info

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from .conftest import ToolCaller

pytestmark = pytest.mark.anyio


async def test_lists_deco_units(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.get_device_list.return_value = [device(), device(custom_nickname="", role="slave")]

    result = await call_tool("list_deco_nodes")

    nodes = result.structured_content["result"]
    assert [node["name"] for node in nodes] == ["Living Room", "living_room"]
    assert nodes[0] == {
        "mac": "0C:EF:15:00:00:01",
        "name": "Living Room",
        "model": "BE65",
        "role": "master",
        "ip": "192.168.68.1",
        "hardware_version": "2.0",
        "firmware_version": "1.3.3 Build 26071612",
        "internet_status": "online",
        "internet_error": "well",
        "group_status": "connected",
        "backhaul_signal_level": {"band2_4": "0", "band5": "0", "band6": "0"},
    }


async def test_reports_router_performance(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.get_performance.return_value = performance()
    deco.get_client_list.return_value = [
        client_device(),
        client_device(up_speed=5, down_speed=50, online=False),
    ]

    result = await call_tool("get_router_performance")

    assert result.structured_content == {
        "cpu_usage_percent": 12.5,
        "memory_usage_percent": 40.0,
        "online_clients": 1,
        "total_download_kilobytes_per_second": 250,
        "total_upload_kilobytes_per_second": 15,
    }


async def test_reports_internet_status(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.get_internet_status.return_value = internet_status()
    deco.get_wan_info.return_value = wan_info()

    result = await call_tool("get_internet_status")

    assert result.structured_content == {
        "cable_status": "plugged",
        "ipv4": {
            "status": "online",
            "dial_status": "connected",
            "connection_type": "pppoe",
            "error_code": 0,
        },
        "ipv6": {
            "status": "offline",
            "dial_status": "unknown",
            "connection_type": "unknown",
            "error_code": 1,
        },
        "wan": {
            "ip": "203.0.113.7",
            "mask": "255.255.255.255",
            "gateway": "203.0.113.1",
            "primary_dns": "1.1.1.1",
            "secondary_dns": "8.8.8.8",
            "automatic_dns": False,
        },
        "lan": {"ip": "192.168.68.1", "mask": "255.255.255.0"},
    }


async def test_surfaces_router_failures_as_tool_errors(
    call_tool: ToolCaller, deco: MagicMock
) -> None:
    deco.get_internet_status.side_effect = TimeoutError()

    result = await call_tool("get_internet_status")

    assert result.is_error
    assert "Failed to read internet status: the router did not answer within 5s" in (
        result.content[0].text
    )
