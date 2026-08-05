"""Retry policy built on top of tenacity.

Retries transient failures (429/500/502/503/504 and network errors) with
exponential backoff + jitter, while giving up immediately on non-retryable
errors like 400/401/403/404/409.
"""

from __future__ import annotations

import logging

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from core.constants import RETRYABLE_STATUS_CODES
from core.logging import get_logger

logger = get_logger(__name__)


class RetryableHTTPError(Exception):
    """Raised internally to signal tenacity should retry an HTTP call."""

    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        super().__init__(f"Retryable HTTP status: {response.status_code}")


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, RetryableHTTPError):
        return True
    if isinstance(
        exc, httpx.ConnectTimeout | httpx.ReadTimeout | httpx.ConnectError | httpx.RemoteProtocolError
    ):
        return True
    return False


def build_retry_decorator(max_retries: int, backoff_factor: float):
    """Return a tenacity retry decorator configured from settings."""
    return retry(
        reraise=True,
        stop=stop_after_attempt(max_retries + 1),
        wait=wait_exponential_jitter(initial=backoff_factor, max=10.0),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )


def is_retryable_status(status_code: int) -> bool:
    return status_code in RETRYABLE_STATUS_CODES
