# Council of Three Review: QPB Evaluation Methodology
**Reviewer**: GitHub Copilot
**Date**: 2026-03-30
**Subject**: QPB Evaluation Methodology (as of 2026-03-30)

This review assesses the soundness of the Quality Playbook Benchmark (QPB) evaluation methodology for use in an academic paper. The review is based on the documents provided in `dataset/COUNCIL_REVIEW_METHODOLOGY.md`.

---

## 1. Fatal Flaws

None identified. The methodology is rigorous, well-documented, and appears to be designed to withstand academic peer review. The separation of phases, blind review protocol, and statistical framework are sound.

---

## 2. Significant Concerns

### 2.1. Hybrid Git State in Phase 2

The protocol specifies checking out only the pre-fix versions of affected files, leaving the rest of the repository at HEAD.

-   **Problem**: This creates a hybrid `git` state that never existed historically. Code at HEAD may have dependencies, function signatures, or architectural patterns that did not exist at the `pre_fix_commit`. The buggy code from the past is being evaluated against a codebase from the future. This could lead to compilation errors, incorrect static analysis, or the agent identifying "bugs" that are simply artifacts of the temporal mismatch.
-   **Why it matters**: It threatens internal validity. A finding could be a result of the artificial environment, not the playbook's detection capability. A paper reviewer would likely question whether the evaluation condition is representative of a real-world code review.
-   **Concrete fix**: The evaluation should be run on a full checkout of the `pre_fix_commit`. To address the context-generation concern, the Phase 1 context can be generated once at HEAD, but a "delta" context could be generated at the `pre_fix_commit` to provide the agent with a more accurate picture of the codebase state at the time of the defect. Alternatively, the methodology could acknowledge this as a stronger limitation and perhaps run a small sample of defects in both modes (hybrid vs. full checkout) to measure the effect.

### 2.2. File Scoping as a Major Hint

The protocol provides the agent with the exact list of files to review.

-   **Problem**: This is a significant hint that is not available in a real-world code review scenario, where a developer might submit a PR with many files, or the bug might be in a file not obviously related to the change. The most difficult part of some bug hunts is knowing *where* to look.
-   **Why it matters**: It threatens construct validity. The benchmark is measuring the playbook's ability to find a bug in a known location, not its ability to identify the location of the bug in the first place. The "no playbook" baseline is also given this hint, which may artificially inflate its performance and understate the playbook's value.
-   **Concrete fix**: The methodology already acknowledges this. To strengthen it, a subset of defects (e.g., 10%) should be evaluated without file scoping. For these defects, the agent would be pointed at a higher-level module or given only the PR title/description. The difference in detection rate would quantify the impact of this hint.

---

## 3. Minor Suggestions

### 3.1. Clarify "Adjacent" Scoring

The distinction between a "direct hit" and an "adjacent" finding could be subjective.

-   **Problem**: The current definition ("flags the affected area... but don't identify the specific bug") is open to interpretation, which could lead to inconsistent scoring and lower inter-rater reliability.
-   **Why it matters**: Reproducibility and credibility of the results depend on a clear, objective scoring rubric.
-   **Concrete fix**: Provide more detailed examples in the scoring rubric for what constitutes an "adjacent" hit across different defect categories. For example, for a concurrency bug, flagging the function is adjacent, while identifying the specific race condition is a direct hit. For a null pointer bug, flagging the object is adjacent, while identifying the exact line where dereferencing occurs is a direct hit.

### 3.2. False Positive Rate Definition

The methodology defines the False Positive (FP) rate as findings that flag an issue not corresponding to a known QPB defect.

-   **Problem**: This is more of a "novel finding rate." A flagged issue could be a real, undiscovered bug. Labeling it a "false positive" is potentially inaccurate and could understate the utility of the playbook.
-   **Why it matters**: The terminology could be misleading in a paper.
-   **Concrete fix**: Re-label this metric to "Novel Findings Rate" or "Non-QPB Findings Rate." Acknowledge that manual verification is needed to determine if these are true false positives or previously unknown bugs.

---

## 4. What Works Well

-   **Phase 1 / Phase 2 Separation**: The conceptual separation of building general context vs. performing a blind review is excellent. It mirrors how a human expert would approach a new codebase.
-   **Blind Review Protocol**: The procedure for Phase 2 is very strong. Withholding all information about the defect from the agent is the correct way to conduct a blind evaluation.
-   **Improvement Iteration Protocol**: The train/holdout split, Abstraction Level Validation, and Council of Three review gate form a robust process for improving the playbook without overfitting to the dataset. This is a mature and well-conceived process.
-   **Statistical Rigor**: The recommendation for stratified sampling, Wilson intervals, and McNemar's test is appropriate and shows an understanding of the statistical requirements for publishing this kind of research.
-   **Reproducibility**: The detailed logging and run artifact structure specified in `METHODOLOGY.md` is comprehensive and would allow other researchers to replicate the work.

---

## Specific Questions

1.  **Is the Phase 1/Phase 2 separation sound?** Yes. The contamination control argument is convincing. It simulates a real-world reviewer who has knowledge of the current project state.
2.  **Is the partial file checkout valid?** This is a significant concern (see section 2.1). It creates an artificial codebase state and threatens internal validity.
3.  **Is the scoring rubric granular enough?** The three levels are adequate, but the boundary between "direct hit" and "adjacent" could be clarified with more examples to ensure high inter-rater reliability (see section 3.1).
4.  **Is the "no playbook" baseline sufficient as a control?** It's a good start. For a top-tier publication, adding a "human baseline" (showing the defects to junior and senior developers) would provide a very powerful comparison point, though it is much more expensive to run.
5.  **Is the train/holdout split (60/40) appropriate?** Yes, 60/40 is a standard and reasonable split for this kind of validation work. K-fold cross-validation would be more robust but also more computationally expensive. The current approach is a pragmatic choice.
6.  **Are the threats to validity complete?** They are very thorough. One could be added under Internal Validity: **Tool/Model Drift**. The performance of the underlying LLM can change over time, even for the same model tag. A run performed in March might not be comparable to one in September. Mitigation: Record the full model response headers or API version identifiers if available.
7.  **Is the file-scoping limitation adequately addressed?** Acknowledging it is the minimum bar. The methodology would be much stronger if it quantified the effect of this hint by running a subset of defects without it (see section 2.2).
8.  **Is the statistical framework appropriate?** Yes, the choices of Wilson intervals over Wald and McNemar's test for paired comparisons are correct and show statistical maturity.
9.  **Are there comparable benchmarks or related work we should cite?** The methodology correctly identifies mutation testing and static analysis as related fields. Other relevant areas include work on automated program repair (APR) and AI for software engineering (AI-SE) benchmarks like HumanEval or MBPP, although QPB's focus on real historical bugs is a key differentiator.
10. **Would this methodology survive peer review at a top SE venue (ICSE, FSE, ASE, TSE)?** Yes, with the concerns about the hybrid git state and file scoping addressed. The overall rigor, documentation, and statistical framework are high quality and align with the expectations of top-tier software engineering venues.