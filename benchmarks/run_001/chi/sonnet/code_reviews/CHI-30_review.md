# Code Review: CHI-30

**File reviewed:** `middleware/wrap_writer.go`
**Date:** 2026-03-31

---

## middleware/wrap_writer.go

### Line 209: BUG — Double-counting bytes in `ReadFrom` when tee is set

- **Severity:** High
- **Finding type:** BUG

`httpFancyWriter.ReadFrom` (lines 206–217) has two code paths:

**Tee path (lines 207–210):**
```go
n, err := io.Copy(&f.basicWriter, r)
f.basicWriter.bytes += int(n)   // line 209 — double count
```

`io.Copy(&f.basicWriter, r)` calls `basicWriter.Write()` repeatedly for each chunk. Each call to `Write()` increments `b.bytes += n` at line 109. After `io.Copy` completes, `n` holds the total bytes transferred. Line 209 then adds that total to `f.basicWriter.bytes` a second time.

**Result:** `BytesWritten()` returns `2 × actual_bytes` when `tee != nil` and `ReadFrom` is the write path.

**Non-tee path (lines 212–216)** is correct: `rf.ReadFrom(r)` bypasses `basicWriter.Write()` entirely (writes directly to the underlying `ResponseWriter`), so line 215's `f.basicWriter.bytes += int(n)` is the only increment — correct.

**Expected:** `f.basicWriter.bytes` equals the actual number of bytes transferred.
**Actual:** When tee is set, bytes are counted once via `basicWriter.Write()` during `io.Copy`, then counted again at line 209, doubling the value.

---

### Lines 9 & 107: BUG — Deprecated `io/ioutil` import and usage

- **Severity:** Low
- **Finding type:** BUG

Line 9 imports `"io/ioutil"`. Line 107 uses `ioutil.Discard.Write(buf)`. `io/ioutil` was deprecated in Go 1.16; the direct replacement is `io.Discard`. The project's main branch already removed all other `io/ioutil` uses (commit `a36a925 Remove last uses of io/ioutil`), but this file was not updated.

**Expected:** `io.Discard` is used directly; `"io/ioutil"` is not imported.
**Actual:** `ioutil.Discard` is used; `"io/ioutil"` is still in the import block.

---

### Lines 144–148, 169–172, 191–195, 232–236: QUESTION — `Flush()` sets `wroteHeader = true` without setting `code`

- **Severity:** Low
- **Finding type:** QUESTION

All four `Flush()` implementations (in `flushWriter`, `flushHijackWriter`, `httpFancyWriter`, `http2FancyWriter`) set `f.wroteHeader = true` but never set `f.code`. For example:

```go
func (f *flushWriter) Flush() {
    f.wroteHeader = true          // code is NOT set
    fl := f.basicWriter.ResponseWriter.(http.Flusher)
    fl.Flush()
}
```

If `Flush()` is called before any `Write()` or `WriteHeader()`, Go's `net/http` sends an implicit 200 to the client when the underlying `Flush()` is called. Setting `wroteHeader = true` prevents any subsequent `WriteHeader(code)` from reaching the underlying writer (the guard at line 84 makes it a no-op). As a result, `Status()` returns `0` even though a 200 was sent.

**Question:** Is it intentional that `Status()` returns `0` after a flush-only response, or should `Flush()` call `b.WriteHeader(http.StatusOK)` (via `maybeWriteHeader()`) before delegating to the underlying `Flush()`?

---

## Summary

| Finding | Type | Severity |
|---------|------|----------|
| Line 209: double-counting bytes in `ReadFrom` tee path | BUG | High |
| Lines 9 & 107: deprecated `io/ioutil` usage | BUG | Low |
| Lines 144–148 etc.: `Flush()` sets `wroteHeader` without `code` | QUESTION | Low |

- **Total BUGs:** 2 (1 High, 1 Low)
- **Total QUESTIONs:** 1 (Low)

**Overall assessment: FIX FIRST** — the double-counting bug in `ReadFrom` causes `BytesWritten()` to report incorrect values for any middleware or handler that uses a tee writer with HTTP/1.1 and calls `ReadFrom` (e.g., `sendfile`-backed responses). Middleware relying on accurate byte counts for logging or rate-limiting will receive wrong data.
