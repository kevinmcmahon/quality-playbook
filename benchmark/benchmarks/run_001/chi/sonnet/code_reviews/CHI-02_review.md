# Code Review: CHI-02 — mux.go

**Reviewer:** claude-sonnet-4-6
**Date:** 2026-03-31
**File reviewed:** `mux.go` (worktree `/tmp/qpb_wt_chi_sonnet_CHI-02`)

---

## mux.go

### Line 110: BUG — `Handle()` only splits on space, not tab; extra spaces cause panic
- **Severity:** Medium
- **Description:** The worktree uses `strings.SplitN(pattern, " ", 2)` to parse `"METHOD /path"` patterns. The reference uses `strings.IndexAny(pattern, " \t")` + `strings.TrimLeft(pattern[i+1:], " \t")`, which handles both spaces and tabs and strips leading whitespace from the path component.
- **Expected:** `r.Handle("GET\t/path", h)` is parsed as method=`GET`, path=`/path`. `r.Handle("GET  /path", h)` (two spaces) is also parsed correctly.
- **Actual:** `r.Handle("GET\t/path", h)` — `SplitN` on `" "` produces one part, so the whole string is passed to `mx.handle(mALL, "GET\t/path", h)`, which panics at line 416 because the pattern does not start with `/`. `r.Handle("GET  /path", h)` produces `parts[1] == " /path"` (with a leading space), which also panics at line 416.
- **Why it matters:** Any caller using tab-separated method+path syntax or more than one space between method and path will get a panic instead of a registered route.

### Lines 121–129: BUG — `HandleFunc()` duplicates pattern-parsing instead of delegating to `Handle()`
- **Severity:** Low
- **Description:** The reference `HandleFunc` is a one-liner: `mx.Handle(pattern, handlerFn)`. The worktree re-implements the split logic (`strings.SplitN(pattern, " ", 2)`) independently. This carries the same tab/whitespace bugs as `Handle()` (lines 122–128) and diverges structurally so any future fix to `Handle()` won't propagate automatically.
- **Expected:** `HandleFunc` delegates to `Handle`, inheriting its parsing logic.
- **Actual:** `HandleFunc` has its own `SplitN`-based parsing that repeats the same deficiencies.

### Lines 374–393: BUG — `Find()` returns sub-router's local pattern, not the composite full pattern
- **Severity:** High
- **Description:** When a matching node has subroutes (i.e., a mounted subrouter), the worktree's `Find()` returns only the subrouter's local pattern. The reference captures `pattern := rctx.routePattern` **before** calling into the subrouter (because `FindRoute` in the subrouter will overwrite `rctx.routePattern`), then constructs the full path: `strings.TrimSuffix(pattern, "/*") + subPattern`.

  Worktree (lines 382–384):
  ```go
  rctx.RoutePath = mx.nextRoutePath(rctx)
  return node.subroutes.Find(rctx, method, rctx.RoutePath)
  ```
  Reference equivalent:
  ```go
  pattern := rctx.routePattern          // saved before subrouter call
  rctx.RoutePath = mx.nextRoutePath(rctx)
  subPattern := node.subroutes.Find(rctx, method, rctx.RoutePath)
  if subPattern == "" { return "" }
  pattern = strings.TrimSuffix(pattern, "/*")
  pattern += subPattern
  return pattern
  ```
- **Expected:** For a router with `Mount("/api", subRouter)` where `subRouter` has `Get("/users/{id}", h)`, `Find(rctx, "GET", "/api/users/42")` returns `"/api/users/{id}"`.
- **Actual:** Returns `"/users/{id}"` — the parent mount prefix `/api` is silently dropped.
- **Why it matters:** `Match()` (which calls `Find()`) and any caller using `Find()` to obtain canonical route patterns for mounted sub-routers will receive wrong patterns. This silently breaks route-pattern-based logging, instrumentation, and documentation generators for all mounted sub-routers.

### Lines 468–475: BUG — `r.Pattern` is never set after a route match
- **Severity:** High
- **Description:** In Go 1.22+, `http.Request.Pattern` holds the matched routing pattern. The reference sets it directly in `routeHTTP`:
  ```go
  r.Pattern = rctx.routePattern
  ```
  The worktree replaces this with `setPathValue(rctx, r)` (defined in `path_value.go`). That function only calls `r.SetPathValue(key, value)` for each URL parameter — it never assigns `r.Pattern`. There is no other location in the worktree that sets `r.Pattern`.
- **Expected:** After routing, `r.Pattern` equals the matched route pattern (e.g., `"/users/{id}"`), matching the behaviour of Go's standard `net/http` ServeMux.
- **Actual:** `r.Pattern` is always the empty string. Any middleware or handler that reads `r.Pattern` (a common pattern for observability in Go 1.22+ code) sees `""` for every request.
- **Why it matters:** Silent data loss — instrumentation that relies on `r.Pattern` (e.g., Prometheus labels, OpenTelemetry span names) will group all requests under a single empty-string pattern, destroying cardinality.

---

## Summary

| Severity | Count |
|----------|-------|
| High     | 2     |
| Medium   | 1     |
| Low      | 1     |
| **Total**| **4** |

| Finding type | Count |
|--------------|-------|
| BUG          | 4     |
| QUESTION     | 0     |

**Overall assessment: FIX FIRST**

The two High-severity bugs (`Find()` pattern prefix loss and missing `r.Pattern`) affect every application that mounts sub-routers or uses Go 1.22+ instrumentation. The `Handle()`/`HandleFunc()` parsing regressions break a documented feature (method+path shorthand syntax).
