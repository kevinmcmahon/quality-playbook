# NSQ-22 Code Review: TCP Server, Lookup Protocol Test, nsqlookupd, TCP Handler

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Files:**
- `internal/protocol/tcp_server.go`
- `nsqlookupd/lookup_protocol_v1_test.go`
- `nsqlookupd/nsqlookupd.go`
- `nsqlookupd/tcp.go`

---

## internal/protocol/tcp_server.go

- **Line 49:** **QUESTION** (Low) — The log message `"TCP: closing %s"` is emitted *after* `wg.Wait()` completes, meaning it logs only after all client handler goroutines have finished. This means the message is logged after all connections are truly closed, but the message text says "closing" rather than "closed". This is cosmetic but could be misleading in debug scenarios — the listener was already closed (at line 33-36 break path) well before this log line executes. Not a bug, just noting for clarity.

No bugs found in this file. The `Temporary()` deprecation workaround at line 27 is correct and documented. The `net.ErrClosed` check at line 33 properly handles listener closure. The `wg` usage is correct.

---

## nsqlookupd/lookup_protocol_v1_test.go

- **Line 51:** **BUG** (Medium) — `defer prot.nsqlookupd.Exit()` is inside the goroutine `testIOLoop` but placed *after* the blocking send to `errChan`. This means `Exit()` is deferred after `IOLoop` returns and `errChan` is sent to, but the defer runs when the goroutine function returns. The real issue: if `IOLoop` blocks forever (the timeout path at line 59-61), the test exits without ever calling `Exit()`, and the `nsqlookupd` instance (with its TCP and HTTP listeners from `New()` at line 41) is leaked. The listeners opened at `New()` bind to `:0` ports and are never closed in the timeout case. Additionally, `Exit()` closes `tcpListener` which would cause `IOLoop` to unblock — but since `Main()` was never called, there is no active `Accept()` loop, so the listeners are simply leaked.

- **Line 41-45:** **QUESTION** (Low) — `nsqlookupd` is created via `New(opts)` which calls `net.Listen` twice (TCP and HTTP listeners at `nsqlookupd.go:40-47`), but `Main()` is never called. The test manually sets `nsqlookupd.tcpServer` at line 45 and calls `prot.IOLoop` directly. The opened `tcpListener` and `httpListener` are never used and never closed (except in the non-timeout path via the deferred `Exit()`). This leaks OS file descriptors in the timeout path.

---

## nsqlookupd/nsqlookupd.go

- **Line 54-76:** **BUG** (Medium) — In `Main()`, if the first goroutine (TCP server, line 66-68) calls `exitFunc` and sends an error on `exitCh`, then `Main()` receives it at line 74 and returns. However, the second goroutine (HTTP server, line 70-72) is still running. `Main()` returns without closing either listener or waiting for the goroutines. The caller must call `Exit()` after `Main()` returns to actually shut down. If the caller does not call `Exit()`, both goroutines and listeners leak. This is a design contract, but it means **`Main()` does not clean up after itself on error** — it relies entirely on the caller calling `Exit()`.

- **Line 57-63:** **QUESTION** (Low) — The `exitFunc` uses `sync.Once` to ensure only one error is sent to `exitCh`. If the TCP server exits with an error and the HTTP server also exits with an error, the second error is silently dropped (line 58-63). This is likely intentional (only the first failure matters), but the second error is permanently lost with no logging.

- **Line 86-98:** **QUESTION** (Medium) — In `Exit()`, `tcpListener.Close()` at line 88 will cause the `TCPServer()` accept loop to break (returning from `protocol.TCPServer`). Then `tcpServer.Close()` at line 92 iterates over `conns` and closes each client. But `tcpServer.Close()` and the `Handle()` goroutines race: `Handle()` at `tcp.go:54` calls `p.conns.Delete()` then `client.Close()`, while `tcpServer.Close()` at `tcp.go:59-62` iterates and calls `v.(protocol.Client).Close()`. This means `Close()` could be called twice on the same client — once from `tcpServer.Close()` ranging over `conns` before the `Handle()` goroutine deletes it, and once from `Handle()` at `tcp.go:56`. Whether this is safe depends on whether `ClientV1.Close()` (which is `net.Conn.Close()`) is idempotent. For TCP connections, calling `Close()` twice returns an error but doesn't panic, so this is likely safe but wasteful.

---

## nsqlookupd/tcp.go

- **Line 47:** **QUESTION** (Medium) — `p.conns.Store(conn.RemoteAddr(), client)` uses `conn.RemoteAddr()` as the map key. `RemoteAddr()` returns a `net.Addr` interface. For TCP connections, this is a `*net.TCPAddr` (a pointer). Two different `net.Addr` values representing the same address will be different pointer values, so `sync.Map` will use pointer identity, not address string equality. This is actually fine for the `Store`/`Delete` pattern within a single `Handle()` call (same pointer), but `tcpServer.Close()` at line 59 iterates with `Range`, which works regardless. However, if `RemoteAddr()` returns a *new* pointer on each call (implementation-dependent), then `Delete` at line 54 could fail to find the entry stored at line 47. In practice, Go's `net.TCPConn.RemoteAddr()` caches the address, so the same pointer is returned each time. This is safe but fragile — it depends on an undocumented implementation detail.

- **Line 54-56:** **BUG** (Low) — `p.conns.Delete(conn.RemoteAddr())` at line 54 removes the entry, then `client.Close()` at line 56 closes the connection. But `tcpServer.Close()` (line 58-62) may be running concurrently during shutdown. The sequence could be: (1) `tcpServer.Close()` ranges and loads the client from `conns`, (2) `Handle()` deletes the entry and calls `client.Close()`, (3) `tcpServer.Close()` calls `Close()` on the already-closed client. As noted above, double-close on `net.Conn` is safe (returns error, no panic), but this is a race condition on the logical level. The `sync.Map` protects the map operations, but not the close lifecycle.

---

## Summary

| Severity | Count |
|----------|-------|
| BUG (Medium) | 2 |
| BUG (Low) | 1 |
| QUESTION (Medium) | 2 |
| QUESTION (Low) | 3 |

### Bugs

1. **`lookup_protocol_v1_test.go:51`** — Deferred `Exit()` after channel send means listeners leak on test timeout.
2. **`nsqlookupd.go:54-76`** — `Main()` returns on first goroutine error without shutting down the other goroutine or closing listeners; relies on caller to call `Exit()`.
3. **`tcp.go:54-56`** — Double-close race between `Handle()` cleanup and `tcpServer.Close()` during shutdown (benign for `net.Conn` but logically racy).

### Files with no actionable bugs
- `internal/protocol/tcp_server.go` — Clean, correct implementation.

### Overall Assessment
**NEEDS DISCUSSION** — The `Main()` error-exit contract (Bug #2) is the most significant finding: if callers don't reliably call `Exit()` after `Main()` returns an error, goroutines and listeners leak. The test file (Bug #1) demonstrates this exact pattern in a minor way. The double-close race (Bug #3) is benign for TCP but indicates a missing lifecycle coordination pattern that could become problematic if `Close()` gains side effects.
