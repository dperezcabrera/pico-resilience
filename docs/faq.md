# FAQ

## Why is `@timeout` async-only?

Python threads cannot be cancelled. A "timeout" on a sync method would return
control while the work keeps running — a lie with a thread leak. Rejecting it
at decoration time is honest; wrap blocking work in async first.

## Does retry re-run other interceptors?

No: attempts after the first call the method directly. That is why
`@retryable` belongs on top when combining — policies below it wrap the whole
retry loop instead of being bypassed per attempt.

## Is circuit state shared between instances?

Yes — keyed by `module.Class.method`, held by the singleton interceptor,
guarded by a lock. Two instances of the same component share one circuit.

## Can I disable everything at once?

`resilience.enabled: false` turns every policy into a pass-through.
