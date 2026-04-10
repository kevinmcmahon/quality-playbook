# Verification Checklist (Phase 3: Verify)

Before declaring the quality playbook complete, check every benchmark below. If any fails, go back and fix it.

## Self-Check Benchmarks

### 1. Test Count

Calculate the heuristic target: (testable spec sections) + (QUALITY.md scenarios) + (defensive patterns from Step 5).

- **Well below target** → You likely missed spec requirements or skimmed defensive patterns. Go back and check.
- **Near target** → Review whether you tested negative cases and boundaries.
- **Above target** → Fine, as long as every test is meaningful. Don't pad to hit a number.

### 2. Scenario Coverage

Count the scenarios in QUALITY.md. Count the scenario test functions in your functional test file. The numbers must match exactly.

### 3. Cross-Variant Coverage

If the project handles N input variants, what percentage of tests exercise all N?

Count: tests that loop or parametrize over all variants / total tests.

**Heuristic: ~30%.** If well below, look for single-variant tests that should be parametrized. Common candidates: structural completeness, identity verification, required field presence, data relationships, semantic correctness. The exact percentage matters less than ensuring cross-cutting properties are tested across all variants.

### 4. Boundary and Negative Test Count

Count the defensive patterns from Step 5. Count your boundary/negative tests. The ratio should be close to 1:1. If significantly lower, write more tests targeting untested defensive patterns.

### 5. Assertion Depth

Scan your assertions. How many are presence checks vs. value checks? If more than half are presence-only (`assert x is not None`, `assert x in output`), strengthen them to check actual values.

### 6. Layer Correctness

For each test, ask: "Am I testing the *requirement* or the *mechanism*?" If any test only asserts that a specific error type is raised without also verifying pipeline output, it's testing the mechanism. Rewrite to test the outcome.

### 7. Mutation Validity

For every test that mutates a fixture, verify the mutation value is in the "Accepts" column of your Step 5b schema map. If any mutation uses a type the schema rejects, the test fails with a validation error instead of testing defensive code. Fix it.

### 8. All Tests Pass — Zero Failures AND Zero Errors

Run the test suite using the project's test runner:

- **Python:** `pytest quality/test_functional.py -v`
- **Scala:** `sbt "testOnly *FunctionalSpec"`
- **Java:** `mvn test -Dtest=FunctionalTest` or `gradle test --tests FunctionalTest`
- **TypeScript:** `npx jest functional.test.ts --verbose`
- **Go:** `go test -v` targeting the generated test file's package — use the project's existing module and package layout
- **Rust:** `cargo test` targeting the generated test — either the integration test target in `tests/` or inline `#[cfg(test)]` tests, matching the project's conventions

**Check for both failures AND errors.** Most test frameworks distinguish between test failures (assertion errors) and test errors (setup failures, missing fixtures, import/resolution errors, exceptions during initialization). Both are broken tests. A common mistake: generating tests that reference shared fixtures or helpers that don't exist. These show up as setup errors, not assertion failures — but they are just as broken.

**Expected-failure (xfail) tests do not count against this benchmark.** Regression tests in `quality/test_regression.*` use expected-failure markers (`@pytest.mark.xfail(strict=True)`, `@Disabled`, `t.Skip`, `#[ignore]`) to confirm that known bugs are still present. These tests are *supposed* to fail — that's the point. The "zero failures and zero errors" benchmark applies to `quality/test_functional.*` (the functional test suite), not to `quality/test_regression.*` (the bug confirmation suite). If your test runner reports failures from xfail-marked regression tests, that's correct behavior, not a benchmark violation. If an xfail test unexpectedly *passes*, that means the bug was fixed and the xfail marker should be removed — treat that as a finding to investigate, not a test failure.

After running, check:
- All tests passed — count must equal total test count
- Zero failures
- Zero errors/setup failures

If there are setup errors, you forgot to create the fixture/setup file or you referenced helpers that don't exist. Go back and either create them or rewrite the tests to be self-contained.

### 9. Existing Tests Unbroken

Run the project's full test suite (not just your new tests). Your new files should not break anything.

## Documentation Verification

### 10. QUALITY.md Scenarios Reference Real Code and Label Sources

Every scenario should mention actual function names, file names, or patterns that exist in the codebase. Grep for each reference to confirm it exists.

If working from non-formal requirements, verify that each scenario and test includes a requirement tag using the canonical format: `[Req: formal — README §3]`, `[Req: inferred — from validate_input() behavior]`, `[Req: user-confirmed — "must handle empty input"]`. Inferred requirements should be flagged for user review in Phase 4.

### 11. RUN_CODE_REVIEW.md Is Self-Contained

An AI with no prior context should be able to read it and perform a useful review. Check: does it list bootstrap files? Does it have specific focus areas? Are the guardrails present?

### 12. RUN_INTEGRATION_TESTS.md Is Executable and Field-Accurate

Every command should work. Every check should have a concrete pass/fail criterion — not "verify it looks right" but a specific expected result.

**Verify quality gates were written from a Field Reference Table, not from memory.** Check that:

1. A Field Reference Table exists in RUN_INTEGRATION_TESTS.md with a row for every field in every schema
2. **Field count check:** For each schema, count the fields in the actual schema file and count the rows in your table. If the numbers don't match, you missed fields or invented fields. The most common failure: a schema has 8 fields but the table only has 2-3 "important" ones.
3. **Character-for-character check:** Re-read each schema file now and compare every field name in your table against the file contents. `document_id` ≠ `doc_id`. `sentiment_score` ≠ `sentiment`. `classification` ≠ `category`.
4. Every type and constraint matches the schema (`float 0-1` is not `int 0-100`, `string enum` is not `integer`)

If any field name, count, or type is wrong, fix it before proceeding. The table is the foundation — if the table is wrong, every quality gate built from it is wrong.

### 13. RUN_SPEC_AUDIT.md Prompt Is Copy-Pasteable

The definitive audit prompt should work when pasted into Claude Code, Cursor, and Copilot without modification (except file reference syntax).

### 14. Structured Output Schemas Are Valid and Conformant

Verify that `RUN_TDD_TESTS.md` and `RUN_INTEGRATION_TESTS.md` both instruct the agent to produce:
- JUnit XML output using the framework's native reporter (pytest `--junitxml`, gotestsum `--junitxml`, Maven Surefire reports, `jest-junit`, `cargo2junit`)
- A sidecar JSON file (`tdd-results.json` or `integration-results.json`) in `quality/results/`

Check that each protocol's JSON schema includes all mandatory fields:
- **tdd-results.json:** `schema_version`, `skill_version`, `date`, `project`, `bugs`, `summary`. Per-bug: `id`, `requirement`, `red_phase`, `green_phase`, `verdict`, `fix_patch_present`, `writeup_path`.
- **integration-results.json:** `schema_version`, `skill_version`, `date`, `project`, `recommendation`, `groups`, `summary`, `uc_coverage`. Per-group: `group`, `name`, `use_cases`, `result`.

Verify that the protocol does NOT contain flat command-list schemas (a `"results"` or `"commands_run"` array without `"groups"` is non-conformant). Verify that verdict/result enum values use only the allowed values defined in SKILL.md (e.g., `"TDD verified"`, `"red failed"`, `"green failed"`, `"confirmed open"` for TDD verdicts; `"pass"`, `"fail"`, `"skipped"`, `"error"` for integration results; `"SHIP"`, `"FIX BEFORE MERGE"`, `"BLOCK"` for recommendations). The TDD verdict `"skipped"` is deprecated — use `"confirmed open"` with `red_phase: "fail"` and `green_phase: "skipped"` instead. The TDD summary must include a `confirmed_open` count alongside `verified`, `red_failed`, and `green_failed`.

Both sidecar JSON templates must use `schema_version: "1.1"` (v1.1 change: `verdict: "skipped"` deprecated in favor of `"confirmed open"`). Both protocols must include a **post-write validation step** instructing the agent to reopen the sidecar JSON after writing it and verify required fields, enum values, and no extra undocumented root keys.

### 15. Patch Validation Gate Is Executable

For each confirmed bug with patches, verify:
1. The `git apply --check` commands specified in the patch validation gate use the correct patch paths (`quality/patches/BUG-NNN-*.patch`)
2. The compile/syntax check command matches the project's actual build system — not a generic placeholder
3. For interpreted languages (Python, JavaScript), the gate specifies the appropriate syntax check (`python -m py_compile`, `node --check`, `pytest --collect-only`, or equivalent)
4. The gate includes a temporary worktree or stash-and-revert instruction to comply with the source boundary rule

### 16. Regression Test Skip Guards Are Present

Grep `quality/test_regression.*` for the language-appropriate skip/xfail mechanism. Every test function must have a guard:
- Python: `@pytest.mark.xfail` or `@unittest.expectedFailure`
- Go: `t.Skip(`
- Java: `@Disabled`
- Rust: `#[ignore]`
- TypeScript/JavaScript: `test.failing(`, `test.fails(`, or `it.skip(`

A regression test without a skip guard will cause unexpected failures when the test suite runs on unpatched code. Every guard must reference the bug ID (BUG-NNN format) and the fix patch path.

### 17. Integration Group Commands Pass Pre-Flight Discovery

For each integration test group command in `RUN_INTEGRATION_TESTS.md`, verify that the command discovers at least one test using the framework's dry-run mode (`pytest --collect-only`, `go test -list`, `vitest list`, `jest --listTests`, `cargo test -- --list`). A group whose command fails discovery will produce a `covered_fail` result that masks a selector bug as a code bug. If a command cannot be validated (no dry-run mode available), note the limitation.

### 18. Version Stamps Present on All Generated Files

Grep every generated Markdown file in `quality/` for the attribution line: `Generated by [Quality Playbook]`. Grep every generated code file for `Generated by Quality Playbook`. Every file must have the stamp with the correct version number. Files without stamps are not traceable to the tool and version that created them. **Exemptions:** sidecar JSON files (use `skill_version` field), JUnit XML files (framework-generated), and `.patch` files (stamp would break `git apply`). For Python files with shebang or encoding pragma, verify the stamp comes after the pragma, not before.

### 19. Enumeration Completeness Checks Performed

Verify that the code review (Pass 1 and Pass 2) performed mechanical two-list enumeration checks wherever the code uses `switch`/`case`, `match`, or if-else chains to dispatch on named constants. For each such check, the review must show: (a) the list of constants defined in headers/enums/specs, (b) the list of case labels actually present in the code, (c) any gaps. A review that claims "the whitelist covers all values" or "all cases are handled" without showing the two-list comparison is non-conformant — this is the specific hallucination pattern the check prevents.

### 20. Bug Writeups Generated for TDD-Verified Bugs

For each bug with `verdict: "TDD verified"` in `tdd-results.json`, verify that a corresponding `quality/writeups/BUG-NNN.md` file exists and that `tdd-results.json` has a non-null `writeup_path` for that bug. Each writeup must include: summary, spec reference, code citation, observable consequence, fix diff, and test description. A TDD-verified bug without a writeup is incomplete.

### 21. Triage Verification Probes Include Executable Evidence

Open the triage report (`quality/spec_audits/YYYY-MM-DD-triage.md`). For every finding that was confirmed or rejected via a verification probe, verify that the triage entry includes a test assertion (not just prose reasoning). Rejections must include a PASSING assertion proving the finding is wrong. Confirmations must include a FAILING assertion proving the bug exists. Every assertion must cite an exact line number. A triage decision based on prose reasoning alone ("lines 3527-3528 explicitly preserve X") without a mechanical assertion is non-conformant.

### 22. Enumeration Lists Extracted From Code, Not Copied From Requirements

When the code review includes an enumeration check (e.g., "case labels present in function X"), verify that the code-side list includes per-item line numbers from the actual source. If the list matches the requirements list word-for-word without line numbers, the enumeration was likely copied rather than extracted and must be redone. Also verify that the triage pre-audit spot-checks report the actual contents of cited lines ("line 3527 contains `default:`") rather than merely confirming claims ("line 3527 preserves RING_RESET").

## Quick Checklist Format

Use this as a final sign-off:

- [ ] Test count near heuristic target (spec sections + scenarios + defensive patterns)
- [ ] Scenario test count matches QUALITY.md scenario count
- [ ] Cross-variant tests ~30% of total (every cross-cutting property covered)
- [ ] Boundary tests ≈ defensive pattern count
- [ ] Majority of assertions check values, not just presence
- [ ] All tests assert outcomes, not mechanisms
- [ ] All mutations use schema-valid values
- [ ] All new tests pass (zero failures AND zero errors — check for fixture errors)
- [ ] All existing tests still pass
- [ ] QUALITY.md scenarios reference real code and include `[Req: tier — source]` tags
- [ ] If using inferred requirements: all `[Req: inferred — ...]` items are flagged for user review
- [ ] Code review protocol is self-contained
- [ ] Integration test quality gates were written from a Field Reference Table (not memory)
- [ ] Integration tests have specific pass criteria
- [ ] Spec audit prompt is copy-pasteable and uses `[Req: tier — source]` tag format
- [ ] Structured output schemas include all mandatory fields and valid enum values
- [ ] Patch validation gate uses correct commands for the project's build system
- [ ] Every regression test has a skip/xfail guard referencing the bug ID
- [ ] Integration group commands pass pre-flight discovery (dry-run finds tests)
- [ ] Every generated file has a version stamp with correct version number
- [ ] Enumeration completeness checks show two-list comparisons (not just assertions of coverage)
- [ ] Every TDD-verified bug has a writeup at `quality/writeups/BUG-NNN.md`
- [ ] Triage verification probes include test assertions (not just prose) for confirmations and rejections
- [ ] Enumeration code-side lists include per-item line numbers (not copied from requirements)
