# Code Review: context.go

**Reviewer:** Claude Opus
**Date:** 2026-03-31
**File:** `context.go`
**Commit:** a54874f (master)

---

### context.go

- **Line 83-96:** [BUG] `Reset()` does not clear the `methodsAllowed` field (declared at line 79). The `methodNotAllowed` bool is correctly reset to `false` at line 94, but the `methodsAllowed []methodTyp` slice is left with stale values from the previous request. When a `Context` is reused from the sync.Pool (mux.go:81-82), and the new request hits a 405 Method Not Allowed (mux.go:446-447), `rctx.methodsAllowed` is populated via `append` in tree.go:473 and tree.go:519. Because the slice is never truncated, stale methods from a prior request are included alongside the current request's allowed methods. This causes the `Allow` response header (mux.go:484-491) to advertise methods that are not actually allowed on the current route.
  **Severity:** Medium
  **Expected:** `x.methodsAllowed = x.methodsAllowed[:0]` should be added to `Reset()`.
  **Actual:** `methodsAllowed` retains values from the previous request lifecycle.

- **Line 83-96:** [QUESTION] `Reset()` sets `x.parentCtx = nil` (line 95) but does not set `x.Routes = nil` before it is reassigned in mux.go:83. This is fine since `Routes` is set to `nil` at line 84. However, for completeness: is there a reason `parentCtx` is reset last rather than alongside the other pointer fields? No functional impact observed, just noting the ordering.
  **Severity:** Low

---

### Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 0     |
| Medium   | 1     |
| Low      | 1     |

- **BUG findings:** 1 (missing `methodsAllowed` reset in pool-reused Context)
- **QUESTION findings:** 1 (field reset ordering)

**Overall assessment:** FIX FIRST — The missing `methodsAllowed` reset is a correctness bug that causes incorrect `Allow` headers on 405 responses when context objects are reused from the sync.Pool. The fix is a one-line addition to `Reset()`.
