> Fictional document created for ProposalBench.

# Laboratory Infrastructure and Software Assets

**Date:** 28 August 2026
**Prepared by:** Dr. Arvid Torsten Lindekvist & Prof. Elias Mattis Norväng

## 1. Hardware Infrastructure
The Västerled Detector Physics Laboratory is equipped with a custom-built cryogenic vacuum chamber capable of maintaining stable temperatures down to 70 K (with a thermal stability of ±0.01 K standard deviation over 24 hours). The optical bench includes a stabilized integrating sphere, a monochromator (300–1100 nm), and a series of calibrated neutral density filters capable of attenuating light to single-photon levels. 

We currently operate three evaluation boards for next-generation sCMOS sensors, provided under non-disclosure agreements by the manufacturers for research purposes. 

## 2. The FaintCal Workflow Tool
The primary software output of the CALIFAINT project is the `FaintCal` workflow tool. It is designed to ingest raw detector frames, apply the dynamic response model, and output calibrated science frames with associated variance maps.

### 2.1. Intellectual Property Status
Västerled University Innovation Office has formally reviewed the codebase. The university host confirms employment through any proposed PoC and owns the new calibration code developed under the CALIFAINT grant. There are no encumbrances on the core algorithmic IP, which was developed entirely by university employees.

### 2.2. Legacy Dependencies and Integration
The current laboratory setup relies on the `DetControl-Pro` legacy detector-driver module to interface the hardware with the `FaintCal` processing pipeline. Note that `DetControl-Pro` is licensed for internal academic use only, with no redistribution rights; it must be replaced, separately licensed, or kept out of a transferable tool. An open-source driver, `SkarvDrive`, exists and provides similar hardware communication capabilities, but its integration with the `FaintCal` workflow remains untested.

## 3. Prospective Validation and Stretch Applications

### 3.1. Laboratory User Validation
To move beyond simulation, prospective laboratory user validation can test the innovation potential of the `FaintCal` tool. We have scheduled sessions for Q1 2027 where two external astrophysics groups will bring their own sensor hardware to our testbench to evaluate the workflow tool's usability and performance on unseen sensor architectures. The Q1 2027 sessions are funded from CALIFAINT and are preparatory activities before any PoC award; their results are not yet available as of this record.

### 3.2. Translation to Environmental Sensing
While `FaintCal` was developed for astronomy, the detector response model is mathematically agnostic to the source of the photons. Translation to low-light environmental sensing is a hypothesized stretch using the same detector response model, provided the noise regimes align. Specifically, we hypothesize that nocturnal atmospheric aerosol fluorescence monitoring (using UV LED excitation and a 10 Hz readout configuration) suffers from similar sub-electron noise limitations. Establishing whether detector-state noise limits this specific measurement will be an early feasibility gate. 

We have planned a domain evaluation in collaboration with the Swedish Institute for Environmental Physics. This evaluation will assess whether the dynamic response model can accurately separate faint aerosol fluorescence signals from sensor noise in ground-based nocturnal monitoring stations. This represents a significant potential pivot for the technology, expanding its utility beyond fundamental astrophysics into applied environmental monitoring.
