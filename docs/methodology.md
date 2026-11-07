# Methodology

How ProposalBench tasks are built, how proposals are scored, and how the scorer itself is
checked. The scoring function is specified exactly in [`scoring_spec.md`](scoring_spec.md); every
change to it is logged with its reason in [`decision-log.md`](decision-log.md). What the
score does not establish is in [`limitations.md`](limitations.md).

## 1. The task

A task reproduces the job of writing a proposal for a specific call from an applicant's prior
research. A system receives four things and returns one Markdown proposal:

| Input | Content |
|---|---|
| `call.md` | A funding call: topic, expected outcomes, scope, exclusions, conditions, award criteria, the proposal template and a word limit |
| dossier files | The applicant's documents: CVs, a prior-project report with numerical results, a publications list, team and resources |
| `brief.md` | The applicant's notes for this call: the idea and practical constraints |
| `instructions.md` | Identical for every task and system: output format, the rule against inventing applicant facts, how to mark missing information |

Systems never see the hidden answer key (`call.yaml`, `dossier.yaml`, `task.yaml`): the
length contract, the call's items with identifiers, the registry of applicant facts and their
exact values, the applicant's own publications, and up to two traps per task.

**Calls** are fictional but follow real schemes: Horizon Europe RIA, ERC Starting Grant, MSCA
Postdoctoral Fellowships (European and Global), NIH R21, NSF and the Spanish AEI *Generación de
Conocimiento* (in Spanish). Everything the funder fixes (sections, award criteria, page limits,
award conditions, eligibility rules) comes from a scheme skeleton (`tools/authoring/schemes/`)
written from the official documents, with sources and verification dates. Only topics,
identifiers, budgets and dates are invented, and each call says so.

**Word limits** replace page limits. Each length contract records the official page limit, the
words-per-page conversion and the enforcement rule of the scheme: text beyond the limit is
ignored where evaluators disregard excess pages (Horizon Europe, ERC, MSCA) and the proposal is
inadmissible where the funder rejects it (NIH, NSF, AEI).

**Dossiers** describe fictional applicants (people, institutions, grants and publications are
invented; methods, instruments and science are real). Their numbers are specific and internally
consistent, existing and planned resources are kept apart, and their gaps are stated, because a
good proposal must not paper over them. The applicants' own publications carry DOIs under the
unregistered prefix `10.99999/pb.`, which can never resolve to a real work.

**Traps** are realistic suggestions in the brief that conflict with the call or the dossier (a
budget above the cap, an excluded activity, a pending result presented as published). Each is
decidable from the inputs alone, and its expected behaviour is written down.

### Splits

| Split | Use | Size |
|---|---|---|
| pilot | Development of the harness | 3 tasks (Horizon Europe, NIH, AEI) |
| public | Development and published results | 60 tasks: 30 calls x 30 dossiers |
| sealed | Planned for a later version: authored after the evaluator, released as hashes until it is run once | not part of v1.0 |

In the public split each call is paired with a close-fit dossier and a stretch dossier, and each
dossier with a close-fit call and a stretch call (`tools/authoring/public_matrix.yaml`, `public_matrix_v2.yaml`). Every
task therefore has a contrast within its call and within its applicant. Consortium calls are
paired with consortium dossiers, so no stretch task requires inventing partners.

### Authoring

Calls, dossiers and briefs are drafted by models of three families (Anthropic, Google, OpenAI)
in rotation, each with a fixed prompt (`tools/authoring/synthesize.py`). Drafts are validated
mechanically (schema, every fact value present in its source file, own publications listed,
language, word counts) with up to two repair rounds. Each call and dossier is then reviewed by a
model of another family against [`task_review_checklist.md`](task_review_checklist.md), the
author revises (it may reject review points with reasons). No human reviews the tasks: in place
of a maintainer sign-off, every call, dossier and task then gets an independent in-depth review by
GPT-6 astra (through Codex, with web search) that verifies each stated rule against the funder's
current documents, searches every name for collisions with real people and organisations, checks
the science and the hidden key, and tests each trap for decidability; its blockers and majors go
back to the author for revision (`tools/authoring/reviews/deep/`). For units GPT-6 drafted, this
reviewer shares the author's family. Every draft, review and revision is kept in
`tools/authoring/{drafts,reviews}/`. Because authors and
evaluated systems share model families, results are reported by author family as well.

Contamination checks are diagnostics, not proof: canary strings in every file, a 12-gram overlap
check against the seed documents, and fictional names.

## 2. Scoring

`Score = max(0, Quality - Integrity deductions)`, on the admissible text only.

**Admissibility** (deterministic): language, length contract, empty or failed output. An
inadmissible proposal scores 0; where excess text is disregarded, it is truncated before scoring.

**Quality** = 0.4 call responsiveness + 0.4 substance + 0.2 applicant grounding. Each component
is the mean of its applicable checklist items:

- *Call items* are generated from the hidden key: each expected outcome and scope item must be
  addressed by a concrete activity, an owner, a time or deliverable and a measure (four atomic
  criteria); exclusions must be respected; mandatory elements must be substantive; traps must be
  handled as expected.
- *Generic items* (`rubrics/generic.yaml`) cover the defects documented in funder and evaluator
  sources (`pitfall_taxonomy.md`): vague objectives, novelty without positioning, methods as a
  black box, risks without mitigation, generic impact, team-task mismatch and others. Each scheme
  maps them to its own sections and adds its own items (`rubrics/schemes/`).
- *Deterministic items* need no judge: the evidence base (EV1: external references cited in the
  text per 1,000 words and verified ones, at most three per citing sentence, leaving out works
  the panel finds unrelated to their sentence) and plan coherence (PC1: a fact sheet of work packages,
  months, deliverables, budget and partners is extracted by each judge, merged by majority and
  checked arithmetically against the call and the dossier).

Judged items are answered by a panel of three models from families that no compared system uses
(currently Kimi K3, GLM-5, DeepSeek V3.2). A positive answer needs a verbatim quote, which is
checked against the text; an answer whose quote is not found counts as invalid. Atomic criteria
take the median of the valid answers; judges may abstain, and abstentions are reported.

**Integrity deductions** are fixed per defect, so padding cannot dilute them:

| Severity | Deduction | Examples |
|---|---|---|
| Critical | -10 each | Invented applicant credential, grant, publication or resource; a preliminary result contradicting the dossier |
| Major | -4 each | A DOI that resolves to a different work; a reference whose authors do not match the work; a citation contradicted or unrelated to its sentence |
| Minor | -0.5 each, at most -5 | Metadata errors; miscited own publications |

A reference that cannot be found anywhere is never penalised: on real published proposals 7.4%
of journal articles from 2000 on are not found by the checker (anchor calibration below).

**Reference verification** resolves each reference by DOI, arXiv id, title search in Crossref
and Semantic Scholar (OpenAlex when a key is available), its URL, and web search (Exa). A
reference is called misattributed only on positive evidence: the identifier leads to a different
work, or the found work's authors are absent from the reference, and never because the parser
split the reference wrongly (the raw reference text is checked before any such verdict).
Citing sentences are compared with the cited work's abstract by the panel; silence is neutral.

## 3. Checking the scorer

v1 has no human raters, so the scorer is checked by tests it can fail.

**Flaw injection** (`meta/perturb/`). Thirteen deterministic operators insert one known defect into
real outputs (a dropped required section, a fabricated award, a contradicted dossier number, a
budget above the cap, a milestone after the end, an undefined work package, a fabricated or
corrupted reference, placeholders, meta-commentary, excess length), each paired with a control
edit of the same kind and size that introduces no defect. A detector counts as detecting a flaw
when it fires on the flawed version and not on its control. Recall and control false-positive
rate are reported per detector and per judge with Wilson intervals. Targets: recall at least
0.95 and false-positive rate at most 0.05 for deterministic checks, at least 0.80 and at most
0.15 for judge-based checks; items that miss them become diagnostics. Two invariance operators
(a prompt injection addressed to evaluators, padding with irrelevant verified citations) must not
raise the score.

Five additional meaning-preserving transformations test stability: equivalent required-section
headings, reordered references with consistent citation labels, numeric-to-author-year citations,
Markdown presentation changes, and paragraph splitting/merging. Each is paired with a freshly
evaluated exact copy of the original text. The suite reports transformed-minus-control score
differences (mean and sample SD), the share exceeding a default absolute tolerance of 3 points,
changes to deterministic finding sets and reference-status counts, and items moving more than
0.25. The original-base versus fresh-control comparison separately measures repeat-evaluation
noise. Heading and citation mappings are verified mechanically; unsupported or ambiguous edits
are recorded as inapplicable, not counted as successful invariance tests. An empty panel
(`--panel none`) measures deterministic findings without model calls; score and item facets are
unavailable. Evidence-service availability remains a possible source of reference-status changes.

**Anchor set** (`data/anchors/`, `meta/anchors.py`). Eleven real, published proposals under CC BY
measure how the evidence layer behaves on genuine references. On 598 references (2026-10-31):
none was misattributed after the matching fixes, and 7.4% of indexable articles were not found. The anchors also set the EV1 thresholds and the human baseline of the style diagnostics.
They are not used to claim anything about quality.

**Judge reliability**: agreement between the panel's judges per item family, test-retest over
repeated runs, and the correlation of scores with length.

## 4. Statistics

Scores are compared with a two-way cluster bootstrap over calls and dossiers, resampling samples
within tasks. Minimum detectable differences are estimated from the pilot variance before the
sealed split is sized. Primary comparisons are pre-registered and Holm-corrected; an interval
that includes zero is reported as no detectable difference. No per-scheme claims are made.

## 5. Reproducibility

Every stage of an evaluation writes its output (`admissibility.json`, `checks.json`,
`references.json`, `judges/*.json`, `claims/*.json`, `factsheet/*.json`, `support/*.json`,
`score.json`) and is skipped when that output exists, so a published results folder can be
re-scored offline byte for byte (`pb evaluate --offline`). HTTP responses are cached; sources that
were unavailable during a run are recorded with the run. A fresh re-evaluation with live judges
and services is expected to reproduce scores within the reported variance, not exactly.
