"""Wi-Fi networks and radios, as shown to the model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from collections.abc import Iterable

    from tplink_deco_api import IotHost, MloHost, WlanBand, WlanConfig


class WifiNetworkSummary(BaseModel):
    """One SSID broadcast by the mesh."""

    model_config = ConfigDict(frozen=True)

    network: str = Field(description="`main`, `guest`, `iot` or `mlo` (multi-link Wi-Fi 7).")
    ssid: str
    password: str | None = Field(
        description="Wi-Fi password; `null` unless `include_passwords` was set."
    )
    enabled: bool
    bands: list[str] = Field(
        description="Bands the SSID is broadcast on: `band2_4`, `band5`, `band6`."
    )
    hidden: bool = Field(description="Whether the SSID is hidden from scans.")


class WifiRadioSummary(BaseModel):
    """Channel settings of one radio band."""

    model_config = ConfigDict(frozen=True)

    band: str = Field(description="`band2_4`, `band5` or `band6`.")
    channel: int = Field(description="Channel serving clients; `0` means automatic.")
    channel_width: str = Field(description="Channel width, such as `HT20`, `HT80`, `HT160`.")
    mode: str = Field(description="802.11 mode, such as `11ng`, `11ac`.")
    backhaul_channel: int = Field(description="Channel the units use to talk to each other.")


class WifiConfigurationSummary(BaseModel):
    """Every SSID the mesh broadcasts and how each radio is tuned."""

    model_config = ConfigDict(frozen=True)

    networks: list[WifiNetworkSummary]
    radios: list[WifiRadioSummary]

    @classmethod
    def from_wlan_config(
        cls, config: WlanConfig, *, include_passwords: bool
    ) -> WifiConfigurationSummary:
        """Summarize the Wi-Fi setup, leaving passwords out unless ``include_passwords``."""
        bands = [
            (name, band)
            for name, band in (
                ("band2_4", config.band2_4),
                ("band5", config.band5_1),
                ("band6", config.band6),
            )
            if band.host.ssid
        ]
        networks = [
            *_merge_by_ssid(
                "main",
                (_host_broadcast(name, band) for name, band in bands),
                include_passwords=include_passwords,
            ),
            *_merge_by_ssid(
                "guest",
                (_guest_broadcast(name, band) for name, band in bands),
                include_passwords=include_passwords,
            ),
            *_iot_network(config.iot_host, include_passwords=include_passwords),
            *_mlo_network(config.mlo_host, include_passwords=include_passwords),
        ]
        radios = [
            WifiRadioSummary(
                band=name,
                channel=band.host.channel,
                channel_width=band.host.channel_width,
                mode=band.host.mode,
                backhaul_channel=band.backhaul.channel,
            )
            for name, band in bands
        ]
        return cls(networks=networks, radios=radios)


@dataclass(frozen=True)
class _Broadcast:
    band: str
    ssid: str
    password: str
    enabled: bool
    hidden: bool


def _host_broadcast(band_name: str, band: WlanBand) -> _Broadcast:
    host = band.host
    return _Broadcast(band_name, host.ssid, host.password, host.enable, host.enable_hide_ssid)


def _guest_broadcast(band_name: str, band: WlanBand) -> _Broadcast:
    guest = band.guest
    return _Broadcast(band_name, guest.ssid, guest.password, guest.enable, hidden=False)


def _merge_by_ssid(
    network: str, broadcasts: Iterable[_Broadcast], *, include_passwords: bool
) -> list[WifiNetworkSummary]:
    """Fold the per-band broadcasts sharing an SSID into one network each."""
    grouped: dict[str, list[_Broadcast]] = {}
    for broadcast in broadcasts:
        if broadcast.ssid:
            grouped.setdefault(broadcast.ssid, []).append(broadcast)
    return [
        WifiNetworkSummary(
            network=network,
            ssid=ssid,
            password=group[0].password if include_passwords else None,
            enabled=any(broadcast.enabled for broadcast in group),
            bands=[broadcast.band for broadcast in group if broadcast.enabled],
            hidden=any(broadcast.hidden for broadcast in group),
        )
        for ssid, group in grouped.items()
    ]


def _iot_network(iot: IotHost, *, include_passwords: bool) -> list[WifiNetworkSummary]:
    if not iot.ssid:
        return []
    bands = [
        band for band, enabled in (("band2_4", iot.enable_2g), ("band5", iot.enable_5g)) if enabled
    ]
    return [
        WifiNetworkSummary(
            network="iot",
            ssid=iot.ssid,
            password=iot.password if include_passwords else None,
            enabled=iot.enable,
            bands=bands if iot.enable else [],
            hidden=False,
        )
    ]


def _mlo_network(mlo: MloHost, *, include_passwords: bool) -> list[WifiNetworkSummary]:
    if not mlo.ssid:
        return []
    return [
        WifiNetworkSummary(
            network="mlo",
            ssid=mlo.ssid,
            password=mlo.password if include_passwords else None,
            enabled=mlo.enable,
            bands=list(mlo.band) if mlo.enable else [],
            hidden=mlo.enable_hide_ssid,
        )
    ]
