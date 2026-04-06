# NSQ-29 Code Review: apps/nsq_to_file/nsq_to_file.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `/tmp/qpb_wt_opus_NSQ-29/apps/nsq_to_file/nsq_to_file.go`

---

### apps/nsq_to_file/nsq_to_file.go

- **Lines 191-198:** BUG (Medium). `Close()` calls `f.out.Sync()` *before* `f.gzipWriter.Close()`. The gzip `Close()` writes the GZIP footer (CRC32 checksum + size) to `f.out` via `f.Write()`, but this data is never synced to stable storage — only `f.out.Close()` follows, which does not guarantee fsync. A crash after `Close()` returns could leave a truncated gzip file missing its trailer, making the entire file unreadable. Compare with `Sync()` (lines 209-212) which correctly calls `gzipWriter.Close()` before `f.out.Sync()`. Fix: move `f.out.Sync()` after `f.gzipWriter.Close()`, or add a second `f.out.Sync()` after the gzip close.

- **Lines 391-394:** BUG (Low). `startTopicRouter()` calls `t.wg.Add(1)` inside the goroutine body, but it is launched with `go t.startTopicRouter(logger)` (lines 427, 535). The `sync.WaitGroup` contract requires `Add()` to be called before `Wait()` can observe it. If a SIGTERM arrives immediately after `go t.startTopicRouter()` in `syncTopics()` (line 427), the `t.wg.Wait()` at line 454 could return before the new goroutine has called `wg.Add(1)`, causing the program to exit before that router has shut down cleanly (potentially losing unflushed messages). Fix: call `t.wg.Add(1)` before the `go` statement, and `defer t.wg.Done()` inside the goroutine.

- **Line 106:** QUESTION (Low). `HandleMessage` sends to `f.logChan` (buffer size 1, line 340) unconditionally after calling `DisableAutoResponse()`. With `maxInFlight` defaulting to 200, the handler goroutine blocks until `router()` drains the channel. This appears to be intentional backpressure via go-nsq's single handler goroutine model, but if go-nsq's concurrency handler count were ever increased (via `AddConcurrentHandlers`), multiple goroutines would contend on the size-1 channel while holding un-finished messages.

- **Line 446:** QUESTION (Low). `time.Tick()` returns a channel from a `Ticker` that can never be stopped or garbage-collected. Since `watch()` runs for the program's lifetime this is benign, but the Go documentation explicitly warns against using `time.Tick` in long-lived functions where the ticker should be recoverable. `time.NewTicker()` with a deferred `Stop()` is the safer pattern and would also clean up properly if `watch()` were ever refactored to return early.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (Medium) | 1 |
| BUG (Low) | 1 |
| QUESTION (Low) | 2 |

**Overall assessment:** NEEDS DISCUSSION — The gzip `Close()` ordering bug (lines 191-198) can cause data loss (unreadable gzip files) on crash. The `WaitGroup` race is low-probability but violates the documented contract. Both are straightforward fixes.
