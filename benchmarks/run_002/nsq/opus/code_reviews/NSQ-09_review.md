# NSQ-09 Code Review: nsqd/stats.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Source:** `/tmp/qpb_wt_opus_NSQ-09/nsqd/stats.go`

---

### nsqd/stats.go

- **Line 54:** [BUG] **Data race on `c.inFlightMessages` — read without lock.** `NewChannelStats()` reads `len(c.inFlightMessages)` but is called at line 143 of `GetStats()` *after* `c.RUnlock()` at line 142. The `inFlightMessages` map is protected by its own dedicated `c.inFlightMutex` (see channel.go:70), not by the channel's main `RWMutex`. Neither lock is held when this read occurs. Concurrent goroutines calling `pushInFlightMessage` / `popInFlightMessage` mutate this map under `inFlightMutex`, so this is a data race. On Go's memory model, concurrent map read + write is undefined behavior and can cause a runtime crash. **Severity: HIGH.**

- **Line 55:** [BUG] **Data race on `c.deferredMessages` — read without lock.** Same issue as line 54. `len(c.deferredMessages)` is read in `NewChannelStats()` without holding `c.deferredMutex` (channel.go:67). Concurrent `pushDeferredMessage` / `popDeferredMessage` calls mutate this map under `deferredMutex`. **Severity: HIGH.**

- **Line 62:** [QUESTION] **`c.e2eProcessingLatencyStream.Result()` called without any lock.** `NewChannelStats()` is called outside the channel's `RLock` scope. If `e2eProcessingLatencyStream` methods are not internally thread-safe, this is a data race. The `quantile` package may provide its own synchronization, but this should be verified. **Severity: MEDIUM (pending verification).**

- **Line 126:** [QUESTION] **`len(n.topicMap)` read after `n.RUnlock()`.** At line 124 the NSQD read lock is released, but line 126 reads `len(n.topicMap)` for slice capacity without the lock. This is technically a data race (concurrent map length read during topic creation/deletion), though the consequence is only a suboptimal capacity hint — not incorrect results. **Severity: LOW.**

- **Line 135:** [QUESTION] **`len(t.channelMap)` read after `t.RUnlock()`.** Same pattern as line 126. The topic read lock is released at line 133, but `len(t.channelMap)` is read at line 135 for slice capacity. Technically a data race, consequence is only suboptimal allocation. **Severity: LOW.**

---

### Summary

| Severity | Count | Type |
|----------|-------|------|
| HIGH     | 2     | BUG  |
| MEDIUM   | 1     | QUESTION |
| LOW      | 2     | QUESTION |

**Total findings:** 5 (2 BUG, 3 QUESTION)

**Overall assessment: FIX FIRST**

The two HIGH-severity bugs are genuine data races on `inFlightMessages` and `deferredMessages` maps. In Go, concurrent unsynchronized map access (even `len()` during a write) is undefined behavior that can crash the process. The fix is straightforward: either acquire `c.inFlightMutex` and `c.deferredMutex` within `NewChannelStats()`, or move the `len()` calls inside the `c.RLock()` scope in `GetStats()` and pass the counts as parameters. The latter approach is preferable as it keeps `NewChannelStats` a pure data constructor.
