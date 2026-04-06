# Code Review: context.go

## Summary
Reviewed context.go for correctness of routing context management, parameter accumulation, and reset logic. One HIGH severity bug found.

## Findings

### BUG #1: methodsAllowed slice not reset in Reset method
**File:** context.go
**Line:** 83-96 (Reset method)
**Severity:** High
**Description:**

The `methodsAllowed` field (declared line 79) is appended to during routing (tree.go lines 473, 519) to track allowed HTTP methods for 405 responses. However, it is never reset in the Reset() method, causing pool reuse leakage.

When the routing context is reused from a sync.Pool:
1. Request 1: Path matches but method not allowed → `methodsAllowed` populated with [GET, POST]
2. Request 2: Same context reused from pool → `methodsAllowed` still contains [GET, POST]
3. If Request 2 also triggers 405, the handler (mux.go line 447) appends new methods to the already-populated slice
4. The 405 response will include both old and new methods, causing incorrect method list in Allow header

**Fix:** Add `x.methodsAllowed = x.methodsAllowed[:0]` to the Reset method, following the pattern used for RoutePatterns (line 87), URLParams (lines 88-89), and routeParams (lines 92-93).

**Violation of protocol requirements:**
- Red flag: "Context reset not clearing all fields"
- Red flag: "Method allowed list including unsupported methods" (from previous requests)
- Defensive pattern: "Reset completeness — Context reset must clear all fields, not just some"
- Scenario #7 (Context pool safety): Concurrent requests reusing contexts must have fully cleaned state

---

## Analysis Details

**Verified against protocol guardrails:**
- ✓ Line numbers provided for all findings
- ✓ Read complete Reset method (lines 83-96) and traced reset logic
- ✓ Grepped for methodsAllowed usage in codebase to confirm bug scope
- ✓ Checked Reset() against all fields in Context struct (lines 45-80)

**Impact:**
- Fitness Scenario #7 (Context pool safety) violated
- Concurrent requests may see stale allowed methods from prior requests
- 405 response Allow header will be incorrect

**Confidence:** High — The field is clearly defined, appended to during routing, used in 405 responses, but explicitly omitted from Reset method.
