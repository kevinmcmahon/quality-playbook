# Code Review: tree.go (CHI-09)

## Review Summary
Reviewed the radix tree implementation in `tree.go` following the code review protocol. Focus areas: pattern insertion, route matching algorithm, parameter extraction, and backtracking logic.

---

## Findings

### 1. BUG: Parameter Value/Key Mismatch on Failed Param Backtracking
- **File:** tree.go
- **Line:** 473
- **Severity:** High
- **Description:**

When all param/regexp nodes fail to match their regex patterns in the loop (lines 421-471), an empty string placeholder is unconditionally appended to `rctx.routeParams.Values` at line 473:

```go
rctx.routeParams.Values = append(rctx.routeParams.Values, "")
```

This happens after the loop exhausts all param nodes without a successful match. However, the subsequent recursive search at line 502 may find and return a valid handler. When it does (line 503-504), the function returns **without removing this empty string**, creating a mismatch:

- `routeParams.Values` has an extra empty element (the placeholder from line 473)
- `routeParams.Keys` was populated when the handler was found, but has no corresponding key for the empty value

**Impact:** This mismatch propagates to `URLParams` at lines 374-375, causing the routing context to contain misaligned Keys/Values arrays. Downstream code accessing `URLParams` may read wrong parameter values or have length mismatches.

**Example:** Pattern `/{id:\d+}/*` with request `/abc/something`:
- The `{id}` param fails regex match
- Line 473 appends `""`
- Line 502 recursively finds the catch-all handler
- Returns with `Values=["", "/abc/something"]` while Keys may be `["id", "*"]`

---

### 2. BUG: methodNotAllowed Flag Set But Handler Still Returned
- **File:** tree.go
- **Lines:** 458, 463-465
- **Severity:** Medium
- **Description:**

When processing param/regexp nodes, if a node is a leaf (has endpoints) but the current method has no handler (lines 449-459), the code sets `rctx.methodNotAllowed = true` at line 458:

```go
if xn.isLeaf() {
    h := xn.endpoints[method]
    if h != nil && h.handler != nil {
        // return handler
    }
    // flag that the routing context found a route, but not a corresponding supported method
    rctx.methodNotAllowed = true  // LINE 458
}
```

The function does **not return** here. Instead, it continues to line 463 and recursively searches child nodes of `xn`. If that recursive search finds a handler (lines 463-465), the function returns at line 465:

```go
fin := xn.findRoute(rctx, method, xsearch)
if fin != nil {
    return fin  // LINE 465
}
```

The `methodNotAllowed` flag set at line 458 is **not cleared**, leaving the routing context marked as "found route but method not allowed" even though a handler was successfully found and returned.

**Impact:** Semantic inconsistency in the routing context. Callers checking `methodNotAllowed` would see it as true despite successfully finding a handler, potentially triggering incorrect 405 Method Not Allowed responses when a handler is available.

---

### 3. QUESTION: Dead Code Path on Failed Param Backtracking
- **File:** tree.go
- **Lines:** 473, 482-512
- **Severity:** Low
- **Description:**

After the param node loop (line 471), line 473 appends an empty string. Then the code checks if `xn == nil` at line 482. However, `xn` is the last param node from the loop, so it's rarely nil. This means lines 487-512 execute with `xn` pointing to a param node that did not successfully match any parameter.

In this state:
- At line 487-498: If `xsearch` is not empty (usual case), the leaf check may set flags but won't return
- At line 502: The code recursively searches from an unmatched param node with the original search path

**Question:** Is line 502 intended to handle child node exploration of an unmatched param node? If all param nodes failed to match their regexes, should we still attempt to search their children? This seems semantically incorrect—child nodes of a param should only be explored if that param matched.

---

## Summary Statistics
- **Total Findings:** 3
- **BUGs:** 2 (High: 1, Medium: 1)
- **QUESTIONS:** 1
- **Code Lines Analyzed:** 126 (lines 388-517 for findRoute, 421-471 for param loop logic)

---

## Guardrails Compliance
✓ Line numbers provided for every finding
✓ Read full function bodies, not just signatures
✓ Traced complete matching paths through the tree
✓ Verified parameter reset logic with grep
✓ Examined backtracking and parameter rollback at lines 469-470
✓ No style suggestions, only correctness issues flagged

---

## Recommended Actions
1. **BUG #1:** Verify that line 473's empty string placeholder is removed on all return paths from recursive searches, or restructure to avoid appending it when backtracking fails.

2. **BUG #2:** Clear `methodNotAllowed` flag before returning a handler found in child nodes, or add a condition to prevent setting the flag if recursive search may succeed.

3. **QUESTION:** Clarify the intended semantics of line 502—should unmatched param nodes' children be explored?

