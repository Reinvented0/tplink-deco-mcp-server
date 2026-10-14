from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from .factories import disabled_band, empty_band, wlan_config

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from .conftest import ToolCaller

pytestmark = pytest.mark.anyio


async def test_merges_bands_sharing_an_ssid_and_hides_passwords(
    call_tool: ToolCaller, deco: MagicMock
) -> None:
    deco.get_wlan_config.return_value = wlan_config()

    result = await call_tool("get_wifi_configuration")

    assert result.structured_content["networks"] == [
        {
            "network": "main",
            "ssid": "Home",
            "password": None,
            "enabled": True,
            "bands": ["band2_4", "band5"],
            "hidden": False,
        },
        {
            "network": "main",
            "ssid": "Home 6",
            "password": None,
            "enabled": True,
            "bands": ["band6"],
            "hidden": False,
        },
        {
            "network": "guest",
            "ssid": "Home Guest",
            "password": None,
            "enabled": True,
            "bands": ["band2_4", "band5"],
            "hidden": False,
        },
        {
            "network": "guest",
            "ssid": "Home 6 Guest",
            "password": None,
            "enabled": False,
            "bands": [],
            "hidden": False,
        },
        {
            "network": "iot",
            "ssid": "Home IoT",
            "password": None,
            "enabled": True,
            "bands": ["band2_4"],
            "hidden": False,
        },
        {
            "network": "mlo",
            "ssid": "Home",
            "password": None,
            "enabled": True,
            "bands": ["band5", "band6"],
            "hidden": True,
        },
    ]
    assert [radio["band"] for radio in result.structured_content["radios"]] == [
        "band2_4",
        "band5",
        "band6",
    ]
    assert result.structured_content["radios"][0] == {
        "band": "band2_4",
        "channel": 36,
        "channel_width": "HT80",
        "mode": "11ax",
        "backhaul_channel": 149,
    }


async def test_returns_passwords_on_request(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.get_wlan_config.return_value = wlan_config()

    result = await call_tool("get_wifi_configuration", include_passwords=True)

    passwords = {
        network["network"]: network["password"] for network in result.structured_content["networks"]
    }
    assert passwords == {
        "main": "main-secret",
        "guest": "guest-secret",
        "iot": "iot-secret",
        "mlo": "main-secret",
    }


async def test_skips_absent_radios_and_networks(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.get_wlan_config.return_value = wlan_config(band6=empty_band(), iot_ssid="", mlo_ssid="")

    result = await call_tool("get_wifi_configuration")

    networks = result.structured_content["networks"]
    assert [(network["network"], network["ssid"]) for network in networks] == [
        ("main", "Home"),
        ("guest", "Home Guest"),
    ]
    assert len(result.structured_content["radios"]) == 2


async def test_reports_a_disabled_band_without_bands(
    call_tool: ToolCaller, deco: MagicMock
) -> None:
    deco.get_wlan_config.return_value = wlan_config(band6=disabled_band("Home 6"))

    result = await call_tool("get_wifi_configuration")

    main_6 = next(
        network for network in result.structured_content["networks"] if network["ssid"] == "Home 6"
    )
    assert main_6["enabled"] is False
    assert main_6["bands"] == []
