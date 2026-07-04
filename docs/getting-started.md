# Getting Started

## Install

```bash
pip install pico-resilience
```

Auto-discovered by pico-boot; nothing to wire. Decorated methods must live on
`@component` classes (interception happens through the container proxy).

## Retry

```python
@retryable(max_attempts=3, backoff_seconds=0.1, retry_on=(ConnectionError, TimeoutError))
async def fetch(self): ...
```

Delay doubles per attempt. Exceptions outside `retry_on` propagate
immediately; exhaustion raises `RetryExhaustedError` (carries `attempts` and
`last_error`).

## Circuit breaker

```python
@circuit_breaker(failure_threshold=5, reset_timeout_seconds=30)
def call_partner(self): ...
```

After 5 consecutive failures the circuit opens: calls raise
`CircuitOpenError` without touching the dependency. After 30s one trial call
is allowed (half-open); success closes the circuit, failure reopens it.
State is per method, shared across instances, thread-safe.

## Timeout

```python
@timeout(2.0)
async def query(self, q): ...
```

Async-only by design — a thread cannot be cancelled, so a sync timeout would
lie. Decorating a sync method raises `TypeError` at import time.

## Combining policies

Decorators attach bottom-up: the bottom one runs **outermost**. Retry
attempts after the first re-invoke the method directly, so anything inside
retry's position is skipped on retries. Rule of thumb: **`@retryable` goes on
top** — `@circuit_breaker` and `@cacheable` below it then wrap the whole
retry loop (the circuit counts exhausted retries; the cache stores the final
result).

```python
@retryable(max_attempts=3)
@circuit_breaker(failure_threshold=5)
def charge(self, order): ...
```

## Disabling in tests

```yaml
resilience:
  enabled: false
```
