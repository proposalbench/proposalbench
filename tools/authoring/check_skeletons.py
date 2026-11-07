"""Render the authored scheme skeletons with dummy topics and validate their contracts.

Run from any directory: uv run python tools/authoring/check_skeletons.py
Optional positional paths select individual skeletons. No generated call files are written.
"""

from __future__ import annotations

import argparse
import re
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path

import yaml
from markdown_it import MarkdownIt

from proposalbench.tasks.schema import CANARY_RE, Call

# Authoring tools are standalone scripts; also support tests loading this file with run_path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from synthesize import _amounts

ROOT = Path(__file__).resolve().parents[2]
SCHEMES = ROOT / "tools" / "authoring" / "schemes"
V2_NAMES = (
    "horizon_stage1",
    "erasmus_ka220",
    "cerv",
    "erc_poc",
    "nsf_career",
    "nih_r21_resubmission",
    "aei_pid_orientada",
    "foundation_concept",
)
NAMES = ("erc_stg", "msca_pf_ef", "msca_pf_gf", "nsf", "aei_pid_noorientada", *V2_NAMES)
BENCHMARK_MECHANICS_RE = re.compile(r"dossier|ProposalBench['’]s|fabricat", re.IGNORECASE)
CANARY = "PROPOSALBENCH-CANARY 00000000-0000-4000-8000-000000000001"
SLOT_RE = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")
BASE_SLOTS = {"topic_code", "max_words", "canary"}
TOPIC_SLOTS = {
    "title",
    "header_table",
    "expected_outcomes_intro",
    "expected_outcomes",
    "scope_intro",
    "scope",
    "exclusions",
    "specific_conditions",
}
PREFIXES = {
    "expected_outcomes": "EO",
    "scope": "SC",
    "exclusions": "EX",
    "mandatory_elements": "ME",
}


def normalise(text: str) -> str:
    return " ".join(text.casefold().split())


def check_applicant_text(skeleton: dict, path: Path) -> None:
    """Reject benchmark mechanics in v2 applicant prose, not authoring notes or v1."""
    if skeleton["name"] not in V2_NAMES:
        return
    fields = [("call_md", skeleton["call_md"])]
    fields.extend(
        (f"fixed_items.{group}.{item['id']}", item["text"])
        for group, items in skeleton["fixed_items"].items()
        for item in items
    )
    for field, text in fields:
        match = BENCHMARK_MECHANICS_RE.search(text)
        assert not match, f"{path}: benchmark mechanics in {field}: {match.group()!r}"


def check_fixed_values(skeleton: dict, path: Path) -> None:
    """Keep overridable ceilings out of topic prose and fixed items.

    fixed_values_in_text maps eligibility keys to numeric lists of deliberate fixed rules,
    e.g. max_budget: [400000] for the Erasmus lump-sum menu. Document each exception in YAML.
    Match the renderer's amount formats, including across YAML/Markdown line wrapping.
    """
    if skeleton["bottom_up"]:
        return
    allowed = skeleton.get("fixed_values_in_text", {})
    text = normalise(
        "\n".join(
            [skeleton["call_md"]]
            + [item["text"] for items in skeleton["fixed_items"].values() for item in items]
        )
    )
    for key in ("max_budget", "duration_months_max"):
        value = skeleton["eligibility"].get(key)
        if value is None or value in allowed.get(key, []):
            continue
        for literal in _amounts(value):
            assert not re.search(rf"(?<![\d.,]){re.escape(normalise(literal))}(?!\d)", text), (
                f"{path}: hard-coded eligibility.{key}={value} ({literal!r}) in call_md or "
                "fixed_items; use the conditions table or document a fixed_values_in_text rule"
            )


def heading_and_list_entries(markdown: str) -> list[str]:
    """Collect actual Markdown headings/list entries, including wrapped list text."""
    entries = []
    list_depth = 0
    previous = ""
    for token in MarkdownIt().parse(markdown):
        if token.type in {"bullet_list_open", "ordered_list_open"}:
            list_depth += 1
        elif token.type in {"bullet_list_close", "ordered_list_close"}:
            list_depth -= 1
        elif token.type == "inline" and (previous == "heading_open" or list_depth):
            plain = "".join(
                child.content if child.type != "softbreak" else " "
                for child in token.children or []
                if child.type in {"text", "code_inline", "softbreak"}
            )
            # Section numbers are template labels, not part of RequiredSection.title.
            plain = re.sub(r"^\d+(?:\.\d+)*[.)]?\s+", "", plain)
            entries.append(normalise(plain))
        previous = token.type
    return entries


def check(path: Path) -> Call:
    skeleton = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert skeleton["name"] == path.stem, f"{path}: name differs from filename"
    assert isinstance(skeleton["bottom_up"], bool), f"{path}: bottom_up must be boolean"
    check_applicant_text(skeleton, path)
    check_fixed_values(skeleton, path)
    items = deepcopy(skeleton["fixed_items"])
    assert set(items) == set(PREFIXES), f"{path}: incomplete fixed_items groups"
    for group, prefix in PREFIXES.items():
        if skeleton["name"] in V2_NAMES:
            assert [item["id"] for item in items[group]] == [
                f"{prefix}{i}" for i in range(1, len(items[group]) + 1)
            ], f"{path}: {group} ids must be contiguous from {prefix}1"
        for item in items[group]:
            assert re.fullmatch(rf"{prefix}[1-9]\d*", item["id"]), (
                f"{path}: invalid {group} id {item['id']}"
            )
    if skeleton.get("bottom_up"):  # topic schemes take their expected outcomes from the topic
        assert items["expected_outcomes"], f"{path}: a scheme-wide expected outcome is required"

    if not skeleton["bottom_up"]:
        existing = {item["id"] for item in items["expected_outcomes"]}
        index = 1
        while f"EO{index}" in existing:
            index += 1
        items["expected_outcomes"].append(
            {"id": f"EO{index}", "text": "Dummy topic: test a specified scientific explanation."}
        )
        bounds_match = re.search(
            r"^eligibility_bounds:\n((?:[ \t]+[^\n]*\n)+)",
            skeleton["author_notes"],
            re.MULTILINE,
        )
        assert bounds_match, f"{path}: missing eligibility_bounds in author_notes"
        bounds = yaml.safe_load(bounds_match.group(0))["eligibility_bounds"]
        for key in ("max_budget", "duration_months_max"):
            value = skeleton["eligibility"][key]
            assert bounds[key]["min"] <= value <= bounds[key]["max"], (
                f"{path}: default {key} outside authoring bounds"
            )

    topic_code = skeleton["topic_code_prefix"] + "-CHECK"
    call = Call.model_validate(
        {
            "id": path.stem.replace("_", "-") + "-check",
            "scheme": skeleton["scheme"],
            "language": skeleton["language"],
            "title": "Dummy topic title",
            "topic_code": topic_code,
            "proposal_type": skeleton.get("proposal_type", "full"),
            "length_contract": skeleton["length_contract"],
            "required_sections": skeleton["required_sections"],
            "eligibility": skeleton["eligibility"],
            **items,
            "provenance": skeleton.get("provenance")
            or {
                "author": "human",
                "author_family": "human",
                "created": date(2026, 10, 31),
                "notes": "Ephemeral checker fixture; not an authored or published call.",
            },
            "canary": CANARY,
        }
    )
    contract = call.length_contract
    assert contract.page_limit and contract.words_per_page, f"{path}: missing conversion"
    estimate = contract.page_limit * contract.words_per_page
    assert abs(contract.max_words - estimate) <= estimate * 0.1, (
        f"{path}: max_words differs from page conversion by more than 10%"
    )
    if call.scheme.value != "foundation":
        assert re.search(r"https://\S+", contract.source_note), f"{path}: no length source URL"
    else:
        assert "invented" in contract.source_note.lower(), f"{path}: missing fictional limit basis"
    for source in skeleton.get("sources", []):
        assert source["url"].startswith("https://"), f"{path}: invalid source URL"
        date.fromisoformat(str(source["verified"]))
    assert re.search(r"\b\d{4}-\d{2}-\d{2}\b", contract.source_note), (
        f"{path}: no source verification date"
    )
    max_words = f"{contract.max_words:,}"
    if call.language == "es":
        max_words = max_words.replace(",", ".")
    consortium_note = (
        call.eligibility.consortium.notes if call.eligibility.consortium else "As specified below"
    )
    slots = {
        "title": call.title,
        "topic_code": topic_code,
        "max_words": max_words,
        "canary": CANARY,
        "header_table": (
            "| Condition | Dummy value |\n|---|---|\n"
            f"| Total award cap (invented) | {call.eligibility.currency} "
            f"{call.eligibility.max_budget or 0:,.0f} |\n"
            f"| Duration (invented) | {call.eligibility.duration_months_min}–"
            f"{call.eligibility.duration_months_max} months |\n"
            "| Submission date (invented) | 15 September 2027 |\n"
            f"| Consortium | {consortium_note} |"
        ),
        "expected_outcomes_intro": "Dummy topic-specific outcomes follow.",
        "scope_intro": "Dummy topic-specific scope follows.",
    }
    for group in PREFIXES:
        slot = "specific_conditions" if group == "mandatory_elements" else group
        slots[slot] = "\n".join("- " + item["text"] for item in items[group])
    template = skeleton["call_md"]
    expected_slots = BASE_SLOTS | (set() if skeleton["bottom_up"] else TOPIC_SLOTS)
    if not skeleton["bottom_up"] and call.language == "es":
        # The renderer's header_table has English labels; Spanish calls keep their own table.
        expected_slots -= {"header_table"}
        assert "| Condición | Requisito |" in template, f"{path}: missing Spanish conditions table"
    assert set(SLOT_RE.findall(template)) == expected_slots, f"{path}: missing or extra slots"
    assert template.rstrip().endswith("<!-- {{canary}} -->"), f"{path}: invalid canary slot"
    rendered = SLOT_RE.sub(lambda match: slots[match[1]], template)
    assert "{{" not in rendered and "}}" not in rendered, f"{path}: unresolved slot"
    assert topic_code in rendered, f"{path}: missing topic code"
    assert max_words in rendered, f"{path}: missing rendered max_words"
    assert CANARY_RE.fullmatch(CANARY)
    assert rendered.rstrip().endswith(f"<!-- {CANARY} -->"), f"{path}: missing canary"
    assert rendered.count(f"<!-- {CANARY} -->") == 1, f"{path}: duplicated canary"

    entries = heading_and_list_entries(rendered)
    for section in call.required_sections:
        title = normalise(section.title)
        assert any(entry == title or entry.startswith(title + ":") for entry in entries), (
            f"{path}: required title is not a heading/list entry: {section.title}"
        )
    for values in items.values():
        for item in values:
            assert normalise(item["text"]) in normalise(rendered), (
                f"{path}: call item {item['id']} is missing from rendered text"
            )
    rubric_path = ROOT / "rubrics" / "schemes" / f"{call.scheme.value}.yaml"
    rubric = yaml.safe_load(rubric_path.read_text(encoding="utf-8"))
    referenced = {str(sid) for ids in rubric["roles"].values() for sid in ids}
    referenced.update(str(sid) for item in rubric["items"] for sid in item.get("sections", []))
    missing = referenced - {section.id for section in call.required_sections}
    assert not missing, f"{path}: rubric references absent sections: {sorted(missing)}"
    print(f"OK {path.name}: Call validates, slots/sections/items/length/canary/rubric agree")
    return call


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", type=Path, nargs="*")
    args = parser.parse_args()
    paths = args.paths or [SCHEMES / f"{name}.yaml" for name in NAMES]
    for path in paths:
        check(path)
    print(f"Validated {len(paths)} skeletons.")


if __name__ == "__main__":
    main()
