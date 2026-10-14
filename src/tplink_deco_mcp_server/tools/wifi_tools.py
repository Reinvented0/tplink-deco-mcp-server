"""Tools about the Wi-Fi networks the mesh broadcasts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from ..summaries import WifiConfigurationSummary
from .tool_registration import READ_ONLY, register_tool

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer

    from ..router import RouterSession


class WifiTools:
    """Reads the SSIDs and radio settings of the mesh."""

    def __init__(self, router: RouterSession) -> None:
        self._router = router

    def register(self, server: MCPServer[None]) -> None:
        """Add the Wi-Fi tools to ``server``."""
        register_tool(
            server, self.get_wifi_configuration, title="Wi-Fi configuration", annotations=READ_ONLY
        )

    def get_wifi_configuration(
        self,
        include_passwords: Annotated[
            bool,
            Field(
                description="Also return each network's password. Only set it when the user "
                "explicitly asks for a password, such as to share the guest network. "
                "Default: false."
            ),
        ] = False,
    ) -> WifiConfigurationSummary:
        """Describe the Wi-Fi networks the mesh broadcasts and how each radio is tuned.

        Returns every network (`main`, `guest`, `iot`, `mlo`) with its SSID,
        whether it is enabled, the bands it is broadcast on and whether it is
        hidden, plus each radio band's channel, channel width, 802.11 mode and
        backhaul channel. Passwords are left out unless `include_passwords` is set.
        """
        config = self._router.run("read Wi-Fi configuration", lambda deco: deco.get_wlan_config())
        return WifiConfigurationSummary.from_wlan_config(
            config, include_passwords=include_passwords
        )
