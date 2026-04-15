# Exploration Findings

## Domain and Stack
- **Language:** Markdown (specification documents), Bash (quality_gate.sh validation script)
- **Framework:** AI coding agent skill — a long-form instruction document (SKILL.md, ~2069 lines) that AI agents read and follow to perform quality audits on arbitrary codebases
- **Build system:** None (no compilation). The project is a specification/protocol document with supporting references, a shell validation script, and orchestrator agent definitions.
- **Deployment target:** Installed into target repositories at `.github/skills/` (Copilot) or `.claude/skills/` (Claude Code) — agents read the files at runtime
- **Key dependencies:** AI coding agents (Claude Code, GitHub Copilot, Cursor), bash shell for quality_gate.sh
- **Primary output:** Nine quality artifacts generated in a target project's `quality/` directory
- **Classification:** Specification-primary repository — the primary product is the SKILL.md specification and its reference documents, with quality_gate.sh as supporting executable infrastructure

## Architecture

The project has five major subsystems:

1. **SKILL.md** (2069 lines) — The main specification. Contains Phase 0-7 instructions, artifact contracts, JSON schema templates, gate definitions, and execution rules. This is the single most critical file.
   - Entry point: An AI agent reads this file and follows instructions sequentially
   - Data flow: SKILL.md instructions → agent explores target codebase → writes artifacts to `quality/` → downstream phases read artifacts from disk

2. **references/** (12 files, ~3442 lines total) — Phase-specific reference documents read during execution:
   - `exploration_patterns.md` — Six bug-finding patterns for Phase 1
   - `requirements_pipeline.md` — Five-phase requirements derivation for Phase 2
   - `review_protocols.md` — Three-pass code review template for Phase 3
   - `spec_audit.md` — Council of Three protocol for Phase 4
   - `verification.md` — 45 self-check benchmarks for Phase 6
   - `iteration.md` — Four iteration strategies (gap, unfiltered, parity, adversarial)
   - `constitution.md`, `defensive_patterns.md`, `schema_mapping.md`, `functional_tests.md`, `requirements_refinement.md`, `requirements_review.md`

3. **quality_gate.sh** (632 lines) — Mechanical validation script that checks artifact conformance after a playbook run. Validates: file existence, JSON schema conformance, heading format, version stamps, TDD log presence, patches, writeups, use case counts, test file extensions, cross-run contamination.

4. **agents/** (2 files) — Orchestrator agent definitions:
   - `quality-playbook.agent.md` — General orchestrator (Copilot/multi-tool)
   - `quality-playbook-claude.agent.md` — Claude Code orchestrator using sub-agents

5. **ai_context/** (2 files) — Documentation for different audiences:
   - `TOOLKIT.md` — User-facing interactive guide
   - `DEVELOPMENT_CONTEXT.md` — Maintainer context (architecture, benchmarking, known issues)

**Most complex module:** SKILL.md — it contains overlapping phase definitions, multiple JSON schema examples that must be consistent, cross-references to reference files using hardcoded paths, gate definitions that reference each other, and evolutionary artifacts from version history.

**Most fragile module:** quality_gate.sh — it must correctly validate all artifacts defined in SKILL.md using grep/awk-based parsing of JSON and Markdown. Any drift between what SKILL.md instructs and what quality_gate.sh validates creates a silent conformance gap.

## Existing Tests
- **No test suite exists.** The project has no automated tests for the specification itself or for quality_gate.sh.
- There is no CI/CD pipeline.
- Validation relies on: (1) manual benchmarking against 10+ open-source repos, (2) quality_gate.sh run after each benchmark, (3) council reviews (human-guided multi-model analysis).
- The benchmarking methodology is described in DEVELOPMENT_CONTEXT.md but the benchmark infrastructure (repos/, setup_repos.sh, run_playbook.sh) is not included in this repository.

## Specifications
- **Primary specification:** SKILL.md itself IS the specification — it defines expected behavior for AI agents executing the playbook
- **Supporting specs:** docs_gathered/ contains 9 documents including:
  - `readme.md` — project README describing intended behavior
  - `toolkit-documentation.md` — user-facing documentation (identical to ai_context/TOOLKIT.md)
  - `development-context.md` — maintainer documentation (identical to ai_context/DEVELOPMENT_CONTEXT.md)
  - O'Reilly Radar articles explaining the design philosophy and methodology
  - `quality-md-genesis-history.md` — design history of the quality constitution concept
  - `article-reference-guide.md` — reference guide for article writing

## Open Exploration Findings

### Finding 1: TDD sidecar JSON summary schema inconsistency between two canonical examples
SKILL.md contains two canonical examples of `tdd-results.json`. They use DIFFERENT summary field names:
- **Example 1** (SKILL.md line 127): `"total": 3, "confirmed_open": 1, "red_failed": 0, "green_failed": 0, "tdd_verified": 2`
- **Example 2** (SKILL.md line 1382-1388): `"total": 6, "verified": 4, "confirmed_open": 1, "red_failed": 1, "green_failed": 0`
- **Line 1394** states: "The `summary` object must contain exactly these keys: `total`, `verified`, `confirmed_open`, `red_failed`, `green_failed`."

The first example uses `tdd_verified` while the second uses `verified`. An agent following Example 1 will produce a schema that does not match the normative text at line 1394. Furthermore, quality_gate.sh (line 229) only checks for `confirmed_open`, `red_failed`, and `green_failed` — it does NOT check for `total`, `verified`, or `tdd_verified`, so either example will pass the gate despite the inconsistency.

### Finding 2: Phase numbering inconsistency — Phase 7 exists but is not in the plan overview
SKILL.md line 12-31 describes Phases 0-6 in the plan overview. Phase 7 ("Present, Explore, Improve") is defined at line 1890 but is NOT mentioned in the plan overview (lines 12-31). Additionally:
- The Phase completion checklist (line 688) lists Phases 1-6 but not Phase 7
- The convergence check (line 1797) says "skip to Phase 7" — referencing a phase that the plan overview omits
- verification.md line 75 says "Inferred requirements should be flagged for user review in Phase 7"
- The end-of-Phase-6 message (line 1838-1864) does NOT mention Phase 7
- The agents/ orchestrators describe six phases, not seven

This creates confusion: is Phase 7 required? Optional? Part of the standard flow or a legacy artifact? An agent following the plan overview will skip Phase 7 entirely.

### Finding 3: Hardcoded `.github/skills/` paths in SKILL.md will fail when skill is installed elsewhere
SKILL.md references `.github/skills/references/` paths throughout (lines 214, 296, 872-877, 888, 1486, 1514, 1559-1561, 1661). But the skill can be installed at:
- `.github/skills/SKILL.md` (Copilot flat layout)
- `.github/skills/quality-playbook/SKILL.md` (Copilot nested layout)
- `.claude/skills/quality-playbook/SKILL.md` (Claude Code)
- Or at project root (as in this repository)

When the skill is at `.claude/skills/quality-playbook/SKILL.md`, the reference path `.github/skills/references/exploration_patterns.md` does not exist. The agents/ orchestrators correctly check multiple paths for SKILL.md but SKILL.md itself hardcodes only one path for references. An agent that reads SKILL.md installed at `.claude/skills/` will fail to find references at `.github/skills/references/`.

### Finding 4: quality_gate.sh does not validate TDD log status tags despite SKILL.md claiming it does
SKILL.md line 1137 states: "The status tag (`RED`, `GREEN`, `NOT_RUN`, `ERROR`) on the first line is machine-readable — `quality_gate.sh` will check for its presence."

However, quality_gate.sh (lines 277-322) only checks whether the log FILES exist (`-f "${q}/results/${bid}.red.log"`). It does NOT read the first line or validate the status tag content. An agent could create empty log files or log files without status tags and pass the gate.

### Finding 5: Artifact contract table says mechanical verify script Created In "Phase 5" but instructions say Phase 1/2
The artifact contract table (SKILL.md line 97) says `quality/mechanical/verify.sh` is created in "Phase 5". But:
- SKILL.md line 531 instructs creation of verify.sh during Step 7 (Phase 1 requirements derivation — which is actually Phase 2's contract extraction)
- SKILL.md line 555 has the "Immediate integrity gate (mandatory, Phase 2a)" that requires verify.sh to run before writing any contract
- The verify receipt files (line 98) are also listed as "Phase 5" but are generated when verify.sh runs in Phase 2a

This table-vs-instruction mismatch means an agent consulting the artifact contract table will expect to create verify.sh in Phase 5, while the detailed instructions demand it in Phase 2.

### Finding 6: DEVELOPMENT_CONTEXT.md incorrectly labels verification.md as "Phase 3"
DEVELOPMENT_CONTEXT.md line 23 lists `verification.md` as "45 self-check benchmarks for Phase 3". But verification.md is used in Phase 6 (Verify), not Phase 3 (Code Review). This appears in both `ai_context/DEVELOPMENT_CONTEXT.md` and `docs_gathered/development-context.md`.

### Finding 7: Duplicate content between ai_context/ and docs_gathered/
`ai_context/TOOLKIT.md` and `docs_gathered/toolkit-documentation.md` are identical (both 475 lines, same content). `ai_context/DEVELOPMENT_CONTEXT.md` and `docs_gathered/development-context.md` are identical (both 173 lines). This creates a maintenance burden where changes must be synchronized in two places, and risks drift where one copy is updated and the other is not.

### Finding 8: quality_gate.sh uses `ls` globbing patterns that may fail on some shells
quality_gate.sh lines 116, 125-126, 159-165, 388-389, 477-478, 506 use unquoted glob patterns like `ls ${q}/code_reviews/*.md` and `ls ${q}/patches/BUG-*-regression*.patch`. While `set -uo pipefail` is set (line 32), `set -e` is not. The `ls` commands with glob patterns will print error messages to stderr if no files match, but the `wc -l` counting will still work. However, on some systems with `nullglob` or `failglob` options, the behavior may differ. More critically, the `for wf in ${q}/writeups/BUG-*.md` pattern (line 507) will iterate over the literal unexpanded glob if no files match, causing `[ -f "$wf" ]` to test against the unexpanded pattern string.

### Finding 9: Step numbering inside Phase 1 is confusing — Steps 0-7 span Phases 1-2
SKILL.md Phase 1 (starting line 292) contains Steps 0 through 7b. But Step 7 ("Derive Testable Requirements") with its five-phase pipeline (Phases A-E) is described as part of Phase 1 exploration. Yet the plan overview says requirements derivation happens in Phase 2 (line 21). The checkpoint at line 665 says "After completing Phase 1 exploration" but Steps 0-7b include the entire requirements pipeline which is a Phase 2 activity. This means the Phase 1 completion gate (line 828) checks for derived requirements that the plan overview assigns to Phase 2.

### Finding 10: The per-bug field list in tdd-results.json schema differs between SKILL.md and verification.md
SKILL.md line 1392 lists required per-bug fields as: `id`, `requirement`, `red_phase`, `green_phase`, `verdict`, `fix_patch_present`, `writeup_path`. The canonical example at line 1362-1379 includes additional fields: `regression_patch`, `fix_patch`, `patch_gate_passed`, `junit_red`, `junit_green`, `junit_available`, `notes`. But the earlier canonical example at line 115-123 uses a different set: `id`, `requirement`, `red_phase`, `green_phase`, `verdict`, `fix_patch_present`, `writeup_path` — matching the required list but missing all the extra fields from the second example. verification.md line 105 lists: `id`, `requirement`, `red_phase`, `green_phase`, `verdict`, `fix_patch_present`, `writeup_path` — matching the first example. Agents following the more detailed second example will produce fields not validated by the gate.

### Finding 11: quality_gate.sh never validates EXPLORATION.md
The Phase 1 completion gate (SKILL.md lines 828-845) describes 12 mandatory checks for EXPLORATION.md. But quality_gate.sh does not check for EXPLORATION.md at all — it is not in the file existence checks (line 107). An agent could skip Phase 1 entirely, produce no EXPLORATION.md, and still pass quality_gate.sh if all other artifacts exist.

## Quality Risks

### Risk 1 (HIGH): Contradictory JSON schema templates cause agent-produced JSON to fail silent validation
**Because** SKILL.md lines 127 and 1382-1388 define two different summary field structures for tdd-results.json (`tdd_verified` vs `verified`), an agent faithfully copying the first template will produce JSON that does not match the normative requirement at line 1394. quality_gate.sh (line 229) only validates three of the five required summary keys (`confirmed_open`, `red_failed`, `green_failed`), so neither `tdd_verified` nor `verified` is actually gate-checked. The result is that the gate passes regardless of which template the agent uses, but downstream tooling or human reviewers expecting one schema will encounter the other.
- **Priority:** 1 — This is a direct specification contradiction with real downstream impact. An agent cannot satisfy both templates simultaneously.

### Risk 2 (HIGH): Phase numbering gap causes agents to skip Phase 7 or misroute convergence
**Because** the plan overview (SKILL.md lines 12-31) describes Phases 0-6 but Phase 7 exists at line 1890, and the convergence check at line 1797 says "skip to Phase 7," an agent that uses the plan overview as its execution roadmap will have no entry for Phase 7 and will not know to execute it. The end-of-Phase-6 message (line 1838) says "STOP" without mentioning Phase 7. The orchestrator agents (agents/quality-playbook-claude.agent.md, agents/quality-playbook.agent.md) describe six phases, confirming Phase 7 is invisible to the orchestration layer.
- **Priority:** 2 — Phase 7 contains the interactive improvement menu, which is valuable but not critical for bug discovery. The real risk is the dangling "skip to Phase 7" reference in the convergence check.

### Risk 3 (HIGH): Hardcoded reference paths break installation at non-default locations
**Because** SKILL.md hardcodes `.github/skills/references/` throughout (16+ occurrences), but Claude Code installations use `.claude/skills/quality-playbook/references/`, an agent running from a Claude Code installation will fail to find reference files. The orchestrator agents check multiple SKILL.md locations but SKILL.md itself does not adapt its internal reference paths. This means the most common Claude Code installation path will produce reference-not-found errors for every phase that reads a reference file.
- **Priority:** 1 — This affects every Claude Code user and every phase that references a file.

### Risk 4 (MEDIUM): quality_gate.sh validates less than SKILL.md claims
**Because** quality_gate.sh does not validate TDD log status tags (Finding 4), does not validate `total` or `verified`/`tdd_verified` summary keys (Finding 1), and does not check for EXPLORATION.md (Finding 11), a run that passes quality_gate.sh may still be non-conformant per SKILL.md. The specification's anti-tampering claims (e.g., "quality_gate.sh will check for its presence" regarding status tags) are false, which means the mechanical validation provides weaker guarantees than documented.
- **Priority:** 2 — Gate under-validation means bugs in artifacts can slip through.

### Risk 5 (MEDIUM): Step 7 requirements pipeline described as Phase 1 but assigned to Phase 2
**Because** Step 7 (SKILL.md line 508) with its five-phase requirements pipeline is located within the Phase 1 section but the plan overview assigns requirements to Phase 2 (line 21), an agent executing phases separately will face a contradiction. If it runs Phase 1 and stops, it may or may not have run the requirements pipeline. The Phase 1 completion gate checks for derived requirements (gate check 3, line 835), suggesting the pipeline IS part of Phase 1 — contradicting the plan overview.
- **Priority:** 3 — This is a structural confusion that affects multi-session execution, though single-session runs handle it implicitly.

## Skeletons and Dispatch

### State machine: Phase execution lifecycle
SKILL.md defines phases 0-7 (though 7 is partially hidden). The state transitions are:
- Phase 0 (automatic, conditional on `previous_runs/`)
- Phase 0b (automatic, conditional on sibling directories and no `previous_runs/`)
- Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → (Phase 7?)
- After Phase 6: iteration loop (gap → unfiltered → parity → adversarial)
- Convergence check may loop back to Phase 0

**Gap:** Phase 7 is unreachable from the standard flow. The end-of-Phase-6 message says STOP, suggests iterations, but never mentions Phase 7.

### Dispatch: quality_gate.sh check_repo() function
The `check_repo()` function (lines 93-582) dispatches across nine validation sections:
1. File Existence (lines 106-150)
2. BUGS.md Heading Format (lines 153-189)
3. TDD Sidecar JSON (lines 192-275)
4. TDD Log Files (lines 278-322)
5. Integration Sidecar JSON (lines 325-345)
6. Use Cases (lines 348-383)
7. Test File Extension (lines 386-443)
8. Terminal Gate (lines 446-450)
9. Mechanical Verification (lines 453-470)
10. Patches (lines 473-498)
11. Bug Writeups (lines 501-532)
12. Version Stamps (lines 535-558)
13. Cross-Run Contamination (lines 561-581)

### Dispatch: SKILL.md reference file routing
SKILL.md references at least 7 reference files. Each phase header contains a "Required references" block that lists which files to read. The routing is:
- Phase 1: exploration_patterns.md
- Phase 2: requirements_pipeline.md, defensive_patterns.md, schema_mapping.md, constitution.md, functional_tests.md, review_protocols.md
- Phase 3: review_protocols.md
- Phase 4: spec_audit.md
- Phase 5: requirements_pipeline.md, review_protocols.md, spec_audit.md
- Phase 6: verification.md

All paths are hardcoded to `.github/skills/references/` (see Finding 3).

## Pattern Applicability Matrix
| Pattern | Decision | Target modules | Why |
|---|---|---|---|
| Fallback and Degradation Path Parity | SKIP | N/A | The project has no runtime fallback paths. SKILL.md describes a single execution flow per phase, not multiple strategies for the same operation. |
| Dispatcher Return-Value Correctness | SKIP | N/A | quality_gate.sh returns exit codes (0 or 1) but has no complex dispatch-return-value interactions. The shell script's control flow is linear. |
| Cross-Implementation Consistency | FULL | agents/, SKILL.md, ai_context/, docs_gathered/ | Multiple documents describe the same concepts (phases, installation, execution) and must be consistent. agents/quality-playbook.agent.md and agents/quality-playbook-claude.agent.md describe the same six phases. SKILL.md and TOOLKIT.md describe the same workflow. |
| Enumeration and Representation Completeness | FULL | SKILL.md artifact contract table, quality_gate.sh, verification.md | The artifact contract table (SKILL.md lines 72-101) defines the canonical list of artifacts. quality_gate.sh must check for all required artifacts. verification.md must have benchmarks for all gate-enforced items. These three closed sets must be synchronized. |
| API Surface Consistency | FULL | SKILL.md JSON schema templates | SKILL.md defines the same JSON schemas in multiple places (tdd-results.json appears twice with different structures). The "API" here is the JSON schema contract that agents produce and gates validate. |
| Spec-Structured Parsing Fidelity | SKIP | N/A | quality_gate.sh uses grep-based JSON parsing (not formal parsing), but the project doesn't parse formal grammars in the spec-structured sense. The grep patterns are ad hoc by design. |

## Pattern Deep Dive — Cross-Implementation Consistency

### Phase descriptions across SKILL.md, agents, and TOOLKIT.md

**SKILL.md plan overview (lines 12-31):** Describes Phases 0-6 explicitly. No Phase 7.

**agents/quality-playbook-claude.agent.md (lines 79-85):** Describes six phases (1-6). No Phase 0, no Phase 7.

**agents/quality-playbook.agent.md (lines 110-118):** Describes six phases (1-6). No Phase 0, no Phase 7.

**ai_context/TOOLKIT.md (lines 148-152):** Describes Phase 1 through Phase 6. References Phase 0 at line 40 indirectly. No Phase 7.

**SKILL.md body (line 1890):** Contains `## Phase 7: Present, Explore, Improve (Interactive)` with full instructions.

**Gap:** Phase 7 exists in SKILL.md body but is absent from ALL cross-implementation surfaces (plan overview, both orchestrators, TOOLKIT.md). Phase 0/0b exist in SKILL.md but are absent from orchestrators.

### Installation instructions across surfaces

**AGENTS.md (lines 27-30):** Copies to `.github/skills/` only. No `.claude/skills/` instructions.

**docs_gathered/readme.md (lines 17-30):** Provides both `.github/skills/` AND `.claude/skills/quality-playbook/` paths.

**ai_context/TOOLKIT.md (lines 20-25):** Only shows `.github/skills/` path.

**agents/quality-playbook.agent.md (lines 17-19, 29-36):** Shows both Copilot and Claude Code paths.

**Gap:** AGENTS.md (the project's own bootstrap file) only shows Copilot installation. Users following AGENTS.md for Claude Code will use the wrong path structure.

### JSON schema templates for tdd-results.json

**SKILL.md Example 1 (lines 109-130):** Summary uses `tdd_verified` key.

**SKILL.md Example 2 (lines 1357-1389):** Summary uses `verified` key.

**SKILL.md normative text (line 1394):** Says summary must contain `total`, `verified`, `confirmed_open`, `red_failed`, `green_failed`.

**quality_gate.sh (line 229):** Only checks for `confirmed_open`, `red_failed`, `green_failed`.

**verification.md (line 108):** Says "TDD summary must include a `confirmed_open` count alongside `verified`, `red_failed`, and `green_failed`" — uses `verified` (matching Example 2).

**Gap:** Example 1's `tdd_verified` key contradicts the normative text's `verified` key. Neither `total` nor `verified`/`tdd_verified` is validated by quality_gate.sh.

## Pattern Deep Dive — Enumeration and Representation Completeness

### Artifact contract table vs quality_gate.sh validation

**Authoritative source:** SKILL.md artifact contract table (lines 72-101) — 27 artifact entries.

**quality_gate.sh file existence checks (lines 107-108):** Checks for: BUGS.md, REQUIREMENTS.md, QUALITY.md, PROGRESS.md, COVERAGE_MATRIX.md, COMPLETENESS_REPORT.md.

**Missing from quality_gate.sh file existence:**
- `CONTRACTS.md` — listed as Required in artifact table (line 78) but not checked by gate
- `test_functional.*` — listed as Required (line 79) but only warned, not failed, when missing (line 442)
- `RUN_CODE_REVIEW.md` — listed as Required (line 81) but not directly checked
- `RUN_INTEGRATION_TESTS.md` — listed as Required (line 82) but not directly checked
- `RUN_SPEC_AUDIT.md` — listed as Required (line 83) but not directly checked
- `RUN_TDD_TESTS.md` — listed as Required (line 84) but not directly checked
- `AGENTS.md` — listed as Required (line 89) but not checked (it's at project root)
- `EXPLORATION.md` — not in artifact table at all, but Phase 1 gate requires it

The code_reviews/ and spec_audits/ directories ARE checked. But 7 individually required artifacts from the contract table are NOT validated by quality_gate.sh. An agent could omit CONTRACTS.md, all four RUN_*.md files, and AGENTS.md, and still pass the gate.

### verification.md benchmark count

**Claim:** "45 self-check benchmarks" (stated in SKILL.md line 1661, DEVELOPMENT_CONTEXT.md, TOOLKIT.md, agents)

**Actual count in verification.md:** Benchmarks numbered 1-45. Count: 45. This is consistent.

However, the quick checklist at the bottom of verification.md (lines 253-301) has approximately 49 checklist items, some of which are duplicates of the numbered benchmarks and some of which are not explicitly numbered benchmarks. This creates ambiguity about whether the checklist is the authoritative set or the numbered benchmarks are.

## Pattern Deep Dive — API Surface Consistency

### tdd-results.json schema across surfaces

**Surface A: SKILL.md "Sidecar JSON Canonical Examples" (lines 109-130)**
```json
"summary": {
  "total": 3, "confirmed_open": 1, "red_failed": 0, "green_failed": 0, "tdd_verified": 2
}
```
Per-bug fields: `id`, `requirement`, `red_phase`, `green_phase`, `verdict`, `fix_patch_present`, `writeup_path`

**Surface B: SKILL.md "File 7: RUN_TDD_TESTS.md" (lines 1357-1389)**
```json
"summary": {
  "total": 6, "verified": 4, "confirmed_open": 1, "red_failed": 1, "green_failed": 0
}
```
Per-bug fields: `id`, `requirement`, `red_phase`, `green_phase`, `verdict`, `regression_patch`, `fix_patch`, `fix_patch_present`, `patch_gate_passed`, `writeup_path`, `junit_red`, `junit_green`, `junit_available`, `notes`

**Surface C: quality_gate.sh validation (lines 199-268)**
Checked per-bug fields: `id`, `requirement`, `red_phase`, `green_phase`, `verdict`, `fix_patch_present`, `writeup_path`
Checked summary keys: `confirmed_open`, `red_failed`, `green_failed`
Rejected non-canonical fields: `bug_id`, `bug_name`, `status`, `phase`, `result`

**Surface D: verification.md (line 105)**
Required per-bug fields: `id`, `requirement`, `red_phase`, `green_phase`, `verdict`, `fix_patch_present`, `writeup_path`

**Divergences:**
1. Summary key `tdd_verified` (Surface A) vs `verified` (Surface B) — normative text says `verified`
2. Surface B has 7 additional per-bug fields not present in Surfaces A/C/D
3. Surface C does not validate `total` or `verified`/`tdd_verified`
4. The non-canonical field rejection list in Surface C (`bug_id`, `bug_name`, `status`, `phase`, `result`) does not include `tdd_verified` — so Example 1's `tdd_verified` in summary would not be flagged as non-canonical

### integration-results.json schema consistency

**SKILL.md template (lines 1213-1244):** Uses `"recommendation": "SHIP"`, per-group fields: `group`, `name`, `use_cases`, `result`, `tests_passed`, `tests_failed`, `junit_file`, `junit_available`, `notes`.

**quality_gate.sh (lines 328-329):** Checks for: `schema_version`, `skill_version`, `date`, `project`, `recommendation`, `groups`, `summary`, `uc_coverage`.

**SKILL.md line 1247:** Lists required top-level fields matching quality_gate.sh. Consistent.

**No divergence detected** for integration-results.json — the schema is consistent across surfaces. This contrasts with tdd-results.json's inconsistency, suggesting tdd-results.json was edited/evolved more frequently.

## Candidate Bugs for Phase 2

### Candidate 1: tdd-results.json summary key inconsistency (`tdd_verified` vs `verified`)
- **Source stage:** Open Exploration (Finding 1) + API Surface Consistency pattern
- **File:line:** SKILL.md:127 (`tdd_verified`) vs SKILL.md:1384 (`verified`)
- **What to inspect:** An agent following the first canonical example will produce `tdd_verified` in the summary. The normative text at line 1394 requires `verified`. quality_gate.sh does not validate either key. The code review should verify: is `tdd_verified` at line 127 a typo that should be `verified`? And should quality_gate.sh validate the `total` and `verified`/`tdd_verified` summary keys?

### Candidate 2: Phase 7 exists in SKILL.md body but is invisible to plan overview and orchestrators
- **Source stage:** Open Exploration (Finding 2) + Cross-Implementation Consistency pattern
- **File:line:** SKILL.md:1890 (Phase 7 definition) vs SKILL.md:12-31 (plan overview, no Phase 7) vs agents/quality-playbook-claude.agent.md:79-85 (six phases)
- **What to inspect:** Is Phase 7 intentionally part of the flow or a legacy artifact? If intentional, the plan overview, Phase completion checklist, and orchestrators all need updating. If legacy, the convergence check's "skip to Phase 7" reference at line 1797 and verification.md's "Phase 7" reference at line 75 need removal.

### Candidate 3: Hardcoded `.github/skills/references/` paths break Claude Code installations
- **Source stage:** Open Exploration (Finding 3)
- **File:line:** SKILL.md:296, SKILL.md:872-877, SKILL.md:1486, SKILL.md:1514, SKILL.md:1559-1561, SKILL.md:1661
- **What to inspect:** Every Phase header that says "Read `.github/skills/references/X.md`" will fail when the skill is installed at `.claude/skills/quality-playbook/`. The code review should check whether these should use relative paths (`references/X.md`) or describe the path lookup logic used by the orchestrators.

### Candidate 4: quality_gate.sh does not validate TDD log status tags despite SKILL.md's claim
- **Source stage:** Open Exploration (Finding 4)
- **File:line:** SKILL.md:1137 (claim) vs quality_gate.sh:277-322 (implementation)
- **What to inspect:** Either quality_gate.sh should be updated to read and validate the first-line status tag of each TDD log file, or SKILL.md's claim should be corrected to say the gate only checks file existence.

### Candidate 5: Seven required artifacts from contract table are not validated by quality_gate.sh
- **Source stage:** Enumeration and Representation Completeness pattern
- **File:line:** SKILL.md:78-84,89 (artifact contract table) vs quality_gate.sh:107 (file existence checks)
- **What to inspect:** CONTRACTS.md, RUN_CODE_REVIEW.md, RUN_INTEGRATION_TESTS.md, RUN_SPEC_AUDIT.md, RUN_TDD_TESTS.md, test_functional.*, and AGENTS.md are all listed as "Required: Yes" in the artifact contract table but are not checked by quality_gate.sh's file existence validation. This means an agent could omit these files and still pass the gate.

### Candidate 6: AGENTS.md installation instructions omit Claude Code path
- **Source stage:** Cross-Implementation Consistency pattern
- **File:line:** AGENTS.md:27-30 (only `.github/skills/`) vs docs_gathered/readme.md:27-30 (both paths)
- **What to inspect:** AGENTS.md is the "read this first" file for AI agents. If it only shows Copilot installation instructions, Claude Code users will follow the wrong path structure.

### Candidate 7: Artifact contract table lists verify.sh as "Phase 5" but instructions say Phase 2
- **Source stage:** Open Exploration (Finding 5)
- **File:line:** SKILL.md:97 (artifact table says Phase 5) vs SKILL.md:531 (creation instructions in Phase 1/2) vs SKILL.md:555 (immediate integrity gate in Phase 2a)
- **What to inspect:** The "Created In" column of the artifact contract table is wrong for mechanical verification artifacts. They are created during contract extraction (Phase 2) and must be verified before any downstream artifact cites them — not deferred to Phase 5.

## Derived Requirements

### REQ-001: JSON schema templates for tdd-results.json must be internally consistent
All canonical examples and normative text for the tdd-results.json schema within SKILL.md must use identical field names. The summary object must use one canonical key name for the "verified bugs" count, and that name must be consistent across all examples, normative text, and validation logic.
- **Spec basis:** [Tier 2] SKILL.md lines 107-132 and 1357-1398

### REQ-002: Phase numbering must be consistent across plan overview, phase definitions, and orchestrators
Every phase defined in SKILL.md body must appear in the plan overview (lines 12-31), the Phase completion checklist (line 688), and both orchestrator agents. Conversely, no phase may be referenced in cross-references (like "skip to Phase N") without being defined in the plan overview.
- **Spec basis:** [Tier 2] SKILL.md lines 12-31 (plan overview) and SKILL.md line 1890 (Phase 7)

### REQ-003: Reference file paths must resolve correctly for all supported installation locations
SKILL.md's references to reference files must work when the skill is installed at `.github/skills/`, `.github/skills/quality-playbook/`, `.claude/skills/quality-playbook/`, or at the project root. Either paths must be relative (e.g., `references/X.md`) or the skill must include path resolution logic.
- **Spec basis:** [Tier 2] SKILL.md lines 296, 872-877 (hardcoded paths) and docs_gathered/readme.md lines 17-30 (installation instructions showing both paths)

### REQ-004: quality_gate.sh must validate all claims SKILL.md makes about gate enforcement
Any artifact that SKILL.md describes as "gate-enforced" or says "quality_gate.sh will check" must actually be checked by quality_gate.sh. Conversely, SKILL.md must not claim gate enforcement for checks that do not exist in quality_gate.sh.
- **Spec basis:** [Tier 2] SKILL.md line 72 ("If the gate checks for it, this skill must instruct its creation") and SKILL.md line 1137 (TDD log status tag claim)

### REQ-005: quality_gate.sh file existence checks must cover all artifacts marked "Required: Yes" in the artifact contract table
Every artifact listed as "Required: Yes" in the artifact contract table (SKILL.md lines 76-101) must be checked for existence by quality_gate.sh, or the table must be corrected to show the artifact as not gate-enforced.
- **Spec basis:** [Tier 2] SKILL.md line 72 (artifact contract principle)

### REQ-006: Duplicate content across files must remain synchronized
Where files contain identical or overlapping content (ai_context/TOOLKIT.md and docs_gathered/toolkit-documentation.md; ai_context/DEVELOPMENT_CONTEXT.md and docs_gathered/development-context.md), the content must be identical or one must clearly reference the other as canonical.
- **Spec basis:** [Tier 3] [source] — inferred from repository structure

### REQ-007: AGENTS.md must provide installation instructions for all supported agent platforms
AGENTS.md installation instructions must cover all platforms described in the README and TOOLKIT.md, including both `.github/skills/` (Copilot) and `.claude/skills/quality-playbook/` (Claude Code) paths.
- **Spec basis:** [Tier 2] docs_gathered/readme.md lines 17-30

### REQ-008: Artifact contract table "Created In" phase assignments must match actual creation instructions
The "Created In" column of the artifact contract table must reflect the phase where the skill instructions actually direct creation of each artifact.
- **Spec basis:** [Tier 2] SKILL.md line 72 and lines 97-98

## Derived Use Cases

### UC-01: User installs the quality playbook skill into a target repository
**Actor:** Developer using Claude Code or GitHub Copilot
**Trigger:** User wants to run the quality playbook on their project
**Expected outcome:** Skill files are correctly installed at the tool-specific path, and the agent can find and read SKILL.md and all reference files

### UC-02: Agent executes a full baseline playbook run (Phases 1-6)
**Actor:** AI coding agent (Claude Code, Copilot, Cursor)
**Trigger:** User says "Run the quality playbook on this project"
**Expected outcome:** Agent produces all required artifacts in quality/, all artifacts pass quality_gate.sh validation, and PROGRESS.md records completion of all phases

### UC-03: Agent produces tdd-results.json sidecar for confirmed bugs
**Actor:** AI coding agent following RUN_TDD_TESTS.md
**Trigger:** Phase 5 with confirmed bugs
**Expected outcome:** tdd-results.json conforms to the canonical schema, passes quality_gate.sh validation, and all field names match normative text

### UC-04: User runs quality_gate.sh to validate a completed playbook run
**Actor:** Developer or CI system
**Trigger:** After Phase 6 completes
**Expected outcome:** quality_gate.sh validates all required artifacts, reports PASS/FAIL/WARN for each check, and exits 0 only when all checks pass

### UC-05: User runs iteration strategies to find additional bugs
**Actor:** Developer or orchestrator agent
**Trigger:** After baseline run completes, user says "run the next iteration"
**Expected outcome:** Iteration strategy explores different code areas, produces merged exploration findings, and re-runs Phases 2-6 with combined results

### UC-06: Maintainer updates the skill and validates the change
**Actor:** Skill maintainer
**Trigger:** Editing SKILL.md or reference files
**Expected outcome:** All internal cross-references remain consistent, version stamps match, quality_gate.sh passes on benchmark repos

## Notes for Artifact Generation
- The project's "language" for test_functional.* should be shell script (`.sh`) since quality_gate.sh is the primary executable and bash is the only runtime
- The "source code" to review is primarily SKILL.md (~2069 lines of specification text) plus quality_gate.sh (~632 lines of bash)
- Requirements should focus on internal consistency of the specification rather than runtime behavior of the tested codebases
- This is a specification-primary repository: derive requirements from the specification's internal consistency, completeness, and correctness — not just from quality_gate.sh's executable code paths

## Gate Self-Check

1. **PASS** — File exists on disk with 411 lines of substantive content (threshold: 120).
2. **PASS** — quality/PROGRESS.md will be created immediately after this gate (Phase 1 checkpoint).
3. **PASS** — Derived Requirements section contains REQ-001 through REQ-008, each with specific file paths (SKILL.md:127, SKILL.md:1384, quality_gate.sh:229, etc.) and function-level references.
4. **PASS** — `## Open Exploration Findings` exists with 11 concrete findings, each with file paths and line numbers. At least 4 reference different modules (SKILL.md, quality_gate.sh, DEVELOPMENT_CONTEXT.md, AGENTS.md, agents/).
5. **PASS** — At least 3 findings trace across 2+ locations: Finding 1 (SKILL.md:127 vs SKILL.md:1382 vs quality_gate.sh:229), Finding 2 (SKILL.md:12-31 vs SKILL.md:1890 vs agents/), Finding 3 (16+ SKILL.md locations vs agents/ orchestrator path checks).
6. **PASS** — `## Quality Risks` exists with 5 ranked failure scenarios. Each names specific files and lines, describes a domain-specific failure mechanism, and explains why the code produces wrong behavior.
7. **PASS** — `## Pattern Applicability Matrix` exists evaluating all six patterns, marking 3 as FULL (Cross-Implementation Consistency, Enumeration and Representation Completeness, API Surface Consistency) and 3 as SKIP with codebase-specific rationale.
8. **PASS** — 3 patterns marked FULL in the matrix.
9. **PASS** — 3 sections with titles starting `## Pattern Deep Dive — ` exist, each with concrete file:line evidence.
10. **PASS** — All 3 pattern deep-dive sections trace code paths across 2+ files: Cross-Implementation traces SKILL.md vs agents/ vs TOOLKIT.md; Enumeration traces SKILL.md artifact table vs quality_gate.sh; API Surface traces SKILL.md examples vs quality_gate.sh vs verification.md.
11. **PASS** — `## Candidate Bugs for Phase 2` exists with 7 prioritized bug hypotheses, all with file:line references and source stage attribution.
12. **PASS** — Ensemble balance: Candidates 1-4 from open exploration; Candidate 5 from Enumeration pattern; Candidate 6 from Cross-Implementation pattern. At least 2 from open exploration (Candidates 1-4) and at least 1 from pattern (Candidate 5).
