> Fictional document created for ProposalBench.

# OUTFALERT: Horizon Europe RIA proposal, abridged copy

**Outfall-to-beach alerts: storm-contamination warnings for coastal bathing waters fed by urban outfalls**

| | |
|---|---|
| Submitted | 16 September 2025 |
| Call | Horizon Europe Cluster 6, 2025 work programme, Zero Pollution destination; single-stage RIA topic |
| Proposal number | 101219884 |
| Duration | 36 months |
| Requested EU contribution | EUR 3,000,000 |
| Coordinator | Cladach Institute for Coastal Science (CICS), Ireland |
| Beneficiaries | Université de Rochefort-Charente (URC), France; Weser-Institut für Stadt- und Wasserplanung (WISW) e.V., Germany |

Abridged by the coordinator in October 2025 from Part B as submitted. Sentences in quotation marks are unchanged; the rest is shortened.

## 1. Excellence

### 1.1 Objectives

- **O1.** Transfer a rapid faecal-contamination proxy, calibrated in Galway Bay, to a second European estuary and quantify its performance there.
- **O2.** Build a 24–48 h warning chain from rainfall nowcasts and overflow telemetry to bathing sites, with a skill target of AUC ≥ 0.80 at each site.
- **O3.** Define warning thresholds and integrate warnings into municipal stormwater and beach-management planning.
- **O4.** Release open data and replicable tools for other outfall-affected coastal sites.

### 1.2 Starting point: BAYPROXY results

BAYPROXY (EPA Research Programme, 2021–2024) produced 142 paired proxy–culture samples from the Corrib estuary and inner Galway Bay. The combined fluorescence–enzymatic proxy detected exceedance of 500 MPN/100 mL with sensitivity 0.76 (95% CI 0.55–0.90) and specificity 0.88. An exceedance model driven by rainfall and spill telemetry reached AUC 0.81 on 486 sample-days at four bathing waters. Median outfall-to-beach travel time was 6.5 h, which leaves time for same-day warnings. A survey of 612 beach users showed that 23% relied only on on-site signs.

### 1.3 Methodology

**Proxy transfer (WP2, lead URC).** “The classifier coefficients calibrated in BAYPROXY will be applied unchanged at three bathing sites at the mouth of the Charente estuary. URC will collect 30 verification samples in year 2 to confirm performance.” URC characterises the organic-matter background at all Charente stations by EEM fluorescence and PARAFAC and analyses 24 outfall effluent samples to compare source signatures with Galway.

**Warning chain (WP3, lead CICS).** Inputs: 1-km radar rainfall nowcasts licensed from Skerrymet Radar Analytics Ltd; overflow telemetry from the Irish national water utility; overflow logs from the wastewater operator at the Charente mouth. The BAYPROXY exceedance model is refitted with nowcast inputs and combined with TELEMAC-2D travel times for Galway and a new TELEMAC-2D set-up for the Charente mouth (month 12). Output: exceedance probabilities 24 h and 48 h ahead, produced daily at 06:00 for B1–B4 and the three Charente sites and run in shadow mode (not public) during two bathing seasons. “A warning is issued when the predicted probability of exceedance is 0.5 or higher.”

**Planning integration (WP4, lead WISW).** WISW maps the warning chain onto stormwater master plans and overflow-reduction programmes, using desk studies of two North Sea municipalities and the Galway case, and writes a planning guidance note for municipalities (month 33). Three user workshops: Galway, Rochefort, Bremen.

**Open science.** Preregistration of the Charente verification analysis; code on a public repository under Apache 2.0; FAIR data management plan in month 6.

## 2. Impact

### 2.1 Expected outcomes and impacts

“OUTFALERT warnings would avoid about 3,400 bather exposures per season at the four Galway Bay pilot beaches.” The figure combined hindcast exceedance days (2019–2023) with mean daily attendance. Charente benefits were not quantified. Target groups: local authorities, wastewater operators and bathers, including year-round swimmers. Replication at 20 European bathing sites by 2030 through the guidance note and open tools. Contribution to the Bathing Water Directive and the Zero Pollution Action Plan.

### 2.2 Dissemination, exploitation and communication

“All project data, including overflow telemetry, radar inputs and survey data, will be published under CC BY 4.0 on Zenodo by month 36.” The same section states: “Overflow telemetry is provided under data-sharing agreements with the operators, and radar nowcasts are licensed from a commercial provider.” Other measures: open-source warning software, a policy brief, three peer-reviewed articles and the three workshops.

## 3. Implementation

### 3.1 Work plan and effort (person-months)

| WP | Title | Lead | CICS | URC | WISW | Total |
|---|---|---|---|---|---|---|
| WP1 | Management | CICS | 14 | 2 | 2 | 18 |
| WP2 | Proxy transfer and source chemistry | URC | 12 | 78 | 0 | 90 |
| WP3 | Warning chain and hindcast | CICS | 108 | 10 | 4 | 122 |
| WP4 | Thresholds and planning integration | WISW | 12 | 6 | 70 | 88 |
| WP5 | Dissemination and open data | CICS | 22 | 6 | 8 | 36 |
| Total | | | 168 | 102 | 84 | 354 |

### 3.2 Requested EU contribution

| Beneficiary | EUR |
|---|---|
| CICS | 1,412,500 |
| URC | 868,750 |
| WISW | 718,750 |
| Total | 3,000,000 |

### 3.3 Risks

| Risk | Mitigation |
|---|---|
| Fewer exceedance events than expected | Event-triggered sampling after heavy rainfall |
| Delayed access to overflow telemetry | Use 2019–2023 historical records for model development |
| Low workshop participation | Invitations through WISW's municipal network |

### 3.4 Consortium

Three beneficiaries in three countries. No municipality or bathing-water authority is a beneficiary; users are engaged through workshops. No letters of support were attached.
