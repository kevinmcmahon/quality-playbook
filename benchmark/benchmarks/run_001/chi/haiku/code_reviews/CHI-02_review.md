# Code Review: mux.go

## Summary
Reviewed mux.go following the code review protocol. Found 2 bugs and 1 question related to context nil checks and error handling.

---

## Findings

### 1. BUG at line 316
**File:** mux.go
**Line:** 316
**Severity:** High
**Type:** BUG

**Issue:** Missing nil check on RouteContext return value in Mount handler.

**Code:**
```go
mountHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    rctx := RouteContext(r.Context())

    // shift the url path past the previous subrouter
    rctx.RoutePath = mx.nextRoutePath(rctx)  // Line 319 - panics if rctx is nil
```

**Problem:** RouteContext (defined in context.go lines 27-30) can return nil when the context value does not exist or the type assertion fails. The code immediately dereferences rctx at line 319 without checking if it's nil.

**Evidence:**
- RouteContext implementation (context.go:27-30) uses type assertion that can return nil
- Other code properly checks for nil: context.go lines 11, 19 use `if rctx := RouteContext(...); rctx != nil`
- Middleware files check for nil: middleware/url_format.go:54, middleware/strip.go:17

**Impact:** Will cause a panic with "invalid memory address or nil pointer dereference" if the routing context is not set up correctly.

---

### 2. BUG at line 442
**File:** mux.go
**Line:** 442
**Severity:** High
**Type:** BUG

**Issue:** Missing nil check on context type assertion in routeHTTP method.

**Code:**
```go
func (mx *Mux) routeHTTP(w http.ResponseWriter, r *http.Request) {
    // Grab the route context object
    rctx := r.Context().Value(RouteCtxKey).(*Context)  // Line 442

    // The request routing path
    routePath := rctx.RoutePath  // Line 445 - panics if rctx is nil
    ...
    if rctx.RouteMethod == "" {  // Line 458 - panics if rctx is nil
```

**Problem:** The type assertion at line 442 can fail and return nil. Go's type assertion without a second return value will return the zero value (nil for pointers). The code then immediately dereferences rctx at lines 445 and 458+ without checking if it's nil.

**Evidence:**
- Consistent with RouteContext behavior that can return nil
- Line 71 in the same file properly checks for nil: `rctx, _ := r.Context().Value(RouteCtxKey).(*Context); if rctx != nil`
- Line 478 also uses `rctx.methodNotAllowed` without nil check, compounding the issue

**Impact:** Will cause a panic if the routing context is missing from the request context. While this should not happen in normal operation (ServeHTTP sets it up), lack of defensive checks violates the protocol's defensive patterns guardrail.

---

### 3. QUESTION at line 388
**File:** mux.go
**Line:** 388
**Severity:** Medium
**Type:** QUESTION

**Issue:** Potential nil dereference when accessing endpoint pattern.

**Code:**
```go
if node != nil {
    e := node.endpoints[m]
    return e.pattern  // Line 389 - what if e is nil?
}
```

**Question:** Is `node.endpoints[m]` guaranteed to be non-nil when `node != nil`? This depends on tree.FindRoute behavior and endpoint registration logic in tree.go. If endpoints[m] can be nil, accessing e.pattern would panic.

**Recommendation:** Verify against tree.go that FindRoute only returns non-nil nodes when a matching endpoint exists, or add a nil check.

---

## Summary of Guardrails Checks

- ✓ Line numbers provided for all findings
- ✓ Read full function bodies (routeHTTP, ServeHTTP, Mount, etc.)
- ✓ Grepped for nil check patterns and RouteContext usage
- ✓ Verified against protocol's red flags and defensive patterns
- ✓ Cross-referenced with context.go implementation

## Recommendation

**High Priority:** Fix bugs at lines 316 and 442 by adding nil checks:

For line 316:
```go
rctx := RouteContext(r.Context())
if rctx == nil {
    // Handle missing context - should not occur in normal operation
    // but defensive check prevents panic
}
```

For line 442:
```go
rctx, ok := r.Context().Value(RouteCtxKey).(*Context)
if rctx == nil {
    // Handle missing context
    mx.MethodNotAllowedHandler().ServeHTTP(w, r)
    return
}
```

Follow the defensive pattern already established at line 71 for consistency.
