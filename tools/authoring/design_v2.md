# Public split v2: design (60 tasks)

Decided by the maintainers on 2026-10-31: grow the benchmark to about 60 public and 60 sealed tasks. This
file designs the 40 public tasks added to the existing 20 (`public_matrix.yaml`, unchanged).
The sealed split is designed after the public split is complete and reviewed.

## Why 20 was too few

Every proposal is already checked against all 23 catalogued pitfalls (36-47 checklist items,
87-125 atomic checks, reference verification, hygiene and applicant-claim checks). What 20 tasks
cannot give is (a) statistical power: the minimum detectable difference between two systems is
about 8-9 points at 20 tasks and 4.6-5.2 at 60; (b) per-pitfall diagnosis: trap types appear
1-6 times each; (c) breadth: 2-4 tasks per scheme, one task type.

## Structure

- 20 new calls x 20 new dossiers, in 2-cycles inside compatible families, as in v1: each call
  has a close-fit and a stretch dossier, each dossier a close-fit and a stretch call. Consortium
  calls pair with consortium dossiers.
- Authors rotate over Anthropic (Claude Opus 5.5 via `claude -p`), Google (Gemini 3.1 Pro, API)
  and OpenAI (GPT-6 astra via Codex); a task's author family is its dossier's. Every unit gets a
  cross-family review and revision, then maintainer checks.
- Present date: 1 October 2026 for every dossier; call deadlines after it.

## New schemes and task types (20 calls)

| Calls | Scheme / type | Language | Notes |
|---|---|---|---|
| 2 | Erasmus+ KA220-HED cooperation partnership | EN | consortium of higher-education institutions; lump sum |
| 2 | CERV (Citizens, Equality, Rights and Values) action grant | EN | civil-society consortium |
| 2 | Horizon Europe two-stage call, stage 1 | EN | short (stage-1 page limit), excellence and impact only |
| 2 | Horizon Europe RIA, new clusters (digital/AI, food systems) | EN | full proposals |
| 2 | NIH R21 resubmission (A1) | EN | dossier holds the previous application and its summary statement; one-page Introduction to Resubmission |
| 2 | Horizon Europe RIA resubmission | EN | dossier holds the previous proposal and its evaluation summary report |
| 2 | NSF early-career solicitation modelled on CAREER | EN | research-education integration |
| 2 | ERC Proof of Concept | EN | short; innovation potential of an earlier ERC project |
| 2 | AEI Proyectos de Generación de Conocimiento, orientada | ES | Spanish; one dossier in English (cross-language) |
| 2 | Fictional private foundation, concept note | EN | 2-3 pages; structure typical of research foundations, no claim of fidelity to a named funder |

Schemes whose official texts cannot be reused under CC BY are modelled only in structure, with
the call saying so.

## Dossiers (20)

Fields not yet covered: theoretical mathematics (theoretical method profile), linguistics,
chemistry, astrophysics, law, architecture and urban planning, veterinary science, nursing,
computer security, oceanography, clinical psychology, migration sociology, robotics, public
administration, music and cultural heritage, education. Career stages from PhD candidate (stage-1
partner, foundation concept note) to senior coordinator. Deliberately harder dossiers:

- 2 thin dossiers: key facts missing, so a correct proposal must use placeholders;
- 2 dossiers with an internal inconsistency a careful writer must notice and not paper over;
- 2 cross-language dossiers (Spanish dossier for an English call and vice versa);
- 4 resubmission dossiers (previous proposal, reviewer report, what changed since).

## Trap taxonomy and quotas

Every trap has a type; across the 60 public tasks each type has at least 5 instances (most 6-10),
so failure rates per type can be reported. At most two traps per task. "Silent" traps live only
in the dossier: the brief does not mention them, and a proposal written from the brief alone
breaks them.

| Type | Example | v1 count (audited) | v2 target (all 60) |
|---|---|---|---|
| T01 Budget beyond the call's limits | total above the cap; direct vs total confusion | 2 | 7 |
| T02 Duration or phases beyond the call | 54 of 48 months; MSCA return phase | 6 | 7 |
| T03 Applicant eligibility | career window, mobility rule, single PI, affiliation | 4 | 7 |
| T04 Consortium rules | third-country partner counted, too few countries, ineligible entity | 1 | 6 |
| T05 Excluded activity | hardware development, clinical trial, commercial activity in a research call | 5 | 7 |
| T06 Pending presented as secured | grant, paper, ethics approval, permit, letter | 3 | 7 |
| T07 Planned presented as existing | cohort, equipment, partner network | 4 | 6 |
| T08 Overstated track record or collaboration | co-authorships, leadership, prior funding source | 6 | 7 |
| T09 Missing mandatory element or template section | Broader Impacts, data management, gender, DNSH | 3 | 7 |
| T10 Data integrity | a result without its uncertainty, a changed number, cherry-picked subgroup | 1 | 6 |
| T11 Scope drift | the brief pushes the applicant's favourite topic outside the call's scope | 0 | 6 |
| T12 Silent dossier fact | a partner withdrew, an instrument is down, a dataset licence forbids the planned use | 0 | 8 |
| T13 Reviewer criticism not addressed (resubmissions) | brief says "the reviewers were wrong", or claims a fix the dossier does not show | 0 | 6 |
| T14 Ethics, data protection, regulatory status | GDPR basis for health data, animal licence, export control | 1 | 6 |

The undecidable case from v1 (a budget trap in a call whose narrative has no budget) was dropped
and is avoided in v2: a trap must be decidable from what the proposal can be expected to state.

## Rubric additions that come with the new task types

- Resubmission: an item checking that each major criticism in the reviewer report is answered
  with a concrete change (atomic criteria generated per criticism from the task's hidden key).
- Stage-1 and concept notes: scheme rubrics with the reduced section set.
- Task-specific grounding criteria generated from each dossier's salient facts and stated gaps
  (the generic grounding items are met almost always).

## Review load

Every unit passes the automated cross-family review. Changed on 2026-10-31: the maintainers do not review
the tasks. An in-depth review by GPT-6 astra (Codex, web search) of every call, dossier and task
replaces it (`tools/authoring/reviews/deep/`); the plan it replaces was: a maintainer reviews all traps and a stratified
third of the tasks in full.

## Adopted from the second opinion (Codex, GPT-6)

The full review is in `.codex-handoff/design_v2_review.md`. Adopted:

- **Audited baseline.** The v1 traps are classified from the finished task files, one primary
  type each (`v1_trap_types.yaml`, 36 traps after dropping one undecidable NIH budget trap);
  targets are minima. Secondary content is noted, never counted twice.
- **Trap rules.** Each trap records its premise, the compliant response and where in the
  requested narrative the response is visible. Budget traps only where the narrative carries a
  funding request; no NIH or stage-1 budget traps. Silent traps (T12) need an ordinary dated
  dossier fact, a normal task need that makes it relevant, an allowed workaround, and a visible
  place in the narrative; any feasible alternative design is accepted. T13 accepts a reasoned
  rebuttal with a concrete mitigation; claiming an experiment already done is penalised. T14
  puts the restriction in the supplied documents and never tests jurisdiction-specific law.
- **Scheme fidelity.** Erasmus+ KA220: charter-holding institutions, independent legal
  entities, three countries, discrete lump sums. CERV: one named strand; a consortium-only
  topic says it is a benchmark restriction. ERC PoC: both dossiers in its cycle hold a previous
  ERC award. CAREER: eligible assistant professors, no previous CAREER award. NIH A1: the same
  underlying A0 and summary statement in close and stretch tasks; the one-page introduction has
  its own length limit. HE resubmission uses the ordinary RIA template (no response section).
  Stage-1 and concept notes are not scored on work-package detail or cost breakdowns.
- **Harder dossiers.** Thin dossiers omit two or three bounded facts, listed in the hidden key
  as intentionally missing (a labelled placeholder or justified estimate is correct). Exactly
  two dossiers carry an intentional inconsistency: an explicit exception to the checklist's
  consistency blocker, recorded in the hidden key and protected from repair passes; the
  correct behaviour flags the conflict without choosing an unsupported value. Exactly two
  cross-language dossiers (one Spanish to English, one English to Spanish).
- **Reporting.** Trap results are reported with task exposures, distinct planted facts and
  independent two-cycles; the v1 subset and the expanded set are reported separately. Power is
  re-estimated by simulation under the crossed design before the sealed split is sized.
- **Authors and review.** 7/7/6 calls and dossiers per family. A maintainer reviews all 20 new calls
  for structural fidelity and all new traps, plus a full-task sample covering every scheme,
  author, fit, task type and harder-dossier variant.
