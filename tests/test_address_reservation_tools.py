from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from tplink_deco_api import AddressReservation

from .factories import client_device, reservation_table

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from .conftest import ToolCaller

pytestmark = pytest.mark.anyio

_TV = AddressReservation("AA:BB:CC:DD:EE:01", "192.168.68.50")
_UNKNOWN = AddressReservation("AA:BB:CC:DD:EE:07", "192.168.68.51")


async def test_lists_reservations_with_client_names(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.address_reservations.get_table.return_value = reservation_table(_TV, _UNKNOWN)
    deco.get_client_list.return_value = [client_device()]

    result = await call_tool("list_address_reservations")

    assert result.structured_content == {
        "reservations": [
            {"mac": "AA:BB:CC:DD:EE:01", "ip": "192.168.68.50", "client_name": "Living Room TV"},
            {"mac": "AA:BB:CC:DD:EE:07", "ip": "192.168.68.51", "client_name": None},
        ],
        "maximum_reservations": 64,
    }


async def test_adds_a_reservation(call_tool: ToolCaller, deco: MagicMock) -> None:
    result = await call_tool("add_address_reservation", mac="aa-bb-cc-dd-ee-01", ip="192.168.68.50")

    deco.address_reservations.add.assert_called_once_with(
        AddressReservation("aa-bb-cc-dd-ee-01", "192.168.68.50")
    )
    assert result.content[0].text == "Reserved 192.168.68.50 for AA:BB:CC:DD:EE:01."


async def test_moves_an_existing_reservation(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.address_reservations.get_table.return_value = reservation_table(_UNKNOWN, _TV)

    result = await call_tool(
        "update_address_reservation", mac="aa-bb-cc-dd-ee-01", ip="192.168.68.60"
    )

    deco.address_reservations.modify.assert_called_once_with(
        _TV, AddressReservation("aa-bb-cc-dd-ee-01", "192.168.68.60")
    )
    assert result.content[0].text == (
        "Moved the reservation of AA:BB:CC:DD:EE:01 from 192.168.68.50 to 192.168.68.60."
    )


async def test_refuses_to_move_a_missing_reservation(
    call_tool: ToolCaller, deco: MagicMock
) -> None:
    deco.address_reservations.get_table.return_value = reservation_table(_UNKNOWN)

    result = await call_tool(
        "update_address_reservation", mac="AA:BB:CC:DD:EE:01", ip="192.168.68.60"
    )

    assert result.is_error
    assert "has no reservation, use add_address_reservation" in result.content[0].text
    deco.address_reservations.modify.assert_not_called()


async def test_removes_a_reservation(call_tool: ToolCaller, deco: MagicMock) -> None:
    result = await call_tool("remove_address_reservation", mac="AA:BB:CC:DD:EE:01")

    deco.address_reservations.remove.assert_called_once_with("AA:BB:CC:DD:EE:01")
    assert result.content[0].text == "Released the fixed IP of AA:BB:CC:DD:EE:01."
