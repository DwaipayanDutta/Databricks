"""Optional response caching layer.

Uses Redis when REDIS_URL / cache_enabled is configured, otherwise falls
back to a simple in-process TTL cache so the connector still works without
any external dependency. This is intended for cheap, idempotent GET
endpoints (e.g. listing clusters) — never for anything that mutates state.
"""

from __future__ import annotations

import json
import time
from typing import Any

from .config import Settings
from .logging import get_logger

logger = get_logger(__name__)


class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = (time.monotonic() + ttl_seconds, value)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


class RedisCache:
    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as redis  # imported lazily; optional dependency

        self._client = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Any | None:
        raw = await self._client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        await self._client.set(key, json.dumps(value, default=str), ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)


class CacheClient:
    """Facade used by services; picks Redis or in-memory transparently."""

    def __init__(self, settings: Settings) -> None:
        self.enabled = settings.cache_enabled
        self.default_ttl = settings.cache_ttl_seconds
        self._backend: Any | None = None
        if self.enabled and settings.redis_url:
            try:
                self._backend = RedisCache(settings.redis_url)
                logger.info("cache_backend_selected", extra={"extra_fields": {"backend": "redis"}})
            except Exception:
                logger.warning("redis_unavailable_falling_back_to_memory")
                self._backend = InMemoryCache()
        elif self.enabled:
            self._backend = InMemoryCache()

    async def get(self, key: str) -> Any | None:
        if not self.enabled or self._backend is None:
            return None
        return await self._backend.get(key)

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        if not self.enabled or self._backend is None:
            return
        await self._backend.set(key, value, ttl_seconds or self.default_ttl)

    async def delete(self, key: str) -> None:
        if not self.enabled or self._backend is None:
            return
        await self._backend.delete(key)

    async def health_check(self) -> dict[str, str]:
        """Report cache health for readiness probes.

        Never raises -- a cache outage should be visible in `/ready` but
        must not itself fail the request, since caching here is a
        best-effort performance optimization, not a hard dependency.
        """
        if not self.enabled:
            return {"enabled": "false", "status": "disabled"}

        backend_name = "redis" if isinstance(self._backend, RedisCache) else "in_memory"
        probe_key = "__health_check_probe__"
        try:
            await self.set(probe_key, "ok", ttl_seconds=5)
            value = await self.get(probe_key)
            await self.delete(probe_key)
            status = "ok" if value == "ok" else "degraded: roundtrip mismatch"
        except Exception as exc:  # noqa: BLE001 - health checks must never raise
            status = f"error: {exc}"

        return {"enabled": "true", "backend": backend_name, "status": status}


_cache_client: CacheClient | None = None


def get_cache_client() -> CacheClient:
    global _cache_client
    if _cache_client is None:
        from databricks_connector.core.config import get_settings

        _cache_client = CacheClient(get_settings())
    return _cache_client
