"""Classify SDK failures and phrase them for the model reading the tool result."""

from __future__ import annotations

from tplink_deco_api import ApiError, AuthenticationError, DecoError, TransportError

_SESSION_REJECTED_STATUS_CODES = frozenset({401, 403})


def is_session_rejected(exception: DecoError) -> bool:
    """Tell a router-side session drop apart from a genuine failure.

    The router keeps a single session per account, so another login (the Deco
    app, a Home Assistant poll) silently invalidates ours and the next request
    comes back as an ``ApiError`` or an HTTP 401/403.
    """
    if isinstance(exception, TransportError):
        return exception.status_code in _SESSION_REJECTED_STATUS_CODES
    return isinstance(exception, ApiError | AuthenticationError)


def describe_router_failure(action: str, exception: Exception, timeout_seconds: float) -> str:
    """Return a short ``Failed to <action>: <cause>`` message for a failed router call."""
    if isinstance(exception, AuthenticationError):
        cause = "the router rejected the credentials"
    elif isinstance(exception, TimeoutError):
        cause = f"the router did not answer within {timeout_seconds:g}s"
    elif isinstance(exception, ApiError):
        cause = f"the router refused the request (error_code={exception.error_code})"
    else:
        cause = str(exception) or type(exception).__name__
    return f"Failed to {action}: {cause}"
