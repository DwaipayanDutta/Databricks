# Architecture

## Overview

`databricks-connector` is a FastAPI service that exposes the Databricks REST
API surface as a clean, typed, enterprise-ready HTTP API for consumption by
agents inside a Multi-Agent AI Platform (or any other HTTP client).

It never lets a router talk to Databricks directly. Every request flows
through a strict layered pipeline:

```
Client
  │
  ▼
FastAPI Router            (routers/*.py)
  │  validates request via Pydantic schema
  ▼
Service Layer              (services/*.py)
  │  encodes Databricks REST semantics (endpoints, payload shape)
  ▼
DatabricksClient            (core/client.py)
  │  auth, retries, circuit breaking, correlation IDs, response parsing
  ▼
Databricks REST API
```

This separation means:

* **Routers** are thin. They only do request/response translation
  (Pydantic model in, dict out) and pick which service method to call.
* **Services** hold business/domain logic and know the Databricks REST
  endpoint shapes (paths, verbs, payloads). They depend only on
  `DatabricksClient`, never on `httpx` directly.
* **`DatabricksClient`** is the single choke point for everything that
  talks to Databricks over the network: authentication headers, retries,
  circuit breaking, timeouts, correlation IDs, and error translation.

## Core building blocks (`core/`)

| Module | Responsibility |
|---|---|
| `config.py` | Typed `Settings` (pydantic-settings) loaded from env vars / `.env`. |
| `auth.py` | `AuthManager` + pluggable `TokenProvider`s for PAT, OAuth, Azure Service Principal, Managed Identity, and static Bearer tokens. All providers cache and auto-refresh tokens. |
| `client.py` | `DatabricksClient`: async HTTP verbs (GET/POST/PUT/PATCH/DELETE) wired through auth, retry, and the circuit breaker. |
| `retry.py` | Tenacity-based retry policy: exponential backoff + jitter for 429/500/502/503/504 and network-level errors. |
| `circuit_breaker.py` | A small async circuit breaker (CLOSED → OPEN → HALF_OPEN) protecting Databricks from thundering-herd retries during an outage. |
| `exceptions.py` | `DatabricksConnectorError` hierarchy, mapped 1:1 to HTTP status codes returned by Databricks. |
| `logging.py` | Structured JSON logging with correlation/request IDs and secret masking. |
| `middleware.py` | Correlation ID propagation, timing, request logging, and a top-level exception handler that turns any connector exception into a consistent JSON error body. |
| `dependencies.py` | Shared `ContextVar`s (request id / correlation id) and small FastAPI dependencies. |
| `cache.py` | Optional Redis-or-in-memory TTL cache for cheap idempotent reads. |
| `constants.py` | Shared constants (timeouts, retryable status codes, header names, masked keys). |

## Authentication

`AuthMode` (in `core/config.py`) selects one of five `TokenProvider`
implementations in `core/auth.py`:

* **PAT** — static personal access token.
* **OAuth** — client-credentials flow against Databricks' OIDC token
  endpoint.
* **Azure Service Principal** — AAD client-credentials flow scoped to the
  Databricks AAD resource ID.
* **Managed Identity** — Azure Instance Metadata Service (IMDS) flow, for
  workloads running on Azure compute.
* **Bearer** — a static token minted and rotated by something else (e.g. a
  platform-level secret manager).

Every provider exposes the same `async get_token() -> str` contract and
caches its token in memory, refreshing ~60 seconds before expiry.

## Resiliency

* **Retries** (`core/retry.py`): exponential backoff with jitter, applied
  only to retryable statuses (429/500/502/503/504) and transient network
  errors. Non-retryable errors (400/401/403/404/409) fail fast.
* **Circuit breaker** (`core/circuit_breaker.py`): after N consecutive
  failures the breaker opens and short-circuits calls for a recovery
  window, then allows a single trial call (HALF_OPEN) before fully
  closing again.
* **Timeouts**: connect and total-request timeouts are both configurable
  and enforced by `httpx.Timeout`.

## Observability

* **Structured JSON logs** with `request_id`/`correlation_id` on every
  line, and automatic masking of sensitive keys (tokens, secrets,
  passwords).
* **Correlation/Request IDs**: minted or propagated by
  `CorrelationMiddleware`, threaded through `ContextVar`s so the
  `DatabricksClient` can forward them to Databricks as
  `X-Request-ID` / `X-Correlation-ID` headers, and returned to the caller
  on the response.
* **Timing**: every response carries an `X-Response-Time-ms` header;
  `LogTimer` is available for timing arbitrary code blocks.
* **OpenTelemetry hooks**: `OTEL_ENABLED` + `OTEL_EXPORTER_ENDPOINT` are
  reserved for wiring `opentelemetry-instrumentation-fastapi` in
  deployments that need distributed tracing.

## Health, readiness, and graceful shutdown

* `GET /health` — process-level liveness, no external calls.
* `GET /ready` — checks the circuit breaker state and makes a cheap call
  to Databricks (`/api/2.0/clusters/spark-versions`) to confirm
  reachability.
* `GET /live` — trivial liveness probe for orchestrators.
* `app.py`'s `lifespan` context manager warms the shared
  `DatabricksClient`/connection pool on startup and closes it cleanly on
  shutdown (`await close_databricks_client()`), so in-flight connections
  are drained rather than dropped.

## Middleware stack (outer → inner)

```
CORSMiddleware
  └─ GZipMiddleware
      └─ ExceptionMiddleware      (catches everything, returns JSON errors)
          └─ RequestLoggingMiddleware
              └─ TimingMiddleware
                  └─ CorrelationMiddleware
                      └─ route handler
```

## Directory layout

```
databricks_connector/
├── app.py / main.py        FastAPI app factory + uvicorn entrypoint
├── core/                   Cross-cutting infrastructure (see table above)
├── routers/                Thin HTTP-layer endpoints (one file per API group)
├── services/                Databricks REST API domain logic
├── schemas/                Pydantic request/response models
├── tests/                  pytest suite (mocked DatabricksClient, no real network I/O)
├── docs/                   This file + docs/api.md
└── scripts/                Convenience scripts (run/lint/format/test)
```
