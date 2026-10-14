"""Tools about the connection between the gateway and the provider."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..summaries import InternetStatusSummary
from .tool_registration import READ_ONLY, register_tool

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer

    from ..router import RouterSession


class InternetTools:
    """Reads whether the mesh is online and how the WAN is addressed."""

    def __init__(self, router: RouterSession) -> None:
        self._router = router

    def register(self, server: MCPServer[None]) -> None:
        """Add the internet tools to ``server``."""
        register_tool(
            server, self.get_internet_status, title="Internet status", annotations=READ_ONLY
        )

    def get_internet_status(self) -> InternetStatusSummary:
        """Report whether the mesh is online and how the gateway reaches the provider.

        Returns the WAN cable state, the IPv4 and IPv6 connection state
        (`online`/`offline`, protocol such as `pppoe`, router error code), the
        public WAN address with its gateway and DNS servers, and the gateway's
        LAN address. Use it to diagnose an internet outage.
        """
        status, addresses = self._router.run(
            "read internet status",
            lambda deco: (deco.get_internet_status(), deco.get_wan_info()),
        )
        return InternetStatusSummary.from_status(status, addresses)
