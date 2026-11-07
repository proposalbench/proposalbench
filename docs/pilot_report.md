# Pilot report (M1)

The pilot ran the whole pipeline on three hand-checked tasks to find out where the evaluator
was wrong before any real task set exists. Its scores are development numbers, not results: the
evaluator changed many times during the pilot, and three tasks cannot rank systems.

## Setup

| | |
|---|---|
| Tasks | `pilot-he-soilwater-close` (Horizon Europe RIA, EN), `pilot-nih-r21-persistence` (NIH R21, EN), `pilot-aei-soledad-close` (AEI, ES) |
| Systems | `direct` baseline (one prompt with all inputs) on Claude Opus 4.6, Gemini 3.1 Pro and gpt-oss-120b |
| Samples | 2 per task and system (18 proposals) |
| Judge panel | Kimi K3, GLM-5, DeepSeek V3.2 (`configs/judges/panel-pilot.yaml`) |

## Scores after the last evaluator change (2026-10-31)

| System | n | Score [95% CI] | Call | Substance | Grounding | ≥1 critical defect | Words / limit |
|---|---|---|---|---|---|---|---|
| direct-claude-opus-4.6 | 6 | 85.7 [62.6, 94.9] | 98.4 | 86.2 | 100.0 | 33% | 0.57 |
| direct-gemini-3.1-pro | 6 | 85.4 [79.6, 91.9] | 93.9 | 72.6 | 99.1 | 0% | 0.29 |
| direct-gpt-oss-120b | 6 | 65.5 [46.5, 78.0] | 87.8 | 71.7 | 99.1 | 67% | 0.30 |
| agent-claude-opus-4.6 | 1 | 94.5 (NIH task only) | 100.0 | 86.2 | 100.0 | 0% | 0.83 |

Intervals are two-way cluster bootstrap over calls and dossiers with samples resampled within
tasks. With three tasks they overlap and say little. The reference agent has run on one task
only; on that task the direct baseline of the same model scored 88.2 before the last changes.

Observations:

- **Integrity separates systems more than quality does.** gpt-oss-120b invented applicant facts
  in four of six proposals and Claude Opus 4.6 (direct) in two, for example "EU project
  coordination experience" for partners the dossier describes only as network participants;
  quality scores were close.
- **Grounding sits at the ceiling.** Every system receives the dossier and uses it; the grounding
  items barely discriminate even after being split into atomic criteria. The public split's
  stretch tasks and traps are meant to test grounding harder.
- **Call responsiveness is near the ceiling for strong systems.** The expected-outcome items
  now need an activity, an owner, a time and a measure, but well-prompted frontier models meet
  them. Substance discriminates more.
- **Systems write short.** Gemini and gpt-oss used about 30% of the allowed length, Claude 57%.
  Length is not scored, but thin plans fail the substance items.

## What the pilot changed in the evaluator

All changes are logged with dates and reasons in `decision-log.md`. The main ones:

1. Single yes/partial/no verdicts were too lenient (a 2,246-word Horizon proposal against an
   18,000-word limit scored 85 on quality): leniency-prone items became atomic criteria with
   verbatim quotes, and the judges were told to take a demanding stance.
2. Judges accepted the applicant's own earlier project as "the state of the art": the item now
   counts only others' work, gated by a deterministic minimum of external references.
3. A misspelled co-author surname was deducted as a critical fabrication: claim severities follow
   explicit rules and need a majority.
4. Plan coherence (dates, work packages, budget, partners) is checked arithmetically on a fact
   sheet extracted by the judges; extraction first failed on every proposal (strict types,
   truncation) and was fixed before use.
5. The reference checker misread real references: Vancouver and Pensoft formats, records
   without subtitles, and parse errors that turned real papers into "misattributed" ones. On the
   anchor set of real proposals this went from 222 of 598 references to none.

## Cost and time

| System | Output tokens (6 proposals) | Wall time per proposal |
|---|---|---|
| direct-claude-opus-4.6 | 74,724 | 6.4 min |
| direct-gemini-3.1-pro | 49,175 | 1.1 min |
| direct-gpt-oss-120b | 31,247 | 5.6 min |

Evaluation used about 8.9 million input and 2.3 million output judge tokens for the 18
proposals (all three judges, all judged stages): roughly 500,000 input and 130,000 output
tokens per proposal. Reference verification is cached and costs nothing after the first run.

## Power

From the pilot's sample-to-sample standard deviation (11.6 points), the minimum detectable
difference between two systems at 80% power with Holm correction over two comparisons is about
8.0 points with 20 tasks and 5.6 with 40 (`pb power`). These are lower bounds: three tasks gave a
between-task variance of the system difference of zero, which is certainly an underestimate.
The public split will re-estimate both components before the sealed split is sized.

## Open after the pilot

- Judge selection on the flaw-injection results (`meta/perturb/`), including Spanish.
- An OpenAlex API key (keyless OpenAlex is off; verification relies on Crossref and Semantic
  Scholar) and a Crossref contact address for the polite pool.
- Baselines beyond direct prompting: the reference agent and frontier models not available on
  the current accounts (Claude Opus 5.5, GPT-6.x).
