> Fictional document created for ProposalBench.

# Infrastructure, prototypes, intellectual property and permissions

Optical Analytical Chemistry group, TU Ennstal. Status as of 30 September 2026.

## 1. Laboratories and equipment

- Two laboratories (95 m² and 70 m²), Campus Steyr, building C; four fume hoods.
- Dip-coater with humidity control (10–80% RH), spin-coater, tube furnace (up to 1,100 °C), plasma cleaner, wafer dicing saw.
- Spectroscopic ellipsometer with ellipsometric porosimetry cell; FTIR and UV-Vis spectrometers; thermogravimetric analyser; benchtop reflectometer with temperature-controlled flow cell.
- Sample preparation: SPE vacuum manifold (12 ports) and nitrogen evaporator (24 positions).
- Shared access: TU Ennstal cleanroom (ISO class 7, 120 m²); LC-MS/MS triple quadrupole of the Department of Environmental Analytics at the internal rate of EUR 38 per injection.

## 2. Portable prototype readers

| Item | Entry |
|---|---|
| Units | 2 (PR2-A, PR2-B), built February–April 2025 by Dr. J. Feichtlbauer |
| Optics | white LED; fibre switch between sensing and reference spot (1.5 mm each); miniature grating spectrometer 400–950 nm, 1.5 nm resolution; peak-position precision 0.02 nm (1σ, single 50 ms spectrum), 0.0009 nm for the averaged differential readout (800 spectra per stack) |
| Fluidics | peristaltic micro-pump; closed-loop flow cell for 12 × 24 mm chips (loop volume 180 µL; exposed area 2.0 × 8.0 mm per stack); two standard-addition reservoirs |
| Sample preparation | off-line SPE in the laboratory; not integrated in the reader |
| Size and mass | 230 × 160 × 90 mm, 2.1 kg |
| Power | Li-ion battery, 6 h of operation |
| Parts cost | EUR 3,400 per unit |
| Software | acquisition and RDC calibration code (Python), version 0.9, TU Ennstal internal GitLab; not publicly released |
| Use to date | 412 measurements (PR2-A 287, PR2-B 125), all in TU Ennstal laboratories |
| Maturity | assessed by the group as TRL 4 (technology validated in laboratory) |
| Certification | none; not CE-marked |

Chip stock: 132 coated chips from batches 7–9. Production capacity: 20 chips per wafer, two wafers per week; material cost about EUR 11 per chip.

## 3. Intellectual property

| Field | Entry |
|---|---|
| Title | Method for calibrating a porous optical sensing coating by a co-located reference stack and in-sample standard addition |
| Application number | EP26162418.7 |
| Applicant and owner | Technische Universität Ennstal |
| Inventors | U. Auernig-Sattler, J. Feichtlbauer, T. Weninger |
| Basis of ownership | service invention claimed by TU Ennstal under § 106 UG 2002 on 2 December 2025; CALISORB results owned by TU Ennstal as beneficiary under the ERC grant agreement |
| Filing date | 17 March 2026 (first filing, no priority claimed) |
| Claims as filed | 14 (method claims 1–11, device claims 12–14) |
| Search | extended European search report with written opinion received 27 August 2026; 4 documents cited; the written opinion raises an inventive-step objection to claims 1–8 over D1 (Auernig-Sattler et al., 2019, Journal of Photonic Coatings) combined with D2 (a 2017 patent document on standard addition in optical flow cells); claims 9–14 not objected to |
| Status | pending; publication expected September 2027; request for examination not yet filed; no decision on grant |
| Costs to date | EUR 9,870, Technology Transfer Office budget |
| Licences and options | none |
| Other rights | acquisition and calibration software (copyright, TU Ennstal); blinded-study dataset released under CC BY 4.0 |

## 4. Laboratory protocols, ethics and permissions

| Item | Entry |
|---|---|
| Laboratory protocol | LP-OA-07, version 3, *Handling of spiked water samples and pharmaceutical reference standards*; approved by the TU Ennstal Occupational Safety and Environment Office on 12 January 2024; next review January 2027 |
| Scope of LP-OA-07 | in-vitro assays on filtered tap, surface and treated effluent water spiked with certified reference standards (diclofenac sodium, carbamazepine, sulfamethoxazole); stock solutions of at most 100 mg/L in methanol prepared in a fume hood; SPE and solvent evaporation in a fume hood; effluent handled under BSL-1 practice; spiked and solvent waste to hazardous-waste collection |
| ERC ethics self-assessment (2022) | no ethics issues identified: no human participants, no personal data, no animals, no activities in third countries |
| Authorisation under the Austrian Animal Experiments Act (TVG 2012) | none held by the group |
| Personal data | none in experimental work; workshop participants' contact details held by the Technology Transfer Office with their consent (GDPR) |

## 5. Laboratory service concept

| Field | Entry |
|---|---|
| Working title | TU Ennstal Trace Residue Calibration Service |
| Document | concept note submitted to the Rectorate on 2 June 2026 by U. Auernig-Sattler and J. Feichtlbauer |
| Content | screening measurements of diclofenac in water samples sent in by utilities and laboratories, using PR2-type readers and RDC calibration |
| Rectorate response | 8 July 2026: cost model and market assessment requested before a decision on establishing the unit |
| Unit established | no |
| Clients | none |
| Signed service contracts | none |
| Price list | not set |
| ISO/IEC 17025 accreditation | not applied for |
| Staff assigned | none |

## 6. Host institution confirmation

Letter of 21 September 2026 from Univ.-Prof. Dr. Gernot Pirchmoser, Vice-Rector for Research, TU Ennstal, issued at the request of Prof. Auernig-Sattler. The letter confirms that:

1. Univ.-Prof. Dr. Ulrike Auernig-Sattler has been employed full-time on a permanent appointment as Universitätsprofessorin (§ 98 UG 2002) since 1 October 2021; Dr. Jakob Feichtlbauer and Ing. Sabine Rührlinger hold permanent positions.
2. TU Ennstal owns the results of CALISORB, including the invention filed as EP26162418.7, the PR2 readers and the acquisition and calibration software, and authorises the PI's group to use them for further development, validation and demonstration.
3. TU Ennstal will maintain the PI's employment, the laboratories listed in section 1 and its ownership of these rights for at least 18 months from the start of a follow-on validation project of the PI hosted at TU Ennstal.
