"""Validate the public v2 authoring design without generation or paid model calls.

Run from any directory: uv run python tools/authoring/check_matrix_v2.py
v1 trap counts come from the audited classification in v1_trap_types.yaml (37 traps).
This checks the specification; rendered calls, dossier evidence and briefs still need review.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
FAMILIES = ("anthropic", "google", "openai")


def _v1_trap_counts() -> dict[str, int]:
    """Per-type counts of the audited v1 traps (one primary type each, v1_trap_types.yaml)."""
    audit = yaml.safe_load((HERE / "v1_trap_types.yaml").read_text(encoding="utf-8"))
    counts = Counter(t for traps in audit.values() for t in traps.values())
    return {f"T{i:02}": counts.get(f"T{i:02}", 0) for i in range(1, 15)}


V1_TRAPS = _v1_trap_counts()
SCHEMES = {
    "erasmus_ka220": 2,
    "cerv": 2,
    "horizon_stage1": 2,
    "horizon_ria": 4,
    "nih_r21_resubmission": 2,
    "nsf_career": 2,
    "erc_poc": 2,
    "aei_pid_orientada": 2,
    "foundation_concept": 2,
}
CONSORTIUM_SCHEMES = {"erasmus_ka220", "cerv", "horizon_stage1", "horizon_ria"}
TASK_TYPES = {"full": 24, "stage1": 4, "concept_note": 4, "resubmission": 8}
VARIANTS = {"thin": 2, "internally inconsistent": 2, "cross-language": 2, "resubmission": 4}


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate mapping keys rather than silently discarding specifications."""


def unique_mapping(loader: UniqueLoader, node: yaml.MappingNode) -> dict:
    result: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise ValueError(f"Duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def load_matrix(path: Path) -> dict[str, Any]:
    data = yaml.load(path.read_text(), Loader=UniqueLoader)
    if not isinstance(data, dict) or set(data) != {"families", "calls", "dossiers", "tasks"}:
        raise ValueError(f"{path}: expected families, calls, dossiers and tasks blocks")
    if not isinstance(data["families"], dict):
        raise ValueError(f"{path}: families must be a mapping")
    for kind in ("calls", "dossiers", "tasks"):
        if not isinstance(data[kind], list) or not all(isinstance(x, dict) for x in data[kind]):
            raise ValueError(f"{path}: {kind} must be a list of mappings")
        if any(not isinstance(x.get("id"), str) or not x["id"] for x in data[kind]):
            raise ValueError(f"{path}: every {kind} entry needs a nonempty string id")
    return data


def read_targets(path: Path) -> dict[str, int]:
    targets = {}
    for line in path.read_text().splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 4 and re.match(r"T\d{2} ", cells[0]):
            targets[cells[0][:3]] = int(cells[-1])
    if set(targets) != set(V1_TRAPS):
        raise ValueError(f"{path}: expected all fourteen trap targets in the design table")
    return targets


def validate_graph(matrix: dict, label: str, errors: list[str]) -> int:
    calls = {x["id"]: x for x in matrix["calls"]}
    dossiers = {x["id"]: x for x in matrix["dossiers"]}
    tasks = matrix["tasks"]
    all_ids = [x["id"] for kind in ("calls", "dossiers", "tasks") for x in matrix[kind]]
    if len(all_ids) != len(set(all_ids)):
        errors.append(f"{label}: IDs must be unique within and across unit kinds")
    for task in tasks:
        if task.get("call") not in calls or task.get("dossier") not in dossiers:
            errors.append(f"{label}/{task['id']}: unknown call or dossier")
            continue
        if task.get("fit") not in {"close", "stretch"}:
            errors.append(f"{label}/{task['id']}: fit must be close or stretch")
        consortium_call = calls[task["call"]]["scheme"] in CONSORTIUM_SCHEMES
        consortium_dossier = dossiers[task["dossier"]]["applicant_type"] == "consortium"
        if consortium_call != consortium_dossier:
            errors.append(f"{label}/{task['id']}: incompatible consortium/applicant pairing")
    for field, units in (("call", calls), ("dossier", dossiers)):
        for uid in units:
            fits = Counter(t.get("fit") for t in tasks if t.get(field) == uid)
            if fits != {"close": 1, "stretch": 1}:
                errors.append(f"{label}/{uid}: expected exactly one close and one stretch use")
    if errors:
        return 0  # Do not derive cycles from invalid references or duplicate usage.
    by_call = {c: {t["fit"]: t for t in tasks if t["call"] == c} for c in calls}
    close_call = {t["dossier"]: t["call"] for t in tasks if t["fit"] == "close"}
    cycles = set()
    for cid, pair in by_call.items():
        own = pair["close"]["dossier"]
        other = pair["stretch"]["dossier"]
        partner = close_call[other]
        if partner == cid or by_call[partner]["stretch"]["dossier"] != own:
            errors.append(f"{label}/{cid}: does not belong to a genuine two-call two-dossier cycle")
        if label == "v2" and calls[cid]["scheme"] != calls[partner]["scheme"]:
            errors.append(f"{label}/{cid}: v2 cycles must remain inside compatible scheme families")
        cycles.add(tuple(sorted((cid, partner))))
    return len(cycles)


def validate_v2(matrix: dict, v1: dict, errors: list[str]) -> None:
    required = {
        "calls": {"id", "scheme", "skeleton", "language", "author", "topic_code", "theme"},
        "dossiers": {
            "id",
            "author",
            "applicant_type",
            "career_stage",
            "language",
            "country",
            "method_profile",
            "disciplines",
            "research_dna",
        },
        "tasks": {"id", "call", "dossier", "fit", "type", "traps"},
    }
    for kind, fields in required.items():
        for item in matrix[kind]:
            allowed = fields | ({"conditions", "title"} if kind == "calls" else set())
            if not fields <= item.keys() or not item.keys() <= allowed:
                errors.append(f"v2/{item['id']}: missing/unknown {kind} fields")
    if errors:
        return
    expected_families = v1["families"] | {"anthropic": {"provider": "claude", "model": "opus"}}
    if matrix["families"] != expected_families:
        errors.append(
            "v2: families must match v1 except anthropic: {provider: claude, model: opus}"
        )
    for kind, count in (("calls", 20), ("dossiers", 20), ("tasks", 40)):
        if len(matrix[kind]) != count:
            errors.append(f"v2: expected {count} {kind}")
    v1_ids = {x["id"] for kind in required for x in v1[kind]}
    v2_ids = {x["id"] for kind in required for x in matrix[kind]}
    if overlap := v1_ids & v2_ids:
        errors.append(f"v2 IDs overlap v1: {sorted(overlap)}")
    if Counter(c["scheme"] for c in matrix["calls"]) != SCHEMES:
        errors.append("v2: call allocation differs from the design's scheme table")
    if Counter(t["type"] for t in matrix["tasks"]) != TASK_TYPES:
        errors.append("v2: expected 24 full, 4 stage1, 4 concept_note and 8 resubmission tasks")
    calls = {c["id"]: c for c in matrix["calls"]}
    dossiers = {d["id"]: d for d in matrix["dossiers"]}
    codes = [c["topic_code"] for c in matrix["calls"]]
    if len(codes) != len(set(codes)) or set(codes) & {c["topic_code"] for c in v1["calls"]}:
        errors.append("v2: topic codes must be unique and disjoint from v1")
    for call in matrix["calls"]:
        if call["skeleton"] != call["scheme"] or call["skeleton"] not in SCHEMES:
            errors.append(f"v2/{call['id']}: wrong exact skeleton name for the scheme")
        if not (call.get("title") or call.get("conditions")):
            errors.append(f"v2/{call['id']}: provide conditions or title")
        language = "es" if call["scheme"] == "aei_pid_orientada" else "en"
        if call["language"] != language:
            errors.append(f"v2/{call['id']}: expected call language {language}")
    for kind in ("calls", "dossiers"):
        counts = Counter(x["author"] for x in matrix[kind])
        if set(counts) != set(FAMILIES) or max(counts.values()) - min(counts.values()) > 1:
            errors.append(f"v2: unbalanced {kind} authors: {dict(counts)}")
    for variant, expected in VARIANTS.items():
        count = sum(f"Variant {variant}" in d["research_dna"] for d in dossiers.values())
        if count != expected:
            errors.append(f"v2: expected {expected} {variant} dossiers, found {count}")
    for dossier in dossiers.values():
        dna = dossier["research_dna"]
        if "Variant resubmission" in dna:
            criticisms = re.findall(r"\(([1-5])\)", dna)
            if not 3 <= len(criticisms) <= 5 or criticisms != list("12345"[: len(criticisms)]):
                errors.append(f"v2/{dossier['id']}: number 3–5 distinct reviewer criticisms")
    for task in matrix["tasks"]:
        cid, did = task["call"], task["dossier"]
        if cid not in calls or did not in dossiers:
            continue  # Graph validator reports broken references.
        call, dossier = calls[cid], dossiers[did]
        expected_type = {
            "horizon_stage1": "stage1",
            "foundation_concept": "concept_note",
            "nih_r21_resubmission": "resubmission",
        }.get(call["scheme"], "full")
        if call["scheme"] == "horizon_ria" and "Variant resubmission" in dossier["research_dna"]:
            expected_type = "resubmission"
        if task["type"] != expected_type:
            errors.append(f"v2/{task['id']}: incompatible task type; expected {expected_type}")
        history = "Variant resubmission" in dossier["research_dna"]
        if (task["type"] == "resubmission") != history:
            errors.append(
                f"v2/{task['id']}: revision task/history mismatch (both fits need history)"
            )
        cross_language = call["language"] != dossier["language"]
        if cross_language != ("Variant cross-language" in dossier["research_dna"]):
            errors.append(f"v2/{task['id']}: unmarked or nonfunctional cross-language variant")
        traps = task["traps"]
        if not isinstance(traps, list) or len(traps) > 2:
            errors.append(f"v2/{task['id']}: traps must be a list of 0–2 entries")
            continue
        seen = set()
        for trap in traps:
            if not isinstance(trap, dict) or set(trap) != {"type", "idea"}:
                errors.append(f"v2/{task['id']}: each trap needs exactly type and idea")
                continue
            typ, idea = trap["type"], trap["idea"]
            if typ not in V1_TRAPS or typ in seen or not isinstance(idea, str) or not idea.strip():
                errors.append(f"v2/{task['id']}: invalid/duplicate trap type or empty idea")
            seen.add(typ)
            if typ == "T13" and task["type"] != "resubmission":
                errors.append(f"v2/{task['id']}: T13 requires a revision history")
            if typ == "T12" and not (
                "Dossier-only fact:" in idea and "Dossier-only fact" in dossier["research_dna"]
            ):
                errors.append(f"v2/{task['id']}: T12 needs explicit dossier-only sourcing")
            if typ == "T01" and call["scheme"] not in {
                "erasmus_ka220",
                "horizon_ria",
                "foundation_concept",
            }:
                errors.append(f"v2/{task['id']}: no required narrative budget; T01 undecidable")
    # Each call uses one output type, including the two RIA revision calls.
    call_types = [{t["type"] for t in matrix["tasks"] if t["call"] == c} for c in calls]
    if any(len(types) != 1 for types in call_types):
        errors.append("v2: each call must have one shared task type across both fits")
    revision_calls = {
        t["call"]
        for t in matrix["tasks"]
        if t["type"] == "resubmission" and calls[t["call"]]["scheme"] == "horizon_ria"
    }
    if len(revision_calls) != 2:
        errors.append("v2: expected exactly two horizon_ria revision calls")


def author_counts(matrix: dict, kind: str) -> Counter:
    if kind != "tasks":
        return Counter(x["author"] for x in matrix[kind])
    dossier_authors = {d["id"]: d["author"] for d in matrix["dossiers"]}
    return Counter(dossier_authors[t["dossier"]] for t in matrix["tasks"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1", type=Path, default=HERE / "public_matrix.yaml")
    parser.add_argument("--v2", type=Path, default=HERE / "public_matrix_v2.yaml")
    parser.add_argument("--design", type=Path, default=HERE / "design_v2.md")
    args = parser.parse_args()
    try:
        v1, v2 = load_matrix(args.v1), load_matrix(args.v2)
        targets = read_targets(args.design)
        errors: list[str] = []
        cycles_v1 = validate_graph(v1, "v1", errors)
        validate_v2(v2, v1, errors)
        cycles_v2 = validate_graph(v2, "v2", errors)
        if errors:
            print("FAIL\n" + "\n".join(f"- {e}" for e in errors))
            return 1
        counts = Counter(trap["type"] for task in v2["tasks"] for trap in task["traps"])
        print("Trap counts (targets are minima; this matrix aims for exact totals)")
        print("| Type | v1 supplied | v2 | All 60 | Target | Status |")
        print("|---|---:|---:|---:|---:|---|")
        for typ, baseline in V1_TRAPS.items():
            total, target = baseline + counts[typ], targets[typ]
            status = "exact" if total == target else "above" if total > target else "SHORT"
            print(f"| {typ} | {baseline} | {counts[typ]} | {total} | {target} | {status} |")
            if total < target:
                errors.append(f"{typ}: {total} is below target {target}")
        print(
            f"| Total | {sum(V1_TRAPS.values())} | {sum(counts.values())} | "
            f"{sum(V1_TRAPS.values()) + sum(counts.values())} | {sum(targets.values())} | |"
        )
        print("\nAuthor family (tasks inherit dossier author)")
        print("| Units | anthropic | google | openai | Total |")
        print("|---|---:|---:|---:|---:|")
        for kind in ("calls", "dossiers", "tasks"):
            new = author_counts(v2, kind)
            combined = new + author_counts(v1, kind)
            for label, authors in ((f"v2 {kind}", new), (f"all {kind}", combined)):
                cells = " | ".join(str(authors[f]) for f in FAMILIES)
                print(f"| {label} | {cells} | {sum(authors.values())} |")
            if kind == "tasks" and sorted(new.values()) != [12, 14, 14]:
                errors.append("v2 task-family balance must be 12/14/14")
        print("\n| Scheme | New calls | New tasks |")
        print("|---|---:|---:|")
        for scheme, count in SCHEMES.items():
            print(f"| {scheme} | {count} | {count * 2} |")
        print("\nTask types: " + ", ".join(f"{k}={v}" for k, v in TASK_TYPES.items()))
        print("Variants: " + ", ".join(f"{k}={v}" for k, v in VARIANTS.items()))
        print(f"Independent two-cycles: v1={cycles_v1}, v2={cycles_v2}")
        trap_load = Counter(len(t["traps"]) for t in v2["tasks"])
        print(f"Traps per v2 task: {dict(sorted(trap_load.items()))}")
        print(
            "NOTE: structural pass does not verify final briefs, source facts or scheme fidelity."
        )
        if errors:
            print("FAIL\n" + "\n".join(f"- {e}" for e in errors))
            return 1
        print("PASS: matrices, cycles, compatibility, quotas and author balance")
        return 0
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
