from proposalbench.checks.admissibility import check_admissibility
from proposalbench.checks.hygiene import check_hygiene, check_required_sections
from proposalbench.parse.sections import count_words, parse_proposal
from proposalbench.tasks.schema import Enforcement

SENTENCE = (
    "The project develops reliable soil monitoring methods for smallholder farms and tests "
    "them in three regions with partner cooperatives. "
)


def proposal(words_per_section: int = 120, refs: bool = True) -> str:
    reps = max(1, words_per_section // 20)
    body = SENTENCE * reps
    doc = (
        "# A test proposal\n\n"
        f"## 1. Excellence\n\n### 1.1 Objectives and ambition\n\n{body}\n\n"
        f"## 2. Impact\n\n{body}\n\n"
        f"## 3. Implementation\n\n{body}\n\n"
    )
    if refs:
        doc += "## References\n\n[1] Smith, J. (2020). Soils. Nature.\n"
    return doc


def test_admissible_within_limit(make_call):
    r = check_admissibility(proposal(), make_call(max_words=2000))
    assert r.admissible
    assert r.language == "en"
    assert r.counted_words < 2000
    assert r.evaluated_text == proposal()


def test_inadmissible_when_over_limit(make_call):
    r = check_admissibility(proposal(400), make_call(max_words=500))
    assert not r.admissible
    assert any(f.check == "admissibility.over_length" for f in r.findings)


def test_tolerance_allows_small_overrun(make_call):
    doc = proposal(200)
    words = check_admissibility(doc, make_call(max_words=10_000)).counted_words
    r = check_admissibility(doc, make_call(max_words=int(words / 1.02)))
    assert r.admissible


def test_disregard_excess_truncates_body_but_keeps_references(make_call):
    doc = proposal(400)
    r = check_admissibility(doc, make_call(max_words=500, enforcement=Enforcement.disregard_excess))
    assert r.admissible
    assert r.truncated_words > 0
    assert "[1] Smith, J. (2020)" in r.evaluated_text
    kept = parse_proposal(r.evaluated_text).body_text()
    assert count_words(kept) <= 500 * 1.03 + 15  # marker sentence + title


def test_wrong_language_is_a_gate(make_call):
    es = (
        "## 1. Excelencia\n\n"
        + "El proyecto desarrolla métodos fiables de seguimiento del suelo para pequeñas "
        "explotaciones y los evalúa en tres regiones con cooperativas socias. " * 20
    )
    r = check_admissibility(es, make_call(max_words=5000))
    assert not r.admissible
    assert r.language == "es"


def test_failed_output_is_a_gate(make_call):
    r = check_admissibility("I'm sorry, I can't help with that.", make_call())
    assert not r.admissible
    assert r.findings[0].check == "admissibility.failed_output"


def test_counted_sections_only(make_call):
    call = make_call(max_words=10_000, counted_sections=["1"])
    r = check_admissibility(proposal(200), call)
    total = check_admissibility(proposal(200), make_call(max_words=10_000)).counted_words
    assert 0 < r.counted_words < total / 2


def test_required_sections_and_order(call):
    p = parse_proposal(proposal())
    assert check_required_sections(p, call.required_sections) == []
    swapped = (
        proposal().replace("## 2. Impact", "## X").replace("## 3. Implementation", "## 2. Impact")
    )
    swapped = swapped.replace("## X", "## 3. Implementation")
    kinds = {
        f.check for f in check_required_sections(parse_proposal(swapped), call.required_sections)
    }
    assert "structure.section_order" in kinds
    missing = proposal().replace("## 2. Impact", "## 2. Outlook")
    found = check_required_sections(parse_proposal(missing), call.required_sections)
    assert [f.data["section_id"] for f in found if f.check == "structure.uncertain_section"] == [
        "2"
    ]
    gone = proposal().replace("## 2. Impact", "## Outlook")
    found = check_required_sections(parse_proposal(gone), call.required_sections)
    assert [f.data["section_id"] for f in found if f.check == "structure.missing_section"] == ["2"]


def test_hygiene_findings():
    para = SENTENCE * 3
    doc = (
        f"## 1. Excellence\n\n{para}\n\n{para}\n\n"
        "Here is the complete proposal you asked for. [[TO COMPLETE: partner]]\n\n"
        "## 1. Excellence\n\nMore.\n"
    )
    checks = [f.check for f in check_hygiene(parse_proposal(doc))]
    assert checks.count("hygiene.duplicate_paragraph") == 1
    assert "hygiene.meta_commentary" in checks
    assert "hygiene.placeholder" in checks
    assert "hygiene.duplicate_heading" in checks


def test_section_over_length_is_a_gate_when_inadmissible(make_call):
    doc = proposal(300)
    lenient = make_call(max_words=50_000, per_section_max_words={"2": 5_000})
    assert check_admissibility(doc, lenient).admissible
    strict = make_call(max_words=50_000, per_section_max_words={"2": 100})
    r = check_admissibility(doc, strict)
    assert not r.admissible
    assert any(
        f.check == "admissibility.section_over_length" and f.kind == "gate" for f in r.findings
    )
    soft = make_call(
        max_words=50_000, enforcement=Enforcement.disregard_excess, per_section_max_words={"2": 100}
    )
    assert check_admissibility(doc, soft).admissible


def test_duplicate_of_a_labelled_paragraph():
    para = (
        "A successful project produces a validated assay with documented performance, a "
        "quantitative estimate of the host-context contribution, and explicit criteria for "
        "deciding whether a larger mechanistic study is justified within the award period."
    )
    md = (
        "# P\n\n## Approach\n\n**Decision criteria and interpretation of negative results**\n"
        f"{para}\n\nOther text that is long enough to be a paragraph of its own here.\n\n{para}\n"
    )
    checks = [f.check for f in check_hygiene(parse_proposal(md))]
    assert checks.count("hygiene.duplicate_paragraph") == 1


def test_undefined_work_package_and_aim_references():
    from proposalbench.checks.hygiene import check_undefined_references

    md = (
        "# P\n\n## Work plan\n\n### WP1: Data\n\nText.\n\n**WP2 - Models** builds on it.\n\n"
        "| WP | Lead |\n|---|---|\n| WP3 | A |\n\n"
        "Results of WP2 feed WP3, and WP9 integrates them. A gap such as WP2 is fine.\n\n"
        "## References\n\n1. Smith J. 2020. Title. Journal.\n"
    )
    found = check_undefined_references(parse_proposal(md))
    assert [(f.data["family"], f.data["id"]) for f in found] == [("work package", 9)]
    aims = "# P\n\n## Specific Aims\n\n**Aim 1.** X.\n\n**Aim 2.** Y.\n\nYear 2 covers Aim 5.\n"
    assert [f.data["id"] for f in check_undefined_references(parse_proposal(aims))] == [5]
    # Nothing is flagged when no identifier of the family is defined.
    assert check_undefined_references(parse_proposal("# P\n\n## A\n\nAs in WP4 of PRIOR.\n")) == []


def test_required_section_item_is_deterministic():
    from proposalbench.evaluate import section_metrics
    from proposalbench.judge.items import items_for
    from proposalbench.tasks.loader import Repository

    repo = Repository()
    rt = repo.load_task(next(d for d in repo.task_dirs() if d.name == "pilot-nih-r21-persistence"))
    item = next(i for i in items_for(rt) if i.id == "CALL-ST")
    assert all(c.check for c in item.criteria)
    missing = [{"check": "structure.missing_section", "data": {"section_id": "innovation"}}]
    metrics = section_metrics(rt.call, missing)
    assert metrics["section_present_innovation"] == 0.0
    assert metrics["section_present_aims"] == 1.0


def test_dates_beyond_the_call_maximum():
    from proposalbench.checks.hygiene import check_dates_beyond

    md = (
        "# P\n\n## Approach\n\n- M1: Trials established (Month 8).\n"
        "- M6 (Month 30): Replication in a second batch.\n\n"
        "M2 macrophages differ from M1 cells in month-long cultures.\n\n"
        "| # | Milestone | Month |\n|---|---|---|\n| MS1 | Data | 12 |\n| MS2 | Final | 27 |\n\n"
        "The 36-month follow-up of the earlier cohort is described elsewhere.\n"
    )
    found = check_dates_beyond(parse_proposal(md), 24)
    assert sorted(f.data["month"] for f in found) == [27, 30]
    assert check_dates_beyond(parse_proposal(md), None) == []
