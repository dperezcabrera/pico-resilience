# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-07-10

### Fixed

- Declare the real dependency floor: `pico-ioc >= 2.3.0`. 0.2.0 imported `ConfigChanged` (new in 2.3.0) while still declaring `>= 2.2.0`, so installs resolving an older pico-ioc broke at import time.

## [0.2.0] - 2026-07-10

### Added

- Hot config reload: `ResilienceConfigRefresher` subscribes to `ConfigChanged` and updates `resilience.enabled` in place, so `container.refresh_config()` enables/disables every policy live.
- Fail-fast: hot reload is on by default and requires an EventBus — startup raises `ConfigurationError` if none is registered. Opt out explicitly with `resilience.hot_reload: false` (new setting).
- Ecosystem e2e test: fastapi + httpx + caching + resilience with live toggling.

## [0.1.0] - 2026-07-03

### Added

- `@retryable` with exponential backoff and `retry_on` filter (sync + async).
- `@circuit_breaker` with per-method closed/open/half-open state, thread-safe.
- `@timeout` for async methods via `asyncio.timeout`; sync methods rejected at decoration time.
- `ResilienceSettings` (prefix `resilience`): `enabled` master switch.
- Auto-discovery through the `pico_boot.modules` entry point; zero-config.

[Unreleased]: https://github.com/dperezcabrera/pico-resilience/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dperezcabrera/pico-resilience/releases/tag/v0.1.0
