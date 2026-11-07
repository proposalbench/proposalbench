"""Checklist items: generic and scheme items from ``rubrics/``, task items from the answer key.

An item is answered in one of two ways:

- *ternary*: one verdict ``yes`` / ``partial`` / ``no`` (or ``na`` / ``cannot_determine``);
  ``evidence`` says which verdicts must be backed by a verbatim quote;
- *criteria*: a list of atomic criteria, each answered ``yes`` / ``no`` / ``na``. A ``yes``
  must quote the proposal. A criterion with ``check`` is computed from deterministic metrics
  and never sent to a judge. The item score is the share of applicable criteria met.

A verdict whose required quotes cannot be found in the proposal is invalid.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from proposalbench.tasks.loader import ResolvedTask
from proposalbench.tasks.schema import MethodProfile, ProposalType

RUBRICS = Path(__file__).resolve().parents[3] / "rubrics"

Component = Literal["call_responsiveness", "substance", "grounding"]
Verdict = Literal["yes", "partial", "no", "na", "cannot_determine"]


class AppliesIf(BaseModel):
    model_config = ConfigDict(extra="forbid")
    method_profile: list[MethodProfile] | None = None
    proposal_type: list[ProposalType] | None = None


class Criterion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    text: str
    # Deterministic check instead of a judge, e.g. "verified_external_references >= 3".
    check: str | None = None
    # Deterministic precondition for a judged criterion: if it fails, the criterion is not met
    # whatever the judges say (e.g. "with citations" needs "external_references >= 1").
    requires: str | None = None


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    component: Component
    question: str
    yes: str = ""
    partial: str = ""
    no: str = ""
    criteria: list[Criterion] = []
    # What the judge reads: call section ids, or roles that each scheme maps to its sections
    # ("objectives", "methods", ...). Both empty = the whole proposal.
    sections: list[str] = []
    roles: list[str] = []
    evidence: list[Literal["yes", "partial", "no"]] = ["yes", "partial"]
    taxonomy: list[str] = Field(default_factory=list)
    applies_if: AppliesIf | None = None

    @model_validator(mode="after")
    def _one_format(self) -> Item:
        if not self.criteria and not (self.yes and self.partial and self.no):
            raise ValueError(f"item {self.id}: give yes/partial/no or criteria")
        ids = [c.id for c in self.criteria]
        if len(set(ids)) != len(ids):
            raise ValueError(f"item {self.id}: duplicate criterion ids")
        return self

    @property
    def judged_criteria(self) -> list[Criterion]:
        return [c for c in self.criteria if c.check is None]

    def applies(self, rt: ResolvedTask) -> bool:
        a = self.applies_if
        if a is None:
            return True
        if a.method_profile and rt.method_profile not in a.method_profile:
            return False
        return not (a.proposal_type and rt.call.proposal_type not in a.proposal_type)


def _yes_no(value):
    """Undo YAML 1.1 booleans: rubric files use the bare words yes/no as keys and values."""
    if value is True:
        return "yes"
    if value is False:
        return "no"
    if isinstance(value, dict):
        return {_yes_no(k): _yes_no(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_yes_no(v) for v in value]
    return value


def _load_yaml(path: Path) -> dict:
    return _yes_no(yaml.safe_load(path.read_text(encoding="utf-8")))


def generic_items() -> list[Item]:
    return [Item.model_validate(i) for i in _load_yaml(RUBRICS / "generic.yaml")["items"]]


def scheme_file(scheme: str) -> Path:
    return RUBRICS / "schemes" / f"{scheme}.yaml"


def scheme_items(scheme: str) -> list[Item]:
    path = scheme_file(scheme)
    return (
        [Item.model_validate(i) for i in _load_yaml(path).get("items", [])]
        if path.is_file()
        else []
    )


def scheme_roles(scheme: str) -> dict[str, list[str]]:
    """Role name -> call section ids for a scheme (``roles:`` in its rubric file)."""
    path = scheme_file(scheme)
    return dict(_load_yaml(path).get("roles", {})) if path.is_file() else {}


def resolve_sections(item: Item, rt: ResolvedTask) -> list[str]:
    """Call section ids the judge should read for ``item``; empty means the whole proposal."""
    roles = scheme_roles(rt.call.scheme.value)
    ids = list(item.sections)
    for role in item.roles:
        ids += [s for s in roles.get(role, []) if s not in ids]
    if item.roles and not ids:
        return []  # role unknown for this scheme: fall back to the whole proposal
    return ids


def section_metric(section_id: str) -> str:
    """Name of the deterministic metric saying whether a required section is present."""
    return "section_present_" + re.sub(r"\W", "_", section_id)


def task_items(rt: ResolvedTask) -> list[Item]:
    """Items generated from the task's answer key (outcomes, scope, exclusions, traps...)."""
    items: list[Item] = []
    for eo in rt.call.expected_outcomes + rt.call.scope:
        kind = "expected outcome" if eo.id.startswith("EO") else "scope element"
        items.append(
            Item(
                id=f"CALL-{eo.id}",
                component="call_responsiveness",
                question=(
                    f"How concretely does the proposal plan the work that would deliver this "
                    f'{kind} of the call?\n{kind.capitalize()}: "{eo.text}"'
                ),
                criteria=[
                    Criterion(
                        id="a",
                        text=(
                            "Names the specific activity, task or work package that produces "
                            "it (restating the call's wording does not count)."
                        ),
                    ),
                    Criterion(id="b", text="Says who carries it out (partner, team or person)."),
                    Criterion(
                        id="c",
                        text="Says when, or which deliverable or milestone will show it is done.",
                    ),
                    Criterion(
                        id="d",
                        text=(
                            "States how achievement will be measured or validated (indicator, "
                            "target, test or acceptance criterion)."
                        ),
                    ),
                ],
                taxonomy=["P01"],
            )
        )
    for ex in rt.call.exclusions:
        items.append(
            Item(
                id=f"CALL-{ex.id}",
                component="call_responsiveness",
                question=(
                    "Does the proposal stay clear of this area that the call excludes?\n"
                    f'Excluded: "{ex.text}"'
                ),
                yes="No planned activity falls in the excluded area.",
                partial="A minor or ambiguous activity touches the excluded area.",
                no=(
                    "The proposal plans work in the excluded area. Quote the passage that "
                    "describes it."
                ),
                evidence=["partial", "no"],
                taxonomy=["P02"],
            )
        )
    for me in rt.call.mandatory_elements:
        items.append(
            Item(
                id=f"CALL-{me.id}",
                component="call_responsiveness",
                question=(
                    "Does the proposal treat this requirement of the call substantively, in a "
                    f'way specific to this project?\nRequirement: "{me.text}"'
                ),
                yes=(
                    "Specific, project-relevant content (what will be done, by whom, how it "
                    "changes the work). Quote it."
                ),
                partial=(
                    "Mentioned in generic or boilerplate terms that would fit any project, or "
                    "only partly covered."
                ),
                no="Absent.",
                taxonomy=["P03"],
            )
        )
    core = [s for s in rt.call.required_sections if s.core]
    if core:
        # Deterministic (no judge): one criterion per core section of the call's template.
        items.append(
            Item(
                id="CALL-ST",
                component="call_responsiveness",
                question="Does the proposal contain every required section of the call's template?",
                criteria=[
                    Criterion(
                        id=re.sub(r"\W", "_", s.id),
                        text=f'Contains the required section {s.id} "{s.title}".',
                        check=f"{section_metric(s.id)} >= 1",
                    )
                    for s in core
                ],
                taxonomy=["P03"],
            )
        )
    for trap in rt.task.traps:
        items.append(
            Item(
                id=f"TRAP-{trap.id}",
                component="call_responsiveness",
                question=(
                    "Does the proposal respect this condition of the call?\n"
                    f"Situation: {trap.description}\nExpected: {trap.expected_behaviour}"
                ),
                yes="The proposal behaves as expected. Quote the passage that shows it.",
                partial="Ambiguous: the proposal neither clearly respects nor clearly breaks it.",
                no="The proposal breaks the condition. Quote the passage that shows it.",
                evidence=["yes", "no"],
                taxonomy=["P04"],
            )
        )
    if rt.task.type == "resubmission" and rt.dossier.reviewer_criticisms:
        items.append(
            Item(
                id="RESUB",
                component="substance",
                question="Does the revised proposal substantively answer each prior criticism?",
                criteria=[
                    Criterion(
                        id=criticism.id,
                        text=(
                            f"Reviewer criticism {criticism.id} of the previous application: "
                            f'"{criticism.text}". The revised proposal resolves it with a '
                            "concrete change to the aims, design or plan, or keeps the original "
                            "approach with a reasoned, evidence-based rebuttal. The change need "
                            "not be labelled as a response. Quote the passage that resolves or "
                            "rebuts it. Restating the criticism or promising to address it does "
                            "not count, nor does a claimed change the narrative does not carry "
                            "out, nor a claim that work was done that the dossier does not show."
                        ),
                    )
                    for criticism in rt.dossier.reviewer_criticisms
                ],
                taxonomy=["P24"],
            )
        )
    if criteria := dossier_grounding_criteria(rt):
        items.append(
            Item(
                id="GR-T",
                component="grounding",
                question=(
                    "Does the proposal keep to what this applicant's dossier establishes, where "
                    "the dossier leaves a fact open, contradicts itself or gives a status?"
                ),
                criteria=criteria,
                taxonomy=["P19", "P22"],
            )
        )
    return items


# A salient fact whose text states a status a proposal could upgrade (pending to secured,
# submitted to accepted, planned to existing).
_STATUS = re.compile(
    r"\b(?:pending|under review|submitted|applied for|requested|not yet|in preparation|"
    r"unsigned|not signed|no signed|awaiting|planned|prospective|pendiente|en revisión|"
    r"solicitad[oa]s?|previst[oa]s?|en trámite|no firmad[oa]s?)\b",
    re.I,
)
MAX_GROUNDING_CRITERIA = 8


def dossier_grounding_criteria(rt: ResolvedTask) -> list[Criterion]:
    """Task-specific grounding criteria from the dossier's hidden key.

    Intentional gaps and inconsistencies first (thin and inconsistent dossiers), then salient
    facts that carry a status (planned, pending, under review). Facts a trap of this task
    already tests are left to the trap item. Every criterion allows ``na`` when the proposal
    does not touch the point, so only what the proposal says is judged.
    """
    out: list[Criterion] = []
    for gap in rt.dossier.gaps:
        out.append(
            Criterion(
                id=gap.id,
                text=(
                    f'The dossier leaves this open: "{gap.text}" Wherever the proposal needs it, '
                    "it does not state a specific value, commitment or date as established: a "
                    "labelled placeholder, an estimate with its basis, or a statement that it is "
                    "still to be determined meets this. Quote the passage. Answer na if the "
                    "proposal does not touch this point."
                ),
            )
        )
    for conflict in rt.dossier.inconsistencies:
        out.append(
            Criterion(
                id=conflict.id,
                text=(
                    f'The dossier\'s documents disagree: "{conflict.text}" Wherever the proposal '
                    "uses this fact, it flags the discrepancy or words it so that neither value is "
                    "presented as settled. Quote the passage. Answer na if the proposal does not "
                    "use this fact."
                ),
            )
        )
    traps = " ".join(f"{t.description} {t.expected_behaviour}" for t in rt.task.traps)
    for fact in rt.dossier.facts:
        if not fact.salient or not (fact.kind == "planned" or _STATUS.search(fact.text)):
            continue
        if fact.value and str(fact.value) in traps:
            continue
        out.append(
            Criterion(
                id=fact.id,
                text=(
                    f'Dossier status: "{fact.text}" If the proposal mentions this, it keeps that '
                    "status: what is planned, pending, requested or under review is not presented "
                    "as existing, secured, approved or accepted. Quote the passage. Answer na if "
                    "the proposal does not mention it."
                ),
            )
        )
    return out[:MAX_GROUNDING_CRITERIA]


def items_for(rt: ResolvedTask) -> list[Item]:
    items = task_items(rt) + scheme_items(rt.call.scheme.value) + generic_items()
    return [i for i in items if i.applies(rt)]
