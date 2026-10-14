"""Gateway load and current traffic, as shown to the model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from collections.abc import Sequence

    from tplink_deco_api import ClientDevice, Performance


class PerformanceSummary(BaseModel):
    """CPU and memory of the gateway plus the traffic of every client right now."""

    model_config = ConfigDict(frozen=True)

    cpu_usage_percent: float
    memory_usage_percent: float
    online_clients: int
    total_download_kilobytes_per_second: int = Field(
        description="Sum of every client's download rate."
    )
    total_upload_kilobytes_per_second: int = Field(description="Sum of every client's upload rate.")

    @classmethod
    def from_readings(
        cls, performance: Performance, clients: Sequence[ClientDevice]
    ) -> PerformanceSummary:
        """Combine the gateway load with the traffic of ``clients``."""
        return cls(
            cpu_usage_percent=round(performance.cpu_usage * 100, 1),
            memory_usage_percent=round(performance.mem_usage * 100, 1),
            online_clients=sum(1 for client in clients if client.online),
            total_download_kilobytes_per_second=sum(client.down_speed for client in clients),
            total_upload_kilobytes_per_second=sum(client.up_speed for client in clients),
        )
