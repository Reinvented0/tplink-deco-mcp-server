"""Access to the router: connection settings and the shared authenticated session."""

from __future__ import annotations

from .router_session import RouterSession
from .router_settings import RouterSettings

__all__ = ["RouterSession", "RouterSettings"]
