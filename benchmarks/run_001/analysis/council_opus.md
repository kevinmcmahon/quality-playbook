# Council Review: Proposed Playbook v1.2.11 Changes

**Reviewer:** Council Member (Opus)
**Date:** 2026-03-31
**Reviewing:** v1.2.10 → v1.2.11 (4 proposed changes from 3 missed defects)

---

## Change 1: Step 5c — Accessor Method Consistency

**Verdict: APPROVE**

**Reasoning:** This fills a genuine gap. Step 5c's existing "Parallel path symmetry" (line 228) addresses analogous *entities* through similar code paths (reviewers vs. assignees, readers vs. writers). But CHI-03 reveals a different pattern: multiple accessor methods on the *same type* returning different views of the *same resource*. The existing guidance wouldn't catch `Close()` using `cw.writer()` instead of `cw.w` because `Close()` and `Hijack()` aren't "parallel paths" in the sense Step 5c describes — they're sibling methods with a shared accessor choice. The proposed text correctly identifies that the audit unit is "every method on the type," not "every parallel entity."

**Risk assessment:** Low false-positive risk. The trigger condition is narrow (type with multiple accessor methods returning different views of one resource), and the action is bounded (audit all call sites on that type). This won't fire on most code — only on types with the specific accessor-method pattern, which is exactly when it's needed.

**Language-agnostic?** Yes. The pattern applies equally to Go receiver methods, Java/Kotlin class methods, Rust impl blocks, Python methods, C# properties vs. methods, etc. The "raw field vs. state-dependent method" framing is universal.

**Minor suggestion:** Consider adding one cross-language example after the Go-flavored description. Something like: "Examples: a Java class with `getConnection()` (returns pooled connection) vs. `getRawSocket()` (returns underlying socket), where some methods should use the pool but accidentally use the raw socket."

---

## Change 2: Step 5d — String Normalization on Minimal Inputs

**Verdict: APPROVE**

**Reasoning:** Step 5d's existing "Boundary conditions with empty and zero values" (line 264) focuses on *empty* inputs — empty strings, zero-length arrays, zero-size buffers. CHI-04 reveals a blind spot: the *shortest valid* input, which is not empty. `"/"` is a valid, non-empty route pattern, but `TrimSuffix("/", "/")` destroys it to `""`. The existing guidance says "trace through all arithmetic and iteration" for empty values, but doesn't say "trace string transformation chains with the shortest valid input." The proposed text correctly extends the boundary analysis from "empty" to "minimal."

The examples are well-chosen and generalize beyond routing: any code that normalizes paths, URLs, identifiers, or configuration strings is susceptible. The "each transformation is individually correct but the chain destroys minimal values" framing is the key insight, and it's stated clearly.

**Risk assessment:** Low-to-moderate. String normalization is common, so reviewers will encounter this trigger frequently. However, the action is lightweight (trace the chain with the shortest valid input), and the "look for guard clauses" heuristic gives a concrete signal to check. The risk of noise is mitigated by scoping to *normalization chains* rather than all string operations.

**Language-agnostic?** Yes. Every language has string trim/replace/join/split operations. The examples use Go syntax but the pattern is universal. Consider adding one non-Go example (e.g., Python `os.path.normpath("/")` or JavaScript `path.normalize`).

---

## Change 3: Step 3 — Test Setup Ordering

**Verdict: REVISE**

**Reasoning:** The pattern is real and well-described, but Step 3 is the wrong location. Step 3 ("Read Existing Tests") is an *exploration* step — its purpose is to understand the existing test suite's coverage, import patterns, and conventions (lines 139–161). The existing "Test harness consistency audit" in Step 3 (line 147) fits because it's about *reading* test files to find silent discovery failures (missing `[TestFixture]` attributes). But "test setup ordering" is a *defect detection* pattern — it's asking the reviewer to find bugs in test code, which is a Step 5 activity. Placing defect detection guidance in an exploration step creates a precedent that blurs the phase boundary.

Additionally, this change overlaps substantially with Change 4 (below), which places the same pattern in Step 5. Having both creates redundancy and risks the two descriptions drifting apart in future versions.

**Suggested revision:** Merge into Change 4's location (Step 5, defensive patterns). Add a one-line cross-reference in Step 3's "Test harness consistency audit" section:

> **Test setup temporal ordering.** Also check for resource creation/configuration ordering bugs in test files — see Step 5 "Test harness concurrency" for the full pattern.

This keeps Step 3 focused on exploration while ensuring the reader knows to look for temporal ordering issues when they encounter test setup code.

**Risk assessment:** The pattern itself has low false-positive risk. The concern is organizational, not technical.

**Language-agnostic?** Yes. The pattern generalizes well across languages: `httptest.NewServer` (Go), database connection pools (Java/Python), HTTP clients (all languages), message consumers (all languages). The description already lists cross-language examples.

---

## Change 4: Step 5 — Test Harness Concurrency

**Verdict: REVISE**

**Reasoning:** The pattern is valid, but the current text is too narrow and overlaps with Change 3. As written, it reads like a Go-specific tip (`httptest.NewServer()` vs. `httptest.NewUnstartedServer()`) with a vague generalization tacked on ("the pattern generalizes"). For a 10-language playbook, the generalization needs to be the primary framing, with language-specific examples as illustrations.

Additionally, the title "Test harness concurrency" is slightly misleading. The core issue isn't concurrency per se — it's *temporal ordering of configuration relative to resource activation*. A server that starts listening before it's configured is a temporal ordering bug that happens to manifest as a race condition. The framing should emphasize the ordering violation, with concurrency as the consequence.

**Suggested revision:**

> **Resource lifecycle ordering in tests.** When test setup creates resources that become "live" at construction time (servers, connection pools, message consumers, stream processors), verify that all configuration happens *before* the resource is activated. The canonical pattern:
>
> 1. Create the resource in an inert state (unstarted server, unconnected pool, unsubscribed consumer)
> 2. Apply all configuration (handlers, auth, connection limits, filters)
> 3. Start/activate the resource
>
> When code uses the "create-and-start" variant (e.g., Go's `httptest.NewServer()`, Python's `socketserver.TCPServer` with `serve_forever()` in a thread, Java's `ServerSocket` that binds immediately), any configuration applied after creation races with the first incoming request. The fix is always: use the builder/unstarted variant, configure, then start.
>
> **Detection heuristic:** Search test files for resource construction. If the resource type has both a "create-and-start" and a "create-inert" variant, and any configuration happens after the "create-and-start" call, flag it.

This version leads with the general principle, provides the detection heuristic the playbook style expects, and includes examples from multiple language ecosystems.

**Risk assessment:** Low. The detection heuristic is precise (look for configuration after create-and-start calls), and the pattern only fires on test setup code, limiting scope.

**Language-agnostic?** The revised version is. The original version leans too heavily on Go's `httptest` API.

---

## Cross-Cutting Observations

### 1. Changes 3 and 4 should be merged

Both address CHI-12 (test setup temporal ordering). Keeping them as separate additions in two different steps creates:
- Redundancy that will drift over time
- A precedent for putting defect detection in exploration steps

**Recommendation:** Single entry in Step 5 (defensive patterns) with a one-line forward reference in Step 3. See my revision for Change 3 above.

### 2. A deeper pattern these misses reveal: "exhaustive sibling audit"

All three missed defects share a common meta-pattern: **the models found the bug pattern in one location but failed to exhaustively check all siblings.**

- CHI-03: Found accessor confusion in `Hijack()` and `Push()`, didn't check `Close()`
- CHI-04: Checked boundary conditions structurally, didn't trace with the actual minimal input
- CHI-12: Reviewed test code for correctness, didn't audit the temporal semantics of test API calls

The proposed changes address each specific instance, but the playbook could benefit from a general "exhaustive sibling" principle in the code review protocol (RUN_CODE_REVIEW.md), something like:

> **Exhaustive sibling rule.** When you find a bug pattern or suspicious construct in one location, immediately grep for all siblings — every other method on the same type, every other call site of the same function, every other instance of the same string operation. Do not stop at the first finding. The most common miss in code review is finding the bug once and assuming the remaining siblings are clean.

This would be a force multiplier across all three defect classes and any future siblings-of-siblings pattern. Consider adding this as a separate Change 5 to the code review protocol rather than embedding it only in Step 5.

### 3. Language-agnostic assessment

Changes 1 and 2 are well-framed for a multi-language playbook. Changes 3 and 4 lean on Go's `httptest` API but describe a universal pattern. The revised versions I suggest above improve cross-language coverage.

### 4. No existing coverage overlap

I verified that none of the four proposed changes duplicate existing playbook content:
- Step 5c's "Parallel path symmetry" (line 228) covers entity-level parallelism, not accessor-method-level — Change 1 is additive
- Step 5d's "Boundary conditions" (line 264) covers empty/zero, not minimal-valid — Change 2 is additive
- Step 3's "Test harness consistency audit" (line 147) covers framework attributes, not temporal ordering — Changes 3/4 are additive
- The defensive_patterns.md "Concurrency Issues" section (line 329) covers thread/goroutine concurrency, not test-setup ordering — Changes 3/4 are additive

---

## Summary Table

| Change | Target | Verdict | Risk | Key Concern |
|--------|--------|---------|------|-------------|
| 1. Accessor method consistency | Step 5c | **APPROVE** | Low | None — fills a clear gap |
| 2. String normalization on minimal inputs | Step 5d | **APPROVE** | Low-moderate | Add one non-Go example |
| 3. Test setup ordering | Step 3 | **REVISE** | Low | Wrong location; merge with Change 4 |
| 4. Test harness concurrency | Step 5 | **REVISE** | Low | Too Go-specific; needs general framing |
| (proposed) 5. Exhaustive sibling rule | RUN_CODE_REVIEW.md | — | Low | Meta-pattern underlying all 3 misses |

**Overall assessment:** All four changes address real gaps. Two can go in as-is (Changes 1, 2). Two should be merged and reframed (Changes 3, 4). The deeper "exhaustive sibling audit" meta-pattern warrants a fifth change to the code review protocol.
