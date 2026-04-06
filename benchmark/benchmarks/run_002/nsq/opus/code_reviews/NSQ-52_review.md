# NSQ-52 Code Review: nsqd/channel.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `nsqd/channel.go` (at `/tmp/qpb_wt_opus_NSQ-52/nsqd/channel.go`)

---

## Findings

### nsqd/channel.go

- **Line 633:** BUG (Severity: High) — `break` instead of `continue` in `inFlightWorker`. When `popInFlightMessage` fails (e.g., due to a race where `TouchMessage` or `FinishMessage` already popped the message), the `break` exits the entire inner `for` loop, stopping timeout processing for all remaining timed-out messages until the next ticker tick (100ms). This means timed-out messages pile up and are only processed one-per-tick instead of being drained. Should be `continue` to skip the one message and keep processing others. Compare with `pqWorker` (line 660–669) which uses a similar pattern for deferred messages — that path does not have this bug because `popDeferredMessage` failure causes `return` inside the callback, and the outer loop naturally continues to the next `PeekAndShift`.

- **Line 635:** BUG (Severity: High) — Data race on `c.clients` map access in `inFlightWorker`. The line `client, ok := c.clients[msg.clientID]` reads from the `clients` map without holding `c.RLock()`. The `clients` map is mutated by `AddClient` (line 393, under `c.Lock()`) and `RemoveClient` (line 404, under `c.Lock()`). Concurrent map read/write in Go is undefined behavior and can cause a runtime panic. This needs `c.RLock()`/`c.RUnlock()` around the map access.

- **Line 239:** BUG (Severity: Medium) — `flush()` silently ignores `writeMessageToBackend` error for messages drained from `clientMsgChan`. The first loop (lines 237–240) discards the error return value from `writeMessageToBackend`, while the second loop (lines 249–252) and the in-flight/deferred flushes (lines 261–263, 268–270) properly check and log errors. A backend write failure here means a message is silently lost during shutdown with no log entry.

- **Line 275:** QUESTION (Severity: Medium) — `flush()` always returns `nil` even when `writeMessageToBackend` calls fail. The function signature returns `error`, but errors are only logged, never returned. The caller in `exit()` (line 198) ignores the return value anyway (`c.flush()` not `return c.flush()`... actually it is `c.flush()` then `return c.backend.Close()`), so the error propagation path is broken. If backend writes fail during flush, the caller has no way to know messages were lost.

- **Lines 604–608:** QUESTION (Severity: Medium) — `deferredWorker` ignores the error return from `c.doRequeue(msg)` (line 608). During shutdown, the sequence can be: (1) ticker fires in `pqWorker`, (2) `popDeferredMessage` succeeds — message removed from `deferredMessages` map, (3) `doRequeue` fails because `exitFlag` is set. The message is now lost: removed from the deferred map (so `flush()` won't find it at line 267), but never requeued. This is a narrow shutdown race but results in silent message loss.

- **Line 118:** QUESTION (Severity: Low) — `messagePump` goroutine is launched with bare `go` and is not tracked by `c.waitGroup`, unlike `router`, `deferredWorker`, and `inFlightWorker` (lines 120–122). Shutdown correctness relies on implicit synchronization: `flush()` blocks on `range c.clientMsgChan` (line 237) which completes when `messagePump` closes `clientMsgChan` (line 598). This works but is fragile — any future change to `flush()` or `messagePump` exit logic could break the implicit contract.

---

## Summary

| Severity | BUG | QUESTION |
|----------|-----|----------|
| High     | 2   | 0        |
| Medium   | 1   | 2        |
| Low      | 0   | 1        |

**Total findings: 6** (3 BUG, 3 QUESTION)

### Critical Bugs

1. **`break` vs `continue` (line 633)** — Causes timed-out in-flight messages to accumulate and process at only one per 100ms tick when any race occurs, instead of draining all expired messages immediately.
2. **Data race on `c.clients` (line 635)** — Unprotected concurrent map read can crash the process with a Go runtime panic.
3. **Silent error swallow in flush (line 239)** — Messages lost during graceful shutdown with no diagnostic output.

### Overall Assessment: **FIX FIRST**

The two high-severity bugs (lines 633 and 635) are correctness issues in the message timeout path. The `break` bug degrades timeout handling under contention, and the data race on `c.clients` can cause a runtime crash. Both should be fixed before shipping.
