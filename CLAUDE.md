Read and follow ./AGENTS.md for project conventions.

## Pico Ecosystem Context

pico-resilience provides resilience AOP (@retryable, @circuit_breaker, @timeout) via pico-ioc `MethodInterceptor`. Decorators mirror pico-pydantic's `@validate` idiom: store policy on the function + `intercepted_by(Interceptor)`. Auto-discovered via `pico_boot.modules` entry point. Config prefix `resilience` (zero-config: all defaults).

## Key Reminders

- pico-ioc dependency: `>= 2.2.0`
- **NEVER change `version_scheme`** in pyproject.toml. It MUST remain `"post-release"`.
- requires-python >= 3.11
- Commit messages: one line only
- Retry attempts after the first re-invoke `ctx.method` directly; the documented rule is `@retryable` on TOP when combining (it runs innermost) — keep code and docs consistent with it
- `@timeout` must keep rejecting sync methods at decoration time
