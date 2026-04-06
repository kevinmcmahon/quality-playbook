# Code Review: CHI-09 — tree.go

**Reviewer:** Claude Sonnet
**File reviewed:** `tree.go`
**Date:** 2026-03-31

---

## tree.go

### Line 61: BUG — `RegisterMethod` assigns first custom method the same bit as `mTRACE`

**Severity:** High

**Description:**
`mSTUB` through `mTRACE` occupy bits 0–9 (10 constants, using `1 << iota`):

```
mSTUB    = 1 << 0 = 1
mCONNECT = 1 << 1 = 2
...
mTRACE   = 1 << 9 = 512
```

`methodMap` contains only the 9 standard HTTP methods (CONNECT through TRACE) — `mSTUB` is an internal sentinel and is **not** in `methodMap`. Therefore `len(methodMap) == 9` at initialization.

`RegisterMethod` computes the new bit as:

```go
n := len(methodMap)          // = 9 on first call
mt := methodTyp(math.Exp2(float64(n)))  // = 2^9 = 512 = mTRACE
```

The first custom HTTP method registered receives bit value `512`, which is **identical to `mTRACE`**. Both the custom method and TRACE will share the same key in the `endpoints` map. Registering a handler for the custom method on any route will overwrite the TRACE handler for that route, and vice versa. The `_examples/custom-method/main.go` demonstrates this: `RegisterMethod("LINK")` is the first call and collides with TRACE.

**Expected:** First custom method should receive bit `1024` (`1 << 10`), the first unused bit.
**Actual:** First custom method receives `512` (`1 << 9 = mTRACE`), colliding with TRACE.
**Why it matters:** Any application using `RegisterMethod` will silently corrupt TRACE routing or the first custom method's routing. Handlers will be overwritten; requests may be routed to the wrong handler with no error or log.

---

### Line 58: BUG — Overflow guard uses `>` instead of `>=`

**Severity:** Low

**Description:**
The guard is:

```go
if n > strconv.IntSize {
    panic(...)
}
mt := methodTyp(math.Exp2(float64(n)))
```

`strconv.IntSize` is 64 on 64-bit platforms. When `n == 64` (allowed through by `>`), `math.Exp2(64.0) = 1.8446744e+19`, which exceeds `MaxInt64`. Converting this float64 to `int` in Go when the value is out of range produces implementation-defined behavior (per the Go spec). The correct guard is `n >= strconv.IntSize`.

**Expected:** Panic when `n >= strconv.IntSize`.
**Actual:** Allows `n == strconv.IntSize`, producing integer overflow.
**Why it matters:** Pathological (55+ custom methods) but results in a silently wrong `methodTyp` value that maps to an already-used bit or zero.

---

### Line 473: QUESTION — Unconditional empty-value append after exhausting param/regexp inner loop

**Severity:** Low (potential confusion; may mask a latent keys/values mismatch)

**Description:**
After the inner `for idx` loop over `ntParam`/`ntRegexp` nodes exhausts all alternatives, control falls through to:

```go
rctx.routeParams.Values = append(rctx.routeParams.Values, "")
```

This appends an empty string to `routeParams.Values`. The code then falls through to:

```go
fin := xn.findRoute(rctx, method, xsearch)  // line 502
```

where `xn` is the last param node in `nds` and `xsearch == search` (reset in the inner loop). If `findRoute` succeeds here, `routeParams.Values` would contain the extra `""` while `routeParams.Keys` (appended at the leaf via `h.paramKeys`) would not have a corresponding empty key — causing `URLParams.Keys` and `URLParams.Values` to be mismatched in `FindRoute` (lines 374–375).

If `findRoute` fails (which should always be the case, since the inner loop already tried the same last node), the cleanup at lines 508–511 removes the `""`:

```go
if xn.typ > ntStatic {
    if len(rctx.routeParams.Values) > 0 {
        rctx.routeParams.Values = rctx.routeParams.Values[:len(rctx.routeParams.Values)-1]
    }
}
```

**Question:** Under what conditions can `fin != nil` at line 502, having already failed for every node in the inner loop? If this is dead code, it should be removed. If it is reachable, the extra `""` in `routeParams.Values` would produce a keys/values length mismatch that propagates into `URLParams` and corrupts `URLParam` lookups for all subsequent parameters.

---

### Line 695: QUESTION — Unclosed brace panic triggers on `pe == ps` even for `pe` never advanced

**Severity:** Low

**Description:**
The brace-tracking loop at lines 684–693 initializes `pe = ps` and updates `pe` only when `cc` reaches 0. The panic fires when `pe == ps` at line 695:

```go
if pe == ps {
    panic("chi: route param closing delimiter '}' is missing")
}
```

However, `pe` is also used as the loop counter variable's relative offset via `pe = ps + i`. If the pattern has `{` at the very last character (e.g., `/{`), the loop runs once (i=0, c='{', cc=1), never finds `}`, and exits with `pe == ps`. The panic correctly fires.

But if the pattern is `{{}` (open-open-close), the loop runs: i=0 cc=1, i=1 cc=2, i=2 cc=1. No `cc==0`, loop ends, `pe == ps`. Panic fires — correct.

**Confirmed:** The panic at line 695 fires correctly for all unclosed-brace patterns. No bug. Flagged for protocol completeness only.

---

## Summary

| Severity | Count | Finding |
|----------|-------|---------|
| BUG — High | 1 | Line 61: `RegisterMethod` first custom method collides with `mTRACE` |
| BUG — Low | 1 | Line 58: Overflow guard `>` should be `>=` |
| QUESTION — Low | 1 | Line 473: Unconditional `""` append after inner param loop; potential keys/values mismatch if the subsequent `findRoute` call ever succeeds |
| QUESTION — Low | 1 | Line 695: Panic guard confirmed correct (noted for completeness) |

**Files with no findings:** None (all findings are in `tree.go`)

**Overall assessment: FIX FIRST**

The `RegisterMethod` bit collision (line 61) is a silent correctness bug that affects every application using custom HTTP methods. The first registered custom method will shadow TRACE in the routing table with no diagnostic output.
