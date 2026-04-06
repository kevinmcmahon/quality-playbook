# Code Review: NSQ-05 — nsqlookupd/nsqlookupd.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `/tmp/qpb_wt_opus_NSQ-05/nsqlookupd/nsqlookupd.go`

---

### nsqlookupd/nsqlookupd.go

- **Line 45:** BUG — Copy-paste error in error message. When the HTTP listener fails to bind, the error message incorrectly references `opts.TCPAddress` instead of `opts.HTTPAddress`. This will mislead operators debugging a port conflict on the HTTP address, as the error will report the TCP address instead.
  - **Expected:** `fmt.Errorf("listen (%s) failed - %s", opts.HTTPAddress, err)`
  - **Actual:** `fmt.Errorf("listen (%s) failed - %s", opts.TCPAddress, err)`
  - **Severity:** Low (diagnostic/observability bug, not data loss)

- **Line 44-45:** BUG — Resource leak on partial initialization failure. If `net.Listen` for `HTTPAddress` (line 44) fails, `New()` returns an error but does not close the already-opened `tcpListener` (opened at line 39). The caller receives `(nil, err)` and has no handle to close the leaked TCP listener, leaving a bound socket that cannot be reclaimed until process exit.
  - **Expected:** Close `l.tcpListener` before returning the error on line 45.
  - **Actual:** `tcpListener` is leaked.
  - **Severity:** Medium (leaked file descriptor and bound port on startup failure; prevents immediate retry)

---

### Summary

| Severity | Count |
|----------|-------|
| Medium   | 1     |
| Low      | 1     |

- **Total findings:** 2
- **Overall assessment:** FIX FIRST — The resource leak (medium) should be fixed before shipping. The error message bug (low) is a straightforward one-line fix that should be included.
