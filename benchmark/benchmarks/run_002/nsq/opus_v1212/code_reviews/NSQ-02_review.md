# NSQ-02 Code Review: channel.go, stats.go, stats_test.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Files:** `nsqd/channel.go`, `nsqd/stats.go`, `nsqd/stats_test.go`

---

## nsqd/channel.go

### Finding 1
- **Line 341-361:** BUG (Medium) — **Topology-aware `put()` sends to potentially nil channels.** The `topologyAwareConsumption` flag (line 92) is set based on `HasExperiment(TopologyAwareConsumption)`, but `zoneLocalMsgChan` and `regionLocalMsgChan` are only initialized when `TopologyZone != ""` and `TopologyRegion != ""` respectively (lines 95-100). These are independent conditions. If the experiment is enabled but the topology strings are empty, `topologyAwareConsumption` is `true` while `zoneLocalMsgChan` and/or `regionLocalMsgChan` are nil. Sending to a nil channel in a select with a `default` clause silently falls through to `default`, so all three nested selects (lines 341-361) immediately fall through, and every message goes to the backend disk queue instead of the memory channel. This silently bypasses the in-memory fast path, causing a significant performance degradation — all messages take the disk I/O path even though `memoryMsgChan` was allocated and available.

### Finding 2
- **Line 217-221:** BUG (Low) — **`Empty()` drains from nil topology channels in select.** The select at lines 217-219 unconditionally includes `c.zoneLocalMsgChan` and `c.regionLocalMsgChan`. Receiving from a nil channel in a select with `default` is a no-op (the nil case is never ready), so the `default` fires immediately, meaning `memoryMsgChan` is never drained either. If topology channels are nil but `memoryMsgChan` has messages, `Empty()` will not drain the memory queue — it exits on the first iteration via `default`. In practice this is mitigated because `Empty()` is typically called before the channel has messages in the non-topology path, but the code is incorrect in the general case.

### Finding 3
- **Line 239-256:** BUG (Low) — **`flush()` has the same nil-channel drain issue as `Empty()`.** The select at lines 239-253 includes `zoneLocalMsgChan` and `regionLocalMsgChan` unconditionally. When these are nil (topology not configured), the cases are never ready. However, unlike `Empty()`, `flush()` can still work correctly if `memoryMsgChan` is the only non-nil channel: the Go runtime will select among ready cases, and nil cases are simply ignored. So this only fails when ALL channels are nil (which can't happen since `memoryMsgChan` is initialized when `MemQueueSize > 0` or ephemeral). Reclassifying: the nil topology channel cases are harmless dead code in the select, and Go correctly skips them. **Not a bug in practice** — select in Go ignores nil channel cases. Retracted.

### Finding 4
- **Line 634-636:** BUG (High) — **`processDeferredQueue` stops processing all remaining items on race condition.** When `PeekAndShift` (line 624, under `deferredMutex`) returns an item, the lock is released, then `popDeferredMessage` (line 633) re-acquires `deferredMutex`. Between these two operations, a concurrent `FinishMessage` or `RequeueMessage` could remove the message from `deferredMessages`. When `popDeferredMessage` returns an error ("ID not deferred"), the `goto exit` at line 635 **abandons all remaining timed-out deferred messages** in the priority queue. These messages remain in the PQ but not in the map, and since they're past their deadline, `PeekAndShift` will return them again on the next scan cycle. However, repeated races could cause persistent delays in deferred message delivery.

### Finding 5
- **Line 663-665:** BUG (High) — **`processInFlightQueue` stops processing all remaining items on race condition.** Same pattern as Finding 4. `PeekAndShift` (line 655) returns a timed-out message under `inFlightMutex`, lock is released, then `popInFlightMessage` (line 663) re-acquires lock. A concurrent `FinishMessage` or `TouchMessage` could remove the message between these operations. The `goto exit` at line 665 abandons all remaining timed-out in-flight messages. This means timed-out messages that should be requeued to clients are delayed until the next queue scan cycle (default interval configured by `QueueScanInterval`). Under high concurrency with many concurrent FIN/TOUCH operations, this could repeatedly truncate timeout processing.

### Finding 6
- **Line 463-479:** QUESTION (Medium) — **`AddClient` TOCTOU race on `MaxChannelConsumers` check.** The method reads `numClients` under `RLock` (line 465), releases the lock, checks `MaxChannelConsumers` (line 472), then acquires write `Lock` to add (line 477). Multiple concurrent goroutines (different clients) could all read `numClients = N`, pass the limit check, and all add themselves, exceeding the configured maximum. Each client's SUB command runs from a separate IOLoop goroutine, so this race is possible when multiple clients subscribe simultaneously. The over-admission is bounded by the number of concurrent racing SUB commands.

### Finding 7
- **Line 96-100:** QUESTION (Low) — **Unbuffered topology channels may cause put() contention.** `zoneLocalMsgChan` and `regionLocalMsgChan` are created with `make(chan *Message)` (zero buffer, unbuffered), while `memoryMsgChan` is created with `make(chan *Message, MemQueueSize)` (buffered). The topology-aware `put()` relies on the `default` clause to fall through when channels aren't ready, but unbuffered channels are only ready when a receiver is actively waiting. If the messagePump goroutine is momentarily busy (e.g., writing to a client), all three topology selects fall through to the backend disk write even though the channel has capacity. This is noted in the code comment (lines 337-339) as intentional ("messagePump is intermittently unavailable"), but it means the topology-aware path writes to disk much more frequently than the non-topology path, which has a buffered `memoryMsgChan`.

### Finding 8
- **Line 674:** QUESTION (Medium) — **`processInFlightQueue` calls `c.put(msg)` for timed-out messages without holding `exitMutex`.** The `exitMutex.RLock` is held at line 645, so the channel can't exit during processing. However, `c.put(msg)` (line 674) can itself call `writeMessageToBackend` which calls `c.backend` methods. If the channel is in the process of being deleted (a concurrent `exit(true)` waiting on `exitMutex.Lock`), the requeued message goes back into the memory channel or backend normally. This is safe because `exitMutex.RLock` prevents concurrent exit. No bug, retracted.

---

## nsqd/stats.go

### Finding 9
- **Line 89:** QUESTION (Low) — **`NewChannelStats` calls `c.e2eProcessingLatencyStream.Result()` on potentially nil receiver.** When `E2EProcessingLatencyPercentiles` is empty, `e2eProcessingLatencyStream` is nil (channel.go line 106-111). However, the `quantile.Quantile.Result()` method (quantile.go line 50-52) has an explicit nil receiver check that returns an empty `Result{}`. This is safe — no panic occurs. Not a bug.

### Finding 10
- **Line 66-71:** QUESTION (Low) — **`NewChannelStats` acquires `inFlightMutex` and `deferredMutex` separately, creating a non-atomic snapshot.** The in-flight count is read under `inFlightMutex` (lines 66-68), then deferred count under `deferredMutex` (lines 69-71). Between these two locks, the counts could change, producing an inconsistent snapshot where in-flight + deferred don't correspond to the same point in time. For stats reporting this is acceptable (eventual consistency), but if any consumer relies on in-flight + deferred summing correctly with depth, the numbers may be transiently inconsistent.

### Finding 11
- **Line 160:** BUG (Medium) — **`GetStats` passes topic filter string to `client.Stats()` instead of actual topic name.** The `topic` variable is the filter parameter passed to `GetStats`. When the filter is empty (`""`, meaning "all topics"), `client.Stats("")` is called for every client under every topic. Inside `clientV2.Stats()` (client_v2.go lines 316-326), when `topicName` is empty, `len(topicName) > 0` is false, so the `continue` is skipped, the first pub count entry is appended, then `break` exits the loop. This means only **one** arbitrary pub count entry is returned per client when requesting all-topic stats, rather than all pub counts. When a specific topic is filtered, it works correctly. The impact is that `/stats?format=json` (no topic filter) returns incomplete `pub_counts` for producer clients.

### Finding 12
- **Line 176:** BUG (Medium) — **Same topic-filter-as-name issue for producer stats.** `c.Stats(topic)` at line 176 passes the topic filter string (potentially `""`) when collecting producer stats. Same `break`-after-first-entry behavior in `clientV2.Stats()` causes only one pub count to be returned per producer when requesting all-topic stats.

### Finding 13
- **Line 203-208:** QUESTION (Low) — **`getMemStats` GC pause percentile calculation uses `ms.NumGC` which wraps around.** `runtime.MemStats.NumGC` is a `uint32` that wraps. When `NumGC` exceeds the `PauseNs` ring buffer size (256), `int(ms.NumGC)` could be very large but `PauseNs` only has 256 entries. The code at line 204 correctly caps `length` to `len(ms.PauseNs)` (256) via `if int(ms.NumGC) < length`, so this is safe until `NumGC` wraps past `math.MaxInt32` (2^31 on 32-bit) — at which point `int(ms.NumGC)` could become negative, and `length` would be set to a negative value, causing `gcPauses := make(Uint64Slice, length)` to panic. In practice, this requires ~2 billion GC cycles and is unlikely, but the cast from `uint32` to `int` is technically unsafe on 32-bit platforms.

---

## nsqd/stats_test.go

### Finding 14
- **Line 137-143:** QUESTION (Low) — **`TestStatsChannelLocking` creates messages and starts in-flight timeouts concurrently with stats collection, but never finishes or cleans up messages.** The test verifies that 25 messages are in-flight at the end (line 159), but the messages are never FIN'd or timed out, so they remain in the in-flight queue permanently. This is acceptable for a test (cleanup happens via `nsqd.Exit()`), but the test doesn't verify that concurrent stats collection didn't corrupt in-flight state — it only checks the final count. A more thorough test would also verify message IDs are intact.

### Finding 15
- **Line 160:** QUESTION (Low) — **`client.Stats(topic)` in test uses topic filter string.** At line 41, `nsqd.GetStats(topicName, "ch", true)` passes `topicName` as the filter, and at line 160, `client.Stats(topic)` in the inner loop of `GetStats` receives this filter. In the test this works correctly because a specific topic is being queried. The test does not cover the case where `GetStats("", "", true)` is called and producer pub counts are examined, so the bug from Finding 11 is not caught by existing tests.

---

## Summary

| Severity | Count | Type |
|----------|-------|------|
| Critical | 0 | — |
| High     | 2 | BUG |
| Medium   | 4 | 2 BUG, 2 QUESTION |
| Low      | 5 | 1 BUG (retracted), 4 QUESTION |

### Key Findings

1. **High — processInFlightQueue/processDeferredQueue early exit on race** (Findings 4, 5): Both queue processors `goto exit` when a concurrent operation removes a message between `PeekAndShift` and the pop, abandoning remaining timed-out items until next scan cycle.

2. **Medium — Topology-aware put() with nil channels** (Finding 1): When the experiment flag is enabled without configuring topology strings, all messages bypass the memory queue and go to disk.

3. **Medium — GetStats passes filter string as topic name** (Findings 11, 12): Producer `pub_counts` are truncated to one entry when stats are requested without a topic filter.

### Files with no critical findings
All three files have findings, but none are critical severity.

### Overall Assessment: **NEEDS DISCUSSION**

The high-severity queue processing race (Findings 4, 5) can cause delayed message redelivery under concurrent load. The topology nil-channel issue (Finding 1) is a configuration footgun. The stats pub_counts bug (Findings 11, 12) affects observability. None are data-loss critical, but the queue processing behavior warrants discussion on whether `goto exit` should be `continue` instead.
