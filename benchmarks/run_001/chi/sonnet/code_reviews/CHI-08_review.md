# Code Review: CHI-08
**File reviewed:** `middleware/url_format.go`
**Reviewer:** sonnet
**Date:** 2026-03-31

---

## middleware/url_format.go

### Finding 1
- **Line 8:** BUG
- **Severity:** Critical
- **Description:** Wrong import path — `"github.com/go-chi/chi"` instead of `"github.com/go-chi/chi/v5"`.
- **Expected:** `import "github.com/go-chi/chi/v5"` to match the module declared in `go.mod` (`module github.com/go-chi/chi/v5`).
- **Actual:** `import "github.com/go-chi/chi"` references the v4/unversioned module, which is a different, incompatible dependency. This will either fail to compile (if the old module is not present) or silently link against the wrong version of `chi.RouteContext`, breaking the `rctx` type returned on line 62.

---

### Finding 2
- **Line 52:** BUG
- **Severity:** High
- **Description:** `path` is always set from `r.URL.Path`, ignoring any pre-existing `rctx.RoutePath`.
- **Expected:** When chi's routing context (`rctx`) is present and `rctx.RoutePath != ""`, the middleware should operate on `rctx.RoutePath` (as in the reference implementation, lines 53–56). This matters in subrouter / `Mount` contexts where the effective routing path has already been rewritten by a parent router.
- **Actual:** The modified file unconditionally uses `r.URL.Path` (line 52), so for subrouted requests the middleware parses the full original URL instead of the already-trimmed routing path. This causes format detection to operate on the wrong segment and `rctx.RoutePath` to be set to an incorrect truncated value of the full URL rather than the subrouted path.

---

### Finding 3
- **Line 56:** BUG
- **Severity:** Medium
- **Description:** `strings.Index(path[base:], ".")` uses the **first** dot in the last path segment instead of the **last** dot.
- **Expected:** `strings.LastIndex(path[base:], ".")` (as in the reference implementation, line 60) so that for a path like `/articles/v1.2.json` the format is `"json"` and `RoutePath` is trimmed to `/articles/v1.2`.
- **Actual:** `strings.Index` finds the first dot, so `/articles/v1.2.json` produces `format = "2.json"` and `rctx.RoutePath = "/articles/v1"`. Both the extracted format string and the rewritten route path are wrong.

---

### Finding 4
- **Line 63:** BUG
- **Severity:** High
- **Description:** `rctx.RoutePath = path[:idx]` is executed without a nil check on `rctx`.
- **Expected:** Guard with `if rctx != nil` before dereferencing (as in the reference implementation, line 66). `chi.RouteContext` returns nil when the middleware is used outside a chi router (e.g., in tests or when composed with a plain `net/http` mux).
- **Actual:** If `chi.RouteContext(r.Context())` returns nil (line 62), line 63 dereferences a nil pointer, causing a runtime panic for any request handled outside a chi routing context.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 1     |
| High     | 2     |
| Medium   | 1     |
| Low      | 0     |

**Total findings: 4**

**Overall assessment: FIX FIRST**

All four findings are regressions from the reference implementation. Finding 1 (wrong import path) is a compilation-level break. Findings 2, 3, and 4 are behavioral regressions that produce wrong output or panics at runtime.
