> Fictional document created for ProposalBench.

# Final report: PB-BUURTGETIJ-26 (2024–2026)

**Neighbourhood flood exposure and adaptation choices in a tidal delta city**

Funded by the ZUT Delta Futures Fund, grant DFF-2023-06, EUR 214,000, 1 January 2024 to 30 June 2026. In-kind contributions: WEIH 8 person-months, FBMI 6 person-months.  
Principal investigator: Prof. dr. ir. Geertje Hoogvliet-Ramaker (ZUT).  
Spatial analysis: Mirthe Zwanenburg-Teeuw, doctoral candidate (ZUT), supervised by the PI and Dr. ir. Koen Stamhuis-Weel.  
Partners: Weser-Ems Institut für Hydrologie e.V. (river boundary ensemble); Fanø Bay Marine Institute (logger checks, floodwater sampling pilot).  
Report submitted 28 July 2026. Revised 15 September 2026: section 5 brought up to date at the request of the Delta Futures Fund after its closing review.

## 1. Objectives

1. Estimate flood depth per urban block under combined rainfall and tidal river conditions, with validated uncertainty.
2. Identify which households are exposed by linking modelled depth to household characteristics.
3. Compare three adaptation options for their effect on the number and distribution of exposed and inundated households.
4. Test a two-round co-design format with adult residents.

## 2. Study area and data

- **Area.** Three post-war neighbourhoods (N1–N3) on the Island of Dordrecht, bounded by tidal reaches of the Rhine–Meuse delta. They contain 240 urban blocks and 9,860 residential addresses, of which 5,170 have a ground-floor dwelling; 51% of addresses are rented.
- **Terrain and sewers.** AHN4 elevation (0.5 m), resampled to a 2 m grid. Sewer network from the municipal sewer database (2023 version), which records house connections but not non-return valves.
- **Address attributes.** Building year from the Basisregistratie Adressen en Gebouwen (BAG); tenure (owner-occupied, social rented, private rented) from the municipal housing register, 2024.
- **Entrance survey, April 2024.** Threshold height above street level measured at 212 ground-floor entrances, sampled across 6 strata of building type and construction period.
- **Household survey, May–July 2024.** 4,800 addresses were invited and 1,127 households responded (23.5%). Renters made up 38% of respondents. 214 respondents consented to be contacted for further research.
- **Temporary monitoring, 15 August 2024 to 30 April 2025.** 38 pressure loggers at street low points in 31 blocks, plus 2 tipping-bucket rain gauges. Two loggers were lost; 36 produced complete records.

## 3. Methods

- **Model.** Coupled 1D sewer (SWMM 5.2) and 2D overland flow model. Outfalls with non-return flaps close when the river level exceeds the outfall level. River levels come from the WEIH 1D tidal network model.
- **Forcing.** The design case combines 100-year rainfall (KNMI'23 high scenario for 2050) with a river level 0.5 m above mean high water. An ensemble of 50 further runs combines rainfall (KNMI'23 scenarios for 2050), river discharge, surge and tidal phase.
- **Validation.** Seven rainfall events between September 2024 and March 2025 produced 186 logger-event peak depths (ponding above 0.02 m). Uncertainty in the error statistics was estimated with a spatial block bootstrap that resampled the 31 logger blocks (2,000 replicates).
- **Endpoints.**
  - *Block exposure.* A block counts as exposed when modelled depth at any street frontage exceeds 0.30 m, the median threshold height of the 212 surveyed entrances. It is reported as exposed blocks and as addresses in exposed blocks, and describes street conditions only.
  - *Property inundation.* A ground-floor address counts as inundated when modelled depth at its frontage exceeds its entrance threshold, or when modelled sewer head at its house connection rises above the threshold level (backflow). Surveyed entrances keep their measured threshold; other addresses take the median of their stratum. No non-return valves were assumed at baseline.
- **Distribution.** Logistic regression of living in an exposed block on income tercile, tenure, age of household head and building year. Survey weights were applied for tenure and building year; standard errors were clustered by block. For each option, the share of avoided property inundation falling to the lowest income tercile was computed among respondents in ground-floor dwellings, with the same weights.
- **Options.** Each option was run on the design case and on all 50 ensemble members. Every option run was paired with a baseline run on identical forcing.
  - (A) Distributed green-blue retrofit: bioswales and permeable paving that disconnect 6.8 ha of roof and paved area.
  - (B) Two water squares with 2,900 m³ storage in total.
  - (C) Property-level protection: at adopting addresses, thresholds raised by 0.20 m and a non-return valve fitted on the house connection. Street depths are unchanged. Uptake was set at 40% among owner-occupiers and 15% among rented dwellings, taken from stated survey intentions, and assigned to individual addresses by random draws within tenure groups (500 draws). Results are means over draws.
- **Uncertainty in option effects.** Point estimates refer to the design case. Ranges are the 5th–95th percentiles of the paired percentage reductions across the 50 ensemble members. They show how effects vary with forcing; they are not confidence intervals and do not include model error, threshold uncertainty or, for option C, uptake. Variation across uptake draws is reported separately.
- **Co-design.** Two workshop rounds (October 2024, March 2025), each held at two locations. Materials were 3D block models, option cards and modelled depth maps. Participants ranked the options at the end of each round.
- **Floodwater pilot.** FBMI sampled ponded street water at 12 locations during three events (October 2024 to February 2025) and analysed *E. coli* (ISO 9308-3, most probable number) and intestinal enterococci (ISO 7899-2, membrane filtration).

## 4. Results

**Model performance.** Against the 186 observed peaks, flood-depth RMSE was 0.19 m (spatial bootstrap 95% CI 0.15 to 0.25 m) and mean bias +0.04 m. Error was larger where entrances lie below street level (41 peaks, RMSE 0.27 m). The largest observed event had a rainfall return period of about 8 years.

**Exposure in the design case.**

- Block exposure: 61 of 240 blocks (25.4%), containing 2,214 of 9,860 addresses (22.5%). Across the ensemble, the number of exposed blocks ranged from 44 to 79 (5th–95th percentile). With the same rainfall at low water, 47 blocks were exposed.
- Property inundation: 1,034 of 5,170 ground-floor addresses (20.0%), 712 through the entrance and 322 through sewer backflow alone. Of these 1,034 addresses, 486 were owner-occupied and 548 rented.

**Who is exposed.** Households in the lowest income tercile were more likely to live in an exposed block (odds ratio 1.7, 95% CI 1.2 to 2.4). The same held for social-housing renters (odds ratio 1.4, 95% CI 1.0 to 2.0).

**Options.** Design case; ranges are ensemble 5th–95th percentiles of paired reductions.

| Option | Addresses in exposed blocks; reduction (range) | Inundated ground-floor addresses; reduction (range) | Share of avoided inundation in lowest income tercile (respondents) |
|---|---|---|---|
| Baseline | 2,214 | 1,034 | – |
| A Green-blue retrofit | 1,528; 31% (22–39%) | 690; 33% (25–41%) | 39% |
| B Water squares | 1,815; 18% (11–26%) | 858; 17% (10–25%) | 21% |
| C Property-level protection | 2,214; 0% | 798; 23% (16–30%) | 26% |

- Exposed blocks fell from 61 to 42 under option A and to 50 under option B. Option C does not change street depths, so block exposure is unchanged.
- The benefits of option B were concentrated in N2, where both squares lie.
- For option C, avoided inundation in the design case ranged from 214 to 259 addresses across the 500 uptake draws (2.5th–97.5th percentile). With full uptake it would avoid 879 of 1,034 inundated addresses (85.0%). With uptake of 40% in both tenures, the lowest-tercile share of avoided inundation was 35%.
- Among respondents, 121 of the 586 households in ground-floor dwellings were inundated at baseline, and 44% of them (weighted) were in the lowest income tercile. The shares in the table rest on 40 (A), 21 (B) and 28 (C, mean over draws) avoided cases.

**Co-design.**

- 36 adults took part: 20 women and 16 men, aged 21–79; 11 (31%) were social-housing renters.
- 33 took part in round 1, 32 in round 2 and 29 in both. Six participants used an interpreter (Turkish or Arabic).
- In round 2, 23 of 32 participants (72%) ranked option A first. 19 named the maintenance of bioswales as their main concern.
- Residents marked 14 low points that the model did not represent. After field checks, 7 were added to the terrain model.

**Floodwater pilot.** In 31 samples, median *E. coli* was 1,900 MPN/100 mL (IQR 640–5,300), and 22 of 31 samples (71%) exceeded 1,000 MPN/100 mL. Median intestinal enterococci was 420 CFU/100 mL. The pilot was not designed to attribute sources and was not linked to any transport model.

## 5. Data management and ethics

- **Ethics approval.** The ZUT Human Research Ethics Committee granted approval HREC-2024-031 on 2 April 2024. Amendment 1 (second workshop round, interpreters) was approved on 21 January 2025. The approval is valid until 31 December 2027.
- **Participants.** The approved protocol covers residents aged 18 and over. It does not allow recruitment of minors until an amendment has been approved and a parent or guardian consent and assent process is in place. As of 15 September 2026 no such amendment has been submitted and no guardian process has been drafted.
- Household geolocations (address points linked to survey answers) fall under the PB-BUURTGETIJ-26 data access agreement of 14 March 2024: analysis is permitted only in the ZUT Secure Research Environment, row-level data may not be transferred to partner laptops, and partners may receive aggregates after disclosure checking (at least 10 households per cell).
- **Published data and code.**
  - Block-level dataset v1.1, March 2026 (Zenodo, CC BY 4.0): 240 blocks with modelled depths, ensemble percentiles and aggregated survey indicators; cells below 10 households are suppressed.
  - Logger time series (CC BY 4.0).
  - Model configuration and scripts (MIT licence).

## 6. Limitations

- The study covers one town and three neighbourhoods; transfer to other estuaries is untested.
- Validation rests on seven events, the largest with a rainfall return period of about 8 years. Performance for 100-year events is extrapolated.
- No coastal surge overtopping or dike breach was modelled. River levels were imposed as boundaries, not dynamically coupled.
- Thresholds outside the 212 surveyed entrances are stratum medians. Existing non-return valves are not recorded, so baseline backflow may be overstated.
- Option ranges reflect forcing only; option C also depends on the assumed uptake.
- Owner-occupiers are over-represented in the survey (renters 38% against 51% in the area). Weighting reduces but does not remove this bias. Income shares of avoided inundation rest on 121 inundated respondent households and are imprecise.
- Co-design involved 36 self-selected adults, not a representative sample.
- Water quality was covered only by the 31-sample pilot. No contaminant transport modelling and no chemical analyses were done.

## 7. Outputs

- Three peer-reviewed articles and one manuscript under review.
- Three chapters of the doctoral thesis of M. Zwanenburg-Teeuw.
- Four briefing sessions with municipal planners (2025–2026).
- Oral presentation at the Estuarine Cities Research Forum 2025, Vienna.

## 8. Expenditure

| Category | Budget (EUR) |
|---|---|
| Personnel | 132,000 |
| Temporary loggers and fieldwork | 41,500 |
| Workshops (venues, interpreters, participant vouchers) | 18,700 |
| Data and computing | 9,800 |
| Publication and dissemination | 12,000 |
| **Total** | **214,000** |

Actual expenditure was EUR 211,640 (98.9% of budget).
