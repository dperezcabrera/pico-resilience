"""Resilience interceptors (pico-ioc ``MethodInterceptor`` singletons).

Chain rule: retry attempts after the first re-invoke the method directly,
so interceptors *inside* retry's position are skipped on retries. Combine
policies with ``@retryable`` as the TOP decorator (it attaches last and runs
innermost): ``@cacheable``/``@circuit_breaker`` below it wrap the whole retry
loop — the cache stores the final result and the circuit counts exhausted
retries, not individual attempts.
"""

import asyncio
import inspect
import logging
import threading
import time
from typing import Any, Callable, Dict

from pico_ioc import MethodCtx, component

from .config import ResilienceSettings
from .decorators import CIRCUIT_META, RETRY_META, TIMEOUT_META, _meta
from .exceptions import CircuitOpenError, RetryExhaustedError

logger = logging.getLogger(__name__)


def _is_async(ctx: MethodCtx) -> bool:
    return inspect.iscoroutinefunction(ctx.method)


@component(scope="singleton")
class RetryInterceptor:
    """Retries the method per its ``@retryable`` policy."""

    def __init__(self, settings: ResilienceSettings):
        self.settings = settings

    def invoke(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        meta = _meta(ctx, RETRY_META)
        if not self.settings.enabled or not meta:
            return call_next(ctx)
        if _is_async(ctx):
            return self._run_async(ctx, call_next, meta)
        return self._run_sync(ctx, call_next, meta)

    def _run_sync(self, ctx, call_next, meta):
        last: Exception | None = None
        for attempt in range(1, meta["max_attempts"] + 1):
            try:
                return call_next(ctx) if attempt == 1 else ctx.method(*ctx.args, **ctx.kwargs)
            except meta["retry_on"] as exc:
                last = exc
                self._log(ctx, attempt, meta, exc)
                if attempt < meta["max_attempts"]:
                    time.sleep(self._delay(meta, attempt))
        raise RetryExhaustedError(ctx.name, meta["max_attempts"], last)

    async def _run_async(self, ctx, call_next, meta):
        last: Exception | None = None
        for attempt in range(1, meta["max_attempts"] + 1):
            try:
                return await (call_next(ctx) if attempt == 1 else ctx.method(*ctx.args, **ctx.kwargs))
            except meta["retry_on"] as exc:
                last = exc
                self._log(ctx, attempt, meta, exc)
                if attempt < meta["max_attempts"]:
                    await asyncio.sleep(self._delay(meta, attempt))
        raise RetryExhaustedError(ctx.name, meta["max_attempts"], last)

    @staticmethod
    def _delay(meta, attempt: int) -> float:
        return meta["backoff_seconds"] * (2 ** (attempt - 1))

    @staticmethod
    def _log(ctx, attempt, meta, exc):
        logger.warning("%s.%s attempt %d/%d failed: %s", ctx.cls.__name__, ctx.name, attempt, meta["max_attempts"], exc)


class _CircuitState:
    __slots__ = ("failures", "opened_at")

    def __init__(self):
        self.failures = 0
        self.opened_at: float | None = None


@component(scope="singleton")
class CircuitBreakerInterceptor:
    """Per-method circuit: closed -> open -> half-open -> closed."""

    def __init__(self, settings: ResilienceSettings):
        self.settings = settings
        self._states: Dict[str, _CircuitState] = {}
        # ponytail: one global lock; per-circuit locks if contention ever matters.
        self._lock = threading.Lock()

    def invoke(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        meta = _meta(ctx, CIRCUIT_META)
        if not self.settings.enabled or not meta:
            return call_next(ctx)
        key = f"{ctx.cls.__module__}.{ctx.cls.__qualname__}.{ctx.name}"
        if _is_async(ctx):
            return self._run_async(ctx, call_next, meta, key)
        self._check(key, meta, ctx)
        try:
            result = call_next(ctx)
        except Exception:
            self._record_failure(key, meta, ctx)
            raise
        self._record_success(key)
        return result

    async def _run_async(self, ctx, call_next, meta, key):
        self._check(key, meta, ctx)
        try:
            result = await call_next(ctx)
        except Exception:
            self._record_failure(key, meta, ctx)
            raise
        self._record_success(key)
        return result

    def _check(self, key: str, meta, ctx) -> None:
        with self._lock:
            st = self._states.setdefault(key, _CircuitState())
            if st.opened_at is None:
                return
            elapsed = time.monotonic() - st.opened_at
            if elapsed < meta["reset_timeout_seconds"]:
                raise CircuitOpenError(ctx.name, meta["reset_timeout_seconds"] - elapsed)
            # half-open: this call is the trial; one failure reopens
            st.opened_at = None
            st.failures = meta["failure_threshold"] - 1

    def _record_failure(self, key: str, meta, ctx) -> None:
        with self._lock:
            st = self._states.setdefault(key, _CircuitState())
            st.failures += 1
            if st.failures >= meta["failure_threshold"]:
                st.opened_at = time.monotonic()
                logger.error("circuit OPEN for %s.%s after %d failures", ctx.cls.__name__, ctx.name, st.failures)

    def _record_success(self, key: str) -> None:
        with self._lock:
            st = self._states.setdefault(key, _CircuitState())
            st.failures = 0
            st.opened_at = None


@component(scope="singleton")
class TimeoutInterceptor:
    """Bounds async methods with ``asyncio.timeout``."""

    def __init__(self, settings: ResilienceSettings):
        self.settings = settings

    def invoke(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        meta = _meta(ctx, TIMEOUT_META)
        if not self.settings.enabled or not meta:
            return call_next(ctx)
        return self._bounded(ctx, call_next, meta["seconds"])

    @staticmethod
    async def _bounded(ctx, call_next, seconds: float):
        try:
            async with asyncio.timeout(seconds):
                return await call_next(ctx)
        except TimeoutError:
            raise TimeoutError(f"{ctx.cls.__name__}.{ctx.name}() exceeded {seconds}s") from None
