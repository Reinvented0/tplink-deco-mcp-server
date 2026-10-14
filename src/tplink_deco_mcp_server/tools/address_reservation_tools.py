"""Tools about the fixed IPs the DHCP server reserves for devices."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import Field
from tplink_deco_api import AddressReservation

from ..summaries import AddressReservationTableSummary
from .tool_parameters import MacAddress, canonical_mac, same_mac
from .tool_registration import CHANGES_SETTINGS, DISCARDS_SETTINGS, READ_ONLY, register_tool

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer
    from tplink_deco_api import DecoClient

    from ..router import RouterSession

Ipv4Address = Annotated[
    str, Field(description="IPv4 address inside the LAN, such as `192.168.68.50`.")
]


class AddressReservationTools:
    """Lists, creates, changes and deletes fixed IP reservations."""

    def __init__(self, router: RouterSession) -> None:
        self._router = router

    def register(self, server: MCPServer[None]) -> None:
        """Add the address reservation tools to ``server``."""
        register_tool(
            server,
            self.list_address_reservations,
            title="List fixed IPs",
            annotations=READ_ONLY,
        )
        register_tool(
            server,
            self.add_address_reservation,
            title="Reserve fixed IP",
            annotations=CHANGES_SETTINGS,
        )
        register_tool(
            server,
            self.update_address_reservation,
            title="Change fixed IP",
            annotations=CHANGES_SETTINGS,
        )
        register_tool(
            server,
            self.remove_address_reservation,
            title="Release fixed IP",
            annotations=DISCARDS_SETTINGS,
        )

    def list_address_reservations(self) -> AddressReservationTableSummary:
        """List the fixed IPs the DHCP server always hands to the same device.

        Returns each reservation's MAC and IP with the device name the mesh
        shows for that MAC (`null` when the device is not on the client list),
        and the most reservations the router accepts.
        """

        def read(deco: DecoClient) -> AddressReservationTableSummary:
            table = deco.address_reservations.get_table()
            names = {client.mac: client.name for client in deco.get_client_list()}
            return AddressReservationTableSummary.from_table(table, names)

        return self._router.run("list fixed IPs", read)

    def add_address_reservation(self, mac: MacAddress, ip: Ipv4Address) -> str:
        """Reserve a fixed IP for a device that has none yet.

        The device picks the address up on its next DHCP renewal or reconnect.
        Use `update_address_reservation` when the device already has one.
        """
        reservation = AddressReservation(mac, ip)
        self._router.run(
            "reserve fixed IP", lambda deco: deco.address_reservations.add(reservation)
        )
        return f"Reserved {ip} for {canonical_mac(mac)}."

    def update_address_reservation(self, mac: MacAddress, ip: Ipv4Address) -> str:
        """Move a device's existing fixed IP reservation to another address."""

        def update(deco: DecoClient) -> str:
            current = _find_reservation(deco, mac)
            deco.address_reservations.modify(current, AddressReservation(mac, ip))
            return current.ip

        previous_ip = self._router.run("change fixed IP", update)
        return f"Moved the reservation of {canonical_mac(mac)} from {previous_ip} to {ip}."

    def remove_address_reservation(self, mac: MacAddress) -> str:
        """Drop a device's fixed IP reservation; it gets a dynamic address on its next renewal."""
        self._router.run("release fixed IP", lambda deco: deco.address_reservations.remove(mac))
        return f"Released the fixed IP of {canonical_mac(mac)}."


def _find_reservation(deco: DecoClient, mac: str) -> AddressReservation:
    reservations = deco.address_reservations.get_table().reservations
    current = next((entry for entry in reservations if same_mac(entry.mac, mac)), None)
    if current is None:
        message = (
            f"Failed to change fixed IP: {mac} has no reservation, use add_address_reservation"
        )
        raise ValueError(message)
    return current
