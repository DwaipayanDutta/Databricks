"""Authentication manager for Databricks.

Supports:
  * Personal Access Token (static)
  * OAuth (client-credentials, machine-to-machine)
  * Azure Service Principal (AAD client-credentials against the Databricks
    AAD resource id)
  * Azure Managed Identity (IMDS)
  * Bearer Token (static, minted elsewhere)

All strategies expose the same async get_token() -> str interface and cache
the token in memory, refreshing it automatically shortly before expiry.
"""

from __future__ import annotations

import asyncio
import threading
import time
from abc import ABC, abstractmethod

import httpx

from .config import AuthMode, Settings, get_settings
from .exceptions import AuthenticationError, ConfigurationError
from .logging import get_logger

logger = get_logger(__name__)

# Refresh this many seconds before actual expiry to avoid using a stale token.
_REFRESH_SKEW_SECONDS = 60


class TokenProvider(ABC):
    """Base class for all authentication strategies.

    Thread/coroutine safety: `get_token()` uses double-checked locking around
    an `asyncio.Lock` so that when many concurrent requests observe an
    expired token at once, only a single `_fetch_token()` call is made
    (avoiding a "thundering herd" of simultaneous token refreshes against
    the identity provider) while everyone else waits for, then reuses, that
    result.
    """

    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._refresh_lock = asyncio.Lock()

    @abstractmethod
    async def _fetch_token(self) -> tuple[str, float]:
        """Return (token, ttl_seconds)."""

    def _is_valid(self, now: float) -> bool:
        return bool(self._token) and now < self._expires_at - _REFRESH_SKEW_SECONDS

    async def get_token(self) -> str:
        now = time.monotonic()
        if self._is_valid(now):
            return self._token  # type: ignore[return-value]

        async with self._refresh_lock:
            # Re-check: another coroutine may have refreshed while we waited.
            now = time.monotonic()
            if self._is_valid(now):
                return self._token  # type: ignore[return-value]

            token, ttl_seconds = await self._fetch_token()
            self._token = token
            self._expires_at = now + ttl_seconds
            return token

    def invalidate(self) -> None:
        self._token = None
        self._expires_at = 0.0


class PATTokenProvider(TokenProvider):
    """Static Personal Access Token. Never expires from our point of view."""

    def __init__(self, token: str) -> None:
        super().__init__()
        if not token:
            raise ConfigurationError("DATABRICKS_TOKEN is required for PAT auth mode")
        self._static_token = token

    async def _fetch_token(self) -> tuple[str, float]:
        return self._static_token, float("inf") if False else 10**9


class BearerTokenProvider(TokenProvider):
    """Static bearer token supplied out of band (e.g. injected by a platform)."""

    def __init__(self, token: str) -> None:
        super().__init__()
        if not token:
            raise ConfigurationError("BEARER_TOKEN is required for bearer auth mode")
        self._static_token = token

    async def _fetch_token(self) -> tuple[str, float]:
        return self._static_token, 10**9


class OAuthTokenProvider(TokenProvider):
    """OAuth 2.0 client-credentials flow against Databricks' OAuth endpoint."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        scope: str,
    ) -> None:
        super().__init__()
        if not (client_id and client_secret and token_url):
            raise ConfigurationError(
                "DATABRICKS_CLIENT_ID, DATABRICKS_CLIENT_SECRET and "
                "DATABRICKS_OAUTH_TOKEN_URL are required for oauth auth mode"
            )
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_url = token_url
        self._scope = scope

    async def _fetch_token(self) -> tuple[str, float]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                self._token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "scope": self._scope,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if response.status_code >= 400:
            logger.error("oauth_token_fetch_failed", extra={"extra_fields": {"status": response.status_code}})
            raise AuthenticationError("Failed to obtain OAuth token from Databricks")
        payload = response.json()
        return payload["access_token"], float(payload.get("expires_in", 3600))


class AzureServicePrincipalTokenProvider(TokenProvider):
    """Azure AD client-credentials flow, scoped to the Databricks AAD resource."""

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        resource_id: str,
    ) -> None:
        super().__init__()
        if not (tenant_id and client_id and client_secret):
            raise ConfigurationError(
                "AZURE_TENANT_ID, AZURE_CLIENT_ID and AZURE_CLIENT_SECRET are "
                "required for azure_service_principal auth mode"
            )
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._resource_id = resource_id

    async def _fetch_token(self) -> tuple[str, float]:
        url = f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "scope": f"{self._resource_id}/.default",
                },
            )
        if response.status_code >= 400:
            logger.error("aad_token_fetch_failed", extra={"extra_fields": {"status": response.status_code}})
            raise AuthenticationError("Failed to obtain Azure AD token")
        payload = response.json()
        return payload["access_token"], float(payload.get("expires_in", 3600))


class ManagedIdentityTokenProvider(TokenProvider):
    """Azure Instance Metadata Service (IMDS) managed identity flow."""

    def __init__(self, imds_endpoint: str, client_id: str | None, resource_id: str) -> None:
        super().__init__()
        self._imds_endpoint = imds_endpoint
        self._client_id = client_id
        self._resource_id = resource_id

    async def _fetch_token(self) -> tuple[str, float]:
        params = {
            "api-version": "2018-02-01",
            "resource": self._resource_id,
        }
        if self._client_id:
            params["client_id"] = self._client_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                self._imds_endpoint,
                params=params,
                headers={"Metadata": "true"},
            )
        if response.status_code >= 400:
            logger.error(
                "managed_identity_fetch_failed", extra={"extra_fields": {"status": response.status_code}}
            )
            raise AuthenticationError("Failed to obtain Managed Identity token")
        payload = response.json()
        expires_in = payload.get("expires_in")
        ttl = float(expires_in) if expires_in else 3600.0
        return payload["access_token"], ttl


class AuthManager:
    """Facade selecting and driving the configured TokenProvider."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._provider = self._build_provider(settings)

    def _build_provider(self, settings: Settings) -> TokenProvider:
        mode = settings.auth_mode
        if mode == AuthMode.PAT:
            return PATTokenProvider(settings.databricks_token or "")
        if mode == AuthMode.BEARER:
            return BearerTokenProvider(settings.bearer_token or "")
        if mode == AuthMode.OAUTH:
            return OAuthTokenProvider(
                client_id=settings.databricks_client_id or "",
                client_secret=settings.databricks_client_secret or "",
                token_url=settings.databricks_oauth_token_url or f"{settings.databricks_host}/oidc/v1/token",
                scope=settings.databricks_oauth_scope,
            )
        if mode == AuthMode.AZURE_SERVICE_PRINCIPAL:
            return AzureServicePrincipalTokenProvider(
                tenant_id=settings.azure_tenant_id or "",
                client_id=settings.azure_client_id or "",
                client_secret=settings.azure_client_secret or "",
                resource_id=settings.azure_resource_id,
            )
        if mode == AuthMode.MANAGED_IDENTITY:
            return ManagedIdentityTokenProvider(
                imds_endpoint=settings.azure_imds_endpoint,
                client_id=settings.azure_managed_identity_client_id,
                resource_id=settings.azure_resource_id,
            )
        raise ConfigurationError(f"Unsupported auth mode: {mode}")

    async def get_auth_header(self) -> dict[str, str]:
        token = await self._provider.get_token()
        return {"Authorization": f"Bearer {token}"}

    def invalidate(self) -> None:
        self._provider.invalidate()


_auth_manager: AuthManager | None = None
_auth_manager_lock = threading.Lock()


def get_auth_manager() -> AuthManager:
    """Return the process-wide singleton AuthManager, creating it lazily.

    This is intentionally lazy (rather than created at import time) so that
    settings are only read -- and validated -- the first time a token is
    actually needed, not merely when this module is imported. Creation is
    guarded by a `threading.Lock` so it is safe to call from multiple
    threads (e.g. uvicorn's threadpool for sync dependencies) as well as
    concurrently from multiple asyncio coroutines.
    """
    global _auth_manager
    if _auth_manager is None:
        with _auth_manager_lock:
            if _auth_manager is None:  # re-check inside the lock
                _auth_manager = AuthManager(get_settings())
    return _auth_manager
