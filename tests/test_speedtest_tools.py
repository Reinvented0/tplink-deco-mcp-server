from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import call

import pytest

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from .conftest import ToolCaller

pytestmark = pytest.mark.anyio

_RESULT = {
    "down_speed": 3982072,
    "up_speed": 1015904,
    "ping_time": 2.381,
    "last_speed_test_time": 1792843742,
    "ever_tested": True,
    "ping_jitter": 0.498,
    "status": "idle",
}


async def test_reads_the_stored_result(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.request.return_value = _RESULT

    result = await call_tool("get_speedtest_result")

    deco.request.assert_called_once_with("admin/device", "speedtest", {"operation": "read"})
    assert result.structured_content == {
        "status": "idle",
        "ever_tested": True,
        "download_megabits_per_second": 3982.1,
        "upload_megabits_per_second": 1015.9,
        "ping_milliseconds": 2.381,
        "jitter_milliseconds": 0.498,
        "tested_at": "2026-10-24T12:09:02+00:00",
    }


async def test_handles_a_router_that_never_tested(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.request.return_value = {"status": "idle", "ever_tested": False, "down_speed": True}

    result = await call_tool("get_speedtest_result")

    assert result.structured_content["tested_at"] == ""
    assert result.structured_content["download_megabits_per_second"] == 0.0


async def test_starts_a_test(call_tool: ToolCaller, deco: MagicMock) -> None:
    deco.request.side_effect = [{}, {**_RESULT, "status": "testing"}]

    result = await call_tool("start_speedtest")

    assert deco.request.call_args_list == [
        call("admin/device", "speedtest", {"operation": "write"}),
        call("admin/device", "speedtest", {"operation": "read"}),
    ]
    assert result.structured_content["status"] == "testing"
