# pico-resilience

Resilience AOP for pico-ioc components: @retryable, @circuit_breaker, @timeout.

## Commands

```bash
pip install -e ".[dev]"
pytest tests/ -v
pytest --cov=pico_resilience --cov-report=term-missing tests/
mkdocs serve -f mkdocs.yml
```

## Project Structure

```
src/pico_resilience/
  __init__.py       # Public API
  decorators.py     # @retryable / @circuit_breaker / @timeout (policy on fn + intercepted_by)
  interceptors.py   # Retry / CircuitBreaker / Timeout MethodInterceptor singletons
  config.py         # ResilienceSettings (prefix "resilience", enabled switch)
  exceptions.py     # RetryExhaustedError, CircuitOpenError
```

## Key Concepts

- Policies live on the function (`_pico_resilience_*_meta`); interceptors read them via `ctx.cls`/`ctx.name`.
- Sync and async both supported; async paths return wrapper coroutines.
- Circuit state: per-method key, shared dict + one lock on the singleton interceptor.
- Chain caveat: retries re-invoke `ctx.method` directly — `@circuit_breaker` above `@retryable` to count every attempt.
- `@timeout` is async-only, enforced at decoration time.
- `resilience.enabled: false` -> every interceptor passes through.

## Boundaries

- Do not modify `_version.py`
- No dependency on pico-boot (entry point only)
