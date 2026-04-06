# NSQ-27 Code Review: internal/writers/spread_writer.go

## internal/writers/spread_writer.go

- **Line 32:** BUG (High). **Division by zero panic when `Flush()` is called with empty buffer.** `s.interval / time.Duration(len(s.buf))` panics if no `Write()` calls preceded `Flush()`. In the caller (`nsqd/statsd.go:152-153`), `bw.Flush()` then `sw.Flush()` are always called. If nsqd has zero topics and `StatsdMemStats` is disabled, nothing is written to the `BoundaryBufferedWriter`, so nothing propagates to `SpreadWriter`, and `sw.Flush()` is called with `len(s.buf) == 0`. This is a runtime panic in production for a freshly started or idle nsqd.

- **Line 33:** BUG (High). **`time.NewTicker` panics on zero or negative duration.** Even when `buf` is non-empty, if `s.interval` is very small relative to `len(s.buf)`, integer division truncation can yield `sleep == 0`. `time.NewTicker` documents that it panics if the duration is not positive. In `statsd.go:46`, the interval passed is `interval - time.Second`; if `StatsdInterval` is configured to exactly 1 second, this yields `0`, and any non-empty buf will trigger a panic. If `StatsdInterval` is less than 1 second (e.g. misconfiguration), the interval is negative, also causing a panic.

- **Line 35:** QUESTION (Medium). **`s.w.Write(b)` return value is discarded.** If the underlying writer (a UDP `net.Conn` in `statsd.go:41`) returns an error, it is silently ignored. This means statsd write failures are invisible -- no log, no metric, no health signal. This may be intentional for UDP fire-and-forget semantics, but it means partial flush failures are completely silent.

## Summary

| Severity | Count |
|----------|-------|
| BUG (High) | 2 |
| QUESTION (Medium) | 1 |

**Overall assessment: FIX FIRST**

The two division/ticker panics on line 32-33 are reachable in production (idle nsqd with no topics, or `StatsdInterval` set to 1s) and will crash the `statsdLoop` goroutine. A guard at the top of `Flush()` to return early when `len(s.buf) == 0` fixes the first bug. Clamping `sleep` to a minimum positive duration (e.g. `1 * time.Millisecond`) or guarding the `NewTicker` call fixes the second.
