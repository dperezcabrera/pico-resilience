import pytest
from pico_ioc import DictSource, configuration, init


@pytest.fixture
def make_container():
    created = []

    def _make(module, enabled=True):
        cfg = configuration(DictSource({"resilience": {"enabled": enabled}}))
        c = init(modules=["pico_resilience", module], config=cfg)
        created.append(c)
        return c

    yield _make
    for c in created:
        c.shutdown()
