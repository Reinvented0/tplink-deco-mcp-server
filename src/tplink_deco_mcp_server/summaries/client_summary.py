"""A device using the network, as shown to the model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from tplink_deco_api import ClientDevice


class ClientSummary(BaseModel):
    """A device the mesh currently knows about."""

    model_config = ConfigDict(frozen=True)

    mac: str = Field(
        description="MAC address, `AA:BB:CC:DD:EE:FF`; the stable key the other client tools take."
    )
    name: str = Field(description="Name shown in the Deco app.")
    ip: str = Field(description="Current IPv4 address.")
    online: bool
    network: str = Field(description="Network the device joined: `main`, `guest`, `iot` or `mlo`.")
    connection: str = Field(
        description="`wired`, or the radio band of a wireless link: `band2_4`, `band5`, `band6`.",
    )
    client_type: str = Field(
        description="Device category set in the Deco app, such as `Mobile`, `Television`, `pc`."
    )
    node_id: str = Field(description="Identifier of the Deco unit the device is attached to.")
    download_kilobytes_per_second: int = Field(description="Instantaneous download rate.")
    upload_kilobytes_per_second: int = Field(description="Instantaneous upload rate.")
    high_priority: bool = Field(description="Whether QoS prioritizes this device.")

    @classmethod
    def from_client_device(cls, client: ClientDevice) -> ClientSummary:
        """Summarize a client reported by the SDK."""
        return cls(
            mac=client.mac,
            name=client.name,
            ip=client.ip,
            online=client.online,
            network=client.interface,
            connection=client.connection_type,
            client_type=client.client_type,
            node_id=client.access_host,
            download_kilobytes_per_second=client.down_speed,
            upload_kilobytes_per_second=client.up_speed,
            high_priority=client.enable_priority,
        )
