> Fictional document created for ProposalBench.

# Final technical summary: Residual Screening for Indoor Robot Localization

**Principal investigator:** Tessa Maren Halwick, Alderquay University  
**Award:** AQU-FIF-24-018, university Faculty Inquiry Fund; $78,000  
**Project period:** 1 January 2024–31 December 2025  
**Report accepted:** 20 February 2026  
**Archive and status check:** 30 September 2026

## Purpose and completed work

The project tested whether a residual-based observation screen improved indoor localization when recorded sensor streams contained specified corruptions. The research question concerned estimator behavior under a reproducible fault model. Completed outputs comprise a paired replay evaluation, a journal article, an institutional technical report, and a documented archive of recordings and analysis scripts.

The system combines a conventional localization filter with a screening rule that compares each incoming observation against its predicted residual distribution. Observations that cross the fixed screening threshold receive reduced weight. The screen uses information available to the estimator; the independent reference position is reserved for scoring. Both the baseline and screened estimator use the same motion model, initialization, and recorded input stream.

The university accepted the final report after an independent internal rerun of the primary analysis. The award is closed. Archive maintenance continued during 2026 through the faculty laboratory's existing university resources.

## Collection and evaluation design

Six differential-drive bench robots were used to record indoor trajectories during 2025. The archive contains 72 source trajectories: 12 development trajectories and 60 held-out evaluation trajectories. Each robot contributed two development trajectories and ten evaluation trajectories. Development trajectories were used to select the screening threshold and settle analysis code. They were excluded from the reported evaluation results.

The 60 evaluation trajectories were recorded in the same instrumented laboratory, with different path shapes and stopping patterns. Each robot operated alone. An independent optical reference system supplied positions for scoring. Reference positions were excluded from the estimator inputs. The reference-system calibration record was checked before collection; scoring nevertheless inherits the reference system's measurement uncertainty.

There were three mutually exclusive replay conditions, each assigned to 20 evaluation trajectories: contiguous observation dropout, persistent additive position bias, and delayed observations delivered with their original timestamps. A trajectory received one fixed condition. The faults were scripted in advance. Condition assignments, affected channels, and fault intervals were frozen before the evaluation runs.

For each evaluation trajectory, the baseline and screened estimator processed the same corrupted stream. The trajectory was the unit of analysis. Repeated software execution checked reproducibility without increasing the sample size. The six robots were repeated-use experimental assets of the same bench configuration; robot identity was retained in the analysis manifest.

## Outcome definition and results

For each estimator, horizontal position error was calculated at the scored timestamps against the optical reference. The median error within each trajectory was then calculated. The primary summary was the median of those 60 trajectory-level medians. Each trajectory therefore contributed one error summary, regardless of its number of scored timestamps.

The baseline primary summary was 0.50 m. The screened estimator's primary summary was 0.34 m. The difference between these two medians was 0.16 m, equivalent to a 32% reduction relative to the baseline summary.

The bootstrap 95% confidence interval for the reduction was 0.09 to 0.23 m. The analysis used 10,000 paired bootstrap resamples. Each resample retained the baseline and screened outputs together and sampled trajectories within robot, preserving each robot's contribution. The interval describes variation among trajectories conditional on the tested robots, room, fault assignments, and analysis procedure.

The pooled estimate was the prespecified primary result. The experiment was not powered to rank the three fault conditions or establish a benefit separately in every condition. Inspection of individual traces showed that screening sometimes discarded valid measurements after sharp turns. Those trace inspections were diagnostic observations, without a prespecified event-counting protocol or an estimated population frequency.

## Reproducibility and released materials

The *Halwick Indoor Replay Collection*, version 1.0, was deposited in Alderquay University's institutional repository on 28 February 2026. It contains the 72 source trajectories, reference-position streams, development/evaluation assignments, evaluation fault manifests, and documentation of coordinate frames and timestamps. Faulted streams are generated from the source recordings by the supplied replay scripts.

The repository also contains the estimator configurations, frozen screening threshold, analysis script, and bootstrap seed. Data are released under CC BY 4.0 and project code under the MIT License. The release contains laboratory robot and sensor records. Student assessment records are maintained separately under the teaching study's access controls.

A second group member, Ravi Nolan Keswick, independently reproduced the primary summaries from the frozen archive before report acceptance. The reproduction used the archived configurations and bootstrap seed. Its purpose was to check executable provenance and the reported summaries; it used the original recordings.

## Interpretation and limitations

The study was a single-robot, offline replay evaluation in one room. Results are conditional on the six robots used for collection. Because observations were replayed, the estimator's output could not change the robot's subsequent motion. Feedback between estimation failure and control action was absent from the experiment.

Fault selection was fixed before execution. The evaluation consequently provides limited evidence about an adversary that observes the screen and adapts its behavior. The observation and motion models were shared between the two estimators, so model misspecification common to both methods remains an additional limitation.

The December 2025 article and this report use the same evaluation dataset; the August 2026 calibration article is a subsequent analysis of that material.
