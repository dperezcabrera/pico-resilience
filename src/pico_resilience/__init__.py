"""pico-resilience: resilience AOP for the Pico ecosystem.

Spring-style resilience annotations over pico-ioc's method interception:
``@retryable`` (exponential backoff), ``@circuit_breaker`` (per-method
closed/open/half-open state) and ``@timeout`` (async time budget). Decorate
methods on ``@component`` classes; interceptors are auto-discovered through
pico-boot. Zero-config: no ``resilience:`` block required.

Public API:
    Decorators: retryable, circuit_breaker, timeout
    Settings: ResilienceSettings
    Exceptions: PicoResilienceError, RetryExhaustedError, CircuitOpenError
"""

from .config import ResilienceSettings
from .decorators import circuit_breaker, retryable, timeout
from .exceptions import CircuitOpenError, PicoResilienceError, RetryExhaustedError
from .interceptors import CircuitBreakerInterceptor, RetryInterceptor, TimeoutInterceptor

__all__ = [
    "retryable",
    "circuit_breaker",
    "timeout",
    "ResilienceSettings",
    "PicoResilienceError",
    "RetryExhaustedError",
    "CircuitOpenError",
    "RetryInterceptor",
    "CircuitBreakerInterceptor",
    "TimeoutInterceptor",
]
