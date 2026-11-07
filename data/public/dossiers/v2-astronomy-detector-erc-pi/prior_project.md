> Fictional document created for ProposalBench.

# Interim Scientific Report: CALIFAINT (Month 54)

**Project Title:** Advanced Calibration Frameworks for Next-Generation Faint-Source Detectors (CALIFAINT)
**Grant Agreement:** ERC-2021-ADG 101055999
**Principal Investigator:** Prof. Elias Mattis Norväng
**Host Institution:** Västerled University, Sweden
**Reporting Period:** 1 April 2022 – 30 September 2026

## 1. Project Objectives
The CALIFAINT project aims to push the boundaries of faint-source astronomical imaging by developing novel, software-based calibration frameworks that mitigate complex, non-linear noise sources in next-generation scientific CMOS (sCMOS) and CCD detectors. The specific objectives are:
1. To characterize non-stationary noise components (e.g., random telegraph signal, dark current drift) at the sub-electron level.
2. To develop algorithmic calibration models that dynamically adjust to sensor state without requiring extensive daily flat-fielding.
3. To implement these models in an open-architecture workflow tool capable of processing high-cadence astronomical data.

## 2. Work Performed and Main Achievements

### WP1: Sub-Electron Noise Characterization
During the first two years, we established a cryogenic testbench at the Västerled Detector Physics Laboratory. We characterized three distinct sCMOS architectures (testing 4 devices per architecture, each with 4 million pixels) at temperatures ranging from 100 K to 200 K. Using a diagnostic threshold of a 3-sigma deviation from the mean dark current over a 10-hour period, we successfully isolated the random telegraph signal (RTS) components. We demonstrated that 14% (standard deviation of 1.2 percentage points across the 12 devices, representing approximately 560,000 pixels per device) exhibit non-Gaussian noise tails that traditional calibration pipelines fail to correct. We generated a comprehensive defect map library comprising 4.2 terabytes of raw sensor data.

### WP2: Algorithmic Calibration Development
Building on the defect maps from WP1, we developed a dynamic response model. Unlike static flat-field and dark-frame subtraction, our model uses a localized Markov Chain approach to predict the probability of a pixel being in a high-noise state during a specific exposure. 

In our primary validation phase (completed August 2026), we ran the calibration algorithm across 200 simulated exposures (each 4 megapixels). These simulations injected 10,000 artificial point sources with a Poisson mean of 15 detected electrons per source into empirical detector-noise backgrounds. No astronomical-magnitude or full telescope-sensitivity equivalence is claimed for this detector-only validation. Source photon arrivals were Poisson sampled. The point-spread function was modeled as a Gaussian with a full width at half maximum of 0.8 arcseconds. A detection was defined as a peak exceeding the local background by 5 times the background standard deviation (a 5-sigma background detection significance, distinct from the source-shot-noise upper bound which is approximately 3.87 for 15 electrons), matched within 2 pixels of an injected coordinate. Sky background and a detector plate scale were not specified, so the reported recovery must not be extrapolated to real-sky completeness. We held out 50 physical acquisitions and 50 simulated exposures from model fitting and threshold selection to serve as the test set.

**Key Result:** Using the held-out calibration set, the pipeline reduced the total number of false detections across the 50 test exposures from 40 to 26, while maintaining a fixed injected-signal recovery rate of 98% (recovering 1,960 of 2,000 injected sources in the test set). The paired bootstrap 95% confidence interval (resampling the 50 test exposures) for the absolute reduction in false detections is 5 to 23. 

*Limitation Note:* We emphasize that this represents simulation performance; field efficacy on physical telescope data has not yet been established. The current metrics reflect algorithmic potential under controlled, simulated conditions.

### WP3: Software Implementation
The algorithms developed in WP2 have been integrated into a unified workflow tool, designated `FaintCal`. The tool is written in C++ with a Python wrapper for pipeline integration. `FaintCal` currently processes a 4-megapixel simulated frame (including file I/O) in 1.2 seconds (standard deviation of 0.1 seconds across 100 timing runs) on a single 16-core AMD Ryzen 9 processor using 8 threads. This is a direct improvement from the 8.5 seconds baseline runtime measured on the identical hardware and workload prior to optimization. This 1.2-second latency meets the throughput requirements for transient surveys acquiring one 4-megapixel frame every 2 seconds.

## 3. Next Steps (Months 55–60)
The final six months of the project will focus on finalizing the documentation for the `FaintCal` workflow tool and preparing the theoretical findings for publication. We will also conduct preliminary integration tests with archival data from the Nordic Optical Telescope to assess how the dynamic response model handles real-world atmospheric variations, though full field validation falls outside the scope of the current ERC grant.
