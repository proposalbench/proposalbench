> Fictional document created for ProposalBench.

# Final scientific report: Mésurafroid-25

**Measurement agreement under interrupted refrigeration in prepared-food matrices**

**Project period:** 1 January 2023–31 December 2025. **Final report accepted:** 27 February 2026. **Archive status checked:** 30 September 2026.

**Principal investigator:** Mireille Vauzernac, IIMAV. Veterinary reference work was performed with Rzewska Veterinary University; telemetry assessment was performed with Kelderspoor Sensorbeveiliging BV.

## Funding and expenditure

The French Agence nationale de la recherche supported the project under award reference ANR-PB-MF25-017. The award and accepted eligible expenditure were both EUR 840,000. Expenditure comprised EUR 502,000 for personnel, EUR 118,000 for equipment and depreciation, EUR 104,000 for consumables, and EUR 116,000 for external analytical and data services.

## Experimental question and material

The study examined whether chemical and temperature measurements could identify a predefined surrogate-growth endpoint after interrupted refrigeration. It did not estimate the prevalence of naturally occurring pathogens in retail food.

Technicians prepared 160 food lots: 80 cooked-rice lots and 80 cooked-poultry lots. A lot was a separately prepared food unit divided into matched analytical portions; repeated instrument readings and duplicate plates were not treated as independent lots. All material was designated for research and excluded from consumption.

The documented nonpathogenic strain Lactococcus lactis IIMAV LL-07 served as the sole biological surrogate. Preparation, inoculation, headspace sampling and microbial enumeration occurred in Lyon room LY-M2. Sealed sample vessels passed through the contained process line in adjoining room LY-P1. Refrigeration profiles included uninterrupted storage at 4 °C and controlled excursions to 10 °C. Samples were opened only in LY-M2.

Headspace measurements were made on the Lyon gas chromatograph. Nantes supplied calibration procedures and reviewed chromatograms electronically. Inoculated food remained at Lyon through analysis and disposal; the study therefore required no inter-site transfer of inoculated food. The protocol history is recorded in the resources register.

The 160 lots were processed in 24 storage batches. Sixteen batches contained seven lots and eight batches contained six lots. Batch membership recorded shared preparation and refrigeration conditions. Food matrix and temperature profile were recorded before outcome measurement.

## Measurements and analysis population

The reference endpoint was a final surrogate count above 6.0 log10 CFU/g. This was an experimental growth threshold, not a statutory food-safety limit. Enumeration used duplicate plates with documented dilution factors. Temperature histories and headspace chemical measurements supplied the model inputs. Matrix identity was included as a prespecified covariate.

There were 144 complete microbial and sensor pairs, representing 90% of the 160 lots. Ten lots lacked a usable sensor history and six lacked an interpretable reference count. These groups did not overlap. The 16 incomplete lots occurred in 11 batches: seven batches lost one lot, three lost two lots and one lost three lots. The remaining 13 batches had complete records. Complete lots per batch ranged from 4 to 7. The complete analysis population contained 70 rice lots and 74 poultry lots.

The missing records were retained in the archive with reason codes. Neither reference outcomes nor sensor histories were imputed for the classification analysis. Connector failures were more frequent during excursion handling, and incomplete records were concentrated in excursion batches. The excluded observations may have been more difficult to classify, so the complete-case results may be optimistic.

## Held-out classification results

Validation used six outer folds, each holding out four entire storage batches. The folds contained 21, 23, 24, 24, 25 and 27 complete lots, respectively. All preprocessing, feature selection and classifier fitting occurred using the other batches. Every complete lot received one prediction from a model that had not seen that lot or its storage batch. Threshold selection occurred within the training data. The reported result pools these held-out predictions; it is not an evaluation of a single final model on a separate external population.

Of the 144 complete lots, 100 exceeded the reference endpoint and 44 did not. The classifier identified 81 of the 100 endpoint-positive lots and correctly classified 36 of the 44 endpoint-negative lots. Sensitivity was 0.81, with bootstrap 95% CI 0.72 to 0.88. Specificity was 0.82, rounded from 36/44. There were 19 false negatives and eight false positives.

The sensitivity interval used 10,000 bias-corrected bootstrap resamples of storage batches, preserving all lot records within each sampled batch. It describes uncertainty in the pooled held-out results under the study's batch structure. It does not include uncertainty from transfer to another food product, organism or commercial setting. The relatively high endpoint-positive proportion was created by the experimental exposure design and cannot be interpreted as commercial prevalence.

Two prespecified baselines used the same complete lots. A fixed time–temperature alarm identified 68 of the 100 positives and correctly classified 33 of the 44 negatives. A temperature-only logistic model identified 72 positives and correctly classified 34 negatives. These paired counts provide comparisons at the selected operating thresholds.

## Fault and security observations

An additional replay exercise used 48 recorded telemetry traces selected from the complete-lot archive. Twenty-four were retained unchanged and 24 were modified to repeat an earlier segment while retaining plausible temperatures. The initial integrity rule flagged 20 of the 24 modified traces and incorrectly flagged two of the 24 unchanged traces. These are laboratory screening counts from a deliberately balanced exercise, not field attack-detection rates.

The exercise exposed dependence on gateway timing and sequence information. It did not test an attacker controlling both the gateway credentials and its clock. There was no independent penetration test or adaptive adversarial search. The security findings were recorded separately from the food classifier's sensitivity.

## Interpretation and retained outputs

The work established a reproducible paired-measurement workflow and evidence of predictive association with surrogate growth under contained conditions. It did not measure avoided food loss, changes in commercial rejection rates, illness reduction or pathogen-specific hazard reduction. No food was sold or consumed, and no human dietary trial was conducted.

The archived dataset is titled 'Mésurafroid paired-lot release 1'. It contains lot identifiers, batch assignments, missingness reasons, reference counts, calibration records and telemetry. A research extract is shared among the partners under their data-use schedule. Supplier identifiers remain in IIMAV's restricted source register. The dataset has no public DOI and is not an unrestricted public release.

The principal limitations are the controlled food matrices, use of a single surrogate, incomplete observations, internal grouped validation and absence of commercial deployment. Technician decisions remained authoritative throughout: the interface supplied an alert and its supporting measurements, while the technician recorded acceptance, rejection or deferral.
