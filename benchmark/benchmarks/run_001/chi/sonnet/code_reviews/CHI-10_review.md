# Code Review: middleware/strip.go

**Reviewer:** sonnet
**Date:** 2026-03-31
**Worktree:** /tmp/qpb_wt_chi_sonnet_CHI-10

---

## middleware/strip.go

### Line 44: BUG — nil pointer dereference in `RedirectSlashes`

- **Finding type:** BUG
- **File and line:** `middleware/strip.go:44`
- **Severity:** High

`RedirectSlashes` calls `chi.RouteContext(r.Context())` on line 43, which returns `nil` when the middleware is used outside a chi router (e.g., wrapping `http.NewServeMux()`). The very next line immediately dereferences `rctx` without a nil check:

```go
// line 43
rctx := chi.RouteContext(r.Context())
// line 44 — PANICS if rctx == nil
if rctx.RoutePath != "" {
```

`chi.RouteContext` (context.go:29-32) returns `nil` via a type-assertion on the context value when the `RouteCtxKey` is absent:

```go
func RouteContext(ctx context.Context) *Context {
    val, _ := ctx.Value(RouteCtxKey).(*Context)
    return val   // nil if key not set
}
```

**Expected:** Same nil-guard pattern used in `StripSlashes` on line 17:
```go
if rctx != nil && rctx.RoutePath != "" {
```

**Actual:** `RedirectSlashes` accesses `rctx.RoutePath` unconditionally, causing a nil-pointer panic when there is no chi routing context.

**Why it matters:** `RedirectSlashes` is documented and designed as a drop-in middleware. Users commonly compose it with non-chi handlers or use it in tests. Any such usage panics immediately. The companion function `StripSlashes` in the same file correctly guards against this case. The test suite has `TestStripSlashesWithNilContext` (strip_test.go:174) covering exactly this scenario for `StripSlashes`, but no equivalent test for `RedirectSlashes`, so the nil-context crash path for `RedirectSlashes` is uncovered.

---

### Line 25: QUESTION — `StripSlashes` updates `r.URL.Path` but not `r.URL.RawPath` when `rctx == nil`

- **Finding type:** QUESTION
- **File and line:** `middleware/strip.go:25`
- **Severity:** Medium

When `rctx == nil`, `StripSlashes` strips the trailing slash by setting `r.URL.Path = newPath` (line 25) but never updates `r.URL.RawPath`. Per Go's `net/http` documentation, `r.URL.RawPath` (if non-empty) takes precedence over `r.URL.Path` for routing. A request with a percent-encoded trailing path segment — e.g., `/accounts%2Fadmin/` — will have:

- `r.URL.Path = "/accounts/admin/"` → gets stripped to `"/accounts/admin"` ✓
- `r.URL.RawPath = "/accounts%2Fadmin/"` → left unchanged ✗

Downstream routing (e.g., `http.ServeMux`) will see the unmodified `RawPath` with its trailing slash, making the strip ineffective.

**Expected:** If `r.URL.RawPath != ""`, it should also be stripped (or cleared) in the same code path.

**Actual:** Only `r.URL.Path` is updated; `r.URL.RawPath` retains the trailing slash.

**Why it matters:** Silent no-op: the stripped path is ignored and the trailing-slash request still fails to route to the intended handler, but without any error or redirect — just a 404.

---

### Line 50-51: QUESTION — `RedirectSlashes` builds redirect target from decoded `r.URL.Path` when `rctx == nil`

- **Finding type:** QUESTION
- **File and line:** `middleware/strip.go:50-51`
- **Severity:** Medium

When `rctx == nil` (path taken from `r.URL.Path`, the decoded form), `RedirectSlashes` builds the redirect target using the percent-decoded path. For a request to `/foo%2Fbar/`, `r.URL.Path` is `/foo/bar/` (decoded), so the redirect goes to `/foo/bar` — which is a different resource than `/foo%2Fbar`. The redirect silently changes the meaning of the path.

Note: This code path only exists in a future fix once the nil-dereference bug on line 44 is corrected, since currently the function panics before reaching this logic.

---

## Summary

| # | Finding | Type | Severity | Line |
|---|---------|------|----------|------|
| 1 | `RedirectSlashes`: nil pointer dereference on `rctx` with no chi routing context | BUG | High | 44 |
| 2 | `StripSlashes`: `r.URL.RawPath` not updated alongside `r.URL.Path` when `rctx == nil` | QUESTION | Medium | 25 |
| 3 | `RedirectSlashes`: redirect target uses decoded `r.URL.Path` instead of `r.URL.RawPath` | QUESTION | Medium | 50-51 |

**Overall assessment: FIX FIRST**

Finding #1 is a hard crash (nil pointer panic) triggered by a well-documented and common usage pattern. It must be fixed before shipping.
