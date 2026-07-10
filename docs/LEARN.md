# Learning Roadmap

Ten minutes from install to production policies.

1. **Install** — `pip install pico-resilience`; nothing to wire
   ([Getting Started](getting-started.md)).
2. **First retry** — add `@retryable(max_attempts=3)` to a flaky call;
   watch the WARNING logs per attempt.
3. **Protect a dependency** — `@circuit_breaker` on the partner API call;
   understand closed  open  half-open.
4. **Bound the tail** — `@timeout(2.0)` on async lookups; learn why sync is
   rejected ([FAQ](faq.md)).
5. **Combine** — `@retryable` on top; see the chain rule in
   [Architecture](architecture.md).
6. **Test** — `resilience.enabled: false` in test config; assert your own
   logic, not the policies.
