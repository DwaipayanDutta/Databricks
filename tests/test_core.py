"""Unit tests for core building blocks: auth, retry, circuit breaker, cache.

These are pure unit tests (no FastAPI TestClient) that exercise the
lower-level building blocks directly, which is where most of the
connector's non-HTTP logic lives.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest
import respx

from core.auth import BearerTokenProvider, PATTokenProvider
from core.cache import CacheClient
from core.circuit_breaker import CircuitBreaker, CircuitState
from core.config import AuthMode, Settings
from core.exceptions import CircuitBreakerOpenError, ConfigurationError
from core.retry import _parse_retry_after


def test_pat_token_provider_returns_static_token() -> None:
    provider = PATTokenProvider("dapi123")
    token = asyncio.run(provider.get_token())
    assert token == "dapi123"


def test_pat_token_provider_requires_token() -> None:
    with pytest.raises(ConfigurationError):
        PATTokenProvider("")


def test_bearer_token_provider() -> None:
    provider = BearerTokenProvider("bearer-xyz")
    token = asyncio.run(provider.get_token())
    assert token == "bearer-xyz"


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold() -> None:
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60, name="test")

    async def failing() -> None:
        raise RuntimeError("boom")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            await breaker.call(failing)

    assert breaker.state == CircuitState.OPEN

    async def would_succeed() -> str:
        return "ok"

    with pytest.raises(CircuitBreakerOpenError):
        await breaker.call(would_succeed)


@pytest.mark.asyncio
async def test_circuit_breaker_closes_on_success() -> None:
    breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60, name="test2")

    async def succeeding() -> str:
        return "ok"

    result = await breaker.call(succeeding)
    assert result == "ok"
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_allows_single_trial_only() -> None:
    """Regression test: HALF_OPEN must let exactly one concurrent trial
    request through; every other concurrent caller should fail fast rather
    than piling onto a still-recovering dependency."""
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05, name="half-open-test")

    async def failing() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await breaker.call(failing)
    assert breaker.state == CircuitState.OPEN

    await asyncio.sleep(0.06)  # let the recovery window elapse

    async def slow_success() -> str:
        await asyncio.sleep(0.05)
        return "ok"

    results: dict[str, tuple[str, str | None]] = {}

    async def attempt(tag: str) -> None:
        try:
            value = await breaker.call(slow_success)
            results[tag] = ("success", value)
        except CircuitBreakerOpenError:
            results[tag] = ("blocked", None)

    await asyncio.gather(attempt("a"), attempt("b"), attempt("c"))

    outcomes = [v[0] for v in results.values()]
    assert outcomes.count("success") == 1
    assert outcomes.count("blocked") == 2
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_reopens_on_half_open_failure() -> None:
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05, name="reopen-test")

    async def failing() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await breaker.call(failing)
    assert breaker.state == CircuitState.OPEN

    await asyncio.sleep(0.06)

    with pytest.raises(RuntimeError):
        await breaker.call(failing)  # the single half-open trial also fails
    assert breaker.state == CircuitState.OPEN


def test_retry_after_parses_seconds() -> None:
    assert _parse_retry_after("5") == 5.0
    assert _parse_retry_after("0") == 0.0


def test_retry_after_clamps_large_values() -> None:
    assert _parse_retry_after("99999") == 120.0


def test_retry_after_handles_missing_and_invalid() -> None:
    assert _parse_retry_after(None) is None
    assert _parse_retry_after("") is None
    assert _parse_retry_after("not-a-valid-value") is None


def test_retry_after_parses_http_date() -> None:
    from datetime import UTC, datetime, timedelta
    from email.utils import format_datetime

    future = datetime.now(UTC) + timedelta(seconds=10)
    header_value = format_datetime(future, usegmt=True)
    parsed = _parse_retry_after(header_value)
    assert parsed is not None
    assert 0 <= parsed <= 15


@pytest.mark.asyncio
async def test_in_memory_cache_roundtrip() -> None:
    settings = Settings(
        databricks_host="https://example.cloud.databricks.com",
        databricks_token="dummy",
        auth_mode=AuthMode.PAT,
        cache_enabled=True,
        redis_url=None,
    )
    cache = CacheClient(settings)
    await cache.set("key1", {"a": 1}, ttl_seconds=30)
    value = await cache.get("key1")
    assert value == {"a": 1}
    await cache.delete("key1")
    assert await cache.get("key1") is None


@pytest.mark.asyncio
async def test_cache_disabled_is_noop() -> None:
    settings = Settings(
        databricks_host="https://example.cloud.databricks.com",
        databricks_token="dummy",
        auth_mode=AuthMode.PAT,
        cache_enabled=False,
    )
    cache = CacheClient(settings)
    await cache.set("key1", "value", ttl_seconds=30)
    assert await cache.get("key1") is None


@pytest.mark.asyncio
@respx.mock
async def test_databricks_client_get_success() -> None:
    from core.auth import AuthManager
    from core.client import DatabricksClient

    settings = Settings(
        databricks_host="https://example.cloud.databricks.com",
        databricks_token="dummy",
        auth_mode=AuthMode.PAT,
        max_retries=1,
    )
    auth_manager = AuthManager(settings)
    breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30, name="unit-test")
    client = DatabricksClient(settings=settings, auth_manager=auth_manager, circuit_breaker=breaker)

    route = respx.get("https://example.cloud.databricks.com/api/2.1/clusters/list").mock(
        return_value=httpx.Response(200, json={"clusters": []})
    )

    result = await client.get("/api/2.1/clusters/list")
    assert result == {"clusters": []}
    assert route.called
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_databricks_client_maps_404() -> None:
    from core.auth import AuthManager
    from core.client import DatabricksClient
    from core.exceptions import NotFoundError

    settings = Settings(
        databricks_host="https://example.cloud.databricks.com",
        databricks_token="dummy",
        auth_mode=AuthMode.PAT,
        max_retries=0,
    )
    auth_manager = AuthManager(settings)
    breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30, name="unit-test-404")
    client = DatabricksClient(settings=settings, auth_manager=auth_manager, circuit_breaker=breaker)

    respx.get("https://example.cloud.databricks.com/api/2.1/jobs/get").mock(
        return_value=httpx.Response(404, json={"message": "Job not found"})
    )

    with pytest.raises(NotFoundError):
        await client.get("/api/2.1/jobs/get", params={"job_id": 1})
    await client.aclose()


@pytest.mark.asyncio
async def test_get_databricks_client_singleton_thread_safe() -> None:
    """get_databricks_client() must return the exact same instance even when
    called concurrently from many coroutines (guards against the
    check-then-set race on the module-level singleton)."""
    import core.client as client_module

    client_module._client = None  # reset singleton for a clean test
    try:
        results = await asyncio.gather(
            *[asyncio.to_thread(client_module.get_databricks_client) for _ in range(10)]
        )
        assert len({id(r) for r in results}) == 1
    finally:
        await client_module.close_databricks_client()


@pytest.mark.asyncio
async def test_close_databricks_client_is_idempotent() -> None:
    import core.client as client_module

    client_module._client = None
    client_module.get_databricks_client()
    await client_module.close_databricks_client()
    await client_module.close_databricks_client()  # must not raise
    assert client_module._client is None


@pytest.mark.asyncio
async def test_token_provider_refresh_is_single_flight() -> None:
    """Concurrent get_token() calls on an expired token must trigger exactly
    one _fetch_token() call, not one per caller."""

    class CountingProvider(PATTokenProvider):
        def __init__(self) -> None:
            super().__init__("seed-token")
            self.fetch_count = 0

        async def _fetch_token(self) -> tuple[str, float]:
            self.fetch_count += 1
            await asyncio.sleep(0.02)
            return "refreshed-token", 3600.0

    provider = CountingProvider()
    provider.invalidate()  # force every caller to see an expired token

    tokens = await asyncio.gather(*[provider.get_token() for _ in range(8)])
    assert all(t == "refreshed-token" for t in tokens)
    assert provider.fetch_count == 1


@pytest.mark.asyncio
async def test_health_service_ready_when_databricks_reachable() -> None:
    from unittest.mock import AsyncMock

    from services.health_service import HealthService

    fake_client = AsyncMock()
    fake_client.get.return_value = {}
    service = HealthService(fake_client)
    result = await service.check_readiness()
    assert result["status"] == "ready"
    assert result["dependencies"]["databricks_api"] == "reachable"


@pytest.mark.asyncio
async def test_health_service_not_ready_on_connector_error() -> None:
    from unittest.mock import AsyncMock

    from core.exceptions import ServiceUnavailableError
    from services.health_service import HealthService

    fake_client = AsyncMock()
    fake_client.get.side_effect = ServiceUnavailableError("down")
    service = HealthService(fake_client)
    result = await service.check_readiness()
    assert result["status"] == "not_ready"
    assert "service_unavailable" in result["dependencies"]["databricks_api"]


@pytest.mark.asyncio
async def test_health_service_not_ready_on_unexpected_error() -> None:
    from unittest.mock import AsyncMock

    from services.health_service import HealthService

    fake_client = AsyncMock()
    fake_client.get.side_effect = RuntimeError("boom")
    service = HealthService(fake_client)
    result = await service.check_readiness()
    assert result["status"] == "not_ready"
    assert result["dependencies"]["databricks_api"] == "unreachable"


def test_exception_status_code_map_covers_documented_codes() -> None:
    from core.exceptions import (
        AuthenticationError,
        AuthorizationError,
        ConflictError,
        NotFoundError,
        RateLimitError,
        ServiceUnavailableError,
        TimeoutErrorConnector,
        ValidationAPIError,
        exception_for_status,
    )

    cases = {
        400: ValidationAPIError,
        401: AuthenticationError,
        403: AuthorizationError,
        404: NotFoundError,
        409: ConflictError,
        429: RateLimitError,
        503: ServiceUnavailableError,
        504: TimeoutErrorConnector,
    }
    for status_code, expected_cls in cases.items():
        exc = exception_for_status(status_code, "msg")
        assert isinstance(exc, expected_cls)
        assert exc.status_code == status_code


@pytest.mark.asyncio
async def test_oauth_token_provider_fetches_and_caches(respx_mock=None) -> None:
    import respx

    from core.auth import OAuthTokenProvider

    with respx.mock:
        route = respx.post("https://example.cloud.databricks.com/oidc/v1/token").mock(
            return_value=httpx.Response(200, json={"access_token": "oauth-tok", "expires_in": 3600})
        )
        provider = OAuthTokenProvider(
            client_id="id",
            client_secret="secret",
            token_url="https://example.cloud.databricks.com/oidc/v1/token",
            scope="all-apis",
        )
        token = await provider.get_token()
        assert token == "oauth-tok"
        assert route.call_count == 1

        # Second call within TTL should be served from cache, not refetch.
        token2 = await provider.get_token()
        assert token2 == "oauth-tok"
        assert route.call_count == 1


def test_oauth_token_provider_requires_credentials() -> None:
    from core.auth import OAuthTokenProvider

    with pytest.raises(ConfigurationError):
        OAuthTokenProvider(client_id="", client_secret="", token_url="", scope="all-apis")


def test_azure_service_principal_requires_credentials() -> None:
    from core.auth import AzureServicePrincipalTokenProvider

    with pytest.raises(ConfigurationError):
        AzureServicePrincipalTokenProvider(tenant_id="", client_id="", client_secret="", resource_id="r")


@pytest.mark.asyncio
async def test_managed_identity_token_provider_fetches_token() -> None:
    import respx

    from core.auth import ManagedIdentityTokenProvider

    with respx.mock:
        respx.get("http://169.254.169.254/metadata/identity/oauth2/token").mock(
            return_value=httpx.Response(200, json={"access_token": "mi-tok", "expires_in": "3600"})
        )
        provider = ManagedIdentityTokenProvider(
            imds_endpoint="http://169.254.169.254/metadata/identity/oauth2/token",
            client_id=None,
            resource_id="2ff814a6-3304-4ab8-85cb-cd0e6f879c1d",
        )
        token = await provider.get_token()
        assert token == "mi-tok"


def test_auth_manager_builds_correct_provider_per_mode() -> None:
    from core.auth import (
        AuthManager,
        AzureServicePrincipalTokenProvider,
        BearerTokenProvider,
        ManagedIdentityTokenProvider,
        OAuthTokenProvider,
        PATTokenProvider,
    )

    base_kwargs = {"databricks_host": "https://example.cloud.databricks.com"}

    pat_settings = Settings(**base_kwargs, auth_mode=AuthMode.PAT, databricks_token="tok")
    assert isinstance(AuthManager(pat_settings)._provider, PATTokenProvider)

    bearer_settings = Settings(**base_kwargs, auth_mode=AuthMode.BEARER, bearer_token="tok")
    assert isinstance(AuthManager(bearer_settings)._provider, BearerTokenProvider)

    oauth_settings = Settings(
        **base_kwargs,
        auth_mode=AuthMode.OAUTH,
        databricks_client_id="id",
        databricks_client_secret="secret",
    )
    assert isinstance(AuthManager(oauth_settings)._provider, OAuthTokenProvider)

    sp_settings = Settings(
        **base_kwargs,
        auth_mode=AuthMode.AZURE_SERVICE_PRINCIPAL,
        azure_tenant_id="t",
        azure_client_id="c",
        azure_client_secret="s",
    )
    assert isinstance(AuthManager(sp_settings)._provider, AzureServicePrincipalTokenProvider)

    mi_settings = Settings(**base_kwargs, auth_mode=AuthMode.MANAGED_IDENTITY)
    assert isinstance(AuthManager(mi_settings)._provider, ManagedIdentityTokenProvider)


@pytest.mark.asyncio
async def test_auth_manager_get_auth_header() -> None:
    from core.auth import AuthManager

    settings = Settings(
        databricks_host="https://example.cloud.databricks.com",
        auth_mode=AuthMode.PAT,
        databricks_token="dapi-secret",
    )
    manager = AuthManager(settings)
    headers = await manager.get_auth_header()
    assert headers == {"Authorization": "Bearer dapi-secret"}
    manager.invalidate()  # should not raise
