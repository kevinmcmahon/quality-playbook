# NSQ-21 Code Review: nsqlookupd Registration Subsystem

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Files reviewed:**
- `nsqlookupd/registration_db.go`
- `nsqlookupd/registration_db_test.go`
- `nsqlookupd/lookup_protocol_v1.go`
- `nsqlookupd/http.go`

**Focus Area:** #7 — nsqlookupd Registration Consistency

---

## nsqlookupd/registration_db.go

- **Lines 48-51:** BUG (Medium). `Producer.Tombstone()` writes `tombstoned` (bool) and `tombstonedAt` (time.Time) without any synchronization (no lock, no atomic). These fields are read concurrently by `IsTombstoned()` (line 53-55), which is called from `FilterByActive()` (line 219) — itself called from HTTP handlers running in separate goroutines. The write path is `doTombstoneTopicProducer` → `Tombstone()` (http.go line 199), which runs after `FindProducers` has released the DB lock. This is a data race. The `time.Time` struct is multi-word, making torn reads a realistic concern on some architectures. The Go race detector would flag this.

- **Lines 53-55:** BUG (Medium). `Producer.IsTombstoned()` reads `tombstoned` and `tombstonedAt` without synchronization. This is the read side of the race described above. Called from `FilterByActive()` (line 219) and `doNodes` (http.go line 285) concurrently with `Tombstone()` writes.

## nsqlookupd/http.go

- **Lines 195-201:** QUESTION (Low). `doTombstoneTopicProducer` calls `FindProducers` which returns `[]*Producer` pointers and releases the DB lock. Then it iterates and calls `p.Tombstone()` (line 199) outside any lock. If a concurrent `RemoveProducer` removes this producer from the DB between the `FindProducers` return and the `Tombstone()` call, the tombstone is set on a producer that is no longer in the registration map, making the tombstone silently ineffective. Additionally, if the topic doesn't exist or the node doesn't match any producer, the handler returns HTTP 200 with no error — silent success for a no-op.

- **Line 329:** BUG (Medium). `doDebug` reads `p.tombstoned` directly (not via `IsTombstoned()`) under the DB's `RLock`. However, `Tombstone()` (registration_db.go line 48-51) writes `tombstoned` without holding the DB lock, so the `RLock` does not protect against this concurrent write. This is a data race between `doDebug` and `doTombstoneTopicProducer`.

- **Lines 163-173:** QUESTION (Low). `doDeleteTopic` performs channel removal and topic removal in separate lock acquisitions (each `FindRegistrations` and `RemoveRegistration` call acquires/releases independently). Between deleting channels (lines 164-167) and deleting the topic (lines 169-173), a concurrent `REGISTER` command could add new channel registrations for the topic being deleted, leaving orphaned channel entries. This is likely acceptable for an eventually-consistent lookup service but worth noting.

## nsqlookupd/lookup_protocol_v1.go

- **Lines 249-251:** QUESTION (Medium). `IDENTIFY` calls `os.Hostname()` and on failure calls `log.Fatalf()`, which terminates the entire nsqlookupd process. A single client IDENTIFY triggering a process-wide crash is disproportionate. While `os.Hostname()` rarely fails, this converts a transient OS error into total service unavailability. Expected: return an error to the client. Actual: `os.Exit(1)` via `log.Fatalf`.

- **Line 48:** QUESTION (Low). In the error handling path of `IOLoop`, the code does `err.(protocol.ChildErr).Parent()` — a type assertion without the comma-ok form. If `err` does not implement `protocol.ChildErr`, this will panic. This relies on all errors returned from `Exec` implementing `ChildErr`. If a future code change introduces an error that doesn't implement this interface, this would panic and crash the connection handler. Currently safe because `Exec` only returns `protocol.FatalClientErr` and `protocol.ClientErr`, both of which implement `ChildErr`.

## nsqlookupd/registration_db_test.go

- **Lines 53, 61, 62:** QUESTION (Low). Direct assignment to `p.peerInfo.lastUpdate` (e.g., `p2.peerInfo.lastUpdate = time.Now().UnixNano()`) instead of `atomic.StoreInt64(&p2.peerInfo.lastUpdate, ...)`. Production code uses `atomic.StoreInt64`/`atomic.LoadInt64` consistently (registration_db.go line 218, lookup_protocol_v1.go lines 233, 270). While there is no concurrent access in this test making it safe in practice, this sets a bad precedent and would mask any future test refactoring that introduces concurrency.

---

## Summary

| Severity | Count |
|----------|-------|
| BUG (Medium) | 3 |
| QUESTION (Medium) | 1 |
| QUESTION (Low) | 4 |

**Total findings: 8**

### Bug summary

The primary correctness issue is the **data race on `Producer.tombstoned` and `Producer.tombstonedAt`** fields. `Tombstone()` writes these fields without synchronization while `IsTombstoned()` and `doDebug` read them concurrently from HTTP handler goroutines. The `time.Time` type is a multi-word struct, making torn reads possible. This would be flagged by `go test -race`. Fix: either protect `tombstoned`/`tombstonedAt` with a mutex on `Producer`, use atomic operations, or hold the DB write lock during `Tombstone()` calls.

### Files with no findings

None — all four files have at least one finding.

### Overall assessment

**FIX FIRST** — The tombstone data race (3 findings) is a real concurrency bug that violates the Go memory model and would be caught by the race detector. The `log.Fatalf` in IDENTIFY is a secondary concern. The remaining QUESTION items are low-severity design observations.
