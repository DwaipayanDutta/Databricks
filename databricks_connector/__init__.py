"""databricks_connector: enterprise async FastAPI connector for the Databricks REST API.

Public entrypoints:
    databricks_connector.app.create_app  -- FastAPI application factory
    databricks_connector.main.run        -- uvicorn entrypoint used by `python -m databricks_connector.main`
"""

from __future__ import annotations

__version__ = "1.1.0"
