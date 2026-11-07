from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from proposalbench.evidence.cache import EvidenceCache, cache_key, safe_url
from proposalbench.evidence.http import (
    USER_AGENT,
    EvidenceClient,
    OfflineCacheMiss,
    SourceExhausted,
)


@pytest.fixture(autouse=True)
def no_dotenv(monkeypatch):
    monkeypatch.setattr("proposalbench.evidence.http.load_dotenv", lambda: None)
    for name in ("CROSSREF_MAILTO", "OPENALEX_API_KEY", "SEMANTIC_SCHOLAR_API_KEY", "EXA_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def test_cache_hit_offline_and_privacy(tmp_path):
    path = tmp_path / "cache.sqlite"
    target = "https://api.example.org/works?apiKey=hidden&mailto=private&z=2"
    with EvidenceCache(path) as cache:
        calls = []

        def serve(request):
            calls.append(request)
            return httpx.Response(
                200,
                json={"title": "Public record"},
                headers={"content-type": "application/json", "set-cookie": "sensitive_cookie"},
            )

        with EvidenceClient(cache, transport=httpx.MockTransport(serve)) as client:
            one = client.request(
                "GET",
                target,
                params={"api_key": "another_secret"},
                headers={"x-api-key": "header_secret"},
                source="test",
            )
            two = client.request("GET", target, params={"api_key": "changed_secret"}, source="test")
            assert one.json() == two.json() and len(calls) == 1
            assert calls[0].headers["User-Agent"] == USER_AGENT
        with EvidenceClient(cache, offline=True) as offline:
            assert offline.request("GET", target, source="test").json() == one.json()
            with pytest.raises(OfflineCacheMiss):
                offline.request("GET", "https://example.org/miss?api_key=hidden", source="test")
        stored = cache.get(cache_key("GET", target))
        assert stored.source == "test" and stored.fetched_at.endswith("+00:00")
        assert "set-cookie" not in stored.headers
    contents = path.read_bytes()
    for secret in (b"hidden", b"private", b"another_secret", b"header_secret", b"sensitive_cookie"):
        assert secret not in contents


def test_canonical_keys():
    one = cache_key(
        "get",
        "https://example.org/?apiKey=hidden&a=1",
        {"b": 2, "mailto": "private"},
        {"z": 1, "api_key": "secret"},
    )
    two = cache_key("GET", "https://example.org/", {"b": 2, "a": 1}, {"z": 1})
    assert one == two
    assert cache_key("POST", "https://example.org/", body={"x": 1}) != two
    assert safe_url("https://user:password@example.org/?api_key=secret&q=ok#secret") == (
        "https://example.org/?q=ok"
    )


@pytest.mark.parametrize("kind", ["timeout", "429", "503"])
def test_retry_logging_and_no_transient_cache(kind):
    calls, sleeps = [], []

    def serve(request):
        calls.append(request)
        if len(calls) < 4:
            if kind == "timeout":
                raise httpx.ReadTimeout("secret response must not be logged", request=request)
            return httpx.Response(int(kind), headers={"Retry-After": "2"})
        return httpx.Response(200, json={"ok": True})

    with (
        EvidenceCache(":memory:") as cache,
        EvidenceClient(cache, transport=httpx.MockTransport(serve), sleep=sleeps.append) as client,
    ):
        response = client.request("GET", "https://example.org/?api_key=secret", source="test")
        assert response.status_code == 200 and len(calls) == 4
        assert len(client.events) == 3
        assert [e["attempt"] for e in client.events] == [1, 2, 3]
        assert "secret" not in json.dumps(client.events)
        assert client.events[2]["delay"] == 4


def test_retry_exhaustion_is_not_cached():
    with (
        EvidenceCache(":memory:") as cache,
        EvidenceClient(
            cache,
            transport=httpx.MockTransport(lambda req: httpx.Response(503)),
            sleep=lambda _: None,
        ) as client,
    ):
        with pytest.raises(httpx.HTTPStatusError):
            client.request("GET", "https://example.org/", source="test")
        assert len(client.events) == 3
        assert cache.get(cache_key("GET", "https://example.org/")) is None


@pytest.mark.parametrize(
    "host,env,param,header,interval",
    [
        ("api.crossref.org", "CROSSREF_MAILTO", "mailto", None, 1 / 3),
        ("api.openalex.org", "OPENALEX_API_KEY", "api_key", None, 0.1),
        ("api.semanticscholar.org", "SEMANTIC_SCHOLAR_API_KEY", None, "x-api-key", 1),
        ("api.exa.ai", "EXA_API_KEY", None, "x-api-key", 0.2),
        ("export.arxiv.org", None, None, None, 3),
        ("doi.org", None, None, None, 0.2),
        ("api.crossref.org", None, None, None, 1.0),
    ],
)
def test_credentials_and_host_rate(monkeypatch, host, env, param, header, interval):
    if env:
        monkeypatch.setenv(env, "test_secret")
    calls, sleeps = [], []

    def serve(request):
        calls.append(request)
        return httpx.Response(200)

    with (
        EvidenceCache(":memory:") as cache,
        EvidenceClient(
            cache, transport=httpx.MockTransport(serve), sleep=sleeps.append, clock=lambda: 0
        ) as client,
    ):
        for index in range(2):
            client.request("GET", f"https://{host}/{index}", source="test")
        if param:
            assert calls[0].url.params[param] == "test_secret"
        if header:
            assert calls[0].headers[header] == "test_secret"
        assert sleeps == [pytest.approx(interval)]


def test_redirect_credentials_and_cached_final_url(monkeypatch):
    monkeypatch.setenv("EXA_API_KEY", "secret")
    calls = []

    def serve(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(302, headers={"location": "https://other.example.org/final"})
        assert "x-api-key" not in request.headers
        return httpx.Response(200, text="<title>Final page</title>")

    with (
        EvidenceCache(":memory:") as cache,
        EvidenceClient(cache, transport=httpx.MockTransport(serve), sleep=lambda _: None) as client,
    ):
        one = client.request("GET", "https://api.exa.ai/start", source="test")
        two = client.request("GET", "https://api.exa.ai/start", source="test")
        assert str(one.url) == str(two.url) == "https://other.example.org/final"
        assert len(calls) == 2


def test_thread_safe_host_slots():
    sleeps = []
    with (
        EvidenceCache(":memory:") as cache,
        EvidenceClient(
            cache,
            transport=httpx.MockTransport(lambda req: httpx.Response(200)),
            sleep=sleeps.append,
            clock=lambda: 0,
        ) as client,
        ThreadPoolExecutor(max_workers=4) as pool,
    ):
        list(
            pool.map(
                lambda i: client.request("GET", f"https://example.org/{i}", source="test"), range(8)
            )
        )
    assert sorted(sleeps) == pytest.approx([0.2 * i for i in range(1, 8)])


@pytest.mark.network
def test_live_doi():
    from proposalbench.evidence.resolvers.doi import resolve_doi

    with EvidenceCache(":memory:") as cache, EvidenceClient(cache) as client:
        records = resolve_doi("10.1126/sciadv.adt3813", client)
        assert records[0].doi == "10.1126/sciadv.adt3813"


def test_url_query_is_sent_to_service():
    def serve(request):
        assert request.url.params["existing"] == "yes"
        assert request.url.params["added"] == "also"
        return httpx.Response(200)

    with (
        EvidenceCache(":memory:") as cache,
        EvidenceClient(cache, transport=httpx.MockTransport(serve)) as client,
    ):
        client.request(
            "GET", "https://example.org/?existing=yes", params={"added": "also"}, source="test"
        )


def test_redirect_preserves_post_for_307():
    calls = []

    def serve(request):
        calls.append(request)
        assert request.method == "POST"
        assert json.loads(request.content) == {"query": "test"}
        return (
            httpx.Response(307, headers={"location": "/final"})
            if len(calls) == 1
            else (httpx.Response(200))
        )

    with (
        EvidenceCache(":memory:") as cache,
        EvidenceClient(cache, transport=httpx.MockTransport(serve), sleep=lambda _: None) as client,
    ):
        client.request("POST", "https://example.org/", json={"query": "test"}, source="test")
        assert len(calls) == 2


def test_long_retry_after_marks_host_exhausted():
    calls, sleeps = [], []

    def serve(request):
        calls.append(request)
        return httpx.Response(429, headers={"Retry-After": "76412"})

    with (
        EvidenceCache(":memory:") as cache,
        EvidenceClient(cache, transport=httpx.MockTransport(serve), sleep=sleeps.append) as client,
    ):
        with pytest.raises(SourceExhausted):
            client.request("GET", "https://api.crossref.org/works", source="crossref")
        with pytest.raises(SourceExhausted):
            client.request("GET", "https://api.crossref.org/works?q=2", source="crossref")
        assert len(calls) == 1 and sleeps == []
        assert client.events[0]["delay"] == 76412


def test_openalex_disabled_without_key(monkeypatch):
    monkeypatch.setattr("proposalbench.evidence.http.load_dotenv", lambda: None)
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    with (
        EvidenceCache(":memory:") as cache,
        EvidenceClient(
            cache, transport=httpx.MockTransport(lambda r: httpx.Response(200))
        ) as client,
        pytest.raises(SourceExhausted),
    ):
        client.request("GET", "https://api.openalex.org/works", source="openalex")


def test_clients_share_host_schedule():
    sleeps = []

    def serve(request):
        return httpx.Response(200)

    with EvidenceCache(":memory:") as cache:
        first = EvidenceClient(cache, transport=httpx.MockTransport(serve), sleep=sleeps.append)
        second = EvidenceClient(cache, transport=httpx.MockTransport(serve), sleep=sleeps.append)
        first.request("GET", "https://doi.org/shared-1", source="test")
        second.request("GET", "https://doi.org/shared-2", source="test")
        first.close()
        second.close()
    # The second client waits for the slot the first one took on the same host.
    assert sleeps and 0 < sleeps[-1] <= 0.2
