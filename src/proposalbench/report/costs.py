"""Generation time and cost per proposal, and judging cost per evaluation (reported, not scored).

A cost the system recorded itself wins: Claude Code and Pro v2 report one, Claude Code's being the
API-equivalent of a subscription run. Otherwise the cost is estimated from the recorded tokens and
``configs/prices.yaml``. Codex counts cache hits inside its input tokens; submissions made before
``cached_input_tokens`` was recorded price all of that input as uncached, so their estimate is an
upper bound.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
PRICES = ROOT / "configs" / "prices.yaml"
SYSTEM_CONFIGS = ROOT / "configs" / "systems"

# Per-sample judge records, one file per judge; the other files in these folders are not calls.
JUDGE_STAGES = ("judges", "claims", "claims_adjudication", "support", "factsheet")
NOT_JUDGE_FILES = {"merged.json", "candidates.json", "pairs.json"}

# Weakest basis wins when a system's samples mix them.
BASIS_ORDER = ("recorded", "estimated", "upper_bound")


@dataclass(frozen=True)
class Price:
    input: float
    cached_input: float
    output: float

    def cost(self, input_tokens: int, output_tokens: int, cached_input_tokens: int = 0) -> float:
        uncached = max(0, input_tokens - cached_input_tokens)
        return (
            uncached * self.input
            + min(cached_input_tokens, input_tokens) * self.cached_input
            + output_tokens * self.output
        ) / 1e6


def load_prices(path: Path = PRICES) -> dict[str, Price]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    prices: dict[str, Price] = {}
    for model_id, p in data["models"].items():
        price = Price(
            float(p["input"]), float(p.get("cached_input", p["input"])), float(p["output"])
        )
        for name in (model_id, *p.get("aliases", [])):
            prices[name] = price
    return prices


def system_tool(system_id: str, configs: Path = SYSTEM_CONFIGS) -> tuple[str, str | None]:
    """(kind, CLI tool) of a system; ("unknown", None) without a config."""
    path = configs / f"{system_id}.yaml"
    if not path.exists():
        return "unknown", None
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return str(cfg.get("kind", "unknown")), (cfg.get("cli") or {}).get("tool")


@dataclass(frozen=True)
class Cost:
    usd: float | None
    basis: str | None  # "recorded" | "estimated" | "upper_bound"; None when unknown


def generation_cost(meta: dict, prices: dict[str, Price], tool: str | None = None) -> Cost:
    if meta.get("cost_usd") is not None:
        return Cost(float(meta["cost_usd"]), "recorded")
    models = meta.get("models") or []
    if not any(m.get("input_tokens") or m.get("output_tokens") for m in models):
        return Cost(None, None)
    total, basis = 0.0, "estimated"
    for m in models:
        price = prices.get(m["model_id"])
        if price is None:
            return Cost(None, None)
        cached = m.get("cached_input_tokens")
        if cached is None and tool == "codex":
            basis = "upper_bound"
        total += price.cost(m.get("input_tokens", 0), m.get("output_tokens", 0), cached or 0)
    return Cost(round(total, 4), basis)


def judging_cost(sample_dir: Path, prices: dict[str, Price]) -> float | None:
    """Judge spend on one evaluated sample, or None when a stage predates token recording or a
    judge has no price."""
    total, seen = 0.0, False
    for stage in JUDGE_STAGES:
        for f in sorted((sample_dir / stage).glob("*.json")):
            if f.name in NOT_JUDGE_FILES:
                continue
            record = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(record.get("record"), dict):  # fact sheets: {"sheet": ..., "record": ...}
                record = record["record"]
            if "input_tokens" not in record:
                return None
            price = prices.get(record.get("judge") or f.stem)
            if price is None:
                return None
            total += price.cost(record["input_tokens"], record.get("output_tokens", 0))
            seen = True
    return round(total, 4) if seen else None


def run_judging_cost(results_dir: Path) -> dict | None:
    """A run-level judging figure (``judging_cost.json``) for runs judged before token recording."""
    path = results_dir / "judging_cost.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def weakest(bases: list[str | None]) -> str | None:
    known = [b for b in bases if b]
    return max(known, key=BASIS_ORDER.index) if known else None
