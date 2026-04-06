# NSQ-37 Code Review: internal/clusterinfo/types.go & producer_test.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Files:** `internal/clusterinfo/types.go`, `internal/clusterinfo/producer_test.go`

---

### internal/clusterinfo/types.go

- **Line 68:** BUG — **Severity: High** — `Producer.UnmarshalJSON` indexes `r.Tombstoned[i]` using the index from iterating `r.Topics` without checking that the two slices have the same length. If the JSON `"topics"` array has more entries than `"tombstones"`, this will panic with an index-out-of-range error. The JSON field `"tombstones"` could be missing entirely (resulting in a nil/empty slice) or have fewer elements than `"topics"`. A bounds check or length equality check is needed before the loop.

- **Lines 302–303:** BUG — **Severity: Medium** — `ClientStatsByNodeTopology.Less` violates the strict weak ordering contract required by `sort.Sort`. When two clients share the same `Node` and both have `TopologyRegion` and `TopologyZone` matching the node's region/zone, `Less(i, j)` returns `true` (line 302) AND `Less(j, i)` also returns `true` (same path). This violates antisymmetry (`Less(a,b) && Less(b,a)` must never both be true). In Go 1.19+, this can cause `sort.Sort` to panic or produce non-deterministic results. The fix is to check whether *both* match zone+region first and return `false` (equal), or to use a tiebreaker. This sort is actively called in `nsqadmin/http.go:332`.

### internal/clusterinfo/producer_test.go

No findings. The tests correctly verify hostname, IPv4, and IPv6 address formatting using `net.JoinHostPort` behavior.

---

### Summary

| Severity | Count |
|----------|-------|
| High     | 1     |
| Medium   | 1     |
| **Total**| **2** |

- **Files with no findings:** `internal/clusterinfo/producer_test.go`
- **Overall assessment:** **FIX FIRST** — The index-out-of-range panic in `UnmarshalJSON` (line 68) is a crash bug triggered by malformed JSON from nsqlookupd. The sort contract violation (lines 302–303) can cause panics in Go 1.19+ when multiple clients in the same topology zone are sorted.
