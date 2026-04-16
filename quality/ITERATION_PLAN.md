# Iteration Plan

## Iteration 2 (Gap Strategy)

**Strategy:** gap
**Iteration number:** 2 (first iteration after baseline)
**Date:** 2026-04-15

### Coverage map from baseline EXPLORATION.md

| Section | Subsystems covered | Findings | Depth |
|---------|-------------------|----------|-------|
| Domain and Stack | All (SKILL.md, quality_gate.sh, references, agents, ai_context) | 1 | Shallow — architecture-level overview |
| Architecture | All files mapped with roles | 1 | Moderate — table plus data flow |
| Existing Tests | quality_gate.sh, SKILL.md | 1 | Shallow — "no tests" observation |
| Specifications | SKILL.md, artifact contract table | 1 | Moderate — key rules listed |
| Open Exploration Findings | quality_gate.sh (8 findings), review_protocols.md (2), SKILL.md (1) | 11 | Deep on quality_gate.sh, thin on reference files and SKILL.md |
| Quality Risks | quality_gate.sh (5), SKILL.md (1), review_protocols.md (1) | 7 | Most risks about quality_gate.sh; SKILL.md risks thin |
| Skeletons and Dispatch | quality_gate.sh check sections, SKILL.md phase progression | 3 | Moderate — section labels listed |
| Pattern Deep Dives | Fallback parity, dispatcher return-value, cross-impl consistency, enumeration completeness | 4 | Deep on gate checks; thin on reference-file and agent-file analysis |
| Candidate Bugs | 6 candidates, all focused on quality_gate.sh or review_protocols.md | 6 | Good but narrow scope |

### Identified gaps

1. Agent definition files (agents/*.agent.md): Listed but never examined for consistency with SKILL.md.
2. TOOLKIT.md installation instructions: Never cross-referenced against SKILL.md's fallback chain.
3. quality_gate.sh repo resolution logic (lines 629-651): --all flag and bash portability not examined.
4. quality_gate.sh bash portability (set -uo with empty arrays).
5. Iteration artifact validation gap.
6. SKILL.md cross-reference accuracy between fallback chain, agent files, and TOOLKIT.md.
7. quality_gate.sh duplicate version check.
8. SKILL.md EXPLORATION.md section title enforcement.

### Net-new bugs from gap iteration: 3

- BUG-008: Bash 3.2 empty array crash (MEDIUM)
- BUG-009: TOOLKIT.md Copilot reference path mismatch (MEDIUM)
- BUG-010: Incomplete writeup WARN severity (MEDIUM)

---

## Iteration 3 (Unfiltered Strategy)

**Strategy:** unfiltered
**Iteration number:** 3 (second iteration)
**Date:** 2026-04-15

### Previous run summary

Previous iterations found 10 bugs (BUG-001 through BUG-010):
- 7 from baseline (quality_gate.sh severity mismatches, test detection, eval injection, numbering, dangling ref, AGENTS.md, version paths)
- 3 from gap iteration (bash 3.2 crash, TOOLKIT.md paths, writeup severity)

All 10 bugs have TDD-verified status with red/green logs.

### Unfiltered strategy — fresh-eyes domain-driven exploration

Reading all source files without structural constraints. Looking for anything surprising, wrong, or inconsistent based on domain expertise in specification systems, shell scripting, and quality engineering tooling.

---

## Iteration 4 (Parity Strategy)

**Strategy:** parity
**Iteration number:** 4
**Date:** 2026-04-15

### Previous run summary

Previous iterations found 14 bugs (BUG-001 through BUG-014):
- 7 from baseline (quality_gate.sh severity mismatches, test detection, eval injection, numbering, dangling ref, AGENTS.md, version paths)
- 3 from gap iteration (bash 3.2 crash, TOOLKIT.md paths, writeup severity)
- 4 from unfiltered iteration (TDD_TRACEABILITY.md, .orig file, second bash 3.2 crash, heading detection)

All 14 bugs have TDD-verified status with red/green logs.

### Parallel groups enumerated

| Group | Description | Paths |
|-------|-------------|-------|
| PG-1 | tdd-results.json vs integration-results.json validation depth | quality_gate.sh:207-291 vs 367-388 |
| PG-2 | SKILL.md Reference Files table vs actual references/ directory | SKILL.md:2075-2083 vs references/ |
| PG-3 | Global vs per-repo version detection paths | quality_gate.sh:59-67 vs 581-586 (BUG-007) |
| PG-4 | Artifact contract "Required: Yes" vs gate severity | SKILL.md:87-115 vs quality_gate.sh:107-128 (BUG-001) |
| PG-5 | Copilot agent vs Claude agent SKILL.md search order | agents/*.agent.md (DC-001) |
| PG-6 | SKILL.md fallback chain vs TOOLKIT.md installation paths | SKILL.md:48-51 vs TOOLKIT.md:22-34 (BUG-009) |
| PG-7 | SKILL.md Phase 5 artifact gate vs quality_gate.sh file checks | SKILL.md:1627-1641 vs quality_gate.sh:107-128 |
| PG-8 | tdd-results.json date validation vs integration-results.json date validation | quality_gate.sh:253-276 vs 367-388 |

### Net-new candidates: 2
- CB-15: integration-results.json validation depth asymmetry
- CB-16: Reference Files table omits 3 required reference files

---

## Iteration 5 (Adversarial Strategy)

**Strategy:** adversarial
**Iteration number:** 5
**Date:** 2026-04-15

### Previous run summary

Previous iterations found 16 bugs (BUG-001 through BUG-016):
- 7 from baseline (quality_gate.sh severity mismatches, test detection, eval injection, numbering, dangling ref, AGENTS.md, version paths)
- 3 from gap iteration (bash 3.2 crash, TOOLKIT.md paths, writeup severity)
- 4 from unfiltered iteration (TDD_TRACEABILITY.md, .orig file, second bash 3.2 crash, heading detection)
- 2 from parity iteration (integration JSON validation depth, reference table)

All 16 bugs have TDD-verified status with red/green logs.

### Adversarial targets

(a) Demoted candidates from manifest with re-promotion criteria:
- DC-001: Agent SKILL.md search order (re-promotion: show dual-installation conflict) -> FALSE POSITIVE
- DC-002: Duplicate tdd-results.json version check (re-promotion: show user misinterpretation) -> DEMOTED (code quality, not spec violation)
- DC-003: --all with empty VERSION (re-promotion: show confusing error) -> FALSE POSITIVE
- DC-004: SKILL.md "nine files" count (re-promotion: show agent under-generating) -> FALSE POSITIVE
- DC-005: Date validation impossible dates (re-promotion: show agent-generated impossible date) -> DEMOTED (real gap, not practically exploitable)
- DC-006: Phase 7 no completion gate (re-promotion: show incorrect Phase 7 output) -> FALSE POSITIVE

(b) Triage dismissals re-investigated:
- SA-07: verification.md benchmark 40 file list -> RE-PROMOTED as CB-19
- SA-09: JSON helper grep false-match -> RE-PROMOTED as CB-18
- SA-11: mechanical/ directory INFO -> FALSE POSITIVE
- SA-13: Integration sidecar WARN -> FALSE POSITIVE

(c) New adversarial findings:
- CB-17: EXPLORATION.md not in artifact contract table
- CB-18: json_key_count false PASS
- CB-19: verification.md benchmark 40 omits required artifacts

### Net-new candidates: 3
- CB-17: EXPLORATION.md missing from artifact contract table (spec inconsistency)
- CB-18: json_key_count false PASS on per-bug field validation
- CB-19: verification.md benchmark 40 omits required artifacts
