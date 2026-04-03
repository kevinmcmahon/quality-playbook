# Code Review: mux.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-03-31
**File reviewed:** mux.go (from /tmp/qpb_wt_chi_opus_CHI-11)
**Focus areas:** Context Pool Lifecycle, Mount Handler Propagation, Middleware Chain Construction

---

### mux.go

- **Line 89:** [BUG] **Severity: Medium.** `mx.pool.Put(rctx)` is not deferred. The context is obtained from the pool at line 79 via `mx.pool.Get()`, but the `Put` at line 89 is a plain (non-deferred) call after `mx.handler.ServeHTTP(w, r)` at line 88. If the handler chain panics and no `Recoverer` middleware is installed (or if a panic occurs *before* the Recoverer in the middleware chain), `pool.Put` is never reached and the `*Context` object is leaked from the pool. While the Recoverer middleware will catch panics that occur *within* its scope, any panic in a middleware registered *before* Recoverer, or in a setup without Recoverer, causes a permanent context leak. The fix is to use `defer mx.pool.Put(rctx)` after the `pool.Get()` call. Expected: `pool.Put` always executes after `pool.Get`. Actual: `pool.Put` is skipped on panic.

- **Line 85 + 89:** [QUESTION] **Severity: Low.** After `pool.Put(rctx)` at line 89 returns rctx to the pool for reuse, the request's `context.Context` (created at line 85 via `r.WithContext(context.WithValue(..., rctx))`) still holds a live reference to the now-pooled `rctx`. If any handler spawns a goroutine that retains a reference to `r.Context()` and accesses routing data (e.g., `chi.URLParam(r, ...)`) after `ServeHTTP` returns, it will observe a context being concurrently mutated by a subsequent request. This is a known trade-off in sync.Pool-based designs, but the lack of documentation or runtime safeguards (e.g., a "recycled" flag) makes it a latent data-race risk for users who aren't aware of this constraint.

- **Line 234-238:** [QUESTION] **Severity: Low.** In `With()`, when the receiver `mx` is NOT inline (i.e., a top-level mux), the new inline mux's `middlewares` field only contains the newly passed-in middlewares, not the parent's middlewares. This works correctly because the parent's middlewares are already baked into the parent's handler chain via `updateRouteHandler()` at line 392-393, and the inline mux's `handle()` method (line 398-400) wraps only with its own middlewares. However, this asymmetry between inline and non-inline parents (lines 235-238 copy parent middlewares only when `mx.inline == true`) is subtle and could mislead future maintainers into thinking parent middlewares are lost.

---

### Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 0     |
| Medium   | 1     |
| Low      | 2     |

**Files with no findings:** N/A (only mux.go was in scope)

**Overall assessment:** NEEDS DISCUSSION — The non-deferred `pool.Put` (line 89) is a real resource leak under panic conditions. While chi's recommended setup includes the Recoverer middleware which mitigates this in practice, the pool lifecycle should be robust regardless of middleware configuration. A one-line change (`defer mx.pool.Put(rctx)`) would eliminate the issue.
