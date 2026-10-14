"""Tools about the mesh-wide internet blocklist."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from ..summaries import BlockedClientSummary
from .tool_parameters import MacAddress, canonical_mac, same_mac
from .tool_registration import CHANGES_SETTINGS, READ_ONLY, register_tool

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer
    from tplink_deco_api import DecoClient

    from ..router import RouterSession

_FALLBACK_CLIENT_TYPE = "other"


class BlocklistTools:
    """Cuts devices off from the internet and lets them back in."""

    def __init__(self, router: RouterSession) -> None:
        self._router = router

    def register(self, server: MCPServer[None]) -> None:
        """Add the blocklist tools to ``server``."""
        register_tool(
            server, self.list_blocked_clients, title="List blocked clients", annotations=READ_ONLY
        )
        register_tool(server, self.block_client, title="Block client", annotations=CHANGES_SETTINGS)
        register_tool(
            server, self.unblock_client, title="Unblock client", annotations=CHANGES_SETTINGS
        )

    def list_blocked_clients(self) -> list[BlockedClientSummary]:
        """List the devices that are blocked from the internet across the whole mesh.

        Returns each blocked device's MAC, the name and the category stored with
        the block.
        """
        blocked = self._router.run("list blocked clients", lambda deco: deco.clients.get_blocked())
        return [BlockedClientSummary.from_blocked_client(client) for client in blocked]

    def block_client(
        self,
        mac: MacAddress,
        name: Annotated[
            str | None,
            Field(
                description="Label for the block. "
                "Omit to reuse the name the mesh already shows for the device."
            ),
        ] = None,
        client_type: Annotated[
            str | None,
            Field(
                description="Device category stored with the block. "
                "Omit to reuse the one the mesh already shows."
            ),
        ] = None,
    ) -> str:
        """Block a device from the internet on every Deco unit; it stays on the local network.

        `name` and `client_type` default to what `list_clients` shows for the
        device, so they are only needed for a device the mesh does not list.
        """

        def block(deco: DecoClient) -> str:
            known = next(
                (client for client in deco.get_client_list() if same_mac(client.mac, mac)), None
            )
            label = name or (known.name if known else "")
            if not label:
                message = f"Failed to block client: {mac} is not on the client list, pass `name`"
                raise ValueError(message)
            category = client_type or (known.client_type if known else "") or _FALLBACK_CLIENT_TYPE
            deco.clients.block(mac, label, category)
            return label

        label = self._router.run("block client", block)
        return f"Blocked {label} ({canonical_mac(mac)}) from the internet."

    def unblock_client(self, mac: MacAddress) -> str:
        """Restore internet access for a device on the blocklist."""
        self._router.run("unblock client", lambda deco: deco.clients.unblock(mac))
        return f"Unblocked {canonical_mac(mac)}."
