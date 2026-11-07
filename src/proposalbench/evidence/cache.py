from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SECRET_NAMES = {"apikey", "mailto", "xapikey", "authorization", "access_token", "token"}
SELECTED_HEADERS = {"content-type", "etag", "last-modified", "retry-after"}


def _secret(name: str) -> bool:
    return name.casefold().replace("_", "").replace("-", "") in {
        x.replace("_", "") for x in SECRET_NAMES
    }


def sanitize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: sanitize(v) for k, v in value.items() if not _secret(str(k))}
    if isinstance(value, (list, tuple)):
        return [sanitize(v) for v in value]
    return value


def safe_url(url: str) -> str:
    parts = urlsplit(url)
    host = parts.netloc.rsplit("@", 1)[-1]
    query = urlencode(sorted((k, v) for k, v in parse_qsl(parts.query) if not _secret(k)))
    return urlunsplit((parts.scheme, host, parts.path, query, ""))


def cache_key(
    method: str, url: str, params: Mapping[str, Any] | None = None, body: Any = None
) -> str:
    parts = urlsplit(safe_url(url))
    query = list(parse_qsl(parts.query))
    for k, v in sanitize(params or {}).items():
        query.extend((k, str(item)) for item in (v if isinstance(v, (list, tuple)) else [v]))
    if isinstance(body, bytes):
        try:
            body = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            body = body.hex()
    canonical = [
        method.upper(),
        urlunsplit(parts._replace(query="")),
        sorted(query),
        sanitize(body),
    ]
    return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class CachedResponse:
    status: int
    headers: dict[str, str]
    body: bytes
    source: str
    fetched_at: str
    response_url: str | None = None


class EvidenceCache:
    def __init__(self, path: str | Path) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._lock = threading.RLock()
        with self._db:
            self._db.execute("""CREATE TABLE IF NOT EXISTS evidence (
                key TEXT PRIMARY KEY, url TEXT NOT NULL, status INTEGER NOT NULL,
                headers TEXT NOT NULL, body BLOB NOT NULL, source TEXT NOT NULL,
                fetched_at TEXT NOT NULL, response_url TEXT)""")

    def get(self, key: str) -> CachedResponse | None:
        with self._lock:
            row = self._db.execute(
                "SELECT status, headers, body, source, fetched_at, response_url "
                "FROM evidence WHERE key = ?",
                (key,),
            ).fetchone()
        return (
            CachedResponse(row[0], json.loads(row[1]), row[2], row[3], row[4], row[5])
            if row
            else None
        )

    def put(
        self,
        key: str,
        *,
        url: str,
        status: int,
        headers: Mapping[str, str],
        body: bytes,
        source: str,
        response_url: str | None = None,
    ) -> None:
        selected = {k.lower(): v for k, v in headers.items() if k.lower() in SELECTED_HEADERS}
        with self._lock, self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    key,
                    safe_url(url),
                    status,
                    json.dumps(selected),
                    body,
                    source,
                    datetime.now(UTC).isoformat(),
                    safe_url(response_url) if response_url else None,
                ),
            )

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> EvidenceCache:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
