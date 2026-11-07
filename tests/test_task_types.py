from dataclasses import replace
from pathlib import Path
from runpy import run_path

import pytest
import yaml
from pydantic import ValidationError

from proposalbench.judge.items import items_for, resolve_sections, scheme_items, task_items
from proposalbench.judge.runner import _batches
from proposalbench.tasks.loader import Repository
from proposalbench.tasks.render_instructions import export_bundle
from proposalbench.tasks.schema import CallItem, Dossier, ProposalType, Scheme, Task
from proposalbench.tasks.validate import check_task

# Authoring tools are standalone scripts, not installed modules.
_CHECKER = run_path(str(Path(__file__).resolve().parents[1] / "tools/authoring/check_skeletons.py"))
NAMES, SCHEMES, check = (_CHECKER[key] for key in ("NAMES", "SCHEMES", "check"))


@pytest.mark.parametrize("location", ["call_md", "fixed_items"])
@pytest.mark.parametrize(
    "key,literal",
    [
        (key, literal)
        for key, value in (("max_budget", 100000), ("duration_months_max", 24))
        for literal in _CHECKER["_amounts"](value)
    ],
)
def test_topic_skeleton_rejects_hard_coded_conditions(tmp_path, location, key, literal):
    skeleton = yaml.safe_load((SCHEMES / "foundation_concept.yaml").read_text())
    # Check wrapped prose too; YAML block scalars can preserve line breaks within a value.
    text = "A fixed rule: " + literal.replace(" ", "\n") + "."
    if location == "call_md":
        skeleton["call_md"] = text + "\n" + skeleton["call_md"]
    else:
        skeleton["fixed_items"]["mandatory_elements"].append({"id": "ME5", "text": text})
    path = tmp_path / "foundation_concept.yaml"
    path.write_text(yaml.safe_dump(skeleton))
    with pytest.raises(AssertionError, match=rf"hard-coded eligibility\.{key}"):
        check(path)

    # Explicit fixed rules are permitted, but an exception for the other key is insufficient.
    other_key = "max_budget" if key == "duration_months_max" else "duration_months_max"
    skeleton["fixed_values_in_text"] = {other_key: [skeleton["eligibility"][key]]}
    path.write_text(yaml.safe_dump(skeleton))
    with pytest.raises(AssertionError, match=rf"hard-coded eligibility\.{key}"):
        check(path)
    skeleton["fixed_values_in_text"] = {key: [skeleton["eligibility"][key]]}
    path.write_text(yaml.safe_dump(skeleton))
    check(path)


NEW_SKELETONS = (
    "horizon_stage1",
    "erasmus_ka220",
    "cerv",
    "erc_poc",
    "nsf_career",
    "nih_r21_resubmission",
    "aei_pid_orientada",
    "foundation_concept",
)


@pytest.mark.parametrize("name", ["foundation_concept", "erc_poc"])
@pytest.mark.parametrize("location", ["call_md", *_CHECKER["PREFIXES"]])
@pytest.mark.parametrize("term", ["DOSSIER", "ProposalBench's", "fabricated"])
def test_v2_skeleton_rejects_benchmark_mechanics(tmp_path, name, location, term):
    skeleton = yaml.safe_load((SCHEMES / f"{name}.yaml").read_text())
    if location == "call_md":
        skeleton[location] += f"\n{term}\n"
    else:
        prefix = _CHECKER["PREFIXES"][location]
        items = skeleton["fixed_items"][location]
        items.append({"id": f"{prefix}{len(items) + 1}", "text": term})
    path = tmp_path / f"{name}.yaml"
    path.write_text(yaml.safe_dump(skeleton))
    with pytest.raises(AssertionError, match="benchmark mechanics"):
        check(path)


def test_v2_skeleton_rejects_noncontiguous_fixed_ids(tmp_path):
    skeleton = yaml.safe_load((SCHEMES / "foundation_concept.yaml").read_text())
    skeleton["fixed_items"]["mandatory_elements"][0]["id"] = "ME9"
    path = tmp_path / "foundation_concept.yaml"
    path.write_text(yaml.safe_dump(skeleton))
    with pytest.raises(AssertionError, match="ids must be contiguous"):
        check(path)


@pytest.fixture
def rt():
    repo = Repository()
    return repo.load_task(repo.task_dirs()[0])


@pytest.mark.parametrize("name", NEW_SKELETONS)
def test_new_skeleton_contract_and_rubric(name, rt):
    assert name in NAMES
    path = SCHEMES / f"{name}.yaml"
    call = check(path)  # renders all slots and verifies actual sections/items/canary/word limits
    skeleton = yaml.safe_load(path.read_text())
    assert call.proposal_type.value == skeleton["proposal_type"]
    assert call.provenance.author_family == "openai"
    assert call.provenance.author_model == "gpt-6-astra"
    assert call.length_contract.tolerance == 0
    paired = replace(rt, call=call)
    section_ids = {s.id for s in call.required_sections}
    all_items = items_for(paired)
    assert len({i.id for i in all_items}) == len(all_items)
    for item in all_items:
        assert set(resolve_sections(item, paired)) <= section_ids
    assert 3 <= len(scheme_items(call.scheme.value)) <= 6
    structure = next(i for i in all_items if i.id == "CALL-ST")
    assert len(structure.criteria) == sum(s.core for s in call.required_sections)
    if name == "nih_r21_resubmission":
        assert any(c.id == "introduction" for c in structure.criteria)
        assert call.scheme == Scheme.nih_r21
        assert call.length_contract.per_section_max_words["introduction"] == 600
    if name == "aei_pid_orientada":
        assert call.scheme == Scheme.aei_pid
        assert call.language == "es"
    if name == "foundation_concept":
        assert call.scheme == Scheme.foundation
        assert not skeleton["sources"]
    else:
        assert skeleton["sources"]
        assert all(str(source["verified"]) == "2026-10-31" for source in skeleton["sources"])


def test_resubmission_has_one_atomic_criterion_per_criticism_and_dossier_context(rt):
    criticisms = [
        CallItem(id="R1", text="The sampling frame cannot represent the target population."),
        CallItem(id="R2", text="The comparator cannot distinguish the proposed mechanism."),
    ]
    dossier = rt.dossier.model_copy(update={"reviewer_criticisms": criticisms})
    revised = replace(rt, task=rt.task.model_copy(update={"type": "resubmission"}), dossier=dossier)
    resub = [item for item in items_for(revised) if item.id == "RESUB"]
    assert len(resub) == 1
    item = resub[0]
    assert item.component == "substance" and item.taxonomy == ["P24"]
    assert [c.id for c in item.criteria] == ["R1", "R2"]
    for criticism, criterion in zip(criticisms, item.criteria, strict=True):
        assert criticism.text in criterion.text
        assert "concrete change" in criterion.text
        assert "evidence-based rebuttal" in criterion.text
        assert "Restating" in criterion.text and "does not count" in criterion.text
    assert resolve_sections(item, revised) == []  # both response and revised narrative
    assert _batches(revised, [item]) == [((), True, [item])]
    for task_type in ("full", "stage1", "concept_note"):
        other = replace(revised, task=rt.task.model_copy(update={"type": task_type}))
        assert not any(i.id == "RESUB" for i in task_items(other))
    no_critics = replace(revised, dossier=rt.dossier.model_copy(update={"reviewer_criticisms": []}))
    assert not any(i.id == "RESUB" for i in task_items(no_critics))


@pytest.mark.parametrize("kind", ["stage1", "concept_note"])
@pytest.mark.parametrize("call_type", list(ProposalType))
def test_task_type_requires_matching_proposal_type(rt, kind, call_type):
    data = rt.task.model_dump() | {"type": kind}
    call = rt.call.model_copy(update={"proposal_type": call_type})
    context = {"call": call, "dossier": rt.dossier}
    if kind == call_type.value:
        assert Task.model_validate(data, context=context).type == kind
    else:
        with pytest.raises(ValidationError, match=f"requires proposal_type {kind}"):
            Task.model_validate(data, context=context)


def test_resubmission_requires_review_key_but_is_scheme_independent(rt):
    data = rt.task.model_dump() | {"type": "resubmission"}
    with pytest.raises(ValidationError, match="requires dossier reviewer_criticisms"):
        Task.model_validate(data, context={"dossier": rt.dossier})
    dossier = rt.dossier.model_copy(
        update={"reviewer_criticisms": [CallItem(id="R1", text="Missing validation.")]}
    )
    for scheme in (Scheme.nih_r21, Scheme.horizon_ria):
        call = rt.call.model_copy(update={"scheme": scheme})
        assert Task.model_validate(data, context={"call": call, "dossier": dossier})


@pytest.mark.parametrize(
    "criticisms,match",
    [
        ([{"id": "R1", "text": "A"}, {"id": "R1", "text": "B"}], "duplicate id"),
        ([{"id": "R0", "text": "A"}], "ids must be"),
        ([{"id": "EO1", "text": "A"}], "ids must be"),
        ([{"id": "R1", "text": "  "}], "nonempty text"),
    ],
)
def test_reviewer_criticism_key_validation(rt, criticisms, match):
    with pytest.raises(ValidationError, match=match):
        Dossier.model_validate(rt.dossier.model_dump() | {"reviewer_criticisms": criticisms})


@pytest.mark.parametrize(
    "key,items,match",
    [
        ("gaps", [{"id": "G1", "text": "A"}, {"id": "G1", "text": "B"}], "duplicate id"),
        ("gaps", [{"id": "R1", "text": "A"}], "gap ids must be G1"),
        ("inconsistencies", [{"id": "I0", "text": "A"}], "inconsistency ids must be I1"),
        ("inconsistencies", [{"id": "I1", "text": " "}], "nonempty text"),
    ],
)
def test_gap_and_inconsistency_key_validation(rt, key, items, match):
    with pytest.raises(ValidationError, match=match):
        Dossier.model_validate(rt.dossier.model_dump() | {key: items})


def test_gaps_and_inconsistencies_accepted_and_hidden(rt, tmp_path):
    data = rt.dossier.model_dump() | {
        "gaps": [{"id": "G1", "text": "Sample size of the second cohort is not stated."}],
        "inconsistencies": [{"id": "I1", "text": "CV says 2019, report says 2020."}],
    }
    dossier = Dossier.model_validate(data)
    assert [g.id for g in dossier.gaps] == ["G1"]
    export_bundle(replace(rt, dossier=dossier), tmp_path)
    exported = "\n".join(p.read_text() for p in tmp_path.rglob("*") if p.is_file())
    assert "Sample size of the second cohort" not in exported


@pytest.mark.parametrize("ttype,ok", [("T01", True), ("T14", True), ("T15", False), ("T1", False)])
def test_trap_type_taxonomy(rt, ttype, ok):
    task = rt.task.model_dump()
    task["traps"] = [{"id": "T1", "type": ttype, "description": "d", "expected_behaviour": "e"}]
    if ok:
        assert Task.model_validate(task).traps[0].type == ttype
    else:
        with pytest.raises(ValidationError):
            Task.model_validate(task)


def test_public_trap_types_match_the_audit():
    audit = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "tools/authoring/v1_trap_types.yaml").read_text()
    )
    repo = Repository()
    for tid, types in audit.items():
        assert {t.id: t.type for t in repo.get(tid).task.traps} == types


def test_old_tasks_and_dossiers_keep_defaults(rt):
    task = rt.task.model_dump()
    task.pop("type")
    dossier = rt.dossier.model_dump()
    dossier.pop("reviewer_criticisms")
    assert Task.model_validate(task).type == "full"
    assert Dossier.model_validate(dossier).reviewer_criticisms == []
    with pytest.raises(ValidationError):
        Task.model_validate(task | {"type": "a1"})


@pytest.mark.parametrize("kind", ["resubmission", "stage1", "concept_note"])
def test_repository_and_validator_reject_inconsistent_pairing(tmp_path, rt, kind):
    task = rt.task.model_copy(update={"type": kind})
    bad = replace(
        rt, task=task, call=rt.call.model_copy(update={"proposal_type": ProposalType.full})
    )
    assert any("inconsistent task type" in p.message for p in check_task(bad))
    split = tmp_path / task.split.value
    paths = [
        (split / "tasks" / task.id / "task.yaml", task),
        (split / "calls" / task.call_id / "call.yaml", bad.call),
        (split / "dossiers" / task.dossier_id / "dossier.yaml", bad.dossier),
    ]
    for path, model in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(model.model_dump(mode="json")))
    with pytest.raises(ValidationError):
        Repository(tmp_path).load_task(paths[0][0].parent)


def test_reviewer_answer_key_is_not_exported(tmp_path, rt):
    hidden = "HIDDEN REVIEW KEY SENTINEL"
    dossier = rt.dossier.model_copy(
        update={"reviewer_criticisms": [CallItem(id="R1", text=hidden)]}
    )
    revised = replace(rt, dossier=dossier)
    paths = export_bundle(revised, tmp_path)
    assert paths
    assert all(hidden not in path.read_text() for path in paths)
    assert not list(tmp_path.rglob("*.yaml"))


def _with(rt, *, dossier=None, task=None):
    d = Dossier.model_validate(rt.dossier.model_dump() | (dossier or {}))
    t = Task.model_validate(rt.task.model_dump() | (task or {}))
    return replace(rt, dossier=d, task=t)


def _grounding(rt):
    return next((i for i in task_items(rt) if i.id == "GR-T"), None)


def test_grounding_item_from_gaps_inconsistencies_and_status_facts(rt):
    facts = [f.model_dump() for f in rt.dossier.facts]
    facts[0] |= {"kind": "planned", "salient": True, "text": "Six chambers ordered.", "value": None}
    facts[1] |= {"kind": "existing", "salient": True, "text": "Paper under review.", "value": None}
    for f in facts[2:]:
        f["salient"] = False
    item = _grounding(
        _with(
            rt,
            dossier={
                "facts": facts,
                "gaps": [{"id": "G1", "text": "Cohort size not stated."}],
                "inconsistencies": [{"id": "I1", "text": "84 in report, 96 in log."}],
            },
            task={"traps": []},
        )
    )
    assert item.component == "grounding"
    assert [c.id for c in item.criteria] == ["G1", "I1", facts[0]["id"], facts[1]["id"]]
    assert all("Answer na" in c.text for c in item.criteria)


def test_grounding_item_leaves_trap_facts_to_the_trap_and_caps_criteria(rt):
    facts = [f.model_dump() for f in rt.dossier.facts]
    for n, f in enumerate(facts):
        f |= {"kind": "planned", "salient": True, "value": f"V{n}x"}
    trap = {
        "id": "T1",
        "description": f"Brief calls {facts[0]['value']} existing.",
        "expected_behaviour": "Keep it planned.",
    }
    item = _grounding(_with(rt, dossier={"facts": facts}, task={"traps": [trap]}))
    ids = [c.id for c in item.criteria]
    assert facts[0]["id"] not in ids
    assert len(ids) == min(8, len(facts) - 1)


def test_no_grounding_item_without_open_points(rt):
    facts = [f.model_dump() | {"salient": False} for f in rt.dossier.facts]
    assert _grounding(_with(rt, dossier={"facts": facts})) is None


def test_validation_flags_trap_quotes_missing_from_the_bundle(rt):
    present = " ".join(rt.call_text.split()[:12])
    good = {"id": "T1", "description": f'The call says "{present}".', "expected_behaviour": "e"}
    stale = {
        "id": "T2",
        "description": 'The dossier says "a sentence that appears in no file '
        'of this bundle at all".',
        "expected_behaviour": "e",
    }
    msgs = [p.message for p in check_task(_with(rt, task={"traps": [good, stale]}))]
    assert not any("trap T1 quotes" in m for m in msgs)
    assert any("trap T2 quotes" in m for m in msgs)
