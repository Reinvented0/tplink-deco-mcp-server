"""Which Deco unit a device hangs on and how well, as shown to the model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from collections.abc import Mapping

    from tplink_deco_api import ClientDevice, Device

_BAND_SUFFIX = {"band2_4": "2g", "band5": "5g", "band6": "6g"}


class ClientConnectionSummary(BaseModel):
    """An online device with the Deco unit it is attached to and its link quality."""

    model_config = ConfigDict(frozen=True)

    mac: str = Field(description="MAC address, `AA:BB:CC:DD:EE:FF`.")
    name: str
    ip: str
    node_mac: str = Field(description="MAC of the Deco unit the device is attached to.")
    node_name: str = Field(description="Name of that Deco unit in the Deco app.")
    connection: str = Field(description="`wired`, or the band: `band2_4`, `band5`, `band6`.")
    roaming_enabled: bool = Field(
        description="The Deco app's per-device Mesh Technology switch: whether the mesh may "
        "steer this device to another unit.",
    )
    signal_level: int | None = Field(
        description="Signal bars 0 (weak) to 3 (strong) on the current band; null when the "
        "router does not report it for this device or it is wired.",
    )
    signal_strength: int | None = Field(
        description="Router's raw RSSI figure on the current band (higher is stronger); null "
        "when not reported.",
    )
    transmit_megabits_per_second: int | None = Field(
        description="Current Wi-Fi link rate from the Deco to the device; null when not reported."
    )
    receive_megabits_per_second: int | None = Field(
        description="Current Wi-Fi link rate from the device to the Deco; null when not reported."
    )

    @classmethod
    def from_readings(
        cls,
        client: ClientDevice,
        node: Device,
        access: Mapping[str, object] | None,
    ) -> ClientConnectionSummary:
        """Combine a client of ``node`` with its ``client_access`` entry, if any."""
        suffix = _BAND_SUFFIX.get(client.connection_type)
        wireless = suffix is not None and access is not None
        return cls(
            mac=client.mac,
            name=client.name,
            ip=client.ip,
            node_mac=node.mac,
            node_name=node.custom_nickname or node.nickname,
            connection=client.connection_type,
            roaming_enabled=client.client_mesh,
            signal_level=_reading(access, f"signal_level_{suffix}") if wireless else None,
            signal_strength=_reading(access, f"rssi_in_dbm_{suffix}") if wireless else None,
            transmit_megabits_per_second=_reading(access, f"txrate_{suffix}") if wireless else None,
            receive_megabits_per_second=_reading(access, f"rxrate_{suffix}") if wireless else None,
        )


class RoamingChangeSummary(BaseModel):
    """Outcome of switching a device's roaming on or off, read back from the router."""

    model_config = ConfigDict(frozen=True)

    mac: str
    name: str
    requested: bool = Field(description="The roaming state that was asked for.")
    roaming_enabled: bool = Field(description="The state the router reports after the change.")
    applied: bool = Field(description="Whether the router now reports the requested state.")


class MeshPlacementSummary(BaseModel):
    """The router's own verdict on where the Deco units stand."""

    model_config = ConfigDict(frozen=True)

    placement: str = Field(description="Router's grade, such as `good`, `fair` or `poor`.")
    supports_powerline: bool


def _reading(access: Mapping[str, object] | None, key: str) -> int | None:
    value = None if access is None else access.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value
