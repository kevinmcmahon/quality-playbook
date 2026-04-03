# Code Review: middleware/strip.go

## middleware/strip.go

### Finding 1
- **Type:** BUG
- **Line:** 56
- **Severity:** Medium
- **Description:** `RedirectSlashes` uses HTTP 301 (Moved Permanently), which per RFC 7231 permits clients to change the request method from POST to GET upon following the redirect. In practice, all major browsers do exactly this. A POST request to `/path/` will be redirected to GET `/path`, silently discarding the request body. The correct status code for method-preserving permanent redirects is 308 (Permanent Redirect). This affects any non-GET/HEAD method (POST, PUT, PATCH, DELETE) that hits a path with a trailing slash.

### Finding 2
- **Type:** BUG
- **Line:** 44-48, 52
- **Severity:** Medium
- **Description:** `RedirectSlashes` constructs its redirect URL from `rctx.RoutePath` when available (line 46), but `RoutePath` is a router-internal path that may differ from the client-visible URL. When this middleware is used inside a mounted sub-router, `RoutePath` is set to the suffix after the mount point (via `mux.nextRoutePath()` at mux.go:313). For example, if a sub-router is mounted at `/api` and a request arrives at `/api/users/`, `RoutePath` will be `/users/`. The redirect will send the client to `/users` instead of the correct `/api/users`. The test at strip_test.go:104-106 confirms the middleware is designed for top-level use only, but there is no runtime guard or documentation in the godoc to prevent misuse in a mounted sub-router. In contrast, `StripSlashes` does not have this problem because it modifies the path for internal routing without issuing an external redirect.

### Finding 3
- **Type:** QUESTION
- **Line:** 25-29
- **Severity:** Low
- **Description:** In `StripSlashes`, when `rctx` is not nil but `rctx.RoutePath` is empty, the path is read from `r.URL.Path` (line 21), but the stripped result is written to `rctx.RoutePath` (line 28) rather than back to `r.URL.Path`. This means a previously-unset `RoutePath` gets populated with the stripped URL path. While chi's router checks `RoutePath` first when set, this side effect could cause unexpected behavior if downstream code relies on `RoutePath` being empty to distinguish whether a sub-router has modified the path. Is this intentional?

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 0     |
| Medium   | 2     |
| Low      | 1     |

- **Total findings:** 3 (2 BUG, 1 QUESTION)
- **Files reviewed:** middleware/strip.go
- **Overall assessment:** NEEDS DISCUSSION — The 301 redirect issue silently breaks non-GET methods, and the RoutePath-based redirect is incorrect when the middleware is used in mounted sub-routers. Neither is a crash-level bug, but both cause silent incorrect behavior for valid use cases.
