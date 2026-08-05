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
