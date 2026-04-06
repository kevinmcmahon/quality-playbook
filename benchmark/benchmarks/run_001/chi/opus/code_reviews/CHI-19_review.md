# Code Review: tree.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-03-31
**File:** tree.go (from worktree /tmp/qpb_wt_chi_opus_CHI-19)

---

## tree.go

### Finding 1

- **Line 492:** [BUG] **Severity: High.** After the `ntParam`/`ntRegexp` for-loop (lines 433–490) exhausts all candidate nodes without finding a match, line 492 unconditionally appends an empty string to `rctx.routeParams.Values` and execution falls through to the common handling code at lines 501–538. At this point, `xn` is set to the last node from the `range nds` iteration (a non-nil param/regexp node that did NOT match), and `xsearch` still equals the original `search` (unchanged). This causes:

  1. A spurious recursive call at line 528: `xn.findRoute(rctx, method, xsearch)` recurses into the children of a non-matching param node using the full original search path.
  2. The empty string `""` appended at line 492 remains in `routeParams.Values` during this recursive call, corrupting the parameter state.

  **Concrete scenario:** For adjacent-param routes like `/{a}{b}` (where `{a}` has tail byte `{`), a request to `/xy` should return 404 because there is no `{` delimiter in `xy`. However, the spurious recursion at line 528 enters `{a}`'s children and matches `{b}` against `"xy"`, yielding an incorrect match with `a=""`, `b="xy"`.

  While the cleanup at lines 534–538 removes the extra value when the recursive call fails, it does NOT run when the recursive call *succeeds* — and the incorrect match is returned with a stale empty-string parameter value.

  **Expected:** After the param/regexp for-loop fails to match, the code should `continue` to the next node type group rather than fall through.
  **Actual:** Falls through with stale `xn` and `xsearch`, enabling incorrect route matches.

### Finding 2

- **Line 390:** [BUG] **Severity: Medium.** `rn.endpoints[method].pattern` is accessed without a nil check on the map lookup result. While `findRoute` only returns a non-nil node when `endpoints[method]` has a non-nil handler, this relies on an implicit invariant across two separate functions. If `findRoute` is ever modified to return a node under different conditions (e.g., for method-not-allowed handling), line 390 would panic with a nil pointer dereference. The same access pattern at line 395 (`rn.endpoints[method].handler`) has the same risk.

  **Expected:** Guard with `if h := rn.endpoints[method]; h != nil && h.pattern != ""`.
  **Actual:** Direct map access trusting an implicit cross-function invariant.

### Finding 3

- **Line 492:** [BUG] **Severity: Medium.** The append of `""` to `rctx.routeParams.Values` creates a Keys/Values length mismatch. At this point, Values has one more entry than Keys. If the subsequent recursive call at line 528 succeeds and returns a match (as described in Finding 1), the handler's `paramKeys` are appended to `routeParams.Keys` at line 510. But the Values slice already contains the spurious `""` from line 492, so the Keys and Values are misaligned. When `FindRoute` copies them to `URLParams` at lines 386–387, subsequent `URLParam(key)` lookups (context.go:100–107) return wrong values — each key maps to the *next* parameter's value.

  **Expected:** Keys and Values always have matching lengths and ordering.
  **Actual:** Spurious empty string in Values shifts all subsequent parameter mappings by one position.

### Finding 4

- **Lines 60–76:** [QUESTION] **Severity: Low.** `RegisterMethod` modifies package-level variables `methodMap`, `reverseMethodMap`, and `mALL` without any synchronization (mutex or sync.Once). If called concurrently from multiple goroutines (e.g., in test parallelism or during init in multiple packages), this is a data race on the maps. The example and test code calls it from `init()` or `TestMain`, which is safe, but the function's public API does not document that it must only be called during initialization.

  **Expected:** Either document the single-goroutine requirement or add synchronization.
  **Actual:** No synchronization on concurrent map writes.

### Finding 5

- **Lines 534–538:** [QUESTION] **Severity: Low.** The backtracking cleanup after a failed recursive call at line 528 uses `len(rctx.routeParams.Values) - 1` to remove the last value. This correctly undoes the append from the `default` catch-all case (line 496) and the ntParam/ntRegexp fallthrough (line 492). However, it does not use a `prevlen` snapshot like the inner param loop does (line 456/488). If the failed recursive call at line 528 inadvertently leaves extra values in `routeParams.Values` (e.g., due to a bug in a deeper recursion level), this cleanup would only remove one value instead of restoring to the correct state.

  **Expected:** Save `prevlen` before line 492/496 and restore to it at line 536, matching the pattern used in the inner loop at lines 456/488.
  **Actual:** Removes exactly one value, assuming the recursive call left Values unchanged.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High     | 1 |
| Medium   | 2 |
| Low      | 2 |

**Total findings:** 5 (3 BUG, 2 QUESTION)

**Files with no findings:** N/A (only tree.go was reviewed)

**Overall assessment:** **NEEDS DISCUSSION**

The high-severity finding (Finding 1) represents a real correctness bug in the radix trie traversal: after the param/regexp matching loop fails, the fallthrough behavior can produce incorrect route matches with corrupted URL parameters. While the triggering condition (adjacent param segments without intervening static segments) is uncommon in typical usage, the code in `addChild` does support constructing such trees, and the misrouting would be silent — returning wrong data rather than an error. This warrants discussion on whether to fix the fallthrough (adding a `continue` after the param loop) and whether to add test coverage for adjacent-param patterns.
