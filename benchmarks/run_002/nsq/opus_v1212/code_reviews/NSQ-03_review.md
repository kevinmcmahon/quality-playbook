# Code Review: nsqd/channel.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Commit:** 9ea5071 (worktree at /tmp/qpb_wt_v1212_NSQ-03)

---

### nsqd/channel.go

- **Lines 563-565:** [BUG] `processInFlightQueue` aborts on race with concurrent `FinishMessage`. Severity: **High**.
  `PeekAndShift` (line 555) pops the message from the priority queue under `inFlightMutex`, then releases the lock. `popInFlightMessage` (line 563) re-acquires `inFlightMutex` and attempts to remove the message from the map. If a concurrent `FinishMessage` (or `TouchMessage`/`RequeueMessage`) calls `popInFlightMessage` between lines 556 and 563, it wins the race and removes the message from the map. The `popInFlightMessage` at line 563 then returns `"ID not in flight"`, and `goto exit` at line 565 **stops processing all remaining timed-out messages** in the queue. Those messages remain in the PQ and won't be requeued until the next scan cycle (up to `QueueScanInterval` later, default 100ms). Under high FIN throughput this can cause repeated early exits, systematically delaying timeout requeues.
  **Expected:** `continue` instead of `goto exit` so remaining timed-out messages are still processed.
  **Sibling:** Same bug exists in `processDeferredQueue` at lines 534-536 — a concurrent operation removing the deferred message causes `goto exit`, halting processing of all remaining ready deferred messages.

- **Lines 534-536:** [BUG] `processDeferredQueue` aborts on race with concurrent message removal. Severity: **High**.
  Identical pattern to the in-flight bug above. `PeekAndShift` (line 524) pops the item from the deferred PQ, then `popDeferredMessage` (line 533) tries to remove from the map. If a concurrent operation already removed it, `goto exit` stops all further deferred message processing for this cycle. Deferred messages that are past their deadline remain stuck until the next scan.

- **Lines 278-290 vs 367-374:** [BUG] `PutMessage` does not hold `exitMutex`, unlike `RequeueMessage`. Severity: **Medium**.
  `RequeueMessage` (line 367) correctly acquires `c.exitMutex.RLock()` before calling `c.put()`, coordinating with `exit()` which holds `exitMutex.Lock()`. However, `PutMessage` (line 279) only acquires `c.RLock()` (the channel's embedded RWMutex) and checks `c.Exiting()` atomically. This creates a TOCTOU race: `PutMessage` observes `Exiting()==false`, then `exit()` sets the flag, calls `flush()` to drain `memoryMsgChan`, and calls `backend.Close()`. Then `PutMessage.put()` writes to `memoryMsgChan` (now drained and never read again) or to a closed backend. In the close path, `flush()` is called without any lock that blocks `PutMessage`, so the message is lost.
  **Expected:** `PutMessage` should use `exitMutex.RLock()`/`exitMutex.RUnlock()` like `RequeueMessage` does.

- **Lines 309-312:** [BUG] `PutMessageDeferred` has no exit guard at all. Severity: **Medium**.
  `PutMessageDeferred` increments `messageCount` and calls `StartDeferredTimeout` without checking `Exiting()` or holding `exitMutex`. After `exit()` has set the exit flag and flushed deferred messages, `PutMessageDeferred` can still push a new deferred message into the map and PQ. This message will never be delivered (no scan worker will process it) and won't be flushed to the backend (flush already completed). The message count is incremented but the message is silently lost.
  **Expected:** Guard with `exitMutex.RLock()` and `Exiting()` check, consistent with `RequeueMessage`.

- **Lines 114-127 (initPQ), called from line 184 (Empty):** [BUG] `initPQ` replaces `inFlightMessages` and `deferredMessages` maps without holding their respective mutexes. Severity: **Medium**.
  `initPQ()` assigns new maps at lines 117-118 without holding `inFlightMutex` or `deferredMutex`. It then separately locks each mutex to replace the PQs (lines 120-126). When called from `Empty()` (line 184), which only holds `c.Lock()`, there is a data race: concurrent `popInFlightMessage` (line 448) holds `inFlightMutex` (not `c.RLock()`) and reads `c.inFlightMessages`. The map variable assignment at line 117 and the map read at line 449 are unsynchronized — a data race detectable by `-race`.
  **Expected:** The map assignments at lines 117-118 should be inside the respective mutex locks, or `Empty()` should also acquire `inFlightMutex` and `deferredMutex`.

- **Lines 203-239 (flush):** [QUESTION] `flush` iterates `inFlightMessages` and `deferredMessages` without holding their mutexes. Severity: **Low**.
  `flush()` is only called from `exit()` which holds `exitMutex.Lock()`, preventing concurrent `processInFlightQueue`/`processDeferredQueue` (which hold `exitMutex.RLock()`). Client connections are closed before `flush()` is called (line 164-167), so `FinishMessage`/`TouchMessage`/`RequeueMessage` should not be running. However, if any client goroutine has not yet fully stopped after `client.Close()` (Close is asynchronous — it signals but may not wait), a `popInFlightMessage` call could race with the map iteration at line 224. This is likely safe in practice due to timing, but is technically a race.

- **Lines 163-167 (exit, client close):** [QUESTION] `exit` iterates clients under `c.RLock()` but `client.Close()` may be asynchronous. Severity: **Low**.
  `exit()` calls `client.Close()` for each client under `c.RLock()` (lines 163-167), then immediately proceeds to `Empty()`/`flush()`. If `client.Close()` only signals the client goroutine to stop (sends on a channel) rather than waiting for it to finish, there is a window where client goroutines are still running when `flush()` or `Empty()` executes. This could cause concurrent access to in-flight/deferred data structures. The severity depends on whether `client.Close()` is synchronous — if it waits for the client goroutine to exit, this is safe.

- **Line 537 (processDeferredQueue put):** [QUESTION] `put` error is silently discarded. Severity: **Low**.
  When `processDeferredQueue` successfully pops a deferred message and calls `c.put(msg)` at line 537, the return value of `put()` is discarded. If `put()` fails (e.g., backend write error), the message has already been removed from both the deferred PQ and the deferred map — it is lost. Compare with `processInFlightQueue` at line 574 which has the same pattern. While `put()` failure sets NSQD health via `SetHealth`, the individual message is silently dropped.
  **Expected:** At minimum, log the error. Or consider whether the message should be re-added to the deferred queue on failure.

---

### Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 2     |
| Medium   | 3     |
| Low      | 3     |

**Total findings:** 8 (5 BUG, 3 QUESTION)

**Key themes:**
1. **`goto exit` instead of `continue` in queue processors** (High): Both `processInFlightQueue` and `processDeferredQueue` abort processing all remaining items when a single race condition occurs, causing systematic requeue/delivery delays under concurrent FIN load.
2. **Inconsistent exit guards** (Medium): `RequeueMessage` correctly uses `exitMutex`, but `PutMessage` and `PutMessageDeferred` do not, creating TOCTOU races that can lose messages during shutdown.
3. **`initPQ` map reassignment without mutex** (Medium): Data race on map variables when `Empty()` is called concurrently with in-flight operations.

**Overall assessment:** **FIX FIRST** — The `goto exit` bugs in both queue processors can cause systematic message delivery delays under normal concurrent operation, not just during shutdown edge cases. The exit guard inconsistency risks message loss during graceful shutdown.
