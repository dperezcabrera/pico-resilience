import pytest
from pico_ioc import DictSource, configuration, init


@pytest.fixture
def make_container():
    created = []

    def _make(module, enabled=True):
        cfg = configuration(DictSource({"resilience": {"enabled": enabled}}))
        c = init(modules=["pico_resilience", "pico_ioc.event_bus", module], config=cfg)
        created.append(c)
        return c

    yield _make
    for c in created:
        c.shutdown()


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
