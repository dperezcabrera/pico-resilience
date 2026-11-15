"""The public API is exactly what ``__all__`` declares (stability contract)."""

import pico_resilience


def test_public_api_is_declared_and_importable():
    assert set(pico_resilience.__all__) == {
        "CircuitBreakerInterceptor",
        "CircuitOpenError",
        "PicoResilienceError",
        "ResilienceConfigRefresher",
        "ResilienceSettings",
        "RetryExhaustedError",
        "RetryInterceptor",
        "TimeoutInterceptor",
        "circuit_breaker",
        "retryable",
        "timeout",
    }
    for name in pico_resilience.__all__:
        assert getattr(pico_resilience, name) is not None
