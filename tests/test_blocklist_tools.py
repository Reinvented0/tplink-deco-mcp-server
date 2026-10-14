from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from .factories import blocked_client, client_device

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from .conftest import ToolCaller

pytestmark = pytest.mark.anyio


async def test_lists_blocked_clients(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.clients.get_blocked.return_value = [blocked_client()]

    result = await call_tool("list_blocked_clients")

    assert result.structured_content["result"] == [
        {"mac": "AA:BB:CC:DD:EE:09", "name": "Tablet", "client_type": "Mobile"}
    ]


async def test_blocks_a_known_client_with_its_current_labels(
    call_tool: ToolCaller, deco: MagicMock
) -> None:
    deco.get_client_list.return_value = [client_device()]

    result = await call_tool("block_client", mac="aa-bb-cc-dd-ee-01")

    deco.clients.block.assert_called_once_with("aa-bb-cc-dd-ee-01", "Living Room TV", "Television")
    assert result.content[0].text == "Blocked Living Room TV (AA:BB:CC:DD:EE:01) from the internet."


async def test_blocks_with_explicit_labels(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.get_client_list.return_value = [client_device()]

    await call_tool("block_client", mac="AA:BB:CC:DD:EE:01", name="TV", client_type="other")

    deco.clients.block.assert_called_once_with("AA:BB:CC:DD:EE:01", "TV", "other")


async def test_blocks_an_unknown_client_given_a_name(
    call_tool: ToolCaller, deco: MagicMock
) -> None:
    deco.get_client_list.return_value = []

    await call_tool("block_client", mac="AA:BB:CC:DD:EE:05", name="Visitor phone")

    deco.clients.block.assert_called_once_with("AA:BB:CC:DD:EE:05", "Visitor phone", "other")


async def test_needs_a_name_for_an_unknown_client(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.get_client_list.return_value = []

    result = await call_tool("block_client", mac="AA:BB:CC:DD:EE:05")

    assert result.is_error
    assert "is not on the client list, pass `name`" in result.content[0].text
    deco.clients.block.assert_not_called()


async def test_unblocks_a_client(call_tool: ToolCaller, deco: MagicMock) -> None:
    result = await call_tool("unblock_client", mac="aa:bb:cc:dd:ee:09")

    deco.clients.unblock.assert_called_once_with("aa:bb:cc:dd:ee:09")
    assert result.content[0].text == "Unblocked AA:BB:CC:DD:EE:09."
