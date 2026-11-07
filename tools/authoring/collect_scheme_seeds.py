"""Record the official scheme documents behind the skeletons as seeds.

Each skeleton in ``tools/authoring/schemes/`` lists the official documents its rules were
verified against (``sources``: url, verified). This script downloads each one, stores the raw
file and its text under ``seeds_raw/schemes/`` (gitignored) and adds a provenance entry with
the rights basis to ``data/seeds/manifest.yaml``. ``pb tasks validate --seeds`` then checks
that no call, dossier or brief copies long passages from them.

    uv run python tools/authoring/collect_scheme_seeds.py            # all skeletons
    uv run python tools/authoring/collect_scheme_seeds.py erc_poc    # one skeleton
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
import yaml
from collect_call_seeds import EU_LICENCE, _strip_html

ROOT = Path(__file__).resolve().parents[2]
SCHEMES = Path(__file__).resolve().parent / "schemes"
RAW = ROOT / "seeds_raw" / "schemes"
MANIFEST = ROOT / "data" / "seeds" / "manifest.yaml"
US_PD = "Public domain: work of the US federal government (17 U.S.C. §105)"

# Rights basis by publisher host; a source on any other host is refused, not guessed.
RIGHTS = {
    "ec.europa.eu": ("European Commission", EU_LICENCE, "© European Union"),
    "erasmus-plus.ec.europa.eu": ("European Commission", EU_LICENCE, "© European Union"),
    "grants.nih.gov": ("National Institutes of Health", US_PD, "National Institutes of Health"),
    "www.nsf.gov": ("National Science Foundation", US_PD, "National Science Foundation"),
    "www.aei.gob.es": (
        "Agencia Estatal de Investigación",
        "Official act, excluded from copyright (Ley de Propiedad Intelectual, art. 13)",
        "Agencia Estatal de Investigación",
    ),
}


def seed_id(skeleton: str, url: str) -> str:
    stem = Path(unquote(urlparse(url).path.rstrip("/"))).name or urlparse(url).netloc
    stem = re.sub(r"[^A-Za-z0-9]+", "-", Path(stem).stem).strip("-").lower()[:60]
    return f"scheme:{skeleton}:{stem}"


def _prose(paragraph: str) -> bool:
    words = paragraph.split()
    return len(words) >= 3 and sum(len(w) >= 4 for w in words) >= 2


def to_text(raw: bytes, content_type: str) -> tuple[str, str]:
    """Plain text and a title from a downloaded PDF or HTML page."""
    if raw[:5] == b"%PDF-" or "pdf" in content_type:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_name = str(Path(tmp) / "source.pdf")
            Path(tmp_name).write_bytes(raw)
            text = subprocess.run(
                ["pdftotext", "-enc", "UTF-8", tmp_name, "-"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
            info = subprocess.run(["pdfinfo", tmp_name], capture_output=True, text=True).stdout
        title = re.search(r"^Title:[ \t]*(.*)$", info, re.M)
        if title and len(title.group(1).strip()) > 8:
            return text, title.group(1).strip()[:150]
        # Otherwise the first real paragraph: skip signature stamps ("... | C.S.V. : ...") and
        # watermark debris (one or two letters per line, e.g. "Example, not to be completed").
        paras = (" ".join(p.split()) for p in text.split("\n\n"))
        return text, next((p for p in paras if _prose(p) and "|" not in p), "")[:150]
    page = raw.decode("utf-8", errors="replace")
    title = re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S)
    page = re.sub(r"<(script|style|nav|header|footer)\b.*?</\1>", " ", page, flags=re.I | re.S)
    return _strip_html(page), _strip_html(title.group(1))[:150] if title else ""


def record(spec: dict, url: str, raw: bytes, text: str, title: str, via: str | None) -> dict:
    """Store the raw document and its text; return the manifest entry."""
    if len(text) < 1000:
        raise SystemExit(f"{url}: only {len(text)} characters of text")
    sid = seed_id(spec["name"], url)
    stem = sid.split(":", 2)[2]
    base = RAW / spec["name"]
    base.mkdir(parents=True, exist_ok=True)
    if via is None:
        ext = ".pdf" if raw[:5] == b"%PDF-" else ".html"
        (base / f"{stem}{ext}").write_bytes(raw)
    md = base / f"{stem}.md"
    md.write_text(f"# {title or stem}\n\nSource: {url}\n\n{text}\n", encoding="utf-8")
    funder, licence, holder = RIGHTS[urlparse(url).netloc]
    verified = next((s.get("verified") for s in spec["sources"] if s["url"] == url), "")
    entry = {
        "id": sid,
        "kind": "scheme_rules",
        "title": title or stem,
        "funder": funder,
        "programme": spec["scheme"],
        "url": url,
        "licence": licence,
        "attribution": f"{holder}; source: {urlparse(url).netloc}",
        "use": f"scheme rules of skeleton {spec['name']} (summarised and paraphrased)",
        "retrieved": datetime.now(UTC).date().isoformat(),
        "verified": str(verified),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "raw_path": str(md.relative_to(ROOT)),
    }
    if via:
        entry["retrieved_via"] = via
    print(f"{sid}  {len(text):>7} chars  {(title or stem)[:70]}")
    return entry


def collect(skeleton: Path, manifest: dict, client: httpx.Client) -> list[str]:
    """Add the skeleton's sources; return the URLs the publisher refused to serve."""
    spec = yaml.safe_load(skeleton.read_text(encoding="utf-8"))
    known = {s["id"] for s in manifest["seeds"]}
    recorded = {s["url"] for s in manifest["seeds"]}  # a document shared by two skeletons
    refused = []
    for src in spec.get("sources") or []:
        url = src["url"]
        if urlparse(url).netloc not in RIGHTS:
            raise SystemExit(f"{skeleton.name}: no rights basis recorded for {url}")
        if seed_id(spec["name"], url) in known or url in recorded:
            continue
        r = client.get(url)
        if r.status_code in (401, 403):
            refused.append(url)
            continue
        r.raise_for_status()
        text, title = to_text(r.content, r.headers.get("content-type", ""))
        manifest["seeds"].append(record(spec, url, r.content, text, title, None))
    return refused


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("skeletons", nargs="*", help="skeleton names (default: all)")
    ap.add_argument(
        "--from-file",
        nargs=3,
        metavar=("SKELETON", "URL", "FILE"),
        help="add a source the publisher refuses to serve to scripts, from text saved by a "
        "browser or reader service (recorded as such; the checksum is of that text)",
    )
    args = ap.parse_args()
    manifest = yaml.safe_load(MANIFEST.read_text()) if MANIFEST.exists() else {"seeds": []}
    if args.from_file:
        name, url, file = args.from_file
        spec = yaml.safe_load((SCHEMES / f"{name}.yaml").read_text(encoding="utf-8"))
        if url not in {s["url"] for s in spec.get("sources") or []}:
            raise SystemExit(f"{url} is not a source of skeleton {name}")
        sid = seed_id(name, url)
        manifest["seeds"] = [s for s in manifest["seeds"] if s["id"] != sid]
        raw = Path(file).read_bytes()
        text = raw.decode("utf-8")
        title = next((ln.lstrip("# ").strip() for ln in text.splitlines() if ln.strip()), "")
        manifest["seeds"].append(record(spec, url, raw, text, title, "reader service"))
        MANIFEST.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
        return
    paths = (
        [SCHEMES / f"{n}.yaml" for n in args.skeletons]
        if args.skeletons
        else sorted(SCHEMES.glob("*.yaml"))
    )
    # Some publishers refuse requests without a browser user agent.
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) ProposalBench-seeds/1.0"}
    refused = []
    with httpx.Client(follow_redirects=True, timeout=120, headers=headers) as client:
        for path in paths:
            refused += [(path.stem, u) for u in collect(path, manifest, client)]
            MANIFEST.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
    for name, url in refused:
        print(f"refused by the publisher, add with --from-file {name} {url} FILE")


if __name__ == "__main__":
    main()
