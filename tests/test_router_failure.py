from __future__ import annotations

import pytest
from tplink_deco_api import ApiError, AuthenticationError, CryptoError, TransportError

from tplink_deco_mcp_server.router.router_failure import (
    describe_router_failure,
    is_session_rejected,
)


@pytest.mark.parametrize(
    ("exception", "rejected"),
    [
        (ApiError(-1), True),
        (AuthenticationError("expired"), True),
        (TransportError("unauthorized", status_code=401), True),
        (TransportError("forbidden", status_code=403), True),
        (TransportError("server error", status_code=500), False),
        (TransportError("unreachable"), False),
        (CryptoError("bad padding"), False),
    ],
)
def test_tells_a_dropped_session_apart(exception: Exception, rejected: bool) -> None:  # noqa: FBT001 - parametrized expectation
    assert is_session_rejected(exception) is rejected


@pytest.mark.parametrize(
    ("exception", "message"),
    [
        (
            AuthenticationError("nope"),
            "Failed to list clients: the router rejected the credentials",
        ),
        (TimeoutError(), "Failed to list clients: the router did not answer within 2.5s"),
        (
            ApiError(-40401),
            "Failed to list clients: the router refused the request (error_code=-40401)",
        ),
        (TransportError("connection refused"), "Failed to list clients: connection refused"),
        (OSError(), "Failed to list clients: OSError"),
    ],
)
def test_phrases_the_failure(exception: Exception, message: str) -> None:
    assert describe_router_failure("list clients", exception, 2.5) == message
