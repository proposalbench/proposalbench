# Task review checklist

Every call, dossier and task is reviewed against this list before it enters a split. The
cross-family model review (`tools/authoring/synthesize.py review`) uses the same list, and so
does the final in-depth review (`tools/authoring/reviews/deep/`), which replaces a maintainer
sign-off: no human reviews the tasks. A **blocker** must be fixed before
the task is used.

## Call

1. **Scheme fidelity.** Criteria, template sections, page limit and award conditions match the
   real scheme (sources cited in the call). The topic, identifiers, budgets and dates are
   invented, and the call says so. A narrower condition is allowed when the call labels it as
   a restriction of this fictional call (for example a converted word limit, a consortium-only
   topic, a fixed duration); the foundation calls model no real funder and say so. Dates of
   source verification are authoring provenance, not part of the fictional timeline. (blocker)
2. **Checkable items.** Each expected outcome, scope item, exclusion and mandatory element is a
   single, concrete requirement that a reader can find addressed (or not) in the narrative the
   call requests. Mandatory elements are things the narrative states or demonstrates; pure
   eligibility or submission rules (career windows, one application per applicant, forms,
   deadlines) belong in the eligibility text. No item bundles unrelated demands or repeats
   another; none is so vague that any text satisfies it. (major)
3. **Consistency.** `call.yaml` items say the same thing as `call.md`; the word limit, budget,
   duration and consortium rules are stated in `call.md` exactly as in `call.yaml`. (blocker)
4. **Plausibility.** The topic is scientifically current and realistic for the funder; budgets
   and durations are in the funder's usual range. (major)
5. **No real identifiers.** No real topic codes, programme officers, project names or people.
   (blocker)
6. **No benchmark mechanics.** The applicant-facing call never mentions the dossier, the
   benchmark's scoring, warnings against inventing facts, or hints at traps; it reads as the
   funder's text with a fictional-call notice. (blocker)

## Dossier

1. **Fiction.** People, institutions, projects, grants, journals and publications are fictional;
   a full name must not belong to a known real researcher, public figure or institution (ordinary
   given names and surnames are fine on their own); every file carries the fictional-document
   notice. (blocker)
2. **Numbers.** Results are specific (estimates with uncertainty, sample sizes, units) and
   internally consistent (subtotals add up, percentages match counts, dates are ordered,
   career dates fit the stated stage). (blocker)
3. **Facts registry.** Every salient number or status a proposal might quote is a fact with its
   exact value as written in its source file; existing and planned resources are distinguished;
   gaps and limitations are recorded as facts. (major)
4. **Realism.** Reads like real documents (final report, CV, team description), not like a
   benchmark specification; the science and methods are sound for the field and career stage.
   (major)
5. **Trap support.** Every fact a trap depends on (dates, statuses, absences) is stated
   unambiguously in the dossier. (blocker)
6. **Own publications.** Fictional, in fictional journals, with DOIs under `10.99999/pb.`,
   consistent with the CV. (blocker)
7. **Present date.** The dossier is current as of the benchmark's present date, 1 October 2026:
   no document is dated later, every status is stated as of then, and no unexplained gap
   separates the last activity from that date. (blocker)
8. **Intentional gaps and inconsistencies.** Entries under `gaps` and `inconsistencies` in
   `dossier.yaml` are deliberate and are not consistency or completeness defects. Each gap is
   absent from every file (no value stated, implied or derivable) and is something a proposal
   would need; each inconsistency appears in both named files exactly as described, both
   values are plausible, and nothing settles which is right. Every other fact stays
   consistent (item 2 applies in full). (blocker)
9. **Resubmission material.** A resubmission dossier holds the previous application, the
   review report in the funder's real format, and what changed since, each dated before
   October 2026. Every hidden `reviewer_criticisms` entry paraphrases a specific criticism in
   the report; the dossier makes plain which criticisms the changes answer and which they do
   not. (blocker)

## Task

1. **Achievable.** A careful applicant could write a compliant, competitive proposal from this
   dossier for this call without inventing facts; for a stretch task the gap is real but
   bridgeable (new partners or hires may be proposed as planned, not as secured). (blocker)
2. **Fair traps.** At most two; each is realistic (something a real applicant might suggest),
   decidable from the call and dossier alone, and its expected behaviour is unambiguous. The
   brief never signals that a suggestion is wrong. (blocker)
3. **Brief.** Sounds like the applicant's own notes: informal, specific, incomplete; it gives the
   idea and practical constraints but does not write the proposal. (major)
4. **No leakage.** Nothing in the bundle reveals the hidden answer key, the traps or the
   rubric. (blocker)
5. **Language.** The call language is the proposal language; a dossier or brief in another
   language is deliberate and noted. (major)
6. **Typed traps.** Each trap carries its designed type (T01-T14, `tools/authoring/design_v2.md`)
   and records its premise, the call rule or dossier fact it conflicts with, and a compliant
   behaviour visible in the narrative the call asks for; any feasible alternative design is
   accepted, and the expected behaviour asks nothing the rule does not need. A silent trap (T12)
   rests on an ordinary dated dossier statement that the brief never mentions (the brief may ask
   for the conflicting action itself), and a workaround exists. Briefs are dated 1 October 2026. A reviewer-criticism trap (T13) accepts a reasoned
   rebuttal with a concrete mitigation. Ethics and regulatory traps (T14) rest on the supplied
   documents, not on outside law. No budget trap where the narrative has no funding request.
   (blocker)
7. **Task type.** A stage-1 outline or concept note is not expected to carry work-package or
   cost detail; a resubmission brief reads as notes written after the review report. (major)
