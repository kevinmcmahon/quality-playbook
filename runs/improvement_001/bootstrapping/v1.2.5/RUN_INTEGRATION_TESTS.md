# Integration Test Protocol: Quality Playbook Benchmark (QPB)

## Purpose

Integration tests verify that the QPB tooling scripts work correctly end-to-end: extracting data from real repositories, normalizing categories, and assembling the master DEFECT_LIBRARY.md. These tests use actual repository clones and real commit data, catching integration issues that unit tests would miss.

**Key principle:** Integration tests use real data. They verify that the tools produce correct output when given authentic input from the 50 cloned repositories and 2,564 real defects.

## Prerequisites

- All 50 repositories must be cloned in `repos/` (~3.6GB)
- Each repo must have full git history (not shallow clones)
- Script dependencies must be installed: `python3`, `git`, standard library only (no pip packages required)
- DEFECT_LIBRARY.md and per-repo description files must exist (`dataset/defects/<repo>/`)

## Test Setup

Run these tests from the QPB repository root:

```bash
cd /path/to/QPB
python3 -m pytest quality/test_integration.py -v
```

Or individually:

```bash
python3 quality/test_integration.py TestExtractDefectData::test_extract_all_defects
```

## Integration Tests

### Test Suite 1: Extract Defect Data (`tooling/extract_defect_data.py`)

These tests verify that `extract_defect_data.py` correctly reads from all repositories and produces complete output.

#### Test 1.1: Script Runs to Completion on All 2,564 Defects

**What it tests:** The extraction script processes all 2,564 defects without errors, and produces output for each.

**How:**
1. Run `python3 tooling/extract_defect_data.py --library dataset/DEFECT_LIBRARY.md --repos repos/ --output /tmp/qpb_test_extract.json`
2. Verify exit code is 0
3. Load the output JSON file
4. Count entries: should have 2,564 (one per defect in DEFECT_LIBRARY.md)
5. For each defect ID in DEFECT_LIBRARY.md, verify an entry exists in the output JSON

**Expected result:** PASS — All 2,564 defects have extraction data.

**Failure indicates:** Silent data loss during extraction (missing prefix mapping, repo not found, commit not found but not reported).

---

#### Test 1.2: Extracted Data Contains All Required Fields

**What it tests:** Each extracted defect entry has: commit_message, files_changed (non-empty list), diff_stat.

**How:**
1. Load extraction output from Test 1.1
2. For each entry:
   - Assert "commit_message" key exists and is non-empty string
   - Assert "files_changed" key exists and is a non-empty list
   - Assert each file in files_changed is a non-empty string
   - Assert "diff_stat" key exists (if applicable for the defect)

**Expected result:** PASS — All entries have required fields.

**Failure indicates:** Incomplete extraction (missing fields means downstream analysis can't work with the data).

---

#### Test 1.3: Extracted Data is Valid JSON

**What it tests:** Output file is valid JSON that can be parsed without errors.

**How:**
1. Load extraction output
2. Attempt `json.loads()` on the file content
3. Verify no parsing errors
4. Check that top-level structure is a dict with defect IDs as keys

**Expected result:** PASS — File is valid, parseable JSON.

**Failure indicates:** Corrupted output file (malformed JSON, incomplete write).

---

#### Test 1.4: Commit SHAs are Resolvable in Cloned Repos

**What it tests:** For a sample of 100 defects across all 50 repos, the fix_commit and pre_fix_commit values can be resolved with `git rev-parse` in the respective repository.

**How:**
1. Sample 100 defects evenly from DEFECT_LIBRARY.md (every 26th defect)
2. For each sampled defect:
   - Look up its prefix in PREFIX_MAP (map prefix to repo directory)
   - In that repo, run `git rev-parse <fix_commit>`
   - Verify exit code is 0 (commit exists)
   - Run `git rev-parse <pre_fix_commit>`
   - Verify exit code is 0
   - Run `git rev-parse <fix_commit>^` and verify it equals `<pre_fix_commit>` (parent relationship)

**Expected result:** PASS — All sampled commits resolve and parent relationship is correct.

**Failure indicates:** Commit data is invalid, corrupted, or doesn't match repos (defects non-evaluable).

---

### Test Suite 2: Normalize Categories (`tooling/normalize_categories.py`)

These tests verify that category normalization produces the expected canonical categories.

#### Test 2.1: All 2,564 Defects Normalize to Canonical Categories

**What it tests:** Running `normalize_categories.py` on DEFECT_LIBRARY.md produces a version where all categories are one of 14 canonical labels.

**How:**
1. Run `python3 tooling/normalize_categories.py --library dataset/DEFECT_LIBRARY.md`
2. Load the updated DEFECT_LIBRARY.md
3. For each defect, extract the category field
4. Verify category is in: {error handling, validation gap, configuration error, type safety, state machine gap, concurrency issue, serialization, API contract violation, protocol violation, null safety, silent failure, security issue, SQL error, missing boundary check}

**Expected result:** PASS — All 2,564 categories normalized.

**Failure indicates:** Non-canonical categories remain (normalization rules incomplete or buggy).

---

#### Test 2.2: Normalization is Deterministic

**What it tests:** Running the normalization script twice produces identical output (same input = same output).

**How:**
1. Run normalization (Test 2.1)
2. Save the result to a temp file
3. Run normalization again
4. Compare the two outputs (file comparison or line-by-line hash)
5. Verify they are identical

**Expected result:** PASS — Identical output on repeated runs.

**Failure indicates:** Non-deterministic behavior (randomness, file I/O race conditions, or state pollution).

---

#### Test 2.3: Category Distribution is Reasonable (No Zero-Count Categories)

**What it tests:** Each of the 14 canonical categories has at least 1 defect after normalization.

**How:**
1. Load normalized DEFECT_LIBRARY.md
2. Count defects per category
3. For each canonical category, verify count > 0

**Expected result:** PASS — All 14 categories represented.

**Failure indicates:** A normalization rule is broken (all defects in a category fell through to wrong rule). May also indicate insufficient defect coverage.

---

#### Test 2.4: Specific Defects Normalize Correctly

**What it tests:** Known difficult-to-categorize defects normalize to the correct canonical category.

**How:**
1. Select 10 test cases with known correct categories (from code review or manual audit)
2. For each test case:
   - Create a defect entry with that raw category string
   - Run normalization
   - Verify result matches expected canonical category

Example test cases:
- "null check" → "null safety"
- "race condition" → "concurrency issue"
- "SQL injection" → "security issue"
- "type mismatch" → "type safety"

**Expected result:** PASS — All test cases normalize correctly.

**Failure indicates:** Specific normalization rules are incorrect or have wrong precedence.

---

### Test Suite 3: Assemble DEFECT_LIBRARY.md (`tooling/assemble_v8.py`)

These tests verify that the assembly script combines mining data into the final DEFECT_LIBRARY.md.

#### Test 3.1: Assembly Script Runs to Completion

**What it tests:** The assembly script executes without errors and produces a DEFECT_LIBRARY.md file.

**How:**
1. Back up existing DEFECT_LIBRARY.md
2. Run `python3 tooling/assemble_v8.py` (assuming it takes standard input or has default paths)
3. Verify exit code is 0
4. Verify new DEFECT_LIBRARY.md file exists and is non-empty
5. Restore original DEFECT_LIBRARY.md

**Expected result:** PASS — Assembly completes without errors.

**Failure indicates:** Assembly script is broken or missing dependencies.

---

#### Test 3.2: Assembled Library Has Correct Row Count

**What it tests:** The assembled DEFECT_LIBRARY.md has exactly 2,564 data rows (plus headers).

**How:**
1. Load assembled DEFECT_LIBRARY.md
2. Count data rows (after header/separator)
3. Verify count == 2,564

**Expected result:** PASS — Correct row count.

**Failure indicates:** Data loss during assembly, or previous assembly was incomplete.

---

#### Test 3.3: Assembled Library Format Matches Spec

**What it tests:** Every row in the assembled library has exactly 8 columns and all required fields are non-empty.

**How:**
1. Load assembled DEFECT_LIBRARY.md
2. For each row:
   - Count columns (pipe-separated)
   - Verify 8 columns
   - Verify ID is non-empty and matches PREFIX-NN format
   - Verify fix_commit and pre_fix_commit are 40-char SHAs
   - Verify category is non-empty
3. Flag any malformed rows

**Expected result:** PASS — All rows well-formed.

**Failure indicates:** Assembly produced corrupted data.

---

### Test Suite 4: Cross-Document Consistency

These tests verify that DEFECT_LIBRARY.md and per-repo description files are consistent.

#### Test 4.1: Defect Count Consistency by Prefix

**What it tests:** For each prefix (repo), the count of defects in DEFECT_LIBRARY.md matches the count in the per-repo description file.

**How:**
1. Load DEFECT_LIBRARY.md, group by prefix (first part of defect ID)
2. Count defects per prefix
3. For each prefix:
   - Check if `dataset/defects/<repo>/defects.md` exists (map prefix to repo dir)
   - Load the per-repo file
   - Count entries
   - Compare counts

**Expected result:** PASS — Counts match for all repos.

**Failure indicates:** Data loss during per-repo file generation (missing entries).

---

#### Test 4.2: All Defects Have Corresponding Per-Repo Entries

**What it tests:** Every defect ID in DEFECT_LIBRARY.md has a corresponding entry in its per-repo description file.

**How:**
1. Load DEFECT_LIBRARY.md
2. For each defect:
   - Extract ID (e.g., GH-03)
   - Load corresponding per-repo file (e.g., `dataset/defects/cli/defects.md`)
   - Search for the defect ID in the per-repo file
   - Verify found

**Expected result:** PASS — All defects found in per-repo files.

**Failure indicates:** Per-repo files are incomplete or have wrong format.

---

#### Test 4.3: Per-Repo Description Quality (Sample Check)

**What it tests:** A sample of per-repo description entries contain the required fields: commit message, files changed, diff stat, playbook angle.

**How:**
1. Sample 10 per-repo files (or all if fewer than 10)
2. For each sampled file, randomly select 1 entry
3. Check that entry includes:
   - Commit message or commit hash
   - List of files changed
   - Playbook angle or detection hint
4. Flag any missing or truncated fields

**Expected result:** PASS — All sampled entries complete.

**Failure indicates:** Per-repo files have incomplete data (may be generator issue or copy-paste error).

---

### Test Suite 5: End-to-End Workflow

These tests verify the entire pipeline: extract → normalize → assemble.

#### Test 5.1: Full Pipeline: Extract → Normalize → Verify

**What it tests:** Running extract_defect_data, then normalize_categories produces a valid, complete DEFECT_LIBRARY.md.

**How:**
1. Run extract_defect_data.py → produces defect_data.json
2. Run normalize_categories.py → updates DEFECT_LIBRARY.md
3. Verify:
   - No errors in either script
   - All 2,564 defects in output
   - All categories normalized
   - Format is valid (8 columns, required fields non-empty)

**Expected result:** PASS — Full pipeline succeeds.

**Failure indicates:** Pipeline has integration issues (one script's output breaks the next).

---

#### Test 5.2: Evaluation Results Schema Validation (Mock)

**What it tests:** Evaluation results would conform to DETECTION_RESULTS.md schema.

**How:**
1. Create synthetic evaluation results (5–10 mock results with valid schema)
2. Create synthetic results with schema violations (invalid score, missing defect_id, etc.)
3. Validate the correct results: should pass validation
4. Validate the incorrect results: should fail validation

**Expected result:** PASS — Validation correctly accepts good results and rejects bad ones.

**Failure indicates:** Schema validation logic (if any) is not catching malformed results.

---

## Test Data

For integration tests, use actual data:

- **Real repositories:** All 50 repos in `repos/` (or skip tests for missing repos with `pytest.skip()`)
- **Real defects:** All 2,564 defects from DEFECT_LIBRARY.md
- **Real commits:** Actual SHAs from repo history

Do not mock git operations or use synthetic data — the purpose is to catch real integration issues.

## Test Execution

Run all integration tests:

```bash
python3 -m pytest quality/test_integration.py -v
```

Run a specific test suite:

```bash
python3 -m pytest quality/test_integration.py::TestExtractDefectData -v
```

Run a specific test:

```bash
python3 -m pytest quality/test_integration.py::TestExtractDefectData::test_extract_all_defects -v
```

## Timeout and Resource Limits

- Extract script: 5-minute timeout (processes 2,564 defects across 50 repos)
- Normalize script: 30-second timeout (in-memory operation)
- Assembly script: 1-minute timeout
- Commit verification (per test): 5-second timeout per commit (may need to increase if repos are slow)

## Failure Handling

If an integration test fails:

1. **Determine the root cause:** Is it a script bug, missing data, or environmental issue?
   - If missing repos: `pytest.skip()` that test
   - If script error: check stderr for the error message
   - If data issue: investigate DEFECT_LIBRARY.md or per-repo files

2. **Debug with explicit output:**
   ```bash
   # Run extraction with verbose output
   python3 tooling/extract_defect_data.py --library dataset/DEFECT_LIBRARY.md --repos repos/ --output /tmp/test.json 2>&1 | head -50
   ```

3. **Check logs:** If scripts log errors, inspect those logs for hints about which defect failed.

4. **Isolate the defect:** If a specific defect ID is failing, test it in isolation:
   ```bash
   # For example, test defect GH-03
   cd repos/cli
   git rev-parse abc123...  # Use fix_commit from DEFECT_LIBRARY.md
   ```

5. **Fix and re-test:** Once the issue is resolved, re-run the integration test.

## Performance Notes

- Full integration test suite: ~10–15 minutes (depending on repo I/O and script performance)
- Extract script alone: ~2 minutes for all 2,564 defects
- Normalize script: <1 second
- Defect count verification: <5 seconds

If tests are taking significantly longer, investigate:
- Disk I/O (repos on slow storage?)
- Git performance (check if repos are fully cloned, not shallow)
- Script performance (check for N² loops or inefficient git operations)

## Integration with CI/CD

When running in CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Clone QPB Repositories
  run: |
    # Clone all 50 repos (one-time setup or cached)
    python3 scripts/clone_repos.py

- name: Run Integration Tests
  run: |
    cd QPB
    python3 -m pytest quality/test_integration.py -v --tb=short
```

For CI/CD, consider:
- Caching the `repos/` directory (clones are large, ~3.6GB)
- Running a subset of tests on pull requests (e.g., only tests that don't require all repos)
- Running full test suite on merge to main branch

## Maintenance

Integration tests must be updated when:

- New repositories are added to the dataset (add new tests for their data)
- The 14 canonical categories change (update Test 2 category set)
- The DEFECT_LIBRARY.md format changes (update column count checks)
- New tooling scripts are added (add integration tests for them)

Keep integration tests in sync with the actual project structure and tools.
