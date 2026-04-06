# Council Review: QPB Evaluation Methodology (Rerun)

**Reviewer**: Cursor  
**Date**: 2026-03-30  
**Overall assessment**: This revision is substantially stronger. The prior fatal issues around `HEAD` contamination, hybrid checkouts, underspecified controls, missing training-data leakage discussion, and vague scoring boundaries have been addressed well enough that I would no longer block the evaluation on those grounds. What remains are a few important design and documentation gaps that should be cleaned up before treating the protocol as publication-ready.

## Fatal flaws

### None identified in the revised methodology

The major threats I flagged in the previous review have been addressed credibly:

- Phase 1 now runs at `pre_fix_commit`, which removes the strongest contamination path.
- Phase 2 now uses a full historical checkout instead of a hybrid file-level checkout.
- The control section now includes matched baselines that can support a causal claim much better than the earlier "no playbook" prompt alone.
- Training-data leakage is now treated as a first-class threat.

I do not currently see a methodology-level flaw that would, by itself, force rejection if the paper is otherwise executed carefully and reported honestly.

## Significant concerns

### 1. Cross-condition contamination/isolation is still underspecified

**Problem**: The methodology says to randomize condition order per defect, but it does not explicitly require that each condition run in a fresh, isolated session with no retained conversational or tool-state memory. If the same agent/session reviews the same defect under multiple conditions, later conditions can inherit knowledge from earlier ones.

**Why it matters**: This directly threatens the validity of treatment-vs-control comparisons. Randomizing order helps with bias, but it does not eliminate state leakage.

**Concrete fix**: Require each `(defect, condition, replicate)` evaluation to run in a fresh process/session with no retained chat history, cached summaries, or tool state from other conditions. Log a session identifier and state explicitly that cross-condition memory carryover is prohibited.

### 2. The power analysis still targets a single proportion, not the paired comparison

**Problem**: The sample-size guidance is still framed around estimating a 75% detection rate with a desired confidence interval width. But the main scientific question is comparative: does the playbook outperform the matched control? That is a paired-comparison power problem, not just a one-proportion estimation problem.

**Why it matters**: The study could be adequately powered to estimate a detection rate but underpowered to detect the treatment effect against the context-matched baseline, especially if the effect size is modest.

**Concrete fix**: Add a comparison-oriented power section based on McNemar's test or on the mixed-effects model target effect size. Even a rough planning table for small/medium/large effect sizes would make the design more defensible.

### 3. Supporting documents are now out of sync with the revised methodology

**Problem**: `dataset/DETECTION_RESULTS.md` still describes `False positive` rather than `Novel findings`, and its improvement-tracking section still says to re-run missed defects rather than the full training set. The run templates also do not reflect the new control conditions and expanded inference metadata.

**Why it matters**: Reviewers care about consistency across the protocol, score sheet, and reporting template. Misaligned artifacts create avoidable confusion and increase the chance that the study is executed inconsistently.

**Concrete fix**: Update `dataset/DETECTION_RESULTS.md` so its terminology, rerun policy, and run templates match `dataset/METHODOLOGY.md` exactly.

### 4. The reproducibility path layout still assumes Phase 1 is per-repo, not per `(repo, pre_fix_commit)`

**Problem**: The methodology correctly changes Phase 1 to run per `(repository, pre_fix_commit)` pair, but the run directory example still stores contexts as `runs/<run_id>/contexts/<repo>.md`. That naming will collide when one repository contributes many pre-fix commits.

**Why it matters**: This is a concrete reproducibility bug. If implemented literally, later contexts can overwrite earlier ones or make it unclear which historical state a context artifact belongs to.

**Concrete fix**: Rename the artifact path to include the commit, for example `runs/<run_id>/contexts/<repo>--<pre_fix_commit>.md`, and mirror that in any token/timing sidecar files.

### 5. File scoping is better framed now, but the task claim still needs discipline in the paper

**Problem**: The methodology now explicitly frames the target task as reviewing a candidate scope and adds an unscoped ablation, which is good. But this still gives the treatment and controls a strong oracle-derived narrowing of the search space.

**Why it matters**: If the paper slides back into broader language like "AI code review bug finding," reviewers will object that the evaluation is really "bug finding within an oracle-derived candidate scope."

**Concrete fix**: Keep the narrower claim everywhere: abstract, introduction, method, and discussion. If feasible, report scoped and unscoped numbers side by side in the main results rather than burying unscoped review as a minor ablation.

## Minor suggestions

### 1. Clarify whether Phase 1 artifacts are shared across conditions

This is implied for the context-matched baseline, but I would state it explicitly: the exact same Phase 1 artifact should be reused across treatment and context-matched control for a given defect.

### 2. Add explicit retry/timeout policy fields to the logging table

The text mentions retry/timeout policies in threats to validity, but the structured logging table does not list them as fields. I would add them to avoid ambiguity.

### 3. Expand scorer guidance for novel findings

You now distinguish `novel findings` from scored outcomes, which is the right move. It would help to add one short rule for how scorers should annotate a novel finding when it co-occurs with a direct hit or adjacent finding in the same review.

### 4. Consider a lightweight execution-order safeguard

Even with isolated sessions, order can matter if shared infrastructure caches code indexes or repository state. A sentence requiring condition runs to start from a clean checkout and fresh agent state would make this clearer.

## What works well

### 1. The methodology responded directly to the earlier council feedback

This revision fixes the biggest design problems rather than papering over them. The changelog is specific, and the revisions line up with the actual concerns.

### 2. The control design is now much more credible

Adding context-matched and budget-matched baselines materially improves the ability to argue that any gain comes from the playbook rather than extra scaffolding or budget.

### 3. The scoring section is much stronger

The worked examples, borderline cases, and blinded inter-rater requirement make the rubric considerably more publication-ready.

### 4. The threats-to-validity section is now robust

The additions on training-data leakage, model/tool drift, scorer blinding, and file-scope oracle hints show the right level of skepticism for an AI-for-SE benchmark paper.

### 5. The paper positioning is clearer

The new related-work section does a good job distinguishing QPB from Defects4J-style repair benchmarks, SWE-bench, mutation testing, and static-analysis evaluation.

## Answers to the specific questions

### 1. Is the Phase 1 / Phase 2 separation sound?

Yes, now that both phases run at `pre_fix_commit`. The optional `HEAD` ablation is correctly demoted to secondary analysis.

### 2. Is the partial file checkout valid?

This issue is resolved. The full-tree historical checkout is the right fix.

### 3. Is the scoring rubric granular enough?

Yes, with the new handbook and blinded double-scoring requirement. I would still expect some direct-vs-adjacent disagreement, but no longer at a level that threatens the study.

### 4. Is the "no playbook" baseline sufficient?

As an optional floor only. The new matched controls are the important improvement and are much more appropriate for causal claims.

### 5. Is the train/holdout split appropriate? Should you use k-fold CV?

The current approach is fine. The added second-seed replication is a good compromise between rigor and cost. I still would not require full k-fold here.

### 6. Are the threats to validity complete?

Mostly yes now. The main thing I would still tighten is explicit session isolation across conditions, which currently sits more as an implicit execution assumption than a named threat/control.

### 7. Is the file-scoping limitation adequately addressed?

Much better than before. It is acceptable if the paper consistently makes the narrower scoped-review claim and reports the unscoped ablation clearly.

### 8. Is the statistical framework appropriate?

Yes as a strong draft. The main missing piece is explicit power planning for the paired treatment-vs-control comparison.

### 9. Are there comparable benchmarks or related work to cite?

Yes, and the new section covers the important ones well. I would keep Defects4J, Bears, Bugs.jar, SWE-bench, mutation testing, and code-review literature in the final paper.

### 10. Would this survive peer review at a top SE venue?

Potentially yes, if executed carefully and reported conservatively. The revised methodology is now in plausible ICSE/FSE/ASE/TSE territory, but I would still clean up the session-isolation rule, paired-power planning, and the supporting-doc inconsistencies before calling it final.
