# NSQ-11 Code Review: internal/quantile/aggregate.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `internal/quantile/aggregate.go` (from `/tmp/qpb_wt_opus_NSQ-11`)

---

### internal/quantile/aggregate.go

- **Line 51:** **BUG** (Severity: High) — `Less()` sorts by key `"percentile"`, but every other location in the file (lines 28, 33, 62, 72) uses the key `"quantile"`. Since `"percentile"` is never set in any map, the lookup returns `0.0` for every element, making `sort.Sort(e)` on line 84 a no-op. The sorted order of percentiles in the aggregate is effectively random (insertion order). Should be `e.Percentiles[i]["quantile"] > e.Percentiles[j]["quantile"]`.

- **Line 74:** **BUG** (Severity: High) — The minimum tracking is completely broken. The line reads:
  ```go
  p[i]["min"] = math.Min(value["max"], p[i]["max"])
  ```
  Both arguments reference `"max"` fields. This should be:
  ```go
  p[i]["min"] = math.Min(value["min"], p[i]["min"])
  ```
  As written, `"min"` is set to the smaller of the two maximums, which is semantically wrong — it neither tracks the true minimum nor preserves any meaningful value.

---

### Summary

| Severity | Count |
|----------|-------|
| High     | 2     |

- **Files with no findings:** N/A (single file review)
- **Overall assessment:** **FIX FIRST** — Both bugs silently produce incorrect results. The `"percentile"` vs `"quantile"` key mismatch makes sorting dead code, and the min-tracking bug means aggregated minimum latency values are wrong.
