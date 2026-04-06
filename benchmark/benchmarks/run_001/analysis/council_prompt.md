# Council of Three Review: Proposed Playbook v1.2.11 Changes

You are reviewing proposed changes to a quality playbook skill (v1.2.10 → v1.2.11). The changes are derived from 3 defects that the playbook-generated code review protocol failed to catch during a benchmark against the QPB dataset (2,564 real defects from 50 open-source repos).

## Context

The quality playbook generates 6 quality artifacts for any codebase, including a code review protocol (RUN_CODE_REVIEW.md). We ran the playbook against the chi Go HTTP router (74 source files, 30 known historical defects), then used the generated code review protocol to review pre-fix commits for each defect. The playbook achieved a 52% direct hit rate and 81% direct+adjacent rate across 21 scored defects. Three defects were missed by ALL three models (Opus, Sonnet, Haiku).

## The 3 Missed Defects

### CHI-03: Method Accessor Confusion (error handling)
- `Close()` delegates to `cw.writer()` (returns encoder when compressible) instead of `cw.w` (raw writer)
- All 3 models found the SAME bug pattern in `Hijack()` and `Push()` but didn't check `Close()`
- One-character fix: `cw.writer()` → `cw.w`

### CHI-04: Boundary Value Destruction in String Normalization (validation gap)
- `TrimSuffix(routePattern, "/")` destroys root route "/" → ""
- Models reviewed the code structurally but didn't trace string ops with minimal input
- Fix: guard with `if routePattern != "/" { ... }`

### CHI-12: Test Setup Temporal Ordering (concurrency issue)
- `httptest.NewServer()` starts listening immediately; configuring after creation races
- Models reviewed test code for coding bugs but not temporal API semantics
- Fix: `NewUnstartedServer()` → configure → `Start()`

## Proposed Changes

### Change 1: Add to Step 5c (Parallel Code Paths)

**Accessor method consistency.** When a type provides multiple accessor methods that return different views of the same underlying resource (e.g., a raw field vs. a state-dependent method), audit ALL call sites to verify each uses the correct accessor. A common bug: one method is updated to use the correct accessor but sibling methods in the same type are not. Check every method on the type, not just the one that looks suspicious.

### Change 2: Add to Step 5d (Boundary conditions with empty and zero values)

**String normalization on minimal inputs.** When code applies string transformations in sequence (trim, replace, join, split), trace the transformation chain with the shortest valid input. Common destruction patterns: `TrimSuffix("/", "/")` → `""`, `strings.Replace(s, "//", "/", -1)` on `"//"` → `"/"` → different semantics, `strings.Join([]string{"/"}, "")` → `"/"` but `TrimSuffix` then destroys it. Each transformation is individually correct but the chain destroys minimal values. Look for guard clauses like `if x != "/" { ... }` — their absence on normalization chains is a bug signal.

### Change 3: Add to Step 3 (Read Existing Tests)

**Test setup ordering.** In test files, check whether resource creation and configuration happen in the correct temporal order. A common bug: `httptest.NewServer(handler)` starts accepting connections immediately — configuring the server *after* creation races with incoming requests. The same pattern appears with database pools (opening before configuring), HTTP clients (sending before setting auth), and message consumers (subscribing before setting handlers). Look for the pattern: resource created on line N, resource configured on line N+k. If the resource is "live" at creation, the configuration races. The fix is always the same: use the unstarted/builder variant, configure, then start.

### Change 4: Add to Step 5 (defensive patterns)

**Test harness concurrency.** When test setup creates servers, clients, or concurrent resources, check that the creation → configuration → start sequence is correct. `httptest.NewServer()` vs `httptest.NewUnstartedServer()` is the canonical example, but the pattern generalizes: any test resource that spawns goroutines at construction time must be fully configured before construction, not after.

## Your Task

Review each proposed change using these criteria:

1. **APPROVE** — The change is well-scoped, clearly written, and likely to improve detection without adding noise
2. **REVISE** — The change addresses a real gap but needs rewording, rescoping, or better examples
3. **REJECT** — The change is too narrow, too noisy, or addresses a pattern that's already covered

For each change, provide:
- Your verdict (APPROVE / REVISE / REJECT)
- Reasoning (2-3 sentences)
- If REVISE: specific suggested rewording
- Risk assessment: could this change cause false positives or distract from more important patterns?

Also consider:
- Are these changes language-agnostic enough for a 10-language playbook?
- Are there additional patterns these misses reveal that the proposals don't address?
- Should any changes be merged or reorganized?

Save your review to the output path specified.
