"""Async Databricks REST API client.

A single reusable client used by every service layer module. It handles:
  * automatic auth (via AuthManager)
  * automatic retries (via core.retry, tenacity based)
  * circuit breaking (via core.circuit_breaker)
  * automatic request id / correlation id propagation
  * consistent JSON response parsing and error translation
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from core.auth import AuthManager, get_auth_manager
from core.circuit_breaker import CircuitBreaker, get_circuit_breaker
from core.config import Settings, get_settings
from core.constants import CONNECTOR_NAME, CONNECTOR_VERSION, HEADER_CORRELATION_ID, HEADER_REQUEST_ID
from core.dependencies import correlation_id_ctx, new_request_id, request_id_ctx
from core.exceptions import DatabricksConnectorError, ServiceUnavailableError, exception_for_status
from core.logging import get_logger
from core.retry import RetryableHTTPError, build_retry_decorator, is_retryable_status

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

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            timeout = httpx.Timeout(
                self._settings.request_timeout_seconds,
                connect=self._settings.connect_timeout_seconds,
            )
            self._http = httpx.AsyncClient(
                base_url=self._settings.databricks_host.rstrip("/"),
                timeout=timeout,
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

        @self._retry_decorator
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

        return await _attempt()

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
        logger.info(
            "databricks_api_call",
            extra={
                "extra_fields": {
                    "method": method,
                    "path": path,
                    "status": response.status_code,
                    "elapsed_ms": elapsed_ms,
                }
            },
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
            return response.json()
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


def get_databricks_client() -> DatabricksClient:
    """FastAPI dependency / module-level accessor returning a shared client."""
    global _client
    if _client is None:
        _client = DatabricksClient()
    return _client


async def close_databricks_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
