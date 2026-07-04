"""Marker decorators: store the policy on the function and attach the
matching interceptor via ``intercepted_by`` (same idiom as pico-pydantic)."""

import inspect
from typing import Any, Callable, Tuple, Type

RETRY_META = "_pico_resilience_retry_meta"
CIRCUIT_META = "_pico_resilience_circuit_meta"
TIMEOUT_META = "_pico_resilience_timeout_meta"


def retryable(
    _func: Callable | None = None,
    *,
    max_attempts: int = 3,
    backoff_seconds: float = 0.1,
    retry_on: Tuple[Type[BaseException], ...] = (Exception,),
):
    """Retry on failure with exponential backoff. Sync or async. Raises
    ``RetryExhaustedError`` when every attempt failed."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    def dec(fn):
        setattr(
            fn, RETRY_META, {"max_attempts": max_attempts, "backoff_seconds": backoff_seconds, "retry_on": retry_on}
        )
        from pico_ioc import intercepted_by

        from .interceptors import RetryInterceptor

        return intercepted_by(RetryInterceptor)(fn)

    return dec(_func) if callable(_func) else dec


def circuit_breaker(
    _func: Callable | None = None,
    *,
    failure_threshold: int = 5,
    reset_timeout_seconds: float = 30.0,
):
    """Per-method circuit: opens after N consecutive failures (calls raise
    ``CircuitOpenError``), half-opens after the reset timeout."""
    if failure_threshold < 1:
        raise ValueError("failure_threshold must be >= 1")

    def dec(fn):
        setattr(
            fn, CIRCUIT_META, {"failure_threshold": failure_threshold, "reset_timeout_seconds": reset_timeout_seconds}
        )
        from pico_ioc import intercepted_by

        from .interceptors import CircuitBreakerInterceptor

        return intercepted_by(CircuitBreakerInterceptor)(fn)

    return dec(_func) if callable(_func) else dec


def timeout(seconds: float):
    """Bound an async method with ``asyncio.timeout``. Sync methods are
    rejected at import time — a thread cannot be cancelled, so a sync
    timeout would lie."""
    if not isinstance(seconds, (int, float)) or seconds <= 0:
        raise ValueError("timeout(seconds) requires a positive number")

    def dec(fn):
        if not inspect.iscoroutinefunction(fn):
            raise TypeError(f"@timeout only supports async methods; {fn.__qualname__} is sync")
        setattr(fn, TIMEOUT_META, {"seconds": float(seconds)})
        from pico_ioc import intercepted_by

        from .interceptors import TimeoutInterceptor

        return intercepted_by(TimeoutInterceptor)(fn)

    return dec


def _meta(ctx: Any, attr: str) -> dict:
    fn = getattr(ctx.cls, ctx.name, None)
    return getattr(fn, attr, {})
