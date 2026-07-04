"""Exceptions for pico-resilience."""


class PicoResilienceError(Exception):
    """Base exception for all pico-resilience errors."""


class RetryExhaustedError(PicoResilienceError):
    """Raised when a ``@retryable`` method fails on every attempt.

    Attributes:
        method_name: The method that kept failing.
        attempts: How many attempts were made.
        last_error: The exception raised by the final attempt.
    """

    def __init__(self, method_name: str, attempts: int, last_error: Exception):
        self.method_name = method_name
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"{method_name}() failed after {attempts} attempts: {last_error}")


class CircuitOpenError(PicoResilienceError):
    """Raised when a call is rejected because the circuit is open.

    Attributes:
        method_name: The protected method.
        retry_after_seconds: Seconds until the circuit allows a trial call.
    """

    def __init__(self, method_name: str, retry_after_seconds: float):
        self.method_name = method_name
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"circuit for {method_name}() is open; retry in {retry_after_seconds:.1f}s")
