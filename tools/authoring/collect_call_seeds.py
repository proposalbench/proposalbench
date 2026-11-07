"""Collect EU Funding & Tenders topics as call seeds.

Queries the public SEDIA search API (the portal's own backend; the key is the public literal
``SEDIA``), stores each topic's text under ``seeds_raw/calls/`` (gitignored) and appends a
provenance entry to ``data/seeds/manifest.yaml``. EU call texts are reusable under
Commission Decision 2011/833/EU (CC BY 4.0).

    uv run python tools/authoring/collect_call_seeds.py --text "soil health" --prefix HORIZON-CL6
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import UTC, datetime
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "seeds_raw" / "calls"
MANIFEST = ROOT / "data" / "seeds" / "manifest.yaml"
SEARCH_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
TOPIC_URL = "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/{}"
EU_LICENCE = "CC-BY-4.0 (Commission Decision 2011/833/EU)"


def _meta(md: dict, key: str) -> str | None:
    v = md.get(key)
    if isinstance(v, list):
        v = v[0] if v else None
    return str(v) if v is not None else None


def _strip_html(raw: str) -> str:
    text = re.sub(r"<\s*(br|/p|/li|/h\d)\s*/?>", "\n", raw, flags=re.I)
    text = re.sub(r"<li[^>]*>", "\n- ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def search(text: str, statuses: list[str], page_size: int = 50) -> list[dict]:
    params = {"apiKey": "SEDIA", "text": text, "pageSize": str(page_size), "pageNumber": "1"}
    query = {"bool": {"must": [{"terms": {"type": ["1", "2"]}}, {"terms": {"status": statuses}}]}}
    files = {
        "query": (None, json.dumps(query), "application/json"),
        "languages": (None, '["en"]', "application/json"),
    }
    r = httpx.post(SEARCH_URL, params=params, files=files, timeout=60)
    r.raise_for_status()
    return r.json().get("results", [])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--prefix", default="", help="keep identifiers starting with this")
    ap.add_argument(
        "--status",
        nargs="+",
        default=["31094501", "31094502", "31094503"],
        help="SEDIA status codes: forthcoming, open, closed",
    )
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    manifest = yaml.safe_load(MANIFEST.read_text()) if MANIFEST.exists() else {"seeds": []}
    known = {s["id"] for s in manifest["seeds"]}
    added = 0
    for res in search(args.text, args.status):
        md = res.get("metadata", {})
        ident = _meta(md, "identifier")
        if not ident or not ident.startswith(args.prefix) or f"sedia:{ident}" in known:
            continue
        body = _strip_html(_meta(md, "descriptionByte") or "")
        if len(body) < 1500:
            continue
        title = _meta(md, "title") or ident
        text = f"# {ident}: {title}\n\n{body}\n"
        path = RAW / f"{ident}.md"
        path.write_text(text, encoding="utf-8")
        manifest["seeds"].append(
            {
                "id": f"sedia:{ident}",
                "kind": "call",
                "title": title,
                "funder": "European Commission",
                "programme": ident.split("-")[0],
                "url": TOPIC_URL.format(ident.lower()),
                "licence": EU_LICENCE,
                "attribution": "© European Union; source: EU Funding & Tenders Portal",
                "use": "structure and topic inspiration for a synthetic call",
                "retrieved": datetime.now(UTC).date().isoformat(),
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "raw_path": str(path.relative_to(ROOT)),
            }
        )
        added += 1
        print(f"{ident}  {len(body):>6} chars  {title[:80]}")
        if added >= args.limit:
            break
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
    print(f"added {added} seeds -> {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
