> Fictional document created for ProposalBench.

# Final report: internal feasibility work, Post-Discharge Routines Study

Phase 1 (diary pilot, 2024–2025) and Phase 2 (electronic monitoring run, 2026)
Submitted to the Associate Dean for Research, CRU College of Nursing, 18 September 2026
PI: Audra N. Kesselring, PhD, RN. Co-investigators: Imani D. Okonkwo-Lattimore, PhD; Gareth P. Lindqvist, PhD (analysis planning, from July 2026).

## 1. Funding and approvals

| | Phase 1 | Phase 2 |
|---|---|---|
| Award | CRU College of Nursing Pilot Research Award, $25,000 | CRU Center for Behavioral Health Research Seed Supplement, $18,500 |
| Period | 1 July 2024–31 December 2025 | 1 March–31 August 2026 |
| CRU IRB protocol | STUDY2024-0177, approved 14 August 2024, closed 15 December 2025 | STUDY2026-0118, approved 2 April 2026; enrollment closed |
| Site | Ridgeline Transitional Care Clinic | Ridgeline Transitional Care Clinic |

Both awards were limited to feasibility aims. Neither phase was designed or powered to test associations, and no intervention was delivered in either phase.

Expenditure. Phase 1: research nurse $15,600; participant compensation (31 x $100) $3,100; loaner smartphones and data plans $2,800; EMA platform license $3,500. Phase 2: 16 MEMS Caps, 2 readers and software $4,960; research nurse $10,240; participant compensation (12 x $150) $1,800; supplies $1,500.

## 2. Phase 1: diary pilot (September 2024–May 2025)

**Methods.** Adults discharged home from CRH medical units within 7 days, with at least 3 scheduled daily oral medications. Recruitment 9 September 2024–28 March 2025: 118 screened, 52 eligible, 31 enrolled. Days 1–7: four EMA prompts per day (momentary stress, 0–10), one 3-minute mobile PVT per day, evening medication diary. Standard PSS-10 (past-month recall) at baseline and week 6; at week 6 a structured recall of missed doses in the previous 7 days.

**Participants.** Mean age 63.8 years (SD 11.2); 17 women (55%); 12 (39%) Black, 17 (55%) White, 2 (6%) other or more than one race; median 7 scheduled daily medications (IQR 5–9).

| Outcome | Result |
|---|---|
| EMA prompts completed | 660 of 868 (76.0%) |
| Mobile PVT sessions completed | 171 of 217 (78.8%) |
| Diary days completed | 189 of 217 (87.1%) |
| Completed week 6 | 26 of 31 (83.9%) |
| Intraclass correlation, momentary stress | 0.48 |
| Diary-reported doses taken, days 1–7, median | 97% (IQR 93–100%) |
| Week-6 recall: no missed doses in previous 7 days | 21 of 26 (81%) |
| Person-mean stress vs week-6 self-reported adherence | r = -0.31 (95% CI -0.62 to 0.09), n = 26 |

**Non-completers.** 5 of 31 participants did not reach week 6 (2 readmitted, 2 lost to contact, 1 withdrew). Their baseline PSS-10 mean was 24.2 (SD 5.1), against 18.9 (SD 6.0) among completers. Two of the five stopped diaries before day 4.

**Timing of regimen changes.** Clinic records show that 14 of 26 completers had a change to their medication regimen between day 8 and day 42, after the measurement window had closed.

## 3. Phase 2: electronic monitoring run (May–August 2026)

**Purpose.** To test whether electronic event monitoring, daily diaries and weekly visits can be run together for six weeks after discharge.

**Methods.** Enrollment 4 May–3 July 2026 (target of 12 reached); last visit 14 August 2026. 57 screened, 26 eligible, 19 approached, 12 enrolled. At enrollment, participants completed the standard PSS-10 (past-month recall), and one index medication per participant (scheduled once or twice daily) was placed in a MEMS Cap. Participants kept an evening diary (paper or smartphone) for all scheduled medications, with a separate entry for the index medication. Weekly visits in weeks 1–6, at the clinic or at home, included a past-week version of the PSS-10, the 3-minute PVT and a MEMS download. In the past-week version, prepared by Dr. Okonkwo-Lattimore, the stem 'In the last month' was replaced by 'In the last week'; the ten items and the 0–4 response scale were otherwise unchanged. The change was made because the standard past-month wording would give consecutive weekly administrations overlapping reference periods. Adherence data were not fed back to participants or clinicians.

**Participants.** Mean age 61.2 years (SD 12.9); 7 women; 5 Black, 7 White.

| Outcome | Result |
|---|---|
| Complete 42-day MEMS record | 10 of 12 |
| Incomplete records | 1 withdrew in week 2 after readmission; 1 cap lost in week 4 (24 days recorded) |
| Weekly visits completed | 63 of 72 scheduled (87.5%) |
| PVT completed at visits | 61 of 63 (97%) |
| Past-week PSS-10 completed at visits | 63 of 63 |
| Diary days completed (10 complete records) | 383 of 420 (91.2%) |
| Day-level agreement, diary vs MEMS (all index doses taken) | 330 of 383 days (86.2%); kappa 0.49 (95% CI 0.36 to 0.62) |
| Diary minus MEMS adherence, per participant | mean 7.4 percentage points (range -2.1 to 19.0) |
| MEMS correct-dosing days | median 88% (IQR 74–93%) |
| Past-week PSS-10, mean absolute change between consecutive completed visits | 3.6 points (SD 2.8; 49 visit pairs) |
| Past-week PSS-10, Cronbach's alpha (63 administrations pooled; clustering not taken into account) | 0.84 |
| Cap rated not at all or slightly burdensome at exit | 9 of 10 |

No association between stress, attention and adherence was estimated, given 10 complete records.

## 4. Missing-data analysis plan (August 2026)

After the summary statement, Dr. Lindqvist reviewed the Phase 1 dropout pattern (5 of 31 non-completers; baseline PSS-10 24.2 vs 18.9) and on 24 August 2026 delivered a written missing-data analysis plan for a six-week cohort with MEMS monitoring, diaries and weekly visits. The plan sets a primary linear mixed model for weekly MEMS correct-dosing proportions, valid under missing at random, and a pattern-mixture sensitivity analysis under missing not at random: three dropout patterns (after weeks 1–2, after weeks 3–4, completers), complete-case and neighbouring-case identifying restrictions, delta adjustment of post-dropout weekly adherence from 0 to -20 percentage points, and a tipping-point analysis. Where a MEMS record is incomplete, diary data enter only as auxiliary variables, because diary adherence exceeded MEMS adherence in Phase 2. The R code (mice, lme4) was tested on simulated data. The plan was not applied to Phase 2 data, whose 2 incomplete records are too few for pattern-specific estimates. It covers missing outcome data only; it does not address confounding and gives mediation estimates no causal interpretation.

## 5. Limitations

- Phase 2 was a feasibility run, not a validation study: one site, one index medication per person and 10 complete records. The kappa interval is wide and does not account for clustering of days within participants. The run does not establish MEMS as a criterion measure in this population; a cap opening records bottle access, not ingestion.
- The weekly stress measure was an adapted, past-week PSS-10. Apart from the pooled alpha above, its reliability and validity have not been evaluated in this population; its scores are not comparable with published past-month norms, with the Phase 2 enrollment score or with Phase 1 PSS-10 scores. With 10 to 12 participants, the 3.6-point week-to-week change cannot be separated from measurement error.
- Neither phase tested hypotheses or evaluated any intervention.
- Both phases recruited at Ridgeline only; there are no data from Lakevale or any other site.
- Phase 2 consent covered the MEMS Cap, diaries and weekly visits, and also review of the CRH discharge summary to record the discharge medication list, but not pharmacy-record access, linkage or recontact for that purpose (see resources.md). Neither phase obtained or linked pharmacy refill data.
- The missing-data plan of 24 August 2026 has not been applied to device data.

## 6. Data holdings

De-identified Phase 1 and Phase 2 datasets in CRU REDCap; MEMS event files for 12 participants (10 complete). Available to the study team under the approved protocols. A Phase 2 manuscript is in preparation and had not been submitted on 18 September 2026.
