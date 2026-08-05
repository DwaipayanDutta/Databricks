"""ASGI middleware: correlation IDs, request timing/logging, exceptions."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.constants import HEADER_CORRELATION_ID, HEADER_REQUEST_ID
from core.dependencies import correlation_id_ctx, new_request_id, request_id_ctx
from core.exceptions import DatabricksConnectorError
from core.logging import get_logger

logger = get_logger(__name__)

RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Mints/propagates X-Request-ID and X-Correlation-ID for every request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(HEADER_REQUEST_ID) or new_request_id()
        correlation_id = request.headers.get(HEADER_CORRELATION_ID) or request_id

        request_id_ctx.set(request_id)
        correlation_id_ctx.set(correlation_id)
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers[HEADER_REQUEST_ID] = request_id
        response.headers[HEADER_CORRELATION_ID] = correlation_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Adds a X-Response-Time-ms header and logs latency for every request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Response-Time-ms"] = str(elapsed_ms)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs one structured line per inbound HTTP request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "http_request",
            extra={
                "extra_fields": {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "elapsed_ms": elapsed_ms,
                    "client": request.client.host if request.client else None,
                }
            },
        )
        return response


class ExceptionMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions and returns a consistent JSON error body.

    DatabricksConnectorError subclasses are translated using their own
    status_code/error_code; anything else becomes a generic 500.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except DatabricksConnectorError as exc:
            logger.warning(
                "connector_error",
                extra={"extra_fields": {"error_code": exc.error_code, "message": exc.message}},
            )
            return JSONResponse(status_code=exc.status_code, content=exc.to_dict())
        except Exception as exc:  # noqa: BLE001 - top level safety net
            logger.exception("unhandled_exception")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": "An unexpected error occurred",
                    "details": {"exception_type": type(exc).__name__},
                },
            )
