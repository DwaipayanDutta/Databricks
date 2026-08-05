# Databricks Connector

An enterprise-grade, async FastAPI connector that exposes the full
Databricks REST API surface — Jobs, Job Runs, Clusters, Workspace/Notebooks,
SQL, Unity Catalog, DBFS, Delta Live Tables, MLflow, Secrets, Permissions,
and Monitoring — as a clean, typed HTTP API. Designed to be dropped in as an
enterprise connector inside a Multi-Agent AI Platform, but usable standalone.

## Features

* **143 endpoints** across 12 API groups, every one documented in OpenAPI/Swagger.
* **Layered architecture**: Router → Service → `DatabricksClient` → Databricks REST API. Routers never call Databricks directly.
* **5 authentication modes**: Personal Access Token, OAuth (client-credentials), Azure Service Principal, Azure Managed Identity, and static Bearer — all with automatic token refresh.
* **Resiliency**: automatic retries with exponential backoff + jitter (Tenacity), and a circuit breaker to fail fast during Databricks outages.
* **Structured JSON logging** with correlation IDs, request IDs, latency, and automatic secret masking.
* **Optional Redis (or in-memory) caching** for cheap idempotent reads.
* **Consistent error model** across every endpoint (`error` / `message` / `details`).
* **Health, readiness, and liveness** endpoints for orchestrators.
* **Docker & docker-compose** ready; **GitHub Actions CI** (pytest + ruff + black + mypy).
* **pytest suite** with mocked Databricks calls (no real network I/O), currently at **80% coverage** across `core/`, `services/`, and `routers/`.

## Installation

Requires **Python 3.12+**.

```bash
git clone <this-repo>
cd databricks_connector
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # runtime only
pip install -r requirements-dev.txt      # + testing/lint/type-check tooling
pip install -e .                         # install the package itself, editable
cp .env.example .env   # then fill in your Databricks credentials
```

## Configuration

All configuration is via environment variables (or a `.env` file); see
`.env.example` for the full list. Key variables:

| Variable | Description |
|---|---|
| `DATABRICKS_HOST` | Your workspace URL, e.g. `https://your-workspace.cloud.databricks.com` |
| `AUTH_MODE` | One of `pat`, `oauth`, `azure_service_principal`, `managed_identity`, `bearer` |
| `LOG_LEVEL` / `LOG_FORMAT` | Logging verbosity and format (`json` or plain text) |
| `MAX_RETRIES` / `BACKOFF_FACTOR` | Retry tuning |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` / `CIRCUIT_BREAKER_RECOVERY_TIMEOUT` | Circuit breaker tuning |
| `CACHE_ENABLED` / `REDIS_URL` | Optional response caching |
| `CONNECTOR_API_KEY` | If set, callers must send a matching `X-API-Key` header |

### Authentication

Set `AUTH_MODE` and the matching credentials:

* **`pat`** — `DATABRICKS_TOKEN`
* **`oauth`** — `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET`, optional `DATABRICKS_OAUTH_TOKEN_URL` (defaults to `{DATABRICKS_HOST}/oidc/v1/token`)
* **`azure_service_principal`** — `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`
* **`managed_identity`** — optional `AZURE_MANAGED_IDENTITY_CLIENT_ID` (omit for the system-assigned identity)
* **`bearer`** — `BEARER_TOKEN`

Tokens are cached in memory and automatically refreshed ~60 seconds before
expiry.

## Running locally

```bash
make run          # python main.py
# or
make dev          # uvicorn main:app --reload
# or
scripts/run.sh
```

The API is then available at `http://localhost:8000`, with interactive docs
at `http://localhost:8000/docs`.

## Examples

Create and trigger a job:

```bash
curl -X POST http://localhost:8000/api/v1/jobs/create \
  -H "Content-Type: application/json" \
  -d '{
        "name": "nightly-etl",
        "tasks": [{"task_key": "main", "notebook_task": {"notebook_path": "/Repos/etl/main"}}]
      }'

curl -X POST http://localhost:8000/api/v1/jobs/trigger \
  -H "Content-Type: application/json" \
  -d '{"job_id": 123}'
```

Execute a SQL statement:

```bash
curl -X POST http://localhost:8000/api/v1/sql/statements/execute \
  -H "Content-Type: application/json" \
  -d '{"statement": "SELECT 1", "warehouse_id": "0123456789abcdef"}'
```

List Unity Catalog tables:

```bash
curl "http://localhost:8000/api/v1/unity-catalog/tables?catalog_name=main&schema_name=default"
```

## Swagger / OpenAPI

* Swagger UI: `/docs`
* ReDoc: `/redoc`
* Raw schema: `/openapi.json`

See `docs/api.md` for a full endpoint index and `docs/architecture.md` for
the layered architecture, auth internals, and resiliency design.

## Testing

```bash
make test
# or
scripts/test.sh
# or directly
pytest -v --cov=core --cov=services --cov=routers --cov-report=term-missing
```

The suite mocks the Databricks HTTP layer (via a fake `DatabricksClient` and
`respx` for lower-level `httpx` tests), so it runs fully offline. Current
coverage is **80%** across `core/`, `services/`, and `routers/`.

## Deployment

### Docker

```bash
docker build -t databricks-connector:latest .
docker run --rm -p 8000:8000 --env-file .env databricks-connector:latest
```

### docker-compose (connector + Redis)

```bash
docker compose up --build
```

The image is a multi-stage build (slim runtime, non-root user, built-in
`HEALTHCHECK` against `/live`).

### Kubernetes

Point liveness/readiness probes at `/live` and `/ready` respectively; the
app's `lifespan` hook drains the Databricks HTTP connection pool on
`SIGTERM` for a clean shutdown.

## Architecture

Routers never call Databricks directly:

```
Router → Service → DatabricksClient → Databricks REST API
```

See `docs/architecture.md` for the full breakdown of `core/` (auth, retry,
circuit breaker, logging, middleware, caching) and the request lifecycle.

## Code quality

```bash
make lint        # ruff check .
make format      # black . && ruff check --fix .
make typecheck   # mypy .
```

CI (`.github/workflows/python.yml`) runs ruff, black --check, mypy, and the
full pytest suite on every push/PR to `main`.

## License

MIT — see `LICENSE`.
