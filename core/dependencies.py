"""Shared ContextVars and FastAPI dependency helpers.

request_id and correlation_id are set by CorrelationMiddleware early in the
request lifecycle and are read from anywhere in the call stack (services,
the Databricks client, logging) without needing to thread them through
every function signature.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

from fastapi import Header, Request

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def new_request_id() -> str:
    return str(uuid.uuid4())


def get_request_id(request: Request) -> str:
    """FastAPI dependency returning the current request's ID."""
    return getattr(request.state, "request_id", request_id_ctx.get() or new_request_id())


def get_correlation_id(
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
) -> str:
    """FastAPI dependency returning (or minting) a correlation ID."""
    return x_correlation_id or correlation_id_ctx.get() or new_request_id()


async def verify_connector_api_key(request: Request) -> None:
    """Optional API-key gate for the connector's own endpoints.

    If settings.connector_api_key is unset, this is a no-op, so the
    connector works out of the box in local/dev environments.
    """
    from core.config import get_settings
    from core.exceptions import AuthenticationError

    settings = get_settings()
    if not settings.connector_api_key:
        return

    provided = request.headers.get("X-API-Key")
    if provided != settings.connector_api_key:
        raise AuthenticationError("Missing or invalid connector API key")
