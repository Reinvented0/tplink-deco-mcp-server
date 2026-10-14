"""Fixed IP reservations, as shown to the model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from collections.abc import Mapping

    from tplink_deco_api import AddressReservation, AddressReservationTable


class AddressReservationSummary(BaseModel):
    """A fixed IPv4 address the DHCP server always leases to one device."""

    model_config = ConfigDict(frozen=True)

    mac: str = Field(description="MAC address of the device, `AA:BB:CC:DD:EE:FF`.")
    ip: str = Field(description="IPv4 address reserved for the device.")
    client_name: str | None = Field(
        description="Name the mesh shows for the device; `null` when the mesh does not list it.",
    )

    @classmethod
    def from_reservation(
        cls, reservation: AddressReservation, client_names: Mapping[str, str]
    ) -> AddressReservationSummary:
        """Summarize a reservation, naming the device from ``client_names`` keyed by MAC."""
        return cls(
            mac=reservation.mac,
            ip=reservation.ip,
            client_name=client_names.get(reservation.mac),
        )


class AddressReservationTableSummary(BaseModel):
    """Every fixed IP reservation and how many the router accepts."""

    model_config = ConfigDict(frozen=True)

    reservations: list[AddressReservationSummary]
    maximum_reservations: int = Field(description="Most reservations the router accepts.")

    @classmethod
    def from_table(
        cls, table: AddressReservationTable, client_names: Mapping[str, str]
    ) -> AddressReservationTableSummary:
        """Summarize the reservation table, naming each device from ``client_names``."""
        return cls(
            reservations=[
                AddressReservationSummary.from_reservation(reservation, client_names)
                for reservation in table.reservations
            ],
            maximum_reservations=table.max_count,
        )
