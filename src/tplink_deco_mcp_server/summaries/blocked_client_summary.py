"""A device cut off from the internet, as shown to the model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from tplink_deco_api import BlockedClient


class BlockedClientSummary(BaseModel):
    """A device on the mesh-wide internet blocklist."""

    model_config = ConfigDict(frozen=True)

    mac: str = Field(description="MAC address, `AA:BB:CC:DD:EE:FF`.")
    name: str = Field(description="Label stored with the blocklist entry.")
    client_type: str = Field(description="Device category stored with the blocklist entry.")

    @classmethod
    def from_blocked_client(cls, client: BlockedClient) -> BlockedClientSummary:
        """Summarize a blocklist entry reported by the SDK."""
        return cls(mac=client.mac, name=client.name, client_type=client.client_type)
