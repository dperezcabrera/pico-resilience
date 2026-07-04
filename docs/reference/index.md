# API Reference

| Symbol | Kind |
|---|---|
| `retryable(max_attempts=3, backoff_seconds=0.1, retry_on=(Exception,))` | decorator |
| `circuit_breaker(failure_threshold=5, reset_timeout_seconds=30.0)` | decorator |
| `timeout(seconds)` | decorator (async-only) |
| `ResilienceSettings` | `@configured`, prefix `resilience` |
| `RetryExhaustedError`, `CircuitOpenError` | exceptions |

Generated API docs: [API](api.md).
