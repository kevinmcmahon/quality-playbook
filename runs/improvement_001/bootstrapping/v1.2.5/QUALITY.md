# Quality Constitution: Quality Playbook Benchmark (QPB)

## Purpose

The Quality Playbook Benchmark (QPB) is a curated dataset of 2,564 real defects from 50 open-source repositories, designed to measure and improve the detection rate of AI-assisted code review playbooks. Quality for QPB means:

- **Deming**: Quality is built into the dataset structure, methodology documentation, and tooling so every AI session that uses QPB inherits the same ground truth and reproducibility standards.
- **Juran**: Fitness for use means QPB provides reliable, verified ground truth for measuring code review effectiveness. A defect record must be verifiable, complete, and traceable to actual code.
- **Crosby**: Building a rigorous dataset upfront costs effort but prevents downstream analysis based on corrupted or ambiguous defect data — which would invalidate all results.

## Coverage Targets

| Subsystem | Target | Why |
|-----------|--------|-----|
| DEFECT_LIBRARY.md format compliance | 100% | Every defect record must be verifiable. Missing or malformed fields make scoring impossible. A single corrupted row undermines statistical validity. |
| Category normalization (14 canonical labels) | 100% | Categories are the axes for analysis (cross-model detection rates by category, defect patterns). Inconsistent categories produce aggregation errors and false detection rate conclusions. |
| Tooling script correctness | 95%+ | Scripts regenerate extracted data and normalize categories. Bugs in these tools produce systematic data errors affecting all downstream analysis. Core modules (extract, normalize, assemble) must be reliable. |
| Defect count consistency across documents | 100% | DEFECT_LIBRARY.md, per-repo description files, and DETECTION_RESULTS.md must agree on defect counts. Discrepancies indicate silent data loss or corruption. |
| Cross-document reference integrity | 100% | Every defect ID in DEFECT_LIBRARY.md must have a corresponding entry in the per-repo description file. Every per-repo file must reference actual commits. Missing references make defects non-evaluable. |

## Coverage Theater Prevention

For QPB, a fake test would be:

- **Asserting a defect library entry contains something without verifying format** — e.g., "assert line 50 contains a defect ID" without checking if the ID is valid or if all 8 columns are present.
- **Counting defects without verifying they are evaluable** — e.g., "assert 2,564 defects exist" without checking that every defect has a valid fix_commit and pre_fix_commit.
- **Asserting category normalization completed without checking canonical membership** — e.g., "assert normalization succeeded" without verifying every category is one of 14 canonical labels.
- **Mocking git operations instead of testing against real repository clones** — Git operations are the foundation; testing with mocks bypasses the real failure modes.
- **Testing DEFECT_LIBRARY.md format without testing against actual markdown parsing** — Markdown is permissive; a test that "asserts a line is present" might pass while actual markdown parsing fails.
- **Extracting defect data without validating commit existence** — A commit hash in the library might be malformed or not exist in the repo. Tests must verify against `git rev-parse`.

## Fitness-to-Purpose Scenarios

### Scenario 1: Defect Library Row Corruption Propagates to All Analysis

**Requirement tag:** [Req: formal — DEFECT_LIBRARY.md format spec, column definitions]

**What happened:** DEFECT_LIBRARY.md is the master index with 2,564 rows. Each row has 8 columns separated by `|`: ID, title, fix_commit, pre_fix_commit, severity, category, description, playbook_angle. A corrupted row (missing a column, unescaped pipe character, truncated field) is silently valid markdown — the markdown parser does not error. But downstream tools that split rows on `|` may assign fields incorrectly (category ends up in the description column) or silently skip the row (if column count doesn't match). This produces silent data loss: evaluators believe they're scoring 2,564 defects but are actually scoring 2,563 (or fewer) because one row is malformed. Statistical analysis on corrupted data invalidates all results. At scale across multiple evaluation runs (10+ models, 50+ repos), one corrupted row affects hundreds of detection rate comparisons.

**The requirement:** Every row in DEFECT_LIBRARY.md must have exactly 8 pipe-separated columns. No column may contain an unescaped pipe character. All required fields (ID, fix_commit, pre_fix_commit, category) must be non-empty. The category must be one of exactly 14 canonical labels. This must be verified by parsing the actual markdown, not by inspection.

**How to verify:**
- Run: `pytest quality/test_functional.py::test_defect_library_format_compliance -v`
- Expected: Test reads DEFECT_LIBRARY.md as markdown table, parses all rows, validates 8 columns per row, no unescaped pipes, all required fields non-empty, categories canonical.
- Failure criteria: Any row with wrong column count, any row with unescaped pipes, any required field empty, any category not in the canonical 14-label set.

---

### Scenario 2: Category Miscount Skews Detection Rate Statistics by 3-7%

**Requirement tag:** [Req: formal — normalize_categories.py specification, canonical category list]

**What happened:** Raw defect mining produces category strings like "bug", "validation", "null check", etc. normalize_categories.py maps these to one of 14 canonical labels. If a normalization rule is broken (e.g., mapping "validation gap" to "error handling" instead of "validation gap"), all 15 defects using that rule get miscategorized. Detection results aggregated by category are then wrong: "validation gap" detection rate is reported as X% when the actual underlying defects include Y% in another category. For detection analysis, this directly breaks the core research question: "which categories are hard for models to detect?" If categories are misaligned, we can't answer that question. With 2,564 defects across 14 categories (average 183 per category), a mismapped rule affecting 15+ defects shifts that category's reported detection rate by 8%+.

**The requirement:** All 2,564 defects must be categorized into exactly one of 14 canonical labels. The normalization rules (keyword matching with ordered precedence) must be deterministic: the same raw category string always produces the same canonical label. All 2,564 defects must be verifiable as canonical. Mismatched or drifted categories must be caught before analysis.

**How to verify:**
- Run: `pytest quality/test_functional.py::test_category_normalization_all_canonical -v`
- Expected: Test reads DEFECT_LIBRARY.md, extracts the category column for all 2,564 rows, verifies every category matches one of exactly 14 canonical strings (case-insensitive match). Produces a histogram showing defects per category.
- Failure criteria: Any category string not matching the 14 canonical labels. Histogram shows fewer than expected defects in any category (indicates mismatches elsewhere).

---

### Scenario 3: Tooling Script Produces Silent Data Loss on Large Batches

**Requirement tag:** [Req: formal — extract_defect_data.py specification, DEFECT_LIBRARY.md format spec]

**What happened:** extract_defect_data.py reads DEFECT_LIBRARY.md, parses each defect ID (PREFIX-NN format), maps the prefix to a repo directory, and runs `git log` / `git show` to extract commit details. If the script encounters a malformed defect ID or a repo directory that doesn't exist, it may log a warning (if error handling exists) or silently skip the row. With 50 repos and 2,564 defects, a silent skip would produce a defect_data.json file that's incomplete — missing data for 10+ defects. Downstream tools that depend on defect_data.json would then ignore those defects in analysis. This is silent data loss: the library says 2,564 but the extraction only produced data for 2,540. No alert. Analysis proceeds on incomplete ground truth.

**The requirement:** extract_defect_data.py must process all 2,564 defects. Every defect ID must be parseable. Every prefix must map to an existing repository directory. Every fix_commit must be resolvable via `git rev-parse` in the corresponding repo. If any defect cannot be processed, the script must fail with an explicit error message naming the defect and the reason (e.g., "GH-03: PREFIX_MAP missing entry for GH2" or "CURL-02: Commit abc123 not found in repos/curl"). No silent skips. The output defect_data.json must include entries for all 2,564 defects.

**How to verify:**
- Run: `pytest quality/test_functional.py::test_extract_defect_data_completeness -v`
- Expected: Test loads DEFECT_LIBRARY.md and invokes extract_defect_data.py. Checks that output defect_data.json contains entries for all 2,564 defects (by ID). For a sample of 20 defects across different repos, verifies the extracted data is non-empty (commit message not blank, files_changed list not empty).
- Failure criteria: defect_data.json missing any defect ID, or any defect with empty commit message / files list.

---

### Scenario 4: Cross-Document Defect Count Mismatch Indicates Data Integrity Loss

**Requirement tag:** [Req: formal — DEFECT_LIBRARY.md, per-repo description files format]

**What happened:** DEFECT_LIBRARY.md lists 2,564 defects. Each defect has a prefix (e.g., GH, CURL, RLS). Per-repo description files in dataset/defects/<repo>/defects.md are organized by prefix and should list all defects for that repo. If one per-repo file is incomplete (20 of 71 defects listed for cli/cli, instead of all 71), the row count in defect_data.json differs from the count in the per-repo file. This mismatch indicates silent data loss during per-repo file generation. Evaluators checking out the pre-fix commit for defect GH-50 might find GH-50 is not in the per-repo description file (or the commit listed there is wrong) — making the defect non-evaluable. At scale across 50 repos, missing or incorrect per-repo files make hundreds of defects impossible to evaluate.

**The requirement:** For every defect in DEFECT_LIBRARY.md, there must be a corresponding entry in the per-repo description file matching its prefix. The per-repo file must list exactly as many defects as DEFECT_LIBRARY.md assigns to that prefix. Cross-document counts must match (within rounding). Any prefix with a count mismatch must be flagged.

**How to verify:**
- Run: `pytest quality/test_functional.py::test_per_repo_defect_count_consistency -v`
- Expected: Test reads DEFECT_LIBRARY.md, groups defects by prefix, counts defects per prefix. Then reads each per-repo description file (if it exists), counts entries, and compares. Produces a report showing prefix, DEFECT_LIBRARY.md count, per-repo file count, and match status.
- Failure criteria: Any prefix with a count mismatch (e.g., GH has 71 in DEFECT_LIBRARY.md but dataset/defects/cli/defects.md lists only 20). Any per-repo file missing (if DEFECT_LIBRARY.md has defects for that prefix, the file must exist).

---

### Scenario 5: Commit SHA Typo in DEFECT_LIBRARY.md Makes Defect Non-Evaluable

**Requirement tag:** [Req: formal — DEFECT_LIBRARY.md column spec, pre_fix_commit and fix_commit format]

**What happened:** A defect row lists fix_commit = "abc123def" (40-char SHA, but typo: only 39 chars valid, last char is "f" instead of a hex digit). When evaluators check out this commit or use it as an oracle, `git rev-parse abc123def` fails (invalid SHA). The defect cannot be evaluated. If this happens for 5+ defects out of 2,564, statistical power is reduced. More importantly, if this is discovered late (after evaluation runs start), it requires re-evaluation of affected defects, wasting compute and model API calls. Commit SHA validation must happen upfront.

**The requirement:** Every fix_commit and pre_fix_commit in DEFECT_LIBRARY.md must be a valid 40-character SHA-1 hash (or resolvable ref, though 40-char SHA is preferred). Each commit must exist in the corresponding repository (resolved via `git rev-parse COMMIT`). The pre_fix_commit must be the immediate parent of the fix_commit (`git rev-parse FIX_COMMIT^ == PRE_FIX_COMMIT`). Any invalid or non-resolvable commit must be detected before the defect is usable.

**How to verify:**
- Run: `pytest quality/test_functional.py::test_commit_sha_validity -v`
- Expected: Test reads DEFECT_LIBRARY.md, extracts fix_commit and pre_fix_commit for all 2,564 defects. For a sample of 100 defects (evenly distributed across prefixes), invokes `git rev-parse` in the corresponding repo to verify both commits exist and pre_fix_commit is the parent of fix_commit.
- Failure criteria: Any invalid SHA format, any SHA that doesn't resolve, any case where pre_fix_commit != git rev-parse FIX_COMMIT^.

---

### Scenario 6: Tooling Script Failure on Edge Cases Requires Manual Intervention

**Requirement tag:** [Req: formal — normalize_categories.py specification, error handling requirements]

**What happened:** normalize_categories.py processes all 2,564 defects and applies keyword-based normalization rules. If a defect has a malformed or unexpected category string (e.g., a raw category with Unicode characters, or a very long string that causes regex backtracking), the script might hang, crash, or produce a nonsensical output. Without defensive error handling, the script fails silently (returns partial output, exits with code 0). Downstream tools depend on all 2,564 categories being normalized; if the script failed on defect #1,500, the output file has categories for 1–1,499 only, and defects 1,500–2,564 have no canonical category assigned. This is silent data loss again, surfaced only if someone manually inspects the output.

**The requirement:** All tooling scripts must include defensive error handling: try/catch for subprocess calls, input validation, explicit logging of failures. If any defect cannot be processed, the script must emit a clear error message and exit with a non-zero code. No silent failures. All errors must be loggable for auditing.

**How to verify:**
- Run: `pytest quality/test_functional.py::test_normalize_categories_handles_edge_cases -v`
- Expected: Test calls normalize_categories.py with deliberately malformed input (missing category field, very long category string, non-ASCII characters) and verifies the script exits with an error code and produces a clear error message (not a silent skip or hang).
- Failure criteria: Script returns exit code 0 despite processing error. Script hangs or times out. No error message logged for problematic defects.

---

### Scenario 7: API Contract Violation — Evaluation Results Schema Mismatch

**Requirement tag:** [Req: formal — DETECTION_RESULTS.md scoring schema]

**What happened:** Evaluators run the quality playbook and score each defect: direct_hit / adjacent / miss / not_evaluable. Results are recorded in a JSONL file (`results.jsonl`) with fields: run_id, defect_id, score, etc. If the scorer uses a non-standard score value (e.g., "direct-hit" instead of "direct_hit", or "MISS" instead of "miss"), downstream analysis that filters on score value silently ignores that row. An evaluator scores 281 defects but because of a typo in 10 score values, analysis only counts 271 defects. Statistical comparison between runs is then invalid: one run appears to have lower detection rate but it's only because the score values don't match the schema.

**The requirement:** All evaluation results must conform to DETECTION_RESULTS.md schema: score must be one of exactly 4 values (direct_hit, adjacent, miss, not_evaluable), all fields present, defect_id must match a valid entry in DEFECT_LIBRARY.md. Any result record that doesn't conform must be rejected during import/analysis.

**How to verify:**
- Run: `pytest quality/test_functional.py::test_detection_results_schema_validation -v`
- Expected: Test reads a sample detection results JSONL file (or creates one synthetically) and validates each record against the schema: required fields, score enum, defect_id exists in DEFECT_LIBRARY.md. Reports any schema violations.
- Failure criteria: Any missing required field, any invalid score value, any defect_id not in DEFECT_LIBRARY.md.

---

## AI Session Quality Discipline

Every AI session working on QPB must:

1. Read this QUALITY.md file before starting work.
2. Run the full test suite (`pytest quality/test_functional.py -v`) before marking any task complete.
3. Add tests for new tooling features (not just happy path — include validation and error cases).
4. Update this file if new failure modes are discovered in code review or audit.
5. Output a Quality Compliance Checklist (below) before ending a session.
6. Never remove a fitness-to-purpose scenario — only add or refine.

## Quality Compliance Checklist

Before ending a session, verify:

- [ ] All tests in `quality/test_functional.py` pass (run `pytest quality/test_functional.py -v`)
- [ ] Code coverage for core modules remains above 80% (run `pytest quality/test_functional.py --cov=tooling`)
- [ ] All defects in DEFECT_LIBRARY.md are verified for format, SHA validity, and category correctness
- [ ] Per-repo description files match DEFECT_LIBRARY.md counts (no silent data loss)
- [ ] All tooling scripts run without errors on the full 2,564-defect dataset
- [ ] DEFECT_LIBRARY.md row count matches sum of per-repo defect counts
- [ ] No fitness-to-purpose scenarios were removed or weakened

## The Human Gate

The following require human judgment and cannot be automated:

- **Verification of defect accuracy** — Is the defect description correct? Does the fix commit actually fix the described issue? Requires reading actual code and commit messages.
- **Category appropriateness** — Is a defect correctly categorized? Some defects genuinely span multiple categories; human judgment is needed to assign the primary category.
- **Severity assessment** — Is a "Critical" severity accurate, or should it be "High"? Requires understanding the system's context and failure impact.
- **Playbook angle accuracy** — Which playbook step should detect this? Requires reading the playbook and reasoning about what the step is designed to catch.
- **Dataset completeness decisions** — Which new repos should be added to fill gaps? Which languages are underrepresented? Requires strategic judgment about research value.
