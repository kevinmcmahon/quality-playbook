# Code Review: CHI-18 — middleware/strip.go

**Reviewer:** claude-sonnet-4-6
**Date:** 2026-03-31
**File reviewed:** `middleware/strip.go`

---

## middleware/strip.go

### Finding 1

- **Finding type:** BUG
- **File and line:** `middleware/strip.go:46` (source selection) and `middleware/strip.go:56` (redirect target)
- **Severity:** High

**Description:**

`RedirectSlashes` constructs the redirect target URL from `rctx.RoutePath` when it is non-empty, but `rctx.RoutePath` in a mounted subrouter context is the *subrouter-relative* path, not the full request path. The redirect is sent to the client, which resolves it as an absolute path on the server — so the mount prefix is silently dropped.

**Root cause trace:**

1. When chi dispatches to a mounted subrouter, `mountHandler` at `mux.go:313` sets `rctx.RoutePath = mx.nextRoutePath(rctx)`. For a subrouter mounted at `/api`, a request for `/api/foo/` results in `rctx.RoutePath = "/foo/"`.
2. The subrouter's middleware chain then runs. If `RedirectSlashes` is in that chain, line 45–46 evaluates `rctx != nil && rctx.RoutePath != ""` as true, so `path = "/foo/"`.
3. After trimming: `path = "/foo"`.
4. `http.Redirect(w, r, "/foo", 301)` at line 56 sends the client to `/foo`, not `/api/foo`.

**Expected:** The redirect target should use `r.URL.Path` (the full request path, trimmed of its trailing slash), not `rctx.RoutePath`, so that mount prefixes are preserved and the client is redirected to the correct URL.

**Actual:** When `RedirectSlashes` is placed in any subrouter's middleware stack, every trailing-slash redirect points to the wrong path (the subrouter-relative path), causing a 301 loop or a 404 at the wrong location.

**Why it matters:** This is a silent correctness failure. The middleware appears to work correctly when placed at the top-level router (where `rctx.RoutePath == ""` and `r.URL.Path` is used), but breaks silently for any mounted subrouter. Most real-world chi applications use `Mount`, so the default usage pattern triggers the bug.

---

### Finding 2

- **Finding type:** QUESTION
- **File and line:** `middleware/strip.go:25–29`
- **Severity:** Low

**Description:**

In `StripSlashes`, when `rctx != nil` but `rctx.RoutePath == ""` (the path override hasn't been set yet), the function reads `path` from `r.URL.Path` (line 21) and writes the stripped path back to `rctx.RoutePath` (line 28), but leaves `r.URL.Path` unchanged.

```
// rctx != nil, rctx.RoutePath == ""
path = r.URL.Path          // line 21: reads from URL
newPath = path[:len-1]     // strip slash
rctx.RoutePath = newPath   // line 28: writes to context only
// r.URL.Path still has trailing slash
```

After this, `rctx.RoutePath` is non-empty and chi routing correctly uses `newPath` (see `mux.go:446–451`). However, any downstream handler that reads `r.URL.Path` directly (e.g., `http.FileServer`, static asset handlers, or any non-chi handler) will still observe the original trailing slash.

**Question:** Is it intentional that `r.URL.Path` is left stale in this case? The `rctx == nil` branch at line 26 correctly updates `r.URL.Path`. The asymmetry between the two branches suggests this may be unintentional, but since chi routing itself is unaffected, it may also be an accepted limitation.

---

## Summary

| # | Type     | Severity | Location                          |
|---|----------|----------|-----------------------------------|
| 1 | BUG      | High     | `strip.go:46,56` (RedirectSlashes redirect target drops mount prefix) |
| 2 | QUESTION | Low      | `strip.go:25–29` (StripSlashes r.URL.Path not updated when rctx present but RoutePath empty) |

- **Total BUGs:** 1 (High)
- **Total QUESTIONs:** 1 (Low)
- **Files with no findings:** none (both functions in the single file have findings)

**Overall assessment: FIX FIRST**

Finding 1 is a real behavioral bug that produces incorrect redirect targets in the most common chi usage pattern (mounted subrouters). The fix is straightforward but must land before this code is relied upon in subrouter contexts.
