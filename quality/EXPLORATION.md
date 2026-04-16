# Exploration Findings

## Domain and Stack
- **Language:** Markdown specification + Bash (quality_gate.sh)
- **Framework:** AI coding agent skill (Claude Code, GitHub Copilot, Cursor compatible)
- **Build system:** None (no compilation; skill is a set of instruction documents)
- **Deployment target:** Installed into target repositories as `.claude/skills/quality-playbook/` or `.github/skills/`
- **Primary product:** SKILL.md (~2083 lines) -- a specification document that AI agents read and follow to produce quality artifacts
- **Supporting infrastructure:** quality_gate.sh (676 lines, Bash), 12 reference files, 2 orchestrator agent definitions, 2 ai_context files, AGENTS.md

This is a **specification-primary repository**: the specification (SKILL.md + references) IS the product, with quality_gate.sh as supporting validation infrastructure. Per SKILL.md's own guidance: "derive requirements from the specification's internal consistency, completeness, and correctness -- not just from the executable code paths."

## Architecture

### Key files and their roles
| File | Lines | Role |
|------|-------|------|
| SKILL.md | 2083 | Master specification -- all phase instructions, gate definitions, artifact contracts |
| quality_gate.sh | 676 | Post-run validation script -- mechanically checks artifact conformance |
| references/exploration_patterns.md | 283 | Six bug-finding patterns for Phase 1 |
| references/review_protocols.md | 611 | Code review + integration test templates |
| references/requirements_pipeline.md | 427 | Five-phase requirements generation pipeline |
| references/spec_audit.md | 249 | Council of Three audit protocol |
| references/verification.md | 302 | 45 self-check benchmarks for Phase 6 |
| references/iteration.md | 191 | Four iteration strategies (gap, unfiltered, parity, adversarial) |
| references/constitution.md | 160 | QUALITY.md template |
| references/functional_tests.md | 589 | Test structure and anti-patterns |
| references/defensive_patterns.md | 221 | Systematic defensive code search |
| references/schema_mapping.md | 139 | Schema type mapping for boundary tests |
| references/requirements_refinement.md | 113 | Refinement pass protocol |
| references/requirements_review.md | 158 | Interactive review protocol |
| agents/quality-playbook.agent.md | 148 | Orchestrator agent (Copilot/general) |
| agents/quality-playbook-claude.agent.md | 103 | Orchestrator agent (Claude Code sub-agents) |
| ai_context/TOOLKIT.md | 484 | User-facing interactive documentation |
| ai_context/DEVELOPMENT_CONTEXT.md | 172 | Maintainer context |
| AGENTS.md | 68 | AI coding agent entry point |

### Data flow
1. User triggers skill -> agent reads SKILL.md + references
2. Phase 1: Agent explores target codebase -> writes quality/EXPLORATION.md
3. Phase 2: Agent reads EXPLORATION.md -> generates 9+ quality artifacts
4. Phases 3-5: Agent runs review, audit, reconciliation using generated artifacts
5. Phase 6: Agent runs verification benchmarks; quality_gate.sh validates mechanically
6. Phase 7: Interactive presentation to user

### Major subsystems
1. **Phase instruction system** (SKILL.md) -- the specification for all 7 phases
2. **Reference document system** (references/*.md) -- detailed instructions for specific tasks
3. **Mechanical validation** (quality_gate.sh) -- script-verified artifact conformance
4. **Orchestration layer** (agents/*.md) -- agent definitions for automated multi-phase execution
5. **Context/documentation layer** (ai_context/*.md, AGENTS.md) -- bootstrap context for agents and users

### Most complex module: SKILL.md
At 2083 lines, SKILL.md is a monolithic specification with deeply nested cross-references, sequential phase dependencies, gate definitions with specific pass/fail criteria, and detailed behavioral rules that AI agents must follow. Its complexity lies in the interplay between phases, the many mandatory gates, and the precise artifact contracts.

### Most fragile module: quality_gate.sh
This is the only executable code. It mechanically validates artifacts produced by the skill. Bugs here directly affect whether real issues are caught or missed. A false-pass in quality_gate.sh means broken artifacts ship.

## Existing Tests
- **Test framework:** None. There is no automated test suite for this repository.
- **Test count:** 0
- **Coverage:** None
- **Gaps:** The entire repository lacks automated testing. quality_gate.sh has no unit tests. SKILL.md's internal consistency is not mechanically verified. The only "testing" is manual benchmarking on external repos (described in DEVELOPMENT_CONTEXT.md).

## Specifications
The repository IS the specification. SKILL.md is the authoritative document. The references/ files are normative extensions. The key behavioral rules are:
- Phase gate definitions with numbered checks (e.g., Phase 1 completion gate has 12 checks)
- Artifact contracts (the table at SKILL.md lines 86-115)
- Sidecar JSON schemas (tdd-results.json, integration-results.json) with exact field requirements
- 45 self-check benchmarks in verification.md
- quality_gate.sh checks that encode a subset of the artifact contract

## Open Exploration Findings

### Finding 1: quality_gate.sh integration sidecar validation is warn-only in benchmark mode
**File:** `/Users/andrewstellman/tmp/QFB-bootstrap/quality_gate.sh`, lines 382-388
**Bug hypothesis:** When integration-results.json is missing, benchmark mode issues only a WARN, not a FAIL. But the artifact contract table in SKILL.md (line 109) says integration-results.json is required "When integration tests run." The gate's leniency means a run that executed integration tests but failed to produce the sidecar JSON would still pass the gate. This traces from `check_repo()` at line 93 through the `[Integration Sidecar JSON]` section at line 368 which uses `warn` instead of `fail` for benchmark mode.

### Finding 2: quality_gate.sh triage probe check has inconsistent strictness handling
**File:** `/Users/andrewstellman/tmp/QFB-bootstrap/quality_gate.sh`, lines 147-163
**Bug hypothesis:** The triage executable evidence check uses `fail` in benchmark mode but `warn` in general mode. However, SKILL.md's spec_audit.md reference (line 130-148) says verification probes "must produce executable evidence" unconditionally. The gate's `--general` mode allows non-executable triage evidence to pass, creating a strictness gap where general-mode runs skip a mandatory requirement. This traces from the `$STRICTNESS` check at line 157 to the probe evidence check at line 148.

### Finding 3: Version detection logic in quality_gate.sh may fail for skill-as-self-target
**File:** `/Users/andrewstellman/tmp/QFB-bootstrap/quality_gate.sh`, lines 59-67
**Bug hypothesis:** When running `quality_gate.sh .` from the QFB-bootstrap directory itself (this repo), the version detection loop tries `${SCRIPT_DIR}/../SKILL.md`, `${SCRIPT_DIR}/SKILL.md`, `SKILL.md`, and three nested paths. Since SKILL.md is in the repo root and quality_gate.sh is also in the root, the detection should work via `SKILL.md` (relative). But if invoked from a different working directory (e.g., `./quality_gate.sh /path/to/QFB-bootstrap`), the relative `SKILL.md` path fails and the nested paths won't match either, since the skill isn't installed in a subdirectory. The script would proceed with `VERSION=""` and skip version-stamp consistency checks entirely.

### Finding 4: SKILL.md Phase 1 gate check 4 allows 4 findings in the same module
**File:** `/Users/andrewstellman/tmp/QFB-bootstrap/SKILL.md`, line 849
**Bug hypothesis:** Gate check 4 requires "at least 8 concrete bug hypotheses... At least 4 must reference different modules or subsystems." This means up to 4 findings could reference the SAME module. Combined with gate check 5 requiring only 3 multi-function traces, a conformant EXPLORATION.md could have 5 single-function isolated findings in one module plus 3 multi-function findings, with only 4 different modules touched. For small codebases with few modules (like this one), the gate is permissive enough that shallow exploration could pass. The spec text at line 321 says "at least 4 must reference different modules or subsystems" but doesn't define what counts as a "module" vs a "subsystem" -- for a single-file project, every function could be argued as a "module."

### Finding 5: quality_gate.sh bug count extraction misses non-heading bugs
**File:** `/Users/andrewstellman/tmp/QFB-bootstrap/quality_gate.sh`, lines 168-205
**Bug hypothesis:** The script counts bugs by grepping for `^### BUG-[0-9]+` headings. If BUGS.md contains confirmed bugs listed only in a summary table (not as `### BUG-NNN` headings), `bug_count` will be 0, and all downstream checks (TDD sidecar, patches, writeups, TDD logs) will be skipped with "Zero bugs" info messages. The function `check_repo()` at line 93 sets `bug_count` from heading matches at line 183, then uses it as the gate for every subsequent check. A BUGS.md with bugs in non-heading format would escape all validation. The zero-bug detection at line 192 (`grep -qE '(No confirmed|zero|0 confirmed)'`) partially addresses this, but only if the file contains those exact phrases.

### Finding 6: SKILL.md and quality_gate.sh disagree on which artifacts are FAIL vs WARN
**File:** `/Users/andrewstellman/tmp/QFB-bootstrap/quality_gate.sh`, lines 106-129 vs `/Users/andrewstellman/tmp/QFB-bootstrap/SKILL.md`, lines 86-115
**Bug hypothesis:** SKILL.md's artifact contract table marks CONTRACTS.md, RUN_CODE_REVIEW.md, RUN_SPEC_AUDIT.md, RUN_INTEGRATION_TESTS.md, and RUN_TDD_TESTS.md as "Yes" (required). But quality_gate.sh at lines 117-123 checks these as `warn` (not `fail`). A run that never produces CONTRACTS.md would pass the quality gate despite the spec saying it's required. The comment at line 116 says "should not halt the skill if absent, per BUG-005" -- but BUG-005 is an internal reference not present in any shipped file, making it an unexplained override of the stated artifact contract.

### Finding 7: Orphaned reference to "BUG-005" in quality_gate.sh
**File:** `/Users/andrewstellman/tmp/QFB-bootstrap/quality_gate.sh`, line 116
**Bug hypothesis:** The comment `per BUG-005` references a bug ID that doesn't appear in any file in the repository. This is likely from the skill's own quality playbook run, but since the quality/ directory doesn't exist, this reference is dangling. A maintainer reading the code cannot verify why these required artifacts were downgraded to warnings. This traces from line 116 (`# should not halt the skill if absent, per BUG-005`) to the absence of any BUG-005 documentation.

### Finding 8: quality_gate.sh uses `ls` glob patterns that may fail on some shells
**File:** `/Users/andrewstellman/tmp/QFB-bootstrap/quality_gate.sh`, lines 125-129, 132, 141-142, 298-301, 431-432, 517-522, 548-551
**Bug hypothesis:** The script uses bare `ls ${q}/code_reviews/*.md` and similar glob patterns without quoting. On bash with `set -u` (which is set at line 32), if the glob doesn't match anything, `ls` gets a literal `*` which causes an error. The script handles this inconsistently -- some places use `2>/dev/null` to suppress errors, some don't. For example, line 132 does `ls ${q}/code_reviews/*.md 2>/dev/null` but line 125 does `ls ${q}/test_functional.* &>/dev/null` -- the `&>` redirects both stdout and stderr which is correct, but the behavior differs from `2>/dev/null` in edge cases. More critically, the `ls` pattern at line 298 (`ls ${q}/patches/BUG-*-regression*.patch 2>/dev/null`) would fail to count correctly if filenames contain spaces.

### Finding 9: SKILL.md references "Phase 6" in integration test results section heading
**File:** `/Users/andrewstellman/tmp/QFB-bootstrap/references/review_protocols.md`, line 378
**Bug hypothesis:** The integration test protocol execution UX section lists three phases of communication: "Phase 1: The Plan", "Phase 2: Progress", and "Phase 6: Results." This is clearly a numbering error -- should be "Phase 3: Results." The jump from Phase 2 to Phase 6 is confusing because "Phase 6" also refers to the verification phase of the overall playbook. An AI agent following these instructions literally might attempt to map this to the playbook's Phase 6. This traces from line 378 (`### Phase 6: Results`) in the execution UX section.

### Finding 10: SKILL.md mechanical verification section references worktree but not all environments support it
**File:** `/Users/andrewstellman/tmp/QFB-bootstrap/SKILL.md`, lines 1069-1080
**Bug hypothesis:** The patch validation gate instructs use of `git worktree` for compile checking, with a fallback to `git stash`. But this repository itself is not a git repo (confirmed: "Is directory a git repo: No" in the environment). When the skill runs on a non-git project (downloaded tarball, copy of source), both the worktree and stash approaches fail. The fallback text says "or accept `--check`-only validation and note the limitation" but this is buried in a parenthetical, not a clear conditional instruction. An agent following the primary instruction would error out.

### Finding 11: Inconsistency between SKILL.md and quality_gate.sh on test_functional file detection
**File:** `/Users/andrewstellman/tmp/QFB-bootstrap/quality_gate.sh`, lines 125-129 vs `/Users/andrewstellman/tmp/QFB-bootstrap/SKILL.md`, line 69
**Bug hypothesis:** SKILL.md says to "Use the project's language" for functional test naming: `test_functional.py`, `FunctionalSpec.scala`, `functional.test.ts`, `FunctionalTest.java`. But quality_gate.sh at line 125 only checks `ls ${q}/test_functional.*` -- it would miss `FunctionalSpec.scala`, `FunctionalTest.java`, and `functional.test.ts`. The language-specific names given in SKILL.md line 69 aren't all prefixed with `test_functional.`, creating a detection gap. The gate's verification.md benchmark 8 references `quality/test_functional.*` but verification.md doesn't mention the alternative names.

## Quality Risks

### Risk 1 (HIGH): quality_gate.sh false-pass on artifact format violations
**Function:** `check_repo()` at quality_gate.sh:93
**Specific scenario:** Because quality_gate.sh downgrads CONTRACTS.md, RUN_CODE_REVIEW.md, RUN_SPEC_AUDIT.md, RUN_INTEGRATION_TESTS.md, RUN_TDD_TESTS.md, and test_functional.* to WARN (lines 117-129), a run that produces only BUGS.md, REQUIREMENTS.md, QUALITY.md, PROGRESS.md, COVERAGE_MATRIX.md, and COMPLETENESS_REPORT.md -- but none of the protocol files, no functional tests, and no contracts -- would pass quality_gate.sh with zero FAILs. The gate would exit 0 (line 673-676 only checks `$FAIL -gt 0`). This directly contradicts SKILL.md's artifact contract table where these are marked "Required: Yes." A user running `quality_gate.sh .` after a partial run would see "GATE PASSED" despite missing half the required artifacts.

### Risk 2 (HIGH): SKILL.md internal cross-reference drift between spec and gate
**Files:** SKILL.md lines 86-115 (artifact contract table) vs quality_gate.sh lines 106-129 (file existence checks) vs references/verification.md (45 benchmarks)
**Specific scenario:** Three documents independently define what's required: SKILL.md's artifact contract table, quality_gate.sh's check logic, and verification.md's benchmark checklist. When a new artifact is added to SKILL.md's table, it must also be added to quality_gate.sh and to verification.md. But there's no mechanical check that these three sources agree. In practice: SKILL.md says `quality/EXPLORATION.md` is written in Phase 1 (line 258), but quality_gate.sh never checks for its existence. SKILL.md says `quality/VERSION_HISTORY.md` is produced by the requirements pipeline (requirements_pipeline.md line 17), but quality_gate.sh doesn't check for it. These silent omissions mean the gate validates a subset of what the spec requires.

### Risk 3 (HIGH): Pattern numbering confusion in review_protocols.md
**File:** references/review_protocols.md, line 378
**Specific scenario:** The integration test execution UX uses "Phase 1", "Phase 2", "Phase 6" as section headings for the three communication phases (plan, progress, results). A conforming AI agent that reads both SKILL.md and review_protocols.md simultaneously will encounter "Phase 6" in two completely different contexts -- the playbook's Phase 6 (Verification) and the integration test UX's Phase 6 (Results). Because AI agents follow instructions literally and SKILL.md has extensive Phase 6 verification content, there's a real risk of an agent confusing these, potentially trying to run verification benchmarks when the protocol means "show results."

### Risk 4 (MEDIUM): quality_gate.sh `eval` usage creates injection risk
**File:** quality_gate.sh, lines 439-448
**Specific scenario:** The test file extension check uses `eval "find '${repo_dir}' ..."` to run find commands. The `repo_dir` variable comes from command-line arguments (line 55: `REPO_DIRS+=("$arg")`). If a user passes a directory name containing shell metacharacters (e.g., `repo'$(id)'name`), the `eval` would execute the injection. While this is a developer tool not exposed to untrusted input, the pattern is dangerous and unnecessary -- the find commands could be run directly without `eval`.

### Risk 5 (MEDIUM): Sidecar JSON validation in quality_gate.sh uses grep, not a JSON parser
**File:** quality_gate.sh, lines 75-91
**Specific scenario:** The `json_has_key`, `json_str_val`, and `json_key_count` helper functions use `grep` to parse JSON. This means: (1) a key inside a string value would be counted (`"description": "the id field"` would match a check for key `id`); (2) multi-line JSON with keys on non-standard lines might not match; (3) escaped quotes in values could break extraction. For the sidecar JSON files the skill generates, these edge cases are unlikely but not impossible -- a bug description containing `"verdict"` as part of the text would inflate the key count check.

### Risk 6 (MEDIUM): SKILL.md "specification-primary" guidance is buried and easy to miss
**File:** SKILL.md, lines 353-354
**Specific scenario:** The guidance for specification-primary repositories (like this one) is a single paragraph at the end of the "pre-flight scope declaration" section. It says to "derive requirements from the specification's internal consistency, completeness, and correctness." But this guidance competes with 30+ pages of instructions about reading source code, tracing function calls, and finding defensive patterns -- all of which are code-centric. An agent following Phase 1 steps sequentially would hit Step 2 (Map the Architecture), Step 3 (Read Existing Tests), Step 5 (Find the Skeletons) -- all code-focused -- before encountering the specification-primary paragraph buried in the pre-flight section. The result: agents applying the playbook to specification-primary repos will over-focus on quality_gate.sh and under-focus on SKILL.md's internal consistency.

### Risk 7 (MEDIUM): quality_gate.sh date validation allows past dates with no lower bound
**File:** quality_gate.sh, lines 256-276
**Specific scenario:** The TDD sidecar date check validates ISO 8601 format, rejects placeholders (`YYYY-MM-DD`, `0000-00-00`), and rejects future dates. But it accepts any past date -- `1970-01-01` would pass. A stale artifact from a previous run with a real but old date would not be flagged. The cross-run contamination check at lines 606-614 compares directory version to skill version, but doesn't check date freshness.

## Skeletons and Dispatch

### State machine: Playbook phase progression
**State field:** Phase completion checkboxes in PROGRESS.md
**States:** Phase 0 (auto) -> Phase 1 (Explore) -> Phase 2 (Generate) -> Phase 3 (Code Review) -> Phase 4 (Spec Audit) -> Phase 5 (Reconciliation) -> Phase 6 (Verify) -> Phase 7 (Present)
**Transitions:** Each phase has entry gates (prerequisites from prior phases) and exit gates (completion checks)
**Gap:** Phase 7 has no completion gate defined. SKILL.md's phase completion checklist in PROGRESS.md (line 707) includes Phase 7 as `[ ] Phase 7: Present, Explore, Improve (interactive)` but there are no instructions for when to check this box or what constitutes Phase 7 completion.

### Dispatch table: quality_gate.sh file existence checks
**Function:** `check_repo()` at quality_gate.sh:93
**Dispatches on:** artifact file names
**Primary artifacts (FAIL if missing):** BUGS.md, REQUIREMENTS.md, QUALITY.md, PROGRESS.md, COVERAGE_MATRIX.md, COMPLETENESS_REPORT.md
**Secondary artifacts (WARN if missing):** CONTRACTS.md, RUN_CODE_REVIEW.md, RUN_SPEC_AUDIT.md, RUN_INTEGRATION_TESTS.md, RUN_TDD_TESTS.md, test_functional.*
**Not checked at all:** EXPLORATION.md, VERSION_HISTORY.md, AGENTS.md, mechanical/verify.sh receipt files (checked only if mechanical/ exists)

### Feature registry: quality_gate.sh section checks
The gate runs these labeled check sections in sequence:
1. `[File Existence]` -- lines 106-166
2. `[BUGS.md Heading Format]` -- lines 169-205
3. `[TDD Sidecar JSON]` -- lines 208-291
4. `[TDD Log Files]` -- lines 294-365
5. `[Integration Sidecar JSON]` -- lines 368-388
6. `[Use Cases]` -- lines 391-426
7. `[Test File Extension]` -- lines 429-486
8. `[Terminal Gate]` -- lines 489-494
9. `[Mechanical Verification]` -- lines 497-513
10. `[Patches]` -- lines 516-541
11. `[Bug Writeups]` -- lines 544-576
12. `[Version Stamps]` -- lines 579-602
13. `[Cross-Run Contamination]` -- lines 605-624

## Pattern Applicability Matrix
| Pattern | Decision | Target modules | Why |
|---|---|---|---|
| Fallback and Degradation Path Parity | FULL | quality_gate.sh strictness modes, SKILL.md phase prerequisites | quality_gate.sh has `--benchmark` vs `--general` dual strictness with different fail/warn behavior; SKILL.md has multiple fallback paths for reference file resolution, git worktree fallbacks |
| Dispatcher Return-Value Correctness | FULL | quality_gate.sh exit codes, SKILL.md gate pass/fail semantics | quality_gate.sh aggregates FAIL/WARN counts to produce a single exit code; incorrect return value means the gate lies about pass/fail status |
| Cross-Implementation Consistency | FULL | SKILL.md artifact contract vs quality_gate.sh checks vs verification.md benchmarks | Three documents independently specify what's required; inconsistencies mean the spec promises something the gate doesn't enforce |
| Enumeration and Representation Completeness | FULL | quality_gate.sh checked artifacts vs SKILL.md required artifacts, verification.md benchmark list vs quality_gate.sh sections | The authoritative list of artifacts is in SKILL.md; the gate and verification checklist must cover all of them |
| API Surface Consistency | SKIP | No multiple API surfaces; this is a specification repo, not a library | Not applicable -- the repo has no dual-surface API pattern |
| Spec-Structured Parsing Fidelity | SKIP | quality_gate.sh does minimal parsing (JSON grep, date regex) but no formal grammar parsing | The grep-based JSON parsing is covered under Risk 5; no RFC/grammar-level parsing exists |

## Pattern Deep Dive -- Fallback and Degradation Path Parity

### quality_gate.sh benchmark vs general strictness modes
- **Primary path (benchmark mode):** Default strictness. All checks run with full `fail()` enforcement.
- **Fallback path (general mode):** Relaxed strictness via `--general` flag.

**Parity analysis across all strictness-sensitive checks:**

| Check | Benchmark | General | Parity gap? |
|---|---|---|---|
| Missing triage probes (line 157-161) | FAIL | WARN | YES -- executable triage evidence is spec-required (spec_audit.md lines 130-148) regardless of mode |
| Missing integration-results.json (line 382-388) | WARN | INFO | Partial -- neither mode FAILs this, but SKILL.md says it's required when integration tests run |
| UC count below threshold (line 416-419) | FAIL | WARN | YES -- canonical UC identifiers are spec-required (verification.md benchmark 43) |

**Candidate bugs:**
- The `--general` mode silently weakens enforcement of spec-required artifacts. A user running `quality_gate.sh --general .` could pass the gate with missing triage probes and insufficient use cases -- both of which SKILL.md and the reference files say are mandatory.
- The integration sidecar check is WARN even in benchmark mode, creating an unconditional gap.

### SKILL.md reference file resolution fallback
- **Primary path:** `references/` relative to SKILL.md (SKILL.md line 47)
- **Fallback 1:** `.claude/skills/quality-playbook/references/` (line 48)
- **Fallback 2:** `references/` in repo root (line 49)
- **Fallback 3:** `.github/skills/quality-playbook/references/` (line 50)

**Parity gap:** The fallback chain assumes the reference files are always present. There is no error handling if none of the four paths resolve -- the instruction says "If the relative path doesn't resolve, walk the fallback list above" but doesn't say what to do if all four fail. An agent on a partial installation (SKILL.md copied but references/ not copied) would silently proceed without the reference files, producing degraded output with no explicit error.

## Pattern Deep Dive -- Dispatcher Return-Value Correctness

### quality_gate.sh exit code determination
- **Function:** Main script body, lines 664-676
- **Input conditions:** `$FAIL` counter (incremented by `fail()` at line 69), `$WARN` counter (incremented by `warn()` at line 71)
- **Return value logic:**
  - `$FAIL -gt 0` -> exit 1 (gate failed)
  - `$FAIL -eq 0` -> exit 0 (gate passed), regardless of WARN count

**Combinations checked:**
- Many FAILs, no WARNs: exits 1 -- correct
- No FAILs, many WARNs: exits 0 -- **potentially incorrect** because some WARNs represent spec-required artifacts (Finding 6)
- No FAILs, no WARNs: exits 0 -- correct
- Mixed FAILs and WARNs: exits 1 -- correct (FAIL dominates)

**The core issue:** The dispatcher's return value is correct for its own logic but incorrect relative to the specification. The WARN-only path returns "gate passed" for conditions that SKILL.md says are failures. This is a dispatcher return-value bug where the classification (WARN vs FAIL) is wrong upstream, causing the final exit code to be wrong downstream.

**Candidate requirement:** REQ: quality_gate.sh must FAIL (not WARN) for all artifacts marked "Required: Yes" in SKILL.md's artifact contract table.

## Pattern Deep Dive -- Cross-Implementation Consistency

### Artifact requirement: three implementations of the same contract

The "required artifacts" contract is stated in three places:

**Implementation A: SKILL.md artifact contract table (lines 86-115)**
Lists 20+ artifacts with Required? column. Key required artifacts: QUALITY.md, REQUIREMENTS.md, CONTRACTS.md, test_functional.*, RUN_CODE_REVIEW.md, RUN_INTEGRATION_TESTS.md, RUN_SPEC_AUDIT.md, RUN_TDD_TESTS.md, BUGS.md, COVERAGE_MATRIX.md, COMPLETENESS_REPORT.md, PROGRESS.md, AGENTS.md, mechanical/verify.sh.

**Implementation B: quality_gate.sh file existence checks (lines 106-129)**
Checks with FAIL: BUGS.md, REQUIREMENTS.md, QUALITY.md, PROGRESS.md, COVERAGE_MATRIX.md, COMPLETENESS_REPORT.md
Checks with WARN: CONTRACTS.md, RUN_CODE_REVIEW.md, RUN_SPEC_AUDIT.md, RUN_INTEGRATION_TESTS.md, RUN_TDD_TESTS.md, test_functional.*
Not checked: AGENTS.md, EXPLORATION.md, VERSION_HISTORY.md

**Implementation C: verification.md benchmark 40 (lines 226-229)**
"Required files: BUGS.md, REQUIREMENTS.md, QUALITY.md, PROGRESS.md, COVERAGE_MATRIX.md, COMPLETENESS_REPORT.md. If Phase 3 ran: at least one file in code_reviews/. If Phase 4 ran: at least one auditor file and a triage file in spec_audits/."

**Consistency gaps:**

| Artifact | SKILL.md says | quality_gate.sh does | verification.md says |
|---|---|---|---|
| CONTRACTS.md | Required: Yes | WARN if missing | Not mentioned in benchmark 40 |
| test_functional.* | Required: Yes | WARN if missing | Not mentioned in benchmark 40 |
| RUN_CODE_REVIEW.md | Required: Yes | WARN if missing | Not mentioned in benchmark 40 |
| RUN_SPEC_AUDIT.md | Required: Yes | WARN if missing | Not mentioned in benchmark 40 |
| RUN_TDD_TESTS.md | Required: Yes | WARN if missing | Not mentioned in benchmark 40 |
| RUN_INTEGRATION_TESTS.md | Required: Yes | WARN if missing | Not mentioned in benchmark 40 |
| AGENTS.md | Required: Yes | Not checked | Not mentioned |
| EXPLORATION.md | Written in Phase 1 | Not checked | Not mentioned |
| VERSION_HISTORY.md | Produced by pipeline | Not checked | Not mentioned |
| mechanical/verify.sh | Required: Yes (benchmark) | Only checked if mechanical/ exists | Mentioned in benchmark 27 |

**Candidate requirement:** REQ: All three artifact-requirement sources (SKILL.md table, quality_gate.sh, verification.md) must agree on which artifacts are required and enforce the same severity for missing artifacts.

## Pattern Deep Dive -- Enumeration and Representation Completeness

### quality_gate.sh check sections vs SKILL.md requirements

**Authoritative source (SKILL.md artifact contract table, lines 86-115):**
All artifacts with "Required: Yes" or conditional requirements.

**Closed set (quality_gate.sh check sections):**
The 13 labeled check sections handle a specific subset of the artifact contract.

**Missing entries -- artifacts required by SKILL.md but not checked by quality_gate.sh:**
1. `AGENTS.md` -- Required: Yes, Created In: Phase 2 -- not checked at all
2. `quality/EXPLORATION.md` -- mandatory handoff file from Phase 1 -- not checked
3. `quality/VERSION_HISTORY.md` -- produced by requirements pipeline -- not checked
4. `quality/RUN_TDD_TESTS.md` -- Required: Yes -- only WARN, not FAIL
5. `quality/CONTRACTS.md` -- Required: Yes -- only WARN, not FAIL

**Missing check categories -- things SKILL.md requires but quality_gate.sh doesn't verify:**
1. EXPLORATION.md section structure (Phase 2 entry gate requires 6 specific sections)
2. REQUIREMENTS.md section structure (must begin with human-readable overview)
3. QUALITY.md scenario count (must have scenarios, not just exist)
4. Version stamp format correctness (gate checks version match but not format)
5. Integration test protocol self-containment (verification.md benchmark 12)

**Candidate requirement:** REQ: quality_gate.sh should verify existence of all "Required: Yes" artifacts from SKILL.md's artifact contract table with FAIL severity, not WARN.

## Candidate Bugs for Phase 2

### CB-1: quality_gate.sh downgrades 6 required artifacts to WARN (HIGH)
**Source:** Open exploration (Finding 6) + Cross-Implementation Consistency pattern
**File:line:** quality_gate.sh:117-129
**Hypothesis:** CONTRACTS.md, RUN_CODE_REVIEW.md, RUN_SPEC_AUDIT.md, RUN_INTEGRATION_TESTS.md, RUN_TDD_TESTS.md, and test_functional.* are marked "Required: Yes" in SKILL.md's artifact contract but quality_gate.sh only WARNs on their absence. A run missing all of these passes the gate.
**Code review should:** Compare SKILL.md lines 86-115 with quality_gate.sh lines 106-129. Verify whether the "per BUG-005" comment justifies the downgrade. Check if BUG-005 is documented anywhere.

### CB-2: review_protocols.md "Phase 6: Results" numbering error (MEDIUM)
**Source:** Open exploration (Finding 9)
**File:line:** references/review_protocols.md:378
**Hypothesis:** The integration test execution UX section jumps from "Phase 2: Progress" to "Phase 6: Results" instead of "Phase 3: Results." This confuses the integration test communication phases with the playbook's own Phase 6 (Verification).
**Code review should:** Read lines 340-400 of review_protocols.md and verify the section numbering sequence.

### CB-3: quality_gate.sh test_functional.* detection misses SKILL.md-allowed alternative names (MEDIUM)
**Source:** Open exploration (Finding 11) + Enumeration Completeness pattern
**File:line:** quality_gate.sh:125-129 vs SKILL.md:69
**Hypothesis:** SKILL.md allows test names like `FunctionalSpec.scala`, `FunctionalTest.java`, `functional.test.ts` but quality_gate.sh only globs `test_functional.*`. Runs using language-conventional names would trigger a WARN.
**Code review should:** Check all test file name patterns mentioned in SKILL.md and functional_tests.md, then verify quality_gate.sh's glob covers them.

### CB-4: quality_gate.sh `eval` usage with user-supplied paths creates shell injection risk (MEDIUM)
**Source:** Quality Risks (Risk 4)
**File:line:** quality_gate.sh:439-448
**Hypothesis:** The `eval "find '${repo_dir}' ..."` pattern passes user-supplied directory names through `eval`, enabling command injection via crafted directory names.
**Code review should:** Trace the `repo_dir` variable from argument parsing (line 55) through `eval` at lines 439-448. Verify whether single-quoting within the eval string is sufficient protection (it is not -- a directory name containing `'` breaks the quoting).

### CB-5: quality_gate.sh AGENTS.md is never checked despite being required (MEDIUM)
**Source:** Enumeration Completeness pattern
**File:line:** quality_gate.sh (absent) vs SKILL.md:102
**Hypothesis:** SKILL.md artifact contract says `AGENTS.md` is "Required: Yes, Created In: Phase 2" but quality_gate.sh has no check for it at all.
**Code review should:** Search quality_gate.sh for any reference to AGENTS.md. Confirm it's absent.

### CB-6: integration-results.json is WARN even in benchmark mode (MEDIUM)
**Source:** Quality Risks (Risk 1) + Fallback Parity pattern
**File:line:** quality_gate.sh:382-388
**Hypothesis:** The integration sidecar check uses `warn` even when `$STRICTNESS = "benchmark"`. SKILL.md says this file is required "When integration tests run" but the gate never fails on its absence regardless of mode.
**Code review should:** Check whether there's a way to determine if integration tests actually ran, and if so, whether the check should escalate to FAIL.

## Derived Requirements

### REQ-001: Artifact contract enforcement consistency
SKILL.md's artifact contract table, quality_gate.sh's file existence checks, and verification.md's benchmarks must agree on which artifacts are required and enforce the same severity for missing artifacts. Currently, 6 required artifacts are downgraded to WARN in quality_gate.sh despite being marked "Required: Yes" in SKILL.md.
- **Spec basis:** [Tier 1] SKILL.md lines 83-85 ("If the gate checks for it, this skill must instruct its creation")
- **File paths:** SKILL.md:86-115, quality_gate.sh:106-129, references/verification.md:226-229

### REQ-002: quality_gate.sh must validate all required artifacts with FAIL severity
All artifacts marked "Required: Yes" in SKILL.md's artifact contract table must be checked by quality_gate.sh with `fail()`, not `warn()`. This includes CONTRACTS.md, test_functional.*, RUN_CODE_REVIEW.md, RUN_SPEC_AUDIT.md, RUN_TDD_TESTS.md, RUN_INTEGRATION_TESTS.md, and AGENTS.md.
- **Spec basis:** [Tier 1] SKILL.md line 83 ("any artifact not listed here should not be gate-enforced, and any gate check should trace to an artifact listed here")
- **File paths:** quality_gate.sh:106-129

### REQ-003: Internal numbering consistency in reference documents
All section numbering within reference documents must be internally consistent. Sequential sections must use sequential numbers. "Phase N" labels must not collide with the playbook's own phase numbering when used in a different context.
- **Spec basis:** [Tier 2] references/review_protocols.md:340-400
- **File paths:** references/review_protocols.md:378

### REQ-004: quality_gate.sh must not use eval with user-supplied paths
Shell commands in quality_gate.sh must not pass user-supplied arguments through `eval`. Use direct command execution or `--` argument termination instead.
- **Spec basis:** [Tier 3] [source] quality_gate.sh:439-448
- **File paths:** quality_gate.sh:439-448

### REQ-005: quality_gate.sh test file detection must cover all SKILL.md-allowed names
The gate's functional test file detection must recognize all naming patterns allowed by SKILL.md: test_functional.*, FunctionalSpec.*, FunctionalTest.*, functional.test.*.
- **Spec basis:** [Tier 1] SKILL.md line 69 naming examples
- **File paths:** quality_gate.sh:125-129, SKILL.md:69

### REQ-006: Reference file resolution must handle missing files explicitly
SKILL.md's reference file resolution fallback chain (4 paths) must include an explicit error or warning when none of the paths resolve, rather than silent degradation.
- **Spec basis:** [Tier 2] SKILL.md lines 44-51
- **File paths:** SKILL.md:44-51

### REQ-007: quality_gate.sh JSON validation must handle edge cases
The grep-based JSON helpers must not false-match on keys appearing inside string values or across unexpected line boundaries.
- **Spec basis:** [Tier 3] [source] quality_gate.sh:75-91
- **File paths:** quality_gate.sh:75-91

## Derived Use Cases

### UC-01: Developer runs quality playbook on a target codebase
**Actor:** Developer with AI coding agent
**Trigger:** "Run the quality playbook on this project"
**Expected outcome:** Agent reads SKILL.md, executes Phase 1, produces EXPLORATION.md, and stops with guidance for next phase

### UC-02: Developer validates quality artifacts after a playbook run
**Actor:** Developer
**Trigger:** Runs `quality_gate.sh .` after playbook completes
**Expected outcome:** Gate checks all required artifacts exist, have correct format, version stamps match, and exits 0 if all checks pass

### UC-03: Maintainer modifies the skill and verifies correctness
**Actor:** Skill maintainer
**Trigger:** Edits SKILL.md or reference files, then benchmarks on test repos
**Expected outcome:** Changes are tested on 2+ repos, version is bumped, quality_gate.sh passes on test results, TOOLKIT.md and DEVELOPMENT_CONTEXT.md are updated

### UC-04: Developer installs skill into a new repository
**Actor:** Developer
**Trigger:** Copies skill files into .claude/skills/ or .github/skills/
**Expected outcome:** Agent can find SKILL.md and all reference files via the resolution fallback chain

### UC-05: Developer runs iteration strategies to find additional bugs
**Actor:** Developer with AI coding agent
**Trigger:** "Run the next iteration using the gap strategy"
**Expected outcome:** Agent reads previous EXPLORATION.md, identifies gaps, produces EXPLORATION_ITER{N}.md, merges findings, and re-runs Phases 2-6

### UC-06: Orchestrator agent runs full pipeline automatically
**Actor:** Orchestrator agent (from agents/*.md)
**Trigger:** "Run the full playbook" or programmatic orchestration
**Expected outcome:** All phases run sequentially with clean context windows, each phase writes checkpoint to PROGRESS.md, final results presented to user

### UC-07: Developer uses quality_gate.sh across multiple benchmark repos
**Actor:** Benchmark maintainer
**Trigger:** `quality_gate.sh --all` or `quality_gate.sh --version 1.4.0 repo1 repo2`
**Expected outcome:** Gate validates each repo independently, reports per-repo results, exits 1 if any repo fails

## Notes for Artifact Generation
- This is a specification-primary repository. Requirements should focus heavily on SKILL.md internal consistency, cross-reference accuracy, and gate enforcement completeness -- not just quality_gate.sh code bugs.
- The project uses Bash (quality_gate.sh) as its only executable code. Functional tests should be shell scripts or Python scripts that validate quality_gate.sh behavior.
- There are no existing tests to match import patterns against. Tests must be written from scratch.
- The test_functional file should be `test_functional.sh` or `test_functional.py` (Python with subprocess calls to quality_gate.sh).
- Mechanical verification: quality_gate.sh has dispatch-style check sections that could benefit from mechanical extraction of what's checked vs what's required.

## Gate Self-Check

1. **File exists with 120+ lines:** PASS -- this file contains substantial findings with file paths, line numbers, and specific behavioral analysis.
2. **PROGRESS.md exists and marks Phase 1 complete:** PASS -- quality/PROGRESS.md written with Phase 1 marked `[x]`.
3. **Derived Requirements contain REQ-NNN with file paths and function names:** PASS -- REQ-001 through REQ-007 all cite specific file paths and line numbers.
4. **Open Exploration Findings has 8+ concrete findings, 4+ different modules:** PASS -- 11 findings across SKILL.md, quality_gate.sh, review_protocols.md, and multiple reference files (4+ distinct modules).
5. **Open-exploration depth check (3+ multi-function traces):** PASS -- Finding 1 traces from check_repo() through the integration sidecar section; Finding 5 traces from check_repo() through heading detection through downstream checks; Finding 6 traces from SKILL.md's artifact table through quality_gate.sh's check logic.
6. **Quality Risks has 5+ domain-driven failure scenarios:** PASS -- 7 ranked risks, each with specific function, file, and line citations.
7. **Pattern Applicability Matrix evaluates all 6 patterns:** PASS -- all 6 patterns evaluated with FULL/SKIP decisions and rationale.
8. **3-4 patterns marked FULL:** PASS -- 4 patterns marked FULL (Fallback Parity, Dispatcher Return-Value, Cross-Implementation Consistency, Enumeration Completeness).
9. **3-4 Pattern Deep Dive sections:** PASS -- 4 deep-dive sections present.
10. **Pattern depth check (2+ trace across functions):** PASS -- Fallback Parity traces across quality_gate.sh strictness paths; Cross-Implementation Consistency traces across SKILL.md, quality_gate.sh, and verification.md; Enumeration Completeness traces from SKILL.md's artifact table through quality_gate.sh's check sections.
11. **Candidate Bugs section with 4+ prioritized bugs:** PASS -- 6 candidate bugs with file:line references, source stages, and review instructions.
12. **Ensemble balance check:** PASS -- CB-1 from open exploration + pattern, CB-2 from open exploration, CB-3 from open exploration + pattern, CB-4 from quality risks, CB-5 from pattern, CB-6 from quality risks + pattern. At least 2 from open exploration/risks, at least 1 from pattern.
