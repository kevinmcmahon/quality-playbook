# Council of Three Review: QPB Evaluation Methodology

## Instructions

You are one member of a Council of Three reviewing the evaluation methodology for the **Quality Playbook Benchmark (QPB)** — a benchmark that measures how well AI-assisted code review playbooks detect real bugs in open-source codebases. This methodology will be used in an academic paper.

**Start by reading these files in order:**

1. `dataset/METHODOLOGY.md` — The full evaluation protocol, statistical framework, improvement iteration rules (including abstraction level validation and Council of Three review gate), reproducibility requirements, and threats to validity
2. `playbook/SKILL.md` — The actual quality playbook under test (v1.2.0). This is the intervention being evaluated. Read Phase 1 (Steps 0–4b) and Phase 2 (Steps 5, 5a, 5b, 6) to understand what the playbook instructs the agent to do.
3. `playbook/references/defensive_patterns.md` — The reference document for Step 5 (defensive pattern analysis). This is where proposed improvements would land.
4. `dataset/DEFECT_LIBRARY.md` — Skim the first 50–100 entries to understand the defect format, categories, and severity distribution
5. `dataset/DETECTION_RESULTS.md` — The scoring rubric schema and cross-model comparison framework
6. `dataset/defects/cli/defects.md` and `dataset/defects/curl/defects.md` — Sample per-repo description files to see the detailed defect format

**Then review the methodology for problems, gaps, and weaknesses.**

**Save your review to:** `reviews/council-review-{your-tool}-methodology-{YYYY-MM-DD}.md`
(e.g., `reviews/council-review-cursor-methodology-2026-03-31.md`)

### Guardrails

This is a **read-only review task**. You must:

- **ONLY create one file**: your review output in `reviews/` using the naming convention above
- **DO NOT modify** any existing files in this repository (no edits to METHODOLOGY.md, SKILL.md, playbook references, defect files, or anything else)
- **DO NOT create** any files outside the `reviews/` directory
- **DO NOT create** directories, scripts, notebooks, or any other artifacts
- If you find issues, describe them in your review — do not attempt to fix them

Your sole deliverable is a single markdown file in `reviews/`.

---

## Context

The QPB contains 2,564 real defects from 50 open-source repos across 14 languages. Each defect is a single fix commit with a known parent commit. The key research question: **Does structured playbook guidance improve AI code review detection rates compared to unstructured prompts?**

The playbook under test (`awesome-copilot/skills/quality-playbook/SKILL.md` — not in this repo, but referenced) has two phases: exploration (understand the codebase) and review (hunt for bugs using defensive patterns, state machine tracing, schema mapping, and domain knowledge).

We ran an initial pilot of 16 defects and found that the playbook v1.2.0 achieves a 75% direct hit rate. Three misses led to proposed playbook improvements (to be applied as edits to the playbook files in `playbook/`). The methodology document (`dataset/METHODOLOGY.md`) defines how to run the full evaluation rigorously enough for publication.

---

## Your Review

**Organize your findings into these sections:**

1. **Fatal flaws** — Issues that would cause a paper reviewer to reject. Must be fixed before running the evaluation.
2. **Significant concerns** — Weaken the paper's claims but don't invalidate them. Should be addressed or explicitly acknowledged.
3. **Minor suggestions** — Improvements to clarity, completeness, or rigor.
4. **What works well** — Aspects that are strong and should be preserved.

**Be specific.** For each issue: (a) what the problem is, (b) why it matters for publication, (c) a concrete fix.

---

## Specific Questions

In addition to your general review, consider:

1. **Is the Phase 1/Phase 2 separation sound?** Phase 1 runs at repo HEAD (which includes fix commits). Is the contamination control argument in METHODOLOGY.md convincing?

2. **Is the partial file checkout valid?** We check out only the files changed by the fix commit, not the whole repo at the pre-fix commit. This preserves Phase 1 context but creates a hybrid git state. Does this introduce artifacts?

3. **Is the scoring rubric granular enough?** Three levels (direct hit / adjacent / miss) plus not-evaluable. Is the boundary between direct hit and adjacent clear enough for inter-rater agreement?

4. **Is the "no playbook" baseline sufficient as a control?** Or do we need additional controls (different model, different playbook, human reviewers)?

5. **Is the train/holdout split (60/40) appropriate?** Should we use k-fold cross-validation instead?

6. **Are the threats to validity complete?** Are there threats we haven't identified?

7. **Is the file-scoping limitation adequately addressed?** Telling the agent exactly which files to review is a significant hint. Is acknowledging it sufficient, or does it need stronger mitigation?

8. **Is the statistical framework appropriate?** Wilson intervals, McNemar's test, stratified sampling — are there better choices?

9. **Are there comparable benchmarks or related work we should cite?** This approach (real historical bugs as oracles for evaluating code review tools) may have precedent in the mutation testing, static analysis, or AI-for-SE literature.

10. **Would this methodology survive peer review at a top SE venue (ICSE, FSE, ASE, TSE)?** What's missing?
