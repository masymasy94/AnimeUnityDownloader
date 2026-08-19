import asyncio

import httpx
import pytest

from app.api.stream import RETRY_ATTEMPTS, _send_with_retry


class _FlakyClient:
    """Fails `failures` times with a ConnectError, then succeeds."""

    def __init__(self, failures: int):
        self.failures = failures
        self.calls = 0

    async def send(self, request, stream=False):
        self.calls += 1
        if self.calls <= self.failures:
            raise httpx.ConnectError("All connection attempts failed")
        return httpx.Response(200, request=request)


class _Resp:
    """Minimal upstream response — real streamed responses get aclose()d before a
    status-retry, so the fake needs an async aclose() too."""

    def __init__(self, status_code: int):
        self.status_code = status_code

    async def aclose(self):
        pass


class _Flaky503Client:
    """Answers 503 `failures` times, then 200 — the transient CDN blip on a seek."""

    def __init__(self, failures: int):
        self.failures = failures
        self.calls = 0

    async def send(self, request, stream=False):
        self.calls += 1
        return _Resp(503 if self.calls <= self.failures else 200)


def _request() -> httpx.Request:
    return httpx.Request("GET", "https://cdn.example/1080p.mp4")


def test_recovers_from_transient_connect_error():
    client = _FlakyClient(failures=RETRY_ATTEMPTS - 1)
    resp = asyncio.run(_send_with_retry(client, _request(), stream=True))
    assert resp.status_code == 200
    assert client.calls == RETRY_ATTEMPTS


def test_raises_when_upstream_stays_down():
    client = _FlakyClient(failures=RETRY_ATTEMPTS + 1)
    with pytest.raises(httpx.ConnectError):
        asyncio.run(_send_with_retry(client, _request(), stream=True))
    assert client.calls == RETRY_ATTEMPTS


def test_recovers_from_transient_503():
    client = _Flaky503Client(failures=RETRY_ATTEMPTS - 1)
    resp = asyncio.run(_send_with_retry(client, _request(), stream=True))
    assert resp.status_code == 200
    assert client.calls == RETRY_ATTEMPTS


def test_returns_final_503_when_upstream_stays_down():
    client = _Flaky503Client(failures=99)
    resp = asyncio.run(_send_with_retry(client, _request(), stream=True))
    assert resp.status_code == 503
    assert client.calls == RETRY_ATTEMPTS
