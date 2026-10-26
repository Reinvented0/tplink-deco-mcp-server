"""Read-only access to router forms that have no dedicated tool yet."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import Field

from .tool_registration import READ_ONLY, register_tool

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer

    from ..router import RouterSession


class RawTools:
    """Reads any admin form directly, for diagnosing what a firmware exposes."""

    def __init__(self, router: RouterSession) -> None:
        self._router = router

    def register(self, server: MCPServer[None]) -> None:
        """Add the raw tools to ``server``."""
        register_tool(
            server, self.read_router_form, title="Read router form", annotations=READ_ONLY
        )

    def read_router_form(
        self,
        path: Annotated[
            Literal["admin/device", "admin/client", "admin/network", "admin/wireless"],
            Field(description="Router API path, e.g. `admin/device`."),
        ],
        form: Annotated[
            str,
            Field(
                pattern=r"^[a-z0-9_]{1,40}$",
                description="Form name, e.g. `speedtest`, `client_access`, `bridge`.",
            ),
        ],
        operation: Annotated[
            Literal["read", "list", "getlist"],
            Field(description="Read operation the form expects. Default: `read`."),
        ] = "read",
        device_mac: Annotated[
            str | None,
            Field(
                pattern=r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$|^default$",
                description=(
                    "Scope the read to one Deco unit (its MAC from `list_deco_nodes`), "
                    "sent as `params.device_mac`. Omit to send no params."
                ),
            ),
        ] = None,
    ) -> dict[str, object]:
        """Read a router form verbatim when no dedicated tool covers it.

        Returns the router's decrypted `result` object unchanged. Only read
        operations are allowed. Prefer the dedicated tools; use this to see
        what a firmware exposes, e.g. `admin/device` + `speedtest` or
        `admin/client` + `traffic_stat` with operation `list`.
        """
        if device_mac is None:
            return self._router.run(
                f"read {path}?form={form}",
                lambda deco: dict(deco.request(path, form, {"operation": operation})),
            )
        scope = device_mac if device_mac == "default" else device_mac.replace(":", "-").upper()
        return self._router.run(
            f"read {path}?form={form}",
            lambda deco: dict(
                deco.request(path, form, {"operation": operation, "params": {"device_mac": scope}})
            ),
        )
