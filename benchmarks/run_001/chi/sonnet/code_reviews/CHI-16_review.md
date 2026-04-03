# Code Review: CHI-16

**File reviewed:** `middleware/wrap_writer.go`
**Reviewer:** sonnet
**Date:** 2026-03-31

---

## middleware/wrap_writer.go

### Finding 1

- **Line 74:** [BUG] `WriteHeader` unconditionally forwards to the underlying writer even after headers have already been sent.
- **Severity:** High
- **Description:** The call `b.ResponseWriter.WriteHeader(code)` at line 74 is outside the `if !b.wroteHeader` guard. The guard on lines 70–73 correctly protects `b.code` and `b.wroteHeader` from being set more than once, but the underlying `WriteHeader` call is not guarded. If a handler (or middleware) calls `WriteHeader` a second time, the underlying `http.ResponseWriter.WriteHeader` is called again.
- **Expected:** Once `b.wroteHeader` is true, subsequent calls to `WriteHeader` should be silently swallowed by the wrapper — the whole point of the guard is to make the wrapper idempotent.
- **Actual:** The underlying writer receives a second (or further) `WriteHeader` call. Go's `net/http` logs `"http: superfluous response.WriteHeader call"` for every extra call. Some custom `ResponseWriter` implementations may behave incorrectly on duplicate calls. The wrapper's recorded `b.code` is the first code (correct), but the underlying writer still receives the duplicate.
- **Why it matters:** Middleware that defensively calls `WriteHeader` to ensure a status is written (e.g., error-recovery middleware) will produce log noise or incorrect behavior in wrapped writers.

---

### Finding 2

- **Lines 118, 135, 177:** [BUG] `Flush()` in `flushWriter`, `httpFancyWriter`, and `http2FancyWriter` sets `wroteHeader = true` without setting `code`, leaving `Status()` returning `0` when flush triggers implicit header dispatch.
- **Severity:** Medium
- **Description:**
  - `flushWriter.Flush()` line 118: `f.wroteHeader = true` — `f.code` is not set.
  - `httpFancyWriter.Flush()` line 135: same pattern.
  - `http2FancyWriter.Flush()` line 177: same pattern.

  When `Flush()` is called before any `WriteHeader` or `Write`, the underlying `http.Flusher.Flush()` causes the HTTP stack to finalize and send response headers with status 200. The wrapper records `wroteHeader = true` to track this, but `code` remains at its zero value (`0`). After the flush, `Status()` returns `0` instead of `200`.
- **Expected:** If flush triggers implicit header dispatch, `Status()` should return `200` (mirroring what `maybeWriteHeader` / `WriteHeader(http.StatusOK)` does).
- **Actual:** `Status()` returns `0` for responses whose headers were flushed implicitly.
- **Why it matters:** Any logging or metrics middleware that records the status code after the handler runs will log `0` instead of `200` for streaming responses that flush before writing.

---

### Finding 3

- **Line 153:** [BUG] `httpFancyWriter.ReadFrom` double-counts bytes when `tee` is set.
- **Severity:** High
- **Description:** The tee branch (lines 151–154):
  ```go
  if f.basicWriter.tee != nil {
      n, err := io.Copy(&f.basicWriter, r)   // basicWriter.Write() is called; it does b.bytes += n (line 87)
      f.basicWriter.bytes += int(n)            // adds n AGAIN
      return n, err
  }
  ```
  `io.Copy(&f.basicWriter, r)` routes data through `basicWriter.Write()`, which already increments `b.bytes` by `n` at line 87. Line 153 then increments `f.basicWriter.bytes` by `n` a second time, resulting in `BytesWritten()` reporting twice the actual bytes transferred.

  The non-tee branch (lines 156–160) is correct: `rf.ReadFrom(r)` bypasses `basicWriter.Write()`, so the single increment at line 159 is the only one.
- **Expected:** `BytesWritten()` should equal the number of bytes actually transferred to the client.
- **Actual:** `BytesWritten()` returns `2 * n` when a tee writer is registered and `ReadFrom` is used.
- **Why it matters:** Any middleware using `BytesWritten()` for logging, rate limiting, or billing (e.g., bandwidth tracking) will report double the actual payload size for responses using `ReadFrom` with a tee attached.

---

## Summary

| Severity | Count |
|----------|-------|
| High     | 2     |
| Medium   | 1     |
| Low      | 0     |

**Total findings:** 3 (all BUG)

**Overall assessment:** FIX FIRST

All three findings affect observable, externally visible behavior: status code tracking (`0` vs `200`), spurious `WriteHeader` calls to the underlying writer, and byte count doubling. Middleware built on top of `WrapResponseWriter` for logging, metrics, or billing cannot trust `Status()` or `BytesWritten()` under these conditions.
