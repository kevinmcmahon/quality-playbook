# Code Review: CHI-06 — middleware/wrap_writer.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-03-31
**File:** `middleware/wrap_writer.go`

---

## Findings

### middleware/wrap_writer.go

- **Line 131-133:** [BUG] **Severity: High.** Double-counting of bytes in `ReadFrom` when tee is non-nil. When `tee != nil`, `io.Copy(&f.basicWriter, r)` calls `basicWriter.Write()`, which increments `b.bytes` at line 84. Then line 133 (`f.basicWriter.bytes += int(n)`) increments `bytes` again. The result is `BytesWritten()` returns roughly 2x the actual bytes written. The non-tee path at lines 136-138 does not go through `basicWriter.Write()` (it calls `rf.ReadFrom(r)` directly), so the explicit increment at line 138 is correct there. Only the tee path double-counts.

- **Line 119, 155:** [BUG] **Severity: Medium.** `Flush()` in both `httpFancyWriter` (line 119) and `http2FancyWriter` (line 155) sets `wroteHeader = true` but does not set `code`. After a `Flush()` followed by `Write()`, `maybeWriteHeader()` (line 88-91) is a no-op because `wroteHeader` is already true, so `code` is never set. `Status()` returns 0 even though the underlying ResponseWriter will have implicitly sent a 200. Any middleware relying on `Status()` (e.g., the logger at `middleware/logger.go`) will see 0 instead of 200 for flushed responses.

- **Lines 20-29:** [QUESTION] **Severity: Medium.** The constructor uses OR logic to decide whether to create a fancy writer: `fl || hj || rf` (line 28) for HTTP/1.x and `fl || ps` (line 22) for HTTP/2. However, the fancy writer methods perform unchecked type assertions — e.g., `Hijack()` at line 125 unconditionally asserts `http.Hijacker`, `ReadFrom()` at line 135 asserts `io.ReaderFrom`, `Push()` at line 161 asserts `http.Pusher`. If the underlying writer satisfies only one of the interfaces (e.g., `http.Flusher` but not `http.Hijacker`), calling the unsatisfied method will panic. In practice, the standard library's `http.ResponseWriter` implements all relevant interfaces, so this may be safe by convention. But any custom ResponseWriter that implements only a subset will trigger a panic. Is this intentional (relying on standard library guarantees) or should these use checked assertions?

- **Lines 133, 138:** [QUESTION] **Severity: Low.** `int(n)` truncates `int64` to `int`. On 32-bit platforms, responses larger than 2GB would cause `BytesWritten()` to return incorrect values. The `bytes` field is declared as `int` (line 62). This may be acceptable given that 32-bit targets are uncommon, but it is a latent overflow.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 1     |
| Medium   | 2     |
| Low      | 1     |

- **Total findings:** 4 (2 BUG, 2 QUESTION)
- **Files with no findings:** N/A (single file review)
- **Overall assessment:** **FIX FIRST** — The double-counting bug in `ReadFrom` (line 131-133) will produce incorrect `BytesWritten()` values whenever `Tee` is used with `ReadFrom`, affecting any middleware that relies on byte counts (e.g., logging, metrics). The `Flush`/status bug is less severe but will cause incorrect status reporting in logged output.
