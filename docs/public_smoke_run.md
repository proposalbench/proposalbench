# Public split: first end-to-end run (2026-10-31)

The first run on the 20 public tasks tested the tasks, the new scheme rubrics (ERC, MSCA, NSF,
AEI no orientada) and the scorer together. One system, one sample per task: these are
development numbers, not results.

## Setup

| | |
|---|---|
| Tasks | 20 public tasks (10 calls x 10 dossiers; Horizon Europe, ERC, MSCA EF and GF, NIH R21, NSF, AEI in Spanish) |
| System | `direct-gemini-3.1-pro` (one prompt with every input file) |
| Samples | 1 per task |
| Judge panel | Kimi K3, GLM-5, DeepSeek V3.2 |

## Faults found in the harness, and fixed

| Fault | Effect | Fix |
|---|---|---|
| A proposal wrapped entirely in a ```` ```markdown ```` fence | No sections, 0 counted words; the length limit could not apply | A whole-document fence is unwrapped before evaluation |
| "Project Description" written as a bold line above `###` sections | Only the 476-word summary was counted (the description's sections became siblings of a level-4 heading) | A bold heading directly followed by a Markdown heading is its parent; reference lists nested in a counted section are not counted |
| The applicant-claims panel saw the dossier but not the brief | Facts a proposal correctly took from the brief (a partner's update) were deducted as fabrications | The brief is included; where it contradicts the other documents, they prevail, so traps in briefs stay traps |
| Parallel evaluations each ran their own Crossref rate limit | Crossref answered 429 and some references went unverified at random | One request schedule per process |

After the fixes the two affected samples moved from 60.9 to 63.9 (fenced proposal) and from
64.3 to 87.2 (bold headings); critical applicant claims across the 20 proposals went from 15 to
12, the largest change being a task where five claims came from the brief.

## What the run shows

| | Value |
|---|---|
| Score [95% CI] | 75.0 [66.5, 82.4] |
| Call responsiveness / substance / grounding | 90.5 / 66.3 / 94.2 |
| Samples with at least one critical applicant claim | 9 of 20 |
| Counted words as a share of the limit | 0.30 (median 2,219 words) |
| External references | none: 100 of 108 references are the applicant's own publications |
| Traps | 37; 30 respected, 6 not fully respected, 1 undecidable |

By scheme (one sample per task): AEI 81.9 and 75.9; ERC 82.5 and 83.6; Horizon Europe 57.7,
63.9, 68.3 and 63.6; MSCA 71.6, 61.6, 54.9 and 71.7; NIH 89.4, 74.9, 82.9 and 85.6; NSF 85.7,
74.8, 87.2 and 81.8. Two to four tasks per scheme support no per-scheme claim.

**Traps discriminate.** The six not respected, mostly with all three judges agreeing:
a Dutch host that breaks the MSCA mobility rule; a co-PI who does not meet the Spanish
affiliation rule; a renovation-health study confined to already-renovated blocks; replacing
clinical measurements by temperature and CO2 proxies; an "established" collaboration the dossier
says does not exist; a recruited cohort that is only planned. The undecidable one is a budget
trap in an NIH call whose narrative has no budget: a proposal that never mentions costs gives
the judges nothing to quote. Avoidance traps in calls without a narrative budget will be
redesigned.

**The evidence base is penalised as intended.** Gemini cited no outside literature in any
public proposal, so the evidence-base item scored 0 everywhere and the state-of-the-art item
lost its verified-reference criterion.

**Rubric behaviour.** Scheme items: the ERC and NIH items sat at the ceiling on these few
proposals; MSCA03 (supervision suited to the fellow, claims limited to the dossier) averaged
0.21. Grounding items are met almost always (see judge agreement): they do not separate
systems and will be complemented by task-specific grounding checks generated from each
dossier's salient facts and stated gaps.

## Judge agreement (pilot and public, 39 evaluations)

Krippendorff's alpha across the three judges (`meta/reliability.py`); binary atomic criteria
nominal, yes/partial/no items interval.

| Item family | Units | Alpha [95% CI] | All judges agree |
|---|---|---|---|
| Call exclusions | 70 | 0.89 [0.65, 0.98] | 94% |
| Traps | 64 | 0.85 [0.67, 0.96] | 92% |
| Generic items, atomic criteria | 1,058 | 0.72 [0.68, 0.75] | 82% |
| Call mandatory elements | 269 | 0.69 [0.57, 0.80] | 90% |
| Generic items, yes/partial/no | 222 | 0.69 [0.62, 0.75] | 68% |
| Scheme items, yes/partial/no | 119 | 0.67 [0.53, 0.78] | 73% |
| Scheme items, atomic criteria | 116 | 0.60 [0.38, 0.76] | 88% |
| Call outcomes and scope, atomic criteria | 855 | 0.57 [0.48, 0.64] | 89% |
| Grounding, atomic criteria | 254 | -0.01 [-0.02, 0.00] | 96% |

The grounding row is not disagreement: nearly every answer is "yes", so alpha has no variation
to explain. Call outcomes rose from 0.31 on the pilot alone to 0.57 once the public tasks
added proposals that miss some outcomes.

## Agent track on the pilot NIH task

| System | Score | Substance | Verified external references |
|---|---|---|---|
| Claude Code, Opus 5.5 (`cli-claude-code-opus`) | 96.9 | 92.2 | 22 |
| Reference agent, Claude Opus 4.6 | 94.5 | 86.2 | 6 |
| Codex, GPT-6 astra (`cli-codex-gpt-6-astra`) | 91.2 | 77.9 | 7 |
| Direct Gemini 3.1 Pro | 78.4 | 77.4 | 3 |
| Direct Claude Opus 4.6 | 78.2 | 85.3 | 13 |
| Direct gpt-oss-120b | 58.0 | 73.8 | 0 |

One task, one sample: the agents' retrieval shows in the evidence base, not yet a ranking.

## Agent track on the 20 public tasks

Same 20 tasks, one sample each, evaluated by the same panel and rubric as the Gemini run above
(Gemini re-evaluated after the rubric gained the task-specific grounding item GR-T; only the new
item was judged). Development numbers, not results.

| | Claude Code, Opus 5.5 | Codex, GPT-6 astra | Direct Gemini 3.1 Pro |
|---|---|---|---|
| Score [95% CI] | 93.0 [91.2, 94.7] | 91.7 [89.7, 93.8] | 74.9 [66.4, 82.4] |
| Call / substance / grounding | 98.8 / 86.8 / 98.8 | 98.9 / 81.7 / 99.0 | 90.7 / 65.9 / 94.2 |
| Traps respected | 36 of 36 | 36 of 36 | 30 of 36 (1 partial) |
| Samples with a critical applicant claim | 1 of 20 | 0 of 20 | 9 of 20 |
| Counted words, median (share of limit) | 5,648 (0.70) | 6,620 (0.76) | 2,188 (0.30) |
| External references verified / not found | 412 / 56 | 111 / 49 | 0 / 5 |
| Wall time per proposal, median | 294 s | 512 s | (one call) |

Paired over the 20 tasks: Claude Code minus Codex +1.3 points [0.0, 2.5] (14 of 20 tasks),
driven by substance, +5.1 [2.4, 7.4] (16 of 20); each agent minus Gemini +18.0 and +16.7, every
task. Codex ran in Docker with the task folder only; neither agent's output tripped the
contamination audit (repository paths, answer-key file names). Claude Code reported USD 21.89 of
API-equivalent usage for the 20 proposals; Codex ran on a subscription that reports no cost.

**The v1 traps no longer separate strong systems.** Both agents respected all 36 decidable
traps, and the task-specific grounding item scored 1.00 for both (the v1 dossiers have no
intentional gaps or inconsistencies). The 40 v2 tasks were designed for this: silent dossier
facts, reviewer criticisms in resubmissions, thin and inconsistent dossiers.

**Where the agents differ.** Substance (methods, work plan, risks, scheme items), the evidence
base and integrity: Codex cited fewer verified works and more that could not be found; Claude
Code had one critical applicant claim.

**Faults found and fixed during this run.** (1) DOIs written as Markdown links
(`[https://doi.org/X](https://doi.org/X)`) were parsed with the link syntax attached and never
resolved: 39 correct Codex references were flagged as metadata errors; after the fix 2 remain
(score 90.7 to 91.7). (2) Two judges returned nothing for one batch of eight items in one
proposal, so those items abstained; re-evaluation now retries absent answers (never a given
verdict), which cleared all seven abstentions.

**Judge agreement with the agent outputs** (pilot and public, 60 public evaluations):

| Item family | Units | Alpha [95% CI] | All judges agree |
|---|---|---|---|
| Generic items, atomic criteria | 2,306 | 0.77 [0.75, 0.80] | 88% |
| Traps | 144 | 0.78 [0.60, 0.91] | 94% |
| Scheme items, yes/partial/no | 224 | 0.65 [0.54, 0.74] | 75% |
| Scheme items, atomic criteria | 368 | 0.64 [0.49, 0.76] | 93% |
| Generic items, yes/partial/no | 486 | 0.64 [0.58, 0.69] | 69% |
| Call exclusions | 183 | 0.60 [0.29, 0.79] | 92% |
| Call mandatory elements | 566 | 0.59 [0.48, 0.69] | 90% |
| Call outcomes and scope, atomic criteria | 1,972 | 0.55 [0.47, 0.61] | 94% |
| Grounding, atomic criteria | 671 | 0.11 [-0.01, 0.24] | 98% |

Alpha for exclusions and traps fell while exact agreement stayed above 90%: the agents' proposals
sit near the ceiling, so there is little variance for alpha to measure. The same holds for
grounding.

**Calls corrected after this run.** Four v1 calls were re-rendered with corrected templates
(both Horizon Europe calls: open-science criterion in its official wording and the requested
EU contribution stated in the narrative; both NSF calls: EX1 states PAPPG 24-1's no-URL rule).
Item ids are unchanged. The numbers above were produced on the earlier wording; a re-evaluation
re-judges the reworded EX1 (judge runs now record the wording each item was judged against).
