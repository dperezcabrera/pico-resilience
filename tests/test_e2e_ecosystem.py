"""E2E: resilience + fastapi + httpx + caching in one container, with hot
config reload flipping resilience live.

The upstream is a real pico-fastapi controller served in-process via
httpx.ASGITransport; the caller is a declarative pico-httpx client with
@retryable stacked on the stub; @cacheable memoizes the recovered result.
"""

import asyncio
import sys

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from pico_caching import cacheable
from pico_fastapi import controller
from pico_fastapi import get as route_get
from pico_httpx import get, http_client
from pico_ioc import DictSource, component, configuration, init

from pico_resilience import ResilienceSettings, retryable


@component
class FlakyUpstream:
    def __init__(self):
        self.hits = 0
        self.fail_next = 0

    def serve(self) -> dict:
        self.hits += 1
        if self.fail_next > 0:
            self.fail_next -= 1
            raise HTTPException(status_code=503, detail="upstream down")
        return {"status": "ok", "hits": self.hits}


@controller(prefix="/upstream")
class UpstreamController:
    def __init__(self, upstream: FlakyUpstream):
        self._upstream = upstream

    @route_get("/data")
    async def data(self):
        return self._upstream.serve()


@http_client(base_url="http://e2e.test")
class UpstreamClient:
    @retryable(max_attempts=3, backoff_seconds=0.01, retry_on=(httpx.HTTPError,))
    @get("/upstream/data")
    async def fetch(self) -> dict: ...


@component
class ReportService:
    def __init__(self, client: UpstreamClient):
        self._client = client

    @cacheable(ttl_seconds=60)
    def report(self, day: str) -> dict:
        return asyncio.run(self._client.fetch())


@pytest.fixture
def e2e():
    data = {
        "resilience": {"enabled": True},
        "fastapi": {"title": "e2e", "version": "0.0.1"},
        "caching": {"enabled": True},
    }
    container = init(
        modules=[
            "pico_resilience",
            "pico_fastapi",
            "pico_httpx",
            "pico_caching",
            "pico_ioc.event_bus",
            sys.modules[__name__],
        ],
        config=configuration(DictSource(data)),
    )
    app = container.get(FastAPI)
    client = container.get(UpstreamClient)
    client.__dict__["_pico_httpx_aclient"] = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://e2e.test"
    )
    yield container, data
    container.shutdown()


def test_retry_recovers_from_flaky_upstream(e2e):
    container, _ = e2e
    upstream = container.get(FlakyUpstream)
    upstream.fail_next = 2

    result = asyncio.run(container.get(UpstreamClient).fetch())
    assert result["status"] == "ok"
    assert upstream.hits == 3


def test_hot_disable_turns_retries_off_live(e2e):
    container, data = e2e
    upstream = container.get(FlakyUpstream)
    client = container.get(UpstreamClient)

    data["resilience"]["enabled"] = False
    assert container.refresh_config() == frozenset({"resilience"})
    assert container.get(ResilienceSettings).enabled is False

    upstream.fail_next = 2
    hits_before = upstream.hits
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(client.fetch())
    assert upstream.hits == hits_before + 1

    data["resilience"]["enabled"] = True
    container.refresh_config()
    assert asyncio.run(client.fetch())["status"] == "ok"


def test_cacheable_memoizes_the_recovered_result(e2e):
    container, _ = e2e
    upstream = container.get(FlakyUpstream)
    service = container.get(ReportService)
    upstream.fail_next = 2

    first = service.report("2026-07-10")
    assert first["status"] == "ok"
    hits_after_first = upstream.hits

    second = service.report("2026-07-10")
    assert second == first
    assert upstream.hits == hits_after_first
