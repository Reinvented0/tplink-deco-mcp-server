"""Tools about the Deco units themselves and the load on the gateway."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..summaries import NodeSummary, PerformanceSummary
from .tool_registration import READ_ONLY, register_tool

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer

    from ..router import RouterSession


class MeshTools:
    """Reads the units of the mesh and how busy the gateway is."""

    def __init__(self, router: RouterSession) -> None:
        self._router = router

    def register(self, server: MCPServer[None]) -> None:
        """Add the mesh tools to ``server``."""
        register_tool(server, self.list_deco_nodes, title="List Deco units", annotations=READ_ONLY)
        register_tool(
            server, self.get_router_performance, title="Router performance", annotations=READ_ONLY
        )

    def list_deco_nodes(self) -> list[NodeSummary]:
        """List the Deco units that form the mesh: the gateway and every satellite.

        Returns each unit's MAC, name, model, role (`master` is the gateway),
        LAN IP, hardware and firmware versions, internet status as the unit
        sees it, and the backhaul signal level per band.
        """
        nodes = self._router.run("list Deco units", lambda deco: deco.get_device_list())
        return [NodeSummary.from_device(node) for node in nodes]

    def get_router_performance(self) -> PerformanceSummary:
        """Report how busy the gateway is and how much traffic flows through the mesh right now.

        Returns CPU and memory usage of the gateway in percent, the number of
        online clients and the summed instantaneous download and upload rates
        of every client, in kilobytes per second.
        """
        performance, clients = self._router.run(
            "read router performance",
            lambda deco: (deco.get_performance(), deco.get_client_list()),
        )
        return PerformanceSummary.from_readings(performance, clients)
