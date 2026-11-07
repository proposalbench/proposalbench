from __future__ import annotations

import contextlib
import os
import threading
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv

from proposalbench.evidence.cache import EvidenceCache, cache_key, safe_url

USER_AGENT = "ProposalBench/0.1 (+https://github.com/proposalbench)"
# A server asking to wait longer than this (a spent daily quota, say) makes its host unavailable
# for the rest of the run instead of stalling every worker.
MAX_RETRY_AFTER_S = 60.0


# Host schedules are shared by every client in the process that uses the real clock: parallel
# evaluations each create a client, and per-client limits multiplied the request rate until
# Crossref answered 429 and references went unverified. Clients with an injected clock
# (tests) keep a private schedule.
_SHARED_SCHEDULE: tuple[threading.Lock, dict[str, float]] = (threading.Lock(), {})
_CONCURRENCY = {"api.crossref.org": threading.BoundedSemaphore(1)}


def _crossref_slots() -> threading.BoundedSemaphore:
    """Crossref also caps simultaneous requests (3 in the polite pool, 1 in the public one)."""
    want = 3 if os.getenv("CROSSREF_MAILTO") else 1
    if getattr(_CONCURRENCY["api.crossref.org"], "_initial_value", None) != want:
        _CONCURRENCY["api.crossref.org"] = threading.BoundedSemaphore(want)
    return _CONCURRENCY["api.crossref.org"]


def _schedule(clock: Callable[[], float]) -> tuple[threading.Lock, dict[str, float]]:
    return _SHARED_SCHEDULE if clock is time.monotonic else (threading.Lock(), {})


class OfflineCacheMiss(LookupError):
    pass


class SourceExhausted(httpx.HTTPError):
    """The host asked for a wait beyond MAX_RETRY_AFTER_S earlier in this run."""


class EvidenceClient:
    """Synchronous, thread-safe host scheduling; use asyncio.to_thread in async callers.

    Each instance represents a run. Retry events contain sanitized URLs and exception
    types only. Transient error responses are never cached.
    """

    def __init__(
        self,
        cache: EvidenceCache,
        *,
        offline: bool = False,
        transport: httpx.BaseTransport | None = None,
        retries: int = 3,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        disabled: dict[str, str] | None = None,
    ) -> None:
        load_dotenv()
        self.cache, self.offline = cache, offline
        self.events: list[dict[str, Any]] = []
        self.retries = min(3, max(0, retries))
        self._sleep, self._clock = sleep, clock
        self._lock = threading.Lock()
        self._slot_lock, self._next = _schedule(clock)
        self._exhausted: dict[str, str] = {}
        # Keyless OpenAlex has a small daily quota that runs out mid-run, which would make the
        # source set depend on run order; without a key it is off for the whole run.
        if not os.getenv("OPENALEX_API_KEY"):
            self._exhausted["api.openalex.org"] = "disabled: no OPENALEX_API_KEY"
        # Hosts a caller chooses not to use (reported like any unavailable source).
        self._exhausted.update(disabled or {})
        self._http = httpx.Client(
            transport=transport,
            timeout=20,
            follow_redirects=False,
            headers={"User-Agent": USER_AGENT},
        )

    def _wait(self, host: str, rate: float) -> None:
        with self._slot_lock:
            now = self._clock()
            slot = max(now, self._next.get(host, now))
            self._next[host] = slot + 1 / rate
        if slot > now:
            self._sleep(slot - now)

    def _credentials(self, url: str, params: dict, headers: dict) -> float:
        host = urlsplit(url).hostname
        if host == "api.crossref.org":
            # Crossref's advertised limits (x-rate-limit-limit, x-concurrency-limit, 2026-10-31):
            # polite pool 3 requests/s and 3 at a time, public pool 1 and 1.
            if mailto := os.getenv("CROSSREF_MAILTO"):
                params.setdefault("mailto", mailto)
                return 3
            return 1
        if host == "api.openalex.org":
            if key := os.getenv("OPENALEX_API_KEY"):
                params.setdefault("api_key", key)
            return 10
        if host == "api.semanticscholar.org":
            if key := os.getenv("SEMANTIC_SCHOLAR_API_KEY"):
                headers.setdefault("x-api-key", key)
            return 1
        if host in {"export.arxiv.org", "arxiv.org"}:
            return 1 / 3
        if host == "api.exa.ai" and (key := os.getenv("EXA_API_KEY")):
            headers.setdefault("x-api-key", key)
        return 5

    def request(
        self,
        method: str,
        url: str,
        *,
        source: str,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
        timeout: float = 20,
        follow_redirects: bool = True,
        retries: int | None = None,
    ) -> httpx.Response:
        host = urlsplit(url).hostname or ""
        if reason := self._exhausted.get(host):
            raise SourceExhausted(f"{host}: {reason}")
        key = cache_key(method, url, params, json)
        if cached := self.cache.get(key):
            return httpx.Response(
                cached.status,
                headers=cached.headers,
                content=cached.body,
                request=httpx.Request(method, cached.response_url or safe_url(url)),
            )
        if self.offline:
            raise OfflineCacheMiss(f"{method.upper()} {safe_url(url)}")
        original_url = url
        request_params, request_headers = dict(params or {}), dict(headers or {})
        rate = self._credentials(url, request_params, request_headers)
        request_params = httpx.QueryParams(urlsplit(url).query).merge(request_params)
        max_retries = self.retries if retries is None else retries
        for attempt in range(max_retries + 1):
            response = None
            reason = None
            try:
                self._wait(urlsplit(url).hostname or "", rate)
                gate = _crossref_slots() if host == "api.crossref.org" else contextlib.nullcontext()
                with gate:
                    response = self._http.request(
                        method,
                        url,
                        params=request_params,
                        json=json,
                        headers=request_headers,
                        timeout=timeout,
                    )
                redirects = 0
                redirect_method, redirect_body = method.upper(), json
                while follow_redirects and response.has_redirect_location:
                    redirects += 1
                    if redirects > 10:
                        raise httpx.TooManyRedirects("Too many redirects", request=response.request)
                    target = str(response.url.join(response.headers["location"]))
                    # Never forward service credentials to a redirect destination.
                    redirect_headers = {
                        k: v
                        for k, v in request_headers.items()
                        if k.lower() not in {"x-api-key", "authorization", "cookie"}
                    }
                    redirect_rate = self._credentials(target, {}, {})
                    self._wait(urlsplit(target).hostname or "", redirect_rate)
                    if response.status_code == 303 or (
                        response.status_code in {301, 302} and redirect_method == "POST"
                    ):
                        redirect_method, redirect_body = "GET", None
                    response = self._http.request(
                        redirect_method,
                        target,
                        json=redirect_body,
                        headers=redirect_headers,
                        timeout=timeout,
                    )
                if response.status_code == 429 or response.status_code >= 500:
                    reason = f"http_{response.status_code}"
                else:
                    self.cache.put(
                        key,
                        url=original_url,
                        status=response.status_code,
                        headers=response.headers,
                        body=response.content,
                        source=source,
                        response_url=str(response.url),
                    )
                    return response
            except httpx.TransportError as exc:
                reason = type(exc).__name__
                if attempt == max_retries:
                    raise
            if attempt == max_retries:
                assert response is not None
                response.raise_for_status()
            delay = float(2**attempt)
            if response is not None and (retry_after := response.headers.get("retry-after")):
                try:
                    delay = max(delay, float(retry_after))
                except ValueError:
                    with contextlib.suppress(ValueError, TypeError, OverflowError):
                        delay = max(
                            delay,
                            (
                                parsedate_to_datetime(retry_after) - datetime.now(UTC)
                            ).total_seconds(),
                        )
            self.events.append(
                {
                    "source": source,
                    "url": safe_url(original_url),
                    "attempt": attempt + 1,
                    "reason": reason,
                    "delay": delay,
                    "at": datetime.now(UTC).isoformat(),
                }
            )
            if delay > MAX_RETRY_AFTER_S:
                with self._lock:
                    self._exhausted[host] = f"{reason}, retry-after {delay:.0f}s"
                raise SourceExhausted(f"{host}: {self._exhausted[host]}")
            self._sleep(delay)
        raise RuntimeError("unreachable")

    @property
    def unavailable_sources(self) -> dict[str, str]:
        """Hosts skipped for (part of) this run, with the reason."""
        with self._lock:
            return dict(self._exhausted)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> EvidenceClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
