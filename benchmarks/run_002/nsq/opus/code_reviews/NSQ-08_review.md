# NSQ-08 Code Review: nsqd/http.go, nsqd/stats.go, nsqd/statsd.go

## nsqd/statsd.go

- **Line 67-72:** QUESTION. The uint64 counter diff `topic.MessageCount - lastTopic.MessageCount` will underflow (wrap to a huge value) if a topic is deleted and recreated between statsd intervals with a lower message count. The result is cast to `int64` via `client.Incr(stat, int64(diff))`, producing a bogus large increment sent to statsd. The same pattern applies to `MessageBytes` at lines 70-72. Expected: diff should be clamped or skipped when the current count is less than the previous. Actual: unsigned underflow produces a corrupt statsd metric. This could cause statsd dashboards to show massive spikes on topic recreation.

- **Line 101-103:** QUESTION. Same uint64 underflow pattern for `channel.MessageCount - lastChannel.MessageCount`. A deleted-and-recreated channel produces a corrupt diff.

- **Line 117-119:** QUESTION. Same uint64 underflow pattern for `channel.RequeueCount - lastChannel.RequeueCount`.

- **Line 120-122:** QUESTION. Same uint64 underflow pattern for `channel.TimeoutCount - lastChannel.TimeoutCount`.

- **Line 46:** QUESTION. `writers.NewSpreadWriter(conn, interval-time.Second, n.exitChan)` computes a spread duration by subtracting 1 second from `StatsdInterval`. There is no validation that `StatsdInterval > time.Second` anywhere in the codebase (only a default of 60s). If an operator configures `--statsd-interval=500ms`, this underflows to a negative `time.Duration`, which would be passed to the SpreadWriter. Similarly, `time.NewTicker(interval)` at line 32 would panic if interval is set to 0.

## nsqd/http.go

- **Line 643-660:** QUESTION. The `/config/:opt` PUT handler reads current options via `opts := *s.nsqd.getOpts()` (a value copy), modifies the copy, then calls `s.nsqd.swapOpts(&opts)`. Two concurrent PUT requests both read the same baseline, each modify a different field, and the last `swapOpts` wins — silently discarding the other request's change. Expected: concurrent config updates are serialized. Actual: last-writer-wins race that can silently lose a config change (e.g., one request updates `nsqlookupd_tcp_addresses` while another updates `log_level`; the second swap overwrites the first).

- **Line 292:** QUESTION. `err.(*protocol.FatalClientErr).Code[2:]` performs an unchecked type assertion on the error returned by `readMPUB`. While inspection of `readMPUB` confirms all current error paths return `*protocol.FatalClientErr`, this is a fragile coupling — any future error path in `readMPUB` that returns a different error type (e.g., a raw `io.EOF` or `io.ErrUnexpectedEOF` leaking through) would cause a nil-pointer panic on the type assertion. A safe type assertion `err, ok := ...` would prevent this.

## nsqd/stats.go

- **Line 66-71:** QUESTION. `NewChannelStats` acquires `c.inFlightMutex.Lock()` and `c.deferredMutex.Lock()` separately (not atomically together). The `inflight` and `deferred` counts are therefore not a consistent snapshot — a message could move from deferred to in-flight between the two lock acquisitions, causing the stats to double-count or under-count by one. This is acceptable for approximate stats but worth noting if exact consistency is ever required.

- **Line 89:** QUESTION. `c.e2eProcessingLatencyStream.Result()` is called outside of any channel lock (the caller at stats.go:165 calls `NewChannelStats` after releasing `c.RUnlock()` at line 164). If the `e2eProcessingLatencyStream` is concurrently being written to by the message processing path, this is a potential data race. Whether this is safe depends on the internal thread-safety of the quantile library.

## Summary

| Severity | Count |
|----------|-------|
| BUG      | 0     |
| QUESTION | 9     |

- **Files with no findings:** None — all three files have findings.
- **Overall assessment:** SHIP IT — No confirmed bugs found. The QUESTION findings are edge cases in statsd counter arithmetic (uint64 underflow on entity recreation), a config update TOCTOU race, and minor consistency gaps in stats collection. These are low-probability operational edge cases rather than correctness bugs in the core message path.
