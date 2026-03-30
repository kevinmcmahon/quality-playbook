# Council of Three Review — Quality Playbook Benchmark (QPB)

You are reviewing the Quality Playbook Benchmark (QPB), a dataset of 2,564 real defects from 50 open-source repositories. The dataset will be used to measure and improve AI-assisted code review playbooks, and will be published publicly. Your job is to assess whether the dataset is sound, the format is complete, and the sample data is accurate.

## Scope of this review

Read and evaluate all the documentation and sample files listed below. For spot-checking, you have access to one full repository clone: **curl/curl** in `repos/curl/`. Use it to verify claims by examining actual commits, diffs, and history. Do **not** crawl into the other 50 repos — they're present on disk but are out of scope for this review.

## Files to read (in order)

1. **`README.md`** (repo root) — Public-facing overview for humans
2. **`AGENTS.md`** (repo root) — AI-facing reference with conventions, workflows, current state
3. **`dataset/METHODOLOGY.md`** — How defects were mined, constraints, format spec, known limitations
4. **`dataset/DEFECT_LIBRARY.md`** — Master index of all 2,564 defects (skim the structure, read the header material, sample a few dozen rows across different prefixes)
5. **`dataset/DETECTION_RESULTS.md`** — Scoring results schema
6. **`dataset/defects/curl/defects.md`** — Per-repo description file for curl/curl (5 entries with full detail: commit message, files changed, issue description, diff stat)
7. **`dataset/defects/cli/defects.md`** — Per-repo description file for cli/cli (20 entries, older format without fetched issue descriptions)
8. **`tooling/extract_defect_data.py`** — Script that extracts commit messages, files, diffs from repos
9. **`tooling/normalize_categories.py`** — Category normalization script

## Spot-check instructions (curl/curl only)

For at least 3 of the 5 CURL defects in `dataset/defects/curl/defects.md`, verify the following against the actual repo in `repos/curl/`:

```bash
cd repos/curl

# 1. Confirm the fix commit exists and its parent matches pre_fix_commit
git log --oneline CURL_FIX_SHA -1
git rev-parse CURL_FIX_SHA^    # should match pre_fix_commit

# 2. Confirm the files changed match
git diff-tree --no-commit-id --name-only -r CURL_FIX_SHA

# 3. Read the actual diff and verify the defect description is accurate
git diff CURL_PRE_FIX_SHA..CURL_FIX_SHA

# 4. Confirm the commit message matches
git log --format="%B" CURL_FIX_SHA -1
```

For each spot-checked defect, report: Does the category assignment match what you see in the diff? Is the severity reasonable? Is the description accurate? Is the playbook angle actionable?

## Review areas

### 1. Methodology soundness
- Is the single-commit constraint appropriate, or does it exclude important classes of bugs?
- Is mining from commit message keywords a reasonable approach? What kinds of bugs might we systematically miss?
- Are 14 defect categories the right granularity? Should any be split or merged?
- Is the severity scale (Critical/High/Medium/Low) well-defined enough for consistent application?

### 2. Dataset format and completeness
- Does the DEFECT_LIBRARY.md table contain all necessary fields?
- Does the per-repo defects.md format contain enough information for independent verification?
- Is the "original issue description" field adding value beyond the commit message and defect summary?
- Should the actual git diff be included inline, or is the diff stat + commit link sufficient?
- Are the README.md and AGENTS.md accurate and complete?

### 3. Sample data quality (curl and cli)
- For CURL-01 through CURL-05: Are the categories correct? Severities consistent? Descriptions accurate?
- For GH-01 through GH-20: Same questions. Note these use an older format — is the newer curl format better?
- Are the "playbook angle" entries specific enough to be actionable, or too vague?

### 4. Scoring rubric
The proposed rubric is:
- **Direct hit**: The review names the specific bug or its root cause
- **Adjacent**: The review flags the affected area or a related concern
- **Miss**: The review doesn't mention the bug or the affected code area

Is this sufficient? Should there be additional categories (partial hit, false positive)? Is it clear enough for consistent scoring across reviewers?

### 5. Tooling review
- Does `extract_defect_data.py` look correct? Any edge cases it might miss?
- Does `normalize_categories.py` have reasonable mapping rules? Any categories that seem mis-mapped?
- Are there obvious improvements to either script?

### 6. Publication readiness
- What's missing before this dataset can be published on GitHub?
- Are there any legal, ethical, or attribution concerns?
- Would you use this dataset as-is for benchmarking? If not, what would need to change?

## Deliverable

Please provide:

1. **Overall assessment**: Sound / Needs revision / Fundamentally flawed
2. **Spot-check results**: For each CURL defect you verified, a pass/fail on category, severity, description accuracy, and playbook angle
3. **Specific feedback** on each of the 6 review areas above
4. **Recommended changes** before generating the remaining ~2,500 detailed defect entries and before publication
5. **Anything we missed** that you'd want to see in a benchmark dataset like this
