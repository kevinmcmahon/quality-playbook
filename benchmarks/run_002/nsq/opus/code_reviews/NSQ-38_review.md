# NSQ-38 Code Review: internal/quantile/aggregate.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `/tmp/qpb_wt_opus_NSQ-38/internal/quantile/aggregate.go`

---

### internal/quantile/aggregate.go

- **Line 97:** BUG — `min` calculation uses wrong map keys. The code reads:
  ```go
  p[i]["min"] = math.Min(value["max"], p[i]["max"])
  ```
  It should be:
  ```go
  p[i]["min"] = math.Min(value["min"], p[i]["min"])
  ```
  Both arguments reference `"max"` instead of `"min"`. This means the aggregated minimum value is actually the minimum of the two maximums, which is incorrect. The true minimum across merged aggregates is silently lost.

- **Line 74:** BUG — `Less()` references non-existent map key `"percentile"`. The sort interface method reads:
  ```go
  return e.Percentiles[i]["percentile"] > e.Percentiles[j]["percentile"]
  ```
  But no code in this file ever sets a `"percentile"` key. The actual key used everywhere else (lines 51, 56, 85, 94) is `"quantile"`. Accessing a missing key in a Go map returns `0`, so the comparison is always `0 > 0` → `false`, meaning `sort.Sort(e)` on line 104 is effectively a no-op. Percentiles are never actually sorted after merging via `Add()`.

- **Line 101:** QUESTION — Potential division by zero when `count` is 0. If the JSON `count` field is 0, then `value["count"]` is `0.0` (set at line 57 as `float64(count)`). After line 99, `p[i]["count"]` could remain 0 (if it was 0 before and `value["count"]` is 0), making line 101 a division by zero producing `NaN`. This would propagate `NaN` into the average. In practice `count == 0` likely means no data, but there is no guard against it.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG      | 2     |
| QUESTION | 1     |

- **Line 97:** BUG (High) — Wrong keys in `min` aggregation, silently produces incorrect minimum values.
- **Line 74:** BUG (High) — Sort uses non-existent key `"percentile"` instead of `"quantile"`, sort is a no-op.
- **Line 101:** QUESTION (Low) — Division by zero when count is 0.

**Overall assessment:** FIX FIRST — Both bugs silently produce incorrect results in the e2e processing latency aggregation. The `min` bug means aggregated minimum latency is wrong, and the sort bug means percentiles may be returned in arbitrary order after merging.
