"""Retry policy built on top of tenacity.

Retries transient failures (429/500/502/503/504 and network errors) with
exponential backoff + jitter, honoring a server-supplied `Retry-After`
header when present (common on 429 and some 503 responses), while giving
up immediately on non-retryable errors like 400/401/403/404/409.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from email.utils import parsedate_to_datetime
from time import time as _wall_clock_now
from typing import Any

import httpx
from tenacity import (
    RetryCallState,
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from .constants import RETRYABLE_STATUS_CODES
from .logging import get_logger

logger = get_logger(__name__)

# Cap how long we'll ever honor a server-supplied Retry-After value for, so
# a misbehaving/hostile upstream can't stall a request indefinitely.
_MAX_RETRY_AFTER_SECONDS = 120.0


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


def _parse_retry_after(value: str | None) -> float | None:
    """Parse a `Retry-After` header value into a non-negative second count.

    Supports both forms allowed by RFC 9110: an integer number of seconds,
    or an HTTP-date. Returns None if the header is absent or unparseable.
    """
    if not value:
        return None

    value = value.strip()
    if value.isdigit():
        seconds = float(value)
        return max(0.0, min(seconds, _MAX_RETRY_AFTER_SECONDS))

    try:
        target = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if target is None:
        return None

    seconds = target.timestamp() - _wall_clock_now()
    return max(0.0, min(seconds, _MAX_RETRY_AFTER_SECONDS))


def _retry_after_wait(backoff_factor: float, max_wait: float = 10.0) -> Callable[[RetryCallState], float]:
    """Return a tenacity `wait` callable that prefers a server `Retry-After`
    header (e.g. on 429 rate-limit responses) and otherwise falls back to
    exponential backoff with jitter.
    """
    exponential_wait = wait_exponential_jitter(initial=backoff_factor, max=max_wait)

    def _wait(retry_state: RetryCallState) -> float:
        outcome = retry_state.outcome
        if outcome is not None and not outcome.failed:
            return 0.0
        exc = outcome.exception() if outcome is not None else None
        if isinstance(exc, RetryableHTTPError):
            retry_after = _parse_retry_after(exc.response.headers.get("Retry-After"))
            if retry_after is not None:
                logger.info(
                    "retry_after_header_honored",
                    extra={"extra_fields": {"retry_after_seconds": retry_after}},
                )
                return retry_after
        return float(exponential_wait(retry_state))

    return _wait


def build_retry_decorator(max_retries: int, backoff_factor: float) -> Any:
    """Return a tenacity retry decorator configured from settings.

    * Retries only on the statuses in RETRYABLE_STATUS_CODES (429, 500,
      502, 503, 504) and a handful of transient network-level errors.
    * Uses exponential backoff with jitter by default, but honors a
      `Retry-After` header when the upstream provides one.
    """
    return retry(
        reraise=True,
        stop=stop_after_attempt(max_retries + 1),
        wait=_retry_after_wait(backoff_factor, max_wait=10.0),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )


def is_retryable_status(status_code: int) -> bool:
    """True if `status_code` is one of the statuses we retry on (429/500/502/503/504)."""
    return status_code in RETRYABLE_STATUS_CODES
