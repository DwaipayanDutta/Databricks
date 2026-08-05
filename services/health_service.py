"""Service layer backing the health/readiness endpoints.

Kept separate from MonitoringService because it answers a different
question ("can we serve traffic right now?") aimed at orchestrators
(Kubernetes readiness probes, load balancers), versus MonitoringService's
domain-level metrics/health summaries aimed at operators and agents.
"""

from __future__ import annotations

from typing import Any

from core.circuit_breaker import get_circuit_breaker
from core.client import DatabricksClient
from core.exceptions import DatabricksConnectorError

# A cheap, side-effect-free Databricks endpoint used purely to confirm
# reachability + valid auth without mutating anything or depending on any
# workspace-specific resource existing.
_REACHABILITY_PROBE_PATH = "/api/2.0/clusters/spark-versions"


class HealthService:
    def __init__(self, client: DatabricksClient) -> None:
        self._client = client

    async def check_readiness(self) -> dict[str, Any]:
        """Determine whether the connector is ready to serve traffic.

        Ready means: the circuit breaker isn't tripped open AND Databricks
        answers a cheap reachability probe successfully.
        """
        dependencies: dict[str, str] = {}

        breaker = get_circuit_breaker("databricks")
        dependencies["circuit_breaker"] = breaker.state.value

        try:
            await self._client.get(_REACHABILITY_PROBE_PATH)
            dependencies["databricks_api"] = "reachable"
            status = "ready"
        except DatabricksConnectorError as exc:
            dependencies["databricks_api"] = f"unreachable: {exc.error_code}"
            status = "not_ready"
        except Exception:  # noqa: BLE001 - any other failure also means "not ready"
            dependencies["databricks_api"] = "unreachable"
            status = "not_ready"

        return {"status": status, "dependencies": dependencies}
