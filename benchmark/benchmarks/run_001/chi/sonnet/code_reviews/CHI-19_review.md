# Code Review: CHI-19 — tree.go

**Reviewer:** Claude Sonnet
**Date:** 2026-03-31
**File reviewed:** `tree.go`

---

## tree.go

### Finding 1

- **Line 492:** [BUG] `ntParam/ntRegexp` inner-loop fallthrough unconditionally appends `""` to `routeParams.Values` and then bypasses the `xn == nil` guard, making a second `findRoute` call with the untrimmed path. If that call returns non-nil, `routeParams.Values` retains a spurious `""` that causes a `Keys`/`Values` length mismatch.
  - **Severity:** Medium
  - **Expected:** After the inner `for _, xn = range nds` loop exhausts all param/regexp candidates without a match, the outer code should `continue` to the next child group — or the stray `""` must be cleaned up unconditionally. The cleanup at lines 534–537 (`rctx.routeParams.Values = rctx.routeParams.Values[:len-1]`) only executes when `xn.findRoute` returns `nil`. If it returns non-nil and the function returns at line 530, the `""` is never removed.
  - **Actual:** After the inner loop, `xn` holds the last node from `range nds` (non-nil, since `len(nds) > 0` is guaranteed by line 406–408). The `if xn == nil { continue }` guard at line 501 is not taken. Line 528 then calls `xn.findRoute(rctx, method, xsearch)` where `xsearch == search` — the **original, untrimmed** path that still contains the param-value prefix. If this outer call finds a node (possible if `xn`'s subtree happens to match the untrimmed path), the function returns at line 530 with `routeParams.Values` containing the extra `""` at some position, while `routeParams.Keys` contains only the expected keys from the matched endpoint. `FindRoute` (lines 386–387) then copies both slices into `URLParams`, producing a misaligned key-value array for the lifetime of the request.
  - **Why it matters:** Misaligned `URLParams.Keys`/`URLParams.Values` causes `URLParam(r, key)` to return the wrong value for every parameter on the matched route — a silent data-corruption bug that could expose one user's route parameters to another request.
  - **Note on likelihood:** In a well-formed chi tree, param-node children expect paths *after* the param segment is consumed. The outer call with the untrimmed path (which still contains the param-value prefix) is structurally unlikely to find a route in practice, because static children would need to match the first byte of the param value, not a delimiter. However, the code makes no structural guarantee of this, and the `""` placement before the cleanup makes the invariant fragile.

---

### Finding 2

- **Line 492 (structural):** [QUESTION] Why does the `ntParam/ntRegexp` `case` fall through to the shared outer code block (lines 501–538) rather than `continue`-ing to the next child group when the inner loop exhausts all candidates?
  - **Severity:** Low
  - **Description:** The outer block (lines 501–538) appears designed for `ntStatic` (where `xn` is set by `nds.findEdge`) and `ntCatchAll` (where `xn = nds[0]`, `xsearch = ""`). For `ntParam/ntRegexp`, if the inner loop finds a match it returns early (`return fin` at line 484); if it doesn't, `xn` is the last-iterated node (semantically meaningless as a routing result) and `xsearch = search`. The outer code then redundantly re-attempts `xn.findRoute` with the untrimmed path (line 528). It's unclear whether this fallthrough is intentional. A `continue` after line 490 (end of inner loop without a match) would skip the outer block for this case and eliminate Finding 1. As written, the intent must be inferred from the cleanup behavior rather than from the code structure.

---

### Verified — No Bug

The following items from the protocol's focus list were read and verified:

- **`patParamKeys` duplicate check (lines 762–765):** The loop `for i := 0; i < len(paramKeys); i++` iterates the **full** accumulated `paramKeys` slice before appending `paramKey`. It is not limited to the most recently added key. Correct.

- **`addChild` regexp compilation (lines 255–261):** `regexp.Compile(segRexpat)` is called with `segRexpat` already anchored (`^`/`$`) by `patNextSegment` lines 735–742. A compile failure panics with a descriptive message. Propagation is correct for a registration-time panic.

- **`patNextSegment` panic at line 696 (`ws < ps`):** The condition `ps >= 0 && ws >= 0 && ws < ps` fires when `*` appears before `{`. `ws == ps` is structurally impossible (a byte cannot be both `'*'` and `'{'`).

- **`patNextSegment` panic at line 749–750 (`ws < len(pattern)-1`):** Fires correctly when `*` is not the final character.

- **Regexp anchor injection (lines 736–742):** `if rexpat[0] != '^'` and `if rexpat[len(rexpat)-1] != '$'` prevent double-anchoring. Correct.

- **Nested braces `/{id:{\\d+}}` (lines 707–718):** The `cc` counter correctly tracks open/close brace pairs; `pe` is set to the outer closing `}` position. Correct.

- **`FindRoute` Keys/Values alignment (lines 386–387):** Under normal operation (inner loop finds the route), `routeParams.Keys` is populated at the leaf via `h.paramKeys` (all keys for the full route pattern at once) and `routeParams.Values` accumulates one value per param node during traversal. The counts match because `patParamKeys` and the traversal both parse left-to-right through the same pattern.

- **Catch-all empty path (line 496):** When `search == ""`, `rctx.routeParams.Values = append(..., "")` captures an empty string, `xn = nds[0]`, `xsearch = ""`. The outer `len(xsearch) == 0` check at line 506 succeeds and the leaf handler is returned if present. This is intentional — a route like `/api/*` correctly matches `/api/` with a catch-all value of `""`.

- **Anonymous regexp param (`{:\\d+}`):** `strings.Cut(":\\d+", ":")` → `key = ""`, `rexpat = "\\d+"`, `isRegexp = true`. `patParamKeys` appends `""` as a key. `URLParam(r, "")` returns the matched value via the backward key search in `context.go:101`. This is documented behavior (chi.go line 41–42) and works as designed.

---

## Summary

| Severity | Count |
|----------|-------|
| BUG – Medium | 1 |
| QUESTION – Low | 1 |
| No findings | All other focus areas |

### Files with no findings
- All other focus areas within `tree.go` (patNextSegment, patParamKeys, addChild, FindRoute under normal paths, catch-all empty path, nested brace handling, regexp anchoring).

### Overall assessment: **NEEDS DISCUSSION**

Finding 1 (line 492) is a structural bug in `findRoute`'s `ntParam/ntRegexp` fallthrough that, while unlikely to trigger in a well-formed routing tree, creates a real Keys/Values misalignment risk if the outer `xn.findRoute` call at line 528 ever returns non-nil. The fix is straightforward (add a `continue` after line 490 or restructure the switch to avoid fallthrough for the param case), but the change touches the hottest path in the router and requires a deliberate decision about whether the outer fallthrough is intentional.
