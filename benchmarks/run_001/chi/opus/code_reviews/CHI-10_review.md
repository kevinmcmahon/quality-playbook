# Code Review: CHI-10 — middleware/strip.go

## middleware/strip.go

### Finding 1
- **Line 44:** **BUG** — Severity: **High**
- `RedirectSlashes` dereferences `rctx` without a nil check (`rctx.RoutePath`), but `chi.RouteContext()` can return nil when the routing context key is absent (context.go:30 returns nil on failed type assertion). Compare with `StripSlashes` at line 17, which correctly guards with `rctx != nil && rctx.RoutePath != ""`. If `RedirectSlashes` is used outside a chi router (e.g., with stdlib `http.ServeMux` or in tests without chi context), this causes a nil pointer dereference panic at line 44.

### Finding 2
- **Line 55:** **QUESTION** — Severity: **Medium**
- `RedirectSlashes` uses a hardcoded HTTP 301 (Moved Permanently) for the redirect. 301 responses are aggressively cached by browsers, meaning a temporarily trailing-slash URL will be permanently cached as redirecting to the non-slash version. Additionally, per the HTTP spec, 301 allows user agents to change the request method from POST to GET on redirect. If the intent is only to strip slashes while preserving the HTTP method, 308 (Permanent Redirect) would be more correct. This may be intentional for backwards compatibility, but it could silently break POST/PUT/PATCH requests that happen to hit a path with a trailing slash.

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 1     |
| Medium   | 1     |
| Low      | 0     |

- **Files reviewed:** middleware/strip.go
- **Overall assessment:** **FIX FIRST** — The nil pointer dereference in `RedirectSlashes` (Finding 1) is a real crash bug that should be fixed before shipping. The inconsistency with `StripSlashes` (which does check for nil) strongly suggests this is an oversight rather than an intentional design choice.
