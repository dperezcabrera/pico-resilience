import asyncio
import sys
import time

import pytest
from pico_ioc import component

from pico_resilience import CircuitOpenError, RetryExhaustedError, circuit_breaker, retryable, timeout


@component
class Flaky:
    def __init__(self):
        self.calls = 0

    @retryable(max_attempts=3, backoff_seconds=0.01)
    def eventually_ok(self):
        self.calls += 1
        if self.calls < 3:
            raise ConnectionError("boom")
        return "ok"

    @retryable(max_attempts=2, backoff_seconds=0.01)
    async def always_fails(self):
        self.calls += 1
        raise ValueError("nope")

    @retryable(max_attempts=3, backoff_seconds=0.01, retry_on=(ConnectionError,))
    def wrong_exception(self):
        self.calls += 1
        raise KeyError("not retryable")


@component
class Breaker:
    def __init__(self):
        self.calls = 0

    @circuit_breaker(failure_threshold=2, reset_timeout_seconds=0.2)
    def unstable(self, fail: bool):
        self.calls += 1
        if fail:
            raise ConnectionError("down")
        return "up"


@component
class Slow:
    @timeout(0.05)
    async def snail(self):
        await asyncio.sleep(1)

    @timeout(0.5)
    async def quick(self):
        return "fast"


def test_retry_succeeds_after_failures(make_container):
    svc = make_container(sys.modules[__name__]).get(Flaky)
    assert svc.eventually_ok() == "ok"
    assert svc.calls == 3


def test_retry_exhausted_async(make_container):
    svc = make_container(sys.modules[__name__]).get(Flaky)
    with pytest.raises(RetryExhaustedError) as e:
        asyncio.run(svc.always_fails())
    assert e.value.attempts == 2
    assert isinstance(e.value.last_error, ValueError)


def test_non_matching_exception_propagates_without_retry(make_container):
    svc = make_container(sys.modules[__name__]).get(Flaky)
    with pytest.raises(KeyError):
        svc.wrong_exception()
    assert svc.calls == 1


def test_circuit_opens_then_half_opens(make_container):
    svc = make_container(sys.modules[__name__]).get(Breaker)
    for _ in range(2):
        with pytest.raises(ConnectionError):
            svc.unstable(fail=True)
    with pytest.raises(CircuitOpenError):
        svc.unstable(fail=False)
    assert svc.calls == 2
    time.sleep(0.25)
    assert svc.unstable(fail=False) == "up"
    assert svc.unstable(fail=False) == "up"


def test_timeout_raises_and_passes(make_container):
    svc = make_container(sys.modules[__name__]).get(Slow)
    with pytest.raises(TimeoutError, match="snail"):
        asyncio.run(svc.snail())
    assert asyncio.run(svc.quick()) == "fast"


def test_timeout_rejects_sync_methods():
    with pytest.raises(TypeError, match="only supports async"):

        class Bad:
            @timeout(1.0)
            def sync_method(self): ...


def test_disabled_bypasses_policies(make_container):
    svc = make_container(sys.modules[__name__], enabled=False).get(Flaky)
    with pytest.raises(ConnectionError):
        svc.eventually_ok()
    assert svc.calls == 1


@component
class CountingInterceptor:
    invocations = 0

    def invoke(self, ctx, call_next):
        CountingInterceptor.invocations += 1
        return call_next(ctx)


def _counted(fn):
    from pico_ioc import intercepted_by

    return intercepted_by(CountingInterceptor)(fn)


@component
class Ordered:
    def __init__(self):
        self.calls = 0

    @retryable(max_attempts=3, backoff_seconds=0.01)
    @_counted
    def flaky(self):
        self.calls += 1
        if self.calls < 3:
            raise ConnectionError("boom")
        return "ok"


def test_policies_below_retryable_wrap_the_whole_loop(make_container):
    CountingInterceptor.invocations = 0
    svc = make_container(sys.modules[__name__]).get(Ordered)
    assert svc.flaky() == "ok"
    assert svc.calls == 3
    assert CountingInterceptor.invocations == 1


@component
class FlakySync:
    def __init__(self):
        self.calls = 0

    @retryable(max_attempts=2, backoff_seconds=0.01)
    def always_fails(self):
        self.calls += 1
        raise ValueError("nope")


def test_retry_exhausted_sync(make_container):
    svc = make_container(sys.modules[__name__]).get(FlakySync)
    with pytest.raises(RetryExhaustedError) as e:
        svc.always_fails()
    assert e.value.attempts == 2
    assert isinstance(e.value.last_error, ValueError)
    assert svc.calls == 2


@component
class AsyncBreaker:
    def __init__(self):
        self.calls = 0

    @circuit_breaker(failure_threshold=2, reset_timeout_seconds=0.2)
    async def unstable(self, fail: bool):
        self.calls += 1
        if fail:
            raise ConnectionError("down")
        return "up"


def test_async_circuit_opens_then_half_opens(make_container):
    svc = make_container(sys.modules[__name__]).get(AsyncBreaker)
    for _ in range(2):
        with pytest.raises(ConnectionError):
            asyncio.run(svc.unstable(fail=True))
    with pytest.raises(CircuitOpenError):
        asyncio.run(svc.unstable(fail=False))
    assert svc.calls == 2
    time.sleep(0.25)
    assert asyncio.run(svc.unstable(fail=False)) == "up"
    assert asyncio.run(svc.unstable(fail=False)) == "up"


def test_disabled_bypasses_circuit_and_timeout(make_container):
    container = make_container(sys.modules[__name__], enabled=False)
    breaker = container.get(Breaker)
    for _ in range(3):
        with pytest.raises(ConnectionError):
            breaker.unstable(fail=True)
    assert breaker.calls == 3
    assert asyncio.run(container.get(Slow).quick()) == "fast"


def test_retryable_rejects_zero_attempts():
    with pytest.raises(ValueError, match="max_attempts"):
        retryable(max_attempts=0)


def test_circuit_breaker_rejects_zero_threshold():
    with pytest.raises(ValueError, match="failure_threshold"):
        circuit_breaker(failure_threshold=0)


def test_timeout_rejects_non_positive_seconds():
    with pytest.raises(ValueError, match="positive"):
        timeout(0)
    with pytest.raises(ValueError, match="positive"):
        timeout("1")
