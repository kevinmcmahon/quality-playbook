# NSQ-03 Code Review: nsqd/channel.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `nsqd/channel.go` (at `/tmp/qpb_wt_opus_NSQ-03`)

---

## Findings

### nsqd/channel.go

- **Line 279-280:** [BUG] **Severity: Medium.** `PutMessage` uses `c.RLock()` (the channel's embedded RWMutex) instead of `c.exitMutex.RLock()` for exit synchronization. Compare with `RequeueMessage` (line 367) which correctly uses `c.exitMutex.RLock()` before calling `c.put()`. The embedded RWMutex does not synchronize with `exit()` (which takes `c.exitMutex.Lock()` at line 145), so there is a TOCTOU race: a goroutine in `PutMessage` can pass the `Exiting()` check at line 281, then `exit()` can complete `flush()` and `c.backend.Close()`, and then `put()` at line 284 writes to a closed backend. This can cause message loss or a panic.

- **Line 309-312:** [BUG] **Severity: Medium.** `PutMessageDeferred` has no `Exiting()` check and does not hold `exitMutex.RLock()`. It unconditionally increments `messageCount` and calls `StartDeferredTimeout`, which adds to the deferred map and PQ. If called while the channel is exiting, messages are added to data structures that `flush()` or `Empty()` may have already drained or that `backend.Close()`/`backend.Delete()` has already finalized. This is inconsistent with `RequeueMessage` (line 367) and `processDeferredQueue` (line 514), both of which correctly guard with `exitMutex.RLock()`.

- **Line 537:** [BUG] **Severity: Medium.** `processDeferredQueue` discards the error return from `c.put(msg)`. At this point the message has already been removed from both the deferred PQ (line 524, via `PeekAndShift`) and the deferred map (line 533, via `popDeferredMessage`). If `put()` fails (e.g., backend write error), the message is silently lost — it exists in no data structure and will never be delivered.

- **Line 574:** [BUG] **Severity: Medium.** `processInFlightQueue` discards the error return from `c.put(msg)`. Same issue as line 537: the message has been removed from both the in-flight PQ (line 555, via `PeekAndShift`) and the in-flight map (line 563, via `popInFlightMessage`). A `put()` failure silently drops the message.

- **Line 239:** [BUG] **Severity: Low.** `flush()` returns `error` but always returns `nil`, even when one or more `writeMessageToBackend` calls fail (lines 215, 225, 233). The errors are logged but never propagated to the caller (`exit()` at line 176). The caller has no way to know that in-flight or deferred messages failed to persist, potentially leading to silent message loss on shutdown.

- **Lines 117-118:** [QUESTION] **Severity: Low.** `initPQ()` reassigns `c.inFlightMessages` and `c.deferredMessages` (the maps) without holding `inFlightMutex` or `deferredMutex`, while the PQ fields at lines 120-126 are reassigned under the respective mutexes. When called from `Empty()` (line 184, under `c.Lock()`), concurrent code that accesses these maps under `inFlightMutex`/`deferredMutex` (e.g., `popInFlightMessage` at line 448) could observe a partially-initialized state. In practice this may be safe because `exit()` holds `exitMutex.Lock()` before calling `Empty()`, blocking `processInFlightQueue`/`processDeferredQueue`, but `FinishMessage` and `TouchMessage` do not hold `exitMutex` and could race.

- **Lines 534-536, 563-566:** [QUESTION] **Severity: Low.** In both `processDeferredQueue` and `processInFlightQueue`, a failed `popDeferredMessage`/`popInFlightMessage` causes `goto exit`, terminating the entire processing loop. Since the PQ item was already shifted out at lines 524/555, the pop failure likely means another goroutine (e.g., `FinishMessage`) already handled the message — this is benign. However, the early exit means other ready-to-process messages in the PQ are delayed until the next tick of the processing interval, which could cause unnecessary latency spikes under high concurrency.

---

## Summary

| Severity | BUG | QUESTION |
|----------|-----|----------|
| Medium   | 4   | 0        |
| Low      | 1   | 2        |
| **Total**| **5** | **2**  |

### Key Concerns

1. **Exit synchronization gap in `PutMessage`** — the most consequential finding. The inconsistency between `PutMessage` (uses embedded RWMutex) and `RequeueMessage` (uses `exitMutex`) suggests `PutMessage` was missed when the exit-guard pattern was implemented.
2. **Silent message loss in `processInFlightQueue`/`processDeferredQueue`** — discarded `put()` errors mean messages removed from in-flight/deferred tracking disappear if the backend write fails.
3. **`PutMessageDeferred` unguarded** — no exit check at all, same class of bug as `PutMessage`.

### Overall Assessment

**FIX FIRST** — The exit-synchronization bugs (findings 1-2) and silent message loss on `put()` failure (findings 3-4) affect core message durability guarantees. These should be addressed before shipping.
