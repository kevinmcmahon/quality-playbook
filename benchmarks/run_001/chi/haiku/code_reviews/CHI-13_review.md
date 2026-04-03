# Code Review: tree.go (CHI-13)

## Review Summary
Reviewed the radix tree routing algorithm in tree.go, focusing on route insertion, matching logic, and parameter backtracking as per RUN_CODE_REVIEW.md protocol.

---

## BUG Findings

### BUG #1: Parameter Corruption via Empty Fallback After Pattern Mismatch
**File:** tree.go
**Lines:** 475 (primary issue), combined with 504-507
**Severity:** High

**Description:**
In the `findRoute` method's ntParam/ntRegexp case (lines 414-476), when NO param/regexp nodes match their pattern constraints, line 475 appends an empty string to `rctx.routeParams.Values`, then proceeds to recurse (line 504) with that empty value.

**The Problem:**
- Lines 421-473: Loop tries each param/regexp node, validating patterns at lines 437-439 (regex match) and 441 (no-slash check)
- When ALL nodes fail pattern validation (e.g., regex doesn't match, `continue` statements at 431, 439, 443), we exit the loop
- Line 475: Unconditionally appends empty string to routeParams.Values
- Line 504: Recursively calls with a node whose pattern FAILED validation, using the original unmatched search string (xsearch remains set to `search` via line 472)

**Concrete Attack/Bug Scenario:**
- Route pattern: `/api/{id:\d+}` (requires numeric ID)
- Request: `/api/abc` (abc is not numeric)
- Expected: No match (pattern requires digits)
- Actual:
  1. Try to match "abc" against regex `\d+` → FAILS (line 438-439)
  2. Append empty value (line 475)
  3. Recurse with unmatched "abc" and empty id parameter
  4. If recursion finds any child node (e.g., catch-all), route matches with id=""
  5. Pattern constraint violated: numeric ID requirement bypassed

**Root Cause:**
The empty append at line 475 is executed unconditionally after the for loop, regardless of whether ANY node's pattern was validated. This creates a fallback path that doesn't enforce the original pattern constraint.

**Impact on Fitness Scenarios:**
- **Scenario #2 (Parameter Corruption):** VIOLATED - Parameter constraint bypassed, incorrect values in routeParams
- **Scenario #4 (Regex Edge Cases):** VIOLATED - Regex patterns can be bypassed via empty fallback
- **Scenario #8 (Boundary Paths):** VIOLATED - Malformed paths accepted with empty parameters

**Expected Fix:**
Remove line 475 OR wrap it in a condition that only appends empty value under specific valid conditions (need clarification on the intent). The current unconditional append allows pattern-mismatched paths to proceed with corrupted parameter values.

---

### BUG #2: Multiple Empty Parameter Entries When Both Regexp and Param Node Groups Exist
**File:** tree.go
**Lines:** 475 (in loop context lines 392-516)
**Severity:** Medium

**Description:**
The outer for loop (line 392) iterates through ALL node type groups (ntStatic, ntRegexp, ntParam, ntCatchAll). The ntParam/ntRegexp case (line 414) executes for BOTH ntRegexp (index 1) and ntParam (index 2) node groups.

**The Problem:**
- When ntRegexp nodes fail pattern matching → append empty at line 475
- When ntParam nodes fail pattern matching → append empty at line 475 again
- Result: Multiple empty parameters in routeParams.Values if both groups contain nodes

**Example:**
- Route tree has both `/api/{id:\d+}` (regexp) and `/api/{name}` (param)
- Request: `/api/abc` where abc matches neither pattern
- Iteration 1 (ntRegexp): Append empty value
- Iteration 2 (ntParam): Append another empty value
- routeParams.Values now has two empty strings

**Cleanup Concern:**
While line 512 removes one value on failed recursion, this cleanup is per-iteration. If both regexp and param groups have nodes and both fail, we could end up with mismatched parameter keys/values counts.

---

## QUESTION Findings

### QUESTION #1: Unclear Intent of Line 475 Empty Parameter Append
**File:** tree.go
**Line:** 475
**Severity:** Medium

**Description:**
After exhaustively trying all param/regexp nodes and validating their patterns (lines 437-444), why append an empty value and recurse anyway?

**Specific Questions:**
- Is this intentional for handling "optional" parameters? (Chi docs suggest parameters are required)
- Should line 475 be conditional on specific node types or pattern characteristics?
- Is this dead code from a refactoring that should be removed?
- What is the intended behavior when NO pattern matches the parameter value?

**Code Context:**
```go
for idx := 0; idx < len(nds); idx++ {
    // ... validate pattern at lines 437-444 ...
    if pattern_invalid {
        continue  // Skip this node
    }
    // ... if valid, recurse and handle ...
}
// After loop: all nodes have been skipped or returned
rctx.routeParams.Values = append(rctx.routeParams.Values, "")  // Why append empty?
fin := xn.findRoute(rctx, method, xsearch)  // Recurse with unmatched path
```

**Request for Clarification:**
The protocol mandates Grep-before-claiming and reading function bodies. This code path genuinely appears to allow invalid patterns to proceed as empty parameters. Either:
1. This is a bug that should be removed
2. This is intentional for a specific routing strategy (please document)

---

## SUGGESTION Findings

### SUGGESTION #1: Node.findEdge Method Signature Inconsistency
**File:** tree.go
**Lines:** 408, 521, 560, 796
**Severity:** Low

**Description:**
Two different `findEdge` methods exist with different signatures:
- Line 521: `func (n *node) findEdge(ntyp nodeTyp, label byte) *node` - takes node type parameter
- Line 796: `func (ns nodes) findEdge(label byte) *node` - takes only label

At line 408, we call `nds.findEdge(label)` (the nodes version).
At line 560, we call `nn.findEdge(nds[0].typ, pattern[0])` (the node version).

Both are used, but this creates API inconsistency. Consider clarifying naming or consolidating if possible.

---

## Review Completion Checklist

✓ Read complete function bodies (lines 388-519)
✓ Traced data flow: pattern matching → backtracking → parameter accumulation
✓ Identified side effects: routeParams.Values mutations, xsearch state resets
✓ Mapped against Fitness Scenarios: #2, #4, #8 violated by BUG #1
✓ Verified parameter reset logic: Lines 364, 471, 512 checked
✓ Grep for append patterns: Verified all 7 append operations
✓ Checked boundary conditions: Empty paths (line 416), missing delimiters (line 427)

---

## Recommendation

**BLOCK approval** until BUG #1 and QUESTION #1 are resolved. The empty parameter append at line 475 appears to create a parameter corruption vulnerability that allows pattern-constrained routes to match incorrectly.

Suggest:
1. Clarify the intent of line 475 empty append
2. Add regression test reproducing the scenario: `/api/{id:\d+}` should NOT match request `/api/abc`
3. If intentional, add detailed comments; if not, remove or fix the logic
