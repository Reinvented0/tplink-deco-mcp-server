"""Tools that read and start the gateway's own WAN speed test."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..summaries import SpeedtestSummary
from .tool_registration import READ_ONLY, RUNS_ACTION, register_tool

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer
    from tplink_deco_api import DecoClient

    from ..router import RouterSession

_PATH = "admin/device"
_FORM = "speedtest"


class SpeedtestTools:
    """Reads the stored speed test result and starts new runs on the gateway."""

    def __init__(self, router: RouterSession) -> None:
        self._router = router

    def register(self, server: MCPServer[None]) -> None:
        """Add the speed test tools to ``server``."""
        register_tool(
            server, self.get_speedtest_result, title="Speed test result", annotations=READ_ONLY
        )
        register_tool(
            server, self.start_speedtest, title="Start speed test", annotations=RUNS_ACTION
        )

    def get_speedtest_result(self) -> SpeedtestSummary:
        """Read the last WAN speed test the gateway ran itself.

        Returns download and upload in Mbit/s, ping and jitter in ms, when it
        was measured and whether a test is running now (`status: testing`).
        Measured on the router, so it is not limited by any one device's
        network card. Does not start a new test; use `start_speedtest`.
        """
        result = self._router.run(
            "read the speed test", lambda deco: deco.request(_PATH, _FORM, {"operation": "read"})
        )
        return SpeedtestSummary.from_api(result)

    def start_speedtest(self) -> SpeedtestSummary:
        """Start a new WAN speed test on the gateway and return right away.

        The test saturates the internet line for about a minute, so avoid it
        during calls or gaming. Call `get_speedtest_result` after about a
        minute; `status` turns back to `idle` with the new result.
        """

        def start(deco: DecoClient) -> SpeedtestSummary:
            deco.request(_PATH, _FORM, {"operation": "write"})
            return SpeedtestSummary.from_api(deco.request(_PATH, _FORM, {"operation": "read"}))

        return self._router.run("start a speed test", start)
