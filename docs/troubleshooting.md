# Troubleshooting

## My policy never triggers

The method must live on a `@component` class resolved **through the
container** — interception happens in the proxy. A manually constructed
instance (`Svc()`) bypasses everything.

## Retry works but the result is not cached / the circuit ignores attempts

Decorator order. `@retryable` must be the **top** decorator; policies below
it wrap the whole retry loop. See [Getting Started](getting-started.md).

## `TypeError: @timeout only supports async methods`

By design — see [FAQ](faq.md). Make the method `async def` (and its blocking
work `asyncio.to_thread`) or drop the timeout.

## Everything passes through in tests

Check `resilience.enabled` — `false` disables every policy. That is also the
recommended way to silence resilience in unit tests.

## `CircuitOpenError` in tests that reuse a process

Circuit state lives in the singleton interceptor per container. A fresh
`init()` gets fresh state; reusing a container across tests shares circuits.
