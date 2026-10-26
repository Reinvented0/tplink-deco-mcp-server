from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from .conftest import ToolCaller

pytestmark = pytest.mark.anyio


async def test_reads_a_form_verbatim(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.request.return_value = {"status": "idle", "down_speed": 2350}

    result = await call_tool("read_router_form", path="admin/device", form="speedtest")

    deco.request.assert_called_once_with("admin/device", "speedtest", {"operation": "read"})
    assert result.structured_content == {"status": "idle", "down_speed": 2350}


async def test_passes_a_list_operation(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.request.return_value = {}

    await call_tool("read_router_form", path="admin/client", form="traffic_stat", operation="list")

    deco.request.assert_called_once_with("admin/client", "traffic_stat", {"operation": "list"})


@pytest.mark.parametrize(
    "arguments",
    [
        {"path": "admin/firmware", "form": "upgrade"},
        {"path": "admin/device", "form": "system", "operation": "reboot"},
        {"path": "admin/device", "form": "../x"},
    ],
)
async def test_refuses_anything_but_reads(
    call_tool: ToolCaller, deco: MagicMock, arguments: dict[str, str]
) -> None:
    result = await call_tool("read_router_form", **arguments)

    assert result.is_error
    deco.request.assert_not_called()


async def test_scopes_a_read_to_one_node(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.request.return_value = {}

    await call_tool(
        "read_router_form", path="admin/client", form="client_list", device_mac="0c:ef:15:00:00:02"
    )

    deco.request.assert_called_once_with(
        "admin/client",
        "client_list",
        {"operation": "read", "params": {"device_mac": "0C-EF-15-00-00-02"}},
    )
