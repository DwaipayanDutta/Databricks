"""FastAPI application factory for the Databricks connector.

Wires together configuration, middleware, routers, and lifespan hooks
(startup/graceful shutdown). `main.py` imports `app` from this module and
runs it with uvicorn.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from databricks_connector.core.client import close_databricks_client, get_databricks_client
from databricks_connector.core.config import get_settings
from databricks_connector.core.constants import CONNECTOR_NAME, CONNECTOR_VERSION
from databricks_connector.core.dependencies import verify_connector_api_key
from databricks_connector.core.logging import configure_logging, get_logger
from databricks_connector.core.middleware import (
    CorrelationMiddleware,
    ExceptionMiddleware,
    MetricsMiddleware,
    RequestLoggingMiddleware,
    TimingMiddleware,
)
from databricks_connector.routers import (
    clusters,
    dbfs,
    dlt,
    health,
    job_runs,
    jobs,
    metrics,
    mlflow,
    monitoring,
    notebooks,
    permissions,
    secrets,
    sql,
    unity_catalog,
)
from databricks_connector.schemas.common import ErrorResponse

settings = get_settings()
configure_logging(level=settings.log_level, json_format=settings.log_format == "json")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / graceful shutdown hooks."""
    logger.info(
        "connector_starting",
        extra={
            "extra_fields": {"name": CONNECTOR_NAME, "version": CONNECTOR_VERSION, "env": settings.app_env}
        },
    )
    # Warm the shared Databricks client/http connection pool.
    get_databricks_client()
    yield
    logger.info("connector_shutting_down")
    await close_databricks_client()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Databricks Connector",
        description=(
            "Enterprise-grade FastAPI connector exposing the full Databricks "
            "REST API surface (Jobs, Clusters, Workspace, SQL, Unity Catalog, "
            "DBFS, Delta Live Tables, MLflow, Secrets, Permissions, Monitoring) "
            "for use inside a Multi-Agent AI Platform."
        ),
        version=CONNECTOR_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        # Documents the shared error body shape (see schemas.common.ErrorResponse
        # and core.exceptions) as the response model for every error status this
        # connector can return, across every endpoint in the generated OpenAPI
        # schema, rather than leaving error responses undocumented.
        responses={
            400: {"model": ErrorResponse, "description": "Validation error"},
            401: {"model": ErrorResponse, "description": "Authentication error"},
            403: {"model": ErrorResponse, "description": "Authorization error"},
            404: {"model": ErrorResponse, "description": "Not found"},
            409: {"model": ErrorResponse, "description": "Conflict"},
            429: {"model": ErrorResponse, "description": "Rate limited"},
            500: {"model": ErrorResponse, "description": "Internal error"},
            503: {"model": ErrorResponse, "description": "Service unavailable"},
        },
    )

    # --- Middleware (order matters: outermost added last is innermost) ---
    # `allow_credentials=True` combined with a literal `allow_origins=["*"]`
    # wildcard is a spec-invalid combination browsers reject outright (and
    # Starlette otherwise papers over in a way that's easy to misread as
    # "working"); only send credentialed CORS headers once the operator has
    # configured a real origin allowlist via CORS_ALLOW_ORIGINS.
    cors_origins = settings.cors_origins_list
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(GZipMiddleware, minimum_size=1024)
    application.add_middleware(ExceptionMiddleware)
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(MetricsMiddleware)
    application.add_middleware(TimingMiddleware)
    application.add_middleware(CorrelationMiddleware)

    # --- Routers ---
    # Health/liveness/readiness and Prometheus metrics stay ungated even
    # when CONNECTOR_API_KEY is set: orchestrators (Kubernetes probes) and
    # scrapers (Prometheus) call these without app-level credentials, and
    # gating them would break standard deployment tooling. Every business
    # API group requires the key (a no-op when CONNECTOR_API_KEY is unset).
    application.include_router(health.router)
    application.include_router(metrics.router)

    api_key_gate = [Depends(verify_connector_api_key)]
    application.include_router(jobs.router, dependencies=api_key_gate)
    application.include_router(job_runs.router, dependencies=api_key_gate)
    application.include_router(clusters.router, dependencies=api_key_gate)
    application.include_router(notebooks.router, dependencies=api_key_gate)
    application.include_router(sql.router, dependencies=api_key_gate)
    application.include_router(unity_catalog.router, dependencies=api_key_gate)
    application.include_router(dbfs.router, dependencies=api_key_gate)
    application.include_router(dlt.router, dependencies=api_key_gate)
    application.include_router(mlflow.router, dependencies=api_key_gate)
    application.include_router(secrets.router, dependencies=api_key_gate)
    application.include_router(permissions.router, dependencies=api_key_gate)
    application.include_router(monitoring.router, dependencies=api_key_gate)

    return application


app = create_app()
