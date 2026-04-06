# Code Review: CHI-09 - tree.go

## tree.go

### Finding 1
- **Line 57-61:** [BUG] **Severity: High.** `RegisterMethod` assigns a bit value that collides with `mTRACE` for the first custom method registered. `methodMap` contains 9 standard methods (CONNECT through TRACE), so `n = len(methodMap) = 9`. The computed bit value is `math.Exp2(float64(9)) = 512`, which equals `mTRACE` (defined as `1 << 9` at line 29). This happens because `methodMap` does not include `mSTUB` (bit 0), so the count is off by one. The first custom method silently overwrites TRACE's bit position, causing TRACE handlers and the custom method to interfere with each other. The fix should use `n + 1` to account for the `mSTUB` bit not being in `methodMap`, e.g., `mt := methodTyp(math.Exp2(float64(n + 1)))`.

### Finding 2
- **Line 58:** [BUG] **Severity: Low.** Off-by-one in the overflow check: `n > strconv.IntSize` should be `n >= strconv.IntSize`. When `n == strconv.IntSize`, `Exp2(n)` produces a value that overflows the `int`-backed `methodTyp`. In practice this is unreachable (would require 55+ custom methods on 64-bit), but the check is still incorrect.

### Finding 3
- **Line 473:** [BUG] **Severity: Medium.** After the `for idx` loop (lines 421-471) exhausts all param/regexp child nodes without finding a match, an empty string is unconditionally appended to `rctx.routeParams.Values`. At this point `xn` still references the last node tried in the loop (not a matched node), and `xsearch` was reset to `search` (line 470). Execution falls through to lines 482-513, where `xn != nil` (since `nds` was non-empty), causing a spurious recursive `findRoute` call (line 502) into a non-matching node with the wrong search path. The empty string is only cleaned up at lines 509-510 if the recursion fails and `xn.typ > ntStatic`, but the unnecessary recursion can cause incorrect backtracking behavior and, in adversarial route trees, potentially match against wrong nodes. The catch-all case at line 477 has a similar pattern but is less problematic because catch-all nodes (`nds[0]`) are expected to consume the remaining path.

### Finding 4
- **Line 61:** [QUESTION] **Severity: Low.** `math.Exp2(float64(n))` converted to `methodTyp(int)` relies on float64 precision for bit-shift arithmetic. While this works for the practical range of values (n < 53), using `methodTyp(1 << uint(n))` would be more idiomatic and avoid any floating-point edge cases. Is there a reason float arithmetic is used instead of integer bit shifting?

### Finding 5
- **Lines 49-63:** [QUESTION] **Severity: Low.** `RegisterMethod` mutates the package-level `methodMap` and `mALL` without synchronization. If two goroutines call `RegisterMethod` concurrently, both the map write and the `mALL |= mt` update are racy. The expected usage pattern is `init()`-time registration (as shown in `_examples/custom-method/main.go`), but this assumption is not enforced or documented in the function's godoc. Is the lack of synchronization intentional?

### Finding 6
- **Line 378:** [QUESTION] **Severity: Medium.** In `FindRoute`, after `findRoute` returns a non-nil node `rn`, the code accesses `rn.endpoints[method].pattern` without a nil check. If `rn.endpoints[method]` is nil (method key not in map), this would be a nil pointer dereference panic. Analysis of `findRoute` suggests it only returns non-nil when `endpoints[method]` has a handler, so this should be safe -- but if `findRoute` is ever modified to return nodes for other reasons (e.g., methodNotAllowed), this would panic. Is the implicit contract that `findRoute` guarantees `endpoints[method] != nil` on non-nil return intentional and relied upon?

## Summary

| Severity | Count |
|----------|-------|
| High     | 1     |
| Medium   | 2     |
| Low      | 3     |

**Total findings:** 6 (2 BUG, 1 BUG/Medium, 3 QUESTION)

- **BUG (High):** RegisterMethod bit collision with mTRACE on first custom method
- **BUG (Medium):** Spurious param value append and recursion on failed param match
- **BUG (Low):** Off-by-one in overflow check

**Overall assessment:** FIX FIRST - The RegisterMethod bit collision (Finding 1) is a correctness bug that silently corrupts method routing for any project using custom HTTP methods alongside TRACE. The spurious append in findRoute (Finding 3) introduces unnecessary recursion and potential backtracking errors in complex route trees.
