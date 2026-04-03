# NSQ-33 Code Review: nsqadmin/http.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `/tmp/qpb_wt_opus_NSQ-33/nsqadmin/http.go`

---

### nsqadmin/http.go

- **Line 133-134:** [BUG] `indexHandler` ignores errors from both `staticAsset("index.html")` and `template.New(...).Parse(string(asset))`. If either fails, `t` could be nil, and `t.Execute(w, ...)` on line 141 will panic with a nil pointer dereference, crashing the HTTP handler. **Severity: Medium.** Expected: errors checked and a proper HTTP error returned. Actual: errors silently discarded via `_`, leading to potential nil pointer panic.

- **Line 408-441:** [BUG] `tombstoneNodeForTopicHandler` is missing an `isAuthorizedAdminRequest` check. All other mutating handlers (`createTopicChannelHandler` line 452, `deleteTopicHandler` line 494, `deleteChannelHandler` line 523, `topicChannelAction` line 568) enforce authorization. Tombstoning a node for a topic is a destructive administrative action that any unauthenticated user can trigger. **Severity: High.** Expected: authorization check before performing the tombstone. Actual: no authorization check, allowing unauthorized users to tombstone producers.

- **Line 730:** [BUG] `graphiteHandler` dereferences `response[0].DataPoints[0][0]` without checking that `response` is non-empty, `DataPoints` is non-empty, or the inner pointer is non-nil. If the Graphite API returns an empty response, an empty `DataPoints` array, or a null data point, this will panic with an index-out-of-range or nil pointer dereference. **Severity: Medium.** Expected: bounds and nil checks before dereferencing. Actual: direct index access and pointer dereference with no validation.

- **Line 747:** [BUG] `doConfig` ignores the error return from `net.ParseCIDR(allowConfigFromCIDR)`. If the configured CIDR string is malformed, `ipnet` will be nil, and `ipnet.Contains(ip)` on line 758 will panic with a nil pointer dereference. This crashes the handler for every config request when the CIDR is misconfigured. **Severity: Medium.** Expected: error checked, invalid CIDR logged and handled gracefully (e.g., deny all or return 500). Actual: error discarded, nil `ipnet` used on line 758 causing panic.

- **Line 334:** [QUESTION] In `channelHandler`, `channelStats[channelName]` performs a map lookup that may return nil if the channel is not found in the stats. The response struct embeds `*clusterinfo.ChannelStats` which would be nil, causing JSON serialization to output null for all embedded fields. Is this the intended behavior, or should a 404 be returned when the channel has no stats?

---

### Summary

| Severity | Count |
|----------|-------|
| High     | 1     |
| Medium   | 3     |
| QUESTION | 1     |

- **Total findings:** 5 (4 BUG, 1 QUESTION)
- **Files with no findings:** N/A (single file review)
- **Overall assessment:** **FIX FIRST** — The missing authorization check on `tombstoneNodeForTopicHandler` is a security issue that should be addressed before shipping. The three potential panic scenarios (template parse failure, graphite response dereference, CIDR parse failure) can crash request handlers in production.
