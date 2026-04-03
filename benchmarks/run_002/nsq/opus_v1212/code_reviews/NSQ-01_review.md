# Code Review: nsqd/channel.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** nsqd/channel.go (617 lines)
**Commit:** 9ea5071 (master)

---

## Findings

### nsqd/channel.go

- **Line 571-572, 601-602:** [BUG] **Severity: High.** `processDeferredQueue` and `processInFlightQueue` abort the entire processing loop on a single race condition. In `processInFlightQueue`, `PeekAndShift` (line 592) removes a message from the priority queue under `inFlightMutex`, then releases the lock. `popInFlightMessage` (line 600) re-acquires `inFlightMutex` to remove from the map. Between these two operations, a concurrent `FinishMessage` or `TouchMessage` can call `popInFlightMessage` first and succeed, causing the subsequent pop at line 600 to return `"ID not in flight"`. The `goto exit` at line 602 then **stops processing all remaining timed-out messages** in the queue. Those messages remain stuck until the next queueScanLoop cycle. The identical pattern exists in `processDeferredQueue` at lines 570-572. Expected: `continue` to skip the raced message and keep processing. Actual: `goto exit` halts all processing. Under high-throughput with frequent FIN/TOUCH operations, this can cause cascading message delivery delays.

- **Line 574, 611:** [BUG] **Severity: Medium.** `processDeferredQueue` and `processInFlightQueue` both call `c.put(msg)` without checking the return value. If `put` fails (e.g., backend disk write error when the memory channel is full), the message is silently lost — it has already been removed from the deferred/in-flight structures but is never delivered or re-enqueued. Expected: error should be logged or the message should be returned to the queue. Actual: message is permanently lost.

- **Line 320-323:** [BUG] **Severity: Medium.** `PutMessageDeferred` does not acquire `c.exitMutex.RLock()` or check `c.Exiting()` before calling `StartDeferredTimeout`. Compare with `PutMessage` (lines 291-303) which correctly guards with `exitMutex`. A deferred message can be added to the deferred queue after the channel has started exiting. The caller in `topic.go:330` invokes `PutMessageDeferred` without any channel-level exit check. If the channel is mid-exit, `StartDeferredTimeout` writes to structures that `flush()` or `Empty()` may have already processed or cleared, causing the message to be orphaned.

- **Line 401-417:** [BUG] **Severity: Medium.** `AddClient` has a TOCTOU race on `MaxChannelConsumers` enforcement. The client count is read under `RLock` (line 403), the limit check happens after `RUnlock` (line 410), and the insertion happens under a separate `Lock` (line 415-417). Two concurrent `AddClient` calls can both read `numClients = N-1` (where N is the limit), both pass the check, and both insert — exceeding the configured `MaxChannelConsumers` limit. Expected: check and insert under a single write lock. Actual: the limit is advisory, not enforced under concurrency.

- **Line 441:** [BUG] **Severity: Medium.** `RemoveClient` reads `len(c.clients)` after releasing the write lock at line 439. This is a data race per Go's memory model — another goroutine can concurrently modify `c.clients` via `AddClient`. While `sync.Once` prevents double-execution of the delete callback, the race window allows: (1) RemoveClient removes last client, releases lock; (2) AddClient adds a new client; (3) RemoveClient reads `len(c.clients) == 1` (not 0), so the ephemeral channel is never deleted despite having no real subscribers after the new client also disconnects (since `deleter` is already consumed). Expected: the ephemeral deletion check should be inside the write lock.

- **Line 215:** [BUG] **Severity: Low.** `flush()` reads `len(c.inFlightMessages)` and `len(c.deferredMessages)` without holding `inFlightMutex` or `deferredMutex` respectively. This is a data race per Go's race detector. The values are only used for a log message, so the impact is limited to potentially inaccurate log output, but it would trigger `-race` failures in testing. The actual flush loops below (lines 233-250) correctly acquire the mutexes.

- **Line 182-183:** [QUESTION] **Severity: Medium.** In the `exit(deleted=true)` path, `Empty()` is called at line 182, which acquires `c.Lock()` and reinitializes in-flight and deferred structures via `initPQ()`. Then `c.backend.Delete()` is called at line 183. However, if `processInFlightQueue` is concurrently running (it checks `c.Exiting()` but the `exitFlag` was just set at line 159 — there's a window where it already passed the check), it could be mid-iteration when `initPQ` replaces the maps. The message peeked from the old PQ would fail `popInFlightMessage` on the new (empty) map, and be silently dropped. Is there a synchronization mechanism outside this file that prevents `processInFlightQueue` from running concurrently with `exit()`?

- **Line 306-316:** [QUESTION] **Severity: Low.** When `memoryMsgChan` is `nil` (MemQueueSize==0 and not ephemeral, per line 88), the `select` in `put()` correctly falls through to `default` (Go spec: send on nil channel in select is never ready). All messages go directly to the backend. This is correct behavior, but worth noting: the comment at line 87 says "avoid mem-queue if size == 0 for more consistent ordering" — the ordering guarantee depends entirely on the backend's FIFO behavior. If the backend (diskqueue) is not strictly FIFO under concurrent writes, the ordering guarantee is not met. Is this assumption validated?

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 1     |
| Medium   | 5     |
| Low      | 2     |

**Total findings:** 8 (6 BUG, 2 QUESTION)

### Key Risk Areas
1. **Message processing stalls** (High): The `goto exit` pattern in both queue processors means a single race condition stops all timeout processing until the next scan cycle, potentially causing message delivery delays across the entire channel.
2. **Silent message loss** (Medium): Two paths — ignored `put()` errors in queue processors, and missing exit guard in `PutMessageDeferred` — can permanently lose messages without any indication.
3. **Concurrency correctness** (Medium): `AddClient` TOCTOU and `RemoveClient` post-lock read are classic concurrency bugs that can violate configured limits and leak ephemeral channels.

### Overall Assessment: **FIX FIRST**

The `goto exit` bug in queue processors (finding #1) is the highest-priority fix — it can cause visible message delivery delays under normal operation. The silent message loss paths (findings #2 and #3) should be addressed next. The concurrency issues (findings #4 and #5) are lower-priority but represent correctness violations.
