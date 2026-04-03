# Code Review: middleware/strip.go

**File:** middleware/strip.go
**Reviewer:** Claude Haiku 4.5
**Review Date:** 2026-03-31

## Summary

Reviewed StripSlashes, RedirectSlashes, and StripPrefix middleware functions against the chi router code review protocol. Found one BUG in the StripSlashes function related to inconsistent read/write path logic.

---

## Findings

### BUG: StripSlashes inconsistent path read/write logic

**Location:** Lines 18-28
**Severity:** Medium
**Component:** Middleware (StripSlashes)

**Description:**

The StripSlashes middleware has inconsistent logic for determining which path to read from versus which path to write to when stripping trailing slashes.

**Code Pattern:**
- **Lines 18-22 (read condition):** `if rctx != nil && rctx.RoutePath != ""`
- **Lines 25-28 (write condition):** `if rctx == nil` (else writes to rctx.RoutePath)

**The Problem:**

If rctx is not nil but rctx.RoutePath is empty, the code will:
- Read the path from r.URL.Path (line 21)
- Write the stripped path to rctx.RoutePath (line 28)

This is logically inconsistent. The middleware should write to the same location it read from. If we're reading from r.URL.Path, we should update r.URL.Path. If we're reading from rctx.RoutePath, we should update rctx.RoutePath.

**Example scenario:**
- If rctx exists but rctx.RoutePath is empty string
- path variable gets set to r.URL.Path
- newPath gets written to rctx.RoutePath instead of r.URL.Path
- Sub-router continues with modified RoutePath that doesn't match the actual path being routed

**Expected fix:**

The write condition should match the read condition. For example:
```go
var readFromRoutePath bool
if rctx != nil && rctx.RoutePath != "" {
    path = rctx.RoutePath
    readFromRoutePath = true
} else {
    path = r.URL.Path
    readFromRoutePath = false
}
if len(path) > 1 && path[len(path)-1] == '/' {
    newPath := path[:len(path)-1]
    if readFromRoutePath {
        rctx.RoutePath = newPath
    } else {
        r.URL.Path = newPath
    }
}
```

Or more concisely, check the same condition for both read and write:
```go
if rctx != nil && rctx.RoutePath != "" {
    if len(rctx.RoutePath) > 1 && rctx.RoutePath[len(rctx.RoutePath)-1] == '/' {
        rctx.RoutePath = rctx.RoutePath[:len(rctx.RoutePath)-1]
    }
} else {
    if len(r.URL.Path) > 1 && r.URL.Path[len(r.URL.Path)-1] == '/' {
        r.URL.Path = r.URL.Path[:len(r.URL.Path)-1]
    }
}
```

---

## Functions Reviewed

### ✓ RedirectSlashes (lines 41-62)
- **Status:** PASS
- **Notes:** Correctly handles both rctx and non-rctx cases. Trims leading/trailing slashes safely (line 52) with proper boundary check on line 50. Includes query params correctly (line 54). Security check for "//" prefix handling is correct (lines 51-52).

### ✓ StripPrefix (lines 66-70)
- **Status:** PASS
- **Notes:** Simple wrapper around http.StripPrefix. No issues.

---

## Code Quality Observations

**Positive:**
- Boundary safety: Line 23 correctly checks `len(path) > 1` before accessing `path[len(path)-1]`
- Nil checks: Code properly checks if rctx is nil before accessing its fields
- Comment clarity: Line 51 in RedirectSlashes has good documentation for security intent

**Defensive Patterns:**
- The code attempts to handle both chi.Router (with context) and http.Handler (without context) cases
- Proper fallback logic for when RoutePath is unavailable

---

## Test Status

Reviewed existing tests in middleware/strip_test.go:
- TestStripSlashes: Tests top-level middleware (rctx == nil) ✓
- TestStripSlashesInRoute: Tests sub-router middleware (rctx != nil with RoutePath set) ✓
- TestStripSlashesWithNilContext: Tests with http.Handler (rctx == nil) ✓
- TestRedirectSlashes: Tests redirect behavior ✓
- TestStripPrefix: Tests prefix stripping ✓

**Note:** Current tests do not cover the edge case of rctx being non-nil but RoutePath being empty. This edge case should be tested or the code should be made more defensive.

---

## Recommendations

1. **Fix the inconsistent read/write logic** in StripSlashes (lines 18-28)
2. **Add a test case** for the edge condition where rctx is not nil but RoutePath is empty
3. Consider adding a defensive check: if rctx is not nil, always use/update RoutePath even if it's empty, similar to the pattern in middleware/clean_path.go

---

## Sign-Off Checklist

- [x] Read complete function bodies (not just signatures)
- [x] Traced data flow and edge cases
- [x] Verified against middleware composition pattern (protocol section 4)
- [x] Checked defensive patterns (nil checks, boundary conditions)
- [x] Reviewed test coverage
- [x] Flagged with line numbers (mandatory per protocol)
- [x] Did not suggest style changes — only correctness issues

