> Fictional document created for ProposalBench.

*(Status as of September 2026)*

# Final Report: VAELTHES (2021–2025)

**Project Title:** Integration of Pit Thermal Energy Storage in Low-Temperature District Heating
**Funder:** Danish Energy Agency (Energy Technology Development and Demonstration Program - EUDP)
**Grant Number:** EUDP-2020-88492
**Total Budget:** DKK 32,500,000
**Project Duration:** 54 months (1 January 2021 – 30 June 2025, including a 6-month extension due to supply chain delays during construction). Commissioning was completed in September 2022.
**Coordinator:** Prof. Dr. Torben Hesselkilde, Hesselvarde Institute of Thermal Systems (HITS).

## 1. Executive Summary
The VAELTHES project designed, constructed, and monitored a full-scale pit thermal energy storage (PTES) pilot integrated into the municipal district heating network of the explicitly fictional municipality of Fjordkøbing, Denmark. The project aimed to demonstrate the technical feasibility and economic viability of seasonal thermal storage for balancing fluctuating renewable heat sources (solar thermal) and continuous industrial waste heat. Over two complete operational heating seasons and a partial third, the project successfully validated thermodynamic models, optimized charge/discharge cycles, and quantified the impact on local heat production costs.

## 2. Site Description and System Architecture
The pilot facility was constructed in the explicitly fictional municipality of Fjordkøbing, which has a fictional network service population of 18,000. In 2021, 92% of its 7,800 households were connected to the district heating network.

- **Storage Facility:** A truncated pyramidal pit excavated in clay soil, lined with a high-density polyethylene (HDPE) geomembrane. The total active storage volume is 75,000 m3. The storage operates between 35°C and 75°C, providing a usable energy capacity of approximately 3,400 MWh. The annual thermal energy input (charge) is 12,500 MWh, and the annual output (discharge) is 9,750 MWh, assuming zero net change in stored energy over a full annual cycle.
- **Heat Sources:** The PTES is charged by a 15,000 m2 solar thermal collector field and a continuous 2.5 MW waste heat stream recovered from a local data centre. The 15,000 m2 solar thermal collector field produces 7,500 MWh/year of useful heat. The 2.5 MW continuous waste heat stream provided 21,900 MWh/year of available heat at 30°C. Of this, 12,600 MWh/year was recovered by the heat pump. The 2.5 MW electrical industrial heat pump consumed 6,000 MWh/year of electricity (average COP 3.1) to deliver 18,600 MWh/year of heat at 75°C. This heat was directed either to the storage or directly to the network.
- **Network Integration:** The low-temperature district heating network operates with a forward temperature of 65°C and return of 35°C. The total delivered heat demand of the network is 30,000 MWh/year.

## 3. Methodology
- **Monitoring:** The PTES was equipped with 120 distributed temperature sensors (PT100) suspended on 12 vertical strings to monitor thermal stratification. Flow meters and energy meters logged data at 5-minute intervals.
- **Modelling:** A dynamic digital twin of the PTES and the district heating network was developed using Modelica. The model was calibrated using the first year of operational data.
- **Control Strategy:** Model predictive control (MPC) algorithms were implemented to optimize the charging from the solar field (weather-dependent) and the data centre (baseload), minimizing the use of a backup gas boiler.

## 4. Key Results

### 4.1. Thermodynamic Performance
- **Efficiency:** The PTES achieved seasonal round-trip thermal efficiencies of 75% (1 Oct 2022 – 30 Sep 2023), 78% (1 Oct 2023 – 30 Sep 2024), and 81% (partial season 1 Oct 2024 – 30 Jun 2025). The pooled average efficiency across the two complete seasons and partial third was 78% (95% CI 76–80%). This confidence interval represents the uncertainty in the observed energy balance, derived from meter accuracy limits and the serial dependence of daily measurements over the 1,004-day monitoring period, rather than variability across seasons. Efficiency is defined as the ratio of annual discharge to annual charge, evaluated between points of identical stored energy inventory.
- **Heat Losses:** With zero annual inventory change, the remaining 2,750 MWh (22% of the 12,500 MWh annual input) is entirely attributed to seasonal heat losses to the surrounding soil and through the floating insulated cover. Losses stabilized after the first 18 months (March 2024) as the surrounding soil reached a thermal quasi-equilibrium.
- **Stratification:** The system maintained a robust thermocline, with a transition zone thickness of less than 1.5 meters during 85.0% of the eligible operational time (208,675 out of 245,500 valid 5-minute observations filtered for periods of active stratification), ensuring high exergy efficiency during discharge.

### 4.2. Economic Impact
- **Heat Cost:** The estimated effect of the intervention was a heat production cost reduction of 12 EUR/MWh (95% CI 10–14 EUR/MWh, calculated via block bootstrap to account for autocorrelation). This compares the operational period (1 July 2023 to 30 June 2025, n = 731 daily observations) to a 2018 baseline system configuration (gas boiler and solar thermal only). The analysis held fuel and electricity prices constant at 2021 real values, included all variable operating and maintenance costs, excluded the capital costs of the storage facility, and normalized for weather variations.
- **Fossil Fuel Displacement:** Backup gas boiler utilization was reduced by 70%, from a 2018 baseline of 25,000 MWh of natural gas fuel input (at 90% boiler efficiency, delivering 22,500 MWh of heat alongside 7,500 MWh from solar) to 7,389 MWh/year of fuel input (delivering 6,650 MWh/year). Using a combustion emission factor of 0.202 tCO2/MWh of fuel input, this resulted in gross avoided combustion emissions of 3,557 tonnes of CO2 annually (95% CI 3,400–3,700, based on n = 731 daily observations and uncertainty in the emission factor). After accounting for the 6,000 MWh/year of electricity used by the industrial heat pump (using a fixed scenario electricity-emissions factor of 0.135 tCO2e/MWh, selected for this fictional analysis and not asserted to be the 2023 Danish grid average), the estimated annual net operational savings under that fixed-factor scenario, excluding embodied and upstream fuel emissions, were 2,747 tonnes of CO2-equivalent.

### 4.3. Network Integration
- The low-temperature supply (65°C) proved sufficient to maintain required substation heat delivery rates and primary return temperatures (35°C) across the connected building stock, which primarily consists of buildings renovated after 1990.

## 5. Limitations and Identified Gaps
While the technical and thermodynamic objectives were fully met, the project identified several non-technical limitations:
1. **Social and Economic Fairness:** The project only calculated the bulk heat production cost reduction for the utility. We did not assess how these savings are passed on to consumers, nor did we design fair tariff structures to ensure the benefits reach low-income households. The consortium lacked the energy economics and social science expertise required for such an analysis.
2. **End-User Health and Comfort:** We monitored aggregate energy consumption and temperatures at the substation level but did not measure indoor climate parameters or health outcomes for the end-users. The impact of the low-temperature supply on the health and well-being of vulnerable occupants remains unquantified.
