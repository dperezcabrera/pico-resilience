import pytest
from pico_ioc import DictSource, configuration, init


@pytest.fixture
def make_container(make_container):
    """Extends the plugin fixture: resilience toggle shortcut plus the EventBus module."""
    plugin_make = make_container

    def _make(module, enabled=True):
        return plugin_make("pico_ioc.event_bus", module, config={"resilience": {"enabled": enabled}})

    return _make


@pytest.fixture
def make_container_with_source(request):
    created = []

    def _make(data):
        cfg = configuration(DictSource(data))
        c = init(modules=["pico_resilience", "pico_ioc.event_bus", request.module], config=cfg)
        created.append(c)
        return c, data

    yield _make
    for c in reversed(created):
        c.shutdown()
