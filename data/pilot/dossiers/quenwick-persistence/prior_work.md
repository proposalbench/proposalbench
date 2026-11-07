> Fictional pilot project and numerical results created for ProposalBench; these are not real experimental evidence.

# RESET-LAG: measurement of heterogeneous antibiotic survival in broth

The internal seed project ran from January 2024 through December 2025 under PI Veylora Quenwick.
Its purpose was to check whether microscopy and a simple analysis pipeline could describe
variation in bacterial recovery after antibiotic exposure. It did not study a host-cell model.
The associated publication is Quenwick, Norquill, and Malvory (2025).

## Pilot design and results

The study used two banked, methicillin-susceptible *Staphylococcus aureus* isolates, PB-SA01 and
PB-SA02, obtained from the institute's teaching and methods collection. They have no linked
patient records and do not constitute a representative clinical panel.

- There were 12 independent broth cultures: six per isolate, prepared over three experimental
  days. Duplicate plating measurements were technical replicates, not additional cultures.
- After the fixed antibiotic-exposure assay, the median culturable surviving fraction was
  0.08% for PB-SA01 (culture range 0.03–0.19%) and 0.21% for PB-SA02 (0.06–0.45%). Fractions
  used each culture's own pre-exposure viable count as the denominator. No comparative
  hypothesis test was prespecified; these are descriptive pilot summaries.
- Eight survivor-derived colonies, four from each isolate, had the same measured minimum
  inhibitory concentration as their corresponding parent after antibiotic-free regrowth,
  within the assay's twofold dilution resolution. This supports a reversible component in
  those sampled survivors; it cannot exclude resistant subpopulations or establish that
  every survivor was a persister.
- In four additional, independently prepared broth cultures, the frozen segmentation pipeline
  was evaluated against 2,400 manually annotated bacterial objects. Object-detection precision
  was 0.91 and recall was 0.87. Images from these cultures were held out from development.
  The annotator knew the imaging condition, and no inter-annotator agreement was measured.
  Objects from one culture are correlated; 2,400 is not the biological sample size.
- An audit flagged 18% of post-exposure image fields for manual review because of clumps or
  focus problems. Reported detection performance applies to the retained fields. Imaging
  performance in host cells has not been measured.

## What the pilot supports

The group can produce auditable broth measurements and maintain a versioned imaging pipeline.
The results suggest a useful measurement problem: survival is heterogeneous and counts are
sensitive to object definition. They do not establish a new persistence mechanism or a
clinically meaningful difference between isolates.

## Limitations and available material

No macrophages, primary donor cells, animal infections, or patient samples were studied.
The two isolates and small culture count limit generalization. Time-kill shape, prolonged
regrowth distributions, and antibiotic carryover were not characterized sufficiently to
classify all survivors. The pilot does not distinguish persistence from population-wide
tolerance, nor does it address intracellular drug access. A proposed host-cell project must
resolve extracellular contamination and host-cell injury as alternative explanations.

The surviving-fraction table, image annotations, exclusion log, and analysis scripts are stored
on the institutional server. There are 480 annotated image fields in the held-out collection;
the 2,400 objects above are distributed among these fields. Public release is planned after
documentation review and has not occurred. These limited observations may motivate an R21,
but they are not a requirement for that mechanism and must not be described as extensive
preliminary validation.
