"""Run synthesize.py over many units in parallel, a few at a time per author family.

    uv run python tools/authoring/batch.py call --matrix v2
    uv run python tools/authoring/batch.py dossier --matrix v2 --skip-existing
    uv run python tools/authoring/batch.py review task --matrix v2
    uv run python tools/authoring/batch.py revise dossier --matrix v2
    uv run python tools/authoring/batch.py revise dossier --issues-dir tools/authoring/reviews/deep

Each unit runs as its own process (a failure stops only that unit); its output goes to
``.work/authoring/<action>-<kind>-<id>.log``. A summary of failures is printed at the end.
Families run side by side, so per-family concurrency is the load on each provider.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LOGS = ROOT / ".work" / "authoring"
REVIEWER = {"anthropic": "google", "google": "openai", "openai": "anthropic"}
OUT = ROOT / "data" / "public"


def units(kind: str, m: dict) -> list[tuple[str, str]]:
    """(unit id, family that does the work for a generation step) in matrix order."""
    dossier_family = {d["id"]: d["author"] for d in m["dossiers"]}
    if kind == "call":
        return [(c["id"], c["author"]) for c in m["calls"]]
    if kind == "dossier":
        return [(d["id"], d["author"]) for d in m["dossiers"]]
    return [(t["id"], dossier_family[t["dossier"]]) for t in m["tasks"]]


def run(action: str, kind: str, uid: str, issues_dir: Path | None = None) -> tuple[str, int]:
    args = [action, uid] if action in ("call", "dossier", "task") else [action, kind, uid]
    if issues_dir is not None:
        args += ["--issues", str(issues_dir / f"{kind}-{uid}.json")]
    log = LOGS / f"{action}-{kind}-{uid}.log"
    with log.open("w", encoding="utf-8") as fh:
        code = subprocess.call(
            [sys.executable, str(HERE / "synthesize.py"), *args],
            stdout=fh,
            stderr=subprocess.STDOUT,
            cwd=ROOT,
        )
    print(f"{'ok ' if code == 0 else 'FAIL'} {action} {kind} {uid}", flush=True)
    return uid, code


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["call", "dossier", "task", "review", "revise"])
    ap.add_argument("kind", nargs="?", choices=["call", "dossier", "task"])
    ap.add_argument("--matrix", default="v2", choices=["v1", "v2"])
    ap.add_argument("--per-family", type=int, default=3)
    ap.add_argument("--only", nargs="*", help="unit ids to run (default: all of the kind)")
    ap.add_argument("--skip-existing", action="store_true", help="skip units already written")
    ap.add_argument(
        "--issues-dir",
        type=Path,
        help="revise: take each unit's issues from <dir>/<kind>-<id>.json, and run only the "
        "units whose file there has a blocker or major issue",
    )
    ns = ap.parse_args()
    kind = ns.kind or ns.action
    name = "public_matrix.yaml" if ns.matrix == "v1" else "public_matrix_v2.yaml"
    m = yaml.safe_load((HERE / name).read_text(encoding="utf-8"))
    todo = [(u, f) for u, f in units(kind, m) if not ns.only or u in ns.only]
    if ns.skip_existing and ns.action in ("call", "dossier", "task"):
        todo = [(u, f) for u, f in todo if not (OUT / f"{kind}s" / u / f"{kind}.yaml").is_file()]
    if ns.issues_dir is not None:
        if ns.action != "revise":
            ap.error("--issues-dir applies to revise only")

        def actionable(uid: str) -> bool:
            path = ns.issues_dir / f"{kind}-{uid}.json"
            if not path.is_file():
                return False
            issues = json.loads(path.read_text(encoding="utf-8")).get("issues", [])
            return any(i.get("severity") in ("blocker", "major") for i in issues)

        todo = [(u, f) for u, f in todo if actionable(u)]
    if ns.action == "review":  # the reviewer is the next family, so the load moves with it
        todo = [(u, REVIEWER[f]) for u, f in todo]
    LOGS.mkdir(parents=True, exist_ok=True)
    by_family: dict[str, list[str]] = {}
    for uid, fam in todo:
        by_family.setdefault(fam, []).append(uid)
    pools = {f: ThreadPoolExecutor(max_workers=ns.per_family) for f in by_family}
    futures = [
        pools[f].submit(run, ns.action, kind, uid, ns.issues_dir)
        for f, ids in by_family.items()
        for uid in ids
    ]
    failed = [uid for uid, code in (fut.result() for fut in futures) if code != 0]
    for pool in pools.values():
        pool.shutdown()
    print(f"{len(todo) - len(failed)}/{len(todo)} ok" + (f"; failed: {failed}" if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
