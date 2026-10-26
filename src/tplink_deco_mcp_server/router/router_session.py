"""The one authenticated router session every tool call goes through."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from mcp.server.mcpserver.exceptions import ToolError
from tplink_deco_api import DecoClient, DecoError

from .router_failure import describe_router_failure, is_session_rejected

if TYPE_CHECKING:
    from collections.abc import Callable

    from .router_settings import RouterSettings

log: logging.Logger = logging.getLogger("tplink_deco_mcp_server.router")

type ClientFactory = Callable[[RouterSettings], DecoClient]


def _open_client(settings: RouterSettings) -> DecoClient:
    return DecoClient(
        settings.host,
        settings.username,
        settings.password,
        timeout=settings.timeout_seconds,
    )


class RouterSession:
    """Serializes router calls over a reused session, logging in again when it is dropped.

    Logging in costs a full RSA handshake and evicts any other holder of the
    account's single session, so the session is kept open between tool calls
    and renewed only once the router rejects it.
    """

    def __init__(
        self, settings: RouterSettings, client_factory: ClientFactory = _open_client
    ) -> None:
        self._settings = settings
        self._client_factory = client_factory
        self._client: DecoClient | None = None
        self._lock = threading.Lock()

    @property
    def settings(self) -> RouterSettings:
        """The settings this session logs in with."""
        return self._settings

    def run[T](self, action: str, operation: Callable[[DecoClient], T]) -> T:
        """Run ``operation`` against the router, turning every failure into a ``ToolError``.

        ``action`` completes the sentence "Failed to …" in the error message.
        """
        with self._lock:
            try:
                return self._run_renewing_session(operation)
            except ValueError as exception:
                raise ToolError(str(exception)) from exception
            except (DecoError, OSError) as exception:
                self._client = None
                message = describe_router_failure(action, exception, self._settings.timeout_seconds)
                log.warning("%s", message)
                raise ToolError(message) from exception

    def _run_renewing_session[T](self, operation: Callable[[DecoClient], T]) -> T:
        client = self._client
        if client is None:
            return operation(self._login())
        try:
            return operation(client)
        except DecoError as exception:
            if not is_session_rejected(exception):
                raise
            log.debug("Router rejected the open session, logging in again")
            return operation(self._login())

    def _login(self) -> DecoClient:
        client = self._client_factory(self._settings)
        client.login()
        self._client = client
        return client
