<div align="center">

# Databricks Connector

### The production-ready API layer between your platform and Databricks.

Build reliable automations, agent workflows, internal tools, and data products on top of a typed, async-first FastAPI service — without coupling your application directly to the Databricks SDK.

<br />

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Async](https://img.shields.io/badge/Async--first-httpx-7C3AED)](https://www.python-httpx.org/)
[![Databricks](https://img.shields.io/badge/Databricks-REST%20API-FF3621?logo=databricks&logoColor=white)](https://docs.databricks.com/api/workspace/introduction)
[![License](https://img.shields.io/badge/License-MIT-22C55E)](LICENSE)

<br />

**139 endpoints** &nbsp;·&nbsp; **14 route groups** &nbsp;·&nbsp; **5 auth modes** &nbsp;·&nbsp; **115 tests** &nbsp;·&nbsp; **87% coverage**

<br />

[Quick start](#-quick-start) &nbsp;·&nbsp; [Capabilities](#-capabilities) &nbsp;·&nbsp; [API surface](#-api-surface) &nbsp;·&nbsp; [Architecture](#-architecture)

</div>

---

## Why this connector?

Databricks is powerful. Integrating it into every service, workflow engine, or AI agent from scratch is not.

**Databricks Connector** gives your systems one consistent, documented HTTP boundary for workspace operations. It handles the production concerns around the Databricks REST APIs — authentication, retries, pooling, circuit breaking, logging, metrics, validation, and error mapping — so your product teams can focus on what they are building.

```text
Your application  →  Databricks Connector  →  Databricks REST APIs
                   auth · retry · resilience
                   observability · validation
```

Use it as:

- A standalone internal microservice
- The data and job execution layer for AI agents
- A shared integration service for workflow platforms
- A typed REST boundary for frontend applications and SDKs

---

## ✨ Capabilities

| Capability | What you get |
| --- | --- |
| **Broad API coverage** | Jobs, runs, clusters, SQL, notebooks, Unity Catalog, DBFS, DLT, MLflow, secrets, permissions, and monitoring |
| **Async by default** | Fully asynchronous FastAPI and `httpx` integration for high-concurrency workloads |
| **Resilient requests** | Connection pooling, exponential backoff with jitter, `Retry-After` support, and an async-safe circuit breaker |
| **Flexible authentication** | PAT, OAuth, Azure Service Principal, Azure Managed Identity, and Bearer Token modes |
| **Observable in production** | Structured JSON logs, request and correlation IDs, secret masking, health probes, and Prometheus metrics |
| **Safe service boundaries** | Thin routers, domain services, typed Pydantic schemas, consistent error-to-status mapping, and fail-fast configuration |
| **Ready to ship** | Docker, docker-compose, non-root runtime image, CI checks, OpenAPI docs, and an offline test suite |

---

## 🚀 Quick start

### 1. Clone and install

```bash
git clone https://github.com/DwaipayanDutta/Databricks.git
cd Databricks

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### 2. Configure your workspace

```bash
cp .env.example .env
```

At minimum, configure your workspace URL and credentials:

```dotenv
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
AUTH_MODE=pat
DATABRICKS_TOKEN=your-token
```

Configuration is validated at startup. The service refuses to boot when the selected authentication mode is missing required values or the workspace URL is invalid.

### 3. Start the service

```bash
make dev
```

Or run it directly:

```bash
uvicorn databricks_connector.main:app --reload
```

The service is available at **[http://localhost:8000](http://localhost:8000)**.

| URL | Purpose |
| --- | --- |
| `/docs` | Interactive Swagger UI |
| `/redoc` | ReDoc API reference |
| `/openapi.json` | OpenAPI schema |
| `/health` | Process health |
| `/ready` | Dependency and readiness checks |
| `/live` | Liveness probe |
| `/metrics` | Prometheus metrics |

---

## 🧩 API surface

All operational endpoints are namespaced under `/api/v1`.

| Domain | Base path | Includes |
| --- | --- | --- |
| **Jobs** | `/api/v1/jobs` | Create, update, delete, trigger, run-now, reset, repair, cancel, pause, resume, clone, export, and import |
| **Job runs** | `/api/v1/job-runs` | List, inspect, cancel, repair, retry, wait, logs, and output |
| **Clusters** | `/api/v1/clusters` | Create, start, restart, resize, edit, terminate, delete, pin, unpin, and events |
| **Workspace & notebooks** | `/api/v1/notebooks` | Import, export, list, delete, status, folders, move, and copy |
| **SQL** | `/api/v1/sql` | Execute, inspect, cancel statements, manage warehouses, and query history |
| **Unity Catalog** | `/api/v1/unity-catalog` | Catalogs, schemas, tables, volumes, functions, grants, permissions, and storage |
| **DBFS** | `/api/v1/dbfs` | Upload, download, read, write, delete, move, mkdir, and streaming create |
| **Delta Live Tables** | `/api/v1/dlt` | Create, update, delete, start, stop, list, inspect, and events |
| **MLflow** | `/api/v1/mlflow` | Experiments, runs, metrics, parameters, artifacts, models, and stage transitions |
| **Secrets** | `/api/v1/secrets` | Scopes, secrets, and access control lists |
| **Permissions** | `/api/v1/permissions` | Get, update, grant, and revoke permissions across object types |
| **Monitoring** | `/api/v1/monitoring` | Cluster and job metrics, health, connector info, and configuration |

See the complete endpoint index in [`docs/api.md`](docs/api.md).

---

## 💻 Example requests

### Trigger a job

```bash
curl -X POST http://localhost:8000/api/v1/jobs/trigger \
  -H "Content-Type: application/json" \
  -d '{"job_id": 12345}'
```

### Execute SQL

```bash
curl -X POST http://localhost:8000/api/v1/sql/statements/execute \
  -H "Content-Type: application/json" \
  -d '{
    "statement": "SELECT 1",
    "warehouse_id": "0123456789abcdef"
  }'
```

### List Unity Catalog tables

```bash
curl "http://localhost:8000/api/v1/unity-catalog/tables?catalog_name=main&schema_name=default"
```

---

## 🔐 Authentication

Choose the mode that matches your deployment environment:

| Mode | `AUTH_MODE` | Required configuration |
| --- | --- | --- |
| Personal Access Token | `pat` | `DATABRICKS_TOKEN` |
| OAuth client credentials | `oauth` | `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET` |
| Azure Service Principal | `azure_service_principal` | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |
| Azure Managed Identity | `managed_identity` | Optional `AZURE_MANAGED_IDENTITY_CLIENT_ID` |
| Bearer Token | `bearer` | `BEARER_TOKEN` |

All providers share the same `TokenProvider` contract. Tokens are cached in memory and refreshed automatically before expiry using single-flight locking, so concurrent requests do not trigger duplicate refreshes.

### Additional protection

Set `CONNECTOR_API_KEY` to protect the connector's own endpoints. Clients must then send:

```http
X-API-Key: your-connector-key
```

The key is enforced on every `/api/v1/*` route. `/health`, `/live`, `/ready`,
and `/metrics` intentionally stay open even when it's set, since Kubernetes
probes and Prometheus scrapers call those without app-level credentials.

Never commit credentials or `.env` files. Use your platform's secret manager in deployed environments.

---

## 🏗️ Architecture

```text
┌──────────────────────────────────────────────────────┐
│              Client applications and agents          │
│                 UI · SDK · CLI · workflows           │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│                    FastAPI application                │
│        validation · middleware · OpenAPI · routes     │
└──────────────────────────┬───────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
       Jobs router     SQL router    Clusters router   ...
            │              │              │
            └──────────────┼──────────────┘
                           ▼
┌──────────────────────────────────────────────────────┐
│                    Domain services                   │
│       Databricks API shapes and business logic       │
└──────────────────────────┬───────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────┐
│                  Shared DatabricksClient              │
│    auth · pooling · retries · circuit breaker        │
│    correlation IDs · logging · metrics · caching     │
└──────────────────────────┬───────────────────────────┘
                           ▼
                 Databricks REST APIs 2.0 / 2.1
```

Routers never call Databricks directly. Every request moves through a domain service, keeping transport concerns separate from API-specific logic and making every layer straightforward to test.

Read the deeper request lifecycle in [`docs/architecture.md`](docs/architecture.md).

---

## 🛡️ Built for production

- Shared, pooled client with graceful shutdown
- Exponential backoff with jitter and server-aware `Retry-After`
- Async-safe circuit breaker: closed → open → half-open
- Structured, one-object-per-line JSON logs
- Request IDs and correlation IDs throughout the request lifecycle
- Automatic masking of tokens, secrets, and passwords
- Consistent exception-to-HTTP status mapping without leaking internal details
- Optional Redis or in-memory response caching
- Health, readiness, liveness, and Prometheus endpoints
- Docker image with a slim runtime, non-root user, and built-in health check

Example log event:

```json
{
  "timestamp": "2026-08-05T12:39:21+0000",
  "level": "INFO",
  "logger": "databricks_connector.core.client",
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

## 🐳 Docker

Build and run the connector:

```bash
docker build -t databricks-connector:latest .
docker run --rm \
  -p 8000:8000 \
  --env-file .env \
  databricks-connector:latest
```

Start the connector with Redis-backed caching:

```bash
docker compose up --build
```

---

## 🧪 Testing and quality

Run the full test suite:

```bash
make test
```

Or run it directly:

```bash
pytest -v --cov=databricks_connector --cov-report=term-missing
```

The test suite runs fully offline:

- Databricks HTTP calls are mocked
- Router tests use a fake `DatabricksClient`
- Lower-level `httpx` and authentication tests use `respx`
- No real workspace network calls are required

Current project checks include:

- `ruff`
- `black`
- `mypy --strict`
- `pytest` with coverage
- `bandit`
- `pip-audit`

All of the above run automatically in CI on every push/PR to `main` via
[`.github/workflows/python.yml`](.github/workflows/python.yml), followed by
a Docker build job that verifies the image still builds cleanly.

---

## 📁 Project layout

```text
databricks_connector/
├── app.py                 FastAPI app factory, middleware, and lifespan
├── main.py                Uvicorn entrypoint
├── core/                  Config, auth, client, retries, logging, metrics
├── routers/               Thin routers organized by Databricks API domain
├── services/              Domain logic for Databricks REST APIs
└── schemas/               Typed Pydantic request and response models

tests/                     Offline pytest suite
docs/                      API reference and architecture guide
scripts/                   Run, test, lint, and formatting helpers
Dockerfile                Multi-stage non-root runtime image
docker-compose.yml         Connector plus Redis
```

---

## ⚙️ Common commands

| Command | Purpose |
| --- | --- |
| `make dev` | Start the development server with auto-reload |
| `make run` | Start a single production-style process |
| `make test` | Run tests and coverage |
| `make lint` | Run lint checks |
| `make format` | Format the codebase |
| `make security` | Run security checks (bandit + pip-audit) |
| `make docker-build` | Build the Docker image |
| `make docker-run` | Run via `docker compose up --build` |

---

## 🗺️ Roadmap

- Kubernetes Helm chart
- Prometheus metrics export improvements
- OpenTelemetry trace export
- Azure Key Vault, AWS Secrets Manager, and GCP Secret Manager integrations
- Generated client SDKs
- Multi-workspace support

Have an idea? Open an issue or start a discussion — contributions are welcome.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your change and add tests
4. Run the formatting, lint, type, and test checks
5. Push your branch
6. Open a pull request with context and a verification plan

Please keep routers thin, preserve the service boundary, and avoid introducing real network calls into the test suite.

---

## 📄 License

MIT — see [`LICENSE`](LICENSE).

For the full history, see [`CHANGELOG.md`](CHANGELOG.md).

<div align="center">

<br />

**Make Databricks feel like a dependable platform primitive.**

<br />
<br />

[⬆ Back to top](#databricks-connector)

</div>