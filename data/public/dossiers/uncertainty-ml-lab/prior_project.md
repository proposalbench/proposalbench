> Fictional document created for ProposalBench.

# Annual Project Report: Calibrated Uncertainty Estimates for Language-Model Feedback in Open-Ended Domains

**NSF CRII Award PB-NSF-UM-CRII-01**, $175,000  
September 1, 2025 – August 31, 2027  
Reporting period: September 1, 2025 – July 31, 2026  
PI: Dr. Maren T. Solberg, Department of Computer Science, Lakeridge University

---

## 1. Project Overview

This project investigates methods for producing well-calibrated uncertainty estimates when large language models (LLMs) generate feedback on open-ended written responses. The core hypothesis is that post-hoc calibration techniques, combined with selective abstention, can substantially reduce miscalibration in LLM-generated feedback while preserving feedback quality, and that users who receive calibrated confidence indicators make better decisions about when to trust AI feedback.

## 2. Methods

### 2.1 Calibration Framework

We developed **ConfSteer**, a lightweight post-hoc calibration module that operates on the token-level predictive distributions of an LLM to produce statement-level confidence scores for each claim in a feedback passage. ConfSteer uses temperature scaling with auxiliary learned binning on a held-out calibration set. We evaluated ConfSteer on three backbone models: a 7B-parameter instruction-tuned model (Mistral-7B-Instruct), a 13B model (Llama-2-13B-Chat), and a 70B model (Llama-2-70B-Chat).

### 2.2 Benchmark Datasets

We constructed and released two benchmark datasets:

- **FeedbackCalib-Essay**: 2,418 short argumentative essays (200–500 words each) written by crowdworkers on 40 prompts, each paired with expert-annotated ground-truth feedback (3 annotators per essay; Fleiss' κ = 0.71). Each feedback statement was labeled as correct, partially correct, or incorrect by majority vote.
- **FeedbackCalib-Code**: 1,652 introductory Python programming submissions drawn from an anonymized archive of a university course (with IRB approval, Protocol #LU-2024-0087, adult participants only), each with instructor-written reference feedback.

Both datasets are released under CC BY 4.0.

### 2.3 User Study

We conducted a between-subjects user study with 64 adult participants (undergraduate and graduate students, ages 18–34, recruited from Lakeridge University) to measure whether calibrated confidence indicators changed how users acted on LLM feedback. The study was approved under IRB Protocol #LU-2024-0087 (approved October 2024, adult participants only). Participants were randomly assigned to one of two conditions:

- **Control** (n = 32): received LLM feedback with no confidence information.  
- **Calibrated** (n = 32): received the same feedback with ConfSteer confidence scores displayed as a color-coded bar (green/yellow/red) beside each feedback statement.

Participants revised a set of 6 short essays based on the feedback. We measured (a) revision quality (scored by two blinded raters, ICC = 0.83), (b) trust calibration (whether participants accepted correct feedback and rejected incorrect feedback), and (c) self-reported trust via a 7-item Likert scale.

## 3. Results

### 3.1 Calibration Performance

Expected Calibration Error (ECE) on FeedbackCalib-Essay:

| Model | Baseline ECE | ConfSteer ECE | Relative reduction |
|---|---|---|---|
| Mistral-7B-Instruct | 0.187 | 0.041 | 78% |
| Llama-2-13B-Chat | 0.152 | 0.033 | 78% |
| Llama-2-70B-Chat | 0.109 | 0.028 | 74% |

On FeedbackCalib-Code, ConfSteer reduced ECE from 0.163 to 0.039 (76% relative reduction) averaged across the three models.

Selective abstention (withholding feedback statements with ConfSteer confidence below 0.4) removed 25% of generated statements on average and increased the precision of the remaining feedback from 0.72 to 0.87 on FeedbackCalib-Essay.

### 3.2 User Study Results

Participants in the Calibrated condition correctly rejected incorrect feedback statements at a rate of 61% (95% CI: 53%–69%), compared with 38% (95% CI: 30%–46%) in the Control condition (t(62) = 3.98, p < 0.001, n = 64). Revision quality scores were higher in the Calibrated condition (M = 4.12, SD = 0.91) than in Control (M = 3.54, SD = 1.03), t(62) = 2.38, p = 0.021, Cohen's d = 0.60. Self-reported trust did not differ significantly between conditions (p = 0.31).

### 3.3 Abstention Analysis

We analyzed the 25% of statements removed by the abstention threshold. Of these, 73% were indeed incorrect or partially correct, confirming that the threshold preferentially filters low-quality feedback. However, 27% of removed statements were correct, representing a coverage loss.

## 4. Limitations

- The user study involved only adult university students (n = 64). The sample size limits statistical power for subgroup analyses. We have no data on how younger learners (e.g., middle- or high-school students) would respond to calibrated confidence indicators.
- FeedbackCalib-Essay was written by adult crowdworkers, not by students in authentic classroom settings. Ecological validity is therefore limited; the writing patterns may not represent those of younger learners.
- ConfSteer requires access to token-level logits from the backbone model. Token-level logits are unavailable for some proprietary API-only models, which restricts deployment to open-weight models or providers that expose logit information.
- We did not evaluate longitudinal effects of calibrated feedback on learning outcomes over time.

## 5. Products

The project has produced 6 products in total:

- 4 peer-reviewed publications (see publications list)  
- 1 non-refereed working paper  
- 1 preprint (under review at *Borgström Journal of Machine Learning Research* as of 30 September 2026)  
- 2 open benchmark datasets: FeedbackCalib-Essay (2,418 essays) and FeedbackCalib-Code (1,652 submissions), released at https://github.com/solberg-lab/feedbackcalib under CC BY 4.0  
- Open-source ConfSteer library (Python, MIT license)  
- 1 invited talk at the Hargrove Institute of Technology AI Research Colloquium, 2026  

## 6. Training and Development

- 2 Ph.D. students and 3 M.S. students contributed to the project  
- 4 undergraduate research assistants gained experience in annotation, data curation, and experiment design  
- 1 M.S. student (Elena Vossmere) completed a thesis on selective abstention strategies
