"""Tool groups, one per router feature, each registering its tools on the server."""

from __future__ import annotations

from .address_reservation_tools import AddressReservationTools
from .blocklist_tools import BlocklistTools
from .client_tools import ClientTools
from .connection_tools import ConnectionTools
from .internet_tools import InternetTools
from .mesh_tools import MeshTools
from .raw_tools import RawTools
from .reboot_tools import RebootTools
from .speedtest_tools import SpeedtestTools
from .system_log_tools import SystemLogTools
from .tool_registration import ToolGroup
from .wifi_tools import WifiTools

__all__ = [
    "AddressReservationTools",
    "BlocklistTools",
    "ClientTools",
    "ConnectionTools",
    "InternetTools",
    "MeshTools",
    "RawTools",
    "RebootTools",
    "SpeedtestTools",
    "SystemLogTools",
    "ToolGroup",
    "WifiTools",
]
