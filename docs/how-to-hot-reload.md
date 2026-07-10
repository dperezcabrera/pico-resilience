# How-To: Hot Config Reload

`resilience.enabled` reacts live to pico-ioc's hot refresh (pico-ioc >= 2.3.0):

```python
data = {"resilience": {"enabled": True}}
container = init(modules=["pico_resilience", "pico_ioc.event_bus", "my_app"],
                 config=configuration(DictSource(data)))

data["resilience"]["enabled"] = False
container.refresh_config()      # publishes ConfigChanged
# from this moment @retryable/@circuit_breaker/@timeout pass through
```

## How it works

pico-ioc's contract (ADR-013): already-created singletons keep their values;
consumers subscribe to `ConfigChanged` and re-read. pico-resilience ships
`ResilienceConfigRefresher`, which updates the shared `ResilienceSettings`
IN PLACE — every interceptor sees the new value on its next invocation.

Requirements and limits:

- An `EventBus` must be registered (module `pico_ioc.event_bus`; pico-boot
  apps usually have it). Without one the refresher is inert — nothing breaks,
  values simply stay as built.
- The refresh trigger lives outside: pico-actuator's `POST /actuator/refresh`,
  a file watcher, or your own call to `container.refresh_config()`.
- Only `resilience.enabled` is config. Per-method policies (attempts,
  thresholds, timeouts) are decorator arguments — code, not config — and do
  not hot-reload by design.

## Validated end to end

`tests/test_e2e_ecosystem.py` runs the real stack in one container —
a pico-fastapi upstream served through `httpx.ASGITransport`, a declarative
pico-httpx client with `@retryable` stacked on the stub, and `@cacheable`
memoizing the recovered result — and flips `resilience.enabled` live in both
directions.
