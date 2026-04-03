# Code Review: NSQ-10 — internal/clusterinfo/data.go

**File reviewed:** `/tmp/qpb_wt_opus_NSQ-10/internal/clusterinfo/data.go`
**Reviewer:** Claude Opus
**Date:** 2026-04-01

---

### internal/clusterinfo/data.go

- **Line 68:** BUG (High Severity) — Struct tag uses single quotes instead of double quotes: `` `json:'version'` `` should be `` `json:"version"` ``. Go's `encoding/json` package only recognizes struct tags with double-quoted values (`key:"value"`). Single quotes are silently ignored, so `resp.Version` will **never** be populated from the JSON response. This causes `GetVersion()` to always see an empty string, set it to `"unknown"`, and then `semver.Parse("unknown")` returns an error. **Impact:** `versionPivotNSQLookupd()` (line 853) calls `GetVersion()` and ignores the error; the returned zero-value `semver.Version{}` fails the `nodeVer.NE(semver.Version{})` check at line 856, so all nsqlookupd requests **always** use the deprecated URI instead of the v1 URI, even when the nsqlookupd supports v1 endpoints.

- **Line 278:** QUESTION (Low Severity) — `GetLookupdTopicProducers()` appends producers from all lookupd instances without deduplication: `producers = append(producers, resp.Producers...)`. If the same nsqd is registered with multiple lookupd instances, it will appear multiple times in the result. By contrast, `GetLookupdProducers()` (lines 211-225) deduplicates by `producer.TCPAddress()`. This inconsistency may cause duplicate operations when callers like `versionPivotProducers()` iterate over the returned producers (e.g., `CreateTopicChannel` at line 681 would send duplicate create-channel requests).

- **Lines 116, 165, 230, 283, 331, 418, 509, 591:** QUESTION (Low Severity) — All "query all" functions check `len(errs) == len(addrs)` to determine total failure. If the input address list is empty (`len == 0`), this condition is `0 == 0 == true`, which returns `"failed to query any nsqlookupd/nsqd"` even though nothing was queried. Callers may guard against empty inputs upstream, but the error message is misleading if an empty list is ever passed.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (High) | 1 |
| QUESTION (Low) | 2 |

**Overall assessment:** FIX FIRST — The single-quote struct tag on line 68 is a clear bug that silently breaks version detection for all nsqlookupd version-pivot operations, causing them to always use deprecated endpoints.
