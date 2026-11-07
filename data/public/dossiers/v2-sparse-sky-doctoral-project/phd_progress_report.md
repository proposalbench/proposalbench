> Fictional document created for ProposalBench.

# Doctoral Progress Report: Mid-Term Review

**Candidate:** Radim Hlubocký
**Supervisor:** Prof. Dr. Milena Vranokvětová
**Date:** 30 September 2026
**Period Covered:** September 2023 – August 2026

## 1. Overview and Objectives

The primary objective of this doctoral project is to develop and validate a novel mathematical framework for recovering sparse astronomical sources (e.g., faint transient events or distant point sources) from imaging data dominated by high levels of instrumental and background noise. The project bridges theoretical mathematics (inverse problems) and astrophysics.

## 2. Completed Work: Theoretical Framework

During the first two years, the focus was on establishing the theoretical foundation for the recovery algorithm. The completed result establishes unique recovery in the noiseless case and conditional bounds on amplitude error and source localisation under bounded noise, for the stated sampling operator, known spatially invariant PSF, minimum separation (at least 2 FWHM) and amplitude assumptions. It does not claim exact identification of the true amplitudes under arbitrary nonzero noise. Under these assumptions, the inverse problem is formulated as an L1-minimisation task (basis pursuit denoising).

## 3. Completed Work: Simulation and Validation

To validate the theorem, we developed a synthetic imaging pipeline. We generated 500 simulated astronomical frames with varying noise profiles to test computational scaling.

**Simulation Setup:**
- For the single-frame primary quantitative validation run, the primary frame was a deliberately constructed stress test: 16 isolated sources were placed at least 6.4 pixels from every other source; four additional sources were arranged as two pairs with 3-pixel within-pair separation, away from the isolated sources. Each source had flux 150 photons in a single simulated background frame (4096 × 4096 pixels).
- The background was populated with uniform noise bounded by $\pm 5$ photons, and the sources were convolved with a known, static Gaussian PSF (FWHM = 3.2 pixels).
- Detection was defined as a recovered support within 1 pixel of the true centroid.

**Results:**
- The recovery algorithm successfully recovered 16 of the 20 injected sources. The 16/20 binomial interval (80%, 95% CI 56–94%) is descriptive for this non-random design, not a generalisable detection-efficiency estimate.
- The 4 missed sources were those deliberately crowded sources, placing them outside the guaranteed regime. This run therefore serves as an exploratory empirical detection performance test outside the strict theoretical guarantees.
- Zero false positives were recorded in this single 4096 × 4096 frame. Under a Poisson model, this yields a one-sided 95% upper bound of approximately 3.00 expected false positives per equivalent frame, or 0.179 per million pixels.

*Important Note:* The numerical checks and empirical detection performance do not constitute mathematical validation of the theorem itself, nor do they imply that the algorithm is currently ready for blind application to raw, uncalibrated telescope data.

## 4. Planned Work: Observational Tests

The next phase of the PhD (2026–2027) involves transitioning from simulated data to real observational data. We have planned new observations using the Moravian Stellar Observatory (MSO). 

The primary challenge will be uncertain calibration. Unlike the simulations, real observations feature spatially varying PSFs and non-Gaussian noise artifacts (e.g., cosmic rays, sensor defects). The planned tests will evaluate how gracefully the sparse-source theorem degrades when the assumptions of a known PSF and bounded noise are relaxed.

## 5. Extension to Archival Records (Stretch Goal)

While developing the mathematical framework, we identified a secondary application for our inverse-method expertise. Historical observing logs from the late 1990s and early 2000s often suffer from severe missingness and selection bias. 

Treating the missing log entries as a sparse recovery problem requires distinguishing between knowing which entries are missing (a realised mask) and knowing the outcome-dependent selection mechanism (e.g., observers only logging specific weather conditions or failing to record null detections). A realised mask does not identify the historical distribution when recording depends on unobserved weather. Furthermore, assuming the underlying weather conditions have a sparse representation in a chosen basis (e.g., temporal Fourier domain) is an untested additional assumption, not a consequence of the imaging theorem.

We plan to frame this extension around testing these sparsity and selection assumptions. We will use outcome-dependent masking experiments on complete modern datasets and develop sensitivity bounds or partial identification methods for cases where point reconstruction is unsupported. These assumptions remain prospective research questions. We approach this purely as a mathematical reconstruction problem, without claiming any expertise in archival historiography.
