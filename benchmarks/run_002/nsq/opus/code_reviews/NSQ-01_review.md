# Code Review: nsqd/channel.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Source:** /tmp/qpb_wt_opus_NSQ-01/nsqd/channel.go

---

### nsqd/channel.go

- **Line 320-323:** BUG (HIGH) — `PutMessageDeferred()` does not acquire `exitMutex.RLock()` before adding a deferred message, unlike `PutMessage()` (line 292) which correctly holds the lock. During shutdown, `exit()` acquires `exitMutex.Lock()` (line 156) and then calls `flush()` (line 187) to persist deferred messages. If `PutMessageDeferred` races with `exit()`, a message can be added to the deferred map *after* `flush()` has already drained it, causing permanent message loss. The message count is also incremented (line 321) for a message that will never be delivered.

- **Line 401-418:** BUG (MEDIUM) — TOCTOU race in `AddClient()`. The existence check and `numClients` count are read under `RLock` (lines 401-404), then the lock is released, and later a write `Lock` is acquired (line 415) to insert the client. Between the two lock acquisitions: (1) another goroutine could add the same `clientID`, causing a silent overwrite of the existing client entry; (2) `numClients` could have changed, allowing the `maxChannelConsumers` limit (line 410) to be exceeded. The check and insert should be done under a single write lock.

- **Line 441:** BUG (MEDIUM) — `RemoveClient()` reads `len(c.clients)` without holding any lock. The write lock was released on line 438, so `len(c.clients)` on line 441 is a data race with any concurrent `AddClient` or `RemoveClient` modifying the map. This can cause the ephemeral channel deletion check to trigger incorrectly (deleting a channel that still has clients) or not trigger when it should.

- **Line 574:** BUG (HIGH) — `processDeferredQueue()` ignores the error return from `c.put(msg)`. At this point, the message has already been removed from both the deferred priority queue (line 561, via `PeekAndShift`) and the deferred map (line 570, via `popDeferredMessage`). If `put()` fails (e.g., backend write error), the message is permanently lost — it exists in no data structure. The error should be handled, or at minimum logged.

- **Line 611:** BUG (HIGH) — `processInFlightQueue()` has the same issue: `c.put(msg)` error is ignored. The message has been removed from the in-flight PQ (line 592, via `PeekAndShift`) and the in-flight map (line 600, via `popInFlightMessage`). If the put fails, the timed-out message is silently dropped. This is the same class of bug as line 574.

- **Line 215:** QUESTION (LOW) — `flush()` reads `len(c.inFlightMessages)` and `len(c.deferredMessages)` without acquiring their respective mutexes. While this is only used for a log message and `flush()` is called during shutdown (after clients are closed), the reads are technically data races under the Go memory model. The subsequent loops (lines 233, 243) correctly acquire the locks, so the race is only in the log statement.

- **Line 252:** QUESTION (LOW) — `flush()` always returns `nil` even when one or more `writeMessageToBackend()` calls fail (lines 224-226, 235-237, 245-247). The caller `exit()` on line 187 receives a nil error and proceeds to `c.backend.Close()` even if messages failed to persist. This may be intentional best-effort behavior, but it means the caller cannot distinguish a clean flush from a partial one.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (HIGH) | 3 |
| BUG (MEDIUM) | 2 |
| QUESTION (LOW) | 2 |
| **Total** | **7** |

**Files with no findings:** N/A (single file review)

**Overall assessment:** **FIX FIRST** — Three high-severity findings involve potential message loss: the unguarded `PutMessageDeferred` and the two ignored `put()` errors in queue processing. The TOCTOU race in `AddClient` can cause the max-consumers limit to be silently exceeded. These should be addressed before shipping.
