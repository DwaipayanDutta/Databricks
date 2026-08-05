"""Entrypoint for running the connector with uvicorn.

Usage:
    python main.py
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import uvicorn

from app import app  # noqa: F401  (re-exported for `uvicorn main:app`)
from core.config import get_settings


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_config=None,  # we manage logging ourselves via core.logging
    )


if __name__ == "__main__":
    run()
