"""Run Proposia's Pro v2 core on one task (development harness for the redesign).

Executed with Proposia's interpreter inside a Proposia checkout:

    <checkout>/.venv/bin/python driver_v2.py --prp prp.md --cfp call.md --notes notes.md \
        --work <dir> --out result.json

Same inputs as the web app (one prior-research file, the call, the notes). Database variables
are blanked (``db_guard.py``); intermediate artefacts are kept in ``--work``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db_guard import check_db_env, isolate_db_env


def main() -> None:
    ap = argparse.ArgumentParser()
    for name in ("prp", "cfp", "notes", "work", "out"):
        ap.add_argument(f"--{name}", required=True)
    args = ap.parse_args()
    root = Path.cwd()
    from dotenv import load_dotenv

    load_dotenv(root / ".env", override=True)
    isolate_db_env(os.environ)
    sys.path.insert(0, str(root))
    from backend.workflow.pro_v2.pipeline import Settings, run_core

    check_db_env(os.environ)
    start = time.monotonic()
    res = run_core(
        [("prior_research.md", Path(args.prp).read_text(encoding="utf-8"))],
        Path(args.cfp).read_text(encoding="utf-8"),
        Path(args.notes).read_text(encoding="utf-8"),
        settings=Settings.from_config(json.loads(os.environ.get("PRO_V2_SETTINGS", "{}"))),
        work_dir=args.work,
    )
    summary = {"total_cost": res.usage.get("cost_usd"), **res.usage}
    out = {
        "proposal": res.proposal,
        "source": "pro_v2.run_core",
        "wall_time_s": round(time.monotonic() - start, 1),
        "summary": summary,
        "length": res.artefacts.get("length"),
    }
    Path(args.out).write_text(json.dumps(out, default=str, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
