# Code Review: context.go — CHI-04

Reviewer: sonnet
Date: 2026-03-31
File reviewed: `context.go`

---

## context.go

### Line 83–96: BUG — `Reset()` does not clear `methodsAllowed`

- **Finding type:** BUG
- **Severity:** High
- **File and line:** `context.go:83–96` (missing reset for field declared at `context.go:79`)

**Description:**
`Reset()` clears `methodNotAllowed` (line 94) but never clears `methodsAllowed`. The field is declared at line 79:

```go
methodsAllowed   []methodTyp // allowed methods in case of a 405
```

The Reset body (lines 83–96) resets every other field but omits:

```go
x.methodsAllowed = x.methodsAllowed[:0]
```

**Expected:** A pooled context returned to the sync.Pool and later reused for a new request has an empty `methodsAllowed` slice.

**Actual:** The slice retains elements from the previous request. When the new request is also a 405, `tree.go:473` and `tree.go:519` do `rctx.methodsAllowed = append(rctx.methodsAllowed, endpoints)` — appending onto the non-empty stale slice. `mux.go:447` then calls `MethodNotAllowedHandler(rctx.methodsAllowed...)`, so the `Allow` response header will include methods from the *previous* 405 request in addition to the correct methods for the current route.

**Why it matters:** Incorrect `Allow` headers are both an HTTP protocol violation (RFC 9110 §15.5.6) and an information-disclosure issue: a client could be told that methods from an unrelated route are allowed on the current path.

---

### Line 123–129: BUG — `RoutePattern()` returns `""` for root route `"/"`

- **Finding type:** BUG
- **Severity:** Medium
- **File and line:** `context.go:127`

**Description:**
`RoutePattern()` unconditionally trims a trailing `"/"` at line 127:

```go
routePattern = strings.TrimSuffix(routePattern, "//")   // line 126
routePattern = strings.TrimSuffix(routePattern, "/")    // line 127
```

When a request matches the root route `"/"`, `x.RoutePatterns` is `["/"]`. After `strings.Join` the pattern is `"/"`. `replaceWildcards("/")` leaves it as `"/"`. `strings.TrimSuffix("/", "//")` leaves it as `"/"`. Then `strings.TrimSuffix("/", "/")` returns `""`.

**Expected:** `RoutePattern()` returns `"/"` for a root route handler.

**Actual:** `RoutePattern()` returns `""`.

**Why it matters:** Instrumentation middleware — the primary documented use case for `RoutePattern()` (see comment at context.go:109–122 and `_examples/fileserver/main.go:66`) — records an empty string for root-route requests. Metrics and tracing systems that key on route pattern will collapse all root-route traffic under an empty-string label, and `http.StripPrefix` logic based on `RoutePattern()` would behave incorrectly for file servers mounted at `/`.

A guard `if routePattern != "/"` before line 127 would fix this.

---

## Summary

| Finding | File | Line | Severity | Type |
|---------|------|------|----------|------|
| `Reset()` omits `methodsAllowed` reset — stale Allow headers on 405 responses | context.go | 83–96 | High | BUG |
| `RoutePattern()` returns `""` for root route `"/"` | context.go | 127 | Medium | BUG |

- **Total BUGs:** 2 (1 High, 1 Medium)
- **Total QUESTIONs:** 0
- **Files with no findings:** n/a (only context.go reviewed)

**Overall assessment: FIX FIRST**
