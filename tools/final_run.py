"""Run every system of both tracks on the public split, then evaluate them.

Lanes run in parallel (Claude Code, Codex, paid APIs). Within a lane, systems
run one after another, and every system's sample 1 comes before any sample 2, so a stop leaves a
complete one-sample matrix. Infrastructure failures (a CLI or API error on our side) are run
again after a pause. Each finished pass queues the system for evaluation; one evaluation runs at
a time, so the evidence services see one request schedule.

    uv run python tools/final_run.py --eval-id public-v1 [--lanes claude,codex,api]

"""

from __future__ import annotations

import argparse
import fcntl
import json
import queue
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBMISSIONS = ROOT / "submissions"
LANES = {
    "claude": (
        [
            "cli-claude-code-opus",
            "direct-cc-claude-opus-5.5",
            "direct-cc-claude-sonnet-5.5",
            "direct-cc-claude-haiku-5.5",
        ],
        3,
    ),
    "codex": (
        [
            "cli-codex-gpt-6-astra",
            "direct-codex-gpt-6-astra",
            "direct-codex-gpt-6-luna",
            "direct-codex-gpt-6-sol",
        ],
        3,
    ),
    "api": (["direct-gemini-3.1-pro", "direct-gemini-3.8-flash", "agent-claude-opus-4.6"], 3),
    "proposia": (["proposia-pro-v2"], 3),
}
PASSES = 6
PAUSE_S = 600


def log(msg: str, fh=None) -> None:
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    if fh:
        fh.write(line + "\n")
        fh.flush()


def failures(system: str, k: int) -> int:
    n = 0
    for p in (SUBMISSIONS / system / "public").glob("*/*/meta.json"):
        meta = json.loads(p.read_text())
        if meta["sample"] <= k and meta["status"] == "infrastructure_failure":
            n += 1
    return n


def lane(name: str, systems: list[str], workers: int, args, evals: queue.Queue, out: Path):
    with open(out / f"{name}.log", "a", encoding="utf-8") as fh:
        for k in range(1, args.samples + 1):
            for system in systems:
                for attempt in range(1, PASSES + 1):
                    log(f"[{name}] {system} sample {k}, pass {attempt}", fh)
                    cmd = ["uv", "run", "pb", "run", "--system", system, "--split", "public"]
                    cmd += ["--samples", str(k), "--workers", str(workers)]
                    cmd += ["--eval-id", args.eval_id]
                    subprocess.run(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT)
                    left = failures(system, k)
                    if not left:
                        break
                    log(f"[{name}] {system}: {left} infrastructure failures; pausing", fh)
                    time.sleep(PAUSE_S)
                evals.put(system)
    log(f"[{name}] lane finished")


def evaluator(evals: queue.Queue, done: threading.Event, args, out: Path):
    with open(out / "evaluate.log", "a", encoding="utf-8") as fh:
        while not (done.is_set() and evals.empty()):
            try:
                system = evals.get(timeout=30)
            except queue.Empty:
                continue
            log(f"[eval] {system}", fh)
            cmd = ["uv", "run", "pb", "evaluate", "--system", system, "--split", "public"]
            cmd += ["--eval-id", args.eval_id, "--workers", str(args.eval_workers)]
            # One evaluation at a time across drivers: evidence services see one schedule.
            with open(out / "evaluate.lock", "w") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                subprocess.run(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT)
    log("[eval] finished")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-id", required=True)
    ap.add_argument("--lanes", default=",".join(LANES))
    ap.add_argument("--samples", type=int, default=2)
    ap.add_argument("--eval-workers", type=int, default=4)
    args = ap.parse_args()
    out = ROOT / ".work" / "runs" / args.eval_id
    out.mkdir(parents=True, exist_ok=True)
    evals: queue.Queue = queue.Queue()
    done = threading.Event()
    ev = threading.Thread(target=evaluator, args=(evals, done, args, out))
    ev.start()
    threads = []
    for name in args.lanes.split(","):
        systems, workers = LANES[name]
        t = threading.Thread(target=lane, args=(name, systems, workers, args, evals, out))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    # A last pass over every system picks up evaluations deferred while a source was out.
    for name in args.lanes.split(","):
        for system in LANES[name][0]:
            evals.put(system)
    done.set()
    ev.join()
    report = subprocess.run(
        ["uv", "run", "pb", "report", "--eval-id", args.eval_id],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    (out / "report.md").write_text(report.stdout + report.stderr, encoding="utf-8")
    log(f"all lanes finished; report in {out / 'report.md'}")


if __name__ == "__main__":
    main()
