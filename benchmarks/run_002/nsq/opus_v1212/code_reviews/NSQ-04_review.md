# NSQ-04 Code Review: nsqd/nsqd.go and nsqd/tcp.go

## nsqd/nsqd.go

- **Line 82:** [BUG] **Severity: Medium.** `os.Getwd()` error is silently discarded (`cwd, _ := os.Getwd()`). If `Getwd` fails, `cwd` is `""`, so `dataPath` becomes `""`. This propagates to `dirlock.New("")` at line 95, which would attempt to lock an empty path. The `dl.Lock()` at line 106 may succeed or fail unpredictably depending on the dirlock implementation, and metadata would be written to the wrong location. Expected: return an error if `Getwd` fails. Actual: proceeds with empty data path.

- **Line 119-121:** [QUESTION] **Severity: Medium.** When `TLSClientAuthPolicy != ""` and `TLSRequired == TLSNotRequired`, the code forces `opts.TLSRequired = TLSRequired`. This silently overrides an operator who explicitly set `TLSNotRequired` (the zero value). There's no way to distinguish "user didn't set TLSRequired" from "user explicitly set TLSNotRequired", so the override is unavoidable. However, combined with the `buildTLSConfig` default case (line 748-749), a typo in `TLSClientAuthPolicy` (e.g., `"verify"` instead of `"require-verify"`) would (a) force TLS required, and (b) set `NoClientCert` via the default case — silently resulting in TLS-required-but-no-client-auth, which is likely not what the operator intended. There is no validation of `TLSClientAuthPolicy` against an allowed-value set.

- **Line 152-166:** [BUG] **Severity: Medium.** Resource leak on partial construction failure in `New()`. If `net.Listen` for `HTTPAddress` fails at line 158, the already-opened `tcpListener` (line 152) is not closed. If `tls.Listen` for `HTTPSAddress` fails at line 163, both `tcpListener` and `httpListener` are leaked. Additionally, the `dirlock` acquired at line 106 is never released on any failure path after that point (lines 111, 115, 123, 127, 129, 138, 143, 153, 158, 163). Expected: all previously acquired resources are cleaned up on error. Actual: listeners and dirlock are leaked.

- **Line 186:** [QUESTION] **Severity: Low.** `prefixWithHost[len(prefixWithHost)-1]` indexes the last byte without checking if `prefixWithHost` is empty. The outer check at line 182 ensures `opts.StatsdPrefix != ""`, and `strings.Replace` with a non-empty input shouldn't produce an empty string (since `%s` replacement produces at minimum the non-`%s` portions). In practice this is safe because `StatsdPrefix` typically contains literal characters beyond `%s`, but if `StatsdPrefix` were exactly `"%s"` and `statsdHostKey` returned `""`, `prefixWithHost` would be `""` and this would panic. `statsd.HostKey` likely never returns empty given a `host:port` input, so this is very unlikely.

- **Line 389-414:** [BUG] **Severity: Medium.** `GetMetadata` is an exported method that iterates `n.topicMap` (line 393) without acquiring `n.RLock()`. It does acquire per-topic locks (line 401) for channel iteration, but the `topicMap` iteration itself is unprotected. Currently all internal call sites (`PersistMetadata` at line 423, called from `Exit` and `Notify`) hold `n.Lock()`, so this is safe in practice. However, as an exported method, any external caller (e.g., an HTTP handler or test) that calls `GetMetadata` without holding the lock would trigger a data race on the map. Expected: `GetMetadata` should be self-protecting or documented as requiring the caller to hold the lock.

- **Line 442-479 (Exit):** [QUESTION] **Severity: Low.** Resource enumeration for `Exit()`:
  1. `tcpListener` — closed at line 448
  2. `tcpServer` (active TCP connections) — closed at line 452
  3. `httpListener` — closed at line 456
  4. `httpsListener` — closed at line 460
  5. Topics (and their channels) — closed at lines 469-471
  6. Metadata — persisted at line 464
  7. `exitChan` — closed at line 475
  8. `waitGroup` — waited at line 476
  9. `dirlock` — unlocked at line 477
  10. Context — cancelled at line 479
  11. `notifyChan` — NOT closed (but goroutines select on `exitChan`, so they drain)
  12. `optsNotificationChan` — NOT closed (but `lookupLoop` selects on `exitChan`)
  13. Tickers (`workTicker`, `refreshTicker`) — stopped inside `queueScanLoop` after exit signal

  All resource types appear accounted for. The ordering (listeners first, then topics flush, then exitChan signals background goroutines, then wait, then dirlock release) is correct. Context cancellation at line 479 happens after `waitGroup.Wait()`, meaning goroutines using `n.ctx` won't see cancellation until after they've already exited via `exitChan`. This is intentional — `ctx` is for external consumers per the comment at line 797-799.

- **Line 475-476 vs. 469-471:** [QUESTION] **Severity: Medium.** `close(n.exitChan)` at line 475 happens AFTER topics are closed at lines 469-471. `Topic.Close()` calls `topic.exit(false)` which closes the topic's `exitChan` and waits for its `messagePump` to exit. The `Notify` goroutines spawned at line 581 select on `n.exitChan`. If a `Notify` goroutine is spawned during topic close (e.g., by a channel close within topic close), it could block trying to send on `n.notifyChan` because `n.exitChan` hasn't been closed yet and `lookupLoop` (the receiver of `notifyChan`) may be blocked in its own select. This could cause `topic.Close()` to hang waiting for the `Notify` goroutine registered in `n.waitGroup`. However, topic/channel Close (not Delete) passes `persist: false` to Notify, so the goroutine would send to `notifyChan` (or exit via `exitChan`), and `lookupLoop` is still running at this point. This is likely safe but the ordering is subtle.

- **Line 706-719:** [BUG] **Severity: Medium.** `queueScanLoop` dirty-percentage loop (`goto loop` at line 719) re-enters the work dispatch at `loop:` (line 706) without re-checking `exitChan`. If the dirty percentage remains above `QueueScanDirtyPercent` persistently, this inner loop never yields to the outer `select` that checks `exitChan`. During shutdown, `close(n.exitChan)` at line 475 fires, but the loop is dispatching work via `workCh` (line 708) and reading responses via `responseCh` (line 713). Workers are still running (they haven't received close signal — `closeCh` is only closed at line 725, after the exit label). So the loop continues executing. It will eventually terminate when topics/channels are closed (making channels return not-dirty), but there is a window where shutdown is delayed by the dirty loop not checking `exitChan`. Expected: check `exitChan` before each `goto loop` iteration. Actual: only checked in the outer `for/select`.

- **Line 576-598 (Notify):** [QUESTION] **Severity: Low.** Each call to `Notify` spawns a new goroutine via `n.waitGroup.Wrap` that blocks trying to send on the unbuffered `notifyChan` (capacity 0, line 93). If topic/channel creation is rapid, many goroutines accumulate waiting to send. They are bounded by the number of topic/channel operations and will exit on shutdown via `exitChan`, so this is not a leak, but under heavy topic/channel churn it could cause significant goroutine buildup. This appears to be a deliberate design choice (see issue #123 reference at line 583).

- **Line 730-750 (buildTLSConfig):** [BUG] **Severity: High.** The `default` case in the `TLSClientAuthPolicy` switch (line 748-749) silently accepts any unrecognized string value and sets `tls.NoClientCert`. Combined with line 119-121, an unrecognized policy value (e.g., a typo like `"required"` instead of `"require"`, or `"verify"` instead of `"require-verify"`) results in: (a) TLS being forced as required (line 120), but (b) no client certificate verification (`NoClientCert`). This silently downgrades security. Expected: unrecognized `TLSClientAuthPolicy` values should be rejected with an error in `New()`. Actual: silently accepted and treated as no-client-cert.

## nsqd/tcp.go

- **Line 57:** [QUESTION] **Severity: Low.** `p.conns.Store(conn.RemoteAddr(), client)` uses `conn.RemoteAddr()` (a `net.Addr` interface value) as the sync.Map key. The `Delete` at line 64 uses the same `conn.RemoteAddr()` call. For TCP connections, `RemoteAddr()` returns a `*net.TCPAddr` which is compared by pointer identity in sync.Map (since `net.Addr` is an interface). If `RemoteAddr()` returns a new `*net.TCPAddr` allocation on each call (implementation-dependent), the `Delete` would fail to find the entry. In the standard library `net.TCPConn`, `RemoteAddr()` returns the same cached pointer, so this works. But it's relying on an implementation detail. If a TLS-wrapped connection or other middleware changes this behavior, the map entry would leak.

- **Line 64-65:** [QUESTION] **Severity: Low.** The ordering is `p.conns.Delete(conn.RemoteAddr())` then `client.Close()`. During shutdown, `tcpServer.Close()` (line 68-73) iterates `p.conns` and calls `Close()` on each client. There is a race window where `Handle` has deleted the client from `conns` (line 64) but hasn't called `Close()` yet (line 65), and `tcpServer.Close()` runs and doesn't see this client. The client is still closed by line 65, so there is no resource leak. However, `client.Close()` could be called twice — once by `tcpServer.Close()` (if it runs before the delete) and once by `Handle` at line 65. Whether double-close is safe depends on the `clientV2` implementation. The `clientV2.Close` method is not visible in the reviewed files, so this cannot be fully verified from these two files alone.

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High     | 1 |
| Medium   | 4 |
| Low      | 3 |
| QUESTION | 5 |

**High severity:**
- `buildTLSConfig` silently accepts unrecognized `TLSClientAuthPolicy` values, downgrading security

**Medium severity:**
- `os.Getwd()` error silently ignored in `New()` constructor
- Resource leak (listeners, dirlock) on partial construction failure in `New()`
- `GetMetadata` iterates `topicMap` without holding lock (exported method)
- `queueScanLoop` dirty loop doesn't check `exitChan`, delaying shutdown

**Overall assessment: FIX FIRST** — The `TLSClientAuthPolicy` silent-accept bug (High) could cause a security misconfiguration in production. The resource leak on `New()` failure and the shutdown delay in `queueScanLoop` are medium-severity correctness issues.
