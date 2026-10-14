"""Tools about the devices that use the network."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from ..summaries import ClientSummary
from .tool_parameters import MacAddress, canonical_mac
from .tool_registration import CHANGES_SETTINGS, DISCARDS_SETTINGS, READ_ONLY, register_tool

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer

    from ..router import RouterSession


class ClientTools:
    """Lists, renames and forgets the devices the mesh knows about."""

    def __init__(self, router: RouterSession) -> None:
        self._router = router

    def register(self, server: MCPServer[None]) -> None:
        """Add the client tools to ``server``."""
        register_tool(server, self.list_clients, title="List clients", annotations=READ_ONLY)
        register_tool(
            server, self.update_client, title="Update client", annotations=CHANGES_SETTINGS
        )
        register_tool(
            server, self.remove_client, title="Forget client", annotations=DISCARDS_SETTINGS
        )

    def list_clients(
        self,
        online_only: Annotated[
            bool,
            Field(
                description="Leave out devices that are not connected right now. Default: false."
            ),
        ] = False,
    ) -> list[ClientSummary]:
        """List the devices (phones, computers, TVs, IoT gadgets) the mesh knows about.

        Returns each device's MAC, name, IP, whether it is online, the network
        it joined (`main`, `guest`, `iot`, `mlo`), how it connects (`wired` or
        the radio band), its category, the Deco unit it is attached to, its
        instantaneous download/upload rate and whether QoS prioritizes it. The
        MAC is the key every other client tool takes; find it here first when
        the user names a device.
        """
        clients = self._router.run("list clients", lambda deco: deco.get_client_list())
        return [
            ClientSummary.from_client_device(client)
            for client in clients
            if client.online or not online_only
        ]

    def update_client(
        self,
        mac: MacAddress,
        name: Annotated[
            str,
            Field(
                description="Name to show in the Deco app. "
                "Pass the current one to change only `client_type`."
            ),
        ],
        client_type: Annotated[
            str | None,
            Field(
                description="New device category, using the values `list_clients` returns "
                "such as `Mobile`, `Television`, `pc`. Omit to keep the current one."
            ),
        ] = None,
    ) -> str:
        """Rename a device and optionally change its category in the Deco app.

        The router only applies an edit that carries a name, so `name` is
        always required.
        """
        self._router.run("update client", lambda deco: deco.clients.update(mac, name, client_type))
        return f"Updated {canonical_mac(mac)}: name={name!r}" + (
            f", client_type={client_type!r}" if client_type else ""
        )

    def remove_client(self, mac: MacAddress) -> str:
        """Forget a device that is no longer used, removing it from the client list.

        Meant for offline devices: the router lists the device again as soon
        as it reconnects. This does not block it — use `block_client` for that.
        """
        self._router.run("remove client", lambda deco: deco.clients.remove(mac))
        return f"Removed {canonical_mac(mac)} from the client list."
