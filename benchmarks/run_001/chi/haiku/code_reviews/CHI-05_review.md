# Code Review: tree.go (CHI-05)

**File**: tree.go
**Review Date**: 2026-03-31
**Reviewer**: Claude Haiku 4.5
**Protocol**: Code Review Protocol for Chi Router

## Summary

One **CRITICAL BUG** found in parameter handling during route matching with backtracking. The bug causes parameter value corruption when multiple param/regexp nodes are evaluated but none find a handler on the first try.

---

## Findings

### BUG #1: Parameter Value Leakage in findRoute Backtracking

**Type**: BUG
**Severity**: Critical
**File**: tree.go
**Line**: 469

**Description**:

Line 469 unconditionally appends an empty string to `rctx.routeParams.Values` after the param/regexp node loop exits:

```go
case ntParam, ntRegexp:
    // ... loop through param nodes (lines 421-467) ...

    rctx.routeParams.Values = append(rctx.routeParams.Values, "")  // LINE 469
```

This empty string placeholder is **only removed** at line 506, which is only reachable if:
1. The recursion at line 498 completes AND
2. `xn.typ > ntStatic` (param/regexp node) AND
3. The recursion failed to find a handler

However, the empty string is **NOT removed** and leaks into the final parameter list if:
- Code returns at line 488 (found handler when `xsearch == 0`)
- Code returns at line 500 (recursion found a handler)
- Code sets `methodNotAllowed` at line 493 without removing the value

**Impact**:

When `rctx.routeParams.Values` contains an extra empty string:
- Line 374-375 in `FindRoute()` copies this corrupted list to `rctx.URLParams.Values`
- HTTP handlers receive incorrect URL parameters with extra empty values
- Parameter keys and values become misaligned if multiple params exist on the path

**Affected Code Path**:

Lines 414-509 show the issue:
- Line 445: Appends actual param value inside loop
- Line 465-466: Resets on backtrack within loop (correct)
- **Line 469: Appends empty placeholder outside loop (problematic)**
- Lines 483-495: Early returns without cleanup
- Line 498-501: Recursive call that may return without cleanup
- Lines 504-508: Only cleans up on failure path

**Example Scenario** (reproduces the bug):

```
Routes:
  GET /users/{id:[0-9]+} → handler1
  GET /users/{name:[a-z]+} → handler2

Request: GET /users/abc

Expected behavior:
  - Should match second route, extract name="abc", return handler2

Buggy behavior:
  - First regex {id} fails to match "abc"
  - Empty string appended at line 469
  - No handler found in first branch
  - Continues to static children search
  - Returns with routeParams.Values = [""] (extra empty value)
  - handler2 receives corrupted URL params
```

**Protocol Violation**:

This violates the code review protocol requirement:
> "Grep for calls to `append` that modify `rctx.routeParams` — verify reset logic"

The append at line 469 has incomplete reset logic—it's only reset on certain code paths, not all.

---

## Other Observations

### Parameter Key/Value Sync (Lines 452, 487)

Keys are appended at lines 452 and 487 only when a handler is found. However, the empty string at line 469 could cause misalignment if:
- An empty value is added (line 469)
- Keys are added for a different node (line 487)
- The empty value never gets its corresponding keys

This compounds the parameter corruption issue.

### Node Splitting and Static Matching (Lines 179-197)

InsertRoute's node splitting logic appears correct. The `longestPrefix` function and node restoration maintain proper tree invariants.

### Regex Compilation (Lines 242-248)

Regex patterns are compiled once at insertion time and cached in `child.rex`. No recompilation on each request—this is correct.

### Boundary Conditions

- Empty path handling at line 132-136: ✓ Correct
- Empty xsearch at line 416: ✓ Short-circuits param matching
- Single-character segments: ✓ Handled by tail delimiter logic

---

## Recommended Action

**Remove or fix line 469**. The empty string append is unconditional but its removal is conditional, creating the parameter leakage window.

Options:
1. Remove the append entirely if it's not needed
2. Ensure cleanup happens on all return paths before line 469
3. Move the append into a guarded block that ensures cleanup

