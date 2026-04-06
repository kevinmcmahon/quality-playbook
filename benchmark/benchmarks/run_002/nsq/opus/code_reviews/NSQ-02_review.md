# NSQ-02 Code Review: channel.go, stats.go, stats_test.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Files:** `nsqd/channel.go`, `nsqd/stats.go`, `nsqd/stats_test.go`

---

## nsqd/channel.go

- **Line 232:** [QUESTION] `flush()` reads `len(c.inFlightMessages)` and `len(c.deferredMessages)` without holding `inFlightMutex`/`deferredMutex`. This is only used in a log condition, and `flush()` is called from `exit()` which holds `exitMutex.Lock()` (preventing new operations via `processInFlightQueue`/`processDeferredQueue`). However, a `FinishMessage()` or `TouchMessage()` call already in progress (they do not acquire `exitMutex`) could still be mutating `inFlightMessages` concurrently, making this a technical data race. Low severity since it only affects logging accuracy, but it would be flagged by `-race`.

- **Line 462-479:** [BUG] **TOCTOU race in `AddClient()`.** The client existence check and `numClients` count are read under `RLock` (lines 463-466), but the actual insertion happens later under a separate `Lock` (lines 477-478). Between the two locks, another goroutine can concurrently add a different client, causing `maxChannelConsumers` to be exceeded. Two goroutines can both read `numClients == maxChannelConsumers - 1`, both pass the check at line 472, and both insert, resulting in `maxChannelConsumers + 1` clients. **Severity: Medium.** The fix is to perform the read-check-write under a single `Lock`.

- **Line 637:** [BUG] **`processDeferredQueue` ignores `c.put(msg)` error.** After a deferred message is popped from both the priority queue (line 624) and the deferred map (line 633), `c.put(msg)` is called at line 637 without checking the return value. If `put()` fails (e.g., backend write error), the message is silently lost — it has already been removed from deferred structures but never re-queued. **Severity: Medium.** The message is permanently lost on backend write failure.

- **Line 675:** [BUG] **`processInFlightQueue` ignores `c.put(msg)` error.** Same pattern as above. After a timed-out in-flight message is popped (line 663) and removed from the in-flight map (line 663), `c.put(msg)` at line 675 discards the error. If `put()` fails, the timed-out message is permanently lost. **Severity: Medium.**

- **Line 382-385:** [QUESTION] `PutMessageDeferred()` increments `messageCount` (line 383) and calls `StartDeferredTimeout()` (line 384), but does **not** hold `exitMutex.RLock()`. Compare with `PutMessage()` (lines 319-320) which does hold `exitMutex.RLock()`. This means a deferred message could be added to a closing channel after `exitFlag` is set. The message would be added to `deferredMessages` after `flush()` has already drained it, causing message loss. **Severity: Medium.**

- **Line 283:** [QUESTION] `Depth()` reads `len(c.memoryMsgChan)`, `len(c.zoneLocalMsgChan)`, `len(c.regionLocalMsgChan)`, and `c.backend.Depth()` in sequence without any lock. Each read is individually atomic for channel length, but the sum is not a consistent snapshot. This is likely acceptable for stats/monitoring purposes but the result could be transiently inconsistent. **Severity: Low.**

---

## nsqd/stats.go

- **Line 89:** [QUESTION] `NewChannelStats()` calls `c.e2eProcessingLatencyStream.Result()` without checking for nil. However, verified that `quantile.Quantile.Result()` has a nil receiver guard (returns `&Result{}`), so this is safe. **No issue — included for documentation.**

- **Line 159:** [QUESTION] `GetStats()` calls `client.Stats(topic)` at line 159 passing the topic filter parameter, but when `topic == ""` (all topics), the loop iterates all topics and for each topic's channels' clients, passes `topic` (empty string) to `client.Stats()`. This means the `topic` parameter passed to `Stats()` is the *filter* topic name, not the actual topic the channel belongs to. Whether this is correct depends on what `client.Stats()` does with the argument — if it uses it to filter stats, passing `""` would be correct (show all). If it uses it for labeling, it could be misleading. **Severity: Low.**

- **Lines 66-71:** [QUESTION] `NewChannelStats()` acquires `inFlightMutex` and `deferredMutex` separately (not atomically) to read counts. This means the inflight and deferred counts in a single `ChannelStats` value might not be from the same instant. Acceptable for stats display but worth noting. **Severity: Low.**

---

## nsqd/stats_test.go

- **Lines 136-142:** [QUESTION] `TestStatsChannelLocking` puts messages via `topic.PutMessage(msg)` and then calls `channel.StartInFlightTimeout(msg, 0, opts.MsgTimeout)` on the same `msg` object. The `topic.PutMessage` routes the message to the topic's message pump, which will eventually deliver it to the channel. Separately, `StartInFlightTimeout` directly adds it to the channel's in-flight structures. This means the same message could end up both in the channel's memory queue (via topic) and in the in-flight map, which is not how normal message flow works (normally `StartInFlightTimeout` is called by the protocol handler after delivering the message to a client). The test is specifically testing locking under concurrency, so this may be intentional for stress testing purposes, but it does not model realistic message flow. **Severity: Low — test-only concern.**

- **No correctness bugs found in test assertions.** The test at line 159 asserts `InFlightCount == 25`, which matches the 25 messages put in-flight by the goroutine. The locking test at lines 122-160 correctly exercises concurrent stats collection vs message operations.

---

## Summary

| Severity | Count |
|----------|-------|
| BUG (Medium) | 3 |
| QUESTION (Medium) | 1 |
| QUESTION (Low) | 4 |

### Bugs

1. **`AddClient()` TOCTOU race** (channel.go:462-479) — can exceed `maxChannelConsumers`
2. **`processDeferredQueue` drops messages on `put()` failure** (channel.go:637) — silent message loss
3. **`processInFlightQueue` drops messages on `put()` failure** (channel.go:675) — silent message loss

### Questions

1. **`PutMessageDeferred()` missing `exitMutex` guard** (channel.go:382-385) — potential message loss on close
2. **`flush()` unsynchronized map reads** (channel.go:232) — data race in logging
3. **`Depth()` non-atomic composite read** (channel.go:283) — inconsistent snapshot
4. **`NewChannelStats` non-atomic stats reads** (stats.go:66-71) — minor inconsistency

### Files with no findings
- `nsqd/stats_test.go` — no correctness bugs (one minor question about test realism)

### Overall Assessment: **NEEDS DISCUSSION**

The `AddClient()` TOCTOU race and the two silent message-loss paths in `processInFlightQueue`/`processDeferredQueue` are real correctness concerns. The `AddClient` race could be fixed by using a single write lock for the check-and-insert. The `put()` error handling in the queue processors should at minimum log the error and ideally retry or preserve the message. The missing `exitMutex` guard on `PutMessageDeferred` should also be evaluated against the shutdown sequence.
