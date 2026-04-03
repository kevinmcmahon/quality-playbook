# Code Review: nsqd/nsqd.go and nsqd/tcp.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Focus Areas:** 9 (Configuration Parameter Validation), 10 (Input Validation Failure Modes), 11 (Exit Path Resource Completeness), 12 (Go Channel Lifecycle in Select Statements)

---

## nsqd/nsqd.go

### Finding 1
- **Line 743-750:** [BUG] **Severity: Medium (Security)**
  `buildTLSConfig` switch on `opts.TLSClientAuthPolicy` has a `default` case that silently sets `tlsClientAuthPolicy = tls.NoClientCert` for any unrecognized value. There is no validation of the policy string in `New()` — line 119 only checks if it's non-empty. A typo such as `--tls-client-auth-policy=reqiure` (instead of `"require"`) causes: (a) line 119 sets `opts.TLSRequired = TLSRequired` because policy is non-empty, (b) line 749 falls to `default`, setting `NoClientCert`. Result: TLS is required but client certificate verification is silently disabled. The `New()` function should validate the policy string against `{"", "require", "require-verify"}` and return an error for unrecognized values.

### Finding 2
- **Line 393:** [QUESTION] **Severity: Medium**
  `GetMetadata` is an exported method that iterates `n.topicMap` (line 393: `for _, topic := range n.topicMap`) without acquiring `n.RLock()`. Current callers (`PersistMetadata` via `Exit()` at line 464 and `Notify()` at line 591) hold `n.Lock()` externally. However, as an exported method with no internal synchronization, any future caller (or external package) that calls `GetMetadata` without holding the lock will cause a data race. The method either needs an internal `n.RLock()`/`n.RUnlock()`, or should be unexported, or should be documented as requiring an external lock.

### Finding 3
- **Lines 447-460 vs 455-460:** [QUESTION] **Severity: Medium**
  Exit() resource completeness for HTTP/HTTPS active connections. TCP active connections are explicitly closed via `n.tcpServer.Close()` (line 451-452), which iterates `sync.Map` and calls `Close()` on each client. However, HTTP and HTTPS only close their **listeners** (lines 455, 459). The `http.Server` created inside `http_api.Serve()` (in `internal/http_api/http_server.go:25`) is a local variable — there is no stored reference to call `server.Close()` or `server.Shutdown()` to terminate active HTTP connections. While `server.Serve()` returns when the listener closes, in-progress HTTP handler goroutines continue running untracked. During shutdown, if an HTTP handler blocks (e.g., waiting on a topic operation that's already closed), this could delay or hang `waitGroup.Wait()` at line 476 depending on handler behavior.

  Resource enumeration for `Exit()`:
  | Resource | Cleanup | Line |
  |---|---|---|
  | tcpListener | Close() | 448 |
  | TCP connections | tcpServer.Close() iterates and closes each | 451-452 |
  | httpListener | Close() | 455 |
  | httpsListener | Close() | 459 |
  | **HTTP active connections** | **NOT CLOSED — only listener closed** | **missing** |
  | **HTTPS active connections** | **NOT CLOSED — only listener closed** | **missing** |
  | Metadata | PersistMetadata() | 464 |
  | Topics (and their channels, disk queues) | topic.Close() | 469-471 |
  | exitChan | close() signals background goroutines | 475 |
  | Goroutines | waitGroup.Wait() | 476 |
  | DirLock | dl.Unlock() | 477 |
  | Context | ctxCancel() | 479 |

### Finding 4
- **Line 479:** [BUG] **Severity: Low**
  `n.ctxCancel()` is called **after** `n.waitGroup.Wait()` (line 476). The docstring at line 797 says "Context returns a context that will be canceled when nsqd initiates the shutdown." But the context is actually canceled after all goroutines have already exited — it signals shutdown **completion**, not **initiation**. Any external code selecting on `n.ctx.Done()` to begin its own graceful shutdown will not receive the signal until everything inside nsqd is already torn down. The `ctxCancel()` call should be moved before or alongside `close(n.exitChan)` at line 475 to match the documented contract.

### Finding 5
- **Line 82:** [BUG] **Severity: Low**
  `os.Getwd()` error is silently discarded: `cwd, _ := os.Getwd()`. If `Getwd` fails (e.g., working directory deleted), `cwd` is `""`, making `dataPath = ""`. This propagates to `dirlock.New("")` at line 96, `newMetadataFile` returning just `"nsqd.dat"` (relative path), and disk queue paths being relative. The system would appear to start successfully but store data in unexpected locations. Expected: return an error from `New()` if `Getwd` fails when `DataPath` is empty.

### Finding 6
- **Line 186:** [QUESTION] **Severity: Low**
  When `opts.HTTPAddress` is empty (no HTTP listener), `n.httpListener` is nil, so `RealHTTPAddr()` returns `&net.TCPAddr{}` with Port=0. At line 168-172, `BroadcastHTTPPort` is set to 0 via this path. Then at line 183, `StatsdPrefix` incorporates `fmt.Sprint(opts.BroadcastHTTPPort)` = `"0"`, producing a statsd key with port 0 embedded. This may produce confusing or colliding statsd metrics when HTTP is intentionally disabled but statsd is enabled.

---

## nsqd/tcp.go

### Finding 7
- **Lines 65 + 69-72:** [QUESTION] **Severity: Low**
  During shutdown, `client.Close()` (which calls the embedded `net.Conn.Close()`) may be called twice: once by `tcpServer.Close()` (line 69-72, iterating the `conns` map), and again by `Handle()` at line 65 after `IOLoop` returns. The sequence: `tcpServer.Close()` closes the conn -> `IOLoop`'s `ReadSlice` gets an error -> `IOLoop` exits -> `Handle` calls `client.Close()` again. While `net.Conn.Close()` on an already-closed connection returns an error rather than panicking, the double-close is unguarded. If `protocol.Client.Close()` is ever replaced with a non-idempotent implementation, this becomes a bug. Consider checking `conns.LoadAndDelete` in `Handle` before calling `Close`, or documenting the idempotency requirement.

### Finding 8
- **Line 57:** [QUESTION] **Severity: Low**
  `p.conns.Store(conn.RemoteAddr(), client)` uses `conn.RemoteAddr()` (a `net.Addr` interface value) as the `sync.Map` key. Interface keys in Go maps use `==` which compares both type and value. For `*net.TCPAddr`, this is pointer equality. This works because the same `conn` object returns the same pointer from `RemoteAddr()` each time. However, this is an implicit contract with the `net` package — if a custom `net.Conn` wrapper (e.g., TLS upgrade, proxy protocol) returns a different pointer from `RemoteAddr()`, the `Delete` at line 64 would fail to remove the entry, causing a leak in the `conns` map. This is safe with stdlib `net.Conn` but fragile under wrapping.

---

## Summary

| Severity | Count |
|---|---|
| Critical | 0 |
| High | 0 |
| Medium | 3 |
| Low | 5 |
| **Total** | **8** |

**Findings by type:**
- BUG: 3 (Findings 1, 4, 5)
- QUESTION: 5 (Findings 2, 3, 6, 7, 8)

**Assessment: NEEDS DISCUSSION**

The most actionable finding is Finding 1 (TLSClientAuthPolicy silent fallback to NoClientCert), which is a security gap that can be triggered by operator typos. Finding 3 (HTTP active connections not closed in Exit) should be evaluated for whether HTTP handler goroutines can block shutdown in practice. The remaining findings are low-severity correctness and robustness concerns.
