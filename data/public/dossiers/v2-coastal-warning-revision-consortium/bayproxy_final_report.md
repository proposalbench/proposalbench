> Fictional document created for ProposalBench.

# Final report: BAYPROXY (2021–2024)

**Rapid faecal-contamination proxies and overflow-driven exceedance forecasting for Galway Bay bathing waters**

Funded by the EPA Research Programme 2021–2030, grant 2021-W-MS-47, EUR 398,000, 1 April 2021 to 30 September 2024 (including a six-month no-cost extension). Lead organisation: Cladach Institute for Coastal Science (CICS), Galway. Principal investigator: Dr Sorcha Mulqueeney. Report submitted 20 December 2024.

## 1. Objectives

1. Calibrate a rapid proxy for faecal contamination, combining tryptophan-like fluorescence (TLF) and β-D-glucuronidase (GLUC) activity, against culture-based *E. coli* in the Corrib estuary and inner Galway Bay.
2. Relate storm-overflow spills, rainfall and tide to exceedances at four designated bathing waters (B1–B4).
3. Describe how beach users receive water-quality information.

## 2. Methods

- **Stations.** Nine stations from the lower Corrib estuary to the bathing waters: five estuarine and transitional stations (E1–E5) and B1–B4. Sampling in the 2021, 2022 and 2023 bathing seasons (1 June to 15 September).
- **Routine sampling.** 22 fortnightly visits were scheduled (7, 8 and 7 per season) and 21 completed; one visit in July 2022 was cancelled for weather. Each visit covered four of the nine stations on a fixed rotation, so that every station was sampled at least every six weeks: 84 samples.
- **Event sampling.** Within 48 h of rainfall above 8 mm in 24 h, samples were taken at B1–B4 and at the two stations nearest the outfalls (E4, E5): 11 events (3, 4 and 4 per season), 66 samples.
- **Exclusions.** 8 of the 150 samples (3 routine, 5 event) were excluded before analysis: 5 because culture started more than 24 h after collection, 3 because the field fluorometer failed its daily drift check. The analysed set is 142 paired samples (81 routine, 61 event), each with proxy and culture from the same bottle; salinity 4–34.
- **Reference method.** *E. coli* by ISO 9308-3 (miniaturised MPN) in the CICS microbiology laboratory, accredited to ISO/IEC 17025 for this method. Exceedance: a single sample above 500 MPN/100 mL.
- **Proxy.** TLF (peak T) read with a field fluorometer; GLUC activity from a 2-hour fluorogenic assay. A logistic classifier on TLF, GLUC and salinity was fitted with leave-one-season-out cross-validation; the cut-off maximised the Youden index. Sensitivity and specificity are computed from out-of-fold predictions. Uncertainty from 2,000 bootstrap resamples stratified by season.
- **Overflows and exceedance model.** Spill telemetry for four storm overflows (2019–2023, 187 spill events) supplied by the national water utility under a data-sharing agreement that prohibits redistribution. Hourly rainfall from Met Éireann gauges. A TELEMAC-2D model of inner Galway Bay (unstructured mesh, 40–250 m) gave outfall-to-beach travel times by particle tracking. A logistic model of exceedance at B1–B4 used observed 24-h rainfall to 09:00 on the sample day, observed spill duration in the preceding 24 h, tidal state at sampling and onshore wind. It was evaluated against regulatory and investigative samples from 2019–2023 (486 sample-days) by leave-one-year-out cross-validation: probabilities for each year come from a model fitted to the other four years. All predictors are observations available at sampling time, so the evaluation is a retrospective hindcast at zero lead time; no rainfall forecasts were used.
- **Survey.** Intercept survey of 612 beach users at B1–B4, July–August 2023, in English only.

## 3. Results

- **Exceedances.** 25 of 142 paired samples (17.6%) exceeded 500 MPN/100 mL: 21 of the 61 event samples and 4 of the 81 routine samples.
- **Proxy performance.** Sensitivity **0.76** (19 of 25; bootstrap 95% CI 0.55–0.90); specificity **0.88** (103 of 117; 95% CI 0.81–0.93). Log proxy score correlated with log *E. coli* (r = 0.71, n = 142). Four of the six false negatives occurred at salinity above 30, where the GLUC signal is diluted.
- **Travel time.** Median outfall-to-beach travel time 6.5 h (interquartile range 3.5–11.0 h).
- **Hindcast skill.** Out-of-fold area under the ROC curve **0.81** (95% CI 0.74–0.87, bootstrap over sample-days) over 486 sample-days, of which 38 were exceedances. With warnings issued at a predicted probability of 0.5, 20 of the 38 exceedances were warned (hit rate 0.53) and 8 of 28 warnings were false alarms (false alarm ratio 0.29).
- **Beach users.** 23% of respondents (141 of 612) relied only on on-site signs for water-quality information; 31% (190 of 612) swam outside the bathing season, when no regulatory sampling takes place; 57% (349 of 612) had entered the water on the day of interview.
- **Data.** The paired proxy–culture dataset (142 samples, with station metadata) was deposited in Zenodo under CC BY 4.0 in October 2024. Spill telemetry and survey microdata were not deposited: the first is covered by the data-sharing agreement, the second by a consent form that allows release of aggregated tables only.

## 4. Limitations

- All calibration samples come from one estuary. Classifier coefficients may depend on salinity regime, organic-matter background and effluent composition; transfer to other estuaries was not tested.
- With 25 exceedances, the sensitivity estimate is imprecise.
- The proxy targets faecal indicator bacteria; no pathogens (for example norovirus) were measured.
- Skill at forecast lead times was not tested. The AUC refers to a zero-lead hindcast with observed rainfall and observed spills; a day-ahead forecast would depend on rainfall forecasts and predicted spills.
- The 0.5 warning cut-off was chosen for illustration; no bathing-water manager was involved in setting it.
- The survey was a convenience sample in English and under-represents non-English speakers and early-morning and winter swimmers.

## 5. Outputs

Two peer-reviewed articles (2023, 2024), one MSc thesis, five conference presentations, the open paired dataset, and an internal prototype run daily at CICS during the 2024 bathing season that gave same-day exceedance probabilities from observed rainfall and telemetry (not issued to the public; its outputs were not systematically compared with samples).
