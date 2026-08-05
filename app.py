"""FastAPI application factory for the Databricks connector.

Wires together configuration, middleware, routers, and lifespan hooks
(startup/graceful shutdown). `main.py` imports `app` from this module and
runs it with uvicorn.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from core.client import close_databricks_client, get_databricks_client
from core.config import get_settings
from core.constants import CONNECTOR_NAME, CONNECTOR_VERSION
from core.logging import configure_logging, get_logger
from core.middleware import (
    CorrelationMiddleware,
    ExceptionMiddleware,
    RequestLoggingMiddleware,
    TimingMiddleware,
)
from routers import (
    clusters,
    dbfs,
    dlt,
    health,
    job_runs,
    jobs,
    mlflow,
    monitoring,
    notebooks,
    permissions,
    secrets,
    sql,
    unity_catalog,
)

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
    )

    # --- Middleware (order matters: outermost added last is innermost) ---
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(GZipMiddleware, minimum_size=1024)
    application.add_middleware(ExceptionMiddleware)
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(TimingMiddleware)
    application.add_middleware(CorrelationMiddleware)

    # --- Routers ---
    application.include_router(health.router)
    application.include_router(jobs.router)
    application.include_router(job_runs.router)
    application.include_router(clusters.router)
    application.include_router(notebooks.router)
    application.include_router(sql.router)
    application.include_router(unity_catalog.router)
    application.include_router(dbfs.router)
    application.include_router(dlt.router)
    application.include_router(mlflow.router)
    application.include_router(secrets.router)
    application.include_router(permissions.router)
    application.include_router(monitoring.router)

    return application


app = create_app()
