# Experiment: Quality Playbook Applied to Non-Code Skills

**Date**: 2026-03-31
**Playbook version**: v1.2.5
**Question**: Does the quality playbook produce useful findings when applied to Markdown-based AI skill definitions instead of code?

---

## Results Summary

| Skill | Lines | Files | Overall | Best Step | Worst Step | Actionable Findings |
|-------|-------|-------|---------|-----------|------------|---------------------|
| agent-governance | 569 | 1 | High signal | Step 5a (state machines) | — | 10 (3 critical) |
| codeql | 405 | 7 | High signal | Step 5 (defensive) | Step 5a (state machines) | 7 (2 critical) |
| eval-driven-dev | 378 | 8 | High signal | Step 6 (domain knowledge) | Step 5 (defensive) | 15 (4 critical) |
| secret-scanning | 242 | 4 | High signal | Step 5d (boundaries) | Step 6 (domain), Verification | 7 (3 critical) |

---

## Signal Quality by Playbook Step (Across All 4 Skills)

| Playbook Step | Designed For | Applied To Skills | Signal |
|---------------|-------------|-------------------|--------|
| Step 4 (Specifications) | Spec documents | Skill requirements clarity | **HIGH** — found ambiguities, contradictions, untestable claims |
| Step 5 (Defensive patterns) | try/catch, null checks | Edge case handling in instructions | **HIGH** — found unhandled scenarios (no data, too much data, missing tools) |
| Step 5a (State machines) | Status fields, lifecycles | Phase dependencies in multi-step skills | **MEDIUM-HIGH** — found stuck states, missing dependency checks |
| Step 5c (Parallel path symmetry) | Analogous code paths | Consistency across categories/scenarios | **MEDIUM** — found uneven coverage across languages, providers, scenarios |
| Step 5d (Boundary conditions) | Empty/zero inputs | Edge repos (empty, monorepo, binary-only) | **MEDIUM-HIGH** — found silent truncation, unhandled scale |
| Step 6 (Domain knowledge) | System failure modes | Skill domain failure modes | **HIGH** — found Goodhart's law risk, false positive blindness, alert fatigue |
| Phase 3 (Verification) | Test suite checks | Self-check mechanisms | **HIGH** — nearly all skills lacked verification steps |

---

## Key Findings Across Skills

### The playbook's strongest contribution to skill review: verification gaps

All 4 skills lacked meaningful self-verification. None had a way for the agent (or user) to confirm that the skill's output was correct. This is the skill equivalent of "tests that don't assert anything" — the skill runs, produces output, and declares success without checking.

- **agent-governance**: No way to test that governance policies actually block what they should
- **codeql**: No post-scan sanity check (did we scan all languages? did results make sense?)
- **eval-driven-dev**: No guard against Goodhart's law — tests can pass while measuring the wrong thing
- **secret-scanning**: No mechanism to distinguish real secrets from false positives

### The playbook's second-strongest contribution: edge case blindness

Skills written for the happy path break when reality diverges:

- **codeql**: Assumes CodeQL CLI is installed, doesn't handle missing installation
- **secret-scanning**: Silent truncation at 1,000 paths-ignore entries with no warning
- **agent-governance**: Policy composition can silently create zero allowed tools
- **eval-driven-dev**: No recovery when the agent gets stuck in an iteration loop

### What didn't transfer well

- **Step 5b (Schema types)** — no direct analogue in Markdown skills (no type system)
- **Step 5c** produced findings but lower signal than for code — skills don't have the same structural symmetry that parallel code paths do
- The playbook's code-specific grep patterns and defensive pattern searches obviously don't apply

---

## Assessment

**The playbook produces genuinely useful findings on non-code skills.** The signal is highest from Steps 4, 5, 6, and Phase 3 — which are the analytical/reasoning steps rather than the mechanical code-inspection steps. This makes sense: those steps ask "what could go wrong?" and "how would you know if the output is correct?" — questions that apply to any structured instruction document.

**Recommendation**: This is worth pursuing as a formal extension. A "Skill Review Protocol" derived from the playbook could use Steps 4, 5 (adapted), 5a, 6, and Phase 3 as its core, dropping the code-specific Steps 5b, 5c, and 5d (or adapting them for structural consistency checks in instruction documents).

---

## Detailed Reports

| Skill | Report |
|-------|--------|
| agent-governance | `scores/skill_agent_governance.md` |
| codeql | `scores/skill_codeql.md` |
| eval-driven-dev | `scores/skill_eval_driven_dev.md` |
| secret-scanning | `scores/skill_secret_scanning.md` |
