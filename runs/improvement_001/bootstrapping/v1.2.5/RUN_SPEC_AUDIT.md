# Council of Three Spec Audit Protocol: Quality Playbook Benchmark (QPB)

## Purpose

A spec audit is a static analysis where AI models read specifications and code, then compare them for divergence. Three independent models audit in parallel, and findings are triaged for confidence: findings all three models report are almost certainly real; findings by one model only need verification.

For QPB, the spec audit checks:
- Do the tooling scripts implement the methodology correctly?
- Does the DEFECT_LIBRARY.md format match the specification in METHODOLOGY.md?
- Are there undocumented features or phantom specifications?
- Do all 2,564 defects conform to the format spec and evaluation protocol?

## Why Three Models?

Different AI models have different blind spots. Cross-referencing three independent reviews catches defects that any single model would miss.

## The Definitive Audit Prompt

Give this prompt identically to three independent AI tools. For QPB, recommend:

1. **Claude Opus** (strong on architecture, data flow, cross-function consistency)
2. **GPT-4o or GPT-5** (strong on edge cases, boundary conditions)
3. **Gemini 2.5 Pro** (independent verification, different training data)

---

## SPEC AUDIT PROMPT FOR QPB

```
## Context: Quality Playbook Benchmark (QPB)

You are the Tester. Your job is to compare the actual code and data against the specifications,
and report divergences, missing implementations, and undocumented features.

### Specification Documents (Read First)

1. dataset/METHODOLOGY.md — Evaluation protocol, defect mining rules, scoring rubric, data format spec
2. dataset/DEFECT_LIBRARY.md — Master defect index (first 100 rows, then spot-check 10 random rows)
3. AGENTS.md — Repository layout, key files, working definitions
4. dataset/DETECTION_RESULTS.md — Results schema and format spec
5. quality/QUALITY.md — Quality constitution, fitness-to-purpose scenarios (use these as scrutiny areas)

### Implementation Documents (Compare Against Spec)

1. tooling/extract_defect_data.py — Extracts commit data
2. tooling/normalize_categories.py — Normalizes categories to 14 canonical labels
3. tooling/assemble_v8.py — Assembles DEFECT_LIBRARY.md
4. dataset/defects/<repo>/defects.md — Per-repo description files (sample 3: cli/cli, curl, zookeeper)

### Requirement Confidence Tiers

Tag all findings with confidence:
- **[Req: formal — Spec]** — Specification document explicitly states this. Divergence is a real defect.
- **[Req: user-confirmed — AGENTS.md]** — Project documentation states this. Treat as authoritative.
- **[Req: inferred — Code exploration]** — Deduced from code behavior. Lower confidence. Report as NEEDS REVIEW.

### Rules for This Audit

1. **ONLY list defects.** Do not summarize what matches the spec. Time is valuable; only findings matter.

2. **For EVERY defect, cite specific file and line numbers.**
   - If you cannot cite a line number, do not include the finding.
   - For tooling scripts: use line numbers from the script.
   - For DEFECT_LIBRARY.md: use row number (after header).
   - For per-repo files: use entry ID and field name.

3. **Before claiming missing, grep the codebase.**
   - If you think a feature is absent, search for it. It may be in a different file.
   - If found elsewhere, that's a location defect, not a missing feature.

4. **Before claiming exists, read the actual function body.**
   - Don't assume a function works correctly based on its name.
   - Read the code to verify behavior.

5. **Classify each finding: MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM**
   - **MISSING** — Spec requires it, code doesn't implement it
   - **DIVERGENT** — Both spec and code address it, but they disagree
   - **UNDOCUMENTED** — Code does it, but spec doesn't mention it
   - **PHANTOM** — Spec describes it, but it's implemented differently than described
   - For findings against inferred requirements: add NEEDS REVIEW

### Project-Specific Scrutiny Areas (Force Deep Reading)

**1. Category Normalization Completeness**

Read normalize_categories.py lines 50–100 (the keyword-based rules). The spec (METHODOLOGY.md,
AGENTS.md) defines exactly 14 canonical categories. The script uses keyword matching to map raw
categories to canonical ones. Check:
- Are all 14 canonical categories explicitly mentioned in the rules?
- Is there a fallback rule for unmappable categories? What does it do?
- Is rule precedence documented? (Security first, validation gap as fallback?)
- Does the script handle edge cases: bold markdown (**), parentheses, slashes, unicode?

**2. Commit SHA Validation**

Read extract_defect_data.py lines 1–50. The spec (METHODOLOGY.md) requires every fix_commit and
pre_fix_commit to be a valid 40-character SHA and the pre-fix commit to be the immediate parent
of the fix commit. The script reads commit data from repos. Check:
- Does the script validate SHA format (40 hex characters)?
- Does it verify parent relationships (pre_fix_commit == git rev-parse FIX_COMMIT^)?
- What happens if a commit doesn't exist in a repo? Does it error or skip silently?
- Are error messages specific (which defect failed and why) or generic?

**3. Defect Count Consistency**

The spec requires all 2,564 defects to be present and accounted for. DEFECT_LIBRARY.md should have
2,564 rows. Per-repo description files (dataset/defects/<repo>/defects.md) should sum to 2,564.
Check:
- Does DEFECT_LIBRARY.md actually contain 2,564 rows? Count them.
- Do per-repo files exist for all prefixes that have defects in DEFECT_LIBRARY.md?
- Do per-repo file counts match DEFECT_LIBRARY.md counts by prefix?
- Are there any orphaned defects (in per-repo files but not in DEFECT_LIBRARY.md, or vice versa)?

**4. Evaluation Results Schema**

Read dataset/DETECTION_RESULTS.md and quality/QUALITY.md (Scenario 7). The spec defines the exact
format for evaluation results: one result per defect, with fields [run_id, defect_id, score, etc.].
Score must be one of exactly 4 values: direct_hit, adjacent, miss, not_evaluable. Check:
- Is the schema unambiguous? Could someone implement it differently than intended?
- Are all required fields documented?
- What happens if a result record has an invalid score value? Is it rejected, silently ignored, or cause an error?
- Is there a way to validate incoming result files against the schema?

**5. Per-Repo Description Format Consistency**

Sample 3 per-repo files (cli/cli, curl, zookeeper). The spec (AGENTS.md, sample files) defines that
per-repo files should include: commit message, files changed, diff stat, issue description, playbook angle.
Check:
- Do all three files use the same markdown format and column structure?
- Are all required fields present in all entries?
- Are there any entries with truncated or missing fields?
- Is the playbook angle field consistently populated, or are some entries empty?

**6. Prefix-to-Repo Mapping**

The spec (PROJECT_PLAN.md, AGENTS.md) defines a mapping of 55 prefixes to 50 repositories.
Read extract_defect_data.py PREFIX_MAP (lines 30–80). Check:
- Are all 55 prefixes in PREFIX_MAP?
- Does each prefix map to a correct (owner/repo) pair?
- Are there any typos in repo names?
- What happens if a defect has a prefix not in PREFIX_MAP? Error or silent skip?

**7. Severity and Category Values**

The spec (METHODOLOGY.md, DEFECT_LIBRARY.md) defines allowed values for severity (Critical, High, Medium, Low)
and 14 canonical categories. Check DEFECT_LIBRARY.md spot-sample (50 rows):
- Do all severity values match the spec? (exact casing: "Critical" not "critical")
- Do all categories match one of the 14 canonical labels?
- Are there any categories that are not canonical (e.g., custom raw categories that weren't normalized)?

### Output Format

For each defect, use this format:

```
### [filename.ext]

- **Line NNN:** [MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM] [Req: tier — source]
  Description. Why it matters.
  Spec says: [quote or reference]. Code does: [what actually happens].
```

**Example:**

```
### normalize_categories.py

- **Line 58:** MISSING [Req: formal — AGENTS.md, 14 canonical categories]
  The keyword rules list does not include "null safety" or "null check". Raw category strings
  matching null safety are not explicitly mapped to the canonical "null safety" category.
  This causes null safety defects to fall through to the fallback rule and be miscategorized.
  Spec says: "14 canonical categories including null safety". Code does: No explicit rule for null safety.

- **Line 70:** UNDOCUMENTED [Req: inferred — error recovery]
  The fallback rule (if no keyword matches) silently assigns the first canonical category
  instead of reporting an unmappable category. No error or warning is logged.
  This could hide data quality issues (raw categories that shouldn't exist).
  Spec says: No fallback behavior documented. Code does: Silently assign first category.

### extract_defect_data.py

- **Line 120:** DIVERGENT [Req: formal — METHODOLOGY.md, commit validation]
  The spec requires pre_fix_commit to be the immediate parent of fix_commit.
  The script extracts both SHAs but does not verify the parent relationship.
  It's possible (if data is corrupted) to have a pre_fix_commit that is not the parent.
  Spec says: "Pre-fix commit is always the immediate parent: git rev-parse FIX_COMMIT^".
  Code does: No verification of parent relationship; both SHAs read independently.

### DEFECT_LIBRARY.md

- **Row 847:** MISSING [Req: formal — METHODOLOGY.md, 8-column format]
  The spec requires 8 pipe-separated columns. This row has only 7 columns (missing playbook_angle).
  Spec says: "8 columns: ID, title, fix_commit, pre_fix_commit, severity, category, description, playbook_angle".
  Code does: Row 847 has 7 columns.
```

---

## Running the Audit

1. **Assign auditors:**
   - Auditor A: Claude (primary architect reviewer)
   - Auditor B: GPT-4o (edge-case reviewer)
   - Auditor C: Gemini (independent verification)

2. **Give each auditor the prompt above, identically.**

3. **Each auditor works independently** — no communication between audits until all reports are collected.

4. **Set a time limit:** 2–3 hours per auditor (to balance thoroughness with efficiency).

5. **Collect all three reports** in `quality/spec_audits/`:
   - `YYYY-MM-DD-claude.md`
   - `YYYY-MM-DD-gpt.md`
   - `YYYY-MM-DD-gemini.md`

---

## Triage Process

After all three models report, merge findings using this confidence table:

| Confidence | Found By | Action |
|------------|----------|--------|
| Highest | All three models | Almost certainly real — fix or update spec. |
| High | Two of three models | Likely real — verify and fix. |
| Needs verification | One model only | Could be real or hallucinated — deploy verification probe. |

### The Verification Probe

When models disagree on factual claims (e.g., "Line 120 verifies parent relationship" vs. "Line 120 does not verify"),
deploy a verification probe: give one auditor the disputed claim and ask it to read the code and report ground truth.
Never resolve factual disputes by majority vote — the majority can be wrong about what code actually does.

**Example probe:**

```
## Verification Probe

Two auditors claim line 120 of extract_defect_data.py verifies the parent relationship between
fix_commit and pre_fix_commit. One auditor claims it does not. Please read the actual code and report:

1. Does line 120 contain a git command or a comparison operation?
2. If it's a git command, what is it? (Show the command text.)
3. If it's a comparison, what two values are being compared?
4. Does the code verify that pre_fix_commit == git rev-parse FIX_COMMIT^? Yes or no?

Ground truth: [Your answer based on reading the code]
```

---

## Triage Output

Create `quality/spec_audits/YYYY-MM-DD-triage.md` with:

### Triaged Findings

| Finding | Models | Confidence | Category | Action |
|---------|--------|------------|----------|--------|
| Missing null safety rule | All 3 | Highest | Real code bug | Fix normalize_categories.py |
| Invalid SHA verification | 2 of 3 | High | Needs clarification | Deploy probe to verify |
| Silent fallback on unmapped categories | All 3 | Highest | Design question | Discuss with team |

### Categorize Each Confirmed Finding

For each confirmed finding, categorize it:

- **Spec bug** — Specification is wrong, code is correct → update spec
- **Design decision** — Code and spec both correct, but raises a question → discuss with team
- **Real code bug** — Code doesn't match spec → fix code
- **Documentation gap** — Feature exists but undocumented → update docs
- **Missing test** — Code is correct but no test verifies it → add to test suite
- **Inferred requirement wrong** — The inferred requirement doesn't match actual intent → update QUALITY.md

### Example Triage Summary

```
## Triaged Findings (2026-03-31)

**Highest confidence (all 3 models):**
1. Missing null safety keyword rule → Fix normalize_categories.py line 58
2. Silent fallback behavior undocumented → Update docstring, consider logging warning
3. Defect library row 847 malformed (7 columns) → Fix DEFECT_LIBRARY.md

**High confidence (2 of 3 models):**
1. Parent commit verification missing → Auditor B vs. A/C; deploy verification probe
2. PREFIX_MAP incomplete → Fix extract_defect_data.py PREFIX_MAP

**Needs verification (1 model only):**
1. Per-repo file format inconsistency → Likely false positive (files reviewed were consistent); verify with grep

**RECOMMENDED ACTIONS**
1. Fix normalize_categories.py (null safety rule)
2. Fix DEFECT_LIBRARY.md (row 847)
3. Deploy verification probe for parent commit check
4. Update documentation (fallback behavior)
5. Re-run audit after fixes to confirm
```

---

## Fix Execution Rules

After triage produces a list of confirmed bugs:

1. **Group fixes by subsystem, not by defect number**
   - Batch 1: normalize_categories.py fixes (rules, fallback behavior)
   - Batch 2: extract_defect_data.py fixes (validation, error handling)
   - Batch 3: DEFECT_LIBRARY.md fixes (malformed rows)

2. **Never one mega-prompt for all fixes**
   - Each batch: implement, test, have at least two auditors verify the diff

3. **At least two auditors must confirm fixes pass before marking complete**

4. **After fixes, re-run the spec audit** against the updated code to ensure no regressions

---

## Model Selection Notes

Different models excel at different aspects of auditing:

- **Claude (Architecture-focused):**
  - Excels at data flow, cross-function consistency, state leaks
  - Strong at silent data loss and mutation patterns
  - Generates clear, line-specific findings

- **GPT-4o (Edge-case focused):**
  - Catches boundary conditions and off-by-one errors
  - Good at format edge cases (trailing whitespace, unicode)
  - Serves as effective cross-checker for precision

- **Gemini (Independent verification):**
  - Different training data — may catch things neither Claude nor GPT saw
  - Good for ensemble voting (three independent opinions)
  - May require more structure (guardrails help Gemini perform better)

The specific models that excel will change over time. The principle holds: use multiple models with different strengths.

---

## Tips for Scrutiny Areas

The scrutiny areas are the most important part of the prompt. Generic questions produce generic answers. Specific questions that name functions, files, and edge cases produce specific findings.

**Good scrutiny area:**
- "Read normalize_categories.py lines 50–100 (the keyword-based rules). The spec defines 14 canonical categories. Does the code explicitly handle all 14? Which categories (if any) lack a keyword rule? What happens to raw categories that don't match any rule?"

**Bad scrutiny area:**
- "Check if the code is correct"
- "Look for bugs"
- "Verify the implementation matches the spec"

Better scrutiny areas force deep reading of specific code sections and reference specific requirements from the spec.

---

## Record Keeping

Save all audit artifacts:

```
quality/spec_audits/
├── 2026-03-31-claude.md        # Claude's report
├── 2026-03-31-gpt.md           # GPT's report
├── 2026-03-31-gemini.md        # Gemini's report
└── 2026-03-31-triage.md        # Merged findings and actions
```

Include timestamp and model name in all filenames for traceability.

---

## Frequency and Scope

- **Full spec audit:** Quarterly or after major refactors (tooling changes, new datasets)
- **Focused audit:** After each code review cycle (focus on specific changed files)
- **Re-audit after fixes:** Always, to confirm regressions and verify fixes work

---

## Guardrails (Critical for All Auditors)

These four rules prevent the most common auditing mistakes:

1. **Mandatory line numbers.** If you cannot cite a line number, do not include the finding. This eliminates vague claims.

2. **Grep before claiming missing.** Before saying a feature is absent, search the codebase. It may be in a different file.

3. **Read function bodies, not just signatures.** Don't assume a function works correctly based on its name.

4. **Classify defect type.** Forces structured thinking (MISSING/DIVERGENT/UNDOCUMENTED/PHANTOM) instead of vague "this looks wrong."

These guardrails are embedded in the audit prompt above. They matter most for models that tend toward confident but unchecked claims.

---

## Example: Running a Full Spec Audit

```bash
# Prepare three separate prompts (one for each model)
# Save the audit prompt above to: quality/spec_audits/AUDIT_PROMPT.txt

# Run Auditor A (Claude)
# [Give AUDIT_PROMPT.txt to Claude Code interface]
# Save results to: quality/spec_audits/2026-03-31-claude.md

# Run Auditor B (GPT)
# [Give AUDIT_PROMPT.txt to GPT via OpenAI / Cursor]
# Save results to: quality/spec_audits/2026-03-31-gpt.md

# Run Auditor C (Gemini)
# [Give AUDIT_PROMPT.txt to Gemini via Copilot / appropriate interface]
# Save results to: quality/spec_audits/2026-03-31-gemini.md

# Triage and merge findings
# Create: quality/spec_audits/2026-03-31-triage.md
# [See triage example above]

# Execute fixes in batches
# [Implement fixes based on triage recommendations]
# [Have at least 2 auditors verify each batch]

# Re-run audit on updated code
# Confirm all critical findings are resolved
```

This ensures QPB's data integrity, methodology compliance, and fitness for use in measuring code review tool performance.
