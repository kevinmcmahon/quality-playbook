# NSQ-24 Code Review: nsqlookupd Core Files

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Files reviewed:**
- `apps/nsqlookupd/main.go` (entry point; `apps/nsqlookupd/nsqlookupd.go` does not exist)
- `nsqlookupd/nsqlookupd.go`

**Supporting files read for context:**
- `nsqlookupd/registration_db.go`
- `nsqlookupd/lookup_protocol_v1.go`
- `nsqlookupd/tcp.go`
- `nsqlookupd/client_v1.go`
- `nsqlookupd/options.go`
- `nsqlookupd/http.go` (lines 178-204)
- `internal/lg/lg.go` (lines 60-87)

---

### apps/nsqlookupd/main.go

- **Line 84:** BUG (Severity: Medium). `logFatal("failed to instantiate nsqlookupd", err)` — the format string has no format verb (`%s` or `%v`), so `err` is passed as an extra argument to `fmt.Sprintf` via `lg.Logf`. The error value will not be printed; instead Go will append `%!(EXTRA ...)` to the output. The operator sees `"failed to instantiate nsqlookupd%!(EXTRA *fmt.wrapError=...)"` instead of the actual error. Should be `logFatal("failed to instantiate nsqlookupd - %s", err)`.

### nsqlookupd/nsqlookupd.go

- **Line 44-46:** BUG (Severity: Low). In `New()`, if `net.Listen` for `HTTPAddress` (line 44) fails, the function returns an error but never closes the already-opened `tcpListener` (line 40). This leaks a file descriptor and leaves a port bound. The TCP listener should be closed in the error path before returning.

### nsqlookupd/registration_db.go

- **Lines 48-55:** BUG (Severity: Medium). `Producer.Tombstone()` writes `tombstoned` (bool) and `tombstonedAt` (time.Time) without synchronization. `Producer.IsTombstoned()` reads the same fields without synchronization. These methods are called from different goroutines: `Tombstone()` is called from HTTP handler `doTombstoneTopicProducer` (http.go:199) on a `*Producer` pointer obtained after the `RegistrationDB.RLock` has already been released by `FindProducers`. `IsTombstoned()` is called from `FilterByActive` (line 219) on the same `*Producer` pointers, also after the DB lock is released. This is a data race: concurrent unsynchronized read+write on `tombstoned` (bool) and `tombstonedAt` (time.Time struct — 24 bytes, not atomically writable). Detectable with `go test -race`.

### nsqlookupd/lookup_protocol_v1.go

- **Line 250:** QUESTION (Severity: Medium). In `IDENTIFY()`, if `os.Hostname()` fails, `log.Fatalf` is called, which invokes `os.Exit(1)` and terminates the entire nsqlookupd process from within a per-client request handler. This bypasses `Exit()` cleanup (no metadata flush, no graceful connection teardown, no `waitGroup.Wait()`). While `os.Hostname()` rarely fails in practice, a hard crash from a request handler is unexpected — returning an error to the client would be safer. Flagged as QUESTION because `os.Hostname()` failure may be considered unrecoverable by design.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (Medium) | 2 |
| BUG (Low) | 1 |
| QUESTION (Medium) | 1 |
| **Total** | **4** |

**Files with no findings:** `nsqlookupd/nsqlookupd.go` has only the minor listener leak; `apps/nsqlookupd/options.go`, `nsqlookupd/tcp.go`, `nsqlookupd/client_v1.go`, `nsqlookupd/options.go`, `nsqlookupd/logger.go` — no findings.

**Overall assessment:** NEEDS DISCUSSION — The tombstone data race (registration_db.go:48-55) is the most significant finding as it affects a production code path (HTTP tombstone endpoint concurrent with lookup queries). The missing format verb in main.go:84 degrades operator experience during a critical failure. The listener leak is low severity but trivially fixable.
