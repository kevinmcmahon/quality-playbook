# Code Review: nsqlookupd/nsqlookupd.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** nsqlookupd/nsqlookupd.go (102 lines)
**Commit:** 9ea5071

---

### nsqlookupd/nsqlookupd.go

- **Line 45:** [BUG] **Severity: Medium.** Copy-paste error in HTTP listener failure message. When `net.Listen` for `opts.HTTPAddress` fails, the error message formats with `opts.TCPAddress` instead of `opts.HTTPAddress`. Expected: operator sees the HTTP address that failed to bind. Actual: operator sees the TCP address, making it appear that the TCP listener failed twice. This misdirects debugging when there is a port conflict on the HTTP port.
  ```go
  // Line 45 (current — wrong):
  return nil, fmt.Errorf("listen (%s) failed - %s", opts.TCPAddress, err)
  // Should be:
  return nil, fmt.Errorf("listen (%s) failed - %s", opts.HTTPAddress, err)
  ```

- **Line 44-46:** [BUG] **Severity: Medium.** TCP listener resource leak on HTTP listen failure. When the HTTP listener fails to bind (line 43-44), `New()` returns an error but never closes the already-opened TCP listener from line 39. The TCP listener holds a file descriptor and binds a port that will remain occupied until process exit. If the caller retries `New()` with different HTTP options but the same TCP address, the retry will also fail because the TCP port is still held by the leaked listener from the first attempt.

- **Line 88-101:** [QUESTION] **Severity: Low.** HTTP active connections are not gracefully drained during `Exit()`. The `httpListener.Close()` at line 98 stops accepting new connections, but `http_api.Serve()` uses bare `http.Server.Serve()` which returns immediately when the listener closes — it does not wait for in-flight HTTP requests to complete. Unlike the TCP side (where `tcpServer.CloseAll()` explicitly closes active connections and `protocol.TCPServer` waits via its internal WaitGroup), there is no equivalent mechanism for HTTP. In practice this is low severity because nsqlookupd HTTP requests are short-lived lookups, but any request in progress during `Exit()` could receive a connection reset rather than a complete response.

- **Line 56-64:** [QUESTION] **Severity: Low.** Second server error is silently dropped. The `exitFunc` uses `sync.Once` so only the first server goroutine to fail sends its error to `exitCh`; the second goroutine's error is discarded. If both TCP and HTTP servers fail during startup (e.g., both ports are in use), `Main()` returns only one error. The operator may fix one port conflict only to discover the second on the next startup attempt. This is arguably acceptable since startup failures are immediately retriable, but it differs from the pattern where all errors are aggregated.

- **Line 26-48:** [QUESTION] **Severity: Low.** No validation of `Options` in `New()`. Unlike `nsqd.New()` which validates configuration parameters, `nsqlookupd.New()` performs no validation on `opts`. A zero value for `InactiveProducerTimeout` would cause `Producers.FilterByActive()` (in `registration_db.go`) to filter out *all* producers since `now.Sub(lastUpdate) > 0` is always true — making every `/lookup` response return an empty producer list. Similarly, a zero `TombstoneLifetime` makes tombstones expire instantly, rendering the tombstone feature ineffective. While defaults from `NewOptions()` are safe, there is no guard against programmatic or flag-based misconfiguration.

---

### Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High     | 0 |
| Medium   | 2 |
| Low      | 3 |

- **BUGs:** 2 (wrong address in error message, TCP listener leak)
- **QUESTIONs:** 3 (HTTP connection draining, silent error drop, missing option validation)

**Overall assessment:** **SHIP IT** — The two medium-severity bugs are real but localized: one produces a misleading error message and the other leaks a listener only on a startup failure path. Neither affects runtime correctness of a successfully started nsqlookupd instance. The questions are defensive-coding concerns worth discussing but not blocking.
