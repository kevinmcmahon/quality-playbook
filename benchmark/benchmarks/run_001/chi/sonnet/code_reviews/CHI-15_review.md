# Code Review: CHI-15 — context.go

## File Reviewed

- `context.go` in `/tmp/qpb_wt_chi_sonnet_CHI-15`

---

### context.go

- **Line 122:** [BUG] `RoutePattern()` is missing a nil receiver guard.
  - **Severity:** High
  - **Expected:** `RoutePattern()` should return `""` when called on a nil `*Context`.
  - **Actual:** If `RouteContext(ctx)` returns nil (i.e., no chi routing context was stored in the request context), then `chi.RouteContext(r.Context()).RoutePattern()` — the exact usage shown in the function's own docstring at line 115-121 — will panic with a nil pointer dereference at line 123 when `strings.Join` accesses `x.RoutePatterns`.
  - **Why it matters:** The docstring itself demonstrates this call pattern. Any middleware using the recommended pattern will panic on requests that pass through a non-chi handler or in test contexts. The master branch added `if x == nil { return "" }` at the top of `RoutePattern()` to guard against this.

- **Lines 122–125:** [BUG] `RoutePattern()` is missing the trailing slash cleanup after `replaceWildcards`.
  - **Severity:** Medium
  - **Expected:** For a request matched via `r.Mount("/api", subRouter)` where the subrouter matches `/`, `RoutePattern()` should return `"/api"`.
  - **Actual:** The joined `RoutePatterns` slice would be `["/api/*", "/"]` → joined string `"/api/*/"` → after `replaceWildcards` (which replaces `/*/` with `/`) → `"/api/"`. Without `strings.TrimSuffix`, the trailing slash is not removed, so `"/api/"` is returned.
  - **Why it matters:** Metrics and tracing systems consuming `RoutePattern()` will record `"/api/"` and `"/api"` as distinct routes (duplicate series). For subrouters mounted at any path with a root handler, every request produces an incorrect pattern with a spurious trailing slash. The master branch adds:
    ```go
    if routePattern != "/" {
        routePattern = strings.TrimSuffix(routePattern, "//")
        routePattern = strings.TrimSuffix(routePattern, "/")
    }
    ```
    after `replaceWildcards` to handle this. The `!= "/"` guard is correct — it prevents trimming the root pattern itself.

- **Lines 45–79:** [QUESTION] `methodsAllowed []methodTyp` field is absent from the `Context` struct.
  - **Severity:** Medium
  - **Description:** The master branch has `methodsAllowed []methodTyp` as a field on `Context` (and `Reset()` clears it). In master, `tree.go` appends to `rctx.methodsAllowed` when a route is found but the method doesn't match, and `mux.go` passes those collected methods to `MethodNotAllowedHandler()` to construct an `Allow` response header (required by RFC 7231 §6.5.5 for 405 responses). CHI-15 has neither the field nor the collection/propagation logic; `methodNotAllowedHandler` (mux.go:482–485) returns a bare 405 with no `Allow` header.
  - **Question:** Is the removal of `methodsAllowed` intentional for this PR? If so, 405 responses from chi will be non-conformant (RFC 7231 mandates the `Allow` header on 405). If this was accidentally dropped, the field and its usage in `tree.go` and `mux.go` need to be restored.

---

### Summary

| Type     | Count |
|----------|-------|
| BUG      | 2     |
| QUESTION | 1     |

**Files with no findings:** none (only `context.go` was in scope)

**Overall assessment: FIX FIRST**

The nil receiver panic in `RoutePattern()` is a correctness defect that fires in production for any middleware using the documented call pattern against requests that lack a chi routing context. The missing trailing slash cleanup produces incorrect route pattern strings for all subrouter-mounted routes with a root handler. Both should be resolved before merge.
