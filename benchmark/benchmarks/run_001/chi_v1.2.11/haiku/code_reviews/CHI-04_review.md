# Code Review: context.go (CHI-04)

**File reviewed:** context.go
**Review date:** 2026-03-31
**Protocol:** Chi Router Code Review Protocol (RUN_CODE_REVIEW.md)

## Summary

Reviewed context.go for correctness of Context struct management, particularly the Reset() function used in the context pool lifecycle. Found **1 High severity bug** that can cause cross-request data leakage.

---

## Findings

### BUG: Missing Reset of methodsAllowed Field in Pool Context

**Type:** BUG
**Severity:** High
**File:** context.go
**Lines:** 79 (field definition), 82-96 (Reset function)

**Description:**

The `methodsAllowed` field (line 79) is not reset in the `Reset()` function (lines 82-96), creating a cross-request data leakage vulnerability when contexts are reused from the sync.Pool.

**Evidence:**

1. **Field definition (line 79):**
   ```go
   methodsAllowed   []methodTyp // allowed methods in case of a 405
   ```

2. **Reset function (lines 82-96):** Resets all other fields but omits methodsAllowed:
   ```go
   func (x *Context) Reset() {
       x.Routes = nil
       x.RoutePath = ""
       x.RouteMethod = ""
       x.RoutePatterns = x.RoutePatterns[:0]          // ✓ reset
       x.URLParams.Keys = x.URLParams.Keys[:0]        // ✓ reset
       x.URLParams.Values = x.URLParams.Values[:0]    // ✓ reset
       x.routePattern = ""                            // ✓ reset
       x.routeParams.Keys = x.routeParams.Keys[:0]    // ✓ reset
       x.routeParams.Values = x.routeParams.Values[:0] // ✓ reset
       x.methodNotAllowed = false                     // ✓ reset
       x.parentCtx = nil                              // ✓ reset
       // methodsAllowed - MISSING RESET ✗
   }
   ```

3. **methodsAllowed is actively used (tree.go:473, 519):**
   ```go
   // tree.go line 473
   rctx.methodsAllowed = append(rctx.methodsAllowed, endpoints)

   // tree.go line 519
   rctx.methodsAllowed = append(rctx.methodsAllowed, endpoints)
   ```

**Impact:**

- When a context is retrieved from the pool for a new request, `methodsAllowed` may contain stale values from the previous request
- Routes that set HTTP 405 (Method Not Allowed) responses could report incorrect allowed methods
- Responses could leak information about allowed methods from unrelated requests

**Example Scenario:**

1. Request A: routes to endpoint that allows GET, POST; methodsAllowed = [GET, POST]
2. Context returned to pool, Reset() called (but methodsAllowed not cleared)
3. Request B: routes to endpoint that allows only GET
4. If code checks methodsAllowed, it may see stale [GET, POST] instead of [GET]

**Required Fix:**

Add the following line to the Reset() function (after line 94):
```go
x.methodsAllowed = x.methodsAllowed[:0]
```

---

## Analysis of Other Fields

All other Context fields are correctly reset:
- ✓ Routes (line 84): reset to nil
- ✓ RoutePath (line 85): reset to ""
- ✓ RouteMethod (line 86): reset to ""
- ✓ RoutePatterns (line 87): reset with [:0] slice truncation
- ✓ URLParams.Keys/Values (lines 88-89): reset with [:0]
- ✓ routePattern (line 91): reset to ""
- ✓ routeParams.Keys/Values (lines 92-93): reset with [:0]
- ✓ methodNotAllowed (line 94): reset to false
- ✓ parentCtx (line 95): reset to nil
- ✗ **methodsAllowed (line 79): NOT RESET**

---

## Other Code Review Observations

### Context Helper Functions (lines 9-35)
- `URLParam()` (lines 9-15): Safely handles nil RouteContext
- `URLParamFromCtx()` (lines 17-23): Correctly delegates to RouteContext
- `RouteContext()` (lines 27-30): Safe type assertion with nil check
- `NewRouteContext()` (lines 32-35): Correctly initializes empty Context

### URLParam Method (lines 100-107)
- ✓ Correctly iterates backwards through Keys to find matching parameter
- ✓ Proper handling of nested routers (last value wins)
- ✓ Returns empty string if key not found

### RoutePattern Method (lines 123-129)
- ✓ Correctly joins patterns and cleans up wildcards
- ✓ Removes trailing slashes as documented

### Helper Functions
- `replaceWildcards()` (lines 133-138): ✓ Safe recursion with strings.Replace(-1) ensuring single pass
- `RouteParams.Add()` (lines 146-149): ✓ Simple and correct append pattern

### Context Key Type (lines 154-160)
- ✓ Correct implementation of context key pattern

---

## Verification Checklist

- [x] All fields in Context struct documented in Reset()
- [x] Grep verification: methodsAllowed is actively appended in tree.go:473, 519
- [x] Pool usage context: Reset() is called during context reuse
- [x] No hallucinated findings: Bug confirmed by code inspection and grep

---

## Recommendations

1. **Critical:** Fix the missing reset of methodsAllowed field in Reset() function
2. **Testing:** Ensure regression tests exist for 405 (Method Not Allowed) responses when contexts are reused
3. **Consistency:** Verify all slice fields use the `[:0]` pattern for pool reuse
