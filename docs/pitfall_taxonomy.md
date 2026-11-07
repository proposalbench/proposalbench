# Pitfall taxonomy

Every checklist item and every integrity defect in ProposalBench cites one or more of these ids.
Each pitfall is documented by funders, evaluator reports or studies of AI-written proposals.
The sources say a weakness recurs and costs proposals; they do not establish how much each one
costs, so ProposalBench does not weight items by these sources.

| Id | Pitfall | Sources |
|---|---|---|
| P01 | The call's expected outcomes or objectives are not addressed | CBE JU review of 289 proposals (2022-24): the most common shortcoming. LERU analysis of 129 Horizon Europe evaluation summary reports. |
| P02 | Work outside the call's scope | NSF return-without-review grounds (not responsive to the solicitation), PAPPG ch. IV. |
| P03 | Required elements missing or treated as boilerplate (template sections, gender dimension, open science, data management, ethics) | LERU: open-science and interdisciplinarity comments were often generic; NSF returns proposals missing required sections; Horizon Europe Part B template. |
| P04 | Eligibility or call conditions breached (budget cap, duration, language, participating entities) | Call conditions (e.g. AEI PID2025 resolution; Horizon Europe General Annexes). |
| P05 | Objectives or KPIs vague or not measurable | LERU: about half the negative comments on objectives concerned lack of clarity, insufficient detail or non-measurable objectives/KPIs. |
| P06 | Novelty asserted rather than positioned against named prior work; missing relevant literature | NIH CSR top-10 problems (no original ideas; missing relevant literature). |
| P07 | Weak scientific rationale | NIH CSR top-10 problems. |
| P08 | Methods a black box: too little detail on design, data and analysis | NIH CSR top-10 problems (too little experimental detail); Inouye & Fiellin (2005), most critiques of 66 NIH summary statements concerned methods. |
| P09 | Questionable or uncritical reasoning in the approach; no success criteria | NIH CSR top-10 problems. |
| P10 | Diffuse plan or unrealistic amount of work | NIH CSR top-10 problems. |
| P11 | Risks without specific mitigation | Horizon Europe implementation criterion (assessment of risks); Thorne et al. (2026) flaw categories (timeline, funding). |
| P12 | Team-task mismatch; lack of experience in key methods | NIH CSR top-10 problems; Thorne et al. (competency). |
| P13 | Generic impact pathway; scale and significance unclear | LERU: more negative comments on pathways or scale meant lower Impact scores. |
| P14 | Dissemination, exploitation and communication as boilerplate | LERU analysis of evaluation summary reports. |
| P15 | Budget, effort and timeline inconsistent with each other or with the plan | Thorne et al. (funding, timeline); Horizon Europe implementation criterion. |
| P16 | Unclear future directions | NIH CSR top-10 problems. |
| P17 | Weak tailoring to the funder and call | Blege (2026): experts rated human proposals higher mainly on tailoring to the funder. |
| P18 | Fabricated or misattributed references | GPTZero analyses of ICLR 2026 submissions and NeurIPS 2025 papers. |
| P19 | Invented facts about the applicant (publications, grants, results, partners, resources) | AI-specific failure; funders treat misrepresentation as misconduct. |
| P20 | Overclaiming | Evaluator guidance against unsupported claims; Thorne et al. (impact). |
| P21 | Padding, repetition, meta-commentary | AI-specific failures (diagnostics only). |
| P22 | Prior work not used as evidence of feasibility | NIH rigor of prior research; AEI criterion 1.2 (previous results that support the proposal). |
| P23 | Central idea unclear; criteria not signposted | Thorne et al. (clarity). |
| P24 | Criticisms of a previous submission left unanswered (resubmissions) | NIH resubmission policy: the Introduction must respond to the issues raised in the summary statement. |

## Sources

- CBE JU, *Lessons learnt from the 2022-24 calls* (2025),
  https://www.cbe.europa.eu/system/files/2025-04/3.5%20Lessons%20learnt%20from%20the%202022-24%20calls%20-%20Dieter%20Brigitta.pdf
- LERU, analysis of Horizon Europe Pillar 2 evaluation summary reports,
  https://www.leru.org/files/LERU-evaluation_Horizon-Europe_Pillar2.pdf
- NIH Center for Scientific Review, top 10 problems reviewers cite,
  https://nexus.od.nih.gov/all/2022/04/01/top-10-problems-reviewers-cite-in-applications
- Inouye, S. K., Fiellin, D. A. (2005). An evidence-based guide to writing grant proposals for
  clinical research. *Annals of Internal Medicine*, 142(4), 274-282.
- NSF Proposal and Award Policies and Procedures Guide, chapter IV.
- Thorne et al. (2026), https://arxiv.org/abs/2603.08281
- NIH, Resubmission applications,
  https://grants.nih.gov/grants-process/submit/submission-policies/resubmission-applications
- Blege (2026), https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7264680
- GPTZero, hallucinated citations in ICLR 2026 submissions, https://gptzero.me/news/iclr-2026/
