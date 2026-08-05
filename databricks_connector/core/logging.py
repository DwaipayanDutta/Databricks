"""Structured JSON logging configuration.

Provides a single configure_logging() entrypoint plus a JsonFormatter that
emits one JSON object per line, including correlation/request IDs pulled
from ContextVars, and masks well-known sensitive keys.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

from .constants import MASKED_KEYS
from .dependencies import correlation_id_ctx, request_id_ctx


class JsonFormatter(logging.Formatter):
    """Renders LogRecords as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = request_id_ctx.get()
        correlation_id = correlation_id_ctx.get()
        if request_id:
            payload["request_id"] = request_id
        if correlation_id:
            payload["correlation_id"] = correlation_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(_mask(extra))

        return json.dumps(payload, default=str)


def _mask(data: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in MASKED_KEYS:
            masked[key] = "***masked***"
        elif isinstance(value, dict):
            masked[key] = _mask(value)
        else:
            masked[key] = value
    return masked


def configure_logging(level: str = "INFO", json_format: bool = True) -> None:
    """Configure the root logger once for the whole process."""
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Avoid duplicate handlers on reload.
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)

    # Quiet down noisy third-party loggers a little.
    logging.getLogger("httpx").setLevel("WARNING")
    logging.getLogger("uvicorn.access").setLevel("WARNING")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class LogTimer:
    """Context manager that logs elapsed wall-clock time for a code block."""

    def __init__(self, logger: logging.Logger, operation: str, **fields: Any) -> None:
        self.logger = logger
        self.operation = operation
        self.fields = fields
        self._start = 0.0

    def __enter__(self) -> LogTimer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        elapsed_ms = round((time.perf_counter() - self._start) * 1000, 2)
        extra = {"operation": self.operation, "elapsed_ms": elapsed_ms, **self.fields}
        if exc_type:
            self.logger.error("operation_failed", extra={"extra_fields": extra})
        else:
            self.logger.info("operation_completed", extra={"extra_fields": extra})
