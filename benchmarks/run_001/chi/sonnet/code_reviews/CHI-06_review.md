# Code Review: CHI-06

**File reviewed:** `middleware/wrap_writer.go`
**Reviewer:** sonnet
**Date:** 2026-03-31

---

## middleware/wrap_writer.go

### Finding 1

- **Line 131-132:** [BUG]
- **Severity:** Medium
- **Description:** Double-counting of bytes in `httpFancyWriter.ReadFrom` when a tee writer is set.

`io.Copy(&f.basicWriter, r)` at line 131 routes data through `basicWriter.Write()`, which already increments `b.bytes += n` at line 84. Line 132 then adds `f.basicWriter.bytes += int(n)` a second time, so `BytesWritten()` reports twice the actual number of bytes transferred.

**Expected:** `BytesWritten()` returns the number of bytes actually sent to the client.
**Actual:** `BytesWritten()` returns twice that value when a tee writer is active and `ReadFrom` is used (e.g., by `http.ServeContent` or `sendfile`).
**Why it matters:** Logging and metrics middleware relying on `BytesWritten()` (e.g., to populate `Content-Length` or bandwidth counters) will emit doubled values. The no-tee branch at lines 137-138 is correct because it calls `rf.ReadFrom` directly (bypassing `basicWriter.Write`), so only that single manual increment is needed there.

---

### Finding 2

- **Line 119:** [BUG]
- **Line 155:** [BUG]
- **Severity:** Medium
- **Description:** `Flush()` sets `wroteHeader = true` without recording the implicit HTTP 200 status in `b.code`, causing `Status()` to return 0.

Both `httpFancyWriter.Flush()` (line 119) and `http2FancyWriter.Flush()` (line 155) set `f.wroteHeader = true` directly, bypassing `WriteHeader`. When `Flush()` is the first output call on the response (no prior `WriteHeader` or `Write`), Go's `net/http` implicitly sends a 200 status to the wire. The wrapper's `b.code` field is never set (it remains 0), so `Status()` returns 0 after Flush instead of 200.

**Expected:** After `Flush()` triggers an implicit 200, `Status()` returns 200.
**Actual:** `Status()` returns 0.
**Why it matters:** Logging middleware (e.g., `middleware/logger.go`) reads `ww.Status()` after the handler returns to log the response code. A streamed response that calls `Flush()` before any `Write` will be logged with status 0, corrupting access logs and any metrics pipelines downstream.

---

## Summary

| Severity | Count |
|----------|-------|
| BUG      | 3 findings across 2 issues (lines 131-132, 119, 155) |
| QUESTION | 0 |
| SUGGESTION | 0 |

**Files with no findings:** none (single file reviewed)

**Overall assessment:** FIX FIRST — both bugs silently corrupt observable behavior (byte counts, status codes) that downstream middleware and logging pipelines depend on. Neither bug causes a panic or data loss, but they produce wrong values in production observability data.
