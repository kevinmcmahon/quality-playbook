# NSQ-34 Code Review: internal/clusterinfo/types.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `/tmp/qpb_wt_opus_NSQ-34/internal/clusterinfo/types.go`

---

### internal/clusterinfo/types.go

- **Line 62:** BUG (High). `r.Tombstoned[i]` is accessed using the index from iterating `r.Topics`, but there is no check that `len(r.Tombstoned) == len(r.Topics)`. If the JSON input has fewer `"tombstones"` entries than `"topics"` entries (or `"tombstones"` is absent/empty while `"topics"` is populated), this will panic with an index-out-of-range error. A nil or short `Tombstoned` slice causes an unrecoverable crash during unmarshalling of producer data from nsqlookupd.

- **Lines 118-128:** BUG (High). In `TopicStats.Add()`, the `found` variable is declared on line 118 (`found := false`) outside the outer loop but is never reset to `false` at the start of each iteration of the outer `for _, aChannelStats := range a.Channels` loop. Once any channel from `a.Channels` matches an existing channel in `t.Channels`, `found` stays `true` permanently. All subsequent channels from `a` that do NOT have a matching name in `t.Channels` will be silently dropped instead of being appended. This causes missing channel statistics when aggregating topic stats across multiple nsqd nodes.

  Expected: `found` should be reset to `false` at the start of each outer loop iteration (i.e., move the declaration inside the loop or add `found = false` as the first statement in the outer loop body).

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (High) | 2 |
| QUESTION | 0 |

**Overall assessment:** FIX FIRST

Both bugs affect correctness of data aggregation and unmarshalling in the cluster info path. The `found` flag bug (lines 118-128) silently drops channel statistics during multi-node aggregation, producing incorrect data in nsqadmin. The index-out-of-range bug (line 62) can crash any component that unmarshals producer data when the topics/tombstones arrays are mismatched.
