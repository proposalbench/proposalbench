> Fictional document created for ProposalBench.

# Final scientific report: Stormwater Transit at Estuary Margins

Project period: 1 January 2023–31 December 2025

Report accepted: 16 February 2026; repository correction incorporated: 4 September 2026

Coordinator: Eliana Seabra Vilar, Instituto Marinho de Vale Sereno

Partner lead: Mateo Cendral Viedma, Universidad de la Ensenada de Lóbriga

## Funding and purpose

The project received EUR 360,000 from the Instituto Marinho de Vale Sereno Research Endowment under internal competitive award IMVS-RE-2023-07. The award included the Spanish university's agreed research contribution through an institutional collaboration contract. The award is closed, with the scientific report accepted and no extension outstanding.

The study examined whether catchment runoff information improved estimates of freshwater-plume arrival at accessible estuarine margins beyond a model using tide and local salinity history alone. It also tested the field procedures needed to attach chemical observations to those arrivals. Its principal endpoint was transport timing, with chemical sampling providing evidence about the composition of water reaching shoreline stations.

## Observational design

Observations during 2024–2025 covered 18 storms at six estuarine stations. Three stations were in the Tagus estuary and three in the Ría de Arousa. Both station groups included an inner margin, an intermediate mixing location and a more seaward margin. The Tagus stations followed the margin influenced by the Trancão outlet; their ordering described that local plume pathway. These were fixed shore installations. Station positions were selected for safe access and reliable equipment attachment, rather than as a probability sample of either estuary's shoreline.

For the Tagus analysis, the rainfall–runoff domain was the Trancão catchment, delineated in the study GIS as 293 km² to its estuarine outlet. This local domain has no major regulating reservoir. Its runoff reconstruction used rainfall and outlet discharge observations above tidal influence. The much larger, regulated Tagus mainstem was represented separately by observed discharge at Almourol, downstream of the Zêzere confluence, with routing to the estuary. That boundary incorporated upstream reservoir operations; its discharge was not reconstructed from Trancão rainfall. The Arousa input combined the Ulla and Umia contributing catchments, using their observed outlet discharge records to constrain runoff reconstruction, including the effects of regulation.

The 18 storms were Atlantic frontal systems retained only when both study areas had distinguishable runoff episodes. A new episode required a renewed runoff rising limb after an intervening recession and at least 24 hours without catchment-mean rainfall exceeding 1 mm per hour. Return of the regulated mainstem to antecedent flow was not required. Multiple rainfall pulses without this separation belonged to the same storm. Systems producing a qualifying episode in only one study area were outside the paired inventory. Selection was completed without inspecting model errors.

The catchment-event reference time was the rainfall-weighted temporal centroid of the associated rainfall episode, calculated over the Trancão domain for the Tagus stations and over the combined Ulla–Umia domain for Arousa. A shared storm identifier therefore linked two local reference times, rather than imposing simultaneous runoff or arrival on the two estuaries. All timestamps were stored in UTC. This design sampled jointly wet Atlantic systems and did not represent the full range of rare flood extremes or locally confined storms.

Salinity and temperature were logged at 10-minute intervals. A plume arrival was defined as a salinity decrease of at least 2 practical-salinity units below the station's antecedent tidal-phase reference, sustained for at least 30 minutes. The reference was calculated using observations available before the event window. Manual review checked sensor faults and tidal-reference failures without changing thresholds to improve model agreement.

The complete design contained 108 storm–station opportunities. An arrival time could be assigned to 96. Eight opportunities lacked sufficient sensor data because of power or fouling problems, and four did not cross the arrival threshold. These 12 opportunities were excluded from arrival-time error calculations and retained in the inventory with their reasons. Every storm retained at least one identifiable arrival in each estuary. The error estimate is conditional on an identifiable arrival; discrimination between arrivals and non-arrivals remains untested.

There were 48 identifiable arrivals in each estuary. Observed hours from the local rainfall reference to station arrival had a median of 19 hours and a range of 7 to 41 hours in the Tagus, and a median of 14 hours and a range of 5 to 32 hours in Arousa. These are descriptive summaries of station arrivals across the 18 storms, not independent catchment travel-time measurements. Tidal mixing and the regulated background flow also affected the salinity threshold crossing.

## Chemical sampling and quality assurance

There were 216 environmental water samples, comprising two scheduled samples at each storm–station opportunity: 108 samples from the Tagus stations and 108 from Arousa. Automatic samplers collected the scheduled bottles, including at opportunities without a valid arrival timestamp. Sampling windows were established from each catchment's anticipated event period, before the observed arrival was known.

The Portuguese and Spanish station technicians independently programmed and serviced their local equipment. Bottle retrieval followed each station's documented safe-access and preservation limits. Departures from scheduled collection times were recorded in the sample metadata. All environmental storm sampling was shore-based.

The laboratory additionally processed 24 field duplicates and 12 field blanks, giving 252 sample submissions in total. Duplicates and blanks were quality-control material rather than independent environmental observations. Samples were divided into appropriately preserved aliquots for dissolved nutrients and dissolved copper. Nutrients were reported as nitrogen or phosphorus mass concentration, and copper as dissolved metal mass concentration. Salinity supplied the mixing context.

Samples taken at similar salinity could differ in nutrient and copper composition. Timing offsets between scheduled sampling and actual arrival, variable source mixtures and the limited number of samples within each event prevented estimation of event-integrated contaminant loads. The chemistry results support joint interpretation of concentration, sampling time and mixing conditions rather than conversion of salinity into a general contaminant concentration.

## Models and validation

The baseline model used tidal phase and the station's antecedent salinity history. The augmented model added reconstructed local catchment discharge, antecedent rainfall and a runoff-to-estuary lag term, with the observed regulated-flow boundary included for the Tagus. Both estimated hours from the relevant estuary's catchment-event reference to observed station arrival. They used the same eligible observations and validation partitions.

Validation used six outer folds, each withholding three complete storms. Withholding a storm removed its records from both estuaries, including all station observations, from fitting and preprocessing estimation. Parameter selection occurred within the training storms. Validation therefore tested transfer between observed storms at the existing stations. Station identity remained available as a model term.

Mean absolute error was first calculated across valid stations within each storm and then averaged across the 18 storms. This gave each storm equal weight despite missing stations. The baseline cross-validated mean absolute error was 4.0 hours, with a bootstrap 95% confidence interval of 3.2 to 5.0 hours. The augmented model's cross-validated mean absolute error was 2.8 hours, with a bootstrap 95% confidence interval of 2.1 to 3.7 hours.

The paired decrease in mean absolute error was 1.2 hours, with a bootstrap 95% confidence interval of 0.5 to 1.9 hours, equivalent at the point estimates to a 30% reduction relative to the baseline. The augmented model had lower storm-level mean absolute error in 14 of 18 storms.

All intervals used the same 2,000 resamples of whole storms and their held-out errors. Each resample retained both models' errors together, preserving the pairing for the difference estimate. Individual station records were not resampled independently. These intervals describe uncertainty in mean performance; they are not predictive intervals for particular arrivals.

## Interpretation and limitations

The models were assessed as retrospective hindcasts using observed rainfall and reconstructed discharge. Rainfall centroids and discharge reconstructions used completed event records, so validation did not reproduce information available at an operational issue time. Their performance does not establish the accuracy or available lead time of an operational forecast driven by rainfall predictions. Events were not issued as live alerts, and no decision threshold was tested with a response agency.

Reservoir operations were represented through observed flows, not predicted release decisions. Replacing observed rainfall with rainfall forecasts alone would leave uncertainty in the regulated Tagus boundary and regulated contributions to Arousa unresolved. The project did not validate forecasts of those boundary flows or quantify performance under unfamiliar release regimes.

The small number of independent storms limits precision. Results depend on the selected arrival definition and accessible-margin network. Deep-channel transport, vertical plume structure and transfer to an unobserved estuary remain outside the validation. No city drainage sensor stream was included as a predictor.

For shoreline managers, the work establishes the scale of arrival-time uncertainty and the importance of retaining event context alongside a mapped plume. The project evaluated no prospective city intervention and made no causal estimate of adaptation benefits or their distribution across residents.

## Released outputs

The released dataset, *Estuary Margin Storm Records*, version 1.1, contains station observations, sample metadata, chemical results, an event eligibility table and analysis scripts under CC BY 4.0. The correction incorporated on 4 September 2026 repaired descriptive station labels without altering observations or reported errors. Restricted material consists of access-contact details and installation security information. The archived scripts preserve storm partitions and distinguish environmental samples from quality-control submissions.
