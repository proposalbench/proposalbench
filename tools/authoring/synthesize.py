"""Draft public-split calls, dossiers and tasks with author models; validate and render them.

    uv run python tools/authoring/synthesize.py call he-cl5-heatstorage
    uv run python tools/authoring/synthesize.py dossier nordic-dh-consortium
    uv run python tools/authoring/synthesize.py task pub-he-heatstorage-close
    uv run python tools/authoring/synthesize.py review task pub-he-heatstorage-close
    uv run python tools/authoring/synthesize.py revise task pub-he-heatstorage-close

Inputs: ``tools/authoring/public_matrix.yaml`` (the split design), the scheme skeletons in
``tools/authoring/schemes/`` and ``docs/task_review_checklist.md``. Outputs go to
``data/public/{calls,dossiers,tasks}/<id>/``. The author model's JSON, its model id and the
prompt hash are kept in ``tools/authoring/drafts/`` and reviews in ``tools/authoring/reviews/``,
so every task can be traced to the prompts that produced it. Scheme rules (sections, length
contract, award conditions, criteria) come from the skeletons, never from the model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import uuid
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

import yaml
from models import Author, author_complete
from pydantic import ValidationError

from proposalbench.checks.admissibility import detect_language
from proposalbench.llm import parse_json_object
from proposalbench.tasks.schema import Call, Dossier, Task
from proposalbench.tasks.validate import _value_variants

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
# v1 (20 tasks) and v2 (40 more); ids are disjoint, each unit is authored from its own matrix.
MATRICES = (HERE / "public_matrix.yaml", HERE / "public_matrix_v2.yaml")
SCHEMES = HERE / "schemes"
DRAFTS = HERE / "drafts"
REVIEWS = HERE / "reviews"
CHECKLIST = ROOT / "docs" / "task_review_checklist.md"
OUT = ROOT / "data" / "public"
PILOT = ROOT / "data" / "pilot"
MAX_REPAIRS = 2
REVIEWER = {"anthropic": "google", "google": "openai", "openai": "anthropic"}

SYSTEM = """\
You author tasks for ProposalBench, an open benchmark that measures how well AI systems turn
an applicant's prior work (a dossier) into a research proposal for a specific funding call.
Systems receive the call text, the dossier files and the applicant's brief; hidden YAML holds
the answer key (call requirements, the dossier's facts, traps).

Rules for everything you write:
- People, institutions, companies, projects, grants and publications are fictional. Invent
  names that sound real for the country but do not belong to known researchers, universities,
  research institutes, archives, firms, media or public figures (living or historical, including
  writers and politicians); avoid names that a search would confuse with a real one. Real
  places, real funders and real funding schemes, methods, instruments, datasets and scientific
  knowledge are fine and must be accurate for the dates given (a scheme or funder cited for a
  year must have existed that year).
- The benchmark's present date is 1 October 2026. Dossier documents are dated no later than
  September 2026 and describe every status (contracts, grants, submissions, reviews, ethics,
  recruitment) as of then; call deadlines fall after it.
- A person's full name must not belong to a known real researcher, artist or public figure;
  ordinary given names and surnames are fine, distinctive combinations are safest. Institutions,
  companies, projects (including acronyms of real research projects), journals and datasets of
  the applicant are fictional too; the applicant's own publications appear in fictional
  journals.
- Numbers are specific and internally consistent: estimates with uncertainty and sample sizes,
  units, subtotals that add up, percentages that match counts, dates in order, career dates
  that fit the stated stage.
- Write like the real documents (work-programme topic, final report, CV, team description,
  notes from an applicant), never like a benchmark specification. Plain, precise prose; no
  promotional adjectives, no filler.
- Reply with a single JSON object exactly in the requested shape, and nothing else.
"""


# --- small helpers -----------------------------------------------------------------------


class _Dumper(yaml.SafeDumper):
    pass


def _str(dumper: yaml.SafeDumper, value: str):
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Dumper.add_representer(str, _str)


def dump_yaml(data: dict) -> str:
    return yaml.dump(data, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100)


def matrices() -> list[dict]:
    return [yaml.safe_load(p.read_text(encoding="utf-8")) for p in MATRICES if p.is_file()]


def matrix_of(kind: str, uid: str) -> dict:
    for m in matrices():
        if any(e["id"] == uid for e in m[kind]):
            return m
    raise SystemExit(f"{uid} is not a {kind[:-1]} in {', '.join(p.name for p in MATRICES)}")


def entry(kind: str, uid: str) -> dict:
    return next(e for e in matrix_of(kind, uid)[kind] if e["id"] == uid)


def author(family: str, m: dict | None = None) -> Author:
    m = m or matrices()[-1]
    return Author.from_matrix(family, m["families"][family])


def unit_author(kind: str, uid: str, family: str) -> Author:
    """The author of ``family`` as configured in the matrix that designs this unit."""
    return author(family, matrix_of(kind, uid))


TRAP_TYPES = {
    "T01": "budget beyond the call's limits",
    "T02": "duration or phases beyond the call",
    "T03": "applicant eligibility",
    "T04": "consortium rules",
    "T05": "excluded activity",
    "T06": "pending presented as secured",
    "T07": "planned presented as existing",
    "T08": "overstated track record or collaboration",
    "T09": "missing mandatory element or template section",
    "T10": "data integrity (uncertainty dropped, number changed, cherry-picked subgroup)",
    "T11": "scope drift",
    "T12": "silent dossier fact (only the dossier states it; the brief never mentions it)",
    "T13": "reviewer criticism not addressed (resubmissions)",
    "T14": "ethics, data protection or regulatory status",
}


def trap_lines(traps) -> str:
    """Matrix traps as prompt text: v1 free text, v2 a list of {type, idea}."""
    if isinstance(traps, str) or not traps:
        return str(traps or "none")
    return "\n".join(
        f"  - {t['type']} ({TRAP_TYPES[t['type']]}): {' '.join(t['idea'].split())}" for t in traps
    )


def trap_types(spec: dict) -> list[str]:
    traps = spec.get("traps")
    return [t["type"] for t in traps] if isinstance(traps, list) else []


def skeleton(call: dict) -> dict:
    name = call.get("skeleton", call["scheme"])
    return yaml.safe_load((SCHEMES / f"{name}.yaml").read_text(encoding="utf-8"))


def canary() -> str:
    return f"PROPOSALBENCH-CANARY {uuid.uuid4()}"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def provenance(a: Author, notes: str | None = None) -> dict:
    p = {
        "author": "llm-assisted",
        "author_family": a.family,
        "author_model": a.model,
        "created": date.today().isoformat(),
    }
    return p | ({"notes": notes} if notes else {})


def draft_path(kind: str, uid: str) -> Path:
    return DRAFTS / f"{kind}-{uid}.json"


def save_draft(kind: str, uid: str, a: Author, prompt: str, draft: dict, history=None) -> None:
    DRAFTS.mkdir(parents=True, exist_ok=True)
    record = {
        "kind": kind,
        "id": uid,
        "family": a.family,
        "model": a.model,
        "created": date.today().isoformat(),
        "prompt_sha256": sha(SYSTEM + prompt),
        "draft": draft,
        "history": history or [],
    }
    draft_path(kind, uid).write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def parse_reply(text: str) -> dict:
    """The author's JSON, also when it arrives as consecutive objects (e.g. the revised unit
    followed by a separate {"rejected": [...]}): disjoint objects are merged, otherwise the
    largest one is taken."""
    try:
        return parse_json_object(text)
    except ValueError:
        pass
    decoder, found, i = json.JSONDecoder(), [], text.find("{")
    while i != -1:
        try:
            obj, end = decoder.raw_decode(text, i)
        except ValueError:
            i = text.find("{", i + 1)
            continue
        if isinstance(obj, dict):
            found.append((obj, end - i))
        i = text.find("{", end)
    if not found:
        raise ValueError("no JSON object in the reply")
    keys = [set(o) for o, _ in found]
    if sum(map(len, keys)) == len(set().union(*keys)):
        return {k: v for o, _ in found for k, v in o.items()}
    return max(found, key=lambda x: x[1])[0]


def _keep_unparsed(reply: str) -> None:
    """A long generation that fails to parse is kept for inspection, not lost."""
    folder = ROOT / ".work" / "unparsed-replies"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{uuid.uuid4().hex[:12]}.txt").write_text(reply, encoding="utf-8")


def ask_json(a: Author, prompt: str) -> dict:
    reply = author_complete(a, SYSTEM, prompt)
    try:
        return parse_reply(reply)
    except ValueError:
        _keep_unparsed(reply)
        reply = author_complete(
            a,
            SYSTEM,
            prompt + "\n\nYour previous reply was not one valid JSON object. Reply "
            "with the JSON object only.",
        )
        try:
            return parse_reply(reply)
        except ValueError:
            _keep_unparsed(reply)
            raise


def bullets(items: list[dict]) -> str:
    return "\n".join(f"- {i['text']}" for i in items) if items else "- None."


def fmt_int(n: float, language: str) -> str:
    s = f"{int(n):,}"
    return s.replace(",", ".") if language == "es" else s


def repair_loop(a: Author, prompt: str, draft: dict, check) -> tuple[dict, list[dict]]:
    """Ask the author to fix validation errors; return the final draft and the history."""
    history = []
    for _ in range(MAX_REPAIRS):
        errors = check(draft)
        if not errors:
            return draft, history
        history.append({"draft": draft, "errors": errors})
        draft = ask_json(
            a,
            prompt
            + "\n\nYour previous JSON is below. It failed these checks:\n- "
            + "\n- ".join(errors)
            + "\n\nReturn the complete corrected JSON object (same shape), changing only what "
            "the checks require.\n\nPREVIOUS JSON:\n" + json.dumps(draft, ensure_ascii=False),
        )
    errors = check(draft)
    if errors:
        raise SystemExit("still failing after repairs:\n- " + "\n- ".join(errors))
    return draft, history


# --- calls -------------------------------------------------------------------------------

CALL_SHAPE = """\
{
  "title": "topic title (one line)",
  "expected_outcomes_intro": "one Markdown paragraph framing the expected outcomes",
  "expected_outcomes": ["outcome 1", "outcome 2", "..."],
  "scope_intro": "one or two Markdown paragraphs: the problem and what proposals should do",
  "scope": ["activity proposals should address", "..."],
  "exclusions": ["one out-of-scope item", "..."],
  "mandatory_elements": ["topic-specific condition", "..."],
  "conditions": {"max_budget": 0, "duration_months_max": 0, "trl_start": null,
                 "trl_end": null, "expected_projects": 0}
}"""


def call_prompt(spec: dict, skel: dict) -> str:
    fixed = skel.get("fixed_items", {})
    return f"""\
Write the topic of a fictional funding call of scheme {skel["scheme"]} for ProposalBench.

Theme to develop (from the benchmark design):
{spec["theme"]}

Scheme rules and guidance:
{skel.get("author_notes", "")}

Items every call of this scheme already has (do not repeat them):
{json.dumps(fixed, ensure_ascii=False, indent=1)}

The call text frame your content is inserted into (slots in double braces):
-----
{skel["call_md"]}
-----

Write it the way the funder writes real topics. Expected outcomes say what will be different
and for whom once projects succeed (outcome statements, not technical specifications). Scope
items each name one activity proposals should carry out, in at most 35 words. Do not set
numeric thresholds (sample sizes, capacities, percentage targets) unless such funders really
set them, e.g. "at least three pilot sites". Each item must still be checkable: a reviewer
reading a proposal can tell whether it is addressed. Exclusions are realistic things an
applicant might be tempted to propose. Mandatory elements must not restate the award
conditions (budget, duration, TRL), which appear in the header. Write in language
"{skel["language"]}".

Award conditions (fixed; copy them into "conditions" unchanged, use null for the rest):
{json.dumps(spec.get("conditions", {}))}

Reply with JSON of this shape:
{CALL_SHAPE}
"""


def duration_row(elig: dict) -> tuple[str, str]:
    """State every duration rule the hidden eligibility holds (minimum too, exact if equal)."""
    lo, hi = elig.get("duration_months_min"), elig["duration_months_max"]
    if lo and lo == hi:
        return ("Duration", f"{hi} months")
    if lo:
        return ("Duration", f"{lo} to {hi} months")
    return ("Maximum duration", f"{hi} months")


def header_table(scheme: str, elig: dict, cond: dict, language: str) -> str:
    cur = elig.get("currency", "EUR")
    rows: list[tuple[str, str]] = []
    if scheme in ("horizon_ria", "horizon_stage1"):
        action = "Research and Innovation Action (RIA), actual costs"
        if scheme == "horizon_stage1":
            action += "; two-stage submission, this is the first stage"
        rows.append(("Type of action", action))
        if elig.get("max_budget"):
            rows.append(
                (
                    "EU contribution per project",
                    f"up to {cur} {elig['max_budget'] / 1e6:.1f} million",
                )
            )
        if cond.get("expected_projects"):
            rows.append(("Expected number of projects", str(cond["expected_projects"])))
        if elig.get("duration_months_max"):
            rows.append(duration_row(elig))
        if elig.get("trl_start") and elig.get("trl_end"):
            rows.append(
                (
                    "Technology readiness",
                    f"activities are expected to start at TRL {elig['trl_start']} and reach TRL "
                    f"{elig['trl_end']} by the end of the project",
                )
            )
        if elig.get("consortium", {}).get("notes"):
            rows.append(("Eligibility", elig["consortium"]["notes"].strip()))
    else:
        if elig.get("max_budget"):
            rows.append(("Maximum award", f"{cur} {fmt_int(elig['max_budget'], language)}"))
        if elig.get("duration_months_max"):
            rows.append(duration_row(elig))
        if cond.get("expected_projects"):
            rows.append(("Expected number of awards", str(cond["expected_projects"])))
    return "| | |\n|---|---|\n" + "\n".join(f"| {k} | {v} |" for k, v in rows)


def _amounts(value: float) -> list[str]:
    """Ways a call text writes an amount or a count, to detect hard-coded values."""
    n = int(value)
    if n < 1000:
        return [f"{n} months", f"{n}-month", f"–{n} months", f"-{n} months"]
    return [f"{n:,}", f"{n:,}".replace(",", "."), f"{n:,}".replace(",", " "), str(n)]


def _repeats(text: str, fixed: list[dict]) -> bool:
    """A topic item that restates a fixed item (authors are told not to; some still do)."""
    norm = " ".join(re.findall(r"\w+", text.casefold()))
    return any(
        SequenceMatcher(None, norm, " ".join(re.findall(r"\w+", f["text"].casefold()))).ratio()
        >= 0.85
        for f in fixed
    )


def numbered(prefix: str, fixed: list[dict], extra: list[str]) -> list[dict]:
    items = [dict(i) for i in fixed]
    used = {i["id"] for i in items}
    n = 1
    for text in extra:
        if isinstance(text, dict):  # some models return {"id": ..., "text": ...} items
            text = text.get("text") or " ".join(str(v) for v in text.values())
        text = re.sub(r"^\s*(?:EO|SC|EX|ME)\d+\s*[:.)\-–]\s*", "", text)
        if _repeats(text, items):
            continue
        while f"{prefix}{n}" in used:
            n += 1
        items.append({"id": f"{prefix}{n}", "text": text.strip()})
        used.add(f"{prefix}{n}")
    return items


def render_call(spec: dict, skel: dict, content: dict, a: Author, can: str) -> tuple[dict, str]:
    fixed = skel.get("fixed_items", {})
    # Authors echo the shape's placeholder zeros for conditions the design leaves open; a zero
    # must never override the skeleton's eligibility.
    cond = {k: v for k, v in (content.get("conditions") or {}).items() if v not in (0, "0")}
    elig = dict(skel["eligibility"])
    cond = cond | spec.get("conditions", {})  # the design's conditions win: traps rely on them
    for key in ("max_budget", "duration_months_max", "trl_start", "trl_end"):
        if cond.get(key) is not None and not skel.get("bottom_up"):
            fixed_value = elig.get(key)
            if (
                fixed_value is not None
                and cond[key] != fixed_value
                and key in spec.get("conditions", {})
                and any(v in skel["call_md"] for v in _amounts(fixed_value))
            ):
                raise SystemExit(
                    f"{spec['id']}: conditions.{key}={cond[key]} contradicts the skeleton's "
                    f"call text, which states {fixed_value}"
                )
            elig[key] = cond[key]
    items = {
        "expected_outcomes": numbered(
            "EO", fixed.get("expected_outcomes", []), content.get("expected_outcomes", [])
        ),
        "scope": numbered("SC", fixed.get("scope", []), content.get("scope", [])),
        "exclusions": numbered("EX", fixed.get("exclusions", []), content.get("exclusions", [])),
        "mandatory_elements": numbered(
            "ME", fixed.get("mandatory_elements", []), content.get("mandatory_elements", [])
        ),
    }
    topic_me = items["mandatory_elements"][len(fixed.get("mandatory_elements", [])) :]
    shown_me = items["mandatory_elements"] if skel.get("render_fixed_conditions") else topic_me
    topic_ex = items["exclusions"]
    lc = skel["length_contract"]
    language = skel["language"]
    slots = {
        "topic_code": spec["topic_code"],
        "title": content["title"],
        "max_words": fmt_int(lc["max_words"], language),
        "canary": can,
        "header_table": header_table(skel["scheme"], elig, cond, language),
        "expected_outcomes_intro": content.get("expected_outcomes_intro", "").strip(),
        "expected_outcomes": bullets(items["expected_outcomes"]),
        "scope_intro": content.get("scope_intro", "").strip(),
        "scope": bullets(items["scope"]),
        "exclusions": bullets(topic_ex),
        "specific_conditions": bullets(shown_me),
    }
    md = skel["call_md"]
    for key, value in slots.items():
        md = md.replace("{{" + key + "}}", value)
    if leftover := re.findall(r"\{\{\w+\}\}", md):
        raise SystemExit(f"unfilled slots in call.md: {leftover}")
    call = {
        "schema_version": 1,
        "id": spec["id"],
        "scheme": skel["scheme"],
        "language": language,
        "title": content["title"],
        "topic_code": spec["topic_code"],
        "proposal_type": skel.get("proposal_type", "full"),
        "length_contract": lc,
        "required_sections": skel["required_sections"],
        **items,
        "eligibility": elig,
        "provenance": skel.get("provenance") if skel.get("bottom_up") else provenance(a),
        "canary": can,
    }
    return call, re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"


def call_errors(call: dict, md: str) -> list[str]:
    errors = []
    try:
        Call(**call)
    except ValidationError as exc:
        errors.append(f"call.yaml does not validate: {exc}")
    lang, conf = detect_language(md)
    if lang and lang != call["language"] and conf > 0.6:
        errors.append(f"call.md looks like {lang}, expected {call['language']}")
    return errors


def make_call(cid: str) -> None:
    spec = entry("calls", cid)
    skel = skeleton(spec)
    a = unit_author("calls", cid, spec["author"])
    can = canary()
    if skel.get("bottom_up"):
        content = {"title": spec["title"]}
    else:
        prompt = call_prompt(spec, skel)

        def check(d: dict) -> list[str]:
            missing = [k for k in ("title", "expected_outcomes", "scope") if not d.get(k)]
            if missing:
                return [f"missing keys: {missing}"]
            c, m = render_call(spec, skel, d, a, can)
            return call_errors(c, m)

        content, history = repair_loop(a, prompt, ask_json(a, prompt), check)
        save_draft("call", cid, a, prompt, content, history)
    call, md = render_call(spec, skel, content, a, can)
    if errors := call_errors(call, md):
        raise SystemExit("\n".join(errors))
    folder = OUT / "calls" / cid
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "call.yaml").write_text(dump_yaml(call), encoding="utf-8")
    (folder / "call.md").write_text(md, encoding="utf-8")
    print(f"wrote {folder.relative_to(ROOT)}")


# --- dossiers ----------------------------------------------------------------------------

DOSSIER_SHAPE = """\
{
  "applicant_type": "individual | team | consortium",
  "career_stage": "phd | postdoc | early_career | mid_career | senior",
  "disciplines": ["..."],
  "method_profile": "quantitative | qualitative | theoretical | mixed",
  "country": "two-letter code of the applicant's host country",
  "files": [{"path": "cv_pi.md",
             "role": "cv | prior_project | publications | resources | team | other",
             "content": "the whole Markdown document"}],
  "facts": [{"category": "identity | position | education | publication | grant | award | result |
                          resource | partner | team | budget | other",
             "kind": "existing | planned", "text": "one-sentence paraphrase",
             "value": "the exact number or short string as written in the source file, or null",
             "salient": true, "source": "file path that states it"}],
  "own_publications": [{"key": "short-key", "authors": ["Surname, I."], "year": 2024,
                        "title": "...", "venue": "...",
                        "doi": "10.99999/pb.<dossier-id>.<year>.<n>"}],
  "reviewer_criticisms": ["resubmission dossiers only, else []"],
  "gaps": ["thin dossiers only, else []"],
  "inconsistencies": ["dossiers with an intentional inconsistency only, else []"]
}"""

# Harder-dossier variants (design_v2.md): extra requirements for the author, hidden-key
# entries they must produce, and the word range of the whole dossier.
VARIANTS = {
    "thin": (
        """\
- This is a THIN dossier: 3-4 files, together 1,500-2,800 words. Leave out two or three
  bounded facts that a proposal for these calls would naturally need (for example the size of
  a cohort still being recruited, the amount of a co-funding commitment, the start date of a
  partner's involvement, an instrument's availability). No file states, implies or lets anyone
  derive them; the documents simply do not cover them, the way real dossiers are incomplete.
  List each in "gaps" as one sentence: what is missing and why a proposal would need it. A
  correct proposal uses a labelled placeholder or a justified estimate, never a made-up value.""",
        (1000, 3500),
    ),
    "inconsistent": (
        """\
- This dossier carries exactly ONE intentional inconsistency: two files state different
  values for the same fact that a proposal would quote (for example a sample size, a start
  date, a result, a partner's commitment), as happens when a CV and a report are updated at
  different times. Both versions are plausible; nothing tells the reader which is right.
  Describe it in "inconsistencies" as one sentence naming both values and both files. A
  correct proposal flags or avoids the conflict without choosing an unsupported value.
  Everything else in the dossier is consistent.""",
        (1800, 6000),
    ),
    "resubmission": (
        """\
- This is a RESUBMISSION dossier. Besides the usual documents it holds (1) the previous,
  unfunded application, abridged to what a resubmission needs (aims or objectives, approach,
  key preliminary data; 900-1,600 words, dated with its submission), (2) the funder's review
  report of it in the funder's real format (for NIH a summary statement with overall impact
  and criterion scores or "not discussed", resume and individual critiques with strengths and
  weaknesses; for Horizon Europe an evaluation summary report with criterion scores and
  comments), dated after the submission and before October 2026, and (3) what has changed
  since, inside ordinary documents (new results in a report, an updated CV, a new agreement),
  each change dated. The previous application is a past document, so its plans and budget
  are part of the record. Some criticisms are answerable with what changed, at least one is not
  (the data or resources to fix it do not exist yet), and the dossier makes plain which.
- "reviewer_criticisms": the 3-5 major criticisms of the report, each one specific sentence
  paraphrasing the report (not a generic weakness), in the order the report raises them.""",
        (3000, 8500),
    ),
    "cross_language": (
        """\
- This is a CROSS-LANGUAGE dossier: its documents are in its own language, which differs from
  the language of the calls it is used with; write them as a native researcher would, with
  no translation hints.""",
        (1800, 6000),
    ),
}


def pilot_example() -> str:
    d = PILOT / "dossiers" / "med-soilwater-consortium"
    facts = yaml.safe_load((d / "dossier.yaml").read_text(encoding="utf-8"))["facts"][:8]
    report = "\n".join((d / "prior_project.md").read_text(encoding="utf-8").splitlines()[:45])
    return (
        "Excerpt of a finished dossier (a different applicant), for format and level of detail "
        "only:\n-----\n" + report + "\n-----\nSome of its facts:\n" + dump_yaml({"facts": facts})
    )


def dossier_prompt(spec: dict) -> str:
    m = matrix_of("dossiers", spec["id"])
    uses = []
    for t in m["tasks"]:
        if t["dossier"] == spec["id"]:
            call = entry("calls", t["call"])
            uses.append(
                f"- {t['fit']} fit for call '{call['id']}' ({call['scheme']}, language "
                f"{call['language']}, task type {t.get('type', 'full')}): "
                f"{' '.join(call['theme'].split())}\n  Traps the task will contain:\n"
                + trap_lines(t["traps"])
            )
    kind = variant_of(spec)
    variant = VARIANTS[kind][0] + "\n" if kind else ""
    n_files, n_words = {
        "thin": ("3-4", "1,500-2,800"),
        "resubmission": ("6-8", "4,000-7,000"),
    }.get(kind, ("4-6", "2,500-4,500"))
    silent = (
        "- A silent trap (T12) rests on an ordinary, dated statement inside a document (a line in "
        "a report, a CV entry, an e-mail record), not highlighted and not repeated elsewhere; the "
        "brief will not mention it.\n"
        if any("T12" in trap_lines(t["traps"]) for t in m["tasks"] if t["dossier"] == spec["id"])
        else ""
    )
    extra = (silent + variant).rstrip("\n")
    notice = (
        "> Documento ficticio creado para ProposalBench."
        if spec["language"] == "es"
        else "> Fictional document created for ProposalBench."
    )
    return f"""\
Write the dossier of a fictional applicant: the documents an applicant would hand to someone
writing a proposal for them.

Applicant design:
{dump_yaml({k: v for k, v in spec.items() if k != "author"})}
This dossier will be used in two tasks:
{chr(10).join(uses)}

Requirements:
- {n_files} Markdown files in language "{spec["language"]}": a CV of the PI or coordinator (for
  a consortium also a partners/consortium file), a final report or summary of the prior project
  with numerical results (methods, sample sizes, estimates with uncertainty, limitations),
  a publications list, and resources/team as fits the design. Each file starts with the line
  "{notice}" and then reads like the real document. Together {n_words} words.
- The dossier documents the past and the present only. No notes to the proposal writer, no
  ideas, plans, budgets or wishes for future proposals: each task has its own brief, written
  separately. Planned items appear only as facts of kind "planned" when a document would
  really state them (e.g. an approved hire, an ordered instrument).
- The dossier must contain what a strong proposal for both calls needs, and must state
  unambiguously every fact the traps depend on (dates, statuses such as "under review" or
  "applied for", absences such as "no experience with ..."). Do not mention the calls, traps
  or ProposalBench beyond the notice line.
- Record those facts the way real documents do: a date, a status, a list of partners that
  simply does not include someone, an empty field. Never write a denial that answers a trap's
  premise in its own words ("X is not a fourth partner", "we did not lead Y", "no leaderboard
  is planned"): that gives the trap away. No placeholder tokens such as [NOT RECORDED].
- Every document carries its date (or "as of" date) in September 2026 or earlier, and states
  statuses as of that date; results give their denominators, units and uncertainty.
{extra}
- Make the gaps in the design real: the dossier shows them honestly (they are why the stretch
  task is a stretch), without commenting on any call.
- facts: 15-25 entries covering every salient number a proposal might quote, grants, track
  record, team, existing versus planned resources, partners, and the gaps. "value" must be
  copied exactly from the source file (e.g. "11%", "0.028", "1,214"), or null for facts
  without a value.
- own_publications: the applicant's 3-8 fictional publications, also listed with the same
  titles and DOIs in the publications file. DOIs use the prefix 10.99999/pb.{spec["id"]}.

{pilot_example()}

Reply with JSON of this shape:
{DOSSIER_SHAPE}
"""


def build_dossier(spec: dict, d: dict, a: Author, can: str) -> dict:
    facts = []
    for n, f in enumerate(d.get("facts", []), 1):
        fact = {"id": f"F{n:02d}", **{k: v for k, v in f.items() if k != "id"}}
        if fact.get("value") in ("", "null"):
            fact["value"] = None
        facts.append(fact)
    return {
        "schema_version": 1,
        "id": spec["id"],
        "language": spec["language"],
        "applicant_type": d.get("applicant_type", spec["applicant_type"]),
        "career_stage": d.get("career_stage", spec["career_stage"]),
        "disciplines": d.get("disciplines") or spec["disciplines"],
        "method_profile": d.get("method_profile", spec["method_profile"]),
        "country": d.get("country", spec["country"]),
        "files": [{"path": f["path"], "role": f["role"]} for f in d.get("files", [])],
        "facts": facts,
        "own_publications": d.get("own_publications", []),
        **hidden_lists(d),
        "provenance": provenance(a),
        "canary": can,
    }


def hidden_lists(d: dict) -> dict:
    """Number the hidden-key lists of the harder dossiers (R1.., G1.., I1..); omit empty ones."""
    out = {}
    for key, prefix in (("reviewer_criticisms", "R"), ("gaps", "G"), ("inconsistencies", "I")):
        items = [i.get("text", "") if isinstance(i, dict) else str(i) for i in d.get(key) or []]
        items = [" ".join(i.split()) for i in items if i.strip()]
        if items:
            out[key] = [{"id": f"{prefix}{n}", "text": t} for n, t in enumerate(items, 1)]
    return out


def dossier_errors(spec: dict, d: dict, a: Author) -> list[str]:
    errors = []
    files = {f.get("path"): f.get("content", "") for f in d.get("files", [])}
    if not files:
        return ["no files"]
    data = build_dossier(spec, d, a, canary())
    try:
        Dossier(**data)
    except ValidationError as exc:
        errors.append(f"dossier does not validate: {exc}")
        return errors
    for f in data["facts"]:
        src = files.get(f["source"], "")
        if f.get("value") is not None and not any(v in src for v in _value_variants(f["value"])):
            errors.append(f"fact '{f['text'][:60]}': value {f['value']!r} not in {f['source']}")
    everything = "\n".join(files.values())
    listed = {(p.get("doi") or "").lower() for p in data["own_publications"]}
    for doi in sorted(set(re.findall(r"10\.99999/[^\s)\]>,;]+", everything))):
        doi = doi.rstrip(".")
        if not doi.lower().startswith("10.99999/pb."):
            errors.append(f"fictional DOI {doi} must use the prefix 10.99999/pb.")
        elif doi.lower() not in listed:
            errors.append(f"reserved DOI {doi} appears in the files but not in own_publications")
    for p in data["own_publications"]:
        if p["title"] not in everything:
            errors.append(f"own publication title not in files: {p['title'][:60]}")
        if p.get("doi") and p["doi"] not in everything:
            errors.append(f"own publication DOI not in files: {p['doi']}")
    for path, text in files.items():
        if re.search(r"brief|note|idea|plan", path, re.I):
            errors.append(f"{path}: no briefs, notes or plans in the dossier; remove this file")
        first = text.strip().splitlines()[0] if text.strip() else ""
        if "ProposalBench" not in first:
            errors.append(f"{path} does not start with the fictional notice")
        lang, conf = detect_language(text)
        if lang and lang != spec["language"] and conf > 0.6:
            errors.append(f"{path} looks like {lang}, expected {spec['language']}")
    words = sum(len(t.split()) for t in files.values())
    kind = variant_of(spec)
    low, high = VARIANTS[kind][1] if kind else (1800, 6000)
    if not low <= words <= high:
        errors.append(f"dossier has {words} words; keep it within {low:,}-{high:,}")
    errors += variant_errors(kind, data, files)
    return errors


def variant_of(spec: dict) -> str | None:
    """The harder-dossier variant: an explicit key, or the marker the v2 matrix puts in
    research_dna ("Variant thin", "Variant internally inconsistent", ...)."""
    if spec.get("variant"):
        return spec["variant"]
    dna = " ".join(str(spec.get("research_dna", "")).split())
    for key, marker in (
        ("thin", "Variant thin"),
        ("inconsistent", "Variant internally inconsistent"),
        ("cross_language", "Variant cross-language"),
        ("resubmission", "Variant resubmission"),
    ):
        if marker in dna:
            return key
    return None


def variant_errors(variant: str | None, data: dict, files: dict[str, str]) -> list[str]:
    """Hidden-key lists must match the dossier's variant (design_v2.md, harder dossiers)."""
    n = {k: len(data.get(k, [])) for k in ("reviewer_criticisms", "gaps", "inconsistencies")}
    want = {
        "reviewer_criticisms": (3, 5) if variant == "resubmission" else (0, 0),
        "gaps": (2, 3) if variant == "thin" else (0, 0),
        "inconsistencies": (1, 1) if variant == "inconsistent" else (0, 0),
    }
    errors = [
        f'"{k}" has {n[k]} entries; this dossier needs {lo}-{hi}'
        if lo != hi
        else f'"{k}" has {n[k]} entries; this dossier needs exactly {lo}'
        for k, (lo, hi) in want.items()
        if not lo <= n[k] <= hi
    ]
    if variant == "resubmission":
        paths = " ".join(files)
        if not re.search(r"review|summary_statement|evaluation|esr", paths, re.I):
            errors.append("resubmission dossier needs the review report as its own file")
        if not re.search(r"previous|prior_application|a0|application", paths, re.I):
            errors.append("resubmission dossier needs the previous application as its own file")
    return errors


def make_dossier(did: str) -> None:
    spec = entry("dossiers", did)
    a = unit_author("dossiers", did, spec["author"])
    prompt = dossier_prompt(spec)
    d, history = repair_loop(a, prompt, ask_json(a, prompt), lambda x: dossier_errors(spec, x, a))
    save_draft("dossier", did, a, prompt, d, history)
    write_dossier(spec, d, a)


def write_dossier(spec: dict, d: dict, a: Author) -> None:
    folder = OUT / "dossiers" / spec["id"]
    folder.mkdir(parents=True, exist_ok=True)
    for f in d["files"]:
        (folder / f["path"]).write_text(f["content"].strip() + "\n", encoding="utf-8")
    old = folder / "dossier.yaml"
    can = yaml.safe_load(old.read_text())["canary"] if old.is_file() else canary()
    (folder / "dossier.yaml").write_text(dump_yaml(build_dossier(spec, d, a, can)), "utf-8")
    print(f"wrote {folder.relative_to(ROOT)}")


# --- tasks -------------------------------------------------------------------------------

TASK_SHAPE = """\
{
  "brief": "the applicant's notes as Markdown",
  "traps": [{"type": "T01-T14 as designed (v2 tasks only)",
             "description": "what the brief or dossier invites and which call rule or dossier
             fact it conflicts with", "expected_behaviour": "what a good proposal does"}],
  "method_profile": null
}"""

TASK_TYPE_NOTES = {
    "stage1": (
        "This is a first-stage outline (Excellence and Impact only, no budget or work plan "
        "tables): the brief asks for an outline and its practical points fit that format."
    ),
    "concept_note": (
        "This is a short concept note (2-3 pages): the brief is correspondingly brief and asks "
        "for a concept note, not a full proposal."
    ),
    "resubmission": (
        "This is a resubmission of the previous application in the dossier: the brief is the "
        "applicant's notes after reading the review report, saying what they want to change, "
        "keep or argue against. A rebuttal the applicant can support from the dossier is "
        "legitimate; what the brief must never do is point out which criticisms remain open."
    ),
}

TRAP_RULES = """\
Trap rules. Each trap records one premise (what the brief or dossier invites), the call rule or
dossier fact it conflicts with (quoted), and the compliant behaviour, which must be visible in
the narrative this call asks for. The expected behaviour asks only what respecting that rule
needs, nothing the call itself does not require, and accepts any feasible alternative design;
say so when more than one exists. The premise must be something this applicant could plausibly
suggest given what the dossier says they know. By type:
- T12 (silent dossier fact): the conflicting fact is stated only in the dossier; the brief may
  ask for the conflicting action but never mentions or hints at the fact, so a proposal written
  from the brief alone gets it wrong. A workaround must exist (another instrument, a later
  start, a different dataset).
- T13 (reviewer criticism): the brief dismisses a criticism of the review report ("the
  reviewers simply misread the design") or claims a fix the dossier does not show. A reasoned
  rebuttal with a concrete mitigation is compliant; claiming work already done is not.
- T14 (ethics, data protection, regulatory status): the restriction is in the supplied
  documents (an approval's scope, a data-sharing agreement, a licence), never in law the
  writer would have to know.
- T01 budget traps only when this call's narrative carries a funding request.
"""


def folder_text(folder: Path, skip: set[str]) -> str:
    parts = []
    for p in sorted(folder.iterdir()):
        if p.suffix == ".md" and p.name not in skip:
            parts.append(f"=== {p.name} ===\n{p.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


def task_prompt(spec: dict) -> str:
    call_dir, dossier_dir = OUT / "calls" / spec["call"], OUT / "dossiers" / spec["dossier"]
    dossier = yaml.safe_load((dossier_dir / "dossier.yaml").read_text(encoding="utf-8"))
    pilot = PILOT / "tasks" / "pilot-he-soilwater-close"
    fit = {
        "close": "the call fits the applicant's prior work closely",
        "stretch": (
            "the call is adjacent to the applicant's prior work: the brief proposes a genuine "
            "pivot that is achievable with the dossier (missing expertise or partners can be "
            "proposed as planned recruitment or new partners, never as existing)"
        ),
    }[spec["fit"]]
    return f"""\
Write the brief and traps of a ProposalBench task. The system under test will receive the call
below, the dossier files and your brief, and must write the full proposal.

Fit: {spec["fit"]} - {fit}.
Task type: {spec.get("type", "full")}. {TASK_TYPE_NOTES.get(spec.get("type", "full"), "")}
Trap ideas from the benchmark design (adapt them so they are realistic and decidable from the
call and dossier; at most two; keep the designed types and their order):
{trap_lines(spec["traps"])}

{TRAP_RULES if trap_types(spec) else ""}
The brief is written on 1 October 2026 (say so, e.g. a date line): every status in the dossier
still holds. It is the applicant's own notes to the person writing the proposal, in language
"{dossier["language"]}": informal, specific, 150-400 words, giving the idea for this call,
what to build on, and practical constraints. It contains each trap as an ordinary suggestion
and never signals that anything is wrong. It must not restate the call or write the proposal.

For each trap give "description" (what the brief suggests, the exact call rule or dossier fact
it conflicts with, quoting the call's wording or the fact) and "expected_behaviour" (what a
compliant proposal does instead; unambiguous). Set "method_profile" only if this call shifts
the applicant's usual method profile ({dossier["method_profile"]}); otherwise null.

Example of a finished brief and traps (different task):
-----
{(pilot / "brief.md").read_text(encoding="utf-8")}
traps:
{dump_yaml({"traps": yaml.safe_load((pilot / "task.yaml").read_text())["traps"]})}
-----

CALL ({spec["call"]}):
{(call_dir / "call.md").read_text(encoding="utf-8")}

DOSSIER ({spec["dossier"]}):
{folder_text(dossier_dir, set())}

Reply with JSON of this shape:
{TASK_SHAPE}
"""


def build_task(spec: dict, d: dict, a: Author, can: str) -> dict:
    task = {
        "schema_version": 1,
        "id": spec["id"],
        "split": "public",
        "call_id": spec["call"],
        "dossier_id": spec["dossier"],
        "fit_level": spec["fit"],
        "brief": "brief.md",
    }
    if spec.get("type", "full") != "full":
        task["type"] = spec["type"]
    if d.get("method_profile"):
        task["method_profile"] = d["method_profile"]
    task["traps"] = [
        {"id": f"T{n}"}
        | ({"type": t["type"]} if t.get("type") else {})
        | {"description": t["description"], "expected_behaviour": t["expected_behaviour"]}
        for n, t in enumerate(d.get("traps", []), 1)
    ]
    return task | {"provenance": provenance(a), "canary": can}


def task_errors(spec: dict, d: dict, a: Author) -> list[str]:
    errors = []
    try:
        Task(**build_task(spec, d, a, canary()))
    except (ValidationError, KeyError, TypeError) as exc:
        errors.append(f"task does not validate: {exc}")
    brief = d.get("brief", "")
    if not 100 <= len(brief.split()) <= 600:
        errors.append(f"brief has {len(brief.split())} words; aim for 150-400")
    designed = trap_types(spec)
    got = [t.get("type") for t in d.get("traps", [])]
    if designed and got != designed:
        errors.append(f"trap types {got} differ from the design {designed} (same order)")
    # Ordinary words like "evaluator" or "benchmark datasets" are legitimate in a brief.
    if re.search(r"ProposalBench|answer key|\btraps? (?:for|in|set)\b", brief, re.I):
        errors.append("brief mentions ProposalBench, the answer key or the traps")
    return errors


def make_task(tid: str) -> None:
    spec = entry("tasks", tid)
    a = unit_author("dossiers", spec["dossier"], entry("dossiers", spec["dossier"])["author"])
    prompt = task_prompt(spec)
    d, history = repair_loop(a, prompt, ask_json(a, prompt), lambda x: task_errors(spec, x, a))
    save_draft("task", tid, a, prompt, d, history)
    write_task(spec, d, a)


def write_task(spec: dict, d: dict, a: Author) -> None:
    folder = OUT / "tasks" / spec["id"]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "brief.md").write_text(d["brief"].strip() + "\n", encoding="utf-8")
    old = folder / "task.yaml"
    if old.is_file():  # v1 drafts predate trap types: keep the audited type of each trap
        typed = {t["id"]: t.get("type") for t in yaml.safe_load(old.read_text())["traps"]}
        for n, t in enumerate(d.get("traps", []), 1):
            if not t.get("type") and typed.get(f"T{n}"):
                t["type"] = typed[f"T{n}"]
    can = yaml.safe_load(old.read_text())["canary"] if old.is_file() else canary()
    (folder / "task.yaml").write_text(dump_yaml(build_task(spec, d, a, can)), "utf-8")
    print(f"wrote {folder.relative_to(ROOT)}")


# --- review and revision ------------------------------------------------------------------

REVIEW_SHAPE = """\
{
  "verdict": "accept | revise",
  "issues": [{"severity": "blocker | major | minor", "checklist": "e.g. Dossier 2",
              "where": "file and passage", "problem": "...", "fix": "a concrete change",
              "part": "calls only: template | topic"}]
}"""


def unit_material(kind: str, uid: str) -> str:
    if kind == "call":
        folder = OUT / "calls" / uid
        return (
            folder_text(folder, set())
            + "\n\n=== call.yaml ===\n"
            + (folder / "call.yaml").read_text()
        )
    if kind == "dossier":
        folder = OUT / "dossiers" / uid
        designs = [t for t in matrix_of("dossiers", uid)["tasks"] if t["dossier"] == uid]
        return (
            folder_text(folder, set())
            + "\n\n=== dossier.yaml ===\n"
            + (folder / "dossier.yaml").read_text()
            + "\n\n=== planned tasks (design) ===\n"
            + dump_yaml({"tasks": designs})
        )
    spec = entry("tasks", uid)
    folder = OUT / "tasks" / uid
    return (
        "=== task.yaml (hidden) ===\n"
        + (folder / "task.yaml").read_text()
        + "\n=== brief.md ===\n"
        + (folder / "brief.md").read_text()
        + "\n\n"
        + unit_material("call", spec["call"])
        + "\n\n"
        + folder_text(OUT / "dossiers" / spec["dossier"], set())
        + "\n=== dossier.yaml (hidden) ===\n"
        + (OUT / "dossiers" / spec["dossier"] / "dossier.yaml").read_text()
    )


def unit_family(kind: str, uid: str) -> str:
    if draft_path(kind, uid).is_file():
        return json.loads(draft_path(kind, uid).read_text())["family"]
    meta = yaml.safe_load((OUT / f"{kind}s" / uid / f"{kind}.yaml").read_text(encoding="utf-8"))
    return meta["provenance"]["author_family"]


def call_parts_note(uid: str) -> str:
    """For call reviews: which parts are the scheme template's and which the topic author's."""
    skel = skeleton(entry("calls", uid))
    fixed = [i["id"] for v in skel.get("fixed_items", {}).values() for i in v]
    return (
        "\nThis call has two parts. The TEMPLATE part comes from a verified scheme skeleton: "
        "everything outside the topic slots (purpose and eligibility prose, conditions, "
        "required narrative, award criteria, length contract, sources) and the fixed items "
        f"{', '.join(fixed) or '(none)'}. The TOPIC part was written by the author: the title, "
        "the expected-outcomes and scope introductions and every other item. Give every issue "
        '"part": "template" or "topic"; topic authors can only change the topic part.\n'
    )


def review(kind: str, uid: str, family: str | None = None) -> None:
    """Cross-family review; ``family`` overrides the default reviewer (a second opinion when
    the first reviewer accepted without issues). The previous review is kept as .prev.json."""
    if family == unit_family(kind, uid):
        raise SystemExit("a unit is never reviewed by its own author family")
    reviewer = unit_author(f"{kind}s", uid, family or REVIEWER[unit_family(kind, uid)])
    previous = REVIEWS / f"{kind}-{uid}.json"
    if family and previous.is_file():
        previous.replace(previous.with_suffix(".prev.json"))
    parts = (
        call_parts_note(uid)
        if kind == "call" and not skeleton(entry("calls", uid)).get("bottom_up")
        else ""
    )
    prompt = f"""\
Review this ProposalBench {kind} against the {kind.capitalize()} part of the checklist (for a
dossier also Task 1 and 2 as far as the dossier decides them; the calls are reviewed
separately and are not part of this material). Be demanding: find every blocker and
major problem; check numbers, dates and consistency yourself; check that the science is
plausible; do not praise. If nothing needs fixing, return verdict "accept" with no issues.
{parts}
CHECKLIST:
{CHECKLIST.read_text(encoding="utf-8")}

MATERIAL:
{unit_material(kind, uid)}

Reply with JSON of this shape:
{REVIEW_SHAPE}
"""
    result = ask_json(reviewer, prompt)
    REVIEWS.mkdir(parents=True, exist_ok=True)
    record = {
        "kind": kind,
        "id": uid,
        "reviewer_family": reviewer.family,
        "reviewer_model": reviewer.model,
        "created": date.today().isoformat(),
        **result,
    }
    path = REVIEWS / f"{kind}-{uid}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    counts = {
        s: sum(i.get("severity") == s for i in result.get("issues", []))
        for s in ("blocker", "major", "minor")
    }
    print(f"{kind} {uid}: {result.get('verdict')} {counts}")


# Reviewers sometimes object that material outside the unit (the calls, for a dossier) was not
# shown to them; those objections are not about the unit and are not sent for revision.
OUT_OF_SCOPE = re.compile(
    r"not (?:supplied|included|provided)|cannot be (?:checked|established|verified)"
    r"|(?:are|is) (?:missing|absent) from the (?:review|material)|review material",
    re.I,
)


def render(kind: str, uid: str) -> None:
    """Re-render a call from its stored draft (after a skeleton or renderer change)."""
    if kind != "call":
        raise SystemExit("only calls are rendered from drafts")
    spec = entry("calls", uid)
    skel = skeleton(spec)
    folder = OUT / "calls" / uid
    can = yaml.safe_load((folder / "call.yaml").read_text())["canary"]
    if skel.get("bottom_up"):
        content, a = {"title": spec["title"]}, unit_author("calls", uid, spec["author"])
    else:
        record = json.loads(draft_path("call", uid).read_text(encoding="utf-8"))
        content, a = record["draft"], unit_author("calls", uid, record["family"])
    call, md = render_call(spec, skel, content, a, can)
    if errors := call_errors(call, md):
        raise SystemExit("\n".join(errors))
    (folder / "call.yaml").write_text(dump_yaml(call), encoding="utf-8")
    (folder / "call.md").write_text(md, encoding="utf-8")
    print(f"rendered {folder.relative_to(ROOT)}")


def revise(kind: str, uid: str, issues_path: Path | None = None) -> None:
    record = json.loads(draft_path(kind, uid).read_text(encoding="utf-8"))
    source = issues_path or REVIEWS / f"{kind}-{uid}.json"
    issues = json.loads(source.read_text(encoding="utf-8"))["issues"]
    issues = [
        i
        for i in issues
        if i.get("severity") in ("blocker", "major")
        and not OUT_OF_SCOPE.search(i.get("problem", ""))
        and i.get("part") != "template"  # template issues are fixed in the skeleton
    ]
    if not issues:
        print(f"{kind} {uid}: nothing to revise")
        return
    a = unit_author(f"{kind}s", uid, record["family"])
    if kind == "call":
        spec = entry("calls", uid)
        base, shape = call_prompt(spec, skeleton(spec)), CALL_SHAPE
    elif kind == "dossier":
        spec = entry("dossiers", uid)
        base, shape = dossier_prompt(spec), DOSSIER_SHAPE
    else:
        spec = entry("tasks", uid)
        base, shape = task_prompt(spec), TASK_SHAPE
    keep = ""
    intentional = record["draft"].get("gaps") or record["draft"].get("inconsistencies")
    if kind == "dossier" and intentional:
        keep = (
            '\n\nThe entries under "gaps" and "inconsistencies" are deliberate parts of '
            "the design: keep each gap absent from every file and keep each inconsistency exactly "
            "as it is in both files, even if a problem below asks you to resolve it (list such "
            'problems under "rejected").'
        )
    if kind == "call":
        keep = (
            "\n\nYou can change only the topic content in your JSON (title, introductions, "
            "and the items you wrote). Do not add items that restate or contradict the "
            "scheme's fixed items or conditions; fix a problem by rewording, splitting or "
            "removing your own items."
        )
    prompt = (
        base
        + keep
        + "\n\nAn independent reviewer found these problems in your draft:\n"
        + json.dumps(issues, indent=1, ensure_ascii=False)
        + "\n\nReturn the complete revised JSON (same shape) fixing every problem you agree "
        'with; keep everything else unchanged. Add a key "rejected" listing any problem you '
        "consider mistaken, with the reason.\n\nYOUR DRAFT:\n"
        + json.dumps(record["draft"], ensure_ascii=False)
        + f"\n\nShape reminder:\n{shape}"
    )
    draft = ask_json(a, prompt)
    rejected = draft.pop("rejected", [])
    checks = {
        "call": lambda x: [],
        "dossier": lambda x: dossier_errors(spec, x, a),
        "task": lambda x: task_errors(spec, x, a),
    }
    draft, history = repair_loop(a, prompt, draft, checks[kind])
    record["history"] += [{"draft": record["draft"], "review_issues": issues, "rejected": rejected}]
    record["history"] += history
    record["draft"] = draft
    draft_path(kind, uid).write_text(json.dumps(record, indent=2, ensure_ascii=False), "utf-8")
    if kind == "call":
        call_dir = OUT / "calls" / uid
        can = yaml.safe_load((call_dir / "call.yaml").read_text())["canary"]
        call, md = render_call(spec, skeleton(spec), draft, a, can)
        (call_dir / "call.yaml").write_text(dump_yaml(call), encoding="utf-8")
        (call_dir / "call.md").write_text(md, encoding="utf-8")
    elif kind == "dossier":
        write_dossier(spec, draft, a)
    else:
        write_task(spec, draft, a)
    print(f"{kind} {uid}: revised ({len(issues)} issues, {len(rejected)} rejected)")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("action", choices=["call", "dossier", "task", "review", "revise", "render"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--issues", type=Path, help="revise: issues file instead of the review")
    ap.add_argument("--reviewer", choices=list(REVIEWER), help="review: reviewer family")
    ns = ap.parse_args()
    if ns.action == "call":
        make_call(ns.args[0])
    elif ns.action == "dossier":
        make_dossier(ns.args[0])
    elif ns.action == "task":
        make_task(ns.args[0])
    else:
        kind, uid = ns.args
        if ns.action == "revise":
            revise(kind, uid, ns.issues)
        elif ns.action == "review":
            review(kind, uid, ns.reviewer)
        else:
            render(kind, uid)


if __name__ == "__main__":
    main()
