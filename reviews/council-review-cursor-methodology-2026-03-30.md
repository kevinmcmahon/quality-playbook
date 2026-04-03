# Council Review: QPB Evaluation Methodology

**Reviewer**: Cursor  
**Date**: 2026-03-30  
**Overall assessment**: Promising benchmark idea, strong artifact discipline, and a thoughtful iteration loop. However, in its current form I do **not** think the methodology would survive peer review at a top SE venue. The main problems are contamination, an invalid hybrid checkout condition, and an underspecified control. Those need to be fixed before the evaluation is run for publication claims.

## Fatal flaws

### 1. Phase 1 contamination is more serious than the methodology claims

**Problem**: `dataset/METHODOLOGY.md` argues that Phase 1 at repo `HEAD` is acceptable because it only provides general architecture and domain knowledge. But the actual playbook in `playbook/SKILL.md` makes Phase 1 much richer than that: it explicitly reads existing tests, specifications, function signatures, real data, and defensive patterns. At `HEAD`, those artifacts may already include the exact fix-added tests, new guards, new fields, clarified docs, or comments that were introduced by the fix commit. That is not just background knowledge. It is post-fix information leakage.

**Why it matters**: This directly threatens internal validity. A reviewer can reasonably say the playbook is being helped by future information that would not have existed at review time. For some defects, the leaked information may all but reveal the missing behavior.

**Concrete fix**: Make the primary published protocol contamination-free. The cleanest option is to run both Phase 1 and Phase 2 on a full checkout of the `pre_fix_commit`. If preserving a more modern architectural view is important, run the current `HEAD`-based Phase 1 only as a secondary ablation and report how much it changes detection rates.

### 2. The partial file checkout creates an invalid evaluation state

**Problem**: Phase 2 checks out only the files changed by the fix commit while leaving the rest of the repository at `HEAD`. This creates a hybrid codebase that never existed historically. A pre-fix file can now be surrounded by post-fix tests, helpers, configs, type definitions, and neighboring modules.

**Why it matters**: The benchmark stops measuring performance on a real historical defect and starts measuring performance on an artificial mixed revision. That can both hide bugs and create bugs. It also makes replication conceptually messy: the evaluated unit is no longer a real commit.

**Concrete fix**: Use a full-tree checkout of the `pre_fix_commit` as the primary evaluation condition. If the hybrid condition is kept, label it explicitly as an experimental ablation, not the main methodology.

### 3. The control condition is not strong enough to support the paper's core causal claim

**Problem**: The methodology proposes a "no playbook" baseline, but it does not define a matched control. As written, the playbook condition receives a structured Phase 1 artifact, stepwise instructions, extra search structure, and likely a larger effective token/time budget. A generic "find bugs in this code" prompt is not a causal control for "playbook guidance."

**Why it matters**: Without a matched control, any observed gain can be attributed to more context, more time, or more scaffolding rather than to the playbook itself. That weakens the central research claim.

**Concrete fix**: Pre-register at least two matched baselines:

1. **Context-matched baseline**: same Phase 1 artifact, same files, same token/time budget, but no playbook instructions.
2. **Budget-matched baseline**: same total budget and tool permissions, but an unstructured generic review prompt.

Optionally add a third baseline using a lightweight checklist to separate "any structure helps" from "this playbook helps."

### 4. The methodology is missing an explicit treatment of model training-data leakage

**Problem**: QPB uses public open-source repositories and historical fixes. Current frontier models may have been trained on some of the same repositories, issue discussions, tests, or even exact fix commits. The threats-to-validity section does not discuss this.

**Why it matters**: Peer reviewers in AI-for-SE will ask this immediately. If a model has memorized parts of the repo, the measured "bug detection" rate may partly reflect prior exposure rather than review skill induced by the playbook.

**Concrete fix**: Add this as a first-class threat and mitigate it where possible. Good options are: sample a recent post-cutoff subset, report results separately for newer vs older defects, exclude heavily benchmarked repos in a sensitivity analysis, and clearly limit the claim from "general code review ability" to "performance on this public historical-bug benchmark."

## Significant concerns

### 1. The exact-file review scope is a strong oracle hint

**Problem**: The agent is told exactly which files changed in the eventual fix commit. That is privileged information from the oracle. Even without the diff, it narrows the search space dramatically.

**Why it matters**: This likely inflates detection rates relative to a more realistic bug-finding setting. A reviewer may accept this as a changed-files code review scenario, but then the paper must make that narrow claim explicitly.

**Concrete fix**: Reframe this as "reviewing the files in a candidate change scope," not general bug finding. Better yet, add an ablation comparing exact-file scope to a broader module-level or subsystem-level scope.

### 2. The direct-hit vs adjacent boundary is still too subjective

**Problem**: The rubric is sensible, but the operational boundary between `direct_hit` and `adjacent` is still fuzzy. "Would know exactly what to fix" leaves room for scorer interpretation, especially for multi-file bugs or findings that identify the right invariant but not the exact line.

**Why it matters**: Inter-rater reliability may end up lower than expected, which weakens claims of measurement rigor.

**Concrete fix**: Add an adjudication guide with 10-20 scored examples spanning all four outcomes, especially borderline direct/adjacent cases. Blind scorers to condition when possible, double-score a meaningful sample, and predefine how disagreements are resolved.

### 3. The statistical plan is good descriptively but thin for clustered data

**Problem**: Wilson intervals and McNemar's test are reasonable starting points, but defects are clustered within repositories, languages, and categories. Also, the proposed stratified sampling includes minimum-per-language and minimum-per-repo constraints that can distort prevalence if the analysis does not weight back to the population.

**Why it matters**: Reported uncertainty may be too optimistic, and aggregate rates may not estimate the full benchmark distribution cleanly.

**Concrete fix**: Keep Wilson intervals for simple descriptive reporting, but add either post-stratification weighting plus bootstrap confidence intervals, or a mixed-effects logistic model for the main comparisons. If using the minimum-per-stratum rule, explicitly describe how estimates are reweighted back to the 2,564-defect population.

### 4. The improvement loop only re-runs misses

**Problem**: Re-running only the misses is efficient, but it hides regressions. A playbook change can convert some misses to hits while also turning some previous hits into misses or increasing noise.

**Why it matters**: That makes the iteration loop look more favorable than it really is.

**Concrete fix**: After each accepted change, re-run the full training subset or at least a stable sentinel panel containing prior hits, adjacents, and misses. Track both gains and regressions.

### 5. Reproducibility metadata is still missing key generation parameters

**Problem**: The methodology logs many useful artifacts, but it does not explicitly require temperature, seed when available, top-p, max output tokens, retry behavior, timeout policy, tool permissions, or the exact system prompt/tool wrapper.

**Why it matters**: For LLM evaluations, these details can move results materially.

**Concrete fix**: Extend `metadata.json` with full inference configuration and execution environment metadata, including model snapshot/version date and tool settings.

### 6. The 60/40 train-holdout split is defensible, but one split is fragile

**Problem**: A single stratified 60/40 split can be noisy, especially when some categories are sparse.

**Why it matters**: The measured improvement after iteration may depend too much on one random partition.

**Concrete fix**: I would not insist on full k-fold cross-validation here because of cost, but I would recommend repeated stratified splits with fixed seeds, or one frozen dev/test split plus one confirmatory replication split.

## Minor suggestions

### 1. Add explicit related-work positioning

**Problem**: The methodology explains the intuition well, but it does not situate QPB clearly against existing SE benchmarks.

**Why it matters**: Reviewers will want to know what is genuinely new.

**Concrete fix**: Add a related-work section that positions QPB against:

- **Defects4J**, **Bears**, and **Bugs.jar** as prior real-bug benchmarks.
- **SWE-bench** as an LLM-oriented benchmark for issue resolution rather than blind review.
- Mutation-testing literature as the closest conceptual ancestor, while stressing that QPB uses historical defects instead of injected mutants.

### 2. Clarify what the primary claim is

**Problem**: Parts of the document read like a benchmark for general bug finding; other parts read like a benchmark for reviewing a known changed scope.

**Why it matters**: Ambiguous claims invite reviewer pushback.

**Concrete fix**: State the target task precisely in one sentence near the top, e.g. "QPB evaluates how well a review protocol finds known defects when pointed at a candidate review scope derived from the eventual fix."

### 3. Tighten not-evaluable handling

**Problem**: `not_evaluable` is defined, but the downstream analysis plan for high non-evaluable rates is not.

**Why it matters**: A model/tool combination could look better simply by failing on hard cases.

**Concrete fix**: Report not-evaluable rate separately by repo/category/model, and predefine exclusion thresholds or fallback retry rules.

### 4. Add scorer blinding language

**Problem**: The document discusses scorer bias, but not whether scorers know which condition produced the output.

**Why it matters**: Knowing "this was the playbook run" can bias borderline calls upward.

**Concrete fix**: Blind scorers to condition and model wherever possible during adjudication.

## What works well

### 1. The benchmark idea is genuinely useful

Using real historical defects as the oracle is much more compelling than synthetic bug injection for this use case. It anchors evaluation in defects that actually fooled real developers and were actually fixed.

### 2. The artifact and logging discipline is strong

The run directory structure, prompt logging, raw findings retention, context hashing, and sampling records are all exactly the kinds of artifacts reviewers want to see.

### 3. The methodology shows healthy skepticism about overfitting

The abstraction-level validation, Council of Three review gate, holdout requirement, and stopping criterion are strong design choices. They demonstrate awareness that prompt/playbook tuning can easily overfit the benchmark.

### 4. The threats-to-validity section is better than most early-stage benchmark docs

The document already identifies several real threats instead of pretending the setup is clean. That gives you a solid base to improve from.

## Answers to the specific questions

### 1. Is the Phase 1 / Phase 2 separation sound?

Not as currently implemented. The separation is conceptually reasonable, but running Phase 1 at `HEAD` is not convincing because the playbook's Phase 1 reads tests, specs, and defensive patterns, not just architecture. That is contamination unless you can show via ablation that it has negligible effect.

### 2. Is the partial file checkout valid?

No for the primary analysis. It is acceptable only as a secondary ablation. The main published evaluation should use a full historical checkout.

### 3. Is the scoring rubric granular enough?

Probably yes at a high level, but not yet operationalized enough for strong inter-rater agreement. Keep the four outcomes, but add a scoring handbook with worked examples.

### 4. Is the "no playbook" baseline sufficient?

No. You need matched controls. A single generic baseline will not isolate the effect of playbook guidance from the effects of context, budget, and scaffolding.

### 5. Is the 60/40 train-holdout split appropriate? Should you use k-fold CV?

60/40 is acceptable as an iteration workflow, but I would not rely on a single split for the paper's main conclusion. Repeated stratified splits are a better cost/rigor tradeoff than full k-fold here.

### 6. Are the threats to validity complete?

No. The biggest missing threat is model training-data leakage from public repositories and historical fixes. I would also add a threat around tooling variance: different IDE agents expose different search/read workflows that can materially affect results.

### 7. Is the file-scoping limitation adequately addressed?

Not yet. Merely acknowledging it is too weak if it remains the only evaluation condition. It needs either stronger mitigation or a narrower claim.

### 8. Is the statistical framework appropriate?

Reasonable as a first draft, but incomplete. Wilson intervals and McNemar are fine building blocks. Add clustered/weighted analysis or bootstrap-based uncertainty to account for the sampling design and repository clustering.

### 9. Are there comparable benchmarks or related work to cite?

Yes. At minimum cite Defects4J, Bears, Bugs.jar, SWE-bench, and mutation-testing literature. The paper should explicitly explain how QPB differs: blind review over historical defects rather than patch generation or synthetic mutant killing.

### 10. Would this survive peer review at ICSE / FSE / ASE / TSE?

Not yet. I think reviewers would like the idea and the care around artifacts, but the current methodology would draw major concerns about contamination, the hybrid checkout, and the underspecified control. Fix those, and this becomes much more publishable.
