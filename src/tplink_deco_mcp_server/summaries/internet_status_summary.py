"""WAN connection state and addressing, as shown to the model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from tplink_deco_api import InternetStatus, IpStatus, WanInfo


class IpConnectionSummary(BaseModel):
    """Connection state for one IP version."""

    model_config = ConfigDict(frozen=True)

    status: str = Field(description="`online` or `offline`.")
    dial_status: str = Field(description="State of the WAN session, such as `connected`.")
    connection_type: str = Field(
        description="WAN protocol, such as `pppoe`, `dynamic_ip`, `static_ip`."
    )
    error_code: int = Field(description="Router error code; `0` when connected.")

    @classmethod
    def from_ip_status(cls, status: IpStatus) -> IpConnectionSummary:
        """Summarize the state of one IP version."""
        return cls(
            status=status.inet_status,
            dial_status=status.dial_status,
            connection_type=status.connect_type,
            error_code=status.error_code,
        )


class WanAddressSummary(BaseModel):
    """Public-facing address the gateway obtained from the provider."""

    model_config = ConfigDict(frozen=True)

    ip: str
    mask: str
    gateway: str
    primary_dns: str
    secondary_dns: str
    automatic_dns: bool = Field(description="Whether the DNS servers come from the provider.")


class LanAddressSummary(BaseModel):
    """Address of the gateway on the local network."""

    model_config = ConfigDict(frozen=True)

    ip: str
    mask: str


class InternetStatusSummary(BaseModel):
    """Whether the mesh is online, and the addresses on both sides of the gateway."""

    model_config = ConfigDict(frozen=True)

    cable_status: str = Field(description="Physical WAN port state: `plugged` or `unplugged`.")
    ipv4: IpConnectionSummary
    ipv6: IpConnectionSummary
    wan: WanAddressSummary
    lan: LanAddressSummary

    @classmethod
    def from_status(cls, status: InternetStatus, addresses: WanInfo) -> InternetStatusSummary:
        """Combine the connection state with the WAN and LAN addressing."""
        wan = addresses.wan.ip_info
        return cls(
            cable_status=status.link_status,
            ipv4=IpConnectionSummary.from_ip_status(status.ipv4),
            ipv6=IpConnectionSummary.from_ip_status(status.ipv6),
            wan=WanAddressSummary(
                ip=wan.ip,
                mask=wan.mask,
                gateway=wan.gateway,
                primary_dns=wan.dns1,
                secondary_dns=wan.dns2,
                automatic_dns=addresses.wan.enable_auto_dns,
            ),
            lan=LanAddressSummary(ip=addresses.lan.ip_info.ip, mask=addresses.lan.ip_info.mask),
        )
