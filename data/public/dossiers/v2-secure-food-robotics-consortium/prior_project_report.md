> Fictional document created for ProposalBench.

**Date:** 15 February 2026

# Final Report: RESIL-BOT (2022–2025)

**Resilient Anomaly Detection for Autonomous Guided Vehicles in Warehousing**

**Funding Agency:** German Research Foundation (DFG)
**Grant Number:** RB-2022-8849-TUF
**Total Budget:** EUR 1,200,000
**Duration:** 1 January 2022 to 31 December 2025
**Principal Investigator:** Prof. Dr. Lukas Varnkötter, Technical University of Falkenburg (TUF)

## 1. Executive Summary

The RESIL-BOT project aimed to enhance the operational resilience of Autonomous Guided Vehicles (AGVs) in warehouse environments by developing advanced anomaly detection algorithms. The primary focus was on identifying sensor faults and adversarial data injections to provide a foundation for bounded operational safety. Over the four-year period, the project successfully developed a novel AI-driven decision-support framework capable of isolating faulty sensor streams in replay evaluations.

## 2. Objectives

1.  Characterise the statistical properties of common sensor faults (e.g., drift, noise, complete failure) in LiDAR and ultrasonic sensors used on warehouse AGVs.
2.  Develop a lightweight, real-time anomaly detection engine capable of running on edge hardware.
3.  Evaluate the detection accuracy and false-positive rate of the engine using historical and synthetic sensor traces.
4.  Design fallback navigation policies that allow AGVs to safely halt or return to base when critical sensor thresholds are breached.

## 3. Methodology

The project utilised a data-driven approach, collecting over 4,500 hours of baseline sensor data from AGVs operating in controlled environments. We injected synthetic faults into these data streams to create a comprehensive testing corpus. The anomaly detection engine was built using a semi-supervised learning architecture, trained exclusively on 3,300 hours of healthy data, with the remaining 1,200 hours used for validation. The 80 test traces used for final evaluation were strictly separated from training and validation sets.

To evaluate the system, we constructed a replay testing framework. This allowed us to feed the recorded and modified sensor traces into the detection engine in real-time, mimicking the data flow of a live AGV without the physical risks associated with testing faulty navigation in a populated warehouse.

## 4. Key Results and Performance Metrics

*   **Fault Detection Accuracy:** In 2025, we completed replay tests on 80 independent sensor traces (each containing exactly one injected fault). The system detected 68 of the 80 injected faults (85 percent, Wilson 95% CI approximately 76 to 91 percent). 
*   **False Positive Rate:** The engine was evaluated over 1,200 hours of healthy validation data, partitioned into 72,000 one-minute decision windows. It flagged 1,728 of these windows as anomalous, resulting in a false positive rate of 2.4%. The operational disruption this would cause in a live setting remains to be measured.
*   **Latency:** The edge-optimised detection algorithm achieved an average inference time of 14 milliseconds (SD = 2.1 ms, n = 10,000 inferences) on a standard ARM Cortex-A76 edge node, well within the 50-millisecond requirement for real-time AGV control loops.
*   **Limitation Note:** While the detection metrics are highly promising, it is critical to acknowledge the boundaries of the current validation. These were simulations, not live warehouse validations. The replay tests demonstrated the detector's performance, but closed-loop navigation safety and operational disruption remain to be validated in live settings.

## 5. Dissemination and Open Data

The project resulted in four peer-reviewed publications in top-tier security and robotics venues. Furthermore, we have released the "RESIL-BOT Warehouse Sensor Corpus," an open dataset containing 2.5 TB of annotated LiDAR, ultrasonic, and IMU data, published under a CC BY 4.0 license to support further research in the community.
