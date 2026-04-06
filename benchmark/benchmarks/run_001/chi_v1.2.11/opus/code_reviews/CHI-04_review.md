# Code Review: CHI-04 — context.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-03-31
**File:** `/tmp/qpb_v1211_opus_CHI-04/context.go`

---

## Findings

### context.go

- **Line 83-96:** [BUG] **Severity: High** — `Reset()` does not clear `methodsAllowed` (declared at line 79). The `methodsAllowed` field is a `[]methodTyp` slice that gets appended to during route matching in `tree.go:473` and `tree.go:519`. When a `Context` is returned to the `sync.Pool` (at `mux.go:91`) and later reused (at `mux.go:81`), stale `methodsAllowed` entries from a previous request survive into the next request. This means a subsequent request that triggers a 405 response could include incorrect methods in the `Allow` header (methods from a completely different route on a prior request). The fix is to add `x.methodsAllowed = x.methodsAllowed[:0]` to `Reset()`, consistent with how `RoutePatterns`, `URLParams.Keys`, `URLParams.Values`, `routeParams.Keys`, and `routeParams.Values` are all reset via `[:0]`.

- **Line 133-138:** [QUESTION] **Severity: Low** — `replaceWildcards()` uses recursion with `strings.Replace(p, "/*/", "/", -1)`. While `-1` replaces all occurrences in a single pass, the recursion is needed because replacements can create new `"/*/"`  patterns (e.g., `"/*/*/"` -> `"//"` won't happen, but `"/*//*/"` could chain). In practice, route patterns are short and bounded by path depth, so stack overflow is not a realistic concern. However, this could be simplified to a loop. Flagging as a question: is the recursion intentional for readability, or an oversight?

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High     | 1 |
| Medium   | 0 |
| Low      | 1 |

**High-severity finding:** `methodsAllowed` not reset in `Reset()` — causes cross-request data leakage of allowed HTTP methods via sync.Pool reuse, leading to incorrect `Allow` headers on 405 responses.

**Overall assessment:** FIX FIRST — The missing `methodsAllowed` reset is a correctness bug that can produce incorrect 405 responses under concurrent load. It follows the exact pattern of all other slice fields being reset via `[:0]` but was missed for this one field.
