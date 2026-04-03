# Code Review: middleware/route_headers.go

**Reviewer:** Claude Sonnet
**Date:** 2026-03-31
**File:** `middleware/route_headers.go`

---

## middleware/route_headers.go

### Line 79–82: BUG — Missing `return` after `next.ServeHTTP` in the empty-routes guard

- **Finding type:** BUG
- **Severity:** High
- **Lines:** 79–82 (missing `return`) and 102 (second invocation)

**Description:**
The early-exit guard for an empty `HeaderRouter` calls `next.ServeHTTP(w, r)` but does not `return`. Execution falls through into the rest of the handler function. Because the map is empty, the `for` loop (line 85) has zero iterations. Then the fallback block (lines 100–103) evaluates `hr["*"]` — which also misses since the map is empty — and calls `next.ServeHTTP(w, r)` a **second time**.

**Trace when `len(hr) == 0`:**
1. Line 81: `next.ServeHTTP(w, r)` — first call
2. No `return` → falls through
3. Lines 85–97: `for` loop, zero iterations
4. Line 100: `hr["*"]` → `ok = false`
5. Line 101: `!ok` is `true`
6. Line 102: `next.ServeHTTP(w, r)` — **second call**
7. Line 103: `return`

**Expected:** When `hr` is empty, `next` is called exactly once and the handler returns.
**Actual:** `next` is called twice, causing double-invocation of the downstream handler — double response writes, double side effects (logging, metrics, request processing).

**Why it matters:** Any middleware or handler that writes to `http.ResponseWriter` will hit "superfluous response.WriteHeader call" or silently corrupt the response. For handlers that perform writes, database mutations, or emit audit events, the double-call produces visible and potentially dangerous duplicate effects.

---

### Line 85–97: QUESTION — Non-deterministic header matching order

- **Finding type:** QUESTION
- **Severity:** Low
- **Lines:** 85–97

**Description:**
`HeaderRouter` is a `map[string][]HeaderRoute`. Go map iteration order is random per run. When a request carries multiple headers that each have registered routes (e.g., both `Host` and `Origin` are configured), the middleware that executes is chosen non-deterministically. The first matching header encountered during iteration wins, but the iteration order varies per request.

**Expected:** Deterministic selection when multiple headers match (e.g., first-registered wins).
**Actual:** Arbitrary selection depending on map traversal order.

**Question:** Is this non-determinism intentional? The typical use case in the docstring configures a single header (either `Host` or `Origin`, not both), so in practice this may never matter. But if it's possible to register routes for multiple distinct headers and have multiple match simultaneously, the behavior is undefined.

---

### Line 136: QUESTION — `strings.Cut` only handles the first `*` in a pattern

- **Finding type:** QUESTION
- **Severity:** Low
- **Line:** 136

**Description:**
`NewPattern` uses `strings.Cut(value, "*")` which splits on the **first** occurrence of `*` only. If a caller passes a pattern with multiple wildcards (e.g., `"*.*.com"`), `strings.Cut` returns `prefix=""`, `suffix="*.com"`, `wildcard=true`. The `Match` function then uses `strings.HasSuffix(v, "*.com")` — matching the literal string `"*.com"` including the asterisk — rather than treating the second `*` as a wildcard.

**Expected (if multi-wildcard were supported):** `"*.*.com"` matches `"a.b.com"`.
**Actual:** `"*.*.com"` only matches strings ending with the literal `"*.com"`.

**Question:** The doc comment examples show only single-`*` patterns (`"*.example.com"`, `"*"`), so multi-wildcard may be intentionally unsupported. But there is no guard or error when a multi-wildcard pattern is registered — silent misparse produces wrong match behavior for callers who try it.

---

## Summary

| Finding | Type | Severity |
|---------|------|----------|
| Missing `return` in empty-routes guard causes double `next.ServeHTTP` invocation | BUG | High |
| Non-deterministic header matching when multiple headers are configured | QUESTION | Low |
| Multi-wildcard patterns silently misparsed by `strings.Cut` | QUESTION | Low |

**Total:** 1 BUG, 2 QUESTIONs

**Overall assessment:** FIX FIRST — the missing `return` on line 82 is an unambiguous correctness bug that causes double-invocation of the downstream handler whenever `RouteHeaders()` is used with no routes configured.
