"""How a tool group publishes its methods on the MCP server."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Protocol

from mcp.types import ToolAnnotations

if TYPE_CHECKING:
    from collections.abc import Callable

    from mcp.server.mcpserver import MCPServer

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
CHANGES_SETTINGS = ToolAnnotations(
    read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False
)
DISCARDS_SETTINGS = ToolAnnotations(
    read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=False
)


class ToolGroup(Protocol):
    """A set of related tools that registers itself on a server."""

    def register(self, server: MCPServer[None]) -> None:
        """Add every tool of the group to ``server``."""


def register_tool[**P, R](
    server: MCPServer[None],
    method: Callable[P, R],
    *,
    title: str,
    annotations: ToolAnnotations,
) -> None:
    """Publish ``method`` under its own name, its docstring becoming the model-facing text."""
    server.add_tool(
        method,
        title=title,
        description=inspect.cleandoc(method.__doc__ or ""),
        annotations=annotations,
    )
