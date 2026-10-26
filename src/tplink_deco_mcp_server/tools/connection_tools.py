"""Tools about which Deco unit each device uses and how well it is connected."""

from __future__ import annotations

from base64 import b64encode
from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from ..summaries import ClientConnectionSummary, MeshPlacementSummary, RoamingChangeSummary
from .tool_parameters import MacAddress, canonical_mac, same_mac
from .tool_registration import CHANGES_SETTINGS, READ_ONLY, register_tool

if TYPE_CHECKING:
    from collections.abc import Mapping

    from mcp.server.mcpserver import MCPServer
    from tplink_deco_api import ClientDevice, DecoClient

    from ..router import RouterSession


class ConnectionTools:
    """Maps devices to Deco units, reports link quality and controls per-device roaming."""

    def __init__(self, router: RouterSession) -> None:
        self._router = router

    def register(self, server: MCPServer[None]) -> None:
        """Add the connection tools to ``server``."""
        register_tool(
            server,
            self.list_client_connections,
            title="Client connections",
            annotations=READ_ONLY,
        )
        register_tool(
            server,
            self.set_client_roaming,
            title="Set client roaming",
            annotations=CHANGES_SETTINGS,
        )
        register_tool(
            server, self.get_mesh_placement, title="Mesh placement", annotations=READ_ONLY
        )

    def list_client_connections(self) -> list[ClientConnectionSummary]:
        """List every online device with the Deco unit it is attached to and its link quality.

        Returns per device its MAC, name, IP, the Deco unit (MAC and name),
        `wired` or the Wi-Fi band, whether mesh roaming is on, and, where the
        router reports it, signal bars (0-3), the raw RSSI figure and the
        current Wi-Fi link rates in Mbit/s. Some firmware reports signal only
        for part of the devices; those fields are then null. Use it to find
        devices on a weak link or on an unexpected unit.
        """
        return self._router.run("list client connections", _read_connections)

    def set_client_roaming(
        self,
        mac: MacAddress,
        enabled: Annotated[
            bool,
            Field(
                description="False keeps the mesh from steering the device to another Deco "
                "unit; true lets the mesh move it again."
            ),
        ],
    ) -> RoamingChangeSummary:
        """Switch the Deco app's per-device Mesh Technology (roaming) on or off.

        Deco cannot pin a device to a chosen unit; the device picks the unit
        it connects to. Turning roaming off only stops the mesh from steering
        it away from the unit it is on now, so connect the device near the
        wanted unit first. Returns the state read back from the router.
        """
        target = canonical_mac(mac)

        def change(deco: DecoClient) -> RoamingChangeSummary:
            client = _find_client(deco.get_client_list(), target)
            deco.request(
                "admin/client",
                "client_list",
                {
                    "operation": "write",
                    "params": {
                        "client_list": [
                            {
                                "mac": target.replace(":", "-"),
                                "name": b64encode(client.name.encode()).decode(),
                                "user_set_name_type": True,
                                "client_mesh": enabled,
                            }
                        ]
                    },
                },
            )
            after = _find_client(deco.get_client_list(), target)
            return RoamingChangeSummary(
                mac=target,
                name=after.name,
                requested=enabled,
                roaming_enabled=after.client_mesh,
                applied=after.client_mesh is enabled,
            )

        return self._router.run("change client roaming", change)

    def get_mesh_placement(self) -> MeshPlacementSummary:
        """Report the router's own grade for where the Deco units are placed.

        Returns `placement` (such as `good`, `fair`, `poor`) and whether the
        mesh supports powerline backhaul. Use with `list_deco_nodes`, whose
        backhaul signal levels show which unit has the weak link.
        """
        result = self._router.run(
            "read the mesh placement",
            lambda deco: deco.request("admin/wireless", "bridge", {"operation": "read"}),
        )
        return MeshPlacementSummary(
            placement=str(result.get("location") or ""),
            supports_powerline=result.get("support_plc") is True,
        )


def _read_connections(deco: DecoClient) -> list[ClientConnectionSummary]:
    access = _access_by_mac(deco.request("admin/client", "client_access", {"operation": "read"}))
    connections: list[ClientConnectionSummary] = []
    for node in deco.get_device_list():
        clients = deco.get_client_list(node.mac.replace(":", "-").upper())
        connections.extend(
            ClientConnectionSummary.from_readings(client, node, access.get(client.mac))
            for client in clients
            if client.online
        )
    return connections


def _access_by_mac(result: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    items = result.get("client_list")
    if not isinstance(items, list):
        return {}
    return {
        canonical_mac(str(item.get("mac", ""))): item for item in items if isinstance(item, dict)
    }


def _find_client(clients: list[ClientDevice], mac: str) -> ClientDevice:
    for client in clients:
        if same_mac(client.mac, mac):
            return client
    message = f"Failed to find client {mac}: the router does not know this device"
    raise ValueError(message)
