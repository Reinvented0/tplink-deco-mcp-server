"""The gateway's own WAN speed test, as shown to the model."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from collections.abc import Mapping

_KILOBITS_PER_MEGABIT = 1000


class SpeedtestSummary(BaseModel):
    """Result of the last speed test the gateway ran against the internet."""

    model_config = ConfigDict(frozen=True)

    status: str = Field(description="`idle` when no test runs; `testing` while one is running.")
    ever_tested: bool = Field(description="False until the router has completed a first test.")
    download_megabits_per_second: float
    upload_megabits_per_second: float
    ping_milliseconds: float
    jitter_milliseconds: float
    tested_at: str = Field(description="When the stored result was measured, ISO 8601 in UTC.")

    @classmethod
    def from_api(cls, result: Mapping[str, object]) -> SpeedtestSummary:
        """Build the summary from an ``admin/device?form=speedtest`` read."""
        # The router reports the rates in kbit/s.
        tested = _number(result, "last_speed_test_time")
        return cls(
            status=str(result.get("status") or ""),
            ever_tested=result.get("ever_tested") is True,
            download_megabits_per_second=round(
                _number(result, "down_speed") / _KILOBITS_PER_MEGABIT, 1
            ),
            upload_megabits_per_second=round(
                _number(result, "up_speed") / _KILOBITS_PER_MEGABIT, 1
            ),
            ping_milliseconds=_number(result, "ping_time"),
            jitter_milliseconds=_number(result, "ping_jitter"),
            tested_at=datetime.fromtimestamp(tested, UTC).isoformat() if tested > 0 else "",
        )


def _number(result: Mapping[str, object], key: str) -> float:
    value = result.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0.0
    return float(value)
