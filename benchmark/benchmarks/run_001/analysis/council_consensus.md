# Council Consensus: v1.2.11 Proposed Changes

**Date:** 2026-03-31
**Council Members:** Opus 4.6, Sonnet 4.6, Haiku 4.5

## Voting Summary

| Change | Opus | Sonnet | Haiku | Consensus |
|--------|------|--------|-------|-----------|
| 1: Accessor method consistency (Step 5c) | APPROVE | REVISE | APPROVE | **APPROVE with integration** |
| 2: String normalization on minimal inputs (Step 5d) | APPROVE | REVISE | APPROVE | **APPROVE with multi-language examples** |
| 3: Test setup ordering (Step 3) | REVISE (wrong location) | APPROVE | APPROVE | **APPROVE** (2-1 majority) |
| 4: Test harness concurrency (Step 5) | REVISE (merge with 3) | REJECT (redundant) | REVISE (consolidate) | **REJECT** — all 3 agree it's redundant with Change 3 |

## Extra Proposals from Council

| Proposal | Source | Action |
|----------|--------|--------|
| "Exhaustive sibling rule" — when you find a bug pattern, grep for ALL siblings | Opus | **ADOPT** — meta-pattern underlying all 3 misses |
| "Symmetric library usage across multiple call sites" | Haiku | Covered by sibling rule above |

## Final Decisions

### Change 1: Accessor Method Consistency → IMPLEMENT in Step 5c

**Integrate into existing "Parallel path symmetry" block** (per Sonnet's suggestion — don't add as separate paragraph; this IS a parallel path symmetry issue).

Add after the existing "Parallel path symmetry" paragraph in Step 5c:

> **Accessor method consistency.** When a type provides multiple accessor methods that return different views of the same underlying resource (e.g., a raw field vs. a state-dependent method), audit ALL call sites to verify each uses the correct accessor. A common bug: one method is updated to use the correct accessor but sibling methods in the same type are not. Check every method on the type, not just the one that looks suspicious.

### Change 2: String Normalization on Minimal Inputs → IMPLEMENT in Step 5d

Add to the "Boundary conditions with empty and zero values" section in Step 5d. **Add cross-language examples** (per Sonnet and Opus):

> **String normalization on minimal inputs.** When code applies string transformations in sequence (trim, replace, join, split), trace the transformation chain with the shortest valid input. Common destruction patterns: Go `strings.TrimSuffix("/", "/")` → `""`, Python `"/".strip("/")` → `""`, Java `"/".replaceAll("/$", "")` → `""`. Each transformation is individually correct but the chain destroys minimal values. Look for guard clauses like `if x != "/" { ... }` or `if len(x) > 1` — their absence on normalization chains is a bug signal.

### Change 3: Test Setup Ordering → IMPLEMENT in Step 3

Add to Step 3 (Read Existing Tests), after the "Test harness consistency audit" block:

> **Test setup temporal ordering.** In test files, check whether resource creation and configuration happen in the correct temporal order. A common bug: `httptest.NewServer(handler)` starts accepting connections immediately — configuring the server *after* creation races with incoming requests. The same pattern appears with database pools (opening before configuring), HTTP clients (sending before setting auth), and message consumers (subscribing before setting handlers). Look for the pattern: resource created on line N, resource configured on line N+k. If the resource is "live" at creation, the configuration races. The fix is always the same: use the unstarted/builder variant, configure, then start.

### Change 4: Test Harness Concurrency → REJECT (redundant with Change 3)

All three models flagged redundancy. Opus wanted to merge; Sonnet wanted to reject; Haiku wanted to consolidate. The consensus is clear: Change 3 already covers the pattern. Adding a second entry in Step 5 creates maintenance burden and conflicting guidance.

### Change 5 (New): Exhaustive Sibling Rule → IMPLEMENT in RUN_CODE_REVIEW.md guardrails

Per Opus's proposal, add to the code review protocol's guardrails:

> **Exhaust the sibling set.** When you find a bug in one method of a type, grep for every other method on that type and check them for the same bug pattern. All three missed defects in the chi benchmark shared this root cause: the model found the pattern once but didn't check sibling methods, sibling call sites, or sibling test fixtures for the same issue.

This goes in the review_protocols.md reference file's Guardrails section.

## Implementation Plan

1. Copy playbook_v1.2.10 → playbook_v1.2.11
2. Edit SKILL.md:
   - Step 5c: Add accessor method consistency paragraph after "Parallel path symmetry"
   - Step 5d: Add string normalization paragraph to "Boundary conditions" section
   - Step 3: Add test setup ordering paragraph after "Test harness consistency audit"
   - Update version number to 1.2.11
3. Edit references/review_protocols.md:
   - Add "Exhaust the sibling set" guardrail
4. Record all changes and prompts
