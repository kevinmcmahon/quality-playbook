# Code Review: middleware/route_headers.go

**Reviewer:** Claude Haiku 4.5
**Date:** 2026-03-31
**File Reviewed:** middleware/route_headers.go
**Scope:** Header-based router middleware for chi HTTP router

---

## Summary

Reviewed the RouteHeaders middleware implementation against the code review protocol. Found **1 critical bug** that violates correct middleware composition patterns.

---

## Findings

### BUG #1: Missing Return Statement in Handler - Double Execution of Next Handler

**Location:** Lines 79-82
**Severity:** High
**Description:**

The `Handler` method contains a missing `return` statement after calling `next.ServeHTTP(w, r)` when no routes are set. This causes the middleware to continue executing and call the next handler a second time.

**Code Flow (when `len(hr) == 0`):**
1. Line 79: Condition `if len(hr) == 0` is true
2. Line 81: `next.ServeHTTP(w, r)` is called (handler executes)
3. Line 82: Control exits the if block WITHOUT returning
4. Lines 85-97: For loop doesn't execute (hr is empty)
5. Line 100-101: Check for "*" route - not found in empty map
6. Line 102: `next.ServeHTTP(w, r)` is called AGAIN
7. Line 103: Return statement (but handler already executed twice)

**Impact:**
- The next handler in the middleware chain is invoked twice when RouteHeaders is used with no routes
- This violates the fundamental middleware contract (call next exactly once)
- Can cause side effects: double logging, duplicate request processing, state corruption

**Expected Behavior:**
The comment on line 80 states "skip if no routes set", which requires returning from the function immediately after handling the request.

**Fix Required:**
Add `return` statement after line 81:
```go
if len(hr) == 0 {
    // skip if no routes set
    next.ServeHTTP(w, r)
    return  // <- MISSING
}
```

---

## Additional Observations

### Code Quality Notes (Non-Critical)

**Lines 50-52 (Route method) and Lines 60-62 (RouteAny method):**
- Redundant nil check: `k := hr[header]` followed by `if k == nil` check is unnecessary
- Go's `append()` handles nil slices correctly
- Not a bug, but slightly inefficient - the variable `k` is assigned but never used
- Removing lines 50-51 would simplify the code

**Lines 134-145 (Pattern Matching):**
- Pattern splitting logic: `strings.Cut(value, "*")` correctly handles wildcard patterns
- Match logic: Length check combined with prefix/suffix checking is sound
- No issues found in pattern matching implementation

---

## Fitness Scenario Checks

| Scenario | Status | Notes |
|----------|--------|-------|
| #3: Middleware ordering | ❌ FAILS | Missing return causes double invocation of next handler |
| #7: Context pool safety | ✓ PASS | No context pool operations in this middleware |
| #10: Handler nil checks | ✓ PASS | Line 101 correctly checks if middleware is nil before calling |

---

## Test Recommendations

Create a regression test to verify this bug:

```go
func TestRouteHeadersEmptyRouter_NoDoubleExecution(t *testing.T) {
    callCount := 0
    nextHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        callCount++
        w.WriteHeader(http.StatusOK)
    })

    router := middleware.RouteHeaders().Handler(nextHandler)

    req := httptest.NewRequest("GET", "/", nil)
    w := httptest.NewRecorder()

    router.ServeHTTP(w, req)

    if callCount != 1 {
        t.Errorf("expected next handler called once, got %d", callCount)
    }
}
```

---

## Sign-Off Checklist

- ✓ Read complete function body (lines 77-107)
- ✓ Traced data flow and control paths
- ✓ Mapped against fitness scenarios (#3 middleware ordering, #7 context safety, #10 nil checks)
- ✓ Verified with grep: no tests or protected paths found
- ✓ Flagged findings with exact line numbers

**Status:** ❌ **Cannot Approve** - Critical bug found. Return statement required at line 82.
