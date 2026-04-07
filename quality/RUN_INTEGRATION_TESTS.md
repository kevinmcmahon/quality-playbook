# Integration Test Protocol: Quality Playbook v1.3.8

## Working Directory

All commands in this protocol use **relative paths from the project root**. Run everything from the repository root.

## Safety Constraints

- DO NOT edit source files while running the protocol.
- ONLY write logs or copied test repos under `quality/results/`.
- If a live CLI-agent execution fails, record the failure and stop; do not silently patch around it.

## Pre-Flight Check

Before running integration tests, verify:

- [ ] `python3` is available for the generated quality suite.
- [ ] `gh` is installed if you plan to use GitHub Copilot CLI for the skill execution test.
- [ ] The repository has a clean destination for a scratch install test (for example `quality/results/integration-scratch/`).
- [ ] `docs_gathered/` is present if running the with-docs variant.

## Field Reference Table (built from artifact templates, not memory)

### Artifact: `quality/PROGRESS.md`
Schema source: `.github/skills/SKILL.md` lines 271-321

| Field | Type | Constraints |
|-------|------|-------------|
| Started | datetime string | must be present in Run metadata |
| Project | string | must name the repository under test |
| Skill version | string | must match the skill version used for the run |
| With docs | `yes` or `no` | must reflect actual `docs_gathered/` presence |
| Phase completion | checklist section | must track `1`, `2`, `2b`, `2c`, `2d`, `3` |
| Terminal Gate Verification | section | must contain the persisted BUG-count arithmetic statement |
| Source | string | BUG tracker column |
| File:Line | string | BUG tracker column with traceable evidence |
| Description | string | BUG tracker column |
| Severity | string | BUG tracker column |
| Closure Status | string | BUG tracker column; `confirmed open (...)`, `fixed (test passes)`, or `exempt (...)` |
| Test/Exemption | string | BUG tracker column |

### Artifact: `quality/VERSION_HISTORY.md`
Schema source: `references/requirements_pipeline.md` lines 361-368

| Field | Type | Constraints |
|-------|------|-------------|
| Version | string | `vX.Y` |
| Date | ISO date | must be present |
| Model | string | generating/refining model |
| Author | string | provenance of the change |
| Reqs | integer | current requirement count |
| Summary | string | concise description of the change |

### Artifact: `quality/spec_audits/*-triage.md`
Schema source: `references/spec_audit.md` lines 68-126

| Field | Type | Constraints |
|-------|------|-------------|
| Model | string | each council participant |
| Status | string | fresh report / timeout / unusable |
| Effective council | string | `3/3`, `2/3`, or `1/3` semantics must be explicit |
| Found By | string | auditor agreement level for each triaged finding |
| Confidence | string | must reflect actual agreement level |
| Action | string | triage action for the finding |

## Test Matrix

| Check | Method | Pass Criteria |
|-------|--------|---------------|
| Functional quality suite | `python3 -m unittest discover -s quality -p 'test_*.py' -v` | Functional tests pass; regression tests are only expected failures |
| Artifact structural check | Verify generated files and directories | Every required artifact exists and is non-empty |
| PROGRESS metadata check | Read `quality/PROGRESS.md` | All six tracked phases are checked off; `With docs` matches reality |
| BUG tracker closure check | Compare BUG rows to regression test names and exemptions | Every BUG row has closure evidence; terminal-gate counts reconcile |
| Review/audit substance check | Inspect `quality/code_reviews/` and `quality/spec_audits/` | Review and triage files contain substantive findings, not empty templates |
| Optional baseline vs with-docs comparison | Run the protocol twice in a scratch repo | With-docs run yields requirement count >= baseline and no weaker artifact coverage |

## Skill Integration Test Protocol

### Prerequisites

- A CLI agent is installed and configured (for example `gh copilot`)
- A scratch repo exists under `quality/results/integration-scratch/`
- The scratch repo starts without a `quality/` directory

### Execution

```bash
rm -rf quality/results/integration-scratch
mkdir -p quality/results/integration-scratch
cp -R . quality/results/integration-scratch/repo
cd quality/results/integration-scratch/repo
rm -rf quality

gh copilot -p "Read .github/skills/SKILL.md and its reference files in .github/skills/references/. Execute the quality playbook for this project. Additional documentation for this project has been gathered in docs_gathered/ — read it during Phase 1 exploration." \
  > quality_run.output.txt 2>&1
```

### Structural Verification

```bash
for f in quality/QUALITY.md quality/REQUIREMENTS.md quality/CONTRACTS.md \
         quality/COVERAGE_MATRIX.md quality/COMPLETENESS_REPORT.md \
         quality/PROGRESS.md quality/RUN_CODE_REVIEW.md \
         quality/RUN_INTEGRATION_TESTS.md quality/RUN_SPEC_AUDIT.md \
         quality/REVIEW_REQUIREMENTS.md quality/REFINE_REQUIREMENTS.md \
         quality/VERSION_HISTORY.md quality/REFINEMENT_HINTS.md AGENTS.md; do
  [ -s "$f" ] || echo "FAIL: $f missing or empty"
done

[ -s quality/test_functional.py ] || echo "FAIL: missing functional test file"
[ -s quality/test_regression.py ] || echo "FAIL: missing regression test file"

grep -q "## Terminal Gate Verification" quality/PROGRESS.md || echo "FAIL: terminal gate section missing"
grep -q "BUG tracker has" quality/PROGRESS.md || echo "FAIL: terminal gate arithmetic missing"
grep -q "## Pre-audit docs validation" quality/spec_audits/*-triage.md || echo "FAIL: triage baseline missing"
```

## Quality Checks

1. **Metadata fidelity:** `With docs` matches the actual presence of `docs_gathered/`.
2. **Closure fidelity:** BUG tracker rows, regression tests, and terminal-gate arithmetic agree.
3. **Mirror fidelity:** Root and `.github/skills/` files remain identical.
4. **Audit fidelity:** The triage explicitly logs effective council size and docs validation.
5. **Versioning fidelity:** Requirement count in `REQUIREMENTS.md`, `COVERAGE_MATRIX.md`, and `VERSION_HISTORY.md` stays consistent.

## Execution UX

### Phase 1: The Plan

Before running anything, present:

| # | Test | What It Checks | Est. Time |
|---|------|----------------|-----------|
| 1 | Functional quality suite | Generated docs and executable checks | ~5s |
| 2 | Artifact structural check | Required files and sections exist | ~5s |
| 3 | PROGRESS + BUG tracker check | Metadata and closure integrity | ~5s |
| 4 | Optional CLI skill execution | End-to-end self-bootstrap in a scratch repo | 1-5m |

### Phase 2: Progress

Use one-line updates:

- `✓ Functional quality suite — PASS`
- `✗ Artifact structural check — FAIL: missing triage baseline`
- `⧗ CLI skill execution — running`

### Phase 3: Results

Summarize:

| # | Test | Result | Notes |
|---|------|--------|-------|
| 1 | Functional quality suite | PASS / FAIL | ... |
| 2 | Artifact structural check | PASS / FAIL | ... |
| 3 | PROGRESS + BUG tracker check | PASS / FAIL | ... |
| 4 | CLI skill execution | PASS / FAIL / SKIPPED | ... |

**Recommendation:** SHIP IT / FIX FIRST / NEEDS INVESTIGATION

Save the detailed summary to `quality/results/YYYY-MM-DD-integration.md`.
