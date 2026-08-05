"""Entrypoint for running the connector with uvicorn.

Usage:
    python -m databricks_connector.main
    uvicorn databricks_connector.main:app --host 0.0.0.0 --port 8000
    uvicorn databricks_connector.app:create_app --factory
"""

from __future__ import annotations

import uvicorn

from databricks_connector.app import app as app  # re-exported for `uvicorn databricks_connector.main:app`
from databricks_connector.core.config import get_settings


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "databricks_connector.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_config=None,  # we manage logging ourselves via core.logging
    )


if __name__ == "__main__":
    run()
