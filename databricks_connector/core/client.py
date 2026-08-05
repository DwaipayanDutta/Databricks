"""Async Databricks REST API client.

A single reusable client used by every service layer module. It handles:
  * automatic auth (via AuthManager)
  * automatic retries (via core.retry, tenacity based)
  * circuit breaking (via core.circuit_breaker)
  * automatic request id / correlation id propagation
  * consistent JSON response parsing and error translation
"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any, cast

import httpx

from .auth import AuthManager, get_auth_manager
from .circuit_breaker import CircuitBreaker, get_circuit_breaker
from .config import Settings, get_settings
from .constants import CONNECTOR_NAME, CONNECTOR_VERSION, HEADER_CORRELATION_ID, HEADER_REQUEST_ID
from .dependencies import correlation_id_ctx, new_request_id, request_id_ctx
from .exceptions import DatabricksConnectorError, ServiceUnavailableError, exception_for_status
from .logging import get_logger
from .metrics import record_databricks_call
from .retry import RetryableHTTPError, build_retry_decorator, is_retryable_status

logger = get_logger(__name__)


class DatabricksClient:
    """Thin async wrapper around httpx for calling the Databricks REST API."""

    def __init__(
        self,
        settings: Settings | None = None,
        auth_manager: AuthManager | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._auth_manager = auth_manager or get_auth_manager()
        self._circuit_breaker = circuit_breaker or get_circuit_breaker(
            "databricks",
            failure_threshold=self._settings.circuit_breaker_failure_threshold,
            recovery_timeout=self._settings.circuit_breaker_recovery_timeout,
        )
        self._retry_decorator = build_retry_decorator(
            self._settings.max_retries, self._settings.backoff_factor
        )
        self._http: httpx.AsyncClient | None = None
        self._http_lock = asyncio.Lock()

    async def _get_http(self) -> httpx.AsyncClient:
        """Return the pooled httpx.AsyncClient, creating it lazily and
        exactly once (guarded by an asyncio.Lock so concurrent callers
        don't race to open duplicate connection pools).
        """
        if self._http is not None and not self._http.is_closed:
            return self._http

        async with self._http_lock:
            # Re-check inside the lock: another coroutine may have already
            # created the pool while we were waiting for it.
            if self._http is None or self._http.is_closed:
                timeout = httpx.Timeout(
                    self._settings.request_timeout_seconds,
                    connect=self._settings.connect_timeout_seconds,
                )
                limits = httpx.Limits(
                    max_connections=self._settings.http_max_connections,
                    max_keepalive_connections=self._settings.http_max_keepalive_connections,
                    keepalive_expiry=self._settings.http_keepalive_expiry_seconds,
                )
                self._http = httpx.AsyncClient(
                    base_url=self._settings.databricks_host.rstrip("/"),
                    timeout=timeout,
                    limits=limits,
                )
        return self._http

    async def aclose(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    async def _headers(self) -> dict[str, str]:
        auth_headers = await self._auth_manager.get_auth_header()
        request_id = request_id_ctx.get() or new_request_id()
        correlation_id = correlation_id_ctx.get() or request_id
        return {
            **auth_headers,
            "Content-Type": "application/json",
            "User-Agent": f"{CONNECTOR_NAME}/{CONNECTOR_VERSION}",
            HEADER_REQUEST_ID: request_id,
            HEADER_CORRELATION_ID: correlation_id,
        }

    async def _do_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        http = await self._get_http()
        headers = await self._headers()

        # tenacity's `retry(...)` factory returns a dynamically-typed
        # decorator (it wraps arbitrary callables generically), so mypy
        # can't infer that this preserves `_attempt`'s signature the way it
        # does at runtime -- suppressed narrowly here rather than loosening
        # typing anywhere else in this module.
        @self._retry_decorator  # type: ignore[misc]
        async def _attempt() -> httpx.Response:
            response = await http.request(
                method,
                path,
                params=params,
                json=json_body,
                headers=headers,
            )
            if is_retryable_status(response.status_code):
                raise RetryableHTTPError(response)
            return response

        # tenacity's `retry(...)` decorator factory has a dynamically-typed
        # return value (it wraps arbitrary callables), so mypy sees
        # `_attempt` as untyped once decorated; `_attempt` itself is
        # annotated `-> httpx.Response` above and that's what actually
        # executes at runtime, so this cast reasserts the true type rather
        # than suppressing a real error.
        return cast(httpx.Response, await _attempt())

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            response = await self._circuit_breaker.call(
                self._do_request, method, path, params=params, json_body=json_body
            )
        except DatabricksConnectorError:
            raise
        except httpx.TimeoutException as exc:
            raise ServiceUnavailableError(f"Timed out calling Databricks: {exc}") from exc
        except httpx.HTTPError as exc:
            raise ServiceUnavailableError(f"Network error calling Databricks: {exc}") from exc

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        # Databricks (and the AWS/Azure/GCP load balancers in front of it)
        # may echo back a request-tracing header useful for correlating our
        # logs with Databricks-side support tickets; capture it if present
        # under any of the header names Databricks/cloud providers use.
        databricks_request_id = (
            response.headers.get("X-Databricks-Request-Id")
            or response.headers.get("x-request-id")
            or response.headers.get("x-amzn-requestid")
        )
        log_fields: dict[str, Any] = {
            "method": method,
            "path": path,
            "status": response.status_code,
            "elapsed_ms": elapsed_ms,
        }
        if databricks_request_id:
            log_fields["databricks_request_id"] = databricks_request_id
        logger.info("databricks_api_call", extra={"extra_fields": log_fields})
        record_databricks_call(
            method=method, path=path, status_code=response.status_code, elapsed_ms=elapsed_ms
        )

        return self._parse_response(response)

    def _parse_response(self, response: httpx.Response) -> dict[str, Any]:
        if response.status_code >= 400:
            try:
                body = response.json()
                message = body.get("message") or body.get("error") or response.text
            except ValueError:
                body = {}
                message = response.text
            raise exception_for_status(response.status_code, message, details=body)

        if response.status_code == 204 or not response.content:
            return {}

        try:
            # httpx's `.json()` is typed to return `Any` (JSON can decode to
            # any type); Databricks always returns a JSON object for our
            # endpoints, so we assert that contract here rather than
            # threading `Any` through every caller.
            return cast(dict[str, Any], response.json())
        except ValueError:
            return {"raw": response.text}

    # --- Public verb methods -------------------------------------------------

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("POST", path, json_body=json_body)

    async def put(self, path: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("PUT", path, json_body=json_body)

    async def patch(self, path: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("PATCH", path, json_body=json_body)

    async def delete(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("DELETE", path, params=params)


_client: DatabricksClient | None = None
_client_lock = threading.Lock()


def get_databricks_client() -> DatabricksClient:
    """FastAPI dependency / module-level accessor returning the process-wide
    singleton DatabricksClient (and, transitively, its pooled httpx
    connection pool). Creation is guarded by a `threading.Lock` for safety
    even if called from multiple threads; used as a FastAPI dependency it
    is called once per request but always returns the same instance.
    """
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:  # re-check inside the lock
                _client = DatabricksClient()
    return _client


async def close_databricks_client() -> None:
    """Gracefully close the shared client's connection pool.

    Called from `app.py`'s lifespan shutdown hook so in-flight connections
    are drained rather than dropped when the process stops.
    """
    global _client
    with _client_lock:
        client_to_close = _client
        _client = None
    if client_to_close is not None:
        await client_to_close.aclose()
