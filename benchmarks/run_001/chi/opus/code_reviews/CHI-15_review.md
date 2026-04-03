# Code Review: context.go (CHI-15)

**Reviewer:** Claude Opus 4.6
**Date:** 2026-03-31
**File:** context.go (reviewed at /tmp/qpb_wt_chi_opus_CHI-15/context.go)

---

### context.go

- **Line 86-88, 91-92:** [QUESTION] `Reset()` uses `[:0]` slicing on `RoutePatterns`, `URLParams.Keys`, `URLParams.Values`, `routeParams.Keys`, and `routeParams.Values`. This retains the backing arrays, meaning old string values (URL parameter names and values from the previous request) remain referenced in memory until overwritten by the next request. Since `Context` objects are pooled via `sync.Pool` (mux.go:79-89), sensitive routing data (user IDs, tokens in path params) could persist in memory longer than expected. This is a standard Go pool optimization pattern, but worth flagging given that the comment at line 48-50 describes `parentCtx` as "an optimization that saves 1 allocation" — the same optimization mindset may have overlooked the data-retention tradeoff. **Severity: Low.**

- **Line 100-102:** [QUESTION] `URLParam()` iterates over `URLParams.Keys` and accesses `URLParams.Values` at the same index (`x.URLParams.Values[k]`). There is no guard ensuring `len(Values) >= len(Keys)`. If a bug in tree.go or a custom route manipulation causes `len(Keys) > len(Values)`, this will panic with an index-out-of-range error at line 102. Currently, tree.go:373-374 appends both Keys and Values from `routeParams` in the same `FindRoute` call, and `routeParams.Values` accumulates entries before `routeParams.Keys` does (values at tree.go:446/478, keys at tree.go:453/492), so `len(Values) >= len(Keys)` holds in normal operation. However, the invariant is implicit and not enforced. **Severity: Low.**

- **Line 48-51:** [QUESTION] `parentCtx` is documented as enabling "using Context as a context.Context directly" — but `Context` does not implement the `context.Context` interface (no `Value()`, `Done()`, `Deadline()`, or `Err()` methods exist). The field is set at mux.go:82 and cleared at line 94, but is never read anywhere in the codebase. This is dead code. If the intent was to implement `context.Context` for the optimization described in the comment, the implementation is incomplete. If the optimization was abandoned, the field and comment are misleading. **Severity: Low.**

- **Line 129-134:** [QUESTION] `replaceWildcards()` uses recursion. Each recursive call invokes `strings.Contains` (O(n)) followed by `strings.Replace` with count=-1 (O(n)). For route patterns this is negligible, but the recursion depth equals the number of reduction passes needed (each pass removes at least one `"/*/"` occurrence). Since `RoutePattern()` at line 123 joins user-controlled `RoutePatterns` — which are appended per sub-router at tree.go:379 — a deeply nested mount hierarchy could produce a long pattern string with many wildcard segments. The function is correct but could be replaced with a simple loop for clarity and to avoid any theoretical stack depth concern. **Severity: Low.**

### Interaction with mux.go (context pool lifecycle)

- **mux.go Line 88-89:** [BUG] `pool.Put(rctx)` is called inline after `mx.handler.ServeHTTP(w, r)`, not via `defer`. If a handler or middleware panics and no `Recoverer` middleware is in the chain (or if the panic occurs before the Recoverer runs), the `pool.Put` is skipped. This causes: (1) the `Context` object leaks from the pool (minor — pool is best-effort), and (2) the `Context` remains reachable via the request's `context.Context` chain after the panic propagates, meaning `Reset()` is never called and routing data from this request persists. While chi's `Recoverer` middleware catches panics (allowing `pool.Put` to execute after the recovered `ServeHTTP` returns), this is not guaranteed — users may omit Recoverer or place it incorrectly in the middleware chain. **Severity: Medium.**

---

### Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High     | 0 |
| Medium   | 1 |
| Low      | 4 |

**Files with no findings:** N/A (only context.go was reviewed)

**Overall assessment:** SHIP IT — No critical or high severity issues found. The medium-severity pool lifecycle issue (in mux.go) is a known pattern trade-off in chi's design that relies on Recoverer middleware for panic safety. The low-severity findings are questions about implicit invariants and dead code rather than active bugs.
