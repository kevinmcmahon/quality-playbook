# Code Review: middleware/wrap_writer.go

## Findings

### middleware/wrap_writer.go

- **Line 153:** [BUG] **Severity: Medium.** Double byte counting in `ReadFrom` when tee is set. When `f.basicWriter.tee != nil`, `io.Copy(&f.basicWriter, r)` calls `basicWriter.Write()` which increments `b.bytes += n` at line 87 on each chunk. Then line 153 increments `f.basicWriter.bytes += int(n)` again with the total bytes copied. This causes `BytesWritten()` to return approximately double the actual bytes written. The non-tee path (line 159) is correct since `rf.ReadFrom(r)` bypasses `basicWriter.Write()` entirely.

- **Line 74:** [BUG] **Severity: Medium.** `WriteHeader` forwards to the underlying `ResponseWriter` unconditionally, even on duplicate calls. The `wroteHeader` guard (line 70) only protects the status code recording, but `b.ResponseWriter.WriteHeader(code)` at line 74 is called every time. In Go's `net/http`, calling `WriteHeader` more than once logs a "superfluous response.WriteHeader call" warning to stderr. The entire call should be guarded, not just the code tracking. Expected: `b.ResponseWriter.WriteHeader(code)` should be inside the `if !b.wroteHeader` block.

- **Lines 118, 135, 177:** [BUG] **Severity: Medium.** `Flush()` on `flushWriter`, `httpFancyWriter`, and `http2FancyWriter` sets `wroteHeader = true` but does not set `code`. After `Flush()` is called, a subsequent `Write()` will not trigger `maybeWriteHeader()` (since `wroteHeader` is already `true`), so `code` remains 0. `Status()` then returns 0 instead of 200. This affects any middleware relying on `Status()` for logging — e.g., `middleware/logger.go:43` calls `ww.Status()`. A Flushed-then-Written response would be logged with status 0 instead of 200.

- **Lines 168-169:** [QUESTION] **Severity: Low.** Comment for `http2FancyWriter` says it "additionally satisfies http.Flusher, and io.ReaderFrom" but the type does not implement `io.ReaderFrom`. There is no `ReadFrom` method and no compile-time assertion (`var _ io.ReaderFrom = &http2FancyWriter{}`). This means HTTP/2 responses lose the `ReadFrom` optimization (e.g., `sendfile` syscall). Is this intentional, or should `http2FancyWriter` also implement `ReadFrom` like `httpFancyWriter` does?

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 0     |
| Medium   | 3     |
| Low      | 1     |

**Total findings: 4** (3 BUG, 1 QUESTION)

**Overall assessment: FIX FIRST** — The double byte counting in `ReadFrom` (line 153) is a clear logic error affecting any code path that uses `ReadFrom` with a tee writer. The `WriteHeader` forwarding on duplicate calls produces noisy stderr warnings. The `Flush`/`Status` interaction silently produces wrong status codes in logs.
