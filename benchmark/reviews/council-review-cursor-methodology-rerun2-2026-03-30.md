# Council Review: QPB Evaluation Methodology (Rerun 2)

**Reviewer**: Cursor  
**Date**: 2026-03-30  
**Overall assessment**: This revision is more operationally realistic, but it regresses on methodological rigor in a few important ways. In particular, it reintroduces post-fix contamination through HEAD-generated quality infrastructure and drops the matched-control design that was previously needed to support the stated research question. As written, this version is better suited to an internal playbook-improvement workflow paper than to a strong causal evaluation of whether structured playbook guidance improves bug detection.

## Fatal flaws

### 1. The methodology no longer matches the stated research question

**Problem**: The review brief still frames the key question as: "Does structured playbook guidance improve AI code review detection rates compared to unstructured prompts?" But the revised methodology no longer includes matched control conditions or any unstructured baseline in the main experiment. Instead, it evaluates iterative playbook improvement and then compares the original playbook to the improved playbook on held-out repos.

**Why it matters**: This is a construct-validity failure. The current protocol can answer "did the revised playbook outperform the original playbook on held-out repos under this workflow?" It cannot answer the broader causal question about structured guidance versus unstructured review. A paper reviewer will notice that the method does not identify the effect named in the introduction.

**Concrete fix**: Choose one of two paths and make the paper consistent:

1. Restore matched controls if the paper's main claim remains "structured guidance improves detection versus unstructured prompts."
2. Narrow the paper claim to "iterative improvement of a structured playbook improves held-out benchmark performance versus its original version."

Right now the methodology and the claim are pointing at different targets.

### 2. HEAD-generated quality infrastructure reintroduces strong post-fix contamination

**Problem**: Step 1 explicitly generates `quality/` artifacts and `AGENTS.md` at repo `HEAD`, then Step 2 reviews historical pre-fix code while keeping that untracked quality infrastructure in place. But the playbook's generation phase reads current tests, docs, defensive patterns, schema definitions, and architecture. Those artifacts can encode information introduced by later fixes, including the very defects under evaluation.

**Why it matters**: This is not minor background context leakage. The generated quality infrastructure can directly carry post-fix knowledge into the historical review condition. That weakens internal validity on both improvement and held-out repos. Saying the before/after comparison "controls for it" helps only for comparing two playbook versions under the same contaminated setup; it does not support claims about historical defect-detection ability.

**Concrete fix**: Generate quality infrastructure from the `pre_fix_commit` or from a contamination-safe historical snapshot for the relevant defect. If that is operationally too expensive, explicitly downgrade the claim to "performance in a retrospective review workflow with modern project context," and present contamination as a major limitation rather than an acceptable property.

### 3. The held-out before/after comparison still lacks isolation from workflow confounds

**Problem**: The methodology says the playbook version is the independent variable, but it does not require fresh isolated sessions, does not specify whether the same agent instance is reused across before/after runs, and does not control for order effects beyond stating the same prompts are used. Because the improved playbook is applied after a long iterative campaign, the evaluation environment may have drifted in practice.

**Why it matters**: Without strict session isolation and stable execution conditions, improvements could be partly attributable to run-order effects, agent memory, or infrastructure drift rather than the playbook text alone.

**Concrete fix**: Require each held-out `(repo, defect, version)` run to execute in a fresh isolated session with no retained conversation state, clean checkout state, and fixed model/tool version. Randomize before/after order if feasible, or at minimum run both versions in temporally adjacent fresh sessions.

## Significant concerns

### 1. The repository-level split is sensible, but the statistical plan is now too thin

**Problem**: The previous version had stronger analysis guidance around clustering and weighted analysis. This revision reduces the statistical plan to basic rates and McNemar's test for before/after validation, even though defects remain clustered within repositories and the unit of holdout is repo-level.

**Why it matters**: Uncertainty may be understated, especially if a few held-out repos dominate the defect count or respond unusually well to the revised playbook.

**Concrete fix**: Restore a clustered analysis plan. At minimum, report repo-level bootstrap confidence intervals or a mixed-effects model with repository as a random effect alongside pooled rates.

### 2. The power/sample-size story is now underspecified

**Problem**: The earlier methodology gave at least rough sample-size guidance. This version no longer defines how many held-out repos or defects are needed to support the before/after comparison with reasonable power.

**Why it matters**: A nontrivial before/after experiment can easily end up underpowered, especially if improvement is modest and repo-level heterogeneity is high.

**Concrete fix**: Add planning guidance for the held-out validation set: target number of repos, target number of defects, and a rough power rationale for the paired comparison.

### 3. The file-scoping oracle hint is still present without an ablation

**Problem**: The methodology continues to tell the agent exactly which files to review, but the previous unscoped-ablation idea is gone.

**Why it matters**: This keeps the benchmark in a narrow "candidate review scope" setting while removing the empirical way to quantify how much that hint inflates results.

**Concrete fix**: Restore the unscoped or broader-scope ablation on a subset of held-out repos, or make the narrow scoped-review claim extremely explicit throughout the paper.

### 4. `DETECTION_RESULTS.md` is still out of sync with the revised methodology

**Problem**: The reporting schema still uses `False positive`, still assumes the older run template, and still says improvement re-tests re-run missed defects only. That does not match the current methodology's `Novel findings` language or full-repo rerun workflow.

**Why it matters**: Inconsistent artifacts create execution drift and make the benchmark harder to reproduce cleanly.

**Concrete fix**: Update `dataset/DETECTION_RESULTS.md` to match the current methodology exactly.

### 5. The reproducibility/logging requirements have been simplified too far

**Problem**: The new logging table drops several fields that materially affect LLM evaluation: system prompt/tool wrapper, retry policy, timeout policy, model snapshot/version details where available, and session identifiers.

**Why it matters**: This makes later replication and adjudication harder, especially if tool behavior changes over time.

**Concrete fix**: Keep the simplified fields that are actually available, but add as much execution metadata as the tools expose, especially session isolation metadata and full prompt capture.

## Minor suggestions

### 1. Clarify whether `AGENTS.md` generated at HEAD is also retained during pre-fix review

The text implies yes, but spell it out. That matters because `AGENTS.md` can itself encode post-fix guidance.

### 2. Add scorer blinding back explicitly

The current text requires inter-rater reliability but no longer explicitly says scorers should be blinded to whether a finding came from the original or improved playbook.

### 3. Define what counts as a "material" increase in novel findings

The stopping criterion currently says "increases materially" without a numeric threshold. That invites post hoc judgment.

### 4. Clarify whether improvement-repo order is fixed in advance

The methodology says to record the order, but not to commit to it before results are known. Precommitting to an order would strengthen credibility.

## What works well

### 1. The workflow now resembles how the playbook is actually used

Generating quality infrastructure once and then using it to review defects is operationally realistic and easier to explain to practitioners.

### 2. The repository-level holdout idea is stronger than a defect-level holdout for this use case

Holding out entire repos is a good way to test whether playbook improvements generalize to unseen codebases rather than just unseen defects in familiar repos.

### 3. The scoring rubric remains solid

The direct/adjacent/miss/not-evaluable framework plus the worked examples is still a good foundation.

### 4. The abstraction-level validation and council gate remain strong

Those sections continue to do good work in guarding against overfitting and overly specific playbook edits.

## Answers to the specific questions

### 1. Is the Phase 1 / Phase 2 separation sound?

No, not in this version. The contamination issue is back in a new form because quality infrastructure is generated at `HEAD` and then reused while reviewing pre-fix code.

### 2. Is the partial file checkout valid?

That specific hybrid-checkout issue is gone, which is good. The repo is now at a real pre-fix state during review. But the retained HEAD-generated artifacts still create a different form of historical contamination.

### 3. Is the scoring rubric granular enough?

Yes. The rubric is no longer the weak point.

### 4. Is the "no playbook" baseline sufficient?

The bigger issue is that there is no real baseline in the current main design. If the paper still wants a structured-vs-unstructured claim, matched controls need to come back.

### 5. Is the train/holdout split (60/40) appropriate? Should we use k-fold cross-validation instead?

This question is partly obsolete for the new repo-level design. The bigger need now is clear held-out repo sizing and a fixed split/order policy. I would still not require full k-fold, but I would want a better-powered repo-level holdout plan.

### 6. Are the threats to validity complete?

Not fully. The biggest missing emphasis is that the quality infrastructure itself is a contamination vector because it is generated from post-fix code at `HEAD`.

### 7. Is the file-scoping limitation adequately addressed?

No. It is acknowledged implicitly by the prompt design, but without an ablation or a tighter claim, it remains a material limitation.

### 8. Is the statistical framework appropriate?

Not yet. It is now too lightweight for a top-venue paper because it dropped clustering and power-planning guidance.

### 9. Are there comparable benchmarks or related work we should cite?

Yes, and the current related-work section is still directionally right: Defects4J, Bears, Bugs.jar, SWE-bench, mutation testing, static-analysis evaluation, and code-review literature should stay.

### 10. Would this methodology survive peer review at a top SE venue?

Not in its current form if the paper keeps the broader causal claim. It could survive as a paper about iterative playbook improvement on a historical-bug benchmark, but only if the claim is narrowed and the contamination from HEAD-generated quality artifacts is treated much more carefully.
