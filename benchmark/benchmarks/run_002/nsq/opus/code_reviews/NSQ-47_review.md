# NSQ-47 Code Review

## Files Reviewed
- `internal/protocol/protocol.go`
- `nsqd/nsqd.go`
- `nsqd/protocol_v2.go`
- `nsqd/protocol_v2_test.go`
- `nsqd/stats.go`
- `nsqd/tcp.go`
- `nsqlookupd/lookup_protocol_v1.go`
- `nsqlookupd/lookup_protocol_v1_test.go`
- `nsqlookupd/nsqlookupd.go`
- `nsqlookupd/tcp.go`

---

### nsqlookupd/lookup_protocol_v1.go

- **Line 250:** [BUG] `log.Fatalf("ERROR: unable to get hostname %s", err)` terminates the entire nsqlookupd process if `os.Hostname()` fails. This is inside the IDENTIFY command handler, which runs per-client. A transient hostname resolution failure or unusual OS state would crash the entire lookup service rather than just failing the single client request. Expected: return an error to the client. Actual: calls `os.Exit(1)` via `log.Fatalf`. Severity: **High** -- a single client connection can kill the server.

- **Line 48:** [QUESTION] `err.(protocol.ChildErr).Parent()` is a type assertion without an `ok` check. If any error returned from `Exec` does not implement `protocol.ChildErr`, this panics and crashes the client handler goroutine. Currently all `Exec` code paths return `protocol.ClientErr` or `protocol.FatalClientErr`, but this is fragile -- adding a new command that returns a bare `error` would cause a panic. Severity: **Low** (latent risk).

### nsqd/protocol_v2.go

- **Line 88:** [QUESTION] Same fragile type assertion pattern as `nsqlookupd/lookup_protocol_v1.go:48`. `err.(protocol.ChildErr).Parent()` will panic if any `Exec` handler returns a non-`ChildErr` error. Currently safe because all handlers wrap errors in `protocol.NewFatalClientErr` / `protocol.NewClientErr`, but a future handler returning a bare error would crash. Severity: **Low** (latent risk).

- **Line 619:** [QUESTION] `SUB` checks `client.State != stateInit`, meaning SUB is only valid from `stateInit`. The client state enum defines `stateConnected` (client_v2.go:23) but no command ever transitions a client to `stateConnected` -- IDENTIFY (line 380-523) checks for `stateInit` but never changes state. The client goes directly from `stateInit` to `stateSubscribed` (line 668), making `stateConnected` unused in the V2 protocol. This appears intentional (it is used by `lookup_peer.go`), but the skipped state is worth noting for protocol correctness. Severity: **Low**.

### nsqd/nsqd.go

- **Line 393:** [QUESTION] `GetMetadata` iterates `n.topicMap` without holding `n.RLock()`. The function is public. Within the reviewed files, all callers hold `n.Lock()` (Exit at line 463, Notify at line 590), but the function does not document this requirement or protect itself. If called from an HTTP handler (outside review scope) without the lock, this is a data race on the map. Severity: **Medium** -- depends on callers outside this review scope.

- **Line 338:** [QUESTION] `writeSyncFile` discards the error from `f.Close()`. After `f.Write` and `f.Sync()` succeed, `f.Close()` is called at line 338 but its return value is ignored. While `Sync()` should have flushed data to disk, some filesystems and NFS mounts may report final write errors only on `Close()`. This function is used for metadata persistence (`PersistMetadata` at line 429). Severity: **Low** -- unlikely in practice after successful `Sync()`.

- **Line 82:** [QUESTION] `cwd, _ := os.Getwd()` silently discards the error. If `Getwd` fails, `dataPath` becomes the empty string, and `dirlock.New("")` attempts to lock an empty path. The `dl.Lock()` at line 106 would likely fail with a confusing error message. Severity: **Low** -- `Getwd` rarely fails, and the dir lock provides a safety net.

### nsqd/tcp.go

- **Line 65:** [QUESTION] `client.Close()` is called after `IOLoop` returns, but `tcpServer.Close()` (line 68-73) also calls `Close()` on all stored connections during shutdown. If shutdown races with a client disconnecting, `Close()` may be called twice on the same client. Whether this causes issues depends on whether `clientV2.Close()` is idempotent. Severity: **Low** -- TCP `Close()` on an already-closed connection returns an error but does not panic.

### nsqlookupd/tcp.go

- **Line 55:** [QUESTION] Same double-close pattern as `nsqd/tcp.go:65`. `client.Close()` at line 55 after IOLoop, plus `tcpServer.Close()` at line 58-62 during shutdown, can both call `Close()` on the same `ClientV1` (which wraps `net.Conn`). Severity: **Low**.

### internal/protocol/protocol.go

- No bugs or correctness issues found. `SendResponse` and `SendFramedResponse` correctly account for bytes written. The Go `io.Writer` contract guarantees that partial writes return non-nil errors, so the byte counting in `SendFramedResponse` (lines 42-54) is correct.

### nsqd/stats.go

- No bugs or correctness issues found. Atomic loads are used correctly for concurrent counters (lines 38-39, 79-85). Lock acquisition order in `GetStats` (n.RLock -> t.RLock -> c.RLock) is consistent, avoiding deadlocks.

### nsqd/protocol_v2_test.go

- No bugs or correctness issues found. Tests cover basic V2 protocol operations, topology-aware consumption, client timeouts, heartbeats, TLS, compression, size limits, and output buffering.

### nsqlookupd/lookup_protocol_v1_test.go

- No bugs or correctness issues found. Tests verify IOLoop error handling for both write-success and write-failure scenarios.

### nsqlookupd/nsqlookupd.go

- No bugs or correctness issues found. Shutdown ordering in `Exit()` (lines 86-99) correctly closes listeners before waiting on goroutines.

---

## Summary

| Severity | Count |
|----------|-------|
| BUG (High) | 1 |
| QUESTION (Medium) | 1 |
| QUESTION (Low) | 6 |

**Files with no findings:** `internal/protocol/protocol.go`, `nsqd/stats.go`, `nsqd/protocol_v2_test.go`, `nsqlookupd/lookup_protocol_v1_test.go`, `nsqlookupd/nsqlookupd.go`

**Overall assessment: NEEDS DISCUSSION**

The `log.Fatalf` in `nsqlookupd/lookup_protocol_v1.go:250` is a real server-crash bug that should be fixed before shipping. The `GetMetadata` locking question needs verification of callers outside the reviewed files. The remaining findings are low-severity latent risks.
