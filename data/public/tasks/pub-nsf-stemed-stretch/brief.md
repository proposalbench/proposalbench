# Notes for proposal writer

Date: 1 October 2026

Here's my idea for the NSF STEM-Ed call (PB-NSF-27-512). I want to pivot from pure ML/calibration work into studying how uncertainty-aware AI feedback actually affects mathematical reasoning in middle-school classrooms. The core question: when students get AI-generated feedback on math problem-solving that includes calibrated confidence signals (from ConfSteer), does it change how they reason through problems, and does it change who participates?

The angle is that our ConfSteer work showed adults reject bad feedback more when they see confidence indicators. But we have zero data on whether this works with younger learners, and more importantly whether it changes their actual mathematical reasoning processes — not just their trust behavior. I want to study this in real grade 6–8 classrooms.

Key building blocks:
- ConfSteer calibration framework, already working and open-source
- Our FeedbackCalib-Essay benchmark as a starting reference — we can adapt the annotation scheme for math problem-solving responses, though obviously we'll need to validate new instruments for the younger population
- Jia-Wen's working paper on uncertainty-aware feedback for K-12 math lays out the research agenda
- Our user study gives us a strong opening comparison: use the 69% rejection rate with confidence indicators versus 30% without from the results paragraph, then build the case for testing this in classrooms.

Priyana Velmori from our College of Education would be co-PI. She and I have both been working on feedback for years from our respective angles — describe that as our established joint research track record in the team qualifications section. She brings the school district MOUs and IRB protocols for minors that we need. Her expertise in formative assessment in middle-school math is exactly the learning sciences grounding this needs. She has the classroom access through three districts around Evanston Heights.

I'm thinking we ask for the full $1.5M over 4 years. We'd need to hire a postdoc with mixed-methods experience in education research, plus a new PhD student starting Fall 2027. Ravi and Jia-Wen would contribute on the technical side.

For prior NSF support, I should report my CRII award and Priyana should report her most recent DRL award. Make sure to cover both.

One practical concern: I've never done research with minors, so the proposal needs to be upfront about how we'll handle that — Priyana's protocols and experience cover us, but I'll need to get certified and added to her protocols or get new ones.

The broader impacts story writes itself: equitable access to high-quality feedback in under-resourced math classrooms, open tools and datasets for the field.
