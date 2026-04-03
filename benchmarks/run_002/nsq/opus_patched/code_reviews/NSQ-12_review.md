# NSQ Code Review — NSQ-12
**Date:** 2026-04-01
**Reviewer:** Claude Opus 4.6
**Scope:** `nsqd/channel.go`, `nsqd/topic.go`
**Focus Areas:** 9 (Config Parameter Validation), 10 (Input Validation Failure Modes), 11 (Exit Path Resource Completeness), 12 (Go Channel Lifecycle in Select Statements)

---

## nsqd/channel.go

### Finding 1
- **Line 637:** BUG — Severity: **High**
  `processDeferredQueue` calls `c.put(msg)` after successfully removing the message from `deferredMessages` (line 633) and `deferredPQ` (line 624), but the return value of `c.put(msg)` is silently discarded. If `put()` fails (e.g., backend write error when all memory channels are full), the message has been removed from the deferred structures but never re-enqueued. **The message is permanently lost.** Expected: error from `put()` should either be propagated, or the message should be re-added to the deferred queue on failure.

### Finding 2
- **Line 674:** BUG — Severity: **High**
  `processInFlightQueue` calls `c.put(msg)` after removing a timed-out message from `inFlightMessages` (line 663) and `inFlightPQ` (line 655), but the return value is silently discarded. Same pattern as Finding 1: if `put()` fails, the message is permanently lost — it has been removed from in-flight tracking but was never successfully re-queued. Expected: the error should be handled to prevent silent message loss on backend failures.

### Finding 3
- **Line 463–479:** BUG — Severity: **Medium**
  `AddClient` has a TOCTOU (time-of-check-time-of-use) race on the `MaxChannelConsumers` limit. The client count `numClients` is read under `RLock` (line 465), then the limit is checked (line 472), but the actual insertion happens under a separate `Lock` (line 477–479). Between `RUnlock` and `Lock`, other goroutines can add clients, allowing the consumer count to exceed `MaxChannelConsumers`. Expected: the existence check, count check, and insertion should all happen under a single `Lock`.

### Finding 4
- **Lines 95–100 vs 92:** QUESTION — Severity: **Medium**
  `topologyAwareConsumption` (line 92) is set from `HasExperiment()`, while `regionLocalMsgChan` (line 96–97) and `zoneLocalMsgChan` (line 98–99) are created based on `TopologyRegion`/`TopologyZone` config values. These are independent: if the experiment is enabled but neither config is set, both topology channels remain nil. In `put()` (line 340–361), the topology-aware branch sends to these nil channels via select-with-default, which harmlessly skips them — but ALL messages then contend on the single final select (lines 353–361) where `memoryMsgChan` competes with two nil channels. The topology-aware feature provides no benefit when the config values are empty. **Is there a missing validation that TopologyZone/TopologyRegion must be set when the experiment is enabled?**

### Finding 5
- **Lines 96, 98:** QUESTION — Severity: **Medium**
  `regionLocalMsgChan` and `zoneLocalMsgChan` are created as **unbuffered** channels (`make(chan *Message)`). In `flush()` (lines 239–243) and `Empty()` (lines 217–219), the code attempts to drain these channels with `select`/`default`. However, unbuffered channels never have buffered messages — they only transfer during a synchronous send/receive handoff. These drain loops will **never** receive any messages from these channels (the select immediately falls to `default`). If topology-aware consumption is active and a message is mid-handoff on `zoneLocalMsgChan` during `flush()`, the draining select might intercept it — but this is timing-dependent. Meanwhile, the `Depth()` function (line 283) reports `len(c.zoneLocalMsgChan)` and `len(c.regionLocalMsgChan)`, which are **always 0** for unbuffered channels, making depth undercount messages that are conceptually "in" the topology pipeline.

### Finding 6
- **Line 279:** BUG — Severity: **Low**
  `flush()` always returns `nil` even when `writeMessageToBackend` fails (errors are logged at lines 242, 247, 252, 264, 273 but never accumulated or returned). The caller `exit()` at line 202 ignores the return value anyway (`c.flush()` followed by `return c.backend.Close()`), so a flush that partially fails reports success to the caller of `Close()`. Expected: `flush()` should return the first error (or an aggregate), and `exit()` should consider it.

### Finding 7
- **Lines 632–636:** QUESTION — Severity: **Low**
  In `processDeferredQueue`, if `popDeferredMessage` fails at line 634 (returns error), the function immediately jumps to `exit` (line 635). The item was already shifted out of `deferredPQ` at line 624, but `popDeferredMessage` removes it from `deferredMessages` map. If the pop fails (message not found in map), the item has been removed from the priority queue but remains absent from the map — an inconsistent state. This should only happen if another goroutine removed it concurrently, but it means the message is silently dropped.

---

## nsqd/topic.go

### Finding 8
- **Lines 377–381:** BUG — Severity: **Medium**
  In `exit(deleted=true)`, the code iterates `t.channelMap` and calls both `delete(t.channelMap, channel.name)` and `channel.Delete()` inside the loop. While Go allows map deletion during range iteration, `channel.Delete()` is a heavyweight operation (closes clients, empties queue, deletes backend) performed while holding `t.Lock()`. This blocks all other operations that need `t.RLock()` (e.g., `PutMessage` at line 181, `GetExistingChannel` at line 133) for the entire duration of all channel deletions. While not a deadlock (Notify spawns a goroutine), it causes extended lock contention during topic deletion. More critically, if any channel's `Delete()` panics, the topic lock is never released (no defer), causing a permanent deadlock.

### Finding 9
- **Line 439:** BUG — Severity: **Low**
  `flush()` always returns `nil`, same pattern as channel.go Finding 6. Backend write errors at line 429 are logged but not returned. The caller at line 401 ignores the return value. Partial flush failure is reported as success to the caller of `Close()`.

### Finding 10
- **Line 49:** QUESTION — Severity: **Low**
  `NewTopic` always creates `memoryMsgChan` with `make(chan *Message, nsqd.getOpts().MemQueueSize)`. When `MemQueueSize == 0`, this creates an **unbuffered** channel (capacity 0). Contrast with `NewChannel` (channel.go line 103) which explicitly sets `memoryMsgChan = nil` when `MemQueueSize == 0` (and not ephemeral). In `Topic.put()` (line 224), the check `cap(t.memoryMsgChan) > 0` correctly skips the unbuffered channel for normal messages. However, deferred messages (`m.deferred != 0`) still attempt to send on the unbuffered channel (line 226), which only succeeds if `messagePump` happens to be receiving at that exact moment. If it's not, the message falls to backend where it **loses its deferred timer** (as noted in the comment at line 223). This is a best-effort design, but the asymmetry with Channel's explicit nil approach is worth noting.

### Finding 11
- **Lines 390–398:** QUESTION — Severity: **Low**
  In `exit(deleted=false)`, channels are closed under `t.RLock()` (line 390). Each `channel.Close()` calls `channel.exit(false)` which acquires `c.exitMutex.Lock()`, closes clients, and calls `c.flush()`. While the operations don't reacquire `t.Lock()` (so no deadlock), closing all channels sequentially under a topic read-lock means `PutMessage` (which also needs `t.RLock()`) could still proceed and attempt `channel.PutMessage()` on a channel that is mid-close. The channel's own `exitMutex` protects against this, but the topic-level RLock provides a false sense of serialization.

---

## Summary

| Severity | BUG | QUESTION |
|----------|-----|----------|
| Critical | 0   | 0        |
| High     | 2   | 0        |
| Medium   | 1   | 2        |
| Low      | 2   | 3        |
| **Total**| **5**| **5**   |

### High-severity findings
1. **Silent message loss in `processDeferredQueue`** (channel.go:637) — `put()` error discarded after removing from deferred structures
2. **Silent message loss in `processInFlightQueue`** (channel.go:674) — `put()` error discarded after removing from in-flight structures

### Files with no findings
None — both files have findings.

### Overall Assessment: **FIX FIRST**
The two high-severity message loss bugs (Findings 1 and 2) are the primary concern. When the backend disk queue has an error, timed-out and deferred messages are silently dropped because `put()` errors are not handled. The TOCTOU race in `AddClient` (Finding 3) can allow exceeding the consumer limit under concurrent connections. These should be addressed before shipping.
