"""Argument types shared by several tools."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

MacAddress = Annotated[
    str,
    Field(description="MAC address of the device, `AA:BB:CC:DD:EE:FF` or `AA-BB-CC-DD-EE-FF`."),
]


def canonical_mac(value: str) -> str:
    """Return ``value`` colon-separated and uppercase, the form every tool result uses."""
    return value.replace("-", ":").upper()


def same_mac(left: str, right: str) -> bool:
    """Compare two MAC addresses regardless of separator and case."""
    return canonical_mac(left) == canonical_mac(right)
