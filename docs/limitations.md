# Limitations

This page states what a ProposalBench score does and does not establish. It is updated with each
version; the entries below describe v0.1 (pilot).

## What the score measures

An automated assessment of a proposal against the requirements of one specific call and against a
catalogue of documented defects (`docs/pitfall_taxonomy.md`): whether the expected outcomes and
mandatory elements are planned concretely, whether the plan and methods give the information an
evaluator needs, whether the applicant's own record is used and not invented, and whether cited
works exist and fit the sentences that cite them.

## What it does not measure

- **Fundability.** No human evaluation panel has scored ProposalBench proposals. Published studies
  find that LLM ratings of grant proposals correlate only weakly with panel scores (Spearman
  ρ ≈ 0.22–0.26). A high score means the checklists were satisfied, not that the proposal would be
  funded.
- **Scientific originality.** Checklists can verify that novelty is positioned against named prior
  work; they cannot judge whether the idea is good.
- **Agreement with human reviewers.** v0.1 has no human calibration. The judge panel is validated
  only by flaw-injection tests, invariance tests and agreement between judges (`docs/methodology.md`).
  Agreement between judges can reflect shared mistakes.

## Known weaknesses of v0.1

- **No human review of the tasks.** Calls, dossiers, briefs and traps were drafted, reviewed and
  revised by models (three families, cross-family review, then an in-depth review by GPT-6 astra
  with web search). No person checked them. Errors a model reviewer shares with the authors can
  remain, and units drafted by GPT-6 were reviewed in depth by their own model family.

- **Judge leniency.** LLM judges are optimistic. The first pilot run showed a proposal at 12% of
  the allowed length scoring 85 on quality with single yes/partial/no verdicts. Items were then
  split into atomic criteria (see `docs/decision-log.md`); whether this is enough is measured,
  not assumed, by the flaw-injection suite.
- **Abstract-only claim checks.** Whether a cited work supports a sentence is judged from its
  abstract. Most specific results are not in abstracts, so most checks end as "cannot tell", which
  is neutral. The check catches unrelated or contradicted citations, not subtle misreadings.
- **Unverifiable references are not penalised.** A reference no index can find may be a fabrication
  or a legitimate book, report or non-English work. v0.1 never deducts for "not found"; fabrications
  that happen to be unfindable therefore cost nothing unless their DOI is wrong or their authors are
  attached to a different real work.
- **Word limits approximate page limits.** Funders set page limits; ProposalBench converts them to
  word limits with a stated words-per-page figure and a 3% tolerance. A proposal near the limit may
  be admissible here and not in the funder's portal, or the reverse.
- **Synthetic tasks.** Calls, people and institutions are fictional (the science and literature are
  real). Fictional calls cannot carry the unwritten priorities of a real programme, and fictional
  applicants cannot be looked up, which removes a source of grounding that real systems might use.
- **Contamination.** Canary strings, n-gram exclusion against seeds and fictional names are
  diagnostics; they do not prove that a model has not seen similar material.
- **Scale.** The pilot has three tasks. Differences between systems are reported with intervals from
  a two-way cluster bootstrap over calls and dossiers; with few clusters the intervals are wide, and
  the benchmark makes no per-scheme or per-component claims.
- **Languages.** Tasks are in English and Spanish only. Style diagnostics for Spanish use a short,
  unvalidated word list and no human baseline yet.

## Conflict of interest

The benchmark is built and maintained by Proposia, whose product is evaluated as a participant. It
was developed on 26 of the public tasks and is reported only on the other 34; there is no sealed
split in v1.0. The safeguards and every relevant decision are in `docs/decision-log.md`. Users
should weigh any Proposia result accordingly.
