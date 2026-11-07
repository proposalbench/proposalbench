> Fictional document created for ProposalBench.

# CALIFAINT Research Group Composition

**Status as of:** 1 September 2026

## Principal Investigator
**Prof. Elias Mattis Norväng** oversees the entire CALIFAINT project, directing the theoretical development of the dynamic response models and managing the laboratory infrastructure.

## Postdoctoral Researchers
- **Dr. Linnea Signe Holmervik (2022–Present):** Lead algorithm designer. Dr. Holmervik holds a PhD in Applied Mathematics from Gothia Institute of Technology. She is responsible for the Markov Chain models used to predict pixel state probabilities. She authored the core mathematical routines in the `FaintCal` tool.
- **Dr. Arvid Torsten Lindekvist (2023–Present):** Lead software engineer. Dr. Lindekvist transitioned from industry (high-frequency trading systems) to academia. He is responsible for optimizing the C++ implementation of `FaintCal`, reducing the processing latency from 8.5 seconds to 1.2 seconds per frame on identical hardware.
- **Dr. Sofia Elin Bergelund (2024–Present):** Experimental physicist. Dr. Bergelund manages the cryogenic testbench and is responsible for acquiring the 4.2 terabytes of raw sensor data used to train the calibration models.
- **Dr. Jesper Alrik Kvarnevik (2025–Present):** Data scientist. Focuses on the statistical validation of the simulated exposures and the calculation of confidence intervals for signal recovery.

## PhD Students
- **Sara Elvira Jannervik (Enrolled 2023):** Focuses on the simulation pipeline. She designed the 200 simulated exposures used in the primary validation phase, ensuring the synthetic faint point sources accurately reflected the point spread functions of modern 8-meter class telescopes.
- **Marcus Ivar Norliden (Enrolled 2024):** Investigates the physical origins of random telegraph signal in sCMOS architectures. His work bridges the gap between semiconductor physics and the algorithmic corrections applied by `FaintCal`.
- **Elsa Linnea Strömvik (Enrolled 2025):** Explores cross-domain applications of the calibration framework. She is currently preparing the protocols for the planned domain evaluation in low-light environmental sensing.

## External Collaborators (Unfunded)
- **Dr. Tobias Lindvret, Swedish Institute for Environmental Physics:** Advising on the requirements for nocturnal atmospheric aerosol fluorescence monitoring. He will facilitate the planned domain evaluation of the detector response model in environmental sensing contexts.
