# NSQ-58 Code Review: nsqd/statsd.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `nsqd/statsd.go` (at `/tmp/qpb_wt_opus_NSQ-58/nsqd/statsd.go`)

---

### nsqd/statsd.go

- **Line 124:** [BUG] **Severity: High** — GC pause percentile calculation is corrupted when `NumGC > 256`. `memStats.PauseNs` is a fixed-size `[256]uint64` array, so `len(memStats.PauseNs)` is always exactly 256. The condition `len(memStats.PauseNs) <= 256` is therefore **always true**, making the initial assignment `length := 256` dead code. `length` is always set to `int(memStats.NumGC)`. When `NumGC > 256`, a slice of size `NumGC` is allocated (line 127) but only 256 values are copied from `PauseNs` (line 128), leaving the remaining elements as zero. After sorting, these zeros land at the front of the array, causing all percentile calculations (lines 135-137) to report artificially low or zero GC pause times. The correct logic should cap `length` at `min(int(memStats.NumGC), 256)`.

- **Line 152-157:** [BUG] **Severity: High** — `percentile()` panics with index out of range when `length` is 0. When `memStats.NumGC` is 0 (no GC cycles have run yet, possible on the very first statsd tick), `length` = 0, and `gcPauses` is an empty slice. Inside `percentile()`: `indexOfPerc = int(math.Ceil((perc/100.0 * 0) + 0.5)) = 1`. The guard `indexOfPerc >= length` triggers, setting `indexOfPerc = length - 1 = -1`. Then `arr[-1]` causes a **panic: runtime error: index out of range**. This crashes the entire `statsdLoop` goroutine, silently stopping all statsd reporting for the lifetime of the process.

- **Line 56-58, 83-85, 99-101, 103-105:** [QUESTION] **Severity: Low** — `diff` is computed as unsigned subtraction of `uint64` counters (e.g., `topic.MessageCount - lastTopic.MessageCount`). If a topic or channel is deleted and recreated between statsd intervals with the same name, and the new counter value is lower than the cached `lastStats` value, this underflows to a very large `uint64`. The result is then cast to `int64` at the `statsd.Incr()` call, producing a bogus metric spike. In normal operation counters are monotonically increasing so this would not trigger, but it could occur during topic/channel churn.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (High) | 2 |
| QUESTION (Low) | 1 |

**Findings:**
- **BUG:** GC pause array always uses `NumGC` as length instead of capping at 256, corrupting percentiles after 256 GC cycles.
- **BUG:** `percentile()` panics on empty input when no GC cycles have occurred.
- **QUESTION:** Unsigned counter diff could underflow on topic/channel recreation with same name.

**Overall assessment:** **FIX FIRST** — The two high-severity bugs will cause a panic (crashing statsd reporting permanently) and silently corrupt GC pause metrics in any long-running nsqd process.
