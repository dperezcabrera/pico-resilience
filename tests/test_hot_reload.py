"""Hot config reload: resilience.enabled reacts to container.refresh_config()."""

import sys

import pytest
from pico_ioc import component

from pico_resilience import CircuitOpenError, ResilienceSettings, circuit_breaker, retryable


@component
class FragileService:
    def __init__(self):
        self.calls = 0

    @retryable(max_attempts=3, backoff_seconds=0.01)
    def eventually_ok(self):
        self.calls += 1
        if self.calls % 3 != 0:
            raise ConnectionError("boom")
        return "ok"

    @circuit_breaker(failure_threshold=2, reset_timeout_seconds=60)
    def always_down(self):
        raise ConnectionError("down")


def test_disable_resilience_hot(make_container_with_source):
    container, data = make_container_with_source({"resilience": {"enabled": True}})
    svc = container.get(FragileService)
    assert svc.eventually_ok() == "ok"
    assert svc.calls == 3

    data["resilience"]["enabled"] = False
    assert container.refresh_config() == frozenset({"resilience"})
    assert container.get(ResilienceSettings).enabled is False

    with pytest.raises(ConnectionError):
        svc.eventually_ok()
    assert svc.calls == 4


def test_enable_resilience_hot(make_container_with_source):
    container, data = make_container_with_source({"resilience": {"enabled": False}})
    svc = container.get(FragileService)
    with pytest.raises(ConnectionError):
        svc.eventually_ok()
    assert svc.calls == 1

    data["resilience"]["enabled"] = True
    container.refresh_config()

    assert svc.eventually_ok() == "ok"


def test_circuit_breaker_reacts_to_hot_disable(make_container_with_source):
    container, data = make_container_with_source({"resilience": {"enabled": True}})
    svc = container.get(FragileService)
    for _ in range(2):
        with pytest.raises(ConnectionError):
            svc.always_down()
    with pytest.raises(CircuitOpenError):
        svc.always_down()

    data["resilience"]["enabled"] = False
    container.refresh_config()

    with pytest.raises(ConnectionError):
        svc.always_down()


def test_unrelated_prefix_changes_are_ignored(make_container_with_source):
    container, data = make_container_with_source({"resilience": {"enabled": True}, "app": {"name": "x"}})
    settings = container.get(ResilienceSettings)
    data["app"]["name"] = "y"
    assert container.refresh_config() == frozenset({"app"})
    assert settings.enabled is True


def test_removing_the_block_falls_back_to_enabled(make_container_with_source):
    container, data = make_container_with_source({"resilience": {"enabled": False}})
    del data["resilience"]
    container.refresh_config()
    assert container.get(ResilienceSettings).enabled is True


def test_missing_eventbus_fails_fast():
    from pico_ioc import ConfigurationError, DictSource, configuration, init

    with pytest.raises(ConfigurationError, match="hot_reload"):
        init(modules=["pico_resilience"], config=configuration(DictSource({})))


def test_hot_reload_opt_out_allows_busless_containers():
    from pico_ioc import DictSource, configuration, init

    container = init(
        modules=["pico_resilience", sys.modules[__name__]],
        config=configuration(DictSource({"resilience": {"hot_reload": False}})),
    )
    svc = container.get(FragileService)
    assert svc.eventually_ok() == "ok"


def test_refresher_without_config_manager_is_inert():
    from pico_resilience import ResilienceSettings
    from pico_resilience.refresh import ResilienceConfigRefresher

    class BareContainer:
        _config_manager = None

    settings = ResilienceSettings(enabled=True)
    refresher = ResilienceConfigRefresher(BareContainer(), settings)
    refresher.on_config_changed(type("E", (), {"prefixes": frozenset({"resilience"})})())
    assert settings.enabled is True


def test_refresh_with_unchanged_value_is_noop(make_container_with_source):
    container, data = make_container_with_source({"resilience": {"enabled": True}})
    settings = container.get(ResilienceSettings)
    data["resilience"]["extra_future_key"] = 1
    container.refresh_config()
    assert settings.enabled is True
