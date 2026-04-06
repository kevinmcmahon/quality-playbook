# Code Review Protocol: Quality Playbook Benchmark (QPB)

## Bootstrap (Read First)

Before reviewing, read these files for context:

1. `quality/QUALITY.md` — Quality constitution with 7 fitness-to-purpose scenarios
2. `AGENTS.md` — QPB purpose, repository layout, dataset overview
3. `dataset/METHODOLOGY.md` — How defects were mined, evaluation protocol, scoring rubric
4. `PROJECT_PLAN.md` — Current state, phase roadmap, known limitations
5. `tooling/extract_defect_data.py` — Defect data extraction logic
6. `tooling/normalize_categories.py` — Category normalization rules
7. `tooling/assemble_v8.py` — DEFECT_LIBRARY.md assembly logic

## What to Check

### Focus Area 1: Category Normalization Logic (`tooling/normalize_categories.py`)

**Where:** `tooling/normalize_categories.py` (entire file, especially the `normalize()` function and keyword-based rules)

**What:**
- Keyword matching rules have correct precedence (security first, validation gap as fallback)
- All 14 canonical categories are referenced
- Mapping is deterministic (same input always produces same output)
- Handles edge cases: whitespace, markdown bold (`**`), parenthetical qualifiers, slashes
- No raw category string is left unmapped (fallback rule exists)
- Normalization preserves the correct casing for output

**Why:** Incorrect normalization silently miscategorizes 10+ defects per wrong rule, shifting detection rate statistics by 3-7%. (Scenario 2, QUALITY.md)

**Specific lines to check:**
- Rule precedence order (does security check come before generic rules?)
- Fallback rule (what happens if a category matches nothing?)
- Parenthetical handling: `re.sub(r'\s*\(.*?\)', '', clean)` — correctly removes secondary tags?

**Red flags:**
- Rules that could match multiple canonical categories without clear precedence
- Fallback rule that silently assigns a default instead of reporting unmappable categories
- Rules that lose information (e.g., treating "null safety" as "error handling")

---

### Focus Area 2: Defect Data Extraction (`tooling/extract_defect_data.py`)

**Where:** `tooling/extract_defect_data.py` (prefix mapping, git operations, JSON output)

**What:**
- Prefix-to-repo mapping (`PREFIX_MAP`) is complete and correct for all 2,564 defects
- Git operations (`git log`, `git show`, `git diff-tree`) run without silent failures
- Extracted data includes all required fields: commit message, files changed, diff stats, issue refs
- Error handling: if a commit doesn't exist or a prefix is unmapped, script exits with error (not silent skip)
- Output JSON is valid and contains entries for all 2,564 defects

**Why:** Silent data loss (skipping defects when repos are missing or commits don't exist) invalidates downstream analysis. (Scenario 3, QUALITY.md)

**Specific lines to check:**
- PREFIX_MAP dictionary: Does it include all 55+ prefixes found in DEFECT_LIBRARY.md?
- Git subprocess calls: Do they have error handling? What happens on returncode != 0?
- Output file writing: Is the JSON file written completely or could it be truncated on error?
- Entry-per-defect: Is the script designed to process all 2,564 defects, or does it skip some?

**Red flags:**
- Missing prefixes in PREFIX_MAP without a fallback or error
- Git operations that fail silently (returncode checked, but error not logged)
- Output file written in a single write (could be truncated) instead of validated
- Early return from loop without processing all defects

---

### Focus Area 3: DEFECT_LIBRARY.md Format Compliance

**Where:** `dataset/DEFECT_LIBRARY.md` (entire file, focus on row structure and column integrity)

**What:**
- Every row has exactly 8 pipe-separated columns: ID, title, fix_commit, pre_fix_commit, severity, category, description, playbook_angle
- No unescaped pipe characters in descriptions (or pipes are correctly handled in parsing)
- All required fields (ID, fix_commit, pre_fix_commit, category) are non-empty
- Defect IDs follow PREFIX-NN format (alphabetic prefix, dash, numeric suffix)
- Severity values are one of: Critical, High, Medium, Low (case-sensitive)
- Categories are one of 14 canonical labels (handled by normalization, but check source data)
- Row count: ~2,564 defects (exact count may vary, but should be in 2,500+ range)

**Why:** Corrupted rows produce silent data loss or miscounts. A single malformed row could break downstream parsing. (Scenario 1, QUALITY.md)

**Specific lines to check:**
- First 10 rows: Do they parse correctly as 8 columns?
- Sample rows from middle and end: Any truncation or misalignment?
- Pipe-character escaping: Do descriptions with pipes (e.g., "foo | bar") break the table?
- ID format: All follow PREFIX-NN? No IDs like "GH01" (should be "GH-1") or "GH-1a"?

**Red flags:**
- Any row with fewer or more than 8 columns
- Unescaped pipes in descriptions that would misalign the table
- Non-canonical severity or category values
- Defect count doesn't match expected range
- Rows with empty required fields

---

### Focus Area 4: Commit SHA Validity and Traceability

**Where:** `dataset/DEFECT_LIBRARY.md` (fix_commit and pre_fix_commit columns) and cross-referenced in `repos/`

**What:**
- All fix_commit and pre_fix_commit values are 40-character SHA-1 hashes (no short SHAs, no refs like `HEAD~1`)
- Commits exist in their respective repositories (can be verified with `git rev-parse`)
- pre_fix_commit is the immediate parent of fix_commit (can be verified with `git rev-parse FIX_COMMIT^`)
- Commits are referenced consistently (casing, no whitespace)

**Why:** Invalid or typo'd commit SHAs make defects non-evaluable. At scale across 2,564 defects, even 5 typos reduce statistical power. (Scenario 5, QUALITY.md)

**Specific lines to check:**
- Sample 10 defects from DEFECT_LIBRARY.md: Are the fix and pre-fix SHAs exactly 40 hex characters?
- For accessible repos (if repos/ is cloned), spot-check that SHAs exist and pre-fix is parent of fix
- Consistency: Are all SHAs lowercase hex, or is there mix of upper/lower case?

**Red flags:**
- Any SHA with non-hex characters
- Any SHA that's not 40 characters (too short/long)
- SHAs that don't resolve in their repos (if repos are available for testing)
- Whitespace in SHA fields
- SHAs that are refs instead of hashes

---

### Focus Area 5: Per-Repo Description File Completeness

**Where:** `dataset/defects/<repo>/` (all subdirectories with defects.md files)

**What:**
- For each repository with defects in DEFECT_LIBRARY.md, a corresponding `defects/<repo>/defects.md` file exists
- Per-repo file lists all defects for that repository (row count matches DEFECT_LIBRARY.md count for that prefix)
- Each per-repo file includes required fields: commit message, files changed, diff stat, issue description, playbook angle
- Format is consistent across all per-repo files (same column headers, same field structure)

**Why:** Missing or incomplete per-repo files make defects non-evaluable (evaluators can't find the file to check details). (Scenario 4, QUALITY.md)

**Specific lines to check:**
- For cli/cli (GH): Is `dataset/defects/cli/defects.md` present? Does it list 71 defects to match DEFECT_LIBRARY.md?
- For curl (CURL): Is `dataset/defects/curl/defects.md` present? Does it list 49 defects?
- Format consistency: Do all per-repo files use the same markdown table structure?
- Required fields: Do all entries include commit message, files changed, and playbook angle?

**Red flags:**
- Missing per-repo description files for repositories with defects in DEFECT_LIBRARY.md
- Defect count mismatch (DEFECT_LIBRARY.md says 71 but per-repo file lists only 20)
- Incomplete entries (missing required fields)
- Format inconsistencies across per-repo files

---

### Focus Area 6: Tooling Script Error Handling and Logging

**Where:** `tooling/extract_defect_data.py`, `tooling/normalize_categories.py`, `tooling/assemble_v8.py`

**What:**
- All subprocess calls (git operations) have error handling (check returncode, log error)
- File I/O operations have error handling (file not found, permission denied, parse errors)
- If a defect cannot be processed, the script logs a specific error message and exits non-zero (or reports the error)
- No silent failures or incomplete output files
- Scripts provide clear help text (`--help`) documenting usage and parameters

**Why:** Silent failures cause data loss that's only discovered late (e.g., after evaluation runs start). (Scenario 6, QUALITY.md)

**Specific lines to check:**
- Subprocess calls: Are returncode != 0 checked? Is stderr logged?
- File operations: Are OSError/IOError caught and logged?
- Exit codes: Does script exit with code != 0 on error, or always exit 0?
- Help text: Does `--help` clearly document required arguments and options?

**Red flags:**
- Subprocess calls without returncode checking
- File operations without try/except
- Error messages that don't include the specific problem (generic "failed" without details)
- No exit code on error (script exits 0 even after logging an error)
- Missing or unclear help text

---

### Focus Area 7: Quality Playbook Methodology Alignment

**Where:** `dataset/METHODOLOGY.md` (evaluation protocol) and cross-referenced in AGENTS.md, PROJECT_PLAN.md

**What:**
- Defect evaluation protocol is clearly documented: Phase 1 (context generation at HEAD), Phase 2 (defect review at pre-fix commit)
- Scoring rubric is unambiguous: direct_hit, adjacent, miss, not_evaluable with clear definitions
- Reproducibility documented: how to check out pre-fix commits, which files to review, how to score against the oracle
- Known limitations are listed (e.g., "Phase 1 runs at HEAD, which includes fix commits" — acceptable because it's about architecture understanding)
- Results schema (DETECTION_RESULTS.md) maps to evaluation protocol (same field names, same score values)

**Why:** Ambiguous evaluation protocol leads to scorer disagreement and non-reproducible results. (Scenario 7, QUALITY.md — API contract compliance)

**Specific lines to check:**
- METHODOLOGY.md Phase 1: Is it clear what the context generation step produces?
- METHODOLOGY.md Phase 2: Are the checkout and review steps unambiguous?
- Scoring Rubric (METHODOLOGY.md): Does each score value have a clear, actionable definition?
- DETECTION_RESULTS.md: Do the score values and required fields match METHODOLOGY.md exactly?

**Red flags:**
- Ambiguous or conflicting evaluation instructions across documents
- Scoring definitions that are subjective or could be interpreted differently
- Score values that don't match between METHODOLOGY.md and DETECTION_RESULTS.md
- Missing documentation of the oracle (what makes the fix commit the ground truth?)

---

## Guardrails

- **Line numbers are mandatory.** If you cannot cite a specific line, do not include the finding. Use this format: "Line NNN: [description]"
- **Read function bodies, not just signatures.** Don't assume a function works correctly based on its name. Check the actual implementation.
- **If unsure whether something is a bug or intentional**, flag it as a QUESTION rather than a BUG, and note the ambiguity.
- **Grep before claiming missing.** If you think a feature is absent, search the codebase first. If found in a different file, that's a location defect, not missing.
- **Do NOT suggest style changes, refactors, or improvements.** Only flag things that are incorrect, could cause failures, or violate the spec (QUALITY.md).
- **Check both code and docs.** A bug in code is critical. A divergence between code and docs (code is correct, but docs say something else) is also critical for reproducibility.

---

## Output Format

Save findings to `quality/code_reviews/YYYY-MM-DD-reviewer.md`

For each file or focus area reviewed:

### [filename.ext or Focus Area Name]

- **Line NNN:** [BUG / QUESTION / INCOMPLETE] Description of finding. Expected vs. actual. Why it matters.

Example:
```
### normalize_categories.py

- **Line 58:** BUG — Keyword rule for "null check" is missing. The rule list includes security, validation, error handling, etc., but not null safety. Any defect with category "null check" will fall through to the fallback rule and be miscategorized. Affects all null safety defects from this mining round.

### extract_defect_data.py

- **Line 120:** QUESTION — Subprocess call to git log does not check returncode. If git fails (e.g., repo corrupted), does the script continue with empty data or exit with error? Need to verify error handling path.

### DEFECT_LIBRARY.md

- **Line 2847:** INCOMPLETE — Defect RLS-25: row has only 7 columns (missing playbook_angle). Required fields: 8 columns expected, got 7. This row will be skipped by parsers expecting 8 columns.
```

### Summary

- Total findings by severity (BUG, QUESTION, INCOMPLETE)
- Files with no findings
- Overall assessment: SHIP IT / FIX FIRST / NEEDS DISCUSSION

Example:
```
## Summary

- **BUGs found:** 3
  - normalize_categories.py: 1 (missing null safety rule)
  - extract_defect_data.py: 1 (subprocess error handling)
  - DEFECT_LIBRARY.md: 1 (malformed row)

- **QUESTIONs:** 2
  - assemble_v8.py: Unclear error recovery path

- **Files reviewed with no findings:** 5

**Overall assessment:** FIX FIRST — The missing null safety rule affects all null safety defects (103 expected in the library). The malformed DEFECT_LIBRARY.md row makes that defect non-evaluable. Both should be fixed before the dataset is used for evaluation.
```

---

## Phase 2: Regression Tests for Confirmed Bugs

After code review produces findings, write regression tests that reproduce each BUG finding. This transforms the review from "here are potential bugs" into "here are proven bugs with failing tests."

**For each BUG finding**, write a test that:
- Targets the exact code path and line numbers from the finding
- Fails on the current implementation, confirming the bug exists
- Uses mocking/monkeypatching to isolate from external services (e.g., git, file I/O)
- Includes the finding description in the test docstring for traceability

**Name the test file** `quality/test_regression.py`

**Each test should document its origin:**

```python
def test_normalize_categories_null_safety_missing():
    """[BUG from 2026-03-31-reviewer.md, Line 58]

    normalize_categories.py lacks a keyword rule for "null safety" / "null check".
    Raw category strings like "null check", "null safety", "NPE" fall through to the
    fallback rule and are miscategorized. This affects 103 null safety defects in
    the library, skewing category-level detection rate analysis.

    Expected: normalize("null check") == "null safety"
    Actual: normalize("null check") != "null safety"
    """
    from tooling.normalize_categories import normalize

    # These raw categories should all map to "null safety"
    test_cases = ["null check", "null safety", "NPE", "null dereference", "null guard"]
    for raw in test_cases:
        result = normalize(raw)
        assert result == "null safety", f"normalize('{raw}') returned '{result}', expected 'null safety'"
```

**Run the tests and report results:**

```
| Finding | Test | Result | Confirmed? |
|---------|------|--------|------------|
| Missing null safety rule | test_normalize_categories_null_safety_missing | FAILED (expected) | YES — bug confirmed |
| Subprocess error handling | test_extract_defect_data_git_failure | FAILED (expected) | YES — bug confirmed |
```

If a test passes unexpectedly, investigate — either the finding was a false positive, or the test doesn't exercise the right code path.

---

## Execution Notes

- Estimated time for code review: 2–3 hours (for 7 focus areas)
- Estimated time for regression tests: 1–2 hours (write and run)
- Total: 3–5 hours per review cycle

Do not rush the code review. The goal is to catch data integrity bugs that would invalidate analysis. Take time to read function bodies and trace data flow.
