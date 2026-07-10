# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [Unreleased]

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
