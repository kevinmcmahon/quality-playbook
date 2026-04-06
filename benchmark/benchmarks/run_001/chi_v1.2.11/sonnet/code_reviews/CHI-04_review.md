# Code Review: CHI-04 — context.go

**Reviewer:** sonnet
**Date:** 2026-03-31
**File reviewed:** `context.go`

---

## context.go

### Line 83–96 — BUG — `methodsAllowed` not reset in `Reset()`

**Finding type:** BUG
**Severity:** High

**Description:**
`Reset()` clears every field in `Context` except `methodsAllowed []methodTyp` (declared at line 79). All other fields — including `methodNotAllowed bool` (line 94), all `RouteParams` slices, `RoutePatterns`, and `parentCtx` — are explicitly zeroed. `methodsAllowed` is silently omitted.

**Root cause:**
`methodsAllowed` is populated via `append` in `tree.go` (lines 473 and 519) during route matching when a method mismatch is detected. It is consumed in `mux.go:447` as the argument to `MethodNotAllowedHandler`:

```go
mx.MethodNotAllowedHandler(rctx.methodsAllowed...).ServeHTTP(w, r)
```

When a `Context` is returned to `sync.Pool` and later reused for a new request, `methodsAllowed` retains its prior contents. The tree's `append` calls add new entries on top of the stale slice rather than starting fresh. The 405 response's `Allow` header then includes methods from the previous request combined with the current one.

**Expected vs. actual:**
- Expected: `Reset()` zeroes `methodsAllowed` (e.g., `x.methodsAllowed = x.methodsAllowed[:0]`), so every reused context starts with an empty allowed-methods slice.
- Actual: `methodsAllowed` is never cleared. Stale entries from a previous request persist into the next request that reuses this context from the pool.

**Why it matters:**
Under concurrent load, pool reuse causes `methodsAllowed` to accumulate entries from prior requests. A 405 response for `DELETE /users` could incorrectly advertise `Allow: GET, POST, PUT` because those methods appeared in an earlier 405 on a different route handled by the same pooled context. This is a data leak across requests that only manifests under traffic and is invisible in sequential tests.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 1     |
| Medium   | 0     |
| Low      | 0     |

**Files with no findings:** none (all findings are in `context.go`)

**Overall assessment:** FIX FIRST

The `methodsAllowed` pool-reuse bug is the sole finding but it is a meaningful correctness issue: incorrect `Allow` headers in 405 responses under load. The remaining code in `context.go` is correct — `Reset()` uses `[:0]` re-slicing (not `= nil`) for all other slices, `URLParam()` iterates backward for correct sub-router param override semantics, `RouteContext()` uses the comma-ok type assertion pattern (no bare assertion panic risk), and `URLParamFromCtx()` nil-guards before dereferencing the route context.
