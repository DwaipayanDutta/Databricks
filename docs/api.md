# API Reference

Interactive documentation is always available at runtime:

* Swagger UI: `GET /docs`
* ReDoc: `GET /redoc`
* Raw OpenAPI schema: `GET /openapi.json`

This document is a quick-reference index of every endpoint grouped by API
area. All request/response bodies are documented in Swagger with full
Pydantic-generated JSON Schemas and examples.

## Health (`/health`, `/ready`, `/live`)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Basic process health. |
| GET | `/ready` | Readiness: circuit breaker state + Databricks reachability. |
| GET | `/live` | Liveness probe. |

## Jobs (`/api/v1/jobs`)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/jobs` | List jobs. |
| GET | `/api/v1/jobs/{job_id}` | Get a job. |
| POST | `/api/v1/jobs/create` | Create a job. |
| PUT | `/api/v1/jobs/update` | Update a job. |
| DELETE | `/api/v1/jobs/delete` | Delete a job. |
| POST | `/api/v1/jobs/trigger` | Trigger a run. |
| POST | `/api/v1/jobs/run-now` | Run now (alias of trigger). |
| POST | `/api/v1/jobs/reset` | Overwrite job settings. |
| POST | `/api/v1/jobs/repair` | Repair a run's failed tasks. |
| POST | `/api/v1/jobs/cancel` | Cancel a run. |
| POST | `/api/v1/jobs/pause` | Pause a job's schedule. |
| POST | `/api/v1/jobs/resume` | Resume a job's schedule. |
| POST | `/api/v1/jobs/clone` | Clone a job. |
| POST | `/api/v1/jobs/export` | Export a job definition. |
| POST | `/api/v1/jobs/import` | Import a job definition. |

## Job Runs (`/api/v1/job-runs`)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/job-runs` | List runs. |
| GET | `/api/v1/job-runs/{run_id}` | Get a run. |
| GET | `/api/v1/job-runs/{run_id}/logs` | Get run logs. |
| GET | `/api/v1/job-runs/{run_id}/output` | Get run output. |
| POST | `/api/v1/job-runs/{run_id}/cancel` | Cancel a run. |
| POST | `/api/v1/job-runs/{run_id}/repair` | Repair a run. |
| POST | `/api/v1/job-runs/{run_id}/retry` | Retry (new run of same job). |
| POST | `/api/v1/job-runs/{run_id}/wait` | Poll until the run is terminal. |

## Clusters (`/api/v1/clusters`)

List, Create, Get, Start, Restart, Resize, Edit, Terminate,
Permanent-delete, Pin, Unpin, plus `meta/node-types`, `meta/spark-versions`,
and `{cluster_id}/events`.

## Workspace / Notebooks (`/api/v1/notebooks`)

Import, Export, List, Delete, Get status, Create folder, Move, Copy.

## SQL (`/api/v1/sql`)

Execute statement, statement status, cancel statement, warehouses
(list/create/get/start/stop/delete), query history.

## Unity Catalog (`/api/v1/unity-catalog`)

Catalogs, Schemas, Tables, Volumes, Functions, Permissions, Grants,
External Locations, Storage Credentials — full CRUD where the underlying
Databricks API supports it.

## DBFS (`/api/v1/dbfs`)

Upload, Download, Delete, Move, List, Mkdir, Read, Put, Create (streaming
handle for large files).

## Delta Live Tables (`/api/v1/dlt`)

Create/Update/Delete pipeline, Start (update), Stop, List, Get, list
pipeline events.

## MLflow (`/api/v1/mlflow`)

Experiments, Runs (create/get/delete/search, log-metric, log-param),
Artifacts (list), Model Registry (registered models + model versions +
stage transitions).

## Secrets (`/api/v1/secrets`)

Scopes (list/create/delete), Put/Delete secret, List secrets, List ACLs.

## Permissions (`/api/v1/permissions`)

Get permissions, Update ACL (PUT), Grant, Revoke — generic across any
Databricks object type (`jobs`, `clusters`, `notebooks`, etc.).

## Monitoring (`/api/v1/monitoring`)

Cluster/job metrics summaries, cluster/job health checks, connector
version/info, and non-sensitive connector configuration.

## Error format

Every error response (4xx/5xx) has the same shape:

```json
{
  "error": "not_found",
  "message": "Job not found",
  "details": {}
}
```

`error` is a stable machine-readable code (see `core/exceptions.py`);
`message` is human-readable; `details` carries any extra context (e.g. the
raw Databricks error body).
