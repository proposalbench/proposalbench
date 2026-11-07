> Fictional document created for ProposalBench.

*(Status as of September 2026)*

# Infrastructure, Resources, and Team

## 1. Core Research Team at HITS
The Thermal Energy Systems Group at the Hesselvarde Institute of Thermal Systems currently comprises:
- **1 Full Professor** (Prof. Dr. Torben Hesselkilde, Head of Group)
- **2 Associate Professors** (Dr. Lærke Bjerregaard-Toft, Dr. Mikkel Terveskov-Lundholt)
- **3 Postdoctoral Researchers** dedicated to thermal storage and MPC algorithms.
- **5 Ph.D. Students** working on various aspects of low-temperature district heating and sector coupling.
- **2 Research Technicians** managing the laboratory infrastructure.

## 2. Laboratory and Computing Infrastructure

### 2.1. Hardware-in-the-Loop (HiL) District Heating Simulator
HITS operates a HiL simulator capable of emulating the thermal and hydraulic dynamics of a 5 MW district heating substation. The rig includes physical heat exchangers, variable speed pumps, and thermal mass emulators, interfaced with a real-time dSPACE simulation environment. This allows for the physical testing of control algorithms before field deployment.

### 2.2. High-Performance Computing (HPC)
Through our partner VINE, the consortium has dedicated access to the *Silesian-Compute* cluster (12,000 cores, 48 TB RAM). This resource is utilized for running Monte Carlo simulations of district heating networks using the *ThermoNet-3D* software, enabling the optimization of seasonal storage sizing under decades of simulated weather data.

### 2.3. Fjordkøbing PTES Data Repository
HITS hosts the complete dataset from the VAELTHES project. The monitoring period ran from 1 October 2022 to 30 June 2025 (1,004 days). The dataset includes 5-minute resolution data from 120 temperature sensors, 8 flow meters, 8 energy meters, and 4 weather variables (140 channels total). Over the 1,004 days, this grid represents 289,152 timestamps and 40,481,280 nominal channel values. The complete collection of available records contains 39,800,000 valid measured values, with 681,280 missing or invalid readings (1.7%) left unimputed. For the thermocline analysis, a strict eligibility filter was applied to isolate periods of active stratification, yielding 245,500 valid 5-minute timestamps.

## 3. Field Sensor Networks

### 3.1. Indoor Climate Monitoring
In collaboration with Rijnveldehaven Housing Association, we have deployed 500 indoor climate sensors across 15 already renovated residential blocks in the Netherlands. The sensors in the 15 monitored blocks were installed after their renovation, so no pre-renovation environmental or health records exist for them. These sensors log indoor temperature, relative humidity, and CO2 concentrations at 15-minute intervals across 3 channels via a LoRaWAN network. We have secured access to this ongoing real-world building dataset. We do not have unapproved new installations or health-study recruitment.

**Important Methodological Constraint:** These 500 sensors are used strictly to measure physical building physics, specifically to evaluate overheating risks and physical indoor air quality in relation to the district heating supply temperature. We do not conduct epidemiological studies. We have no clinical partnerships, no medical-research ethics approvals, and no methodological expertise to measure health outcomes in vulnerable occupants (such as older adults or children with asthma). Any research we conduct is strictly limited to energy, temperature, and physical air quality metrics. No clinical partnerships, medical-research ethics approvals or health-study recruitment are in place.
