# Code Review: tree.go (CHI-19)

**Reviewer:** Claude Haiku 4.5
**Date:** 2026-03-31
**Protocol:** RUN_CODE_REVIEW.md

---

## Summary

Reviewed the radix tree implementation in `tree.go` with focus on:
- Pattern insertion logic (InsertRoute method, lines 138-227)
- Route matching logic (findRoute method, lines 401-544)
- Parameter accumulation and backtracking
- Edge cases in parameter reset

**Total Findings:** 1 BUG, 1 QUESTION

---

## Findings

### 1. BUG: Parameter Value Leakage When Param/Regexp Nodes Fail Before Catch-All

**File:** tree.go
**Lines:** 426-538 (specifically 492, 496, 536)
**Severity:** High
**Category:** Parameter Corruption under Overlapping Routes

#### Description

In the `findRoute` method, when a router has both regexp/param nodes AND catch-all nodes at the same tree level, a sequence of unbalanced appends/removes causes orphaned values to remain in `rctx.routeParams.Values`.

#### The Issue

The control flow in the outer loop (line 404) iterates through node types in order:
1. **Iteration with ntRegexp (type 1)**: If regexp nodes exist and none match, line 492 appends `""` to Values
2. **Iteration with ntParam (type 2)**: If param nodes exist and none match, line 492 appends `""` again to Values
3. **Iteration with ntCatchAll (type 3)**: If catch-all nodes exist, line 496 appends the `search` string to Values

This results in **up to 3 appends** to `rctx.routeParams.Values`. However, the cleanup at line 536 only removes **1 value**:

```go
if xn.typ > ntStatic {
    if len(rctx.routeParams.Values) > 0 {
        rctx.routeParams.Values = rctx.routeParams.Values[:len(rctx.routeParams.Values)-1]  // Line 536: removes only 1
    }
}
```

#### Example Scenario

Given routes:
- Pattern 1: `GET /api/{id:\d+}/users` (regexp param node)
- Pattern 2: `GET /api/{name}/profile` (param node)
- Pattern 3: `GET /api/*` (catch-all node)

Request: `GET /api/test/other` where "test" matches neither `\d+` nor triggers catch-all at this level.

**Trace:**
1. After iteration with regexp nodes: append "" (line 492), Values = [`""`]
2. After iteration with param nodes: append "" (line 492), Values = [`""`, `""`]
3. After iteration with catch-all nodes: append "test/other" (line 496), Values = [`""`, `""`, `"test/other"`]
4. Cleanup at line 536: remove 1 value, Values = [`""`, `""`]
5. **Result:** Two orphaned empty strings remain in routeParams.Values

This violates Fitness Scenario #2 (Parameter corruption) from the quality constitution.

#### Root Cause

The append at line 492 is intended to represent a failed param/regexp match but is not tracked for backtracking. The value is appended unconditionally after the inner loop (line 433) completes, without saving a checkpoint via `prevlen`.

#### Consequence

- Stale parameter values accumulate in `rctx.routeParams.Values`
- Subsequent routing contexts reusing the pool will inherit corrupted parameter values
- Visible impact: `chi.URLParam()` might return incorrect values, or parameter count mismatches could cause handlers to access wrong indices

#### Affected Code Section

```go
// Lines 426-492: Param/Regexp case
case ntParam, ntRegexp:
    // short-circuit and return no matching route for empty param values
    if xsearch == "" {
        continue
    }

    // serially loop through each node grouped by the tail delimiter
    for _, xn = range nds {
        prevlen := len(rctx.routeParams.Values)
        rctx.routeParams.Values = append(rctx.routeParams.Values, xsearch[:p])
        // ... match and search logic ...
        rctx.routeParams.Values = rctx.routeParams.Values[:prevlen]  // Reset on failure
        xsearch = search
    }

    rctx.routeParams.Values = append(rctx.routeParams.Values, "")  // LINE 492: Untracked append!

// Lines 494-499: Catch-all case
default:
    // catch-all nodes
    rctx.routeParams.Values = append(rctx.routeParams.Values, search)  // LINE 496: Another untracked append
    xn = nds[0]
    xsearch = ""

// Lines 534-538: Cleanup only removes 1 value
if xn.typ > ntStatic {
    if len(rctx.routeParams.Values) > 0 {
        rctx.routeParams.Values = rctx.routeParams.Values[:len(rctx.routeParams.Values)-1]  // Only -1!
    }
}
```

---

### 2. QUESTION: Semantics of Empty String Append at Line 492

**File:** tree.go
**Line:** 492
**Severity:** Medium
**Category:** Logic Clarity

#### Description

After the param/regexp node loop completes without a match, line 492 unconditionally appends an empty string to `rctx.routeParams.Values`:

```go
rctx.routeParams.Values = append(rctx.routeParams.Values, "")
```

#### Unclear Aspects

1. **Purpose:** What semantic meaning does this empty string represent? Is it a placeholder for a parameter that's defined in the pattern but unmatched in the search path?

2. **Condition:** The append happens regardless of whether:
   - Any param nodes were actually tried (some might be skipped via `continue` at lines 441, 444)
   - The recursive search succeeded or failed
   - The next node type (catch-all) will execute

3. **Tracking:** This value is not tracked with a `prevlen` checkpoint, so it cannot be selectively reset during backtracking. It can only be removed by the cleanup at line 536, which happens after the catch-all case.

#### Impact

If this is intentional (e.g., padding for pattern structure), it should be documented. If unintentional, it contributes to the parameter leakage issue described in BUG #1.

#### Recommendation

Clarify the intended behavior with a comment or refactor to make the logic explicit.

---

## Code Review Sign-Off Checklist

- ✓ Read complete functions (InsertRoute, findRoute, FindRoute)
- ✓ Traced parameter handling through backtracking and catch-all cases
- ✓ Mapped against Fitness Scenario #2 (Parameter corruption under overlapping routes)
- ✓ Verified node type ordering and cleanup logic
- ✓ Grepped for routeParams access points to confirm append/reset patterns

---

## Recommendations

1. **Fix BUG #1:** Either:
   - Don't append at line 492 if it's unintended
   - Track the append with a `prevlen` checkpoint before line 492
   - Adjust cleanup logic at line 536 to remove multiple values when needed

2. **Clarify QUESTION #2:** Add explicit documentation or test case for the line 492 append behavior.

3. **Regression Test:** Create a test that reproduces the parameter leakage scenario with overlapping regexp/param/catch-all nodes.
