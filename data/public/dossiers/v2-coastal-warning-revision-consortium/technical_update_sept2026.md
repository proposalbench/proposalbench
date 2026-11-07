> Fictional document created for ProposalBench.

# OUTFALERT consortium: technical update since the evaluation summary report

Prepared by CICS (S. Mulqueeney) for the consortium partners. Version of 30 September 2026. Covers February to September 2026; all work funded from the partners' own resources.

## 1. Second-estuary calibration (ESR, Excellence, first shortcoming)

**Protocol.** OUTFALERT-CAL-2E v1.0 was approved by CICS and URC on 30 June 2026. It replaces the 2025 design (Corrib coefficients applied unchanged in the Charente, plus 30 verification samples in one season) with:

- independent calibration in each estuary (Corrib, Ireland; Charente, France), coefficients fitted separately and then cross-tested (fit in one estuary, test in the other);
- event-triggered sampling after rainfall above 8 mm in 24 h or a recorded overflow spill, spread over two bathing seasons per estuary;
- a target of 115 paired samples per estuary, at least 40 of them exceedances, giving an expected half-width of about 0.13 for the 95% CI of sensitivity. In BAYPROXY, 21 of 61 event samples (34%) exceeded; at that rate about 116 event samples yield 40 exceedances, so the target assumes that almost all samples are taken during events;
- exchange of 10% of samples as split samples between the CICS and URC culture laboratories;
- a transfer rule (protocol section 7): coefficients from one estuary are accepted for the other only if, in the receiving estuary, the lower 95% bound for sensitivity is at least 0.60 and specificity is at least 0.80; otherwise that estuary keeps site-specific coefficients and the transfer is reported as failed.

The protocol has no rule for an estuary that yields fewer than 40 exceedances. Funding for the full campaign has not been secured. Apart from the pilot below, no sampling under the protocol has started.

**Charente pilot.** URC collected 6 paired samples at three stations at the mouth of the Charente between 22 July and 28 August 2026 (salinity 12–31). By culture, 1 sample exceeded 500 MPN/100 mL. The classifier with BAYPROXY coefficients flagged that sample and gave one false positive; 5 of 6 samples were classified correctly. With one exceedance, these data give no usable estimate of sensitivity or specificity in the Charente. The only sensitivity estimate remains the Corrib value of 0.76 (bootstrap 95% CI 0.55–0.90), which is preliminary. Cross-estuary validation has not been done.

**Shannon Estuary Laboratory.** The CICS Shannon Estuary Laboratory ran the proxy assay on 20 split samples from Galway in April–May 2026; its exceedance classification agreed with the Galway laboratory in 18 of 20 samples. No samples from the Shannon estuary have been collected.

## 2. Decision-cost table (ESR, Excellence, second shortcoming)

WISW drafted a decision-cost table (draft v0.2, 31 July 2026; authors J. Kettler and H. Wolfsteller) to replace the fixed 0.5 warning probability with a cost-based rule. Costs are per beach-day and bathing water.

| Outcome | Bears the cost | Cost items | Range (EUR) |
|---|---|---|---|
| Warning, exceedance occurs | Local authority; bathers | Signage and staff (avoided illness not counted) | 1,900–4,600 |
| Warning, no exceedance (false alarm) | Local authority; local businesses | Signage and staff; lost trade; loss of trust (not priced) | 1,900–4,600 |
| No warning, exceedance (miss) | Bathers; health system; local authority | Gastrointestinal illness at assumed attack rates; lost workdays; complaint handling | 14,000–38,000 |
| No warning, no exceedance | none | none | 0 |

Under a cost–loss rule (warn when the predicted probability exceeds the ratio of action cost to avoidable loss), the table implies thresholds between 0.05 and 0.33, with a central value of 0.14 (EUR 3,000 / EUR 22,000), against the fixed 0.5 of the 2025 application. Applied to the out-of-fold BAYPROXY hindcast probabilities (486 sample-days, 38 exceedances), a threshold of 0.14 would have warned 32 of the 38 exceedances (hit rate 0.84) with 61 warnings in total, 29 of them false alarms (false alarm ratio 0.48).

The table is a draft. Cost ranges come from published illness-cost studies and CICS and URC estimates of signage and staff costs. No local authority, bathing-water manager or wastewater operator has reviewed it; no organisation has agreed to own or apply a decision rule; its usefulness to decision-makers has not been tested. Responsibility for bathing-water management and public information lies with local authorities in Ireland (Bathing Water Quality Regulations 2008) and with the commune in France; in Germany it is set by Land bathing-water ordinances.

## 3. Uncertainty in impact estimates (ESR, Impact, first shortcoming)

**Quantity.** The 2025 figure of 3,400 counted, for each 2019–2023 hindcast exceedance day at B1–B4, the mean daily attendance as exposures. It assumed that (i) every attendee enters the water, (ii) a warning issued at a predicted probability of 0.5 or higher, posted on site and online for the whole beach-day, reaches every attendee, (iii) every warned person stays out of the water, and (iv) the proxy classifies perfectly. It is a modelled count of potentially avoidable exposures, not an observed reduction.

**Code.** outfalert-uq v0.3 (Python, 15 June 2026; author Dr R. Tobin-Hayes) removes assumption (iv) and propagates, over 10,000 bootstrap replicates: (a) proxy misclassification, by resampling the 142 BAYPROXY paired samples and reclassifying proxy-flagged exceedance days; (b) outfall-to-beach travel time, from a 50-member TELEMAC-2D ensemble; (c) beach attendance, from counter data for 2022–2024 with a ±20% recording error.

**Results.** Under assumptions (i)–(iii) and the 0.5 threshold: median 2,580 potentially avoidable exposures per season at B1–B4 (95% interval 1,610–3,390), an upper bound. In a sensitivity run that replaces attendance by water entrants (57%, 349 of 612 survey respondents, resampled binomially) and assumes that half of warned bathers stay out of the water (an assumed value; no compliance data exist for Galway Bay): median 740 (95% interval 450–990).

**Not included.** Warning reach and behavioural response (fixed by assumption); error of forecasts at positive lead times (section 5); transfer to other estuaries, which cannot be included until second-estuary data exist; out-of-season swimming; illness given exposure. The intervals cover the Corrib only. A manuscript was submitted on 20 August 2026 and is under review. The code is in the CICS internal repository and is not public.

## 4. Data inventory (ESR, Impact, second shortcoming)

Data inventory v1.0 (25 September 2026), compiled by R. Tobin-Hayes with partner input, was updated to v1.1 on 29 September 2026 to add the 2026 observations (U1, U2). It lists 14 data assets: restricted raw (5), unrestricted raw not yet deposited (2), shareable derived (5) and already open (2).

| ID | Asset | Holder | Class | Licence or condition |
|---|---|---|---|---|
| R1 | Overflow spill telemetry, 4 Galway outfalls | National water utility | Restricted raw | Data-sharing agreement to 31 December 2027; no redistribution of raw or event-level records |
| R2 | 1-km radar rainfall nowcasts | Skerrymet Radar Analytics Ltd | Restricted raw | Commercial licence, internal use only |
| R3 | Overflow logs, Charente | Local wastewater operator | Restricted raw | Convention with URC; no redistribution |
| R4 | BAYPROXY survey microdata (612 respondents) | CICS | Restricted raw | Consent covers aggregated release only |
| R5 | Beach-attendance counter data | Galway local authority | Restricted raw | Permission for research use only |
| U1 | Charente pilot paired proxy–culture records (6 samples, July–August 2026) | URC | Unrestricted raw, not deposited | No third-party restriction; release requires URC approval |
| U2 | Galway–Shannon split-sample assay results (20 samples, April–May 2026) | CICS | Unrestricted raw, not deposited | No third-party restriction |
| D1 | Daily hindcast exceedance probabilities per bathing water | CICS | Shareable derived | CC BY 4.0 |
| D2 | Classifier coefficients and bootstrap outputs | CICS, URC | Shareable derived | CC BY 4.0 |
| D3 | TELEMAC-2D mesh and travel-time fields | CICS | Shareable derived | CC BY 4.0 |
| D4 | Aggregated survey tables | CICS | Shareable derived | CC BY 4.0 |
| D5 | Monthly spill counts per outfall | CICS (from R1) | Shareable derived | After utility review, as the agreement allows |
| O1 | BAYPROXY paired proxy–culture dataset (142 samples) | CICS | Open | Zenodo, CC BY 4.0, October 2024 |
| O2 | Rain-gauge data | Met Éireann | Open | CC BY 4.0 |

CICS has no dedicated data steward.

## 5. Forecast lead time

The BAYPROXY AUC of 0.81 is a retrospective hindcast (leave-one-year-out, observed rainfall to 09:00 and observed spill duration, zero lead time). The 2025 design sought warnings 24 h and 48 h ahead from 1-km radar nowcasts and overflow telemetry. The Skerrymet nowcast product extends to 3 h, and telemetry reports spills only once they occur. Outputs 24–48 h ahead would need rainfall from numerical weather prediction and a model predicting spill occurrence and duration from forecast rainfall. Neither has been obtained, built or tested, and no skill estimate at any positive lead time exists.

## 6. Status by ESR shortcoming

| ESR shortcoming | Changed since February 2026 (date) | Open at 30 September 2026 |
|---|---|---|
| Excellence 1: calibration in one estuary | Protocol OUTFALERT-CAL-2E v1.0 (30 June 2026); 6 Charente pilot samples (22 July–28 August 2026) | Second-estuary calibration and cross-estuary validation not done; campaign unfunded; sensitivity known for the Corrib only; no pathogen data |
| Excellence 2: no user decision rule | Draft decision-cost table v0.2 (31 July 2026) with implied thresholds 0.05–0.33 | Not reviewed by any decision-maker; no owner of a rule; usefulness not tested |
| Excellence 3: open science in general terms | Data inventory v1.1 (29 September 2026); transfer rule prespecified in the approved protocol (30 June 2026) | Protocol not registered publicly; no data management plan drafted; outfalert-uq not public; no dedicated data steward |
| Impact 1: no uncertainty in impact | outfalert-uq v0.3 (15 June 2026); conditional estimates with intervals | Corrib only; warning reach and behavioural response assumed, not measured; transfer uncertainty excluded |
| Impact 2: open data versus licences | Inventory separates restricted raw from shareable derived and open assets | Licence terms unchanged; R1 agreement ends 31 December 2027; D5 release needs utility review |
| Impact 3: replication target, no end-user commitment | WISW exploratory calls with two Lower Saxony drainage departments (12 May and 9 June 2026) | No letter or commitment from any end user; Galway local authority has not reviewed the cost table; no replication sites identified |
| Implementation 1: no contingency for too few Charente events | Protocol adds spill-triggered sampling and two bathing seasons per estuary | Charente exceedance rate unknown (1 of 6 in pilot); no rule for fewer than 40 exceedances |
| Implementation 2: coordinator experience | Consortium memorandum of understanding signed 18 September 2026 | Dr Mulqueeney has not coordinated a multi-beneficiary EU project; CICS has not coordinated a Horizon 2020 or Horizon Europe project |
