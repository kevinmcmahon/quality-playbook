# Code Review: tree.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-03-31
**File:** tree.go (worktree at /tmp/qpb_wt_chi_opus_CHI-05)

---

## Findings

### tree.go

- **Line 57-61:** [BUG] **Severity: High.** `RegisterMethod` assigns a bit value that collides with `mTRACE` for the first custom method registered. `methodMap` contains 9 entries (CONNECT through TRACE; mSTUB is excluded). So `n := len(methodMap)` is 9, and `mt := methodTyp(math.Exp2(float64(9)))` produces 512, which equals `mTRACE` (defined as `1 << 9`). The first custom HTTP method registered (e.g., "LINK", "PURGE") silently shares the same bit flag as TRACE, meaning setting a handler for the custom method overwrites the TRACE handler and vice versa. The fix should account for mSTUB occupying bit 0 outside the map, e.g., `mt := methodTyp(math.Exp2(float64(n + 1)))` or including mSTUB in methodMap.

- **Line 58:** [BUG] **Severity: Medium.** Off-by-one in the overflow guard. The check `if n > strconv.IntSize` allows `n == strconv.IntSize` (e.g., 64 on 64-bit systems), which computes `math.Exp2(64)` = 1.8e19, overflowing `int64` (max 2^63-1) when cast to `methodTyp`. The condition should be `n >= strconv.IntSize` (or more precisely `n >= strconv.IntSize - 1` to avoid the sign bit).

- **Line 469:** [QUESTION] **Severity: Medium.** After the param/regexp loop (lines 421-467) exhausts all child nodes without finding a match, an empty string is unconditionally appended to `rctx.routeParams.Values`. Execution then falls through to lines 498 where `xn.findRoute(rctx, method, xsearch)` is called with `xn` set to the last param node tried and `xsearch` reset to the original `search` path. If this recursive call somehow succeeds, the empty string would remain in `routeParams.Values`, corrupting parameter data. While the empty string is cleaned up on failure (lines 504-507), the correctness of the intermediate recursive call at line 498 with stale state is questionable. Is this intentional for some edge case, or dead/unreachable code?

- **Line 49-63:** [QUESTION] **Severity: Low.** `RegisterMethod` mutates the package-level `methodMap` and `mALL` variables without synchronization. Concurrent calls to `RegisterMethod` (or concurrent calls to `RegisterMethod` and route matching that reads `methodMap`) would cause a data race. The expected usage is calling `RegisterMethod` in `init()` before any routing, but this invariant is not enforced or documented in the function itself.

- **Line 61:** [QUESTION] **Severity: Low.** `math.Exp2(float64(n))` uses floating-point arithmetic to compute a power of 2 that must be an exact integer. For large `n` values (n > 52), `float64` cannot represent `2^n` exactly, causing silent precision loss when cast to `methodTyp`. A bit shift `methodTyp(1) << n` would be both correct and clearer. (In practice, the overflow guard at line 58 prevents `n` from reaching 52 on 64-bit systems, but the approach is fragile.)

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 1     |
| Medium   | 2     |
| Low      | 2     |

**Total findings:** 5 (2 BUG, 3 QUESTION)

**Overall assessment:** FIX FIRST

The `RegisterMethod` bit collision (line 57-61) is a confirmed functional bug that causes the first custom HTTP method to silently conflict with TRACE. The custom-method example in `_examples/custom-method/main.go` registers LINK, UNLINK, and WOOHOO, meaning LINK would collide with TRACE, making this reproducible with the project's own example code. The routing trie logic (`InsertRoute`, `findRoute`, `addChild`, `replaceChild`) is otherwise well-structured, with correct prefix splitting, proper backtracking cleanup of `routeParams.Values`, and correct binary search in `findEdge`.
