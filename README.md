# ProposalBench

An open benchmark for **call-conditioned research proposal writing**: given a funding call and an
applicant's prior research, write the proposal.

Every system gets the same inputs (a call, the applicant's dossier, an optional brief and fixed
instructions) and returns one Markdown proposal. An open harness scores it with deterministic
checks, verification of every reference against scholarly indexes, and a judge panel drawn from
model families that no compared system uses.

**What the score means.** ProposalBench is an automated assessment of call responsiveness, plan
coherence and integrity against specified requirements and a catalogue of documented defects. It
does not measure whether a proposal would be funded, and it has not been calibrated against human
panel scores. See [`docs/limitations.md`](docs/limitations.md).

## Results: November 2026 run (`public-v1`)

<!-- results:start -->
| # | System | Type | Score [95% CI] | Cost per proposal | Minutes per proposal |
|---|---|---|---|---|---|
| 1 | Proposia Pro | product | 96.6 [94.6, 98.0] | not disclosed | 13.2 |
| 2 | Claude Code (Opus 5.5) | agent | 93.3 [90.9, 94.9] | $1.31 † | 6.8 |
| 3 | Claude Opus 5.5 | single prompt | 92.3 [90.2, 93.8] | $2.33 † | 14.4 |
| 4 | Codex (GPT-6 Astra) | agent | 89.4 [75.9, 93.3] | ≤$6.01 † | 7.7 |
| 5 | GPT-6 Astra | single prompt | 88.8 [86.6, 90.8] | ≤$0.60 † | 4.0 |
| 6 | GPT-6 Sol | single prompt | 86.5 [83.2, 89.0] | ≤$0.11 † | 2.1 |
| 7 | Claude Haiku 5.5 | single prompt | 83.3 [79.1, 86.6] | $0.01 † | 1.7 |
| 8 | GPT-6 Luna | single prompt | 79.5 [67.1, 84.5] | ≤$0.01 † | 1.0 |
| 9 | Claude Sonnet 5.5 | single prompt | 78.2 [58.7, 89.5] | $0.32 † | 3.2 |
| 10 | Gemini 3.1 Pro | single prompt | 75.4 [68.7, 81.5] | $0.13 est. | 1.2 |
| 11 | Baseline agent (Claude Opus 4.6) | agent | 68.0 [48.5, 82.1] | $3.75 est. | 14.8 |
| 12 | Gemini 3.8 Flash | single prompt | 59.8 [37.7, 76.4] | $0.06 est. | 1.9 |

Sample 1 of every system on the 34 public tasks that Proposia Pro was not developed on. Scores run from 0 to 100; intervals are a two-way bootstrap over calls and dossiers. Cost and time are medians per proposal and are not scored: *est.* is recorded tokens × list prices, *≤* an upper bound (cache hits priced as uncached input), and † the API-equivalent cost of a run made on a subscription. Proposia Pro is a commercial product; its generation cost is not disclosed.
<!-- results:end -->

Proposals were generated between 31 October and 6 November 2026 and judged with the same panel.
The full analysis (pairwise comparisons, results by funding scheme, integrity metrics, judge
agreement, and the proposals themselves) is at **[proposia.ai/benchmark](https://proposia.ai/benchmark)**.
The numbers come from [`release/2026-11/`](release/2026-11/), written by `pb export --release 2026-11`;
the other 11 systems are also reported there on all 60 public tasks.

## Disclosure

ProposalBench is built and maintained by Proposia, whose product, Proposia Pro, is one of the
systems evaluated. So that the result can be checked rather than trusted:

- Proposia Pro was developed against 26 of the 60 public tasks and is reported only on the other
  34 ([`configs/release/2026-11.yaml`](configs/release/2026-11.yaml) lists both sets).
- The three judges (Kimi K3, GLM-5 and DeepSeek V3.2) come from model families that no evaluated
  system uses.
- Every task, rubric, prompt, generated proposal and judgment is released, and
  [`docs/decision-log.md`](docs/decision-log.md) records every change that could favour or
  disfavour a participant, with its reason.
- An earlier Proposia version was evaluated during development; its results are not reported.
- v1.0 has no sealed split: every result is on public tasks.

## How a proposal is scored

- **Admissibility.** A failed output (under 300 words), a proposal in the wrong language, or one
  over a length limit the funder enforces by rejection (NIH, NSF, AEI) scores 0. Where funders
  disregard excess text (Horizon Europe, ERC, MSCA), it is cut before judging.
- **Quality** = 0.4 × call responsiveness + 0.4 × substance and plan + 0.2 × applicant grounding,
  from checklist items judged by the panel (atomic yes/no criteria, median of the judges) and
  deterministic checks.
- **Integrity deductions**, fixed points per defect: 10 for a claim about the applicant that the
  dossier does not support, 4 for a misattributed or non-existent reference or a citation of an
  unrelated work, 0.5 for minor defects (capped at 5).
- **Score** = max(0, quality − deductions).

Details: [`docs/scoring_spec.md`](docs/scoring_spec.md) and [`docs/methodology.md`](docs/methodology.md).
Checks on the scorer itself (flaw injection, meaning-preserving edits, real funded proposals):
[`docs/meta_evaluation.md`](docs/meta_evaluation.md).

## Layout

```
data/<split>/calls/<id>/        call.md (given to systems) + call.yaml (hidden answer key)
data/<split>/dossiers/<id>/     applicant files (given) + dossier.yaml (hidden)
data/<split>/tasks/<id>/        task.yaml pairing one call with one dossier (+ optional brief.md)
src/proposalbench/              harness: tasks, parse, checks, evidence, judge, scoring, systems
rubrics/  lexicons/  configs/   checklist items, word lists, systems, judge panels, releases
tools/authoring/                task design, scheme skeletons, synthesis, and every draft and
                                cross-family review of the public split
meta/                           checks on the scorer: flaw injection, invariance, anchors
release/<release>/              the published numbers of a release
```

## Quick start

```bash
uv sync
uv run pb tasks validate
uv run pb tasks export <task_id> --out /tmp/bundle   # exactly what a system receives
uv run pb run --system direct-gemini-3.1-pro --split public --samples 1 --max-usd 10
uv run pb evaluate --system direct-gemini-3.1-pro --split public --eval-id my-run --max-usd 100
uv run pb report --eval-id my-run
```

Copy `.env.example` to `.env` and fill in the keys you use. Judging calls three models on Amazon
Bedrock and cost about $2.40–3.00 per proposal in this run; both `pb run` and `pb evaluate` stop
starting new work once a `--max-usd` cap could be passed.

## Submitting a system

See [`CONTRIBUTING.md`](CONTRIBUTING.md): systems are added through a config in
[`configs/systems/`](configs/systems/), and model labs and grant-writing tools are welcome to
submit theirs.

## Citation and licences

Cite with [`CITATION.cff`](CITATION.cff). Code: Apache-2.0 ([`LICENSE`](LICENSE)). Task data,
proposals and judgments: CC BY 4.0 ([`LICENSE-DATA`](LICENSE-DATA)), with sources listed in
[`data/ATTRIBUTION.md`](data/ATTRIBUTION.md).
