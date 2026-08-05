# Databricks Connector

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)
![Async](https://img.shields.io/badge/Async-httpx-success.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Databricks](https://img.shields.io/badge/Databricks-REST_API-orange.svg)
![Status](https://img.shields.io/badge/Status-Production_Ready-success.svg)
![Coverage](https://img.shields.io/badge/Coverage-83%25-brightgreen.svg)

---

## Enterprise Databricks Connector

A **production-grade**, **async** Databricks connector built with **FastAPI**, exposing the full Databricks REST API surface through a clean, modular, layered service architecture.

Designed to run as a standalone microservice or as an enterprise connector inside a **Multi-Agent AI Platform** — letting agents, workflow engines, and internal tools talk to a Databricks workspace over a typed, documented HTTP API instead of the raw Databricks SDK.

---

## Features

- Production-ready, fully async FastAPI service
- Strictly typed throughout (Python 3.12, `mypy`-clean)
- 139 API endpoints across 13 route groups covering the full Databricks REST API surface
- Layered architecture: Router → Service → `DatabricksClient` → Databricks REST API
- Shared, pooled, singleton `DatabricksClient` with graceful shutdown
- 5 authentication modes with automatic token refresh
- Retry with exponential backoff + jitter, honoring `Retry-After`
- Async-safe circuit breaker (closed → open → half-open)
- Structured JSON logging with correlation IDs, request IDs, and secret masking
- Consistent exception → HTTP status mapping across every endpoint
- OpenAPI / Swagger / ReDoc documentation out of the box
- Health, readiness, and liveness endpoints
- Docker + docker-compose, non-root runtime image
- GitHub Actions CI (ruff, black, mypy, pytest + coverage)
- 94 tests, 83% coverage, no real network I/O in the test suite

---

## Architecture

```
                 ┌───────────────────────────────┐
                 │           Client Apps          │
                 │  AI Agents • UI • SDK • CLI    │
                 └───────────────┬─────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────┐
                  │        FastAPI App        │
                  │      REST Endpoints       │
                  └───────────────┬────────────┘
                                  │
         ┌────────────────────────┼─────────────────────────┐
         ▼                        ▼                          ▼
    Jobs Router              SQL Router                Clusters Router  ...
         ▼                        ▼                          ▼
   Service Layer            Service Layer              Service Layer
         └──────────────────────┬───────────────────────────┘
                                 ▼
                     Shared DatabricksClient
                                 │
        Auth  •  Retry  •  Circuit Breaker  •  Correlation IDs
                                 │
                                 ▼
                Databricks REST APIs (2.0 / 2.1)
```

Routers never call Databricks directly — every request flows through a
service, which is the only layer that knows Databricks REST endpoint
shapes. See `docs/architecture.md` for the full breakdown.

---

## Project structure

```
databricks_connector/
│
├── app.py                   FastAPI app factory (create_app), middleware, lifespan
├── main.py                  uvicorn entrypoint
├── requirements.txt         Runtime dependencies
├── requirements-dev.txt     + testing / lint / type-check tooling
├── pyproject.toml           Package metadata, ruff/black/mypy/pytest config
├── setup.py                 Legacy setuptools entrypoint
├── Dockerfile                Multi-stage, non-root runtime image
├── docker-compose.yml       Connector + Redis
├── Makefile                 install / run / test / lint / format / docker targets
├── .env.example
├── .dockerignore
├── CHANGELOG.md
├── LICENSE
│
├── core/
│   ├── config.py             Typed Settings (pydantic-settings)
│   ├── auth.py                AuthManager + 5 TokenProvider strategies
│   ├── client.py              DatabricksClient (pooled, singleton, retried)
│   ├── retry.py                Tenacity retry policy + Retry-After support
│   ├── circuit_breaker.py     Async-safe circuit breaker
│   ├── exceptions.py           Exception hierarchy + status-code mapping
│   ├── logging.py              Structured JSON logging
│   ├── middleware.py           Correlation / timing / request-logging / exception middleware
│   ├── dependencies.py         Shared ContextVars + FastAPI dependencies
│   ├── cache.py                 Optional Redis / in-memory response cache
│   └── constants.py
│
├── routers/                  One thin router per API group
│   ├── health.py  jobs.py  job_runs.py  clusters.py  notebooks.py
│   ├── sql.py  unity_catalog.py  dbfs.py  dlt.py  mlflow.py
│   └── secrets.py  permissions.py  monitoring.py
│
├── services/                 Databricks REST API domain logic
│   ├── health_service.py  jobs_service.py  cluster_service.py
│   ├── notebook_service.py  sql_service.py  unity_catalog_service.py
│   ├── dbfs_service.py  dlt_service.py  mlflow_service.py
│   ├── secrets_service.py  permissions_service.py  monitoring_service.py
│   └── _common.py            Small helpers shared across services
│
├── schemas/                  Pydantic request/response models
├── tests/                    pytest suite (mocked DatabricksClient, no real network I/O)
├── docs/                     architecture.md, api.md
└── scripts/                  run.sh / run.bat / lint.sh / format.sh / test.sh
```

---

## Supported authentication

| Mode | `AUTH_MODE` value | Required config |
|---|---|---|
| Personal Access Token | `pat` | `DATABRICKS_TOKEN` |
| OAuth (client credentials) | `oauth` | `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET` |
| Azure Service Principal | `azure_service_principal` | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |
| Azure Managed Identity | `managed_identity` | optional `AZURE_MANAGED_IDENTITY_CLIENT_ID` |
| Bearer Token | `bearer` | `BEARER_TOKEN` |

All five share the same `TokenProvider` interface, cache their token in
memory, and refresh automatically ~60 seconds before expiry using
single-flight locking (concurrent callers reuse one in-flight refresh
instead of each triggering their own).

---

## API groups

All endpoints are namespaced under `/api/v1/*` except health checks.

| Group | Base path | Highlights |
|---|---|---|
| Health | `/health` `/ready` `/live` | Process health, Databricks reachability, liveness |
| Jobs | `/api/v1/jobs` | Create, update, delete, trigger, run-now, reset, repair, cancel, pause, resume, clone, export, import |
| Job Runs | `/api/v1/job-runs` | List, get, logs, output, cancel, repair, retry, wait |
| Clusters | `/api/v1/clusters` | Create, get, start, restart, resize, edit, terminate, permanent-delete, pin, unpin, events |
| Workspace / Notebooks | `/api/v1/notebooks` | Import, export, list, delete, status, folders, move, copy |
| SQL | `/api/v1/sql` | Execute statement, statement status/cancel, warehouses, query history |
| Unity Catalog | `/api/v1/unity-catalog` | Catalogs, schemas, tables, volumes, functions, permissions, grants, external locations, storage credentials |
| DBFS | `/api/v1/dbfs` | Upload, download, delete, move, mkdir, read, put, streaming create |
| Delta Live Tables | `/api/v1/dlt` | Create/update/delete pipeline, start, stop, list, get, events |
| MLflow | `/api/v1/mlflow` | Experiments, runs, log-metric/param, artifacts, model registry + versions + stage transitions |
| Secrets | `/api/v1/secrets` | Scopes, put/delete secret, list secrets, ACLs |
| Permissions | `/api/v1/permissions` | Get, update ACL, grant, revoke — generic across object types |
| Monitoring | `/api/v1/monitoring` | Cluster/job metrics, cluster/job health, connector info + config |

Full endpoint index: `docs/api.md`. Interactive docs: `/docs` and `/redoc`.

---

## Installation

```bash
git clone https://github.com/DwaipayanDutta/Databricks.git
cd Databricks

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt          # runtime only
pip install -r requirements-dev.txt      # + pytest / ruff / black / mypy
pip install -e .                         # install the package, editable

cp .env.example .env           # then fill in your Databricks credentials
```

---

## Configuration

All configuration is via environment variables (or a `.env` file); see
`.env.example` for the complete list. Key variables:

| Variable | Description |
|---|---|
| `DATABRICKS_HOST` | Workspace URL, e.g. `https://your-workspace.cloud.databricks.com` |
| `AUTH_MODE` | `pat` \| `oauth` \| `azure_service_principal` \| `managed_identity` \| `bearer` |
| `LOG_LEVEL` / `LOG_FORMAT` | Logging verbosity and format (`json` or plain text) |
| `MAX_RETRIES` / `BACKOFF_FACTOR` | Retry tuning |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` / `CIRCUIT_BREAKER_RECOVERY_TIMEOUT` | Circuit breaker tuning |
| `CACHE_ENABLED` / `REDIS_URL` | Optional response caching |
| `CONNECTOR_API_KEY` | If set, callers must send a matching `X-API-Key` header |

---

## Running

Development (auto-reload):

```bash
uvicorn main:app --reload
# or
make dev
```

Simple single-process run (uses `HOST`/`PORT` from settings):

```bash
python main.py
# or
make run
```

Using the FastAPI factory directly:

```bash
uvicorn app:create_app --factory
```

Production (matches the Dockerfile's `CMD`):

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or with gunicorn as a process manager (not bundled — install separately:
`pip install gunicorn`):

```bash
gunicorn app:app -k uvicorn.workers.UvicornWorker -w 4
```

The API is then available at `http://localhost:8000`.

---

## Swagger / OpenAPI

```
http://localhost:8000/docs        # Swagger UI
http://localhost:8000/redoc       # ReDoc
http://localhost:8000/openapi.json
```

---

## Health

```
GET /health   process-level liveness, no external calls
GET /ready    circuit breaker state + Databricks reachability probe
GET /live     liveness probe for orchestrators
```

---

## Example

Trigger a job:

```bash
curl -X POST http://localhost:8000/api/v1/jobs/trigger \
  -H "Content-Type: application/json" \
  -d '{"job_id": 12345}'
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

---

## Logging

Structured JSON logs, one object per line, with correlation IDs, request
IDs, and automatic masking of sensitive keys (tokens, secrets, passwords):

```json
{
  "timestamp": "2026-08-05T12:39:21+0000",
  "level": "INFO",
  "logger": "core.client",
  "message": "databricks_api_call",
  "request_id": "e2b1...",
  "correlation_id": "e2b1...",
  "method": "POST",
  "path": "/api/2.1/jobs/run-now",
  "status": 200,
  "elapsed_ms": 142.3
}
```

---

## Security

- OAuth / PAT / Azure Service Principal / Managed Identity / Bearer auth
- Automatic, single-flight token refresh
- Secret masking in all structured logs
- Optional `X-API-Key` gate on the connector's own endpoints
- Consistent exception → HTTP status mapping (no leaking internal detail)
- Circuit breaker to fail fast rather than hammer a struggling dependency
- Retry policy that honors server-supplied `Retry-After`

---

## Testing

```bash
make test
# or
scripts/test.sh
# or directly
pytest -v --cov=core --cov=services --cov=routers --cov-report=term-missing
```

The suite mocks the Databricks HTTP layer (a fake `DatabricksClient` for
router tests, `respx` for lower-level `httpx`/auth tests) so it runs fully
offline. Current state: **94 tests passing, 83% coverage** across `core/`,
`services/`, and `routers/`.

---

## Docker

```bash
docker build -t databricks-connector:latest .
docker run --rm -p 8000:8000 --env-file .env databricks-connector:latest
```

With Redis for caching:

```bash
docker compose up --build
```

Multi-stage build, slim runtime, non-root user, built-in `HEALTHCHECK`
against `/live`, and a `.dockerignore` that keeps `.env`, `.git`, and test
artifacts out of the image.

---

## CI/CD

`.github/workflows/python.yml` runs on every push/PR to `main`:

- `ruff check .`
- `black --check .`
- `mypy core routers services schemas tests app.py main.py`
- `pytest` with coverage reporting

---

## Design principles

- Clean, layered architecture (Router → Service → `DatabricksClient`)
- SOLID principles, dependency injection via FastAPI's `Depends`
- Async-first throughout
- Thin routers — no business logic, no duplicated code
- Single shared, pooled `DatabricksClient` with graceful shutdown
- Enterprise-grade structured logging
- High testability: every service accepts an injectable client

---

## Roadmap

- Kubernetes Helm chart
- Prometheus metrics export
- OpenTelemetry trace export (hooks already present in config)
- Azure Key Vault / AWS Secrets Manager / GCP Secret Manager integration
- Generated client SDKs
- Multi-workspace support

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push your branch
5. Open a Pull Request

---

## License

MIT — see `LICENSE`.

See `CHANGELOG.md` for a full history of changes, and `docs/architecture.md`
for a deep dive into the request lifecycle, auth internals, and resiliency
design.
