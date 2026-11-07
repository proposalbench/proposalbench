"""Build systems from ``configs/systems/<id>.yaml``."""

from __future__ import annotations

from pathlib import Path

import yaml

from proposalbench.llm import ModelSpec
from proposalbench.systems.agent import ReferenceAgent
from proposalbench.systems.direct import DirectSystem

CONFIGS = Path(__file__).resolve().parents[3] / "configs" / "systems"


def load_system(name_or_path: str):
    path = Path(name_or_path)
    if not path.is_file():
        path = CONFIGS / f"{name_or_path}.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    if cfg["kind"] == "cli":
        from proposalbench.systems.cli import CliSystem

        return CliSystem(cfg["id"], **cfg["cli"])
    if cfg["kind"] == "proposia":
        from proposalbench.systems.proposia import ProposiaSystem

        return ProposiaSystem(cfg["id"], **cfg["proposia"])
    model = cfg["model"]
    spec = ModelSpec(
        provider=model["provider"],
        model_id=model["id"],
        max_output_tokens=model.get("max_output_tokens", 32000),
        temperature=model.get("temperature"),
        region=model.get("region", "us-east-1"),
    )
    if cfg["kind"] == "direct":
        return DirectSystem(cfg["id"], spec)
    if cfg["kind"] == "agent":
        return ReferenceAgent(cfg["id"], spec, **cfg.get("agent", {}))
    raise ValueError(f"unknown system kind {cfg['kind']!r} in {path}")
