# Databricks Connector

<p align="center">
  <img src="docs/assets/logo.png" width="180" alt="Databricks Connector">
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)
![Async](https://img.shields.io/badge/Async-httpx-success.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Databricks](https://img.shields.io/badge/Databricks-REST_API-orange.svg)
![Status](https://img.shields.io/badge/Status-Production_Ready-success.svg)

</p>

---

# Enterprise Databricks Connector

A **production-grade**, **enterprise-ready**, **async Databricks Connector** built with **FastAPI**, designed to expose the complete Databricks REST API through a clean, modular, and scalable interface.

This connector is intended to be used as a standalone microservice or as a connector inside an **Agentic AI / Multi-Agent Platform**, enabling AI agents, workflow engines, and enterprise applications to securely interact with Databricks Workspaces.

---

# Features

- Production Ready
- Async FastAPI Architecture
- Fully Typed (Python 3.12)
- REST API Wrapper for Databricks
- Modular Router Design
- Service Layer Architecture
- Shared Databricks Client
- Multiple Authentication Methods
- Automatic Token Refresh
- Retry with Exponential Backoff
- Circuit Breaker
- Structured JSON Logging
- Correlation IDs
- Request Tracing
- OpenAPI Documentation
- Swagger UI
- Health Endpoints
- Docker Support
- CI/CD Ready
- Unit Tests
- Clean Architecture
- Enterprise Security

---

# Architecture

```
                    ┌───────────────────────────────┐
                    │        Client Apps            │
                    │ AI Agents • UI • SDK • CLI   │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
                     ┌────────────────────────────┐
                     │        FastAPI API         │
                     │      REST Endpoints        │
                     └──────────────┬─────────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               ▼                    ▼                    ▼
          Jobs Router         SQL Router          Cluster Router
               ▼                    ▼                    ▼
        Service Layer      Service Layer      Service Layer
               └────────────────┬─────────────────────────┘
                                ▼
                   Databricks Async Client
                                │
     Authentication • Retry • Logging • Circuit Breaker
                                │
                                ▼
                  Databricks REST APIs (2.0 / 2.1)
```

---

# Project Structure

```
databricks_connector/
│
├── app.py
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
│
├── core/
│   ├── auth.py
│   ├── client.py
│   ├── config.py
│   ├── constants.py
│   ├── dependencies.py
│   ├── exceptions.py
│   ├── logging.py
│   ├── retry.py
│   ├── middleware.py
│   ├── circuit_breaker.py
│   └── cache.py
│
├── routers/
│   ├── health.py
│   ├── jobs.py
│   ├── job_runs.py
│   ├── clusters.py
│   ├── notebooks.py
│   ├── sql.py
│   ├── unity_catalog.py
│   ├── dbfs.py
│   ├── dlt.py
│   ├── mlflow.py
│   ├── secrets.py
│   ├── monitoring.py
│   └── permissions.py
│
├── services/
│
├── schemas/
│
├── tests/
│
├── docs/
│
└── scripts/
```

---

# Supported Authentication

The connector supports every major Databricks authentication mechanism.

| Authentication | Supported |
|---------------|-----------|
| Personal Access Token | ✅ |
| OAuth | ✅ |
| Azure Service Principal | ✅ |
| Azure Managed Identity | ✅ |
| Bearer Token | ✅ |

---

# API Groups

## Health

```
GET /health
GET /ready
GET /live
```

---

## Jobs

```
GET    /api/v1/jobs
GET    /api/v1/jobs/{id}
POST   /api/v1/jobs/create
PUT    /api/v1/jobs/update
DELETE /api/v1/jobs/delete

POST   /api/v1/jobs/trigger
POST   /api/v1/jobs/run-now
POST   /api/v1/jobs/reset
POST   /api/v1/jobs/repair
POST   /api/v1/jobs/pause
POST   /api/v1/jobs/resume
POST   /api/v1/jobs/clone
POST   /api/v1/jobs/export
POST   /api/v1/jobs/import
```

---

## Job Runs

```
GET    /api/v1/job-runs
GET    /api/v1/job-runs/{run_id}
GET    /api/v1/job-runs/{run_id}/logs
GET    /api/v1/job-runs/{run_id}/output

POST   /api/v1/job-runs/{run_id}/cancel
POST   /api/v1/job-runs/{run_id}/repair
POST   /api/v1/job-runs/{run_id}/retry
POST   /api/v1/job-runs/{run_id}/wait
```

---

## Clusters

```
Create Cluster
Get Cluster
List Clusters
Start Cluster
Restart Cluster
Resize Cluster
Terminate Cluster
Delete Cluster
Pin Cluster
Unpin Cluster
```

---

## Workspace

```
Import Notebook
Export Notebook
List Workspace
Delete Notebook
Move Notebook
Copy Notebook
Create Folder
```

---

## SQL

```
Execute SQL
Statement Status
Cancel Statement
Query History
Warehouses
```

---

## Unity Catalog

```
Catalogs
Schemas
Tables
Volumes
Functions
Permissions
Storage Credentials
External Locations
```

---

## DBFS

```
Upload
Download
Delete
Move
Read
Write
List
Create Directory
```

---

## Delta Live Tables

```
Create Pipeline
Update Pipeline
Delete Pipeline
Start
Stop
List
Get Pipeline
```

---

## MLflow

```
Experiments
Runs
Artifacts
Registry
Models
Versions
```

---

## Secrets

```
Scopes
Secrets
Create
Delete
List
```

---

## Permissions

```
Get
Grant
Revoke
ACL
```

---

## Monitoring

```
Metrics
Connector Status
Logs
Health
Version
Configuration
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/<your-org>/databricks-connector.git

cd databricks-connector
```

---

## Create Virtual Environment

```bash
python -m venv .venv
```

Windows

```bash
.venv\Scripts\activate
```

Linux

```bash
source .venv/bin/activate
```

---

## Install

```bash
pip install -r requirements.txt
```

---

# Configuration

Create

```
.env
```

```
DATABRICKS_HOST=https://adb-xxxxxxxx.azuredatabricks.net

DATABRICKS_TOKEN=xxxxxxxxxxxxxxxxxxxx

DATABRICKS_AUTH_TYPE=pat

DEFAULT_CLUSTER=cluster-id

DEFAULT_WAREHOUSE=warehouse-id

TIMEOUT=30

MAX_RETRIES=3

VERIFY_SSL=true
```

---

# Running

Development

```bash
uvicorn app:app --reload
```

Production

```bash
gunicorn app:app \
-k uvicorn.workers.UvicornWorker \
-w 4
```

---

# Swagger

```
http://localhost:8000/docs
```

---

# OpenAPI

```
http://localhost:8000/openapi.json
```

---

# Health

```
GET /health

GET /ready

GET /live
```

---

# Example

Trigger a Job

```bash
curl -X POST \
http://localhost:8000/api/v1/jobs/run-now \
-H "Content-Type: application/json" \
-d '{
  "job_id":12345
}'
```

---

# Logging

Structured JSON logs

```json
{
  "timestamp":"...",
  "level":"INFO",
  "request_id":"...",
  "correlation_id":"...",
  "execution_time":"102ms"
}
```

---

# Security

- OAuth Support
- PAT Authentication
- Managed Identity
- Secret Masking
- SSL Verification
- Correlation IDs
- Request Validation
- Rate Limiting Ready
- Circuit Breaker
- Retry Policies

---

# Testing

Run all tests

```bash
pytest
```

Coverage

```bash
pytest --cov=databricks_connector
```

---

# Docker

Build

```bash
docker build -t databricks-connector .
```

Run

```bash
docker-compose up
```

---

# CI/CD

GitHub Actions pipeline includes

- Ruff
- Black
- MyPy
- PyTest
- Coverage
- Docker Build

---

# Design Principles

- Clean Architecture
- SOLID Principles
- Dependency Injection
- Async First
- Modular Routers
- Thin Controllers
- Service Layer Pattern
- Shared Databricks Client
- Enterprise Logging
- High Testability

---

# Future Roadmap

- Kubernetes Helm Chart
- Prometheus Metrics
- Grafana Dashboard
- OpenTelemetry
- Redis Distributed Cache
- Azure Key Vault Integration
- AWS Secrets Manager
- GCP Secret Manager
- SDK Generation
- MCP Server Support
- LangGraph Native Integration
- Agentic Workflow Support
- Multi-Workspace Support

---

# Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push your branch
5. Open a Pull Request

---

# License

MIT License

---

# Maintainer

**Dwaipayan Dutta**

Enterprise AI • Agentic AI • Databricks • Multi-Agent Systems • Generative AI

---

<p align="center">

**Enterprise Databricks Connector**

*Production-ready • Async • Scalable • Secure*

</p>
