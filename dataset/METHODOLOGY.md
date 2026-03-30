# Quality Playbook Benchmark (QPB) — Methodology

## Purpose

The QPB is a curated dataset of 2,564 real defects from 50 open-source repositories across 14 programming languages. Its purpose is to measure and improve the detection rate of AI-assisted code review playbooks by providing ground truth: known bugs at known commits with known fixes.

This is mutation testing applied one level up — instead of injecting synthetic faults into code, we use real historical bugs as the oracle. If a code review playbook can't find a bug that actually existed and was actually fixed, that's a true miss.

## Dataset Composition

- **2,564 defects** across **50 repositories** (55 prefixes including 5 original projects)
- **14 languages**: Java, Python, Go, TypeScript, Rust, Scala, C#, JavaScript, Ruby, PHP, Kotlin, C, Swift, Elixir
- **4 repo types**: Library, Framework, Application, Infrastructure
- **14 defect categories**: error handling, validation gap, configuration error, type safety, state machine gap, concurrency issue, serialization, API contract violation, protocol violation, null safety, silent failure, security issue, SQL error, missing boundary check

## How Defects Were Mined

For each repository:

1. **Clone the repo** with full history
2. **Scan git log** for commits whose messages indicate bug fixes (keywords: fix, bug, patch, resolve, repair, correct, handle, prevent, avoid, etc.)
3. **Examine the diff** of each fix commit to understand what was wrong in the pre-fix code
4. **Record**: fix commit SHA, pre-fix commit SHA (parent of fix), severity, category, one-line description, playbook detection angle
5. **Verify**: confirm the fix commit exists and the parent commit is its immediate ancestor (`git rev-parse FIX_COMMIT^`)

### Constraints

- **Every defect is tied to a single fix commit.** This ensures unambiguous traceability: checking out the pre-fix commit gives you the exact code with the exact bug, and the fix commit diff is the ground truth oracle.
- **Fix commits with multiple parents (merges) are excluded.** Only single-parent commits are included so the parent is unambiguous.
- **Categories are normalized to exactly 14 canonical labels.** Raw category strings from mining were mapped to canonical categories using keyword-based rules (see `normalize_categories.py`).

---

## Evaluation Protocol

This section defines the exact procedure for measuring a playbook's detection rate against the QPB. The protocol is designed for reproducibility: a different team running the same protocol should produce statistically comparable results.

### Overview

The evaluation has two phases per repository, then a scoring phase per defect:

1. **Phase 1 (Context Generation)**: Run the playbook's exploration steps at repo HEAD to build codebase understanding
2. **Phase 2 (Defect Review)**: For each defect, check out the pre-fix code and run the playbook's review steps against the affected files
3. **Scoring**: Compare each review's findings against the oracle (fix commit diff) using a three-level rubric

Phase 1 runs once per repository. Phase 2 runs once per defect. The two phases use different git states.

### Phase 1: Context Generation (Per Repository)

**Purpose**: Build the codebase context that the playbook's review steps depend on. This is the "understand the project" phase.

**Git state**: Repository HEAD (latest commit on the default branch).

**Procedure**:

```
cd repos/<repo>
git checkout HEAD          # or the default branch
```

Run the playbook's Phase 1 exploration steps (Steps 0–4b from SKILL.md):

| Step | What It Does | Output |
|------|-------------|--------|
| Step 0 | Check for development history / chat logs | Context notes |
| Step 1 | Identify domain, stack, specifications | Domain summary |
| Step 2 | Map architecture (subsystems, data flow) | Architecture map |
| Step 3 | Read existing tests (count, coverage, gaps) | Test inventory |
| Step 4 | Read specifications | Requirement catalog |
| Step 4b | Read function signatures and real data | Function call map |

**Output**: A context artifact (structured text) summarizing the codebase. This artifact is saved to a run log and provided to every Phase 2 review for this repository.

**Logging**: Record the full context artifact, the model used, token counts, and wall-clock time. The context artifact is an input to Phase 2 and must be reproducible — if the same model with the same prompt produces different context on two runs, that variance propagates to Phase 2 scores.

**Contamination control**: Phase 1 runs at HEAD, which includes the fix commits for every QPB defect. This means the Phase 1 context may include code that was added by a fix commit. This is acceptable because:
- Phase 1 is about understanding the codebase's architecture, domain, and conventions — not finding specific bugs
- A human reviewer doing a code review would also understand the project's current state before reviewing a specific change
- The pre-fix checkout in Phase 2 is what creates the evaluation condition; Phase 1 is background knowledge

However, the Phase 1 prompt must NOT reference any specific QPB defects, fix commits, or bug descriptions. It should be the same prompt you'd give for any code review engagement.

### Phase 2: Defect Review (Per Defect)

**Purpose**: Run the playbook's review steps against the pre-fix version of the files changed by a specific fix commit, with the Phase 1 context available.

**Git state**: Pre-fix commit for the affected files only.

**Procedure**:

```
cd repos/<repo>

# 1. Identify files changed by the fix commit
git diff-tree --no-commit-id --name-only -r <fix_commit>

# 2. Check out the pre-fix versions of ONLY those files
git checkout <pre_fix_commit> -- <file1> <file2> ...

# 3. Run the playbook review steps (5, 5a, 5b, 6) against those files
#    providing the Phase 1 context artifact as background

# 4. Restore the files to HEAD when done
git checkout HEAD -- <file1> <file2> ...
```

**Why checkout only the affected files, not the whole pre-fix commit?**
- Checking out the entire repo at the pre-fix commit would invalidate the Phase 1 context (which was generated at HEAD)
- In practice, a code reviewer reviews specific files, not the entire repo at a point in time
- Checking out only the affected files preserves the surrounding codebase context while presenting the reviewer with the buggy code

**What the Phase 2 agent receives**:
1. The Phase 1 context artifact (architecture map, test inventory, etc.)
2. The playbook's review instructions (Steps 5, 5a, 5b, 6, and the `references/defensive_patterns.md` content)
3. The file paths to review (from `git diff-tree`)
4. Access to read those files (which are now at their pre-fix versions)

**What the Phase 2 agent does NOT receive**:
- The defect ID, title, or description
- The fix commit SHA or diff
- The defect category or severity
- The playbook angle (which step should catch it)
- Any hint that there is a known bug in these files

**This is a blind review.** The agent believes it is doing a routine code review. If it finds the bug, that's a detection. If it doesn't, that's a miss.

**Logging**: For each defect review, record:

| Field | Description |
|-------|-------------|
| `run_id` | Unique identifier for this evaluation run |
| `defect_id` | QPB defect identifier (e.g., GH-03, CURL-02) |
| `repo` | Repository name |
| `playbook_version` | Playbook version being tested |
| `model` | Model identifier (e.g., claude-opus-4-6) |
| `timestamp` | ISO 8601 start time |
| `duration_ms` | Wall-clock duration of the review |
| `total_tokens` | Total tokens consumed (input + output) |
| `phase1_context_hash` | SHA-256 of the Phase 1 context artifact (for reproducibility tracking) |
| `files_reviewed` | List of file paths reviewed |
| `findings_raw` | Full text of the agent's findings (unedited) |
| `score` | direct_hit / adjacent / miss / not_evaluable |
| `score_evidence` | Brief explanation of why this score was assigned |
| `scorer` | Who scored it (human ID or "auto") |

All logs are appended to `runs/<run_id>/results.jsonl` (one JSON object per line, one line per defect).

### Scoring Rubric

Scoring compares the agent's raw findings against the oracle (fix commit diff).

| Score | Criteria | Example |
|-------|----------|---------|
| **Direct hit** | The findings name the specific bug, the specific code path, or describe the root cause such that a developer reading the findings would know exactly what to fix | "The `err =` on line 279 should be `err :=` to avoid sharing the outer-scope variable with the goroutine" |
| **Adjacent** | The findings flag the affected area, function, or a related concern, but don't identify the specific bug | "The goroutine in UpdatePortVisibility has potential concurrency issues" (without naming the specific variable scoping problem) |
| **Miss** | The findings don't mention the bug, the affected code area, or any related concern | Review discusses other files or other issues entirely |
| **Not evaluable** | The agent crashed, timed out, produced no output, or the defect couldn't be checked out | Tool error, git checkout failure, empty response |

**Scoring is conservative**: direct hit requires that a developer reading the findings would know what to fix without looking at the oracle. Adjacent means they'd know where to look but would need to investigate further.

**Inter-rater reliability**: For paper publication, a sample of scores should be independently rated by at least two scorers. Report Cohen's kappa or percent agreement. Disagreements should be resolved by a third scorer or by consensus.

### Statistical Framework

#### Sample Sizes

The full QPB has 2,564 defects, but running all of them may be impractical (cost, time). For statistically meaningful results:

- **Minimum viable sample**: 100 defects (yields ±10% confidence interval at 95% confidence for a 75% detection rate)
- **Recommended sample**: 300 defects (yields ±5% confidence interval)
- **Full benchmark**: 2,564 defects (definitive, but expensive)

#### Stratified Sampling

If not running the full benchmark, select defects using stratified random sampling to ensure representation across:

1. **Category** — proportional to category distribution in the full dataset (e.g., if error handling is 18% of defects, 18% of the sample should be error handling)
2. **Language** — at least 2 defects per language present in the dataset
3. **Severity** — proportional to severity distribution
4. **Repository** — at least 1 defect per repository (or per repository cluster if >50 repos)

Record the sampling method and random seed. This allows others to reproduce the exact sample.

#### Metrics

Primary metrics (always report):

| Metric | Definition |
|--------|-----------|
| **Detection rate (strict)** | direct_hits / (total - not_evaluable) |
| **Detection rate (relaxed)** | (direct_hits + adjacent) / (total - not_evaluable) |
| **Miss rate** | misses / (total - not_evaluable) |

Secondary metrics (report when sample size permits):

| Metric | Definition |
|--------|-----------|
| **Detection rate by category** | Strict detection rate computed per defect category |
| **Detection rate by language** | Strict detection rate computed per programming language |
| **Detection rate by severity** | Strict detection rate computed per severity level |
| **Detection rate by playbook step** | Which playbook step produced the detection (from the "playbook angle" field) |
| **False positive rate** | Findings that flag an issue in the reviewed files that doesn't correspond to any known QPB defect. Note: this is a lower bound — the "false positive" may be a real bug not in the QPB. |

#### Confidence Intervals

Report 95% Wilson score confidence intervals for all detection rates. For a sample of size n with k detections:

```
p̂ = k/n
CI = Wilson score interval (not Wald — Wald is unreliable for extreme proportions)
```

For cross-model or cross-version comparisons, use McNemar's test (paired, since both runs score the same defects) or a chi-squared test (unpaired).

### Improvement Iteration Protocol

When using QPB results to improve the playbook:

1. **Run baseline**: Score playbook version N against the sample
2. **Analyze misses**: For each miss, examine the oracle and the agent's findings. Identify the class of bug the playbook failed to guide the agent toward.
3. **Propose changes**: Draft playbook text changes as edits to the actual playbook files in `playbook/`. Each change must pass the Abstraction Level Validation (see below).
4. **Re-run misses**: Re-run ONLY the missed defects with the updated playbook text. Record re-run scores separately from baseline scores.
5. **Run holdout**: Run the updated playbook against a HELD-OUT set of defects that were NOT used to identify misses. This is the real test — improvement on the training misses is expected; improvement on the holdout set demonstrates generalization.
6. **Report both**: Always report baseline, re-run, and holdout scores. Improvement that only appears on re-runs (the defects that motivated the change) is overfitting.

#### Abstraction Level Validation

Every proposed playbook change must be a general principle, not a fix for a specific codebase. Before any change is accepted:

- **Strip all codebase-specific references.** The proposed text must not mention specific libraries, specific function names from the test repos, or specific variable names from the miss that motivated the change. If you can't state the rule without naming the library, the rule is too narrow.
- **State the underlying invariant.** Each change should express a general software engineering principle that applies across languages and domains.
- **Provide cross-language examples.** If the principle is real, it should have natural examples in at least 3 languages/ecosystems. If you can only think of examples from the miss that motivated it, the principle may be too narrow.
- **Check for existing coverage.** Verify the playbook doesn't already cover the principle under a different name or in a different section. Duplication dilutes the playbook.

#### Council of Three Review Gate

Before any proposed change is published, a Council of Three review must validate:

- **Abstraction level**: Is the rule general enough to apply to codebases the QPB hasn't tested? Could you explain it to a reviewer working on a completely different tech stack?
- **Overfitting risk**: Does the rule help only with the specific miss, or does it plausibly help with a class of bugs? If you removed the QPB dataset entirely, would a senior engineer still agree this belongs in a code review playbook?
- **Regression risk**: Could the new rule cause false positives that waste reviewer attention? Is the signal-to-noise ratio acceptable?
- **Minimal scope**: Is the change the smallest addition that captures the principle? Could it be a single sentence added to an existing section instead of a new section?

#### Re-Run Scoring Rules

- Track detection rates honestly. Don't count re-runs in the baseline numbers.
- Report both baseline scores AND re-run scores for each defect.
- A change that converts a MISS to ADJACENT is partial credit, not full success.
- **DIRECT HIT on re-run**: Change is validated. Proceed to Council of Three review.
- **ADJACENT on re-run**: Change helped but may need tightening.
- **Still MISS on re-run**: Revise the proposed text or accept that the miss isn't addressable by general playbook guidance.

#### Train/Holdout Split

When iterating on the playbook:

- **Training set** (60%): Used for identifying misses and motivating playbook changes
- **Holdout set** (40%): Scored only after playbook changes are finalized. Never used to motivate changes.

The split should be stratified (same category/language/severity proportions in both sets). Record the split and random seed.

#### Stopping Criterion

Stop iterating when:
- Detection rate on the holdout set plateaus (less than 2 percentage point improvement across two consecutive iterations), OR
- The proposed changes fail the Abstraction Level Validation (changes are becoming too specific to the training misses), OR
- The false positive rate increases by more than 5 percentage points (new guidance is causing false alarms)

---

## Reproducibility Requirements

For paper publication, the following must be available:

| Artifact | Purpose | Location |
|----------|---------|----------|
| QPB defect dataset | Ground truth | `dataset/DEFECT_LIBRARY.md`, `dataset/defects.jsonl` |
| Repository snapshots | Code under test | `repos/` (git clones with full history) |
| Playbook under test | The intervention | `playbook/SKILL.md` + `playbook/references/` (also versioned in `awesome-copilot/skills/quality-playbook/`) |
| Phase 1 context artifacts | Input to Phase 2 | `runs/<run_id>/contexts/<repo>.md` |
| Phase 2 agent prompts | Exact prompts sent | `runs/<run_id>/prompts/<defect_id>.md` |
| Phase 2 agent outputs | Raw findings | `runs/<run_id>/findings/<defect_id>.md` |
| Scoring log | Score + evidence | `runs/<run_id>/results.jsonl` |
| Run metadata | Parameters, timing, costs | `runs/<run_id>/metadata.json` |
| Sampling record | Which defects, why | `runs/<run_id>/sample.json` |

All run artifacts should be committed to version control or archived with the paper.

### Review Output Directory

Council of Three reviews, methodology audits, and playbook change reviews are stored in `reviews/` at the repo root. These are authored artifacts and should be version-controlled as part of the paper's audit trail.

Naming convention: `{type}-{reviewer}-{subject}-{date}.md`

- **type**: `council-review`, `spec-audit`, `playbook-review`
- **reviewer**: `copilot`, `cursor`, `claude`, `human`
- **subject**: what was reviewed (e.g., `methodology`, `playbook-v1.3.0`)
- **date**: `YYYY-MM-DD`

### Run Directory Structure

```
runs/
  <run_id>/
    metadata.json          # Run parameters, model, playbook version, dates
    sample.json            # Defect IDs in this run, sampling method, random seed
    contexts/
      <repo>.md            # Phase 1 context artifact for each repo
      <repo>.tokens.json   # Token count and timing for Phase 1
    prompts/
      <defect_id>.md       # Exact prompt sent for each Phase 2 review
    findings/
      <defect_id>.md       # Raw agent output for each Phase 2 review
    results.jsonl          # One JSON line per defect: score, evidence, timing
    summary.md             # Aggregate statistics, tables, charts
```

---

## Per-Repo Description File Format

Each repository will have a `dataset/defects/<repo>/defects.md` file containing detailed descriptions of its defects. Currently, sample files exist for `curl` (5 of 49 entries) and `cli` (20 of 71 entries). The remaining repositories will be generated after council review of the format. The target format for each defect entry is:

```markdown
## PREFIX-NN | Title | Category | Severity

**Fix commit**: [`<sha>`](https://github.com/<owner>/<repo>/commit/<sha>)
**Pre-fix commit**: `<parent_sha>`
**Issue/PR**: [#NNN](https://github.com/<owner>/<repo>/pull/NNN)

**Files changed**:
- `path/to/file1.ext`
- `path/to/file2.ext`

**Commit message**:
(verbatim commit message from git log)

**Issue/PR summary**:
(1-3 sentence summary of the GitHub issue or PR, in our own words; see Issue Text Reuse Policy below)

**Defect summary**:
(2-4 sentence description of what was wrong, derived from examining the actual git diff)

**Diff stat**:
(output of git diff --stat between pre-fix and fix commits)

**Playbook angle**:
(which playbook step should catch this, and what pattern to look for)
```

### Data Sources for Each Field

| Field | Source | Availability |
|-------|--------|-------------|
| Fix commit | DEFECT_LIBRARY.md | 100% (2,564/2,564) |
| Pre-fix commit | DEFECT_LIBRARY.md (parent of fix) | 100% |
| Issue/PR | Extracted from commit message | 73% (1,877/2,564) |
| Files changed | `git diff-tree --name-only` on fix commit | 97% (2,480/2,564) |
| Commit message | `git log --format=%B` on fix commit | 98% (2,508/2,564) |
| Original issue description | Fetched from GitHub issue/PR page | Available for all with issue refs |
| Defect summary | Written by mining agent based on diff analysis | 100% |
| Diff stat | `git diff --stat` between pre-fix and fix | 97% |
| Playbook angle | Written by mining agent | 100% |

---

## Threats to Validity

### Internal Validity

1. **Phase 1 contamination**: Phase 1 context is generated at HEAD, which includes fix commits. The agent may learn about the codebase's defensive patterns from code that was added by fix commits. Mitigation: Phase 1 builds general context (architecture, domain), not bug-specific knowledge. The review prompt in Phase 2 gives no indication of which bugs exist.

2. **Prompt sensitivity**: Agent performance depends on exact prompt wording. Mitigation: Log exact prompts; report prompt variation experiments if feasible.

3. **Scorer bias**: Human scorers who know the oracle may be biased toward generous scores. Mitigation: Use the conservative rubric (direct hit requires actionable specificity); report inter-rater reliability.

4. **Model nondeterminism**: LLM outputs are stochastic. The same defect may score differently on two runs. Mitigation: For high-stakes results, run each defect 3 times and report majority vote. For exploratory runs, single-pass is acceptable but note it.

### External Validity

1. **Mining bias**: Defects were mined from commit messages containing fix-related keywords. Bugs fixed without such keywords are missed. This biases toward well-documented fixes.

2. **Repository selection**: The 50 repositories were hand-selected for diversity, not randomly sampled from all open-source projects. Results may not generalize to closed-source or enterprise codebases.

3. **Single-commit constraint**: Bugs fixed across multiple commits are not captured. This may under-represent complex architectural defects that require multi-file refactoring.

4. **Category judgment**: Category assignment involves judgment calls. A bug might reasonably be categorized as both "error handling" and "null safety." We chose one primary category per defect.

5. **Severity subjectivity**: Severity (Critical/High/Medium/Low) was assessed based on the defect description and affected code, not on production impact data.

### Construct Validity

1. **Detection ≠ Prevention**: Finding a bug in a code review doesn't mean it would have been prevented. A reviewer might find the bug but fail to communicate it effectively, or the fix might introduce new bugs.

2. **Playbook vs. model**: It's hard to separate the playbook's contribution from the model's inherent code understanding. A sufficiently capable model might find the same bugs without any playbook guidance. Mitigation: run a "no playbook" baseline where the agent reviews the same files with only "find bugs in this code" as guidance, and compare detection rates.

3. **File scoping**: Providing the exact files changed by the fix commit is a form of hint — a real reviewer wouldn't know which files to examine. Mitigation: acknowledge this as a limitation. For a subset of defects, try the review without specifying files (point at the whole module instead) and compare.

---

## Issue Text Reuse Policy

The per-repo description files include an "Original issue description" field. To avoid legal risk from reproducing full GitHub issue or PR text:

- **Commit messages** are included verbatim (they are part of the repository's version-controlled history under its license).
- **Issue/PR descriptions** are summarized in our own words, not quoted verbatim. Each summary is 1-3 sentences capturing the essential technical content.
- **Links** to the original issue/PR are always provided so readers can access the full context.
- **No reproduction of comments, discussion threads, or reproduction steps** from issue trackers.

This approach provides sufficient context for defect verification while respecting upstream content ownership.

---

## Changelog

- **2026-03-29**: Initial methodology document created with dataset composition, mining protocol, and scoring rubric.
- **2026-03-30**: Major revision. Added: complete evaluation protocol (Phase 1/Phase 2 separation), statistical framework (sampling, confidence intervals, metrics), improvement iteration protocol (train/holdout split, stopping criterion), reproducibility requirements (run directory structure, logging schema), threats to validity (internal, external, construct). Moved scoring rubric into evaluation protocol. Added contamination controls, inter-rater reliability requirements, and "no playbook" baseline recommendation.
