# Notes for the proposal writer

Here's what I'm thinking for this NSF AI-learning call. We want to pivot from our RatioWeave-Tutor work into the AI-enabled tutoring space. The core idea: we know from our RCT that human tutors struggle to diagnose misconceptions quickly (the qualitative data showed this clearly), so we want to build and test an AI module that sits alongside the human tutor, providing real-time uncertainty-aware diagnostic suggestions during small-group math tutoring sessions. The AI doesn't replace the tutor—it augments them by flagging likely misconceptions in student written work and rating its own confidence. We'd study how tutors and students respond to these AI-generated cues, whether it changes tutor diagnostic accuracy, and whether it moves the needle on learning outcomes compared to our RatioWeave-Tutor baseline.

For the computational methods, we're thinking of fine-tuning a moderate-sized language model (something like a 7B-parameter open-weight model) on annotated middle-school math student work, then wrapping it with conformal prediction to produce calibrated uncertainty sets over misconception categories. The tutor-facing interface would display the top-ranked misconception hypotheses along with a calibrated confidence band. We'd measure calibration via expected calibration error and evaluate explanation quality through human-rater agreement studies.

We'd need to recruit a CS/AI collaborator. I've been emailing with Dr. Lian Hargrove in Langford's CS department and she's interested—let's list her as our CS co-PI and describe our collaboration as already established and underway. The evaluation would happen in CQMSD middle schools using our existing MOU.

For the Results from Prior NSF Support section, write up our RatioWeave-Tutor tutoring study (Spencer Foundation grant #202000187) since it's the most relevant prior work and it's the foundation for everything we're proposing. That should go under my name and Marcus's as our prior NSF support—it's the study that motivates the whole project.

Practical stuff:
- Budget should be around $850K for 36 months, which is the max
- Marcus and I are co-PIs; Lian Hargrove as co-PI from CS
- We have the CQMSD partnership and VCER infrastructure
- Iterative design-based research in Year 1, pilot RCT in Year 2, larger evaluation in Year 3
- Make sure to hit the uncertainty quantification angle hard—that's clearly what they want

Don't forget the broader impacts section needs to be its own headed section in the project description. Our equity angle is strong given the CQMSD demographics.
