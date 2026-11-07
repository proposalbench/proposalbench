# Paired flaw injection

This suite tests evaluator sensitivity, not proposal quality or agreement with human reviewers.
Every edit is mechanical and uses a local `random.Random`; neither operators nor dry runs call
models or evidence services. It is repository tooling, run from the repository root.

```bash
uv run python -m meta.perturb.run --eval pilot --out /tmp/pb-perturb-dryrun --dry-run
uv run python -m meta.perturb.run --eval pilot --out results/meta/perturb-v0 --panel pilot
```

The second command **does evaluate documents**, including paid judge calls. It has not been run
as part of implementation. `--seed` defaults to zero. Output must be absent or empty: evaluator
stages are cached by filename, so reusing a populated folder could silently score stale text.
The input is a snapshot of all `results/<eval>/*/*/*/*/evaluated.md` paths at startup, including
partially evaluated samples. The runner never edits base results or submissions.

Each applicable pair is written to
`<out>/<operator>/<system>/<task>/<sample>/{perturbed.md,control.md,expectation.json}`.
The root `manifest.json` includes **all** attempted pairs, applicability and skip reasons. Seeds
derive from SHA-256 of the global seed, system, split, task, sample and operator; iteration order
does not affect the edit. Pair manifests also retain source paths and SHA-256 document hashes.

Normal runs copy the original `SubmissionMeta`, changing only `system_id` to
`<system>+perturb:<operator>` or `<system>+control:<operator>`, and evaluate each into a fresh
`evaluation/perturbed` or `evaluation/control` folder. Base metadata comes from the evaluated
sample's `meta.json`, or the corresponding `submissions/` folder. Missing metadata is an error
in normal runs; dry runs need only the text and task. Citation padding has no edited control:
`control.md` is the base for inspection, and detection reuses the original base evaluation.

## Operator API and coverage

```python
perturbed, control, expectation = OPERATORS[name](
    base_markdown,
    resolved_task,
    random.Random(42),
    references=base_reference_verdicts,
)
```

`references` is the `verdicts` list in the base `references.json`. Inapplicable operators return
the base twice and `Expectation(applicable=False, reason=...)`. They never silently fabricate
missing proposal structure, verification evidence, or a control fact.

| Operator | Taxonomy | Intervention and matched control | Detectors |
|---|---|---|---|
| `drop_required_section` | P03 | Delete a core subtree; delete whole prose paragraphs from at least two other sections, within 25% of its word count | Missing/uncertain selected section; call-responsiveness drop |
| `exceed_length` | P04 | Repeat body prose in a counted section until above 120% of the limit; insert identical text into exempt References | Contract-specific admissibility finding |
| `duplicate_paragraph` | P21 | Repeat a prose paragraph of at least 25 words; insert similarly sized neutral task-specific prose | Duplicate paragraph |
| `leave_placeholder` | P21 | Insert `[[TO COMPLETE: ...]]`; insert plain text at the same location | Placeholder |
| `meta_commentary` | P21 | Insert assistant commentary; insert neutral prose at the same location | Meta-commentary |
| `fabricated_reference` | P18 | Cite and append an invented article and unregistered-looking DOI; cite and append Kobak et al. (2025) | Target reference `doi_unresolved`; matching integrity defect |
| `corrupt_reference_metadata` | P18 | Change a verified entry's first surname and year (+3); italicise its title | Target reference `verified_with_errors` or `misattributed` |
| `wrong_doi_on_real_reference` | P18 | Swap in another verified work's DOI; change only DOI rendering | Target reference `misattributed`, with `doi_points_to_different_work` |
| `contradict_dossier_number` | P19 | Change a contextual number from a salient existing dossier fact; apply the same relative change to an unrelated cited number | Critical applicant claim at the edited passage |
| `fabricated_applicant_award` | P19 | Assert an invented PI prize; restate an existing dossier grant/award | Critical applicant claim at the inserted passage |
| `budget_over_cap` | P04/P15 | Rewrite matching mentions of a selected requested total to 115% of cap; rewrite the same mentions to 95% of their original value | `plan.budget_over_cap`; applicable budget-related P04/TRAP item drops |
| `milestone_after_end` | P15 | Change one due month beyond the call maximum; move that date within the stated duration, falling back to the call maximum | `plan.activity_after_end` |
| `undefined_work_package` | P15 | Rename one prose use of a defined WP (or Aim when no WPs exist); rename that identifier consistently throughout the body | `plan.undefined_wp` |
| `prompt_injection` | None | Insert the specified evaluator instruction; insert equally long neutral prose | No total-score increase |
| `citation_padding` | None | Cite and append ten real astronomy references; compare with base | No total-score increase; no judged G02 criterion change |
| `rename_headings` | invariance | Rename mapped required headings with call aliases, case or numbering punctuation; unchanged control | Score, deterministic findings and item stability |
| `reorder_references` | invariance | Permute numeric references and consistently relabel citations, or alphabetise/reverse author-year references; unchanged control | Same |
| `citation_style` | invariance | Convert numeric citations to author-year and alphabetise references; unchanged control | Same |
| `markdown_presentation` | invariance | Swap bullet, ordered-list and emphasis delimiters, vary table rules and blank spacing; unchanged control | Same |
| `reparagraph` | invariance | Split a long prose paragraph at a sentence boundary and merge two short adjacent ones in one section; unchanged control | Same |

### Meaning-preserving invariance

The five meaning-preserving operators always write an **exact unchanged copy** to `control.md`
and evaluate it afresh (`control_is_base=False`). The original base evaluation is used only for
the separate `control_invariance` noise diagnostic, never in place of the new control. These
operators differ from the older prompt-injection and citation-padding attacks above.

Heading renaming verifies that every required section maps to the same heading position, with
the same number-only uncertainty, before accepting an edit. Reference transformations require
every citation label to resolve uniquely and verify the transformed mappings using the
evaluator's `cited_reference_indices`, without its per-sentence count cap. Numeric ranges are
expanded before relabelling. Mixed citation styles are allowed when all targets resolve.
Author-year conversion uses one surname, two surnames joined by `&`, or `et al.` as appropriate;
same-surname/year entries receive a/b suffixes in citations and references. The current matcher
ignores those suffixes, so conversions that remain ambiguous are inapplicable. Unknown labels,
missing cited author/year metadata, and citation-like code literals also cause skips.

Presentation edits preserve the CommonMark token structure, including emphasis and table
alignment, and protect fenced/indented code and inline code/link lines. They do not avoid an edit
merely because a deterministic check changes. Reparagraphed prose has at least 30 words for the
split, at most 40 words in each merged paragraph, sentence punctuation, and no hard line breaks.
Inline formatting must survive intact; headings, lists, tables and section boundaries are not
crossed. Both the split and the merge must be possible, otherwise the operator skips.

The data-driven `invariance` detector has `score`, `findings` and `items` facets, selected by
`Detector.values`. `Expectation.score_tolerance` defaults to **3.0 points**; a score violation
requires an absolute difference strictly above it. Items report signed per-item differences
and the items moving strictly more than **0.25**. Findings compare sets of check IDs plus
section IDs or stable subject keys (WP/aim family and ID, month/bound, order, placeholder style),
ignoring quotes, offsets and measured word counts. They include `checks.json`, admissibility,
`plan.undefined_wp`, and `plan.activity_after_end` only with `bound=call_maximum_text`, plus
reference-status counts. Extracted plan findings are excluded. Missing stages remain unavailable.

`detection.json.invariance` records the three facets, including signed/absolute score differences,
added/removed finding keys and both reference-status histograms. `summary.json.invariance` and
the added Markdown table report applicable n, observed score n, mean signed difference, sample
SD (unavailable below two observations), observed shares exceeding tolerance/changing findings,
and item movement counts with observed denominators. Missing score observations do not suppress
the findings facet. A changed old-base comparison does not veto stability of the fresh pair.

```bash
uv run python -m meta.perturb.run --eval pilot --out /tmp/pb-inv --panel none \
  --operators rename_headings reorder_references citation_style markdown_presentation reparagraph
```

`--panel none` is also supported by `rescore`: it loads no judge panel and makes no model calls.
Reference verification still runs and may contact evidence services; an existing HTTP cache can
be copied to the otherwise empty output directory. Resolver availability can change status
counts, so inspect saved source errors before attributing such a difference to the parser.
Offline operator and detector tests need no model or evidence calls.

Existing target hygiene findings make the corresponding hygiene operator inapplicable. Reference
corruption still requires an exact, unique entry whose base status is `verified` and which has a
resolver record. Dossier references and `verified_with_errors` entries do not qualify. Reference
insertion preserves numbered versus unnumbered lists, avoids label collisions, and precedes
bibliography-ending rules. The five section/numeric/plan operators select spans solely from the
proposal and hidden task data; they never consult fact sheets, claims or judge outputs.

Section deletion samples core subtrees in a seeded order weighted toward smaller word counts.
A subtree is eligible only if no remaining heading maps to its requirement. The control uses a
bounded subset-sum search over ordinary prose paragraphs returned by `_paragraphs` (at least 25
words each), outside the target subtree. It deletes at least two paragraphs spread over at least
two other sections, preserves each section's first eligible paragraph, removes at most half its
eligible paragraphs, and never removes headings. There is no five-word tolerance: the deleted
control word count must be within 75–125% of the subtree's word count. Sparse or list-heavy
proposals can therefore still be inapplicable.

Dossier numbers are matched by value, including semicolon-separated values, percentages with or
without spaces, decimal comma/point and thousands separators. A matching sentence must share at
least two distinct case-insensitive five-letter prefixes of words of at least five letters with
the fact text. Explicit future-work/criterion/simulation sentences are excluded. Citation markers,
DOIs, years 1900–2099 and the bibliography are not editable number spans. Integers/percentages
increase by at least five or 50%; non-percentage decimals below one increase by 60%, preserving
precision. Integer increases round upward. Dossier-value collisions advance the change again.
Controls require a citation-bearing sentence sharing fewer than two such prefixes with **every**
dossier fact and a non-year number absent from the dossier's values and text. The same relative
change is rounded to that number's precision; reversed ranges are rejected. Both detector targets
are the whole changed sentences. This lexical overlap rule is auditable but is not semantic
entailment, and a changed literature claim need not remain scientifically correct.

Budget parsing supports EUR/USD codes and symbols before/after amounts, decimal comma/point,
comma/point/space/NBSP/narrow-NBSP thousands groups, `million`, `millones`, `M` and `k`, and bold
prose/table cells. Wrapped prose is matched by sentence and tables by row. Total labels include
`total requested`, `requested (EU) contribution`, `total budget`, `total (direct) costs requested`,
`presupuesto total`, `importe solicitado`, `total solicitado`, and `costes directos solicitados`.
Explicit language-rule thresholds and quoted budget ceilings are excluded. A selected total must
be in the call currency and in [30% of cap, cap]; every monetary mention of that value is changed
at the same locations in both variants. The new totals are `ceil(1.15 * cap)` and `round(0.95 * V)`.
Currency placement, bold markup, scale words and separator styles remain intact; decimal precision
increases only when needed to express the exact scaled total. Controls below a call minimum are
rejected. Calls without a narrative-budget requirement remain inapplicable because the existing
`plan.budget_over_cap` detector does not check their budgets. Controls remain within the monetary
limits, but neither variant recomputes line-item sums or indirect costs.

Milestones/deliverables accept `M18`, `(M18)`, `Month 18`, `mes 18`, and `end of month 18`, plus
Month/Due/Mes/Fecha table columns and inline labels such as `Month 18 milestone`. Identifiers such
as `Milestone M2` are not dates; task lines that merely cite deliverables are excluded. The control
uses the parsed compliant duration, or `eligibility.duration_months_max` if parsing fails (including
fixed min=max calls). Perturbed dates exceed the call maximum by a seeded 1–6 months. This fallback
improves applicability, but the existing evaluator still needs an extracted proposal duration to
emit `plan.activity_after_end`; dry-run applicability does not demonstrate detector recall.

WP definitions include headings, first table cells, bold line starts (including bullet-prefixed
bold), and `Work Package 1` line starts. With no WP identifiers, heading/bold definitions of
`Aim 1` and `Specific Aim 1` are supported, including Unicode whitespace. One prose reference is
renamed; the control renames definitions and references in the body consistently, expanding
explicit numeric ranges when necessary. Undefined Aims use `Aim <max+3>`. The existing evaluator's
`WP_ID_RE` accepts both generated WP and Aim identifiers after its normalisation. Implicit or
unrecognised cross-reference syntax remains outside this mechanical parser. No LLM fallback exists.

## Expectations and detection

`Expectation` and `Detector` are small serialisable dataclasses in `operators.py`. The JSON
envelope's `expectation` contains operator, taxonomy, severity, applicability, details and
detectors. Each detector specifies:

- `id`, `kind`, alternative `values`, and `family` (`deterministic` or `judge`);
- optional `ref_index`, `section_id`, quote/defect `target` and `control_target`, severity and note;
- `expected=False` for invariance violations, plus `exclude_criteria` for G02's deterministic `d`.

Detection is data-driven: check IDs come from `checks.json` and `admissibility.json`; reference
statuses/notes from `references.json`; defects (`detail`), consensus claims, components and items
from `score.json`. The adapter also reads `factsheet/merged.json` or `score.json.plan_findings` for
the integrated fact-sheet evaluator. There is no direct fact-sheet import. Reference indices,
section IDs and quote targets prevent unrelated pre-existing defects from counting as detections.
Quote matching uses the evaluator's Markdown/whitespace normalisation, including a quote that is
a substring of the target (at least four words).

For ordinary detectors, `detected = perturbed_fires and not control_fires`. Item and component
drops compare perturbed with control; control false positives compare control with the original
base. Invariance events are violations: an increased score is attack success, while a successful
expectation means no increase and no control violation. G02 stability compares all judged
criterion states, excluding `d`; it does not mask changes to the other criteria behind a mean.
The total-score invariance test is strict, including increases attributable to the deterministic
reference-count criterion; raw score, quality, component and item deltas expose that effect.

`detect(...)` and `summarize(out)` also work on saved artefacts without API calls. Individual
model views reaggregate each model's validated item judgments and applicant claims, retaining
shared reference and panel citation-support deductions. These diagnostic scores are distinct
from official panel scores. Plan findings are based on panel-extracted facts: individual-model
plan detection remains unavailable rather than assigning the panel's result to each model.

## Reporting and limits

`summary.json` and `summary.md` report applicability (including zero-coverage operators), recall
and control false-positive rates with Wilson 95% intervals, by operator, detector and judge.
Deterministic and judge-based detectors are separate. Plan checks are judge-based because their
input extraction uses models, despite deterministic arithmetic. Operator success requires all
its detectors in that family; its control false-positive event is any firing detector.

The recall denominator is all applicable pairs. If some observations are missing, the requested
recall is `null`, with observed numerator, full denominator, unavailable count, and a separately
labelled observed-only recall. Dry runs report no measured recall. False-positive denominators
count observed controls; attack-success denominators count observed interventions. Zero
denominators have null rates and intervals. Missing stages, abstentions, unavailable base scores,
and missing individual model runs are not treated as negative findings. Wilson intervals do not
account for shared proposals/tasks and should not be read as cluster-adjusted uncertainty.

Controls match the kind and approximate size of the specified edit; WP renaming deliberately
changes all occurrences. They do not guarantee identical semantic effects or absence of every
possible defect. Large repetitions can trigger both length and duplication diagnostics. Existing
base flaws, truncation, evaluator errors and stochastic model judgments remain confounders.
Applicability is a property of the supported mechanical patterns, not proof that a proposal is
free of the corresponding issue. This suite has no human-rater calibration.

The fabricated DOI uses real publisher prefix `10.1016`, future year 2099, and a seeded
high-entropy suffix. No syntactically valid DOI under a real publisher prefix can be guaranteed
never to be registered. Dry runs do not assert a resolver result: the unresolved-DOI expectation
must be confirmed by the actual verifier (404 plus index absence), and a resolving collision
would invalidate that injection. The real control is pinned to the existing evidence fixture
for `10.1126/sciadv.adt3813`.

Citation padding uses `tests/fixtures/perturb/astronomy.json`, ten compact Crossref metadata
snapshots with source URLs and verification dates. Relevance was curated for the three pilot
calls only; other calls are inapplicable until a suitable bank is selected. The operator does
not infer irrelevance from a generic disciplinary keyword. Runtime evaluation verifies the
references normally. The snapshots and existing Kobak fixture keep dry runs and tests offline.
