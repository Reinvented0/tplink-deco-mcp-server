"""Where the router lives and how to log in to it."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

_DEFAULT_USERNAME = "admin"
_DEFAULT_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class RouterSettings:
    """Address and credentials of the Deco gateway node."""

    host: str
    password: str = field(repr=False)
    username: str = _DEFAULT_USERNAME
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS
    allow_reboot: bool = False

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> RouterSettings:
        """Read the ``DECO_*`` variables: host, password, username, timeout, allow-reboot."""
        host = environment.get("DECO_HOST", "").strip()
        password = environment.get("DECO_PASSWORD", "")
        if not host or not password:
            message = "Failed to read settings: DECO_HOST and DECO_PASSWORD must be set"
            raise ValueError(message)
        return cls(
            host=host,
            password=password,
            username=environment.get("DECO_USERNAME", "").strip() or _DEFAULT_USERNAME,
            timeout_seconds=_parse_timeout(environment.get("DECO_TIMEOUT", "")),
            allow_reboot=environment.get("DECO_ALLOW_REBOOT", "").strip().lower()
            in {"1", "true", "yes"},
        )


def _parse_timeout(value: str) -> float:
    if not value.strip():
        return _DEFAULT_TIMEOUT_SECONDS
    try:
        timeout = float(value)
    except ValueError as exception:
        message = f"Failed to read settings: DECO_TIMEOUT={value!r} is not a number"
        raise ValueError(message) from exception
    if timeout <= 0:
        message = f"Failed to read settings: DECO_TIMEOUT={value!r} must be positive"
        raise ValueError(message)
    return timeout
