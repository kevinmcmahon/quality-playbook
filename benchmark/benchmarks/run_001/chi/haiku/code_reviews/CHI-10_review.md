# Code Review: middleware/strip.go

**File:** middleware/strip.go
**Reviewer:** Claude Haiku 4.5
**Date:** 2026-03-31
**Protocol:** RUN_CODE_REVIEW.md

## Summary

Two bugs identified in the strip.go middleware: one missing nil check causing a panic risk in RedirectSlashes, and one logic error in StripSlashes where path source/destination become misaligned.

---

## Findings

### 1. BUG: RedirectSlashes - Nil pointer dereference

**Finding Type:** BUG
**Severity:** Critical
**File & Line:** middleware/strip.go:44
**Description:**

The `RedirectSlashes` function accesses `rctx.RoutePath` without first checking if `rctx` is nil. According to context.go:29-31, `RouteContext()` returns `*Context` and can return nil:

```go
func RouteContext(ctx context.Context) *Context {
    val, _ := ctx.Value(RouteCtxKey).(*Context)
    return val  // returns nil if key not set or wrong type
}
```

The problematic code at line 44:
```go
rctx := chi.RouteContext(r.Context())
if rctx.RoutePath != "" {  // <-- PANIC if rctx is nil
    path = rctx.RoutePath
} else {
    path = r.URL.Path
}
```

If `chi.RouteContext()` returns nil (middleware runs before chi routing, or context not properly initialized), accessing `rctx.RoutePath` will panic with a nil pointer dereference.

**Contrast with StripSlashes:**
The `StripSlashes` function on line 17 correctly checks for nil:
```go
if rctx != nil && rctx.RoutePath != "" {  // Proper nil check
    path = rctx.RoutePath
} else {
    path = r.URL.Path
}
```

**Impact:**
Service crash when `RedirectSlashes` middleware is invoked in contexts where `RouteContext` is not yet set.

---

### 2. BUG: StripSlashes - Path source/destination mismatch

**Finding Type:** BUG
**Severity:** High
**File & Lines:** middleware/strip.go:17-28
**Description:**

The `StripSlashes` function has a logic error where it determines which path to read from (lines 17-21) but doesn't track which source was used, then updates based only on whether `rctx` is nil (lines 24-27). This causes path state corruption.

Scenario: `rctx != nil` but `rctx.RoutePath == ""` (empty string) and `r.URL.Path == "/api/"`:

```go
// Line 17: condition fails because rctx.RoutePath != "" is false
if rctx != nil && rctx.RoutePath != "" {
    path = rctx.RoutePath
} else {
    path = r.URL.Path  // <-- path is set to "/api/"
}

// Lines 22-28: Strip logic
if len(path) > 1 && path[len(path)-1] == '/' {
    newPath := path[:len(path)-1]  // newPath = "/api"
    if rctx == nil {
        r.URL.Path = newPath
    } else {
        rctx.RoutePath = newPath  // <-- Updates rctx.RoutePath but...
    }
}
// Result: rctx.RoutePath="/api" but r.URL.Path="/api/" (MISMATCH!)
```

The function reads from `r.URL.Path` (line 20) but writes to `rctx.RoutePath` (line 27). The subsequent routing will see inconsistent paths: one source has the slash stripped, the other doesn't.

**Fix approach:**
Track which path source was actually used:
```go
var usedRoutePath bool
if rctx != nil && rctx.RoutePath != "" {
    path = rctx.RoutePath
    usedRoutePath = true
} else {
    path = r.URL.Path
    usedRoutePath = false
}

if len(path) > 1 && path[len(path)-1] == '/' {
    newPath := path[:len(path)-1]
    if usedRoutePath {
        rctx.RoutePath = newPath
    } else {
        r.URL.Path = newPath
    }
}
```

**Impact:**
Trailing slash stripping fails in certain contexts (when RouteContext exists but RoutePath is empty), leading to incorrect routing behavior.

---

## Checklist Against Fitness Scenarios

- ✓ #2 Parameter corruption: No parameter accumulation changes, but path state issue flagged
- ✓ #3 Middleware ordering: No middleware ordering issues detected
- ✓ #6 405 detection: No method tracking changes
- ✓ #7 Context pool safety: No pool operations in this middleware
- ✓ #8 Boundary paths: Edge case detected (empty RoutePath with trailing slash)

---

## Files Reviewed

- middleware/strip.go (complete)
- context.go (lines 1-50, for RouteContext behavior verification)

## Sign-Off Completion

- ✓ Read complete function bodies (lines 13-61)
- ✓ Traced data flow through both middleware functions
- ✓ Grep verified RouteContext nil-checking patterns in codebase
- ✓ Flagged issues with line numbers and severity
- ✓ Distinguished between BUG and QUESTION appropriately
