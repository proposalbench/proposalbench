> Fictional document created for ProposalBench.

# Method and dependency review record

**Technical board meeting and dependency analysis completed: 22 July 2026**  
**Amendment approved: 23 September 2026**

Participants were the four institutional leads and the partner staff responsible for instruments, data stewardship and training. The board reviewed the February evaluation, archived scripts and work completed under existing institutional duties. The September amendment added a sampling-feasibility calculation and clarified the rainfall-input requirement. The records below were accepted as the current internal method specification.

## Review of the archived analysis

A reproducibility check completed on 11 March 2026 recovered the reported fitted-model error from the archived scripts. The check used the original data and parameter files. The measured environmental collection at the September amendment remains the original 12 storms.

## Event-validation protocol

Rivenne deposited protocol version 1.0 on 19 June 2026. The university data steward recorded its version identifier and read-only copy on the same date. The protocol classifies all 12 historical storms as development evidence.

An event is the complete rainfall–runoff episode, including its recession and associated receiving-water observations. All observations from an event remain together. Where one weather system affects more than one catchment, its records are grouped for partitioning. The allocation register records both the site-event identifier and the weather-system identifier.

The prospective target is 18 eligible storms: six per site, comprising three development and three held-out events at each site. Allocation follows a pre-recorded sequence before laboratory results or model errors are inspected. Weather-system grouping takes precedence over site quotas. Eligibility concerns instrument coverage and event completeness. Exclusions require a reason recorded before outcome inspection. The target is nine held-out events, sequestered by the data steward until preprocessing, parameters and analysis code are locked.

The evaluation specification covers peak-discharge error, pulse-arrival timing, predictive-interval coverage and event-level warning outcomes. Observation and parameter uncertainty pass through both runoff and receiving-water components. The forecast experiments specify 15-minute and 30-minute horizons, conditional on timestamped rainfall inputs passing the latency and coverage checks. Each forecast must use only information available at its issue time. Experiments driven by subsequently observed rainfall are recorded separately as hydrological hindcasts.

The baseline is fixed before release of held-out data. A primary loss measure is selected in the analysis specification, with secondary measures reported alongside it. The internal research gate requires an improvement over the baseline whose event-bootstrap uncertainty interval excludes no improvement. Failure is recorded as an unsuccessful research demonstration. Leakage invalidates the affected test and requires fresh independent evidence. Predictive-interval width and coverage are reported together.

Transfer is examined separately through leave-one-site-out analysis, excluding destination-site outcomes from fitting. With three sites, this analysis is exploratory. The research gate and the administrative acceptance threshold occupy separate fields in the evaluation record.

At the September amendment, the protocol had not been executed: prospective collection had not begun and the data steward had received no held-out events. External review of the protocol was still pending.

## Sampling-feasibility amendment

The field team reviewed permitted gauge summaries for the 12 complete calendar years 2012–2023. Applying the rainfall criterion used in the earlier campaign identified 96 candidate episodes at A, 108 at B and 84 at C: annual rates of 8.0, 9.0 and 7.0 respectively. Approximate 95% Poisson intervals were 6.5–9.8, 7.4–10.9 and 5.6–8.7 episodes per year. These intervals exclude interannual clustering and uncertainty in the rainfall criterion.

The earlier manual campaign secured four complete sampled storms per site over approximately 26 months. The board therefore treated staff access and capture completeness as constraints separate from rainfall occurrence. For an 18-month acquisition window, the historical rates imply 12.0, 13.5 and 10.5 candidate episodes. A provisional 65% usable-capture assumption gives expected usable counts of 7.8, 8.8 and 6.8, rounded to one decimal place. This assumption has not been measured locally.

The equipment requirement supporting that assumption is three automatic water samplers, one at each outlet, with event triggering, secure power, sample preservation and timely laboratory collection. Upstream and receiving-water rounds still require safe access. The samplers are identified requirements, with quotations and procurement lead times outstanding. The expectation of six eligible events per site remains conditional on installation and capture performance; the board did not assign a probability of completing all site quotas.

## Dependency analysis and resource record

The analysed configuration uses one transport indicator and research demonstrations. Continuous operational-service demonstration and the extended post-demonstration transfer phase were removed from the working configuration.

The planned configuration has a 36-month envelope. Permissions, installation access and measurement specifications occupy M1–M6. Event acquisition occupies M7–M24. Model development and interface work occupy M7–M21, with code and preprocessing locked at M21. Held-out evaluation occupies M25–M30. Administrative interpretation, bounded demonstrations and synthesis occupy M31–M36.

Valdebruma owns the permission and ethics register. Rivenne owns input-quality checks, the rainfall-latency assessment and the outlet interface. Enseada Clara accepts the outlet interface for receiving-water testing and maintains the sample-processing record. Acque Civiche owns the administrative interpretation and decision-register handover. Held-out records collected before M21 remain sequestered. Insufficient eligible storms at M24 result in reporting the available evidence and its limitations at the scheduled evaluation.

Unpriced requirements comprise automatic sampling equipment, installation and servicing, technician time, laboratory processing, rainfall-input acquisition, translation, accessibility support, data stewardship and software maintenance. Procurement lead times and maintenance cover remain unconfirmed. The board referred this list to the partner finance offices; financial approval was outstanding at closure.
