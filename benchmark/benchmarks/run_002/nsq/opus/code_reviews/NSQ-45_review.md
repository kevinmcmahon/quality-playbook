# Code Review: nsqd/topic.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Source:** `/tmp/qpb_wt_opus_NSQ-45/nsqd/topic.go`

---

### nsqd/topic.go

- **Line 387:** [BUG] **Unsynchronized map iteration in Close path — data race.** In `exit(false)` (the `Close` path), `t.channelMap` is iterated without holding any lock. Compare with the `exit(true)` (Delete) path at line 374 which correctly acquires `t.Lock()` before iterating. `GetChannel()` (line 106) does not check `exitFlag` before acquiring `t.Lock()` and modifying `channelMap`, so a concurrent `GetChannel()` call during shutdown creates a data race on the map. **Severity: HIGH.** Expected: iteration under `t.RLock()` (consistent with the Delete path). Actual: no lock held. Impact: concurrent map read/write panic or silent corruption.

- **Line 106:** [QUESTION] **`GetChannel()` does not check `exitFlag` before creating a channel.** `PutMessage()` (line 187) and `PutMessages()` (line 204) both check `exitFlag` under `t.RLock()` to reject operations on a closing topic. `GetChannel()` does not. A new channel created after `exit()` sets `exitFlag` (line 354) but before the channel iteration at line 387 could be created and never properly closed, leaking its goroutines and backend resources. **Severity: MEDIUM.** Is this intentional, relying on callers to not call `GetChannel()` during shutdown?

- **Lines 413–435:** [BUG] **`flush()` swallows all write errors and always returns nil.** `flush()` has return type `error` but always returns `nil` (line 434). When `writeMessageToBackend` fails at line 423, the error is logged but not accumulated or returned. The caller at line 396 (`t.flush()`) discards the return value anyway, but the function signature is misleading and errors during shutdown flush are silently lost — the caller has no way to know messages were dropped. **Severity: LOW.** Expected: propagate at least the first (or last) error. Actual: always returns nil. Impact: silent message loss on shutdown if backend write fails.

- **Line 241:** [QUESTION] **`Depth()` reads `memoryMsgChan` length and backend depth without synchronization.** `len(t.memoryMsgChan)` and `t.backend.Depth()` are read without any lock, so the two values are not atomic with respect to each other — a message could move from memory to backend between the two reads, causing a momentary double-count or under-count. **Severity: LOW.** This is likely acceptable for a stats/monitoring function, but worth confirming this is only used in non-critical paths.

---

### Summary

| Severity | Count |
|----------|-------|
| HIGH     | 1     |
| MEDIUM   | 1     |
| LOW      | 2     |

- **BUG findings:** 2 (unsynchronized map iteration in Close, flush swallows errors)
- **QUESTION findings:** 2 (GetChannel missing exitFlag check, Depth non-atomic read)

**Overall assessment: FIX FIRST** — The missing lock on `channelMap` iteration in the Close path (line 387) is a data race that can cause a runtime panic under concurrent access during shutdown. This should be fixed before shipping.
