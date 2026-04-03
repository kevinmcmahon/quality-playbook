# Council of Three Re-Review: QPB Evaluation Methodology
**Reviewer**: GitHub Copilot
**Date**: 2026-03-30
**Subject**: QPB Evaluation Methodology (post-update)

This is a re-review of the QPB evaluation methodology, following updates made to address the findings from the initial review on 2026-03-30.

---

## Summary of Changes

The updated methodology document (`dataset/METHODOLOGY.md`, changelog date 2026-03-30 "Council of Three revision") has successfully addressed all major concerns raised in the previous review. The changes are substantial and significantly strengthen the protocol for academic publication.

Key improvements noted:

1.  **Elimination of Hybrid Git State**: The protocol now correctly specifies a full checkout of the `pre_fix_commit` for both Phase 1 and Phase 2. This removes the artificial git state and ensures the evaluation is performed on a real, historically accurate version of the codebase. This was the most significant concern, and it has been fully resolved.

2.  **Matched Control Conditions**: The addition of context-matched and budget-matched baselines is a major improvement. This allows for a much more rigorous analysis that can isolate the specific contribution of the playbook's *structure* from the confounding factors of having more context or a larger token budget. This directly addresses the "Playbook vs. model vs. scaffolding" construct validity threat.

3.  **Quantification of File-Scoping Hint**: The addition of an "Unscoped Review" ablation is an excellent way to measure the effect of providing the agent with the file list. This turns a limitation into a measurable variable.

4.  **Rigor in Statistical Analysis and Reporting**: The methodology now includes guidance for mixed-effects models to handle clustering, bootstrap CIs for robustness, and post-stratification weighting. This demonstrates a sophisticated understanding of the statistical challenges.

5.  **Improved Scoring and Reliability Measures**: The addition of a "Scoring Handbook" with worked examples and the requirement for scorers to be blinded to the experimental condition will significantly improve inter-rater reliability and reduce bias.

6.  **Addressing Model-Specific Threats**: The new sections on "Model training-data leakage" and "Tool/model drift" are critical additions that acknowledge the unique challenges of evaluating LLMs. The proposed mitigations are appropriate and necessary.

7.  **Improved Terminology**: Renaming "false positive rate" to "novel findings rate" is more accurate and avoids mischaracterizing potentially valuable new discoveries.

---

## 1. Fatal Flaws

None. The methodology is now exceptionally strong.

---

## 2. Significant Concerns

None remain. The previous significant concerns regarding the hybrid git state and file-scoping hint have been effectively addressed through protocol changes and the addition of a specific ablation study.

---

## 3. Minor Suggestions

The methodology is now very comprehensive. The following are minor points for consideration:

-   **Practicality of Per-Defect Phase 1**: The document states that "Phase 1 runs approximately once per defect." Given the cost and time of running Phase 1, it might be worth exploring batching defects that are close in the commit history (e.g., within a certain number of commits or days) to share a single Phase 1 context. This is a minor optimization and does not affect the validity of the current protocol. The current approach is more correct, just more expensive.
-   **Human Baseline**: The previous review mentioned a "human baseline" as a powerful but expensive addition. While not a flaw, it's worth keeping in mind for future work or as a discussion point in the paper's "Future Work" section. Comparing the playbook's performance to that of junior and senior human reviewers would provide invaluable context.

---

## 4. What Works Well

The methodology has been elevated from good to excellent. The following aspects are particularly strong and publication-ready:

-   **Experimental Design**: The use of matched controls and specific ablations provides a robust framework for making causal claims about the playbook's effectiveness.
-   **Threats to Validity**: The "Threats to Validity" section is now comprehensive, nuanced, and directly addresses the most challenging aspects of evaluating LLM-based systems, including data contamination and model drift. The mitigations are practical and well-reasoned.
-   **Reproducibility**: The detailed logging requirements, including full inference parameters and prompt hashing, set a high standard for reproducibility.
-   **Improvement Loop**: The protocol for iterating on the playbook, which now includes re-running the *full* training set to check for regressions, is methodologically sound and guards against overfitting.
-   **Positioning**: The new "Related Work" section correctly and clearly positions QPB within the existing landscape of software engineering benchmarks, highlighting its unique contributions.

---

## Conclusion

The updated methodology is outstanding. It is rigorous, comprehensive, and demonstrates a deep understanding of the challenges of empirical software engineering and LLM evaluation. The changes made in response to the initial council review have been thorough and effective. The protocol is now in excellent shape for a top-tier academic publication.