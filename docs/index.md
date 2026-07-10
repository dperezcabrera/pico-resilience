# pico-resilience

Part of an ecosystem [built for the AI era](https://dperezcabrera.github.io/pico-ioc/ai-ready/):
machine-readable conventions in every repo, installable
[AI coding skills](https://github.com/dperezcabrera/pico-skills), and
[scaffolds](https://dperezcabrera.github.io/pico-initializer/) that generate
AI-maintainable projects.

Spring-style resilience annotations over [pico-ioc](https://github.com/dperezcabrera/pico-ioc)
method interception, auto-discovered by pico-boot. Zero-config.

| Decorator | Policy |
|---|---|
| `@retryable` | Exponential-backoff retry (sync + async) |
| `@circuit_breaker` | Per-method circuit: closed → open → half-open |
| `@timeout` | Async time budget via `asyncio.timeout` |

## 30-second example

```python
from pico_ioc import component
from pico_resilience import retryable, circuit_breaker

@component
class PaymentGateway:
    @retryable(max_attempts=3, backoff_seconds=0.2, retry_on=(ConnectionError,))
    @circuit_breaker(failure_threshold=5, reset_timeout_seconds=30)
    def charge(self, order): ...
```

Continue with [Getting Started](getting-started.md).

**See it in context**: the [flagship use case](https://dperezcabrera.github.io/pico-boot/flagship/) wires this module into a full order platform together with the rest of the ecosystem.
