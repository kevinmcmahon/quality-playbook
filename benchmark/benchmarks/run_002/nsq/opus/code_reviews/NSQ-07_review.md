# NSQ-07 Code Review: nsqd/topic.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Source:** `/tmp/qpb_wt_opus_NSQ-07/nsqd/topic.go`

---

### nsqd/topic.go

- **Line 197-204:** [BUG] **PutMessages undercounts messageCount on partial failure.** If `put()` succeeds for messages 0..N-1 but fails on message N, the function returns the error at line 199-200 without incrementing `messageCount` (line 203 is never reached). The N messages that were successfully written to the memory channel or backend are not reflected in `messageCount`. This makes the topic's message counter permanently inaccurate. Severity: **Low** (affects metrics/stats only, not message delivery).

- **Line 372-378:** [BUG] **Close (non-delete) path iterates `channelMap` without holding a lock.** After `messagePump` exits (line 356), the non-delete branch at line 372 iterates `t.channelMap` with no lock held. `GetChannel()` (line 103) and `DeleteExistingChannel()` (line 145) both acquire `t.Lock()` and mutate `channelMap`, but neither checks `exitFlag`. A concurrent call to either function during shutdown creates a data race on the map. The delete path at lines 359-364 correctly acquires the lock. Severity: **Medium** (data race; could cause a panic from concurrent map read/write on shutdown).

- **Line 398-421:** [BUG] **`flush()` always returns nil, silently discarding backend write errors.** The `flush()` function logs backend write errors at line 412 but continues the loop and unconditionally returns `nil` at line 421. Furthermore, the caller at line 381 discards the return value (`t.flush()` with no assignment). During graceful shutdown, if the backend disk queue is unhealthy, in-memory messages that fail to flush are silently lost with no error propagation. Severity: **Medium** (silent message loss during shutdown when backend is degraded).

- **Line 358-363:** [QUESTION] **Delete path calls `channel.Delete()` while holding the topic lock.** The delete branch acquires `t.Lock()` at line 359 and calls `channel.Delete()` at line 362 inside the loop. `channel.Delete()` → `channel.exit(true)` acquires `c.exitMutex` and iterates `c.clients`, calling `client.Close()`. If any client close handler attempts to acquire the topic lock (e.g., through a channel update notification path), this would deadlock. Inspecting `channel.exit()` shows it does NOT call back into the topic's deleteCallback, so this appears safe in the current code. However, the coupling is fragile — a future change to `channel.Delete()` that calls back into the topic would introduce a deadlock. Flagged for awareness, not as a confirmed bug.

- **Line 168:** [QUESTION] **Ephemeral topic deletion relies on `numChannels` captured before channel.Delete() completes.** `numChannels` is captured at line 153 under the lock, then the lock is released, and `channel.Delete()` runs. If another goroutine concurrently calls `DeleteExistingChannel()` on a different channel of the same ephemeral topic, both could see `numChannels == 0` (since each captures the count after its own deletion). Both would invoke `t.deleter.Do(...)`, but `sync.Once` ensures only one executes. This is safe due to `sync.Once`, so this is not a bug — just noting the non-obvious correctness dependency.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (Medium) | 2 |
| BUG (Low) | 1 |
| QUESTION | 2 |

**Files with no findings:** N/A (single file review)

**Overall assessment:** **NEEDS DISCUSSION** — The two medium-severity bugs (unlocked map iteration during close, silent error swallowing in flush) both relate to the shutdown path and could cause message loss or panics under specific timing conditions. The PutMessages counter bug is low-impact but straightforward to fix. None of these are critical runtime bugs under normal operation, but the shutdown-path issues should be addressed for production reliability.
