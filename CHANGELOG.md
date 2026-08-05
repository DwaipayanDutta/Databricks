# Changelog

All notable changes to `databricks-connector` are documented here. This
entry covers the **production-readiness audit** pass — no public REST API
endpoints, paths, methods, or request/response shapes changed as a result
of this audit; every fix is internal (imports, resiliency, concurrency
safety, exception mapping, code de-duplication, packaging).

## [1.0.1] - Production-readiness audit

### Fixed (real bugs)

- **Circuit breaker HALF_OPEN state let unlimited concurrent calls through.**
  Previously, once the recovery timeout elapsed, *every* concurrent caller
  that observed `state == HALF_OPEN` was allowed through, not just a single
  trial request — defeating the purpose of the half-open state (protecting
  a recovering dependency from a thundering herd). Added a
  `_half_open_trial_in_flight` flag under the existing lock so exactly one
  trial call is permitted; any other concurrent caller fails fast with
  `CircuitBreakerOpenError`. A failure during the trial now immediately
  re-opens the circuit (fresh recovery window) instead of requiring the
  failure threshold to be hit again. (`core/circuit_breaker.py`)
- **`ValidationAPIError` (HTTP 400) was defined but never registered in
  `STATUS_CODE_EXCEPTION_MAP`.** A 400 response from Databricks fell through
  to the generic `DatabricksConnectorError`, returning a confusing body
  (`"error": "internal_error"`) alongside a `400` status code. Added `400`
  and `501` to the map so every documented Databricks response status
  produces a matching, correctly-labeled connector exception.
  (`core/exceptions.py`)
- **`Retry-After` header was not honored at all**, despite being a stated
  requirement for the retry layer. Added RFC 9110-compliant parsing
  (integer seconds or HTTP-date, clamped to a 120s ceiling so a
  misbehaving upstream can't stall a request indefinitely) wired into a
  custom tenacity `wait` callable that prefers the server-supplied value
  and falls back to exponential backoff + jitter when the header is
  absent. (`core/retry.py`)
- **Unguarded singleton creation (race conditions).** `get_databricks_client()`,
  `get_auth_manager()`, and `DatabricksClient._get_http()`'s connection-pool
  creation all used an unguarded check-then-set pattern. Added
  double-checked locking: `threading.Lock` for the two module-level
  singletons (safe even if called from multiple threads, e.g. a sync
  dependency running in FastAPI's threadpool) and `asyncio.Lock` for the
  httpx connection pool. (`core/client.py`, `core/auth.py`)
- **Token refresh had no single-flight protection.** When many concurrent
  requests observed an expired token at once, each would independently
  call `_fetch_token()`, hammering the identity provider. `TokenProvider.get_token()`
  now uses double-checked locking around an `asyncio.Lock` so only one
  refresh happens; everyone else waits for and reuses that result.
  (`core/auth.py`)

### Fixed (correctness / hygiene)

- Removed a dead no-op branch in `JobsService.retry_run`
  (`raise ... if False else None`) — a leftover from an earlier draft.
  Replaced with a real `ValueError` when a run's `job_id` can't be
  determined. (`services/jobs_service.py`)
- Removed a redundant `time` import inside `MlflowService.log_metric`
  (`import time as _time` inside the method body) — hoisted to a normal
  module-level import. (`services/mlflow_service.py`)
- Removed two lazy imports (`core.dependencies.verify_connector_api_key`,
  `core.auth.get_auth_manager`) that had no circular-import justification
  (verified: `core.config` and `core.exceptions` do not import
  `core.dependencies`, so there was no cycle to avoid). Hoisted both to
  normal top-level imports.
- Fixed two real `mypy` errors introduced in the previous iteration:
  `before_sleep_log(logger, "WARNING")` passed a `str` where `tenacity`
  expects an `int` logging level (`logging.WARNING`); and a
  `raise X if False else None` construct that isn't a valid exception
  raise. Both are covered by the dead-code fix above and the retry.py
  fix.
- `docker-compose.yml`: removed the obsolete top-level `version: "3.9"` key
  (Compose v2 warns that it's ignored).
- `Dockerfile`: removed a redundant `RUN chown -R connector:connector /app`
  that duplicated work already done by the preceding `COPY --chown=...`
  layer (wasted build time / an extra image layer for no effect); added
  `--chown=connector:connector` to the builder-stage `COPY --from=builder`
  so the installed Python packages aren't left root-owned in a
  non-root-user image.
- Added a missing `.dockerignore` — without it, `.env` (real credentials),
  `.git`, test/lint caches, and `tests/`/`docs/` were all being copied into
  the build context and potentially the image.

### Changed (architecture / de-duplication)

- **Moved business logic out of `routers/health.py` into a new
  `services/health_service.py`.** The `/ready` endpoint's reachability
  probe, exception-to-status mapping, and dependency-status assembly were
  previously inline in the router; the router now only calls
  `HealthService.check_readiness()` and serializes the result — consistent
  with the Router → Service → DatabricksClient layering used everywhere
  else.
- **De-duplicated repeated logic across services:**
  - `MlflowService`: the `{key: value} -> [{"key": k, "value": v}, ...]`
    tag conversion was duplicated in three methods (`create_experiment`,
    `create_run`, `create_registered_model`). Extracted to
    `services/_common.py::tags_dict_to_kv_list`.
  - `NotebookService.move_object` / `copy_object` duplicated the
    export-then-extract-content-and-language logic. Extracted to a shared
    `_export_content_and_language` helper.
  - `JobsService.pause_job` / `resume_job` duplicated the
    get-job-then-patch-schedule logic. Extracted to a shared
    `_set_schedule_pause_status` helper.
- New `services/_common.py` module for small, dependency-free helpers
  shared across service modules (currently `tags_dict_to_kv_list`,
  `prune_none`).
- Converted intra-`core/` imports (i.e. one `core` module importing
  another `core` module) from absolute (`from core.x import y`) to
  package-relative (`from .x import y`) form, which is the idiomatic
  convention for imports within the same package and reduces coupling to
  the top-level package name. Cross-package imports (`services` → `core`,
  `routers` → `core`/`services`/`schemas`) remain absolute, which is
  correct for this flat multi-package layout.

### Changed (packaging / CI)

- **Split `requirements.txt` into runtime-only dependencies and a new
  `requirements-dev.txt`** (testing + lint/format/type-check tooling,
  `-r requirements.txt` plus `pytest`, `pytest-asyncio`, `pytest-cov`,
  `respx`, `pyyaml`, `ruff`, `black`, `mypy`). The Docker image now installs
  only runtime dependencies, meaningfully shrinking the production image
  and its attack surface. `pyproject.toml`'s `[project.optional-dependencies].dev`
  remains the canonical list; `requirements-dev.txt` mirrors it for
  pip-only workflows.
- Updated `Makefile` (`install` now installs only runtime deps; new
  `install-dev` target installs dev tooling + the package in editable
  mode) and `.github/workflows/python.yml` (now installs
  `requirements-dev.txt` and does `pip install -e .` before running
  ruff/black/mypy/pytest, matching real local-dev usage).

### Tests

- Added `tests/test_core.py` coverage for all of the above:
  - `test_circuit_breaker_half_open_allows_single_trial_only` — regression
    test proving exactly one of three concurrent callers gets the HALF_OPEN
    trial slot and the other two fail fast.
  - `test_circuit_breaker_reopens_on_half_open_failure` — a failed trial
    re-opens the circuit.
  - `test_retry_after_parses_seconds`, `test_retry_after_clamps_large_values`,
    `test_retry_after_handles_missing_and_invalid`,
    `test_retry_after_parses_http_date` — `Retry-After` parsing.
  - `test_get_databricks_client_singleton_thread_safe`,
    `test_close_databricks_client_is_idempotent` — singleton concurrency
    safety and idempotent shutdown.
  - `test_token_provider_refresh_is_single_flight` — proves 8 concurrent
    `get_token()` calls on an expired token trigger exactly one
    `_fetch_token()`.
  - `test_health_service_ready_when_databricks_reachable`,
    `test_health_service_not_ready_on_connector_error`,
    `test_health_service_not_ready_on_unexpected_error` — the extracted
    `HealthService`.
  - `test_exception_status_code_map_covers_documented_codes` — every
    mapped status code (400/401/403/404/409/429/503/504) produces the
    correct exception subclass and matching `status_code`.
  - `test_oauth_token_provider_fetches_and_caches`,
    `test_oauth_token_provider_requires_credentials`,
    `test_azure_service_principal_requires_credentials`,
    `test_managed_identity_token_provider_fetches_token`,
    `test_auth_manager_builds_correct_provider_per_mode`,
    `test_auth_manager_get_auth_header` — previously-uncovered auth
    strategies (OAuth, Azure Service Principal, Managed Identity) and the
    `AuthManager` provider-selection logic.
- Total: **94 tests passing** (up from 75), **83% coverage** across
  `core/`, `services/`, `routers/` (up from 80%).

### Verification performed

- `pytest` — 94/94 passing, 83% coverage, in both the original venv and a
  completely fresh venv installed from the split requirements files.
- `ruff check .` — clean.
- `black --check .` — clean.
- `mypy core routers services schemas app.py main.py` — clean, 54 source
  files, 0 errors.
- `pip install -e .` — succeeds in a fresh venv.
- `uvicorn app:create_app --factory` — boots, logs structured startup/shutdown
  JSON, serves traffic, and shuts down gracefully (drains the
  `DatabricksClient` connection pool via the `lifespan` hook) on `SIGTERM`/Ctrl-C.
- No circular imports: verified by importing every module individually and
  by importing all of `core/` in reverse dependency order.
- `core.retry` exports verified: `RetryableHTTPError`, `build_retry_decorator`,
  `is_retryable_status` all present and correctly typed.
- `pyproject.toml` parses via `tomllib`; `docker-compose.yml` parses via
  `pyyaml` and lists the expected two services (`databricks-connector`,
  `redis`).
- Docker build itself could **not** be executed in this environment (no
  `docker` binary available in the sandbox) — see "Remaining technical
  debt" below.

### No public API changes

Every fix in this pass is internal. No router path, HTTP method, request
schema, response schema, or status-code contract changed.

---

## [1.0.0] - Initial release

Initial generation of the full connector: Jobs, Job Runs, Clusters,
Workspace/Notebooks, SQL, Unity Catalog, DBFS, Delta Live Tables, MLflow,
Secrets, Permissions, Monitoring, and Health APIs behind a
Router → Service → DatabricksClient layered architecture, with PAT/OAuth/
Azure Service Principal/Managed Identity/Bearer authentication, retry +
circuit breaker resiliency, structured JSON logging, Docker/compose,
GitHub Actions CI, and a pytest suite.
