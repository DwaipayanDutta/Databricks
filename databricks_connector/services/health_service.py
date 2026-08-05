"""Service layer backing the health/readiness endpoints.

Kept separate from MonitoringService because it answers a different
question ("can we serve traffic right now?") aimed at orchestrators
(Kubernetes readiness probes, load balancers), versus MonitoringService's
domain-level metrics/health summaries aimed at operators and agents.
"""

from __future__ import annotations

from typing import Any

from databricks_connector.core.cache import CacheClient, get_cache_client
from databricks_connector.core.circuit_breaker import get_circuit_breaker
from databricks_connector.core.client import DatabricksClient
from databricks_connector.core.config import Settings
from databricks_connector.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DatabricksConnectorError,
)

# A cheap, side-effect-free Databricks endpoint used purely to confirm
# reachability + valid auth without mutating anything or depending on any
# workspace-specific resource existing.
_REACHABILITY_PROBE_PATH = "/api/2.0/clusters/spark-versions"


class HealthService:
    def __init__(
        self,
        client: DatabricksClient,
        settings: Settings,
        cache: CacheClient | None = None,
    ) -> None:
        self._client = client
        self._settings = settings
        self._cache = cache or get_cache_client()

    async def check_readiness(self) -> dict[str, Any]:
        """Determine whether the connector is ready to serve traffic.

        Checks, independently:
          * the circuit breaker isn't tripped open
          * Databricks authentication succeeds (a 401/403 is reported
            distinctly from a network/5xx failure, since the fix for each
            is completely different -- credentials vs. connectivity)
          * Databricks connectivity/reachability
          * the optional cache backend (informational only -- a cache
            outage is reported but never flips overall readiness to
            "not_ready", since caching is a best-effort optimization here)

        Overall status is "ready" only if the circuit breaker is not open
        and the Databricks probe (auth + connectivity) succeeds.
        """
        dependencies: dict[str, str] = {}
        critical_failure = False

        breaker = get_circuit_breaker("databricks")
        dependencies["circuit_breaker"] = breaker.state.value
        if breaker.state.value == "open":
            critical_failure = True

        try:
            await self._client.get(_REACHABILITY_PROBE_PATH)
            dependencies["databricks_authentication"] = "ok"
            dependencies["databricks_connectivity"] = "reachable"
        except (AuthenticationError, AuthorizationError) as exc:
            dependencies["databricks_authentication"] = f"failed: {exc.error_code}"
            dependencies["databricks_connectivity"] = "unknown"
            critical_failure = True
        except DatabricksConnectorError as exc:
            dependencies["databricks_authentication"] = "unknown"
            dependencies["databricks_connectivity"] = f"unreachable: {exc.error_code}"
            critical_failure = True
        except Exception:  # noqa: BLE001 - any other failure also means "not ready"
            dependencies["databricks_authentication"] = "unknown"
            dependencies["databricks_connectivity"] = "unreachable"
            critical_failure = True

        cache_health = await self._cache.health_check()
        dependencies["cache"] = cache_health["status"]

        status = "not_ready" if critical_failure else "ready"
        return {"status": status, "dependencies": dependencies}
