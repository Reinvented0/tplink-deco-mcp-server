"""Tool that reboots Deco units; only registered when the operator opts in."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, Field

from .tool_parameters import MacAddress, canonical_mac, same_mac
from .tool_registration import INTERRUPTS_NETWORK, register_tool

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer
    from tplink_deco_api import DecoClient

    from ..router import RouterSession


class RebootSummary(BaseModel):
    """The Deco units a reboot was sent to."""

    model_config = ConfigDict(frozen=True)

    rebooting: list[str] = Field(description="Names of the units that are restarting.")


class RebootTools:
    """Restarts Deco units, the same way the router's own Reboot page does."""

    def __init__(self, router: RouterSession) -> None:
        self._router = router

    def register(self, server: MCPServer[None]) -> None:
        """Add the reboot tool to ``server`` when ``DECO_ALLOW_REBOOT`` is set."""
        if self._router.settings.allow_reboot:
            register_tool(
                server,
                self.reboot_deco_nodes,
                title="Reboot Deco units",
                annotations=INTERRUPTS_NETWORK,
            )

    def reboot_deco_nodes(
        self,
        macs: Annotated[
            list[MacAddress],
            Field(
                min_length=1, description="MACs of the units to restart, from `list_deco_nodes`."
            ),
        ],
    ) -> RebootSummary:
        """Restart one or more Deco units.

        Every device on those units loses its connection for about two
        minutes; restarting the gateway (`role: master`) takes the whole
        network and the internet down for that time. Only call this when the
        user explicitly asks for a reboot.
        """
        targets = [canonical_mac(mac) for mac in macs]

        def reboot(deco: DecoClient) -> RebootSummary:
            nodes = deco.get_device_list()
            names: list[str] = []
            for target in targets:
                node = next((node for node in nodes if same_mac(node.mac, target)), None)
                if node is None:
                    message = f"Failed to reboot {target}: not a Deco unit of this mesh"
                    raise ValueError(message)
                names.append(node.custom_nickname or node.nickname)
            deco.request(
                "admin/device",
                "system",
                {
                    "operation": "reboot",
                    "params": {
                        "mac_list": [{"mac": target.replace(":", "-")} for target in targets]
                    },
                },
            )
            return RebootSummary(rebooting=names)

        return self._router.run("reboot Deco units", reboot)
