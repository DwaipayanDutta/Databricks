"""A small async-safe circuit breaker.

States: CLOSED -> OPEN -> HALF_OPEN -> CLOSED

* CLOSED: requests pass through normally; consecutive failures are counted.
* OPEN: requests fail fast with CircuitBreakerOpenError until the recovery
  timeout elapses.
* HALF_OPEN: a single trial request is allowed through; success closes the
  circuit, failure re-opens it.
"""

from __future__ import annotations

import asyncio
import enum
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from .exceptions import CircuitBreakerOpenError
from .logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CircuitState(enum.StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Async-safe circuit breaker with CLOSED -> OPEN -> HALF_OPEN -> CLOSED
    transitions.

    Concurrency model: a single `asyncio.Lock` guards all state mutation, so
    state transitions themselves are atomic. In HALF_OPEN, only **one**
    in-flight trial call is permitted at a time -- every other concurrent
    caller fails fast with `CircuitBreakerOpenError` rather than piling on
    to a service that is still recovering. Any failure during that trial
    immediately re-opens the circuit (a fresh `recovery_timeout` window
    starts); a success closes it and resets the failure count.
    """

    def __init__(
        self, failure_threshold: int = 5, recovery_timeout: float = 30.0, name: str = "default"
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at: float = 0.0
        self._half_open_trial_in_flight = False
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    async def _record_success(self) -> None:
        async with self._lock:
            self._failure_count = 0
            self._half_open_trial_in_flight = False
            if self._state != CircuitState.CLOSED:
                logger.info("circuit_breaker_closed", extra={"extra_fields": {"name": self.name}})
            self._state = CircuitState.CLOSED

    async def _record_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            was_half_open = self._state == CircuitState.HALF_OPEN
            self._half_open_trial_in_flight = False
            if was_half_open or self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                logger.warning(
                    "circuit_breaker_opened",
                    extra={
                        "extra_fields": {
                            "name": self.name,
                            "failures": self._failure_count,
                            "from_half_open": was_half_open,
                        }
                    },
                )

    async def _before_call(self) -> None:
        async with self._lock:
            if self._state == CircuitState.OPEN:
                elapsed = time.monotonic() - self._opened_at
                if elapsed < self.recovery_timeout:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is open; retry after "
                        f"{self.recovery_timeout - elapsed:.1f}s"
                    )
                # Recovery window elapsed: transition to HALF_OPEN and let
                # *this* caller through as the single trial request.
                self._state = CircuitState.HALF_OPEN
                self._half_open_trial_in_flight = True
                logger.info("circuit_breaker_half_open", extra={"extra_fields": {"name": self.name}})
                return

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_trial_in_flight:
                    # A trial call is already in flight; everyone else fails
                    # fast rather than piling on to a recovering dependency.
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is half-open; a trial request is already in flight"
                    )
                self._half_open_trial_in_flight = True
                return

            # CLOSED: pass through freely.
            return

    async def call(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        await self._before_call()
        try:
            result = await func(*args, **kwargs)
        except Exception:
            await self._record_failure()
            raise
        else:
            await self._record_success()
            return result


_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str = "databricks", failure_threshold: int = 5, recovery_timeout: float = 30.0
) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(failure_threshold, recovery_timeout, name)
    return _breakers[name]
