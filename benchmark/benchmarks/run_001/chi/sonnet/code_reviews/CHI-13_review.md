# Code Review: CHI-13 — tree.go

## tree.go

### BUG — RegisterMethod: first custom method collides with mTRACE

- **Line 61:** [BUG] `mt := methodTyp(math.Exp2(float64(n)))` where `n = len(methodMap)`.

  **Root cause:** The pre-defined method constants use `1 << iota` starting at iota=0:

  | constant  | iota | value |
  |-----------|------|-------|
  | mSTUB     | 0    | 1     |
  | mCONNECT  | 1    | 2     |
  | mDELETE   | 2    | 4     |
  | mGET      | 3    | 8     |
  | mHEAD     | 4    | 16    |
  | mOPTIONS  | 5    | 32    |
  | mPATCH    | 6    | 64    |
  | mPOST     | 7    | 128   |
  | mPUT      | 8    | 256   |
  | mTRACE    | 9    | 512   |

  `methodMap` is initialized with 9 entries (CONNECT through TRACE; mSTUB is intentionally absent). So `n = 9` on the first `RegisterMethod` call, and `mt = math.Exp2(9) = 512 = mTRACE`.

  **Expected:** The first custom method receives a unique bit value (1024 = 2^10) that does not overlap any built-in constant.

  **Actual:** The first custom method receives 512, which is identical to `mTRACE`. Routing with the custom method is indistinguishable from routing with TRACE at the `endpoints` map level: `endpoints[customMethod]` and `endpoints[mTRACE]` are the same map entry. If both TRACE and the custom method are registered on the same pattern, one handler silently overwrites the other. If only the custom method is registered, a TRACE request will route to it—and vice versa.

  **Severity:** High. The collision is silent (no panic, no log), and it affects every project that calls `RegisterMethod`. mALL is widened correctly (`mALL |= mt`) but `mt` itself is wrong.

  **Secondary — Line 58:** `if n > strconv.IntSize` should be `if n >= strconv.IntSize`. When `n == strconv.IntSize` (64 on 64-bit), `math.Exp2(64)` produces a float64 that overflows `int64` when cast, yielding implementation-defined behaviour without a panic. The guard fires one step too late.

  **Severity (secondary):** Low. Requires more than 64 distinct HTTP methods, which is unrealistic in practice.

---

### QUESTION — findRoute: spurious empty-string value append after ntParam/ntRegexp inner loop exhaustion

- **Line 475:** `rctx.routeParams.Values = append(rctx.routeParams.Values, "")`

  After the inner `for idx` loop exits without finding a match, `""` is unconditionally appended to `routeParams.Values`. Control then falls through to the outer generic block (lines 484–514), which re-attempts `xn.findRoute(rctx, method, xsearch)` using the last-tried param node and the original, untrimmed `search` string.

  If that outer recursion returns a non-nil node (fin != nil, line 505–507), the function returns `fin` while `routeParams.Values` still contains the `""` appended at line 475. The cleanup at lines 510–513 only runs when the recursion *fails*. Were the outer recursion ever to succeed, `routeParams.Values` would have one extra element with no corresponding key, misaligning the `Keys`/`Values` slices that `FindRoute` (lines 374–375) copies into `rctx.URLParams`.

  **Expected:** If intentional, a comment explaining the invariant that the outer recursion cannot succeed here would clarify correctness. If unintentional, the `""` should either be removed or guarded by checking that the outer recursion succeeds before finalising the value.

  **Actual:** In all reachable cases identified during review, the outer recursion does fail (because the inner loop already tried each node with more-favourable trimmed paths), so the cleanup at line 512 fires and the slice is restored. The bug is latent rather than triggered by current routing patterns.

  **Severity:** Medium (latent). No currently reachable path through normal routing produces the misalignment, but the invariant is not enforced by the code structure.

---

### QUESTION — patNextSegment: anonymous regexp parameter produces empty-string key

- **Lines 709–712:**

  ```go
  if idx := strings.Index(key, ":"); idx >= 0 {
      nt = ntRegexp
      rexpat = key[idx+1:]
      key = key[:idx]
  }
  ```

  For a pattern like `{:\d+}`, `key` is `":\d+"` before the cut, then `key = ""` after. `patParamKeys` appends `""` to the param key list. `URLParam(r, "")` would return the captured value. The duplicate-key check at line 742 would panic on a second anonymous regexp param in the same pattern.

  This is documented in chi.go as `{:\\d+}` (empty name before colon), implying intentional support. Flagging as QUESTION to confirm that the empty-string key is the designed mechanism for anonymous regexp capture groups and that `URLParam(r, "")` returning a value is expected behaviour.

---

### QUESTION — patParamKeys: duplicate-key check covers full accumulated list (confirmed correct)

- **Lines 742–745:** The loop iterates `i` from `0` to `len(paramKeys)-1`, checking `paramKeys[i] == paramKey` before appending. This checks the *entire* accumulated key list, not just the most-recently-added entry. Behaviour is correct per the protocol's concern.

---

### No findings

The following items from the review protocol were examined and found to be correct:

- `patNextSegment` panic when `*` precedes `{` (line 673): fires correctly on `ws < ps`.
- `patNextSegment` panic when `*` is not the last character (line 728): fires correctly on `ws < len(pattern)-1`.
- `patNextSegment` closing-brace detection (line 697): `pe == ps` correctly identifies a missing `}`.
- `addChild` regexp compilation (lines 243–248): error propagates as a panic at registration time. ✓
- Regexp anchor injection (lines 715–722): `^` and `$` are only prepended/appended if not already present; no double-anchoring. ✓
- `FindRoute` URLParams append order (lines 374–375): both Keys and Values are appended from `rctx.routeParams` after successful `findRoute`; they are built in parallel during traversal and should remain aligned on the success path. ✓
- `findRoute` catch-all with `search == ""` (lines 477–481): the empty string is stored as the catch-all value and the leaf is checked normally; this is the correct behaviour for a request that matches exactly up to the catch-all wildcard. ✓

---

## Summary

| Severity | Count | Findings |
|----------|-------|----------|
| BUG – High | 1 | RegisterMethod exponent off-by-one causes first custom method to collide with mTRACE (line 61) |
| BUG – Low | 1 | RegisterMethod overflow guard uses `>` instead of `>=` (line 58) |
| QUESTION – Medium | 1 | Spurious `""` append in ntParam/ntRegexp path; latent Keys/Values misalignment if outer recursion ever succeeds (line 475) |
| QUESTION – Low | 2 | Anonymous regexp param empty-string key (line 712); duplicate-key check confirmed correct (lines 742–745) |

**Overall assessment: FIX FIRST** — The `RegisterMethod` bit-collision bug is a silent correctness failure affecting any chi application that registers custom HTTP methods. The first registered custom method silently shares a routing bit with TRACE.
