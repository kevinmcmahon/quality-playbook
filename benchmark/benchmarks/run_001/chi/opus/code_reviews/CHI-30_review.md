# Code Review: middleware/wrap_writer.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-03-31
**Worktree:** /tmp/qpb_wt_chi_opus_CHI-30

---

### middleware/wrap_writer.go

- **Line 209:** [BUG] **Severity: High** — Double byte counting in `ReadFrom` when tee is set. When `f.basicWriter.tee != nil`, `io.Copy(&f.basicWriter, r)` calls `basicWriter.Write()` which increments `b.bytes += n` on line 109 for each chunk written. Then line 209 does `f.basicWriter.bytes += int(n)` again with the total bytes copied. This causes `BytesWritten()` to report approximately double the actual bytes written. The non-tee branch (line 215) is correct because `rf.ReadFrom(r)` bypasses `basicWriter.Write()` and only counts bytes at line 215.

- **Line 9, 107:** [BUG] **Severity: Low** — Uses deprecated `io/ioutil` package (imported on line 9, used on line 107 as `ioutil.Discard.Write(buf)`). This was already removed from the main branch (commit a36a925 "Remove last uses of io/ioutil") but persists in this file. Should use `io.Discard` from the `io` package instead. Not a runtime failure, but `io/ioutil` has been deprecated since Go 1.16 and the import is unnecessary since `io` is already imported on line 7.

- **Line 144-147, 169-172, 191-194, 232-235:** [QUESTION] **Severity: Medium** — All `Flush()` implementations set `f.wroteHeader = true` but do not set `f.code`. If `Flush()` is called before any explicit `WriteHeader()` or `Write()`, Go's HTTP server will implicitly send a 200 status. However, `Status()` will return 0 because `code` was never set. Additionally, subsequent calls to `Write()` will skip `maybeWriteHeader()` (since `wroteHeader` is true), so the proxy never records the actual status code. Is this intentional behavior, or should `Flush()` call `maybeWriteHeader()` to ensure `code` is set to 200?

- **Line 144-147, 169-172, 191-194, 232-235:** [QUESTION] **Severity: Medium** — `Flush()` implementations do not check the `discard` flag. When `Discard()` has been called, `WriteHeader()` (line 87-89) and `Write()` (line 95-108) both skip the original `ResponseWriter`, but `Flush()` still calls `f.basicWriter.ResponseWriter.(http.Flusher).Flush()` unconditionally. Is this intentional? If the caller expects discarded responses to not touch the original writer at all, this could cause unexpected behavior (e.g., flushing partially written or empty response headers to the client).

- **Line 202-204:** [QUESTION] **Severity: Low** — The `http2FancyWriter.Push()` method is defined in the middle of `httpFancyWriter` methods (between `Hijack()` on line 197 and `ReadFrom()` on line 206). This is not a bug, but the placement is confusing — the method belongs to a different type than its surrounding methods. Was this intentional or a misplaced definition?

---

### Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 1     |
| Medium   | 2     |
| Low      | 2     |

- **BUGs:** 2 (double byte counting in ReadFrom, deprecated ioutil usage)
- **QUESTIONs:** 3 (Flush/wroteHeader without code, Flush ignoring discard, Push method placement)
- **Files with no findings:** None (only one file reviewed)

**Overall assessment: FIX FIRST** — The double byte counting bug in `ReadFrom` (line 209) is a real correctness issue that will cause `BytesWritten()` to return wrong values when both tee and ReadFrom are used together (e.g., logging middleware with `http.ServeContent`). The fix is to remove line 209 (`f.basicWriter.bytes += int(n)`) since `io.Copy` already counts bytes through `basicWriter.Write()`.
