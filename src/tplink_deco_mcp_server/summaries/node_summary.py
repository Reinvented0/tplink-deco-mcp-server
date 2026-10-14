"""A Deco unit of the mesh, as shown to the model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from tplink_deco_api import Device


class NodeSummary(BaseModel):
    """One Deco unit (the gateway or a satellite)."""

    model_config = ConfigDict(frozen=True)

    mac: str = Field(description="MAC address of the unit, `AA:BB:CC:DD:EE:FF`.")
    name: str = Field(description="Name given to the unit in the Deco app.")
    model: str = Field(description="Hardware model, such as `BE65`.")
    role: str = Field(
        description="`master` for the gateway connected to the modem, `slave` for a satellite."
    )
    ip: str = Field(description="LAN IP address of the unit.")
    hardware_version: str
    firmware_version: str
    internet_status: str = Field(description="`online` or `offline`, as seen by this unit.")
    internet_error: str = Field(
        description="Router-reported detail of the internet state; `well` while healthy."
    )
    group_status: str = Field(
        description="Mesh membership state; `connected` when the unit is part of the mesh."
    )
    backhaul_signal_level: dict[str, str] = Field(
        description="Wireless backhaul signal level per band (`band2_4`, `band5`, `band6`); "
        "`0` on the gateway and on wired satellites.",
    )

    @classmethod
    def from_device(cls, device: Device) -> NodeSummary:
        """Summarize a Deco unit reported by the SDK."""
        return cls(
            mac=device.mac,
            name=device.custom_nickname or device.nickname,
            model=device.device_model,
            role=device.role,
            ip=device.device_ip,
            hardware_version=device.hardware_ver,
            firmware_version=device.software_ver,
            internet_status=device.inet_status,
            internet_error=device.inet_error_msg,
            group_status=device.group_status,
            backhaul_signal_level={
                "band2_4": device.signal_level.band2_4,
                "band5": device.signal_level.band5,
                "band6": device.signal_level.band6,
            },
        )
