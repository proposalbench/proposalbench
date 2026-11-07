> Fictional document created for ProposalBench.

# CALISORB: summary of results, months 1–40

**Calibrated sorption in porous optical coatings for trace-residue sensing in water**

- Funding: European Research Council, Consolidator Grant ERC-2022-COG, grant agreement No. 101088736, EUR 1,994,800
- Host institution: Technische Universität Ennstal (TU Ennstal), Steyr, Austria
- Principal investigator: Univ.-Prof. Dr. Ulrike Auernig-Sattler
- Duration: 1 May 2023 – 30 April 2028 (60 months); status: ongoing
- Period covered: 1 May 2023 to 31 August 2026 (month 40); expenditure to 31 August 2026: EUR 1,047,270 (52.5%)
- Compiled: 18 September 2026

## 1. Objectives

1. Produce porous photonic coatings (mesoporous SiO2/TiO2 Bragg stacks) with a reproducible pore structure that enrich polar organic micropollutants from water.
2. Model how enrichment, temperature, ionic strength and dissolved organic matter change the optical signal.
3. Build a calibration framework, traceable to certified reference standards, that corrects these matrix effects in natural waters.
4. Test on blinded samples, against LC-MS/MS, whether calibrated coatings return accurate concentrations.

Work packages: WP1 Coatings (M1–M36), WP2 Signal model (M1–M48), WP3 Calibration (M7–M54), WP4 Validation and instrumentation (M13–M60).

## 2. Methods

**Coatings (WP1).** Six-period Bragg stacks are dip-coated on 100 mm borosilicate wafers by evaporation-induced self-assembly, alternating mesoporous SiO2 (layer thickness 110 ± 4 nm, pore diameter 7.2 ± 0.5 nm, open porosity 43 ± 2%) and mesoporous TiO2 (75 ± 3 nm, pore diameter 4.8 ± 0.4 nm, open porosity 31 ± 2%); all values by ellipsometric porosimetry. In the sensing stack the SiO2 layers are grafted with β-cyclodextrin through the open pore network (0.19 mmol per g of coating, by thermogravimetry). Each 12 × 24 mm chip carries two stacks side by side: the grafted sensing stack and an otherwise identical, non-grafted reference stack. One wafer yields 20 chips; a production batch is three wafers.

**Sample enrichment.** 250 mL of filtered sample, adjusted to pH 3.0, is passed through a 150 mg polymeric reversed-phase SPE cartridge; diclofenac is eluted with 4 mL of methanol, evaporated to dryness under nitrogen at 40 °C and reconstituted in 250 µL of 10 mM phosphate buffer, pH 7.0 (nominal concentration factor 1,000). SPE is carried out off-line in the laboratory on a 12-port vacuum manifold.

**Readout.** 180 µL of the extract is recirculated through the flow cell of the reader in a closed loop (50 µL/min, 20 min). The channel exposes 2.0 × 8.0 mm of each stack; a fibre probe illuminates a 1.5 mm spot on each stack, and a fibre switch directs the two spots alternately to one spectrometer. Reflectance spectra (450–900 nm, 50 ms integration) are recorded with the flow-cell temperature logged; each readout point averages 800 spectra per stack. The observable is the shift of the first-order Bragg peak (near 580 nm in water).

**Calibration (WP3).** In the reference-stack differential calibration (RDC), the concentration is calculated from the differential peak shift (sensing minus reference stack), in which bulk refractive-index changes and lamp and temperature fluctuations common to both stacks cancel. The differential shift is corrected for residual temperature dependence with a chip-specific coefficient and anchored by two standard additions of certified diclofenac sodium reference material into the recirculating extract. The RDC method was disclosed to the TU Ennstal Technology Transfer Office on 12 November 2025 and is the subject of European patent application EP26162418.7, filed 17 March 2026 and pending. Journal publication of the method was held back until after the filing.

**Reference method.** LC-MS/MS (triple quadrupole, isotope-labelled internal standard diclofenac-d4, LOQ 0.01 µg/L), Department of Environmental Analytics, TU Ennstal.

**Blinded recovery study (WP4, Task 4.2).** Three matrices were sampled: laboratory tap water (Steyr municipal supply); river water from the Enns at Steyr (grab samples on 3 and 17 February 2026); and secondary effluent of a municipal wastewater treatment plant in Upper Austria (grab samples on the same dates; dissolved organic carbon 7.9 mg/L). All were filtered at 0.45 µm. Dr. Herbert Lindmayr's group spiked 500 mL aliquots with diclofenac at 0.2, 1.0 and 5.0 µg/L, four samples per matrix and level (3 × 3 × 4 = 36), coded them and kept the key; 250 mL of each was used for SPE and sensor measurement and the remainder for LC-MS/MS. J. Feichtlbauer and T. Weninger extracted and measured the 36 blinded spiked samples on prototype reader PR2-A in the laboratory at 22 ± 1 °C between 23 February and 13 March 2026 and submitted their results on 16 March 2026; the code was broken on 18 March 2026. Background diclofenac, measured with the same method on three unspiked aliquots per matrix, was subtracted (LC-MS/MS background: < 0.01 µg/L tap, 0.03 µg/L river, 0.38 µg/L effluent). Recovery = (measured − background) / nominal spike. Confidence intervals are percentile bootstrap intervals (10,000 resamples, stratified by matrix).

## 3. Results

### 3.1 Blinded recovery study (completed March 2026)

| Subset | n | Mean recovery | Bootstrap 95% CI |
|---|---|---|---|
| Tap water | 12 | 98% | 91–105% |
| River water (Enns) | 12 | 95% | 87–103% |
| Treated effluent | 12 | 89% | 79–99% |
| Spike 0.2 µg/L | 12 | 91% | 81–101% |
| Spike 1.0 µg/L | 12 | 95% | 89–101% |
| Spike 5.0 µg/L | 12 | 96% | 92–100% |
| **All samples** | **36** | **94%** | **89–99%** |

- Applied to the same 36 data sets, conventional external calibration in ultrapure water (no reference stack, no standard addition) gave a mean recovery of 78% (95% CI 70–86%), and 64% in effluent.
- Against LC-MS/MS on the same 36 samples, Passing–Bablok regression gave a slope of 0.94 (95% CI 0.89–0.99) and an intercept of 0.01 µg/L (95% CI −0.02 to 0.04 µg/L).
- 33 of 36 samples (92%) fell within 80–120% recovery. The three outside this range were effluent samples spiked at 0.2 µg/L (63%, 71% and 124%).

### 3.2 Analytical performance (ultrapure water and buffer; full procedure including SPE unless stated)

- Bulk sensitivity of the Bragg peak to the refractive index of the pore liquid (water–glycerol series, n_D 1.333–1.373): 162 nm per RIU for the sensing stack, 159 nm per RIU for the reference stack.
- Partition coefficient of diclofenac between the pore volume of the coating and buffer at 1.0 mg/L (methanol elution of exposed chips, LC-MS/MS; n = 8 chips): 2.3 × 10³ (RSD 14%) for the grafted stack, 41 (RSD 22%) for the reference stack. At equilibrium the coating takes up about 5% of the analyte in the 180 µL loop.
- SPE recovery at 1.0 µg/L (LC-MS/MS on extracts, n = 4 per matrix): 99% ultrapure water, 97% tap, 95% river, 90% effluent.
- Calibration slope, in units of sample concentration: diclofenac 0.055 nm per µg/L; carbamazepine 0.022 nm per µg/L. The diclofenac slope agrees within 30% with the value calculated from the partition coefficient, the bulk sensitivity and the concentration factor.
- Differential blank variability (1σ): 0.0009 nm for the averaged differential readout in buffer (n = 30), against 0.02 nm for a single spectrum; 0.0011 nm for full procedural blanks of ultrapure water (n = 20).
- Limit of detection (3σ of procedural blanks divided by the slope): diclofenac 0.06 µg/L; carbamazepine 0.15 µg/L. Linear range for diclofenac 0.2–5.0 µg/L (R² = 0.996); between 5 and 20 µg/L the response follows the adsorption model of section 3.3.
- Repeatability RSD 5.4% at 1.0 µg/L (n = 10, one day); intermediate precision RSD 8.9% (n = 25, five days, two operators).
- Temperature: uncorrected drift equivalent to 0.7% of signal per °C; after chip-specific correction, residual drift below 0.1% per °C over 15–30 °C.
- Dissolved organic matter: Suwannee River natural organic matter (IHSS), added before SPE at up to 10 mg C/L, suppressed the uncorrected signal by up to 31%; with RDC the bias stayed within ±6%.
- Coating reproducibility: 9 wafer batches; between-batch coefficient of variation of sensitivity 7.8%, within-wafer 3.1%.
- Storage: chips stored dry at room temperature for 90 days kept 96% of their initial sensitivity (n = 12 chips).
- Time per sample: SPE about 2.5 h per batch of 12 samples, including evaporation; reader time 27 min per extract, including on-chip enrichment and two standard additions.

### 3.3 Signal model (WP2)

A two-term adsorption model (Langmuir term for cyclodextrin sites plus a non-specific partition term) fitted 64 calibration series (0.2–20 µg/L) with a median relative residual of 3.8%. Competitive adsorption in mixtures of analytes is not yet modelled.

## 4. Limitations

- All 36 samples were spiked in the laboratory. The matrices came from one river site and one treatment plant on two dates. No measurements have been made on site or in continuous field operation.
- SPE is carried out off-line with a vacuum manifold and a nitrogen evaporator; the readers have no on-line enrichment. The full method has not been run outside the laboratory.
- The standard additions are made to the extract and do not correct SPE losses; the effluent recovery (89%) is close to the SPE recovery in effluent (90%).
- The blinded study covered one analyte (diclofenac). Carbamazepine and sulfamethoxazole were characterised in ultrapure water only; mixtures have not been tested.
- Both prototype readers were operated by the team that built them. There has been no measurement by external operators and no interlaboratory comparison.
- Fouling was studied for up to 8 h of continuous exposure to filtered effluent.
- In effluent at 0.2 µg/L the spike is about half the background, and recovery is imprecise.
- The reader and the chips are research prototypes: neither is CE-marked, and the method is neither accredited (no ISO/IEC 17025 scope) nor standardised.
- With n = 36 the overall 95% CI spans ±5 percentage points; per-matrix intervals are wider (±10 points in effluent).

## 5. Outputs and transfer activities to date

- Peer-reviewed articles from CALISORB: 3 (two in 2025, one in 2026), plus one review (2024).
- Dataset of the blinded study (raw spectra, sample codes, LC-MS/MS values) in Ennstal Research Data, record 4417, CC BY 4.0, released 2 September 2026.
- Two portable prototype readers (PR2-A, PR2-B) built February–April 2025.
- Invention disclosure 12 November 2025; service invention claimed by TU Ennstal 2 December 2025; European patent application EP26162418.7 filed 17 March 2026.
- Stakeholder workshop *Trace residues in water monitoring: practice and needs*, TU Ennstal, 20 May 2026: 14 participants from 9 organisations (3 municipal water utilities, 4 environmental testing laboratories, 1 regional water authority, 1 engineering consultancy). Of 12 returned feedback forms, 10 named turnaround time and 8 named cost per sample as the main limitations of current practice; 6 stated that results used for regulatory compliance must come from an accredited or standardised method; 7 would use a screening measurement to select samples for LC-MS/MS confirmation.
- Concept note for a university laboratory service submitted to the Rectorate on 2 June 2026.
- Additional funding for transfer activities: none. Patent costs are borne by the Technology Transfer Office budget.

## 6. Remaining work under the grant (months 41–60)

- WP2: competitive adsorption in multi-analyte mixtures.
- WP3: extension of RDC to carbamazepine and sulfamethoxazole.
- WP4: second-generation coatings with an antifouling top layer; long-term stability.
