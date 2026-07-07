# pico-resilience

[![PyPI](https://img.shields.io/pypi/v/pico-resilience.svg)](https://pypi.org/project/pico-resilience/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/dperezcabrera/pico-resilience)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![CI (tox matrix)](https://github.com/dperezcabrera/pico-resilience/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/dperezcabrera/pico-resilience/branch/main/graph/badge.svg)](https://codecov.io/gh/dperezcabrera/pico-resilience)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-resilience&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-resilience)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-resilience&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-resilience)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-resilience&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-resilience)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pico-resilience)](https://pypi.org/project/pico-resilience/)
[![Docs](https://img.shields.io/badge/Docs-pico--resilience-blue?style=flat&logo=readthedocs&logoColor=white)](https://dperezcabrera.github.io/pico-resilience/)
[![Interactive Lab](https://img.shields.io/badge/Learn-online-green?style=flat&logo=python&logoColor=white)](https://dperezcabrera.github.io/pico-learn/)

Spring-style **resilience annotations** for the [Pico](https://github.com/dperezcabrera/pico-ioc) ecosystem, built on pico-ioc method interception and auto-discovered by [pico-boot](https://github.com/dperezcabrera/pico-boot). Zero-config.

| Decorator | Policy |
|---|---|
| `@retryable(max_attempts, backoff_seconds, retry_on)` | Exponential-backoff retry (sync + async) |
| `@circuit_breaker(failure_threshold, reset_timeout_seconds)` | Per-method circuit: closed → open → half-open |
| `@timeout(seconds)` | Async time budget via `asyncio.timeout` |

## Install

```bash
pip install pico-resilience
```

## Use

```python
from pico_ioc import component
from pico_resilience import retryable, circuit_breaker, timeout

@component
class PaymentGateway:
    @retryable(max_attempts=3, backoff_seconds=0.2, retry_on=(ConnectionError,))
    @circuit_breaker(failure_threshold=5, reset_timeout_seconds=30)
    def charge(self, order): ...

    @timeout(2.0)
    async def query_partner(self, q): ...
```

Failures raise `RetryExhaustedError` / `CircuitOpenError` / `TimeoutError` with the method name. `resilience.enabled: false` in `application.yaml` bypasses every policy (handy in tests).

Chain rule: put `@retryable` **at the top** when combining decorators (it runs innermost); `@circuit_breaker`/`@cacheable` below it then wrap the whole retry loop — the circuit counts exhausted retries and the cache stores the final result. `@timeout` rejects sync methods at import time: a thread cannot be cancelled, and a timeout that lies is worse than none.

## Documentation

Full docs at **[dperezcabrera.github.io/pico-resilience](https://dperezcabrera.github.io/pico-resilience/)**.

## License

MIT
