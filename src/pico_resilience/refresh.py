"""Hot config reload: keep ResilienceSettings live across refresh_config().

pico-ioc's contract (ADR-013): already-created singletons keep their values;
components that need live config subscribe to ConfigChanged and re-read.
This subscriber updates the shared ResilienceSettings IN PLACE, so every
interceptor holding it sees the new value on the next invocation.

Fail-fast: hot reload is on by default and REQUIRES an EventBus — a missing
bus raises at startup instead of silently not reloading. Opt out explicitly
with ``resilience.hot_reload: false``. Only settings-driven behavior reloads
(today: ``enabled``); per-method policies are decorator arguments — code,
not config.
"""

import logging

from pico_ioc import ConfigChanged, ConfigurationError, EventBus, PicoContainer, component, configure

from .config import ResilienceSettings

logger = logging.getLogger(__name__)


@component
class ResilienceConfigRefresher:
    def __init__(self, container: PicoContainer, settings: ResilienceSettings):
        self._container = container
        self._settings = settings

    @configure
    def wire(self) -> None:
        if not self._settings.hot_reload:
            return
        if not self._container.has(EventBus):
            raise ConfigurationError(
                "resilience.hot_reload is on but no EventBus is registered: add "
                "'pico_ioc.event_bus' to init(modules=[...]) or opt out explicitly "
                "with resilience.hot_reload=false"
            )
        self._container.get(EventBus).subscribe(ConfigChanged, self.on_config_changed)

    def on_config_changed(self, event: ConfigChanged) -> None:
        if "resilience" not in event.prefixes:
            return
        manager = getattr(self._container, "_config_manager", None)
        resolver = getattr(manager, "_resolver", None)
        if resolver is None:
            return
        node = (resolver.tree() or {}).get("resilience") or {}
        enabled = bool(node.get("enabled", True))
        if enabled != self._settings.enabled:
            self._settings.enabled = enabled
            logger.info("resilience.enabled hot-reloaded to %s", enabled)
