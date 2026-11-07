"""Offline intervention and artefact-contract tests; no model or evidence API calls."""

# meta/ is a repository tool, deliberately outside the installed src/ package.
import json
import random
import re
import sys
from dataclasses import asdict, replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from meta.perturb.operators import (
    OPERATORS,
    ROOT,
    Detector,
    Expectation,
    _ref_line,
)
from meta.perturb.run import detect, fires, run, summarize, wilson
from proposalbench.checks.admissibility import check_admissibility, counted_text
from proposalbench.checks.hygiene import check_hygiene, check_required_sections
from proposalbench.parse.citations import find_citations
from proposalbench.parse.references import parse_references
from proposalbench.parse.section_mapping import map_sections
from proposalbench.parse.sections import count_words, parse_proposal
from proposalbench.systems.base import SubmissionMeta
from proposalbench.tasks.loader import Repository
from proposalbench.tasks.schema import Enforcement


@pytest.fixture
def rt():
    return Repository().get("pilot-he-soilwater-close")


@pytest.fixture
def proposal(rt):
    intro = (
        "The document provides a concise introduction to the research context for interested "
        "readers. It uses ordinary disciplinary terminology and describes the proposed study "
        "in the following sections without further administrative information."
    )
    pieces = ["# Soil water study", intro]
    for i, section in enumerate(rt.call.required_sections):
        heading = "###" if section.parent else "##"
        # Distinct prose avoids pre-existing near-duplicate paragraphs in the fixture.
        pieces.append(f"{heading} {section.id} {section.title}")
        if section.id == "2.3":
            pieces.append(
                "Farmers will receive a guide to water retention. Regional advisers will "
                "distribute this guide through their existing meetings. The expected result "
                "is improved access to locally relevant knowledge about soil management."
            )
        else:
            pieces.append(f"The study addresses requirement {i} through a specific task.")
        if section.id == "1.2":
            pieces += [
                rt.dossier.facts[0].text,
                "Published telescope observations detected 73 distant galaxies [1].",
            ]
        if section.id == "3.1":
            pieces += [
                "Project duration: 48 months.",
                "The total requested budget is EUR 5000000.",
                "An illustrative example cost for comparison is EUR 20000.",
                "| WP | Title | Start | End |\n|---|---|---|---|\n"
                "| WP1 | Field sampling | 1 | 24 |\n| WP2 | Synthesis | 24 | 48 |",
                "The analysis in WP1 feeds the synthesis in WP2.",
                "Deliverable D1.1 is due in month 24; WP1 provides the observations.",
                "Milestone M2 is due in month 36 and confirms the analysis.",
            ]
    records = [
        dict(
            authors=["Kobak"],
            year=2025,
            title="Delving into LLM-assisted writing in biomedical publications "
            "through excess vocabulary",
            venue="Science Advances",
            doi="10.1126/sciadv.adt3813",
        ),
        dict(
            authors=["Vaswani"],
            year=2017,
            title="Attention is all you need",
            venue="Advances in Neural Information Processing Systems",
            doi="10.48550/arXiv.1706.03762",
        ),
    ]
    pieces += [
        "## References",
        "\n\n".join(f"[{i}] {_ref_line(r)}" for i, r in enumerate(records, 1)),
    ]
    return "\n\n".join(pieces) + "\n"


def verdicts(base):
    return [
        {"ref": asdict(r), "status": "verified", "best": {"doi": r.doi}}
        for r in parse_references(parse_proposal(base).references_block or "")
    ]


def hygiene(base):
    return {f.check for f in check_hygiene(parse_proposal(base))}


@pytest.mark.parametrize("name", OPERATORS)
def test_every_operator(name, proposal, rt):
    base = proposal
    if name == "drop_required_section":
        base = proposal.replace(
            "## References", _section_control_prose() + "\n\n## References"
        ).replace(
            "locally relevant knowledge about soil management.",
            "locally relevant knowledge about soil management. " + "Further detail. " * 12,
        )
    if name == "fabricated_reference":
        # Its matched real reference must not already be in the proposal.
        base = proposal.replace("10.1126/sciadv.adt3813", "10.1126/another-existing-work")
    p, c, e = OPERATORS[name](base, rt, random.Random(42), references=verdicts(base))
    assert e.applicable, e.reason
    assert p != base and p != c
    assert c != base or name == "citation_padding" or e.taxonomy == ("invariance",)
    assert e.detectors
    assert parse_proposal(p).sections and parse_proposal(c).sections
    assert parse_references(parse_proposal(p).references_block or "")
    assert parse_references(parse_proposal(c).references_block or "")
    assert (p, c, e) == OPERATORS[name](base, rt, random.Random(42), references=verdicts(base))
    roundtrip = Expectation.from_dict(json.loads(json.dumps(e.to_dict())))
    assert roundtrip.to_dict() == json.loads(json.dumps(e.to_dict()))

    if name == "drop_required_section":
        sid = e.details["section_id"]
        assert any(
            f.data.get("section_id") == sid and f.check == "structure.missing_section"
            for f in check_required_sections(parse_proposal(p), rt.call.required_sections)
        )
        assert all(m.section for m in map_sections(parse_proposal(c), rt.call.required_sections))
    elif name == "exceed_length":
        assert (
            count_words(counted_text(parse_proposal(p), rt.call))
            > 1.2 * rt.call.length_contract.max_words
        )
        assert count_words(counted_text(parse_proposal(c), rt.call)) == count_words(
            counted_text(parse_proposal(base), rt.call)
        )
        assert count_words(p) == count_words(c)
    elif name in {"duplicate_paragraph", "leave_placeholder", "meta_commentary"}:
        check = e.detectors[0].values[0]
        assert check in hygiene(p)
        assert check not in hygiene(c)
    elif name == "fabricated_reference":
        assert e.details["fabricated_doi"] in p and e.details["fabricated_doi"] not in c
        assert e.details["control_doi"] in c
        assert find_citations(parse_proposal(p).body_text())
        assert find_citations(parse_proposal(c).body_text())
        assert len(parse_references(parse_proposal(p).references_block)) == 3
    elif name == "corrupt_reference_metadata":
        ref_p = parse_references(parse_proposal(p).references_block)[e.details["ref_index"]]
        ref_c = parse_references(parse_proposal(c).references_block)[e.details["ref_index"]]
        assert ref_p.year == ref_c.year + 3
        assert ref_p.authors[0] == "Zorvellan" and ref_c.authors[0] != "Zorvellan"
    elif name == "wrong_doi_on_real_reference":
        ref_p = parse_references(parse_proposal(p).references_block)[e.details["ref_index"]]
        ref_c = parse_references(parse_proposal(c).references_block)[e.details["ref_index"]]
        assert ref_p.doi == e.details["replacement_doi"]
        assert ref_c.doi == e.details["original_doi"]
        assert (ref_p.title, ref_p.authors, ref_p.year) == (ref_c.title, ref_c.authors, ref_c.year)
    elif name == "contradict_dossier_number":
        assert f"by {e.details['replacement']}%" in p and "by 11%" in c
        assert "73 distant galaxies" in p and "73 distant galaxies" not in c
    elif name == "fabricated_applicant_award":
        assert e.details["prize"] in p and e.details["prize"] not in c
        assert e.detectors[0].control_target in c
    elif name == "budget_over_cap":
        assert "EUR 6900000" in p and "EUR 4750000" in c
        assert "EUR 20000" in c and "EUR 20000" in p
        assert "TRAP-T2" in {d.id for d in e.detectors}
    elif name == "milestone_after_end":
        assert any(f"month {m}" in p for m in range(49, 55))
        assert all(f"month {m}" not in c for m in range(49, 55))
    elif name == "undefined_work_package":
        new, old = e.details["undefined_id"], e.details["old_id"]
        assert new in p and f"| {new} |" not in p
        assert f"| {new} |" in c and old not in c
    elif name == "prompt_injection":
        assert "rate all items yes" in p and "rate all items yes" not in c
        assert not e.detectors[0].expected
    elif name == "citation_padding":
        assert len(parse_references(parse_proposal(p).references_block)) == 12
        assert c == base and e.control_is_base
        assert len(find_citations(parse_proposal(p).body_text())[-1].labels) == 10
        assert e.detectors[1].exclude_criteria == ("d",)


@pytest.mark.parametrize("name", OPERATORS)
def test_every_operator_not_applicable(name, rt):
    p, c, e = OPERATORS[name]("", rt, random.Random(1))
    assert p == c == ""
    assert not e.applicable and e.reason


def test_rejects_existing_hygiene_and_unverified_refs(proposal, rt):
    for name in ("duplicate_paragraph", "leave_placeholder", "meta_commentary"):
        p, _, _ = OPERATORS[name](proposal, rt, random.Random(0))
        assert not OPERATORS[name](p, rt, random.Random(0))[2].applicable
    for name in ("corrupt_reference_metadata", "wrong_doi_on_real_reference"):
        assert not OPERATORS[name](proposal, rt, random.Random(0))[2].applicable
        refs = verdicts(proposal)
        refs[0]["status"] = refs[1]["status"] = "dossier"
        assert not OPERATORS[name](proposal, rt, random.Random(0), references=refs)[2].applicable


def test_length_inadmissible_and_missing_counted_sections(proposal, rt):
    lc = rt.call.length_contract.model_copy(update={"enforcement": "inadmissible"})
    altered = replace(rt, call=rt.call.model_copy(update={"length_contract": lc}))
    _, _, e = OPERATORS["exceed_length"](proposal, altered, random.Random(0))
    assert e.detectors[0].values == ("admissibility.over_length",)
    assert not OPERATORS["exceed_length"]("ordinary words " * 40, rt, random.Random(0))[
        2
    ].applicable


def test_reference_append_before_rule_and_unnumbered(proposal, rt):
    base = proposal.replace("10.1126/sciadv.adt3813", "10.1126/another-work")
    base = base.replace("[1] ", "").replace("[2] ", "") + "\n---\n\nFinal note.\n"
    p, c, e = OPERATORS["fabricated_reference"](base, rt, random.Random(0))
    assert e.applicable
    assert len(parse_references(parse_proposal(p).references_block)) == 3
    assert len(parse_references(parse_proposal(c).references_block)) == 3
    assert p.index(e.details["fabricated_doi"]) < p.index("\n---\n")


def test_numerical_operators_reject_ambiguous_controls(proposal, rt):
    without_citation = proposal.replace(
        "Published telescope observations detected 73 distant galaxies [1].", ""
    )
    assert not OPERATORS["contradict_dossier_number"](without_citation, rt, random.Random(0))[
        2
    ].applicable
    without_fact_context = proposal.replace(rt.dossier.facts[0].text, "Our new target is 11%.")
    assert not OPERATORS["contradict_dossier_number"](without_fact_context, rt, random.Random(0))[
        2
    ].applicable
    budget = proposal.replace("illustrative example cost", "personnel cost")
    assert OPERATORS["budget_over_cap"](budget, rt, random.Random(0))[2].applicable
    nih = Repository().get("pilot-nih-r21-persistence")
    assert not OPERATORS["budget_over_cap"](proposal, nih, random.Random(0))[2].applicable


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))


def result(folder, *, checks=(), score_value=80, item_score=1, claims=(), defects=(), refs=()):
    dump(folder / "checks.json", list(checks))
    dump(folder / "admissibility.json", {"admissible": True, "findings": []})
    dump(folder / "references.json", {"verdicts": list(refs)})
    dump(
        folder / "score.json",
        {
            "scorecard": {
                "score": score_value,
                "quality": score_value,
                "defects": list(defects),
                "components": {"call_responsiveness": score_value},
            },
            "items": [{"item_id": "TRAP-T2", "score": item_score, "status": "scored"}],
            "claims": list(claims),
        },
    )
    return folder


@pytest.mark.parametrize("both,detected,fpr", [(False, True, False), (True, False, True)])
def test_detection_requires_clean_control(tmp_path, both, detected, fpr):
    finding = {"check": "hygiene.placeholder"}
    p = result(tmp_path / "p", checks=[finding])
    c = result(tmp_path / "c", checks=[finding] if both else [])
    e = Expectation(
        "leave_placeholder",
        ("P21",),
        "diagnostic",
        [Detector("placeholder", "check", ("hygiene.placeholder",))],
    )
    d = detect(e, p, c)["detectors"][0]
    assert d["detected"] is detected
    assert d["control_fires"] is fpr


def test_scoped_reference_defect_claim_and_admissibility(tmp_path):
    p, c = result(tmp_path / "p"), result(tmp_path / "c")
    detectors = [
        Detector(
            "ref", "reference", ("misattributed",), ref_index=1, note="doi_points_to_different_work"
        ),
        Detector(
            "defect",
            "defect",
            ("doi_unresolved",),
            target="Invented journal reference",
            control_target="Real journal reference",
        ),
        Detector(
            "claim",
            "claim",
            ("contradicted",),
            "judge",
            target="The applicant observed a nineteen percent improvement.",
            control_target="The applicant observed an eleven percent improvement.",
            severity="critical",
        ),
        Detector("gate", "check", ("admissibility.over_length",)),
    ]
    result(
        p,
        refs=[
            {
                "ref": {"index": 1},
                "status": "misattributed",
                "notes": ["doi_points_to_different_work"],
            }
        ],
        defects=[{"kind": "doi_unresolved", "detail": "Invented journal reference"}],
        claims=[
            {
                "type": "contradicted",
                "severity": "critical",
                "quote": "a nineteen percent improvement",
            }
        ],
    )
    result(
        c,
        refs=[
            {
                "ref": {"index": 0},
                "status": "misattributed",
                "notes": ["doi_points_to_different_work"],
            },
            {"ref": {"index": 1}, "status": "verified"},
        ],
        defects=[{"kind": "doi_unresolved", "detail": "Unrelated old reference"}],
        claims=[{"type": "contradicted", "severity": "critical", "quote": "Other claim"}],
    )
    dump(p / "admissibility.json", {"findings": [{"check": "admissibility.over_length"}]})
    e = Expectation("test", (), "major", detectors)
    assert all(d["detected"] for d in detect(e, p, c)["detectors"])


def test_score_drops_and_invariance(tmp_path):
    b = result(tmp_path / "b")
    c = result(tmp_path / "c")
    p = result(tmp_path / "p", score_value=70, item_score=0)
    detectors = [
        Detector("item", "item_drop", ("TRAP-T2",), "judge"),
        Detector("component", "component_drop", ("call_responsiveness",), "judge"),
        Detector("attack", "score_increase", family="judge", expected=False),
    ]
    e = Expectation("test", (), "major", detectors)
    d = detect(e, p, c, b)
    assert all(r["detected"] for r in d["detectors"])
    assert d["deltas"]["score"] == -10
    assert d["deltas"]["items"]["TRAP-T2"] == -1
    result(p, score_value=90)
    assert detect(e, p, c, b)["detectors"][2]["attack_success"] is True
    assert detect(e, p, c)["detectors"][0]["detected"] is None


def test_g02_ignores_only_deterministic_criterion():
    detector = Detector("G02", "item_change", ("G02",), "judge", exclude_criteria=("d",))

    def data(**criteria):
        return {"score": {"items": [{"item_id": "G02", "criteria": criteria}]}}

    base = data(a="met", b="not_met", c="met", d="not_met")
    assert fires(detector, data(a="met", b="not_met", c="met", d="met"), base) is False
    assert fires(detector, data(a="met", b="met", c="met", d="met"), base) is True
    assert fires(detector, data(a="met", b="abstained", c="met", d="met"), base) is None


def test_missing_stage_and_section_scope():
    d = Detector("plan", "check", ("plan.undefined_wp",), "judge")
    assert fires(d, {"checks": []}) is None
    assert fires(d, {"checks": [], "plan_available": True}) is False
    section = Detector("section", "check", ("structure.missing_section",), section_id="1")
    assert (
        fires(
            section,
            {"checks": [{"check": "structure.missing_section", "data": {"section_id": "2"}}]},
        )
        is False
    )
    assert fires(section, {}) is None


def test_wilson():
    assert wilson(0, 0) is None
    assert wilson(0, 10) == pytest.approx((0.0, 0.2775328))
    assert wilson(10, 10) == pytest.approx((0.7224672, 1.0))
    assert wilson(5, 10) == pytest.approx((0.2365931, 0.7634069))
    with pytest.raises(ValueError):
        wilson(2, 1)


def test_summary_denominators_and_unknown(tmp_path):
    e = Expectation(
        "leave_placeholder",
        ("P21",),
        "diagnostic",
        [Detector("placeholder", "check", ("hygiene.placeholder",))],
    )
    pairs = []
    for n, observed in enumerate([True, False, None]):
        folder = tmp_path / str(n)
        dump(folder / "expectation.json", {"expectation": e.to_dict()})
        pairs.append({"applicable": True, "path": str(n), "operator": e.operator})
        if observed is not None:
            dump(
                folder / "detection.json",
                {
                    "detectors": [
                        {"id": "placeholder", "detected": observed, "control_fires": not observed}
                    ]
                },
            )
    dump(tmp_path / "manifest.json", {"pairs": pairs})
    s = summarize(tmp_path)
    d = s["by_detector"][0]
    assert d["applicable"] == 3 and d["unavailable"] == 1
    assert d["recall"]["rate"] is None
    assert d["observed_recall"]["rate"] == 0.5
    assert d["false_positive_rate"]["rate"] == 0.5
    assert (tmp_path / "summary.md").is_file()


def test_runner_dry_run_no_calls(tmp_path, proposal, rt, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("dry run must not evaluate or load a model panel")

    monkeypatch.setattr("proposalbench.evaluate.evaluate_submission", forbidden)
    monkeypatch.setattr("proposalbench.evaluate.load_panel", forbidden)
    base_folder = tmp_path / "results/pilot/system/pilot" / rt.id / "1"
    base_folder.mkdir(parents=True)
    (base_folder / "evaluated.md").write_text(proposal)
    out = tmp_path / "out"
    summary = run("pilot", out, dry_run=True, results_root=tmp_path / "results")
    assert summary["pairs"] == len(OPERATORS) and summary["applicable"] > 5
    assert not list(out.rglob("score.json"))
    assert not list(out.rglob("meta.json"))
    assert all(d["evaluated"] == 0 for d in summary["by_detector"])
    with pytest.raises(ValueError, match="fresh results"):
        run("pilot", out, dry_run=True, results_root=tmp_path / "results")
    with pytest.raises(ValueError, match="No evaluated"):
        run("missing", tmp_path / "none", dry_run=True, results_root=tmp_path / "results")


def test_runner_copies_metadata_and_uses_fresh_folders(tmp_path, proposal, rt, monkeypatch):
    monkeypatch.setattr("proposalbench.evaluate.load_panel", lambda _: ("test", []))
    monkeypatch.setattr(
        "meta.perturb.run.OPERATORS", {"prompt_injection": OPERATORS["prompt_injection"]}
    )
    seen = []

    def evaluate(task, sub, out, panel, cache):
        assert not (out / "score.json").exists()
        seen.append((sub.meta, out))
        result(out)
        return {}

    monkeypatch.setattr("proposalbench.evaluate.evaluate_submission", evaluate)
    folder = tmp_path / "results/pilot/system/pilot" / rt.id / "1"
    result(folder)
    (folder / "evaluated.md").write_text(proposal)
    meta = SubmissionMeta("system", "revision", rt.id, "pilot", 1, "ok", notes=["original"])
    (folder / "meta.json").write_text(meta.to_json())
    run("pilot", tmp_path / "out", results_root=tmp_path / "results")
    assert [m.system_id for m, _ in seen] == [
        "system+perturb:prompt_injection",
        "system+control:prompt_injection",
    ]
    assert all(m.notes == ["original"] and m.created_at == meta.created_at for m, _ in seen)
    assert seen[0][1] != seen[1][1]


def test_reference_bank_has_provenance():
    records = json.loads((ROOT / "tests/fixtures/perturb/astronomy.json").read_text())
    assert len({r["doi"] for r in records}) == 10
    for r in records:
        assert r["source"].startswith("https://api.crossref.org/works/")
        parsed = parse_references(_ref_line(r))[0]
        assert parsed.title and parsed.authors and parsed.year == r["year"]
        assert parsed.doi == r["doi"].lower()


@pytest.mark.parametrize("enforcement", list(Enforcement))
def test_length_reaches_actual_gate(proposal, rt, monkeypatch, enforcement):
    monkeypatch.setattr("proposalbench.checks.admissibility.detect_language", lambda _: ("en", 1))
    lc = rt.call.length_contract.model_copy(update={"max_words": 1200, "enforcement": enforcement})
    task = replace(rt, call=rt.call.model_copy(update={"length_contract": lc}))
    p, c, e = OPERATORS["exceed_length"](proposal, task, random.Random(0))
    assert e.applicable
    assert e.detectors[0].values[0] in {f.check for f in check_admissibility(p, task.call).findings}
    assert e.detectors[0].values[0] not in {
        f.check for f in check_admissibility(c, task.call).findings
    }


def test_milestone_edits_date_not_identifier(rt):
    for form in (
        "Milestone M2 is due in month 24.",
        "Deliverable D2.1 is the dataset (M24).",
        "| Milestone | Description | Month |\n|---|---|---|\n| M2 | Validated model | 24 |",
    ):
        base = "# Plan\n\nProject duration: 48 months.\n\n" + form
        for seed in range(5):
            p, c, e = OPERATORS["milestone_after_end"](base, rt, random.Random(seed))
            assert e.applicable
            assert "M2" in p or "D2.1" in p
            assert "M2" in c or "D2.1" in c
            assert "24" not in p and "25" in c


def test_plan_findings_read_from_current_evaluator(tmp_path):
    p, c = result(tmp_path / "p"), result(tmp_path / "c")
    dump(p / "factsheet/merged.json", {"findings": [{"check": "plan.undefined_wp"}]})
    dump(c / "factsheet/merged.json", {"findings": []})
    e = Expectation(
        "undefined_work_package",
        ("P15",),
        "major",
        [Detector("plan.undefined_wp", "check", ("plan.undefined_wp",), "judge")],
    )
    assert detect(e, p, c)["detectors"][0]["detected"] is True


def test_individual_judges_and_missing_model_denominator(tmp_path, rt):
    e = Expectation(
        "budget_over_cap",
        ("P04",),
        "major",
        [Detector("TRAP-T2", "item_drop", ("TRAP-T2",), "judge")],
    )
    folders = [result(tmp_path / name) for name in ("p", "c", "b")]
    for folder in folders:
        for model in ("sensitive", "lenient"):
            verdict = "no" if model == "sensitive" and folder.name == "p" else "yes"
            dump(
                folder / "judges" / f"{model}.json",
                {
                    "judge": model,
                    "judgments": [{"item_id": "TRAP-T2", "judge": model, "verdict": verdict}],
                    "calls": [],
                },
            )
            dump(folder / "claims" / f"{model}.json", {"judge": model, "claims": [], "raw": ""})
    d = detect(e, *folders, rt=rt)
    assert d["judges"]["sensitive"]["detectors"][0]["detected"] is True
    assert d["judges"]["lenient"]["detectors"][0]["detected"] is False
    for n in ("one", "two"):
        dump(tmp_path / n / "expectation.json", {"expectation": e.to_dict()})
    dump(tmp_path / "one/detection.json", d)
    dump(tmp_path / "two/detection.json", {"judges": {"lenient": d["judges"]["lenient"]}})
    dump(
        tmp_path / "manifest.json",
        {
            "pairs": [
                {"operator": e.operator, "applicable": True, "path": n} for n in ("one", "two")
            ]
        },
    )
    summary = summarize(tmp_path)
    row = next(r for r in summary["by_detector"] if r["judge"] == "sensitive")
    assert row["applicable"] == 2 and row["unavailable"] == 1


def test_citation_padding_reuses_base_evaluation(tmp_path, proposal, rt, monkeypatch):
    monkeypatch.setattr("proposalbench.evaluate.load_panel", lambda _: ("test", []))
    monkeypatch.setattr(
        "meta.perturb.run.OPERATORS", {"citation_padding": OPERATORS["citation_padding"]}
    )
    seen = []

    def evaluate(task, sub, out, panel, cache):
        seen.append(sub.meta.system_id)
        result(out)
        return {}

    monkeypatch.setattr("proposalbench.evaluate.evaluate_submission", evaluate)
    folder = tmp_path / "results/pilot/system/pilot" / rt.id / "1"
    result(folder)
    (folder / "evaluated.md").write_text(proposal)
    meta = SubmissionMeta("system", "revision", rt.id, "pilot", 1, "ok")
    (folder / "meta.json").write_text(meta.to_json())
    run("pilot", tmp_path / "out", results_root=tmp_path / "results")
    assert seen == ["system+perturb:citation_padding"]


def test_milestone_operator_ignores_task_lines_that_cite_deliverables():
    from meta.perturb.operators import DATED_LINE_RE

    assert DATED_LINE_RE.match("| MS3 | Field season completed | M24 |")
    assert DATED_LINE_RE.match("- D3.2 GHG balance report (M36)")
    assert DATED_LINE_RE.match("**Milestone 2** (month 18): first data release")
    assert not DATED_LINE_RE.match(
        "- T3.2 Life-cycle GHG accounting (M25–M36): combine chamber data ... [D3.2]"
    )


def _section_control_prose():
    sections = []
    for topic in ("Outreach", "Governance", "Training"):
        paragraphs = [
            f"{topic} introduction {i}: " + " ".join(f"detail{j}" for j in range(28)) + "."
            for i in range(4)
        ]
        sections.append(f"## {topic}\n\n" + "\n\n".join(paragraphs))
    return "\n\n".join(sections)


def test_drop_section_balances_whole_paragraphs_and_protects_structure(rt):
    from meta.perturb.operators import _offset, _paragraphs, _span

    required = rt.call.required_sections[0].model_copy(
        update={"id": "1", "title": "Excellence", "core": True, "parent": None}
    )
    task = replace(rt, call=rt.call.model_copy(update={"required_sections": [required]}))
    target = "## 1 Excellence\n\n" + "Detailed objective. " * 33
    base = target + "\n\n" + _section_control_prose() + "\n\n## References\n\n[1] Citation."
    variants = set()
    for seed in range(5):
        p, c, e = OPERATORS["drop_required_section"](base, task, random.Random(seed))
        assert e.applicable, e.reason
        assert "Excellence" not in p and target in c
        parsed = parse_proposal(base)
        assert [s.title for s in parse_proposal(c).sections] == [s.title for s in parsed.sections]
        assert not check_required_sections(parse_proposal(c), task.call.required_sections)
        removed = 0
        touched = 0
        for section in parsed.body_sections():
            a = _offset(base, section.line_start)
            b = _span(parsed, section)[1]
            ps = [m[0] for m in _paragraphs(base) if a <= m.start() < b]
            if ps:
                assert ps[0] in c
                missing = [paragraph for paragraph in ps if paragraph not in c]
                assert len(missing) <= len(ps) // 2
                touched += bool(missing)
                removed += sum(count_words(paragraph) for paragraph in missing)
        assert touched >= 2
        assert 0.75 <= removed / e.details["deleted_words"] <= 1.25
        assert parse_proposal(p).references_block == parse_proposal(c).references_block
        variants.add(c)
    assert len(variants) > 1
    assert not OPERATORS["drop_required_section"](target, task, random.Random(0))[2].applicable
    duplicate = base.replace("## References", "## Excellence\n\nMore discussion.\n\n## References")
    assert not OPERATORS["drop_required_section"](duplicate, task, random.Random(0))[2].applicable


def _numeric_task(rt, value, text="The calibrated probes measured gravimetric moisture precisely."):
    fact = rt.dossier.facts[0].model_copy(update={"value": value, "text": text})
    return replace(rt, dossier=rt.dossier.model_copy(update={"facts": [fact]}))


@pytest.mark.parametrize(
    "value,old,new",
    [
        ("11%", "11%", "17%"),
        ("11 %", "11 %", "17 %"),
        ("23,4", "23.4", "35.1"),
        ("23.4", "23,4", "35,1"),
        ("1,214", "1.214", "1.821"),
        ("1.214", "1,214", "1,821"),
        ("0.028", "0.028", "0.045"),
        ("0.800", "0.800", "1.280"),
        ("7; 23,4", "23,4", "35,1"),
    ],
)
@pytest.mark.parametrize("citation", ["[1]", "(Smith et al., 2021)", "Smith (2021)"])
def test_dossier_numbers_match_paraphrases_and_keep_format(rt, value, old, new, citation):
    task = _numeric_task(rt, value)
    fact_sentence = f"Gravimetric moisture recorded by our calibrated probes was {old}."
    literature = f"Published telescope observations detected 73 distant galaxies {citation}."
    base = f"# Results\n\n{fact_sentence}\n\n{literature}\n\n## References\n\n[1] Work."
    p, c, e = OPERATORS["contradict_dossier_number"](base, task, random.Random(0))
    assert e.applicable, e.reason
    assert fact_sentence.replace(old, new) in p and fact_sentence in c
    assert literature in p and literature not in c
    assert e.detectors[0].target == fact_sentence.replace(old, new)
    assert e.detectors[0].control_target in c
    for variant in (p, c):
        assert parse_proposal(variant).sections
        assert parse_references(parse_proposal(variant).references_block)
    old_control = 73
    changed_control = int(re.search(r"detected (\d+)", c)[1])
    assert abs(changed_control - old_control * e.details["relative_change"]) <= 0.5


@pytest.mark.parametrize(
    "bad",
    [
        "Gravimetric moisture measured by calibrated probes was [11].",
        "Gravimetric moisture measured by calibrated probes: https://doi.org/10.1234/11.",
        "Gravimetric moisture measured by calibrated probes was 111%.",
        "Gravimetric moisture measured by calibrated probes was code11.",
        "Different concepts were reported at 11%.",
        "## References\n\nGravimetric moisture measured by calibrated probes was 11%.",
    ],
)
def test_dossier_number_rejects_unanchored_spans(rt, bad):
    task = _numeric_task(rt, "11%")
    base = "# Results\n\nPublished telescope observations detected 73 galaxies [1].\n\n" + bad
    assert not OPERATORS["contradict_dossier_number"](base, task, random.Random(0))[2].applicable


def test_dossier_rejects_years_shared_control_and_colliding_values(rt):
    for value, control in [
        ("2020", "Published telescope observations detected 73 galaxies [1]."),
        ("11", "Published telescope observations detected 2020 galaxies [1]."),
        ("11", "Calibrated probes measured gravimetric moisture in 73 samples [1]."),
        ("11", "Published telescope observations detected 11 galaxies [1]."),
        ("11", "Published telescope observations detected 73 galaxies."),
    ]:
        task = _numeric_task(rt, value)
        base = (
            f"# Results\n\nCalibrated probes measured gravimetric moisture at {value}.\n\n{control}"
        )
        assert not OPERATORS["contradict_dossier_number"](base, task, random.Random(0))[
            2
        ].applicable
    task = _numeric_task(rt, "10")
    collision = task.dossier.facts[0].model_copy(
        update={"id": "OTHER", "value": "15; 20", "salient": False}
    )
    task = replace(
        task, dossier=task.dossier.model_copy(update={"facts": [*task.dossier.facts, collision]})
    )
    base = (
        "# Results\n\nCalibrated probes measured gravimetric moisture at 10.\n\n"
        "Published telescope observations detected 73 galaxies [1]."
    )
    p, c, e = OPERATORS["contradict_dossier_number"](base, task, random.Random(0))
    assert e.applicable and e.details["replacement"] == "25"
    assert "moisture at 25" in p and "moisture at 10" in c


@pytest.mark.parametrize(
    "line,old,bad,good,cap",
    [
        (
            "Requested EU contribution: EUR 5,940,000",
            "5,940,000",
            "6,900,000",
            "5,643,000",
            6000000,
        ),
        (
            "The total requested budget is strictly capped at **EUR 6.0 million**.",
            "6.0",
            "6.9",
            "5.7",
            6000000,
        ),
        ("*(Total Budget: €6.0M. Estimated effort: 550 PM)*", "6.0", "6.9", "5.7", 6000000),
        ("| **Presupuesto total** | **150 040** |", "150 040", "172 500", "142 538", 150000),
        ("Costes directos solicitados: 124 000 €.", "124 000", "172 500", "117 800", 150000),
        (
            "El importe solicitado es 124\u00a0000 EUR.",
            "124\u00a0000",
            "172\u00a0500",
            "117\u00a0800",
            150000,
        ),
        (
            "Total solicitado: 124\u202f000 euros.",
            "124\u202f000",
            "172\u202f500",
            "117\u202f800",
            150000,
        ),
        ("Presupuesto total: EUR 5,94 millones.", "5,94", "6,90", "5,643", 6000000),
        (
            "Total budget: EUR 5.940.000,00.",
            "5.940.000,00",
            "6.900.000,00",
            "5.643.000,00",
            6000000,
        ),
        (
            "Total budget: 5,940,000.00 EUR.",
            "5,940,000.00",
            "6,900,000.00",
            "5,643,000.00",
            6000000,
        ),
        ("Total costs requested: EUR 124k.", "124", "172.5", "117.8", 150000),
        ("Total direct costs requested: USD 124000.", "124000", "172500", "117800", 150000),
        ("Requested contribution: $124,000.", "124,000", "172,500", "117,800", 150000),
    ],
)
def test_budget_formats(rt, line, old, bad, good, cap):
    currency = "USD" if "USD" in line or "$" in line else "EUR"
    # The supplied 150 040 example exceeds the pilot AEI cap and must be skipped at that cap.
    if old == "150 040":
        base = "# Budget\n\n" + line
        task = replace(
            rt,
            call=rt.call.model_copy(
                update={"eligibility": rt.call.eligibility.model_copy(update={"max_budget": cap})}
            ),
        )
        assert not OPERATORS["budget_over_cap"](base, task, random.Random(0))[2].applicable
        cap = 160000
        bad = "184 000"
    eligibility = rt.call.eligibility.model_copy(update={"max_budget": cap, "currency": currency})
    task = replace(rt, call=rt.call.model_copy(update={"eligibility": eligibility}))
    base = f"# Budget\n\n{line}\n\n## References\n\n[1] Work."
    p, c, e = OPERATORS["budget_over_cap"](base, task, random.Random(0))
    assert e.applicable, e.reason
    assert line.replace(old, bad) in p
    assert line.replace(old, good) in c
    assert bad not in c and e.details["control_total"] <= cap < e.details["replacement"]
    for variant in (p, c):
        assert parse_proposal(variant).sections
        assert parse_references(parse_proposal(variant).references_block)
    from proposalbench.checks.fact_sheet import FactSheet, _budget_checks

    for total, expected in [(e.details["replacement"], True), (e.details["control_total"], False)]:
        sheet = FactSheet(requested_budget=total, budget_currency=currency)
        checks = {f.check for f in _budget_checks(sheet, task.call)}
        assert ("plan.budget_over_cap" in checks) == expected


def test_budget_repeated_totals_and_not_applicable(rt):
    base = (
        "# Budget\n\nTotal budget: €6.0M.\n\n"
        "Requested EU contribution: EUR 6,000,000.\n\nTotal requested: 6.000.000 EUR."
    )
    p, c, e = OPERATORS["budget_over_cap"](base, rt, random.Random(0))
    assert e.applicable and e.details["mentions_changed"] == 3
    assert "€6.9M" in p and "EUR 6,900,000" in p and "6.900.000 EUR" in p
    assert "€5.7M" in c and "EUR 5,700,000" in c and "5.700.000 EUR" in c
    for line in [
        "Total budget: USD 6000000.",
        "Total budget: EUR 6000001.",
        "Total budget: EUR 10000.",
        "A cost estimate is EUR 6000000.",
        "Total budget is discussed here. Other equipment costs EUR 6000000.",
    ]:
        assert not OPERATORS["budget_over_cap"]("# Budget\n\n" + line, rt, random.Random(0))[
            2
        ].applicable


@pytest.mark.parametrize("form", ["M18", "(M18)", "Month 18", "mes 18", "end of month 18"])
@pytest.mark.parametrize("header", [None, "Month", "Due", "Mes", "Fecha"])
def test_milestone_formats_use_fixed_call_duration(rt, form, header):
    eligibility = rt.call.eligibility.model_copy(
        update={"duration_months_min": 36, "duration_months_max": 36}
    )
    task = replace(rt, call=rt.call.model_copy(update={"eligibility": eligibility}))
    line = f"Milestone M2: validation due {form}."
    if header:
        line = f"| ID | Description | {header} |\n|---|---|---|\n| M2 | Validation | {form} |"
    base = "# Plan\n\n" + line
    p, c, e = OPERATORS["milestone_after_end"](base, task, random.Random(0))
    assert e.applicable, e.reason
    assert e.details["duration_source"] == "call"
    assert "M2" in p and "M2" in c and "18" not in p
    assert "19" in c and any(str(n) in p for n in range(37, 43))
    assert parse_proposal(p).sections and parse_proposal(c).sections
    from proposalbench.checks.fact_sheet import Dated, FactSheet, _timeline_checks

    for month, expected in [(int(re.findall(r"\d+", p)[-1]), True), (19, False)]:
        sheet = FactSheet(
            duration_months=36, milestones=[Dated(id="M2", title="Validation", month=month)]
        )
        assert (
            "plan.activity_after_end" in {f.check for f in _timeline_checks(sheet, task.call)}
        ) == expected


def test_milestone_requires_date_not_id_or_task_reference(rt):
    for line in [
        "Milestone M18: validation.",
        "M18: validation.",
        "- T2.1 Test at M18, delivering [D1.1].",
        "Milestone M2 due M90.",
    ]:
        assert not OPERATORS["milestone_after_end"]("# Plan\n\n" + line, rt, random.Random(0))[
            2
        ].applicable


@pytest.mark.parametrize(
    "definition,reference,new",
    [
        ("**WP1: Sampling**", "WP1", "WP9"),
        ("- **WP1: Sampling**", "WP1", "WP9"),
        ("Work Package 1: Sampling", "WP1", "WP9"),
        ("## WP1: Sampling", "Work Package 1", "WP9"),
        ("## Aim 1: Sampling", "Aim 1", "Aim 4"),
        ("## Specific Aim 1: Sampling", "Aim 1", "Aim 4"),
        ("**Aim 1: Sampling**", "Aim 1", "Aim 4"),
        ("**Aim\u202f1: Sampling**", "Aim\u202f1", "Aim 4"),
    ],
)
def test_wp_and_aim_definition_formats(rt, definition, reference, new):
    from proposalbench.checks.fact_sheet import (
        WP_ID_RE,
        FactSheet,
        WorkPackage,
        _timeline_checks,
        _wp_id,
    )

    base = f"# Plan\n\n{definition}\n\nThe analysis depends on {reference} for validation."
    p, c, e = OPERATORS["undefined_work_package"](base, rt, random.Random(0))
    assert e.applicable and e.details["undefined_id"] == new
    assert definition in p and definition not in c
    assert e.details["old_id"] not in c
    assert parse_proposal(p).sections and parse_proposal(c).sections
    assert WP_ID_RE.fullmatch(_wp_id(new))
    for defined, expected in [(e.details["old_id"], True), (new, False)]:
        sheet = FactSheet(
            work_packages=[WorkPackage(id=defined, title="Sampling")],
            referenced_work_packages=[new],
        )
        assert (
            "plan.undefined_wp_extracted" in {f.check for f in _timeline_checks(sheet, rt.call)}
        ) == expected
    # The deduction comes from the text: it fires on the flawed text, not on the control.
    from proposalbench.checks.hygiene import check_undefined_references

    assert check_undefined_references(parse_proposal(p))
    assert not check_undefined_references(parse_proposal(c))


def test_wp_and_aim_require_definition_and_reference(rt):
    for base in [
        "# Plan\n\nWe will use Aim 1.",
        "# Plan\n\n**Aim 1: Sampling**",
        "# Plan\n\n**WP1: Sampling**\n\n**Aim 1: Testing**\n\nWe use Aim 1.",
    ]:
        assert not OPERATORS["undefined_work_package"](base, rt, random.Random(0))[2].applicable


def test_budget_wrapped_sentence_and_language_threshold(rt):
    task = Repository().get("pilot-aei-soledad-close")
    base = (
        "# Budget\n\nLos costes directos solicitados son de 100.000 € o superiores "
        "solo cuando la memoria está en inglés; solicitamos **99.500 euros**.\n\n"
        "Costes directos solicitados:\n124 000 € (menores de 100 000 € según la memoria)."
    )
    for seed in range(5):
        p, c, e = OPERATORS["budget_over_cap"](base, task, random.Random(seed))
        assert e.applicable
        assert e.details["original"] in {99500, 124000}
        assert "100.000 €" in p and "100.000 €" in c
        assert "100 000 €" in p and "100 000 €" in c
    base = "# Budget\n\nRequested EU contribution:\nEUR 6.0 million."
    p, c, e = OPERATORS["budget_over_cap"](base, rt, random.Random(0))
    assert e.applicable and "EUR 6.9 million" in p and "EUR 5.7 million" in c


def test_dossier_does_not_edit_proposed_sample_size(rt):
    task = _numeric_task(rt, "12", "The pilot used twelve independent broth cultures.")
    for sentence in (
        "The feasibility criterion is success with 12 independent cultures.",
        "With 12 independent cultures, simulation suggests adequate power.",
        "We will recruit 12 independent cultures for the experiment.",
    ):
        base = "# Study\n\n" + sentence + "\n\nTelescope observations found 73 galaxies [1]."
        assert not OPERATORS["contradict_dossier_number"](base, task, random.Random(0))[
            2
        ].applicable


def test_dossier_control_keeps_range_order(rt):
    task = _numeric_task(rt, "10")
    base = (
        "# Study\n\nCalibrated probes measured gravimetric moisture at 10.\n\n"
        "Telescope observations found between 73–75 galaxies [1]."
    )
    for seed in range(5):
        p, c, e = OPERATORS["contradict_dossier_number"](base, task, random.Random(seed))
        assert e.applicable and "moisture at 15" in p
        lo, hi = map(int, re.search(r"(\d+)–(\d+)", c).groups())
        assert lo <= hi and "moisture at 10" in c


def test_milestone_inline_date_before_label(rt):
    base = "# Plan\n\n**Month 18 milestone:** Validation complete."
    p, c, e = OPERATORS["milestone_after_end"](base, rt, random.Random(0))
    assert e.applicable and "Month 19 milestone" in c and "Month 18" not in p


@pytest.mark.parametrize("label,range_text", [("Aim ", "Aims 1–2"), ("WP", "WP1–WP2")])
def test_renamed_plan_control_expands_ranges(rt, label, range_text):
    base = (
        f"# Plan\n\n## {label}1: Sampling\n\n## {label}2: Analysis\n\n"
        f"The analysis uses {label}1 and {label}2.\n\n{range_text} contribute data."
    )
    for seed in range(5):
        p, c, e = OPERATORS["undefined_work_package"](base, rt, random.Random(seed))
        assert e.applicable
        assert e.details["old_id"] not in c and range_text not in c
        assert e.details["undefined_id"] in c and e.details["undefined_id"] in p
        assert parse_proposal(p).sections and parse_proposal(c).sections


def test_dossier_detector_retains_personal_title(rt):
    task = _numeric_task(rt, "10")
    sentence = "Dr. Smith's calibrated probes measured gravimetric moisture at 10."
    base = f"# Results\n\n{sentence}\n\nTelescope observations found 73 galaxies [1]."
    p, c, e = OPERATORS["contradict_dossier_number"](base, task, random.Random(0))
    assert e.applicable and e.detectors[0].target == sentence.replace("10", "15")
    assert e.detectors[0].target in p and sentence in c


def test_dossier_cell_line_identifier_is_not_a_numeric_fact(rt):
    task = _numeric_task(
        rt, "authenticated THP-1 cell bank", "Tessivar has authenticated THP-1 cells."
    )
    base = (
        "# Study\n\nTessivar's authenticated THP-1 cells are available.\n\n"
        "Telescope observations found 73 galaxies [1]."
    )
    assert not OPERATORS["contradict_dossier_number"](base, task, random.Random(0))[2].applicable


def test_wp_reference_must_be_prose_not_fenced_diagram(rt):
    base = "# Plan\n\n## WP1: Sampling\n\n```\nWP1 (Sampling)\n```"
    assert not OPERATORS["undefined_work_package"](base, rt, random.Random(0))[2].applicable


INVARIANCE_OPERATORS = (
    "rename_headings",
    "reorder_references",
    "citation_style",
    "markdown_presentation",
    "reparagraph",
)


@pytest.fixture
def invariant_proposal(proposal):
    long = (
        "Field technicians will calibrate the moisture sensors against independently collected "
        "gravimetric measurements before each deployment across the selected agricultural sites. "
        "Laboratory staff will then compare the resulting calibration curves using a predefined "
        "statistical protocol with uncertainty estimates reported for every instrument."
    )
    plan = (
        long + "\n\nRecruitment begins after local approval.\n\n"
        "Participants receive translated instructions.\n\n"
        "**WP3: Validation** combines the sampling and synthesis data.\n\n"
        "The project depends on WP9 for independent auditing.\n\n"
        "* Record *soil* and **water** conditions.\n"
        "* Preserve _temperature_ and __humidity__ measurements.\n\n"
        "1. Obtain written permission.\n2. Archive consent records.\n\n"
        "| Milestone | Due |\n|:---|---:|\n| M2 | 36 |\n| M3 | 54 |\n\n"
        "The instrument design builds on published observations [1; 3-5].\n\n"
        "A separate experiment supplies the calibration method [2].\n\n"
    )
    body = proposal.split("## References")[0].replace(
        "Project duration:", plan + "Project duration:"
    )
    refs = [
        "Zulu, A. (2020). Sensor drift in agricultural fields. Journal of Measurements.",
        "Smith, A., & Jones, B. (2019). Independent calibration of probes. Field Methods.",
        "Chen, A., Lee, B., & Wang, C. (2021). Spatial interpolation of soil data. Soil Science.",
        "Adams, A. (2018). Regional observations of water stress. Water Research.",
        "Baker, A. (2022). Seasonal patterns of plant growth. Plant Science.",
    ]
    return (
        body
        + "## References\n\n"
        + "\n\n".join(f"[{i}] {ref}" for i, ref in enumerate(refs, 1))
        + "\n"
    )


def invariant_findings(text, rt):
    from meta.perturb.run import _finding_key
    from proposalbench.checks.hygiene import check_dates_beyond, check_undefined_references

    parsed = parse_proposal(text)
    return {
        _finding_key(f.to_dict())
        for f in (
            check_hygiene(parsed)
            + check_required_sections(parsed, rt.call.required_sections)
            + check_undefined_references(parsed)
            + check_dates_beyond(parsed, rt.call.eligibility.duration_months_max)
        )
    }


def cited_works(text, per_sentence=None):
    from proposalbench.evidence.verify import ReferenceVerdict, RefStatus
    from proposalbench.judge.support import cited_reference_indices

    parsed = parse_proposal(text)
    refs = parse_references(parsed.references_block or "")
    verdicts = [ReferenceVerdict(r, RefStatus.NOT_FOUND, False) for r in refs]
    indices = cited_reference_indices(parsed.body_text(), verdicts, per_sentence=per_sentence)
    return {(refs[i].title, tuple(refs[i].authors), refs[i].year) for i in indices}


@pytest.mark.parametrize("name", INVARIANCE_OPERATORS)
@pytest.mark.parametrize("author_year", [False, True])
def test_meaning_preserving_operators(name, author_year, invariant_proposal, rt):
    base = invariant_proposal
    if author_year:
        base, _, expectation = OPERATORS["citation_style"](base, rt, random.Random(5))
        assert expectation.applicable, expectation.reason
    if author_year and name == "citation_style":
        assert not OPERATORS[name](base, rt, random.Random(5))[2].applicable
        return
    for seed in (0, 1, 42):
        p, c, e = OPERATORS[name](base, rt, random.Random(seed))
        assert e.applicable, e.reason
        assert p != base and c == base and not e.control_is_base
        assert e.taxonomy == ("invariance",)
        assert e.score_tolerance == 3.0
        assert (p, c, e) == OPERATORS[name](base, rt, random.Random(seed))
        assert invariant_findings(p, rt) == invariant_findings(base, rt)
        assert {"plan.undefined_wp", "plan.activity_after_end"} <= {
            check for check, _ in invariant_findings(p, rt)
        }
        assert len(parse_references(parse_proposal(p).references_block)) == 5
        assert cited_works(p) == cited_works(base)
        assert cited_works(p, per_sentence=3) == cited_works(base, per_sentence=3)
        if name == "citation_style":
            assert {c.kind for c in find_citations(p[: p.index("## References")])} == {
                "author_year"
            }
            assert "(Smith & Jones, 2019)" in p
            assert "Chen et al., 2021" in p
        if name == "markdown_presentation":
            for fragment in ("- Record _soil_ and __water__", "1) Obtain", "|:-----|-----:|"):
                assert fragment in p
            assert "__WP3: Validation__" in p
        if name == "reparagraph":
            assert re.sub(r"\s+", " ", p) == re.sub(r"\s+", " ", base)


@pytest.mark.parametrize("name", INVARIANCE_OPERATORS)
def test_invariance_inapplicable_has_unchanged_control(name, rt):
    base = "Plain text without any editable structure."
    p, c, e = OPERATORS[name](base, rt, random.Random(42))
    assert p == c == base and not e.applicable and e.reason and not e.control_is_base


@pytest.mark.parametrize("name", ["reorder_references", "citation_style"])
@pytest.mark.parametrize("citation", ["[99]", "[1-99]", "[5-3]", "[1, 99]"])
def test_citation_edits_skip_unresolved_labels(name, citation, invariant_proposal, rt):
    base = invariant_proposal.replace("[1; 3-5]", citation)
    assert not OPERATORS[name](base, rt, random.Random(0))[2].applicable


def test_citation_style_skips_missing_metadata_and_disambiguates_years(rt):
    base = (
        "# Study\n\nEvidence comes from experiments [1].\n\n## References\n\n"
        "[1] Anonymous work without author or date.\n\n[2] Other unknown work."
    )
    p, c, e = OPERATORS["citation_style"](base, rt, random.Random(0))
    assert not e.applicable and p == c == base
    from meta.perturb.operators import _citation_indices

    # Same first author and year: the conversion adds a/b and still cites the same work.
    base = (
        "# Study\n\nEvidence comes from experiments [1].\n\n## References\n\n"
        "[1] Smith, A. (2020). First distinct work. Journal.\n\n"
        "[2] Smith, B. (2020). Second distinct work. Journal."
    )
    p, _, e = OPERATORS["citation_style"](base, rt, random.Random(0))
    assert e.applicable and "(Smith, 2020a)" in p
    refs = parse_references(parse_proposal(p).references_block)
    assert [r.title for i, r in enumerate(refs) if i in _citation_indices(p, refs)] == [
        "First distinct work"
    ]


def test_heading_mapping_guard_and_number_punctuation(invariant_proposal, rt, monkeypatch):
    from meta.perturb import operators

    p, _, e = operators.rename_headings(invariant_proposal, rt, random.Random(0))
    assert e.applicable and "### 1.1." in p
    original = operators.map_sections
    calls = 0

    def changed_mapping(parsed, required):
        nonlocal calls
        calls += 1
        mapped = original(parsed, required)
        if calls == 2:
            mapped[0] = replace(mapped[0], section=None)
        return mapped

    monkeypatch.setattr(operators, "map_sections", changed_mapping)
    assert not operators.rename_headings(invariant_proposal, rt, random.Random(0))[2].applicable


def test_presentation_preserves_code_links_and_nested_structure(rt):
    base = (
        "# Example\n\n- **outer**\n  - *inner*\n\n"
        "Literal `**code**` and [a link](https://example.org/a_b) stay intact.\n\n"
        "```markdown\n**WP1**\n\n* unchanged code\n```\n\n"
        "    **indented code**\n"
    )
    p, _, e = OPERATORS["markdown_presentation"](base, rt, random.Random(0))
    assert e.applicable, e.reason
    assert "* __outer__\n  * _inner_" in p
    assert "`**code**`" in p and "https://example.org/a_b" in p
    assert "```markdown\n**WP1**\n\n* unchanged code\n```" in p
    assert "    **indented code**" in p


@pytest.mark.parametrize(
    "separator", ["\n\n## Other\n\n", "\n\n- List item\n\n", "\n\n| A |\n|---|\n| B |\n\n"]
)
def test_reparagraph_never_merges_across_structure(separator, rt):
    long = " ".join(["First sentence describes twenty independently calibrated sensors."] * 4)
    base = (
        "# Study\n\n"
        + long
        + "\n\n## Detail\n\nFirst short paragraph."
        + separator
        + "Second short paragraph."
    )
    assert not OPERATORS["reparagraph"](base, rt, random.Random(0))[2].applicable


def invariance_expectation():
    from meta.perturb.operators import _invariance

    return _invariance("rename_headings", "changed", "base")[2]


def deterministic_result(folder, *, findings=(), score_value=80, item_score=1, **kwargs):
    result(folder, score_value=score_value, item_score=item_score, **kwargs)
    dump(folder / "factsheet/merged.json", {"findings": list(findings)})
    return folder


def test_invariance_detector_facets_and_noise(tmp_path):
    e = invariance_expectation()
    p = deterministic_result(tmp_path / "p", score_value=76, item_score=0.5)
    c = deterministic_result(tmp_path / "c")
    b = deterministic_result(tmp_path / "b", score_value=60)
    d = detect(e, p, c, b)
    facets = d["invariance"]
    assert facets["score"] == {
        "difference": -4,
        "absolute_difference": 4,
        "tolerance": 3.0,
        "changed": True,
    }
    assert facets["findings"]["changed"] is False
    assert facets["items"]["moved"] == {"TRAP-T2": -0.5}
    assert d["control_invariance"]["score"]["difference"] == 20
    assert d["detectors"][1]["detected"] is True
    e.score_tolerance = 4.0
    assert detect(e, p, c)["invariance"]["score"]["changed"] is False
    assert detect(e, p, c)["detectors"][0]["detected"] is True  # no old base required
    p = deterministic_result(p, score_value=84, item_score=0.75)
    assert detect(e, p, c)["invariance"]["items"]["moved"] == {}


def test_invariance_findings_are_location_independent_and_text_only(tmp_path):
    e = invariance_expectation()
    wp = {
        "check": "plan.undefined_wp",
        "location": "**WP9** in a long line",
        "data": {"family": "work package", "id": 9, "highest_defined": 3},
    }
    dated = {
        "check": "plan.activity_after_end",
        "data": {"month": 54, "bound": "call_maximum_text"},
    }
    judged = {"check": "plan.budget_over_cap", "data": {"amount": 999999}}
    section = {
        "check": "structure.uncertain_section",
        "data": {"section_id": "1", "heading": "OLD"},
    }
    refs = [{"status": "verified", "ref": {"index": 0}}]
    p = deterministic_result(
        tmp_path / "p", findings=[wp, dated, judged], refs=refs, checks=[section]
    )
    c = deterministic_result(
        tmp_path / "c",
        findings=[wp | {"location": "new line"}, dated],
        refs=[{"status": "verified", "ref": {"index": 8}}],
        checks=[section | {"data": {"section_id": "1", "heading": "NEW"}}],
    )
    # No judges: quality=None and empty items must not be treated as a score of zero.
    for folder in (p, c):
        dump(folder / "score.json", {"scorecard": {"score": 0, "quality": None}, "items": []})
    d = detect(e, p, c)
    assert d["invariance"]["score"]["changed"] is None
    assert d["invariance"]["items"]["changed"] is None
    assert d["invariance"]["findings"]["changed"] is False
    assert d["detectors"][1]["detected"] is True
    dump(p / "factsheet/merged.json", {"findings": [wp, judged]})
    d = detect(e, p, c)["invariance"]["findings"]
    assert d["changed"] is True and d["removed"][0][0] == "plan.activity_after_end"
    dump(p / "factsheet/merged.json", {"findings": [wp, dated]})
    dump(p / "references.json", {"verdicts": [{"status": "misattributed"}]})
    assert detect(e, p, c)["invariance"]["findings"]["changed"] is True
    (p / "references.json").unlink()
    assert detect(e, p, c)["invariance"]["findings"]["changed"] is None


def test_invariance_admissibility_and_missing_stages(tmp_path):
    e = invariance_expectation()
    p = deterministic_result(tmp_path / "p")
    c = deterministic_result(tmp_path / "c")
    dump(p / "admissibility.json", {"findings": [{"check": "admissibility.over_length"}]})
    assert detect(e, p, c)["invariance"]["findings"]["changed"] is True
    (p / "factsheet/merged.json").unlink()
    assert detect(e, p, c)["invariance"]["findings"]["changed"] is None


def test_invariance_summary_saved_folders(tmp_path):
    e = invariance_expectation()
    pairs = []
    for i, difference in enumerate((-4, 2, None)):
        folder = tmp_path / str(i)
        p = deterministic_result(
            folder / "p", score_value=80 + difference if difference else None, item_score=0.5
        )
        c = deterministic_result(folder / "c")
        if i == 1:
            dump(p / "checks.json", [{"check": "hygiene.placeholder"}])
        dump(folder / "detection.json", detect(e, p, c))
        dump(folder / "expectation.json", {"expectation": e.to_dict()})
        pairs.append({"operator": e.operator, "path": str(i), "applicable": True})
    pairs.append(
        {"operator": "reparagraph", "path": "skip", "applicable": False, "reason": "No prose"}
    )
    dump(tmp_path / "manifest.json", {"pairs": pairs})
    summary = summarize(tmp_path)
    row = summary["invariance"][e.operator]
    assert row["n"] == 3 and row["score_n"] == 2
    assert row["mean_score_difference"] == -1
    assert row["sd_score_difference"] == pytest.approx(18**0.5)
    assert row["over_tolerance"]["rate"] == 0.5
    assert row["over_tolerance"]["unavailable"] == 1
    assert row["finding_changes"]["rate"] == pytest.approx(1 / 3)
    assert row["items_moved_most"] == [
        {"item_id": "TRAP-T2", "count": 3, "observed": 3, "share": 1}
    ]
    assert summary["invariance"]["reparagraph"]["n"] == 0
    assert summary["invariance"]["reparagraph"]["finding_changes"]["rate"] is None
    assert summary["by_operator"] and summary["by_detector"]
    assert "Meaning-preserving invariance" in (tmp_path / "summary.md").read_text()


def test_panel_none_reevaluates_unchanged_controls(tmp_path, invariant_proposal, rt, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("panel none must not load judges")

    monkeypatch.setattr("proposalbench.evaluate.load_panel", forbidden)
    seen = []

    def evaluate(task, submission, folder, panel, cache):
        assert panel == []
        seen.append((submission.proposal, folder))
        deterministic_result(folder, score_value=None)

    monkeypatch.setattr("proposalbench.evaluate.evaluate_submission", evaluate)
    base = tmp_path / "results/pilot/system/pilot" / rt.id / "1"
    base.mkdir(parents=True)
    (base / "evaluated.md").write_text(invariant_proposal)
    (base / "meta.json").write_text(
        SubmissionMeta("system", "rev", rt.id, "pilot", 1, "ok").to_json()
    )
    summary = run(
        "pilot",
        tmp_path / "out",
        panel="none",
        operators=list(INVARIANCE_OPERATORS),
        results_root=tmp_path / "results",
    )
    assert len(seen) == 10
    assert all(text == invariant_proposal for text, folder in seen if folder.name == "control")
    assert all(row["finding_changes"]["rate"] == 0 for row in summary["invariance"].values())
    assert all(row["score_n"] == 0 for row in summary["invariance"].values())


@pytest.mark.parametrize("name", ["reorder_references", "citation_style"])
@pytest.mark.parametrize(
    "extra", ["An unresolved marker [1000].", "Literal `[1]` indexing.", "```python\na[1]\n```"]
)
def test_citation_edits_do_not_modify_unparsed_markers_or_literal_code(
    name, extra, invariant_proposal, rt
):
    base = invariant_proposal.replace("## References", extra + "\n\n## References")
    assert not OPERATORS[name](base, rt, random.Random(0))[2].applicable


def test_reparagraph_preserves_inline_emphasis(rt):
    base = (
        "# Study\n\nThe **field technicians** will calibrate every moisture sensor using "
        "independent measurements before deployment across the agricultural sites. "
        "Laboratory staff will compare the resulting curves with a predefined statistical protocol "
        "and report uncertainty for every instrument.\n\n"
        "Recruitment needs **local approval**.\n\nParticipants receive *translated instructions*."
    )
    p, _, e = OPERATORS["reparagraph"](base, rt, random.Random(0))
    assert e.applicable, e.reason
    assert "sites.\n\nLaboratory" in p
    assert "**local approval**. Participants receive *translated instructions*." in p


@pytest.mark.parametrize("kind", ["bold_heading", "bold_milestone", "bold_date_cell"])
def test_presentation_changes_keep_checks(kind, rt):
    """Regression: underscore and asterisk bold are the same for every check."""
    from proposalbench.checks.hygiene import check_dates_beyond

    if kind == "bold_heading":
        title = rt.call.required_sections[0].title
        base = f"**{title}**\n\nParagraph.\n\n**{title}**\n\nOther paragraph."
        p, _, e = OPERATORS["markdown_presentation"](base, rt, random.Random(0))
        assert e.applicable and p != base
        assert hygiene(base) == hygiene(p)
        required = rt.call.required_sections
        assert [f.check for f in check_required_sections(parse_proposal(base), required)] == [
            f.check for f in check_required_sections(parse_proposal(p), required)
        ]
    else:
        base = (
            "**M1**: M54."
            if kind == "bold_milestone"
            else "| ID | Due |\n|---|---|\n| M1 | **54** |"
        )
        p, _, e = OPERATORS["markdown_presentation"](base, rt, random.Random(0))
        assert e.applicable and p != base
        assert check_dates_beyond(parse_proposal(base), 48)
        assert check_dates_beyond(parse_proposal(p), 48)


def test_reparagraph_keeps_duplicate_finding(rt):
    paragraph = (
        "Field technicians collect carefully calibrated observations at each agricultural site "
        "during the spring growing season using independently validated instruments. "
        "Laboratory scientists compare these observations against archived regional measurements "
        "and publish uncertainty estimates for every treatment group."
    )
    base = (
        f"# Study\n\n{paragraph}\n\n{paragraph}\n\nApproval is documented."
        "\n\nRecruitment follows consent."
    )
    p, _, e = OPERATORS["reparagraph"](base, rt, random.Random(0))
    assert e.applicable and p != base
    assert "hygiene.duplicate_paragraph" in hygiene(base) & hygiene(p)


def test_author_year_suffix_selects_one_reference():
    from meta.perturb.operators import _citation_indices

    refs = parse_references(
        "Smith, A. (2020a). First distinct work. Journal.\n\n"
        "Smith, B. (2020b). Second distinct work. Journal."
    )
    assert _citation_indices("(Smith, 2020a)", refs) == {0}


def test_reference_title_ignores_emphasis_markup():
    a = parse_references(
        "Holland TL. Clinical management of *Staphylococcus aureus* bacteremia. JAMA. 2014."
    )[0]
    b = parse_references(
        "Holland TL. Clinical management of _Staphylococcus aureus_ bacteremia. JAMA. 2014."
    )[0]
    assert a.title == b.title == "Clinical management of Staphylococcus aureus bacteremia"
