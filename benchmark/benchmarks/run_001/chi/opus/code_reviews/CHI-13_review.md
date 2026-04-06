# Code Review: tree.go

Reviewed from: `/tmp/qpb_wt_chi_opus_CHI-13/tree.go`

---

### tree.go

- **Line 57-61:** [BUG] **Critical** — `RegisterMethod` assigns duplicate bit value for the first custom method. `methodMap` has 9 entries (the 9 standard HTTP methods), but bit positions 0–9 are already used (mSTUB=1<<0 through mTRACE=1<<9). `n := len(methodMap)` returns 9, so `math.Exp2(float64(9))` = 512 = 1<<9 = mTRACE. The first custom method registered collides with TRACE. Subsequent custom methods (n=10, 11, ...) get unique bits, but the first one silently shares TRACE's bit. This means registering a handler for a custom method also overwrites TRACE's handler (via `setEndpoint` at line 347 which iterates `methodMap`), and vice versa. **Expected:** The next available bit should account for mSTUB not being in `methodMap`, e.g., `mt := methodTyp(1 << (n + 1))` or tracking bit positions separately from map size.

- **Line 58:** [BUG] **Medium** — Off-by-one in overflow guard. The check `if n > strconv.IntSize` should be `n >= strconv.IntSize`. When `n == strconv.IntSize`, `math.Exp2(float64(n))` produces a value that requires bit position `n`, which overflows the `int`-backed `methodTyp`. This allows one extra custom method registration that silently produces an overflowed (zero or negative) bit flag.

- **Line 475:** [QUESTION] **Medium** — After the `ntParam`/`ntRegexp` for-loop (lines 421–473) exhausts all param nodes without finding a match, an empty string is unconditionally appended to `rctx.routeParams.Values`. No corresponding key is appended to `rctx.routeParams.Keys`. The cleanup at lines 510–513 removes this value only when the recursive call at line 504 returns nil. If the recursive call at line 504 were to succeed (returning non-nil), the function returns at line 506 with the stale empty-string value still in `routeParams.Values` and no matching key, causing Keys/Values misalignment. In practice this code path appears difficult to trigger since the same param nodes were already tried in the loop, but the invariant violation (Values growing without Keys) is a latent correctness risk. Is this append intentional, or should it be removed?

- **Line 61:** [QUESTION] **Low** — `RegisterMethod` uses `math.Exp2(float64(n))` (floating-point exponentiation) to compute bit flags instead of integer bit shift `1 << n`. On 64-bit systems, for n > 52, `float64` cannot exactly represent 2^n, which would produce an incorrect `methodTyp` value. The overflow guard at line 58 should prevent n from reaching this range, but only if the guard is corrected (see finding above). Using `methodTyp(1) << n` would be exact for all valid bit positions.

---

### Summary

| Severity | Count |
|----------|-------|
| Critical | 1     |
| Medium   | 2     |
| Low      | 1     |

- **Total findings:** 4 (2 BUG, 2 QUESTION)
- **Files with no findings:** N/A (single file reviewed)
- **Overall assessment:** **FIX FIRST** — The `RegisterMethod` bit collision (line 57–61) is a silent data-corruption bug: the first custom HTTP method shares its bit flag with TRACE, causing handler overwrites. The custom-method example in `_examples/custom-method/main.go` registers "LINK" as the first custom method, which would collide with TRACE in production use. This must be fixed before relying on custom method support.
