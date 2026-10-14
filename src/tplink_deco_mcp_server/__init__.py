"""MCP server exposing a TP-Link Deco mesh as tools for LLM clients."""

from __future__ import annotations

from .router import RouterSession, RouterSettings
from .server import build_server

__all__ = ["RouterSession", "RouterSettings", "build_server"]
