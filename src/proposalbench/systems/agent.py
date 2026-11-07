"""An open, bundle-only proposal writer with retrieval and one critique/revision pass."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

import httpx
from pydantic import BaseModel, Field, ValidationError

from proposalbench.evidence.abstracts import get_work_abstract
from proposalbench.evidence.cache import EvidenceCache
from proposalbench.evidence.http import EvidenceClient, OfflineCacheMiss
from proposalbench.evidence.records import WorkRecord
from proposalbench.evidence.resolvers import crossref, openalex
from proposalbench.llm import InfrastructureError, ModelSpec, complete, parse_json_object
from proposalbench.parse.sections import (
    REFERENCE_HEADINGS,
    count_words,
    normalize_heading,
    parse_proposal,
    strip_tables,
)
from proposalbench.systems.base import ModelUsage, Submission, SubmissionMeta, content_hash
from proposalbench.systems.direct import FILE_BLOCK, MIN_PROPOSAL_CHARS, bundle_files
from proposalbench.tasks.loader import ResolvedTask

SYSTEM_PROMPT = "You write research funding proposals using only the supplied inputs and sources."
PLAN_PROMPT = """PLAN
Read the bundle. Return only JSON with this structure:
{"language": "English", "max_words": 4200, "counted_headings": [], "exempt_tables": false,
 "sections": [{"heading": "Specific Aims", "level": 2, "max_words": 600,
 "word_budget": 540, "points": ["point to make"],
 "requirements": ["short exact quote from call.md"],
 "dossier_facts": ["fact to use"], "dossier_files": ["dossier/cv.md"]}],
 "queries": [{"query": "literature query", "purpose": "what the source must support",
 "sections": ["Specific Aims"]}],
 "dossier_publications": [{"source": "dossier/publications.md",
 "reference": "verbatim complete bibliographic entry from that file"}]}
Extract proposal language, word ceilings, required headings and their order FROM call.md.
Use null for an unstated ceiling. max_words on a section includes its children; word_budget
is for its own prose only. Include parent and child headings in order, levels 2 through 6.
Do not include a proposal title or References in sections. counted_headings is empty when
all narrative counts; otherwise list exactly the headings whose subtrees count toward the
combined ceiling. Set exempt_tables only if the call excludes tables from the overall count.
Budget about 90% of the overall ceiling and respect each section ceiling including children.
Map every expected outcome, scope item, exclusion, mandatory element and award criterion to
sections using short verbatim phrases from call.md. Identify dossier facts and source files.
Give 6-12 literature queries covering state of the art, methods and context, each with its
purpose and relevant section headings. Extract dossier publications verbatim, preserving all
metadata; do not invent or complete metadata. The call takes precedence over the brief.
"""
SELECT_PROMPT = """SELECT
For this query and purpose, select at most three candidates whose title and abstract actually
support the purpose, or none. Do not infer findings absent from the supplied evidence.
Return only JSON: {"selected": ["candidate key", "candidate key"]}.
"""
SECTION_PROMPT = """DRAFT
Write only the requested section's own prose, in the proposal language, within its word budget.
Use the outline, points, call requirements, dossier facts, sources and previous-section summaries.
Do not write its heading, child sections or a reference list; these are assembled separately.
Follow instructions.md. Cite external literature only using the supplied [R1] style keys.
Cite dossier publications only using supplied [D1] style keys; their verbatim metadata will be
listed in References. Never cite another work or invent a key. Use separate keys, e.g. [R1] [R2].
Do not put numeric citations, author-year citations, DOIs or source URLs in the prose.
Return only JSON: {"text": "section prose in Markdown", "summary": "short summary, including
activities, owners, months, measures and budget commitments needed by subsequent sections"}.
"""
CRITIQUE_PROMPT = """CRITIQUE
Review the whole proposal against the bundle and source library. Check every expected outcome
and mandatory element has a concrete activity, owner, timing and measure; scope, exclusions and
award criteria are respected. Check applicant facts against the dossier, distinguishing planned
from existing work/resources. Check brief constraints, with the call taking precedence. Check
months are within duration, work packages are defined, budgets add up and sections are consistent.
Check citations support their claims and use only the library or dossier publications.
Return only JSON: {"issues": [{"heading": "exact outline heading", "issues": ["specific issue"]}]}.
List only sections needing changes; use an empty issues array if no changes are needed.
"""
REVISE_PROMPT = """REVISE
Rewrite only this section to resolve its listed issues in one revision. Keep it consistent with
the whole current proposal and within its budget. Follow the same section output and citation
rules below. Return the complete replacement section, not a patch.
"""
SHORTEN_PROMPT = """SHORTEN
Shorten only this section to at most target_words of its own prose. Preserve concrete activities,
owners, timing, measures, call coverage, dossier facts and supported citations. Do not truncate.
Follow the same section output and citation rules below. Return a complete replacement section.
"""
MAX_LIBRARY = 30
MAX_SELECTED = 3
LENGTH_ROUNDS = 2
BUDGET_FRACTION = 0.9
KEY = re.compile(r"\[([RD]\d+)\]")
# A surname: capitalised, then lower case, so project acronyms with a year are not citations.
_NAME = r"[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ’'][\w’'-]*"
# Reject common unapproved citation forms instead of silently deleting or relabelling them.
# Author-year forms must look like authors: "(Smith, 2020)", "(see Smith et al., 2020; ...)",
# "Smith et al. (2020)", "Smith and Jones (2020)". "Paris Agreement (2015)" is not a citation.
OTHER_CITATION = re.compile(
    r"\[(?:\d+(?:[\s,;–-]+\d+)*|[RD]\d+[^\d\]\n][^\]\n]*)\]"
    r"|10\.\d{4,9}/\S+|https?://\S+"
    rf"|\((?:(?:see|e\.g\.|cf\.),?\s+)?{_NAME}(?:\s+et al\.|\s+(?:and|&)\s+{_NAME})?"
    r",\s*(?:19|20)\d{2}[a-z]?[^()\n]*\)"
    rf"|{_NAME}(?:\s+et al\.|\s+(?:and|&)\s+{_NAME})\s+\((?:19|20)\d{{2}}[a-z]?\)",
)


_MD_HEADING_LINE = re.compile(r"^ {0,3}#{1,6}[ \t]+(.+?)[ \t#]*$", re.MULTILINE)
_BOLD_LINE = re.compile(r"^(\*\*|__)(.+?)\1\s*:?$")
_KEY_GROUP = re.compile(r"\[([RD]\d+(?:\s*[,;]\s*[RD]\d+)+)\]")
_STRAY_BRACKET = re.compile(r"(?<!\[)\[(?!\[)([^\[\]\n]+)\](?![\](])")
_NUMERIC_CITATION = re.compile(r"\s?\[\d+(?:[\s,;–-]+\d+)*\]")


def normalize_section_text(text: str) -> str:
    """Content-preserving fixes applied to every section reply before it is checked.

    Grouped keys are split ([R1, R2] -> [R1] [R2]); a heading or standalone bold line inside
    the prose becomes the bold run-in head of the paragraph after it (a section reply must not
    open sections the outline does not have); other square-bracket remarks become parentheses.
    """
    text = _KEY_GROUP.sub(lambda m: " ".join(f"[{k}]" for k in re.split(r"\s*[,;]\s*", m[1])), text)
    text = _MD_HEADING_LINE.sub(lambda m: f"\n\n**{m[1].strip().strip('*_').strip()}**\n\n", text)
    out: list[str] = []
    heads: list[str] = []
    for block in (b.strip() for b in re.split(r"\n\s*\n", text)):
        if not block:
            continue
        if "\n" not in block and (m := _BOLD_LINE.match(block)):
            heads.append(m[2].strip().rstrip(".:"))
            continue
        if heads:
            head = "**" + ". ".join(heads) + ".**"
            joiner = "\n" if re.match(r"([-*+]|\d+[.)]|\|)\s", block) else " "
            block, heads = head + joiner + block, []
        out.append(block)

    def bracket(m: re.Match) -> str:
        inner = m[1]
        if re.fullmatch(r"[RD]\d+", inner) or re.fullmatch(r"[\d\s,;–-]+", inner):
            return m[0]  # citation keys, and numeric citations (rejected by the check)
        return f"({inner})"

    return _STRAY_BRACKET.sub(bracket, "\n\n".join(out))


class ModelFailure(ValueError):
    """Invalid, empty or refused model output; the sample cannot be completed."""


class AgentInfrastructureError(InfrastructureError):
    """Carry completed-call usage to the runner even when a later dependency fails."""

    def __init__(self, message: str, submission: Submission):
        super().__init__(message)
        self.submission = submission


class SectionPlan(BaseModel):
    heading: str = Field(min_length=1)
    level: int = Field(default=2, ge=2, le=6)
    max_words: int | None = Field(default=None, gt=0)
    word_budget: int = Field(ge=0)
    points: list[str]
    requirements: list[str]
    dossier_facts: list[str]
    dossier_files: list[str]


class Query(BaseModel):
    query: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    sections: list[str]


class DossierPublication(BaseModel):
    source: str
    reference: str = Field(min_length=1)


class Plan(BaseModel):
    language: str = Field(min_length=1)
    max_words: int | None = Field(default=None, gt=0)
    counted_headings: list[str] = Field(default_factory=list)
    exempt_tables: bool = False
    sections: list[SectionPlan] = Field(min_length=1)
    queries: list[Query] = Field(min_length=6, max_length=12)
    dossier_publications: list[DossierPublication] = Field(default_factory=list)


class SectionReply(BaseModel):
    text: str
    summary: str = Field(min_length=1, max_length=3000)


class Selection(BaseModel):
    selected: list[str] = Field(max_length=MAX_SELECTED)


class SectionIssues(BaseModel):
    heading: str
    issues: list[str]


class Critique(BaseModel):
    issues: list[SectionIssues]


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _descendants(plan: Plan, index: int) -> list[int]:
    end = index + 1
    while end < len(plan.sections) and plan.sections[end].level > plan.sections[index].level:
        end += 1
    return list(range(index, end))


def _verbatim(quote: str, text: str) -> bool:
    return " ".join(quote.split()) in " ".join(text.split())


def _paths(plan: Plan) -> list[tuple[str, ...]]:
    """Each section's heading with its ancestors' (calls may repeat a heading under two parts)."""
    paths: list[tuple[str, ...]] = []
    stack: list[tuple[int, str]] = []
    for section in plan.sections:
        while stack and stack[-1][0] >= section.level:
            stack.pop()
        stack.append((section.level, normalize_heading(section.heading)))
        paths.append(tuple(h for _, h in stack))
    return paths


def _plan_problems(plan: Plan) -> list[str]:
    """Structural defects the planner must fix (the plan is asked for again once).

    A reference-list section is not one of them: ``_prepare_plan`` removes it."""
    plan = plan.model_copy(deep=True)
    _drop_reference_sections(plan)
    headings = [s.heading for s in plan.sections]
    problems = []
    paths = _paths(plan)
    if repeated := sorted({" > ".join(p) for p in paths if paths.count(p) > 1}):
        problems.append("duplicate planned headings under the same parent: " + "; ".join(repeated))
    if ambiguous := [h for h in plan.counted_headings if headings.count(h) > 1]:
        problems.append("counted_headings names a repeated heading: " + "; ".join(ambiguous))
    if multiline := [h for h in headings if "\n" in h]:
        problems.append("planned headings span lines: " + " | ".join(map(repr, multiline)))
    if not set(plan.counted_headings) <= set(headings):
        problems.append("counted_headings names a heading that is not in sections")
    return problems


def _drop_reference_sections(plan: Plan) -> list[str]:
    """A planned reference list is removed: References are always assembled from the library."""
    refs = {s.heading for s in plan.sections if REFERENCE_HEADINGS.match(s.heading)}
    if refs and len(refs) < len(plan.sections):
        plan.sections = [s for s in plan.sections if s.heading not in refs]
        plan.counted_headings = [h for h in plan.counted_headings if h not in refs]
        for query in plan.queries:
            query.sections = [h for h in query.sections if h not in refs]
    return [f"reference-list section removed: {h}" for h in sorted(refs)]


def _prepare_plan(plan: Plan, files: dict[str, str]) -> list[str]:
    """Drop unusable optional hints (they only steer drafting); return what was dropped."""
    dropped = _drop_reference_sections(plan)
    if problems := _plan_problems(plan):
        raise ModelFailure("; ".join(problems))
    headings = [s.heading for s in plan.sections]
    for section in plan.sections:
        keep = [q for q in section.requirements if _verbatim(q, files["call.md"])]
        dropped += [
            f"requirement not in call.md: {q[:80]}" for q in section.requirements if q not in keep
        ]
        section.requirements = keep
        keep = [f for f in section.dossier_files if f.startswith("dossier/") and f in files]
        dropped += [f"unknown dossier file: {f}" for f in section.dossier_files if f not in keep]
        section.dossier_files = keep
    for query in plan.queries:
        query.sections = [h for h in query.sections if h in headings]
    keep = [
        pub
        for pub in plan.dossier_publications
        if pub.source.startswith("dossier/") and _verbatim(pub.reference, files.get(pub.source, ""))
    ]
    dropped += [
        f"dossier publication not verbatim: {pub.reference[:80]}"
        for pub in plan.dossier_publications
        if pub not in keep
    ]
    plan.dossier_publications = keep
    # Scale own-prose budgets together within each ceiling, including nested sections.
    groups = []
    if plan.max_words:
        indices = (
            [i for h in plan.counted_headings for i in _descendants(plan, headings.index(h))]
            if plan.counted_headings
            else list(range(len(headings)))
        )
        groups.append((indices, plan.max_words))
    groups += [
        (_descendants(plan, i), s.max_words)
        for i, s in enumerate(plan.sections)
        if s.max_words is not None
    ]
    for indices, limit in groups:
        total = sum(plan.sections[i].word_budget for i in indices)
        target = max(
            0, int(limit * BUDGET_FRACTION) - sum(count_words(headings[i]) for i in indices)
        )
        if total > target:
            for i in set(indices):
                plan.sections[i].word_budget = int(plan.sections[i].word_budget * target / total)
    return dropped


def _reference(work: WorkRecord) -> str:
    return (
        f"{'; '.join(work.authors)} ({work.year}). {work.title}. "
        f"{work.venue}. https://doi.org/{work.doi}"
    )


def assemble(plan: Plan, texts: list[str], references: dict[str, str]) -> str:
    body = "\n\n".join(
        f"{'#' * section.level} {section.heading}\n\n{text}"
        for section, text in zip(plan.sections, texts, strict=True)
    )
    used: list[str] = []

    def number(match: re.Match) -> str:
        key = match[1]
        if key not in references:
            raise ModelFailure(f"citation outside the library: {key}")
        if key not in used:
            used.append(key)
        return f"[{used.index(key) + 1}]"

    body = KEY.sub(number, body)
    entries = [f"[{i}] {references[key]}" for i, key in enumerate(used, 1)]
    return body + "\n\n## References\n\n" + "\n\n".join(entries) + "\n"


def _parsed_sections(plan: Plan, parsed) -> list:
    """The parsed section of each planned section, by position (assembly keeps plan order)."""
    body = parsed.body_sections()
    if len(body) == len(plan.sections) and all(
        normalize_heading(b.title) == normalize_heading(s.heading)
        for b, s in zip(body, plan.sections, strict=True)
    ):
        return body
    first: dict[str, object] = {}
    for b in body:
        first.setdefault(b.title, b)
    return [first[s.heading] for s in plan.sections]


def length_counts(plan: Plan, proposal: str) -> tuple[int, dict[int, int]]:
    """Mirror harness body/subtree counting using only the public contract in the plan.

    Per-section counts are keyed by the section's index in the plan."""
    parsed = parse_proposal(proposal)
    matched = _parsed_sections(plan, parsed)
    headings = [s.heading for s in plan.sections]
    text = parsed.body_text()
    if plan.counted_headings:
        text = "\n\n".join(
            f"{h}\n{parsed.subtree_text(matched[headings.index(h)])}" for h in plan.counted_headings
        )
    if plan.exempt_tables:
        text = strip_tables(text)
    # Harness per-section limits exclude the section's own heading but include child headings
    # and tables, even when tables are exempt from the overall count.
    return count_words(text), {
        i: count_words(parsed.subtree_text(matched[i]))
        for i, s in enumerate(plan.sections)
        if s.max_words is not None
    }


@dataclass
class ReferenceAgent:
    id: str
    spec: ModelSpec
    cache_path: str | Path | None = None
    # OpenAlex's daily quota is per key and shared with the evaluator's reference checks; a
    # run can turn the agent's use of it off so evaluation keeps one source set.
    openalex: bool = True
    _client: EvidenceClient | None = field(default=None, init=False, repr=False)
    _client_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    @property
    def client(self) -> EvidenceClient:
        path = (
            self.cache_path
            or Path(__file__).resolve().parents[3] / "results/pilot/agent-cache.sqlite"
        )
        with self._client_lock:
            if self._client is None:
                off = {} if self.openalex else {"api.openalex.org": "disabled for this system"}
                self._client = EvidenceClient(EvidenceCache(path), disabled=off)
            return self._client

    def close(self) -> None:
        with self._client_lock:
            if self._client is not None:
                self._client.close()
                self._client.cache.close()
                self._client = None

    def version(self) -> str:
        # Includes all prompts, algorithm parameters and model settings. Cache location is storage,
        # not a generation parameter. Record the enabled source set without including credentials.
        return content_hash(
            Path(__file__).read_text(encoding="utf-8"),
            FILE_BLOCK,
            str(MIN_PROPOSAL_CHARS),
            _json(asdict(self.spec)),
            _json({"openalex": self.openalex and bool(os.getenv("OPENALEX_API_KEY"))}),
        )

    def generate(self, task: ResolvedTask, sample: int) -> Submission:
        usage = ModelUsage(self.spec.model_id, self.spec.family)
        # Routing metadata comes from the repository path, never from hidden Task/Call/Dossier.
        meta = SubmissionMeta(
            self.id,
            self.version(),
            task.task_dir.name,
            task.task_dir.parent.parent.name,
            sample,
            "ok",
            models=[usage],
            logs_available=False,
        )
        start = time.monotonic()
        proposal = ""
        trace: dict = {"queries": [], "library": {}, "calls": []}

        def ask(prompt: str, context: dict, schema, check=None, salvage=None):
            """One call; on an invalid reply, one more call told what was wrong.

            If that reply still has problems, SALVAGE may return a usable version of it (or
            None); otherwise the step fails."""
            try:
                result = ask_once(prompt, context, schema)
                problems = check(result) if check else []
            except ModelFailure as exc:
                problems = [str(exc)]
            if not problems:
                return result
            trace.setdefault("repairs", []).append(
                {"step": prompt.splitlines()[0], "problems": problems}
            )
            retry = context | {
                "problems_in_previous_reply": problems,
                "instruction": "Your previous reply had these problems. Reply again, fixing them.",
            }
            result = ask_once(prompt, retry, schema)
            if check and (problems := check(result)):
                if salvage and (kept := salvage(result)) is not None:
                    trace.setdefault("salvaged", []).append(
                        {"step": prompt.splitlines()[0], "problems": problems, **kept}
                    )
                    return result
                raise ModelFailure(f"{prompt.splitlines()[0]}: " + "; ".join(problems))
            return result

        def ask_once(prompt: str, context: dict, schema):
            try:
                reply = complete(
                    self.spec,
                    [{"role": "user", "content": prompt + "\n" + _json(context)}],
                    system=SYSTEM_PROMPT,
                )
            except InfrastructureError:
                raise
            except Exception as exc:
                raise InfrastructureError(f"model transport: {type(exc).__name__}") from exc
            usage.calls += 1
            usage.input_tokens += reply.input_tokens
            usage.output_tokens += reply.output_tokens
            meta.retries += reply.retries
            trace["calls"].append(
                {
                    "step": prompt.splitlines()[0],
                    "stop": reply.stop_reason,
                    "input_tokens": reply.input_tokens,
                    "output_tokens": reply.output_tokens,
                }
            )
            if not reply.text.strip() or reply.stop_reason != "end":
                raise ModelFailure(f"{prompt.splitlines()[0]}: empty, refused or incomplete output")
            try:
                return schema.model_validate(parse_json_object(reply.text))
            except (ValueError, TypeError, ValidationError) as exc:
                raise ModelFailure(f"{prompt.splitlines()[0]}: invalid JSON response") from exc

        try:
            files = dict(bundle_files(task))
            bundle = "\n\n".join(FILE_BLOCK.format(name=n, content=t) for n, t in files.items())
            plan = ask(PLAN_PROMPT, {"bundle": bundle}, Plan, _plan_problems)
            trace["plan_dropped"] = _prepare_plan(plan, files)
            trace["plan"] = plan.model_dump()
            library: dict[str, dict] = {}
            trace["library"] = library
            references = {}
            for i, pub in enumerate(plan.dossier_publications, 1):
                # Strip only the original list marker; preserve the publication metadata verbatim.
                references[f"D{i}"] = re.sub(r"^\s*(?:\d+[.)]|[-*])\s+", "", pub.reference)
            trace["dossier_publications"] = references.copy()
            meta.tools = ["crossref", "abstracts"]
            resolvers = [crossref]
            if self.openalex and os.getenv("OPENALEX_API_KEY"):
                resolvers.append(openalex)
                meta.tools.append("openalex")
            for query in plan.queries:
                candidates: dict[str, WorkRecord] = {}
                counts = {}
                for resolver in resolvers:
                    try:
                        works = resolver.search(query.query, self.client)
                    except (ValueError, KeyError, TypeError) as exc:
                        raise InfrastructureError("malformed search response") from exc
                    counts[resolver.__name__.rsplit(".", 1)[-1]] = len(works)
                    for work in works:
                        if (
                            work.kind in {"journal_article", "review"}
                            and work.doi
                            and work.title
                            and work.authors
                            and work.year
                            and work.venue
                            and (work.doi not in candidates or work.abstract)
                        ):
                            candidates[work.doi] = work
                choices = {}
                for i, work in enumerate(candidates.values(), 1):
                    abstract, _ = get_work_abstract(work, self.client)
                    choices[f"C{i}"] = replace(work, abstract=abstract)
                query_trace = {
                    **query.model_dump(),
                    "retrieved": counts,
                    "eligible": len(choices),
                    "selected": [],
                }
                trace["queries"].append(query_trace)
                try:
                    selected = ask(
                        SELECT_PROMPT,
                        {
                            "query": query.model_dump(),
                            "candidates": {k: asdict(w) for k, w in choices.items()},
                        },
                        Selection,
                    ).selected
                except ModelFailure as exc:
                    # A refused or garbled selection (e.g. a provider content filter on the
                    # abstracts) leaves this query without sources; the proposal goes on.
                    query_trace["skipped"] = str(exc)
                    selected = []
                # Unknown or repeated candidate keys are ignored, never turned into sources.
                selected = [k for k in dict.fromkeys(selected) if k in choices]
                selected_keys = []
                for choice in selected:
                    work = choices[choice]
                    key = next(
                        (k for k, v in library.items() if v["work"]["doi"] == work.doi), None
                    )
                    if key is None:
                        if len(library) >= MAX_LIBRARY:
                            continue
                        key = f"R{len(library) + 1}"
                        library[key] = {"work": asdict(work), "purposes": [], "sections": []}
                        references[key] = _reference(work)
                    entry = library[key]
                    entry["purposes"].append(query.purpose)
                    entry["sections"] = sorted(set(entry["sections"]) | set(query.sections))
                    selected_keys.append(key)
                query_trace["selected"] = selected_keys

            texts: list[str] = []
            summaries: list[str] = []

            def write(index: int, prompt: str, extra: dict) -> SectionReply:
                section = plan.sections[index]
                context = {
                    "outline": plan.model_dump(),
                    "section": section.model_dump(),
                    "instructions": files["instructions.md"],
                    "call": files["call.md"],
                    "brief": files.get("brief.md", ""),
                    "dossier": {f: files[f] for f in section.dossier_files},
                    "library": library,
                    "dossier_publications": trace["dossier_publications"],
                    "previous_summaries": summaries[:index],
                    **extra,
                }

                def problems(reply: SectionReply) -> list[str]:
                    reply.text = normalize_section_text(reply.text)
                    found = []
                    if not reply.text.strip() and section.word_budget:
                        found.append("empty section")
                    if parse_proposal(reply.text).sections:
                        found.append("section reply contains headings; write prose only")
                    if stray := sorted({m[0] for m in OTHER_CITATION.finditer(reply.text)}):
                        found.append(
                            "citations must use only the supplied [R1]/[D1] keys; rewrite: "
                            + " | ".join(stray[:12])
                        )
                    if unknown := [k for k in KEY.findall(reply.text) if k not in references]:
                        found.append(f"unknown citation keys: {', '.join(sorted(set(unknown)))}")
                    bare = re.sub(r"\[\[.*?\]\]", "", reply.text, flags=re.S)
                    if marks := sorted(set(re.findall(r"\[[^\]\n]+\]", KEY.sub("", bare)))):
                        found.append(
                            "square-bracket markers other than citation keys or [[...]]: "
                            + " | ".join(marks[:12])
                        )
                    return found

                def salvage(reply: SectionReply) -> dict | None:
                    """After the repair: keys that resolve to nothing and numeric citations are
                    removed (they would point at no or the wrong reference); author-year
                    citations, DOIs and URLs stay in the text as written, for the evaluator."""
                    unknown = sorted({k for k in KEY.findall(reply.text) if k not in references})
                    reply.text = KEY.sub(lambda m: "" if m[1] in unknown else m[0], reply.text)
                    removed = _NUMERIC_CITATION.findall(reply.text)
                    reply.text = _NUMERIC_CITATION.sub("", reply.text)
                    reply.text = re.sub(r"(?<=\S) +([.,;:])", r"\1", reply.text)
                    left = [p for p in problems(reply) if not p.startswith("citations must")]
                    if left:
                        return None
                    kept = sorted({m[0] for m in OTHER_CITATION.finditer(reply.text)})
                    return {"removed": unknown + [r.strip() for r in removed], "kept": kept}

                return ask(prompt + "\n" + SECTION_PROMPT, context, SectionReply, problems, salvage)

            for i in range(len(plan.sections)):
                reply = write(i, "DRAFT", {})
                texts.append(reply.text)
                summaries.append(reply.summary)
            proposal = assemble(plan, texts, references)
            critique = ask(
                CRITIQUE_PROMPT,
                {
                    "bundle": bundle,
                    "outline": plan.model_dump(),
                    "proposal": proposal,
                    "library": library,
                },
                Critique,
            )
            trace["critique"] = critique.model_dump()
            issues: dict[str, list[str]] = {}
            known = {s.heading for s in plan.sections}
            for issue in critique.issues:
                if issue.heading not in known:
                    # A misnamed section in the critique is skipped, not a failed proposal.
                    # A heading the call repeats under two parts is revised in both.
                    trace.setdefault("ignored_critique", []).append(issue.heading)
                    continue
                issues.setdefault(issue.heading, []).extend(issue.issues)
            for i, section in enumerate(plan.sections):
                if issues.get(section.heading):
                    try:
                        reply = write(
                            i,
                            REVISE_PROMPT,
                            {
                                "issues": issues[section.heading],
                                "current_text": texts[i],
                                "proposal": proposal,
                            },
                        )
                    except ModelFailure as exc:
                        # A revision is an improvement step: the checked draft stands.
                        trace.setdefault("revision_skipped", []).append(str(exc))
                        continue
                    texts[i], summaries[i] = reply.text, reply.summary
                    proposal = assemble(plan, texts, references)

            for _ in range(LENGTH_ROUNDS):
                # Recompute after every edit. Longest own-prose sections are shortened first;
                # a parent's excess can be corrected in its children without rewriting siblings.
                order = sorted(range(len(texts)), key=lambda i: count_words(texts[i]), reverse=True)
                for i in order:
                    total, per_section = length_counts(plan, proposal)
                    reductions = []
                    counted_indices = (
                        {
                            j
                            for h in plan.counted_headings
                            for j in _descendants(plan, [s.heading for s in plan.sections].index(h))
                        }
                        if plan.counted_headings
                        else set(range(len(texts)))
                    )
                    if plan.max_words and total > plan.max_words and i in counted_indices:
                        reductions.append(total - plan.max_words)
                    for j, section in enumerate(plan.sections):
                        if (
                            section.max_words
                            and per_section[j] > section.max_words
                            and i in _descendants(plan, j)
                        ):
                            reductions.append(per_section[j] - section.max_words)
                    if not reductions or not texts[i].strip():
                        continue
                    target = max(0, count_words(texts[i]) - max(reductions) - 5)
                    try:
                        reply = write(
                            i,
                            SHORTEN_PROMPT,
                            {
                                "target_words": target,
                                "current_text": texts[i],
                                "proposal": proposal,
                            },
                        )
                    except ModelFailure as exc:
                        # The length contract decides, as for any over-long proposal.
                        trace.setdefault("revision_skipped", []).append(str(exc))
                        continue
                    texts[i], summaries[i] = reply.text, reply.summary
                    proposal = assemble(plan, texts, references)
            total, per_section = length_counts(plan, proposal)
            trace["length"] = {
                "counted_words": total,
                "sections": {plan.sections[i].heading: n for i, n in per_section.items()},
            }
            if (plan.max_words and total > plan.max_words) or any(
                s.max_words and per_section[i] > s.max_words for i, s in enumerate(plan.sections)
            ):
                # Submitted as is: the harness's length contract decides (truncation or
                # inadmissibility), exactly as for any other system.
                meta.notes.append("stated length limit still exceeded after shortening rounds")
            if len(proposal.strip()) < MIN_PROPOSAL_CHARS:
                raise ModelFailure("no substantive proposal text returned")
        except ModelFailure as exc:
            meta.status = "model_failure"
            meta.notes.append(str(exc))
        except (
            InfrastructureError,
            httpx.HTTPError,
            OfflineCacheMiss,
            OSError,
            sqlite3.Error,
        ) as exc:
            meta.status = "infrastructure_failure"
            message = f"agent dependency: {type(exc).__name__}"
            meta.notes.append(message)
            raise AgentInfrastructureError(message, Submission(proposal, meta)) from exc
        finally:
            meta.wall_time_s = round(time.monotonic() - start, 1)
            meta.notes.append(_json({"agent": trace}))
        return Submission(proposal, meta)
