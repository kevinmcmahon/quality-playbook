# NSQ Code Review: NSQ-12

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Files:** `nsqd/channel.go`, `nsqd/topic.go`

---

## nsqd/channel.go

### Finding 1

- **Line 463-479:** BUG — `AddClient` TOCTOU race allows `MaxChannelConsumers` to be exceeded. Severity: **Medium**.

  `numClients` is read under `RLock` (line 465), then the lock is released (line 466). The `maxChannelConsumers` check at line 472 uses this stale value. The write `Lock` is only acquired at line 477. Between the `RUnlock` and `Lock`, other goroutines can concurrently pass the same check and add clients, each seeing room for one more. This allows the consumer limit to be exceeded by up to N-1 where N is the number of concurrent `AddClient` calls.

  **Expected:** The read of `numClients`, the limit check, and the map write should all occur under a single write `Lock`.
  **Actual:** Check-then-act with a gap between `RLock` read and `Lock` write.

### Finding 2

- **Line 382-385:** BUG — `PutMessageDeferred` is missing `exitMutex` protection, unlike `PutMessage`. Severity: **Medium**.

  `PutMessage` (line 318-330) acquires `exitMutex.RLock()` and checks `c.Exiting()` before proceeding. `PutMessageDeferred` does neither. This means:
  1. A deferred message can be added to a channel that is in the middle of `exit()`.
  2. `StartDeferredTimeout` (line 384) can race with `flush()` (lines 269-277) which iterates `deferredMessages` — `flush()` runs under `exitMutex.Lock` but `PutMessageDeferred` does not acquire `exitMutex.RLock`, so `exitMutex` does not serialize them.
  3. `messageCount` is incremented (line 383) even if the channel is exiting, inflating the counter.

  The caller (`topic.messagePump`, topic.go:330) does not hold the channel's `exitMutex`. If a channel is deleted independently while the topic's `messagePump` is still running, this race is reachable.

  **Expected:** `PutMessageDeferred` should hold `exitMutex.RLock()` and check `Exiting()`, consistent with `PutMessage`.
  **Actual:** No exit guard, allowing races with channel shutdown.

### Finding 3

- **Line 663-665:** QUESTION — `processInFlightQueue` exits loop entirely on `popInFlightMessage` failure. Severity: **Low**.

  When `PeekAndShift` (line 655) removes a message from the priority queue, and then `popInFlightMessage` (line 663) fails (e.g., because a concurrent `FinishMessage` already removed it from the map), the `goto exit` abandons all remaining timed-out messages in the queue. They will not be processed until the next `queueScanWorker` cycle. The same pattern exists in `processDeferredQueue` (line 634-636).

  This is likely benign in practice since the scan loop runs frequently, but under high concurrency with many simultaneous FIN commands, timeout processing could be systematically delayed.

### Finding 4

- **Line 232:** QUESTION — `len(c.inFlightMessages)` and `len(c.deferredMessages)` accessed without their respective mutexes in `flush()`. Severity: **Low**.

  The `flush()` function reads the length of `inFlightMessages` (protected by `inFlightMutex`) and `deferredMessages` (protected by `deferredMutex`) at line 232 without holding either mutex. This is technically a data race under the Go memory model.

  In practice this is likely safe: `flush()` is called from `exit()` which holds `exitMutex.Lock`, and client connections are closed before `flush()` runs, so no concurrent modifications should occur. However, the Go race detector would flag this.

---

## nsqd/topic.go

### Finding 5

- **Line 378-381:** QUESTION — `channel.Delete()` called while holding topic write lock during topic deletion. Severity: **Low-Medium**.

  In `exit(deleted=true)`, the topic write lock is held (line 377) while iterating channels and calling `channel.Delete()` on each. `channel.Delete()` calls `channel.exit(true)` which closes client connections, empties the queue, and deletes the backend — all potentially slow I/O operations. During this entire time, all other operations requiring the topic lock (`GetChannel`, `GetExistingChannel`, `DeleteExistingChannel`, `PutMessage`, `PutMessages`, `messagePump` channel updates) are blocked.

  `Notify()` itself is safe (runs in a goroutine), but the extended lock hold during backend deletion could cause cascading stalls in a system with many topics.

  **Expected:** Channels could be collected under lock, then deleted after releasing the lock (similar to the pattern in `DeleteExistingChannel` at lines 144-147).
  **Actual:** Channel deletion occurs under lock.

### Finding 6

- **Line 390-398:** QUESTION — `channel.Close()` called under topic `RLock` during graceful shutdown. Severity: **Low**.

  Similar to Finding 5 but for the non-deleted path. `channel.Close()` flushes in-flight and deferred messages to the backend (potentially slow disk I/O) while the topic `RLock` is held. This blocks any operation needing the topic write lock (e.g., `GetChannel`, `DeleteExistingChannel`) until all channels finish flushing.

---

## Summary

| Severity | Count | Type |
|----------|-------|------|
| Medium   | 2     | BUG  |
| Low-Medium | 1   | QUESTION |
| Low      | 3     | QUESTION |

**Files with no findings:** None — both files had findings.

**BUG findings:**
1. `AddClient` TOCTOU race bypasses `MaxChannelConsumers` (channel.go:463-479)
2. `PutMessageDeferred` missing `exitMutex` protection (channel.go:382-385)

**QUESTION findings:**
3. `processInFlightQueue`/`processDeferredQueue` early exit on concurrent finish (channel.go:663-665, 634-636)
4. Unsynchronized `len()` reads in `flush()` (channel.go:232)
5. `channel.Delete()` under topic write lock (topic.go:378-381)
6. `channel.Close()` under topic `RLock` (topic.go:390-398)

**Overall assessment:** **NEEDS DISCUSSION** — The two BUG findings are real concurrency defects. Finding 1 (`AddClient` TOCTOU) can violate the `MaxChannelConsumers` limit under concurrent connections. Finding 2 (`PutMessageDeferred` missing exit guard) is an inconsistency that can race with channel shutdown. Neither is likely to cause data loss in typical deployments, but both violate the intended concurrency contracts.
