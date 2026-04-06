# NSQ-47 Targeted Code Review

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Focus Areas:** 9 (Configuration Parameter Validation), 10 (Input Validation Failure Modes), 11 (Exit Path Resource Completeness), 12 (Go Channel Lifecycle in Select Statements)

---

## internal/protocol/protocol.go

### Line 49-50: **BUG** — Severity: Low — `SendFramedResponse` returns incorrect byte count on second write error
When the second `w.Write(beBuf)` (frame type) fails at line 49, the function returns `n + 4`. But `n` is the return from this second write (which may be 0 on error), and `4` is a hardcoded offset for the first write. The total bytes written should be `4 + n` (first write succeeded with 4 bytes, second write wrote `n` bytes). The arithmetic happens to be equivalent (`n + 4` == `4 + n`), so the returned count is actually correct. **On further analysis, this is not a bug — the return values are correct.** Retracted.

No findings for this file.

---

## nsqd/nsqd.go

### Line 119-121: **QUESTION** — Severity: Medium — `TLSClientAuthPolicy` unconditionally overrides explicit `TLSRequired` setting (Focus Area 9)
```go
if opts.TLSClientAuthPolicy != "" && opts.TLSRequired == TLSNotRequired {
    opts.TLSRequired = TLSRequired
}
```
This correctly checks `TLSRequired == TLSNotRequired` before overriding, so it does NOT clobber an explicit `TLSRequiredExceptHTTP` setting. This follows the safe pattern from Focus Area 9. No issue.

### Line 168-173: **QUESTION** — Severity: Low — `BroadcastHTTPPort` fallback silently fails if `httpListener` is nil
When `opts.BroadcastHTTPPort == 0` and `opts.HTTPAddress == ""`, `RealHTTPAddr()` returns an empty `*net.TCPAddr{}` (line 220). The type assertion `*net.TCPAddr` succeeds (`ok == true`) and sets `BroadcastHTTPPort = 0`, which is a no-op. This means if the operator disables HTTP but relies on `StatsdPrefix` with `%s`, the host key will use port 0. This is arguably correct behavior (don't use statsd prefix substitution without HTTP), but could be confusing.

### Line 389-414: **BUG** — Severity: High — `GetMetadata` reads `topicMap` without holding `n.RLock()` (Focus Area 2/11)
The `GetMetadata` method at line 389 iterates `n.topicMap` (line 393) without acquiring the NSQD-level read lock. This is a data race with `GetTopic` (line 504) and `DeleteExistingTopic` (line 570) which modify `topicMap` under `n.Lock()`. The caller `PersistMetadata` (line 424) does NOT hold the lock either — it only acquires it in the `Exit()` path (line 463) and `Notify()` path (line 590). However, in the `Notify` path, `n.Lock()` is acquired at line 590 before calling `PersistMetadata`, which in turn calls `GetMetadata`. So the lock IS held in the `Notify` path. In the `Exit` path, `n.Lock()` is acquired at line 463 before `PersistMetadata`. So both callers do hold the lock. **Retracted — callers always hold the lock.**

### Line 442-480: **BUG** — Severity: Medium — `Exit()` closes `exitChan` after closing topics, causing goroutines to miss shutdown signal (Focus Area 11)
The `Exit()` method at line 475 calls `close(n.exitChan)` AFTER closing all topics (line 469-471). The `queueScanLoop` (line 697), `lookupLoop`, and `statsdLoop` goroutines all select on `n.exitChan` to exit. But since topics are closed first (which may flush data and take time), these background goroutines continue running during topic shutdown. This is the intended ordering — topics should be closed before goroutines that process them are stopped. The `waitGroup.Wait()` at line 476 then ensures all goroutines finish. This is actually fine — the goroutines gracefully handle closed channels/topics.

### Line 442-480: **BUG** — Severity: High — `Exit()` does not close active HTTP/HTTPS connections (Focus Area 11)
Resource enumeration for `Exit()`:
1. **TCP listener** — closed at line 448 ✓
2. **Active TCP connections** — closed via `tcpServer.Close()` at line 452, which iterates `conns` sync.Map ✓
3. **HTTP listener** — closed at line 456 ✓
4. **HTTPS listener** — closed at line 460 ✓
5. **Active HTTP/HTTPS connections** — **NOT explicitly closed**. Closing the listener stops new connections but does NOT close existing in-flight HTTP connections. The `http.Server` used in `Main()` (line 275) is created via `http_api.Serve` which calls `http.Serve` — this does not provide a `Shutdown()` mechanism. Long-lived HTTP connections (e.g., keep-alive, long-polling `/stats` requests) will prevent `waitGroup.Wait()` from completing.
6. **Goroutines** — tracked via `waitGroup`, waited at line 476 ✓
7. **Backend stores** — closed via `topic.Close()` at line 470 ✓
8. **Dir lock** — released at line 477 ✓
9. **Context** — canceled at line 479 ✓

### Line 475-479: **QUESTION** — Severity: Medium — `ctxCancel()` called after `waitGroup.Wait()`, but `ctx` is not used by any waited goroutine
The context cancel at line 479 happens after all goroutines have already exited via `waitGroup.Wait()`. If any goroutine was using `n.ctx` for shutdown signaling, it would never see the cancellation. Currently `n.ctx` is only exposed via `Context()` (line 799) for external use, so this may be intentional — but it means `ctx` cannot be used as a shutdown signal for internal goroutines.

---

## nsqd/protocol_v2.go

### Line 203-218: **BUG** — Severity: High — `messagePump` creates tickers with potentially zero/negative duration, causing panic (Focus Area 9/12)
At line 217, `outputBufferTicker` is created with `client.OutputBufferTimeout`. At line 218, `heartbeatTicker` is created with `client.HeartbeatInterval`. The defaults are set in `newClientV2()`: `OutputBufferTimeout` defaults to `opts.OutputBufferTimeout` (250ms) and `HeartbeatInterval` defaults to `opts.ClientTimeout / 2` (30s). These are safe defaults. However, `messagePump` starts BEFORE `IDENTIFY` is processed (line 52-53). The `identifyEventChan` case at line 294 handles subsequent changes. Since defaults are positive, the initial tickers are safe. **No bug — defaults ensure positive values.**

### Line 298-308: **BUG** — Severity: Medium — `messagePump` replaces `outputBufferTicker` but does not handle zero `OutputBufferTimeout` (Focus Area 9)
At line 299, when an identify event is received with `OutputBufferTimeout > 0`, a new ticker is created. But if `OutputBufferTimeout == 0` (meaning "use default" per client_v2.go), the old ticker is stopped but a new one is never created — `outputBufferTicker` points to a stopped ticker whose channel will never fire. However, looking at the `Identify()` path in client_v2.go: when the client sends `output_buffer_timeout: 0`, `SetOutputBuffer` keeps the existing default value. The `identifyData.OutputBufferTimeout` sent to `messagePump` is the CLIENT'S value after processing — which retains the default. Let me check what `identifyEvent` actually contains...

The `identifyEvent` struct contains `OutputBufferTimeout: c.OutputBufferTimeout` (from client_v2.go line 289). Since `SetOutputBuffer` with timeout=0 leaves `c.OutputBufferTimeout` at its default (250ms), `identifyData.OutputBufferTimeout` will be > 0 in that case.

But if the client sends `output_buffer_timeout: -1` (disable), `SetOutputBuffer` sets `c.OutputBufferTimeout = 0`. Then `identifyData.OutputBufferTimeout == 0`, and at line 299 the condition `identifyData.OutputBufferTimeout > 0` is false. The `outputBufferTicker` is stopped (line 298) but no new ticker is created and no nil assignment occurs. The stopped ticker's channel `outputBufferTicker.C` will block forever in select — this is functionally correct (disabled = never fires). **Not a bug.**

### Line 299-301: **QUESTION** — Severity: Low — Stopped ticker channel behavior
When `outputBufferTicker.Stop()` is called at line 298 but `identifyData.OutputBufferTimeout <= 0`, the code relies on `outputBufferTicker.C` never firing again after `Stop()`. Per Go docs, `Stop` prevents the ticker from firing but does not close the channel. A stopped ticker's channel blocks forever on receive, which is the desired behavior. This is correct.

### Line 304-308: **BUG** — Severity: Low — When heartbeats are disabled via IDENTIFY, `heartbeatTicker` is stopped but not garbage-collected
At line 303, `heartbeatTicker.Stop()` is called. At line 304, `heartbeatChan = nil` correctly disables the select case. But the stopped `heartbeatTicker` object is never released — it's held by the `heartbeatTicker` local variable until `messagePump` exits (line 373 calls `heartbeatTicker.Stop()` again). This is a minor memory/resource concern but not a correctness issue.

### Line 619-668: **BUG** — Severity: Medium — `SUB` transitions from `stateInit` to `stateSubscribed`, bypassing `stateConnected` (Focus Area 3)
At line 619, `SUB` checks that the client is in `stateInit`. At line 668, it transitions directly to `stateSubscribed`. There is no intermediate `stateConnected` state. This means a client can `SUB` without ever calling `IDENTIFY`. While `IDENTIFY` is technically optional in the protocol (the code at line 169 allows IDENTIFY to be skipped with `enforceTLSPolicy` checked after), this means default configuration values are used. This is by design — the protocol spec allows SUB without IDENTIFY. **Not a bug.**

### Line 671: **QUESTION** — Severity: Medium — `SubEventChan` send could block if messagePump is not receiving (Focus Area 12)
At line 671, `client.SubEventChan <- channel` is an unbuffered or buffer-1 send. From client_v2.go, `SubEventChan` has buffer size 1. If `messagePump` has already exited (e.g., due to a write error), this send will block forever, causing the IOLoop goroutine to hang. However, `messagePump` always selects on `subEventChan` until it receives one event (line 291-293), and both `messagePump` exit and IOLoop exit are coordinated through `client.ExitChan`. If `messagePump` exits due to error, it goes to `exit:` label, but IOLoop is the one that closes `ExitChan` (line 116). So `messagePump` exits when `ExitChan` is closed, and `SubEventChan` send in IOLoop happens before `ExitChan` close. There's a potential deadlock: IOLoop blocks on `SubEventChan` send (line 671), `messagePump` is waiting at select which includes `subEventChan` case. If `messagePump` already processed the `subEventChan` and set it to nil (line 292-293), and the client somehow sends a second SUB... but SUB is rejected in `stateSubscribed` (line 619). So the send always has a receiver. **Not a bug.**

### Line 691-698: **QUESTION** — Severity: Low — `RDY` default count is 1 when no parameter is provided
At line 691, if `len(params) <= 1` (no count parameter), `count` defaults to `1`. The NSQ protocol spec says RDY requires a count parameter. Silently defaulting to 1 is lenient but could mask client bugs. This appears intentional.

### Line 700-706: **BUG** — Severity: Medium — `RDY` uses FatalClientErr for out-of-range count instead of clamping (Focus Area 10)
At line 701-705, when `count < 0 || count > MaxRdyCount`, the handler returns `FatalClientErr` which disconnects the client. The code comment at line 702-703 explains: "this needs to be a fatal error otherwise clients would have inconsistent state." This is intentional — unlike REQ timeout which can be clamped, RDY count affects client flow control state and clamping would cause the client and server to disagree on the ready count. **Intentional — not a bug.**

### Line 760-773: **Observation** — `REQ` correctly clamps timeout instead of disconnecting (Focus Area 10)
The REQ handler properly clamps out-of-range timeouts and logs a warning (lines 764-772), which is the correct pattern per Focus Area 10.

### Line 923-927: **BUG** — Severity: Medium — `DPUB` disconnects client for out-of-range defer timeout instead of clamping (Focus Area 10)
At line 923-927, when `timeoutDuration < 0 || timeoutDuration > MaxDeferTimeout`, the handler returns `FatalClientErr`. This disconnects the client for a recoverable validation error. Unlike RDY (where clamping would cause state inconsistency), a DPUB defer timeout could be safely clamped like REQ does (lines 760-773). A message deferred for `MaxDeferTimeout` instead of the requested value is better than dropping the connection. The REQ handler demonstrates the correct pattern already exists in the codebase.

### Line 1045-1050: **QUESTION** — Severity: Low — `readLen` casts uint32 to int32, allowing negative body sizes
At line 1050, `int32(binary.BigEndian.Uint32(tmp))` converts a uint32 to int32. Values > 2^31-1 become negative. All callers check for `bodyLen <= 0` which catches this. This is a deliberate pattern for detecting overflow.

---

## nsqd/protocol_v2_test.go

### Line 48-53: **QUESTION** — Severity: Low — `mustStartNSQD` starts `Main()` in goroutine without waiting for readiness
At line 48-53, `Main()` is started in a goroutine but there's no synchronization to ensure the TCP and HTTP listeners are fully ready before returning. The listeners are already bound in `New()` (lines 152-167 of nsqd.go), so `RealTCPAddr()` and `RealHTTPAddr()` return valid addresses immediately. `Main()` just starts `Accept()` loops. There could be a brief window where `Accept()` hasn't been called yet, but `net.Listen` queues incoming connections, so this is safe.

No correctness bugs found in the test file.

---

## nsqd/stats.go

No findings. The file correctly uses locks and atomic operations for all shared state access.

---

## nsqd/tcp.go

### Line 57-66: **BUG** — Severity: Medium — `tcpServer.Handle` calls `client.Close()` after `IOLoop` returns, double-closing the connection
At line 65, `client.Close()` is called after `prot.IOLoop(client)` returns. But `IOLoop` (protocol_v2.go line 116-119) already closes `client.ExitChan` and calls `client.Channel.RemoveClient()`. The actual TCP connection close depends on what `client.Close()` does. Looking at client_v2.go, `Close()` closes the underlying `net.Conn`. In `IOLoop`, when the read loop exits (e.g., EOF or error), it closes `ExitChan` but does NOT close the connection itself — that's left to `Handle`. So this is correct — `Handle` is responsible for closing the connection.

### Line 68-73: **QUESTION** — Severity: Medium — `tcpServer.Close()` closes connections but doesn't wait for IOLoop goroutines to finish
At line 68-73, `Close()` iterates connections and calls `Close()` on each. This will cause the `IOLoop` `ReadSlice` to return an error, breaking out of the read loop. But `Handle` is still running — it will call `conns.Delete` and `client.Close()` (again). The `Close()` on an already-closed connection returns an error that is silently ignored. The sync.Map `Range` during concurrent `Delete` is safe per Go docs. The real question is whether the `waitGroup` in NSQD waits for these `Handle` goroutines — yes, because `TCPServer` is wrapped in `waitGroup` (nsqd.go line 269-271), and `TCPServer` only returns after all `Handle` goroutines complete.

---

## nsqlookupd/lookup_protocol_v1.go

### Line 48: **QUESTION** — Severity: Low — Type assertion `err.(protocol.ChildErr)` panics if error doesn't implement ChildErr
At line 48, `err.(protocol.ChildErr)` is a non-checked type assertion. If `Exec` returns an error that doesn't implement `protocol.ChildErr`, this will panic. However, all errors returned by `Exec` and its callees use `protocol.NewFatalClientErr` or `protocol.NewClientErr`, which both implement `ChildErr`. Custom `error` values would panic here. The same pattern exists in nsqd/protocol_v2.go line 88. This is fragile but consistent.

### Line 207-211: **BUG** — Severity: Low — `IDENTIFY` uses `bodyLen` as int32, allowing negative-length allocation
At line 207-208, `bodyLen` is `int32`, read via `binary.Read`. A malicious client sending a negative int32 would cause `make([]byte, bodyLen)` at line 213 to panic (negative length). There's no check for `bodyLen <= 0` before the allocation, unlike nsqd's IDENTIFY handler which checks at line 397-399.

### Line 249-250: **QUESTION** — Severity: Low — `IDENTIFY` calls `log.Fatalf` on hostname error, crashing the entire process
At line 249-250, if `os.Hostname()` fails, the code calls `log.Fatalf` which terminates the entire nsqlookupd process. A single client's IDENTIFY shouldn't be able to crash the server. However, `os.Hostname()` essentially never fails on a properly configured system.

---

## nsqlookupd/lookup_protocol_v1_test.go

### Line 51-52: **BUG** — Severity: Low — Deferred `Exit()` may never run due to goroutine structure
At line 51, `prot.nsqlookupd.Exit()` is deferred inside the `testIOLoop` closure which runs in a goroutine. If the test exits (via the timeout path at line 59), the goroutine's defers may not execute, leaking the nsqlookupd resources. However, since `New()` doesn't call `Main()` in this test, there are no background goroutines or listeners to clean up (the TCP/HTTP listeners from `New()` are never served).

No other findings.

---

## nsqlookupd/nsqlookupd.go

### Line 86-99: **BUG** — Severity: Medium — `Exit()` does not close active HTTP connections (Focus Area 11)
Resource enumeration for `NSQLookupd.Exit()`:
1. **TCP listener** — closed at line 88 ✓
2. **Active TCP connections** — closed via `tcpServer.Close()` at line 92 ✓
3. **HTTP listener** — closed at line 96 ✓
4. **Active HTTP connections** — **NOT explicitly closed**. Same issue as nsqd — closing the HTTP listener stops new connections but existing keep-alive connections continue. These connections hold goroutines in `http.Serve`, which is tracked by `waitGroup`. The `waitGroup.Wait()` at line 98 will hang until these connections are closed by the remote end or timeout.
5. **Goroutines** — waited via `waitGroup` at line 98 ✓
6. **Registration DB** — no explicit cleanup needed (in-memory) ✓

---

## nsqlookupd/tcp.go

### Line 46-56: **Observation** — Same pattern as nsqd/tcp.go
Connection management follows the same pattern. `Handle` stores conn, runs IOLoop, then deletes and closes. `Close` iterates and closes all conns. Same analysis as nsqd/tcp.go applies.

No additional findings.

---

## Summary

### Findings by Severity

| Severity | Count | Type |
|----------|-------|------|
| Critical | 0 | — |
| High | 1 | BUG |
| Medium | 4 | 2 BUG, 2 QUESTION |
| Low | 3 | 1 BUG, 2 QUESTION |

### Findings Detail

| # | Type | File | Line | Severity | Description |
|---|------|------|------|----------|-------------|
| 1 | BUG | nsqd/nsqd.go | 442-480 | High | `Exit()` does not close active HTTP/HTTPS connections; only closes listeners. Long-lived HTTP connections prevent `waitGroup.Wait()` from completing, causing shutdown hang. |
| 2 | BUG | nsqd/protocol_v2.go | 923-927 | Medium | `DPUB` disconnects client via `FatalClientErr` for out-of-range defer timeout instead of clamping (as `REQ` does at lines 760-773). |
| 3 | BUG | nsqlookupd/lookup_protocol_v1.go | 207-213 | Low | `IDENTIFY` does not validate `bodyLen > 0` before `make([]byte, bodyLen)` — negative int32 causes panic. |
| 4 | BUG | nsqlookupd/nsqlookupd.go | 86-99 | Medium | `Exit()` does not close active HTTP connections; `waitGroup.Wait()` can hang on keep-alive connections. |
| 5 | QUESTION | nsqd/nsqd.go | 475-479 | Medium | `ctxCancel()` is called after `waitGroup.Wait()` — context is never used as internal shutdown signal. |
| 6 | QUESTION | nsqlookupd/lookup_protocol_v1.go | 48 | Low | Unchecked type assertion `err.(protocol.ChildErr)` panics if error doesn't implement interface. |
| 7 | QUESTION | nsqlookupd/lookup_protocol_v1.go | 249-250 | Low | `log.Fatalf` on `os.Hostname()` failure crashes entire process from client handler. |

### Files with No Findings
- `internal/protocol/protocol.go`
- `nsqd/stats.go`
- `nsqd/protocol_v2_test.go`
- `nsqlookupd/lookup_protocol_v1_test.go`
- `nsqlookupd/tcp.go`

### Overall Assessment: **NEEDS DISCUSSION**

The most significant finding is the missing HTTP connection cleanup in both `nsqd` and `nsqlookupd` Exit() paths (findings #1 and #4). Closing a `net.Listener` does NOT close already-accepted connections — the code needs to use `http.Server.Shutdown()` or track and close active HTTP connections. This can cause graceful shutdown to hang indefinitely.

The DPUB fatal-vs-clamp inconsistency (finding #2) is a design decision worth discussing — the codebase already implements the clamp pattern correctly in REQ, making the DPUB behavior inconsistent.

The nsqlookupd IDENTIFY negative body length (finding #3) is a crash bug reachable by any TCP client, though exploitation requires intentional malicious input.
