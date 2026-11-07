"""Schemas for calls, dossiers and tasks.

A task pairs one call with one applicant dossier. Calls and dossiers are defined once
(``call.yaml`` / ``dossier.yaml``) because the public split reuses each of them in two tasks.
The YAML files are the hidden answer key: systems only ever see the exported Markdown bundle.
"""

from __future__ import annotations

import re
from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

SCHEMA_VERSION = 1

# Fictional DOIs for applicants' own (invented) publications use this prefix. It is not a
# registered DOI prefix, so it can never resolve to a real work.
RESERVED_DOI_PREFIX = "10.99999/pb."
# The whole registrant code is unregistered: any DOI under it is fictional, whatever its suffix.
FICTIONAL_DOI_REGISTRANT = "10.99999/"

ID_PATTERN = r"^[a-z0-9][a-z0-9-]*[a-z0-9]$"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Split(StrEnum):
    pilot = "pilot"
    public = "public"
    sealed = "sealed"


class Scheme(StrEnum):
    horizon_ria = "horizon_ria"
    erc_stg = "erc_stg"
    msca_pf = "msca_pf"
    nih_r21 = "nih_r21"
    nsf = "nsf"
    aei_pid = "aei_pid"
    horizon_stage1 = "horizon_stage1"
    erasmus_ka220 = "erasmus_ka220"
    cerv = "cerv"
    erc_poc = "erc_poc"
    nsf_career = "nsf_career"
    foundation = "foundation"


class Enforcement(StrEnum):
    # Evaluators ignore text beyond the limit (Horizon Europe, ERC, MSCA).
    disregard_excess = "disregard_excess"
    # Over-length applications are not reviewed (NIH, NSF, AEI).
    inadmissible = "inadmissible"


class MethodProfile(StrEnum):
    quantitative = "quantitative"
    qualitative = "qualitative"
    theoretical = "theoretical"
    mixed = "mixed"


class FitLevel(StrEnum):
    close = "close"
    stretch = "stretch"
    pivot = "pivot"


class ProposalType(StrEnum):
    full = "full"
    concept_note = "concept_note"
    stage1 = "stage1"


class FactKind(StrEnum):
    existing = "existing"  # true now (a past result, a held grant, an owned instrument)
    planned = "planned"  # promised for the project (a hire, a purchase)


class FactCategory(StrEnum):
    identity = "identity"
    position = "position"
    education = "education"
    publication = "publication"
    grant = "grant"
    award = "award"
    result = "result"
    resource = "resource"
    partner = "partner"
    team = "team"
    budget = "budget"
    other = "other"


class Provenance(Strict):
    author: Literal["human", "llm-assisted"]
    author_family: str  # model family that drafted it, or "human"
    author_model: str | None = None
    created: date
    reviewed_by: str | None = None
    notes: str | None = None


class LengthContract(Strict):
    """What is counted, the limit, and what happens beyond it.

    Word limits are a benchmark adaptation of the scheme's page limit; ``source_note`` says
    where the page limit comes from and how it was converted.
    """

    max_words: int = Field(gt=0)
    enforcement: Enforcement
    tolerance: float = Field(default=0.03, ge=0, le=0.2)
    counted_sections: list[str] | None = None  # RequiredSection ids; None = whole body
    exempt: list[Literal["references", "title", "tables", "abstract", "budget_table"]] = [
        "references",
        "title",
    ]
    per_section_max_words: dict[str, int] = {}
    abstract_max_chars: int | None = None
    page_limit: float | None = None
    words_per_page: int | None = None
    source_note: str


class RequiredSection(Strict):
    id: str
    title: str
    aliases: list[str] = []
    parent: str | None = None
    core: bool = True


class CallItem(Strict):
    id: str
    text: str


class Consortium(Strict):
    min_entities: int | None = None
    min_countries: int | None = None
    notes: str | None = None


class Eligibility(Strict):
    budget_in_narrative: bool
    currency: str = "EUR"
    max_budget: float | None = None
    min_budget: float | None = None
    duration_months_min: int | None = None
    duration_months_max: int | None = None
    trl_start: int | None = Field(default=None, ge=1, le=9)
    trl_end: int | None = Field(default=None, ge=1, le=9)
    consortium: Consortium | None = None

    @model_validator(mode="after")
    def _ranges(self) -> Eligibility:
        if self.min_budget and self.max_budget and self.min_budget > self.max_budget:
            raise ValueError("min_budget exceeds max_budget")
        lo, hi = self.duration_months_min, self.duration_months_max
        if lo and hi and lo > hi:
            raise ValueError("duration_months_min exceeds duration_months_max")
        if self.trl_start and self.trl_end and self.trl_start > self.trl_end:
            raise ValueError("trl_start exceeds trl_end")
        return self


class Call(Strict):
    schema_version: Literal[1] = SCHEMA_VERSION
    id: str = Field(pattern=ID_PATTERN)
    scheme: Scheme
    language: str = Field(pattern=r"^[a-z]{2}$")
    title: str
    topic_code: str
    proposal_type: ProposalType = ProposalType.full
    length_contract: LengthContract
    required_sections: list[RequiredSection]
    expected_outcomes: list[CallItem]
    scope: list[CallItem] = []
    exclusions: list[CallItem] = []
    mandatory_elements: list[CallItem] = []
    eligibility: Eligibility
    provenance: Provenance
    canary: str

    @model_validator(mode="after")
    def _consistency(self) -> Call:
        _unique_ids("required_sections", [s.id for s in self.required_sections])
        items = self.expected_outcomes + self.scope + self.exclusions + self.mandatory_elements
        _unique_ids("call items", [i.id for i in items])
        section_ids = {s.id for s in self.required_sections}
        for s in self.required_sections:
            if s.parent and s.parent not in section_ids:
                raise ValueError(f"section {s.id!r} has unknown parent {s.parent!r}")
        lc = self.length_contract
        for sid in (lc.counted_sections or []) + list(lc.per_section_max_words):
            if sid not in section_ids:
                raise ValueError(f"length contract refers to unknown section {sid!r}")
        if not self.expected_outcomes:
            raise ValueError("a call needs at least one expected outcome")
        return self


class DossierFile(Strict):
    path: str  # relative to the dossier folder; always Markdown
    role: Literal["cv", "prior_project", "publications", "resources", "team", "other"]


class Fact(Strict):
    id: str
    category: FactCategory
    kind: FactKind = FactKind.existing
    text: str
    value: str | float | int | None = None
    salient: bool = False
    source: str  # DossierFile.path that states it


class OwnPublication(Strict):
    key: str
    authors: list[str]
    year: int
    title: str
    venue: str
    doi: str | None = None

    @field_validator("doi")
    @classmethod
    def _reserved_prefix(cls, v: str | None) -> str | None:
        if v is not None and not v.lower().startswith(RESERVED_DOI_PREFIX):
            raise ValueError(f"fictional DOIs must use the reserved prefix {RESERVED_DOI_PREFIX}")
        return v


class Dossier(Strict):
    schema_version: Literal[1] = SCHEMA_VERSION
    id: str = Field(pattern=ID_PATTERN)
    language: str = Field(pattern=r"^[a-z]{2}$")
    applicant_type: Literal["individual", "team", "consortium"]
    career_stage: Literal["phd", "postdoc", "early_career", "mid_career", "senior"]
    disciplines: list[str] = Field(min_length=1)
    method_profile: MethodProfile
    country: str
    files: list[DossierFile] = Field(min_length=1)
    facts: list[Fact] = Field(min_length=1)
    own_publications: list[OwnPublication] = []
    reviewer_criticisms: list[CallItem] = []  # hidden key; report belongs in dossier Markdown
    # Hidden key of the harder dossiers: facts left out on purpose (a proposal should use a
    # labelled placeholder or a justified estimate, never an invented value) and conflicts
    # between dossier documents left in on purpose (a proposal should flag, not pick one).
    gaps: list[CallItem] = []
    inconsistencies: list[CallItem] = []
    provenance: Provenance
    canary: str

    @model_validator(mode="after")
    def _consistency(self) -> Dossier:
        _unique_ids("dossier files", [f.path for f in self.files])
        _unique_ids("facts", [f.id for f in self.facts])
        _unique_ids("own publications", [p.key for p in self.own_publications])
        for what, prefix, items in (
            ("reviewer criticism", "R", self.reviewer_criticisms),
            ("gap", "G", self.gaps),
            ("inconsistency", "I", self.inconsistencies),
        ):
            _unique_ids(f"{what} ids", [c.id for c in items])
            for item in items:
                if not re.fullmatch(rf"{prefix}[1-9]\d*", item.id):
                    raise ValueError(f"{what} ids must be {prefix}1, {prefix}2, ...")
                if not item.text.strip():
                    raise ValueError(f"{what} entries must have nonempty text")
        paths = {f.path for f in self.files}
        for fact in self.facts:
            if fact.source not in paths:
                raise ValueError(f"fact {fact.id} cites unknown dossier file {fact.source!r}")
        return self


class Trap(Strict):
    id: str
    # Taxonomy type T01-T14 (tools/authoring/design_v2.md), for per-type failure rates.
    type: str | None = Field(default=None, pattern=r"^T(0[1-9]|1[0-4])$")
    description: str
    expected_behaviour: str


class Task(Strict):
    schema_version: Literal[1] = SCHEMA_VERSION
    id: str = Field(pattern=ID_PATTERN)
    split: Split
    call_id: str
    dossier_id: str
    type: Literal["full", "stage1", "concept_note", "resubmission"] = "full"
    fit_level: FitLevel
    brief: str | None = None  # file name inside the task folder, e.g. "brief.md"
    method_profile: MethodProfile | None = None  # overrides the dossier's when the call shifts it
    traps: list[Trap] = Field(default=[], max_length=2)
    provenance: Provenance
    canary: str

    @model_validator(mode="after")
    def _task_type(self, info: ValidationInfo) -> Task:
        # Call/dossier are separate files: the loader supplies them once resolved.
        context = info.context or {}
        call = context.get("call")
        dossier = context.get("dossier")
        if (
            self.type in {"stage1", "concept_note"}
            and call is not None
            and call.proposal_type.value != self.type
        ):
            raise ValueError(f"{self.type} task requires proposal_type {self.type}")
        if self.type == "resubmission" and dossier is not None and not dossier.reviewer_criticisms:
            raise ValueError("resubmission task requires dossier reviewer_criticisms")
        return self


def _unique_ids(what: str, ids: list[str]) -> None:
    seen: set[str] = set()
    for i in ids:
        if i in seen:
            raise ValueError(f"duplicate id {i!r} in {what}")
        seen.add(i)


CANARY_RE = re.compile(
    r"^PROPOSALBENCH-CANARY [0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
