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

**Original issue description**:
(full text from the GitHub issue or PR that reported/fixed this defect)

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

## How to Use the QPB

### For playbook evaluation

1. Check out `pre_fix_commit` for a given defect
2. Run your code review playbook against the files listed in `files_changed`
3. Score using the rubric:
   - **Direct hit**: The review names the specific bug or its root cause
   - **Adjacent**: The review flags the affected area or a related concern but doesn't identify the specific bug
   - **Miss**: The review doesn't mention the bug or the affected code area
4. The `fix_commit` diff is the ground truth oracle — it shows exactly what was wrong and how it was fixed

### For council-of-three review

Each per-repo `defects.md` file is self-contained. A reviewer can:
- Verify that the category assignment is correct by reading the defect summary and commit message
- Verify that the severity is appropriate by reading the impact described
- Verify that the playbook angle is actionable by considering whether the suggested detection step would realistically catch this class of bug
- Spot-check by examining the actual fix commit on GitHub

## Files in This Dataset

- `dataset/DEFECT_LIBRARY.md` — Master index with all QPB entries (summary table, one row per defect)
- `dataset/defects.jsonl` — Machine-readable export (one JSON object per line)
- `dataset/METHODOLOGY.md` — This methodology document
- `dataset/DETECTION_RESULTS.md` — Results schema for scoring playbook runs against the QPB
- `dataset/defects/<repo>/defects.md` — Per-repo detailed defect descriptions
- `tooling/extract_defect_data.py` — Git data extraction script
- `tooling/normalize_categories.py` — Category normalization script (14 canonical categories)

## Issue Text Reuse Policy

The per-repo description files include an "Original issue description" field. To avoid legal risk from reproducing full GitHub issue or PR text:

- **Commit messages** are included verbatim (they are part of the repository's version-controlled history under its license).
- **Issue/PR descriptions** are summarized in our own words, not quoted verbatim. Each summary is 1-3 sentences capturing the essential technical content.
- **Links** to the original issue/PR are always provided so readers can access the full context.
- **No reproduction of comments, discussion threads, or reproduction steps** from issue trackers.

This approach provides sufficient context for defect verification while respecting upstream content ownership.

## Known Limitations

1. **Mining bias**: Defects were mined from commit messages containing fix-related keywords. Bugs fixed without such keywords in the message are missed. This biases toward well-documented fixes.
2. **Category judgment**: Category assignment involves judgment calls. A bug might reasonably be categorized as both "error handling" and "null safety." We chose one primary category per defect.
3. **Severity subjectivity**: Severity (Critical/High/Medium/Low) was assessed based on the defect description and affected code, not on production impact data.
4. **Shallow history**: Some repository clones have limited history (e.g., FastAPI with only 63 commits), yielding fewer defects.
5. **Single-commit constraint**: Bugs fixed across multiple commits are not captured. This may under-represent complex architectural defects.
6. **Issue description availability**: 27% of defects don't have extractable issue/PR references in their commit messages, so the "original issue description" field relies on the commit message body for those entries.
