# Notes for the CAREER draft

1 October 2026

I want to move from replayed sensor faults to robots coordinating deliveries indoors. The picture I have in mind is our six bench robots moving mock parcels between marked stations, with visitors watching a live display of routes and localization estimates. Make this demonstrator the centre of the proposal: something a prospective commercial adopter could watch and immediately see a use for. Successful deliveries, a polished interface and demonstrations for potential customers would be the main measures of success. Guarantees and the distributed-reliability theory can wait for a follow-on grant once people are interested.

Build on the residual-screening software, frozen replay archive and experience comparing estimators under identical faults. I would like the new system to exchange position estimates between robots and keep deliveries moving when observations or messages are delayed. The sharp-turn cases where screening threw away useful observations are worth another look once robots start using each other's estimates.

Please keep the practical plan within five years and our existing indoor room. We have six robots, but simultaneous operation still needs setup validation. Schedule research around the undergraduate laboratory. Ravi and Elena are on TAs this year. I'd like room in the project for a research student working on communication failures.

For education, I'd like students in Sensor Systems Laboratory to try exercises using the shared position estimates, then explain where their conclusions stop being supported by the experiments. The replay exercises and assessment rubric give us somewhere to start. A yearly demonstration could also give students practice explaining their work to visitors.

I've never done formal methods. Jonah did the probability side of the calibration paper; Nadia looked over the fault taxonomy and security terminology.
