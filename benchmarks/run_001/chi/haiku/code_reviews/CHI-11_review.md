# Code Review: CHI-11 (mux.go)

**Reviewed File:** `/tmp/qpb_wt_chi_haiku_CHI-11/mux.go`

**Review Date:** 2026-03-31

**Reviewer:** Claude Haiku 4.5

---

## Summary

Found 1 BUG and 1 QUESTION. The primary issue is missing nil checks on routing context retrieval, violating the defensive patterns already established in context.go.

---

## Findings

### 1. BUG: Missing nil check on RouteContext in Mount handler

**File:** mux.go
**Line:** 301-304
**Severity:** High

**Description:**

The mount handler retrieves the routing context without checking for nil:

```go
301  rctx := RouteContext(r.Context())
302
303  // shift the url path past the previous subrouter
304  rctx.RoutePath = mx.nextRoutePath(rctx)
```

**Issue:**
- `RouteContext` (defined in context.go:27-30) returns `*Context` which can be nil if the context value is not set or not a `*Context`
- Lines 304 and 307 access `rctx.RoutePath` and `rctx.URLParams.Keys` without nil check
- This would cause a **nil pointer dereference panic** if `RouteContext` returns nil

**Evidence:**
Context.go demonstrates the correct defensive pattern:
- Line 11-12: `if rctx := RouteContext(r.Context()); rctx != nil { return rctx.URLParam(key) }`
- Line 19-20: Same pattern in `URLParamFromCtx`

The Mount handler breaks this established pattern by omitting the nil check.

**Impact:**
- Potential runtime panic in mount handlers if context is not properly initialized
- Violates the defensive patterns defined in context.go

---

### 2. QUESTION: Type assertion without error handling on RouteContext in routeHTTP

**File:** mux.go
**Line:** 413-416
**Severity:** Medium

**Description:**

The routeHTTP method retrieves the routing context using a type assertion without error handling:

```go
413  rctx := r.Context().Value(RouteCtxKey).(*Context)
414
415  // The request routing path
416  routePath := rctx.RoutePath
```

**Question:**
- The type assertion can return nil if the context value is not a `*Context`
- Line 416 immediately accesses `rctx.RoutePath` without nil check
- Should this have a nil check like the pattern in context.go lines 11 and 19?

**Note:** While ServeHTTP always sets the routing context before calling this method (line 85), defensive programming would suggest a nil check here as well. However, this may be intentionally omitted if routeHTTP is guaranteed to only be called after ServeHTTP has initialized the context.

---

## Checklist Against Protocol

✓ Line numbers are mandatory — flagged exact lines
✓ Read function bodies, not just signatures — traced data flow in ServeHTTP, Mount, routeHTTP
✓ Grep before claiming missing — verified nil checks throughout file
✓ Middleware freeze check (lines 99-100) — PASS: panic on middleware-after-routes
✓ Context pool Get/Put (lines 79, 89) — PASS: context.Reset() called before use
✓ Handler nil checks verified at lines 65, 209, 229, 290
✗ Context nil checks at lines 301, 413 — MISSING

---

## Recommendation

**Priority Fix:** Add nil checks for RouteContext retrieval at line 301 to match the defensive pattern established in context.go. A minimum safe approach:

```go
rctx := RouteContext(r.Context())
if rctx == nil {
    // Handle error appropriately
    return
}
```

Consider applying the same defensive check at line 413 for consistency with context.go patterns.
