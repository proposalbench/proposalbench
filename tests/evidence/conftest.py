from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).parents[1] / "fixtures" / "evidence"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if os.getenv("PB_NETWORK_TESTS") != "1":
        for item in items:
            if item.get_closest_marker("network"):
                item.add_marker(pytest.mark.skip(reason="Set PB_NETWORK_TESTS=1 for live tests"))


class FixtureClient:
    """Replay by URL with explicit search fixtures; unregistered calls never hit the network."""

    def __init__(self, routes: dict[str, str | tuple[int, object] | Exception]) -> None:
        self.routes = routes
        self.calls: list[dict] = []
        self.manifest = json.loads((ROOT / "manifest.json").read_text())

    def request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        self.calls.append({"method": method, "url": url, **kwargs})
        value = self.routes.get(url)
        if value is None:
            raise httpx.ConnectError("Unregistered offline fixture")
        if isinstance(value, Exception):
            raise value
        if isinstance(value, str):
            meta = self.manifest[value]
            return httpx.Response(
                meta["status"],
                content=(ROOT / meta["file"]).read_bytes(),
                headers={"content-type": meta["content_type"]},
                request=httpx.Request(method, meta.get("response_url", url)),
            )
        status, body = value
        return httpx.Response(status, json=body, request=httpx.Request(method, url))


@pytest.fixture
def fixture_client():
    return FixtureClient


@pytest.fixture(autouse=True)
def block_unmarked_network(request, monkeypatch):
    if not request.node.get_closest_marker("network"):

        def blocked(*args, **kwargs):
            pytest.fail("Unmarked evidence test attempted a live HTTP request")

        monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked)
