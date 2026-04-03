# Code Review: middleware/wrap_writer.go

## Summary
Reviewed the response writer wrapper middleware. Found 3 issues: two Flush() methods don't properly track HTTP status codes, and ReadFrom() double-counts bytes when tee is configured.

---

## Findings

### 1. BUG: httpFancyWriter.Flush() doesn't track default status code
**File:** middleware/wrap_writer.go
**Line:** 118-121
**Severity:** Medium

**Description:**
The `Flush()` method sets `wroteHeader = true` but does not call `maybeWriteHeader()` to ensure the status code is tracked. When `Flush()` is called before any `WriteHeader()` or `Write()` call:

1. The underlying `http.ResponseWriter.Flush()` will implicitly write a 200 OK status to the client
2. But `f.basicWriter.code` remains 0
3. Calling `Status()` returns 0 instead of 200

This violates the wrapper's contract to track all response metadata.

**Example scenario:**
```go
w := NewWrapResponseWriter(w, 1)  // HTTP/1
w.(http.Flusher).Flush()           // Flushed before any Write/WriteHeader
w.Status()                          // Returns 0, but client received 200 OK
```

**Fix:** Call `f.basicWriter.maybeWriteHeader()` before calling the underlying `Flush()`:
```go
func (f *httpFancyWriter) Flush() {
    f.basicWriter.maybeWriteHeader()
    fl := f.basicWriter.ResponseWriter.(http.Flusher)
    fl.Flush()
}
```

---

### 2. BUG: http2FancyWriter.Flush() doesn't track default status code
**File:** middleware/wrap_writer.go
**Line:** 154-157
**Severity:** Medium

**Description:**
Same issue as Finding #1. The `Flush()` method sets `wroteHeader = true` without calling `maybeWriteHeader()`, causing `Status()` to return 0 when the underlying ResponseWriter implicitly sends 200 OK.

**Fix:** Call `f.basicWriter.maybeWriteHeader()` before calling the underlying `Flush()`:
```go
func (f *http2FancyWriter) Flush() {
    f.basicWriter.maybeWriteHeader()
    fl := f.basicWriter.ResponseWriter.(http.Flusher)
    fl.Flush()
}
```

---

### 3. BUG: httpFancyWriter.ReadFrom() double-counts bytes when tee is set
**File:** middleware/wrap_writer.go
**Line:** 132
**Severity:** Medium

**Description:**
When `tee` is configured, `io.Copy(&f.basicWriter, r)` calls `Write()` on the wrapper multiple times. Each `Write()` call increments `f.basicWriter.bytes` at line 84. Then line 132 adds the total `n` to `bytes` again, double-counting:

1. `io.Copy(&f.basicWriter, r)` writes 1000 bytes
2. Each `Write()` increments `bytes` (lines 84) → bytes = 1000
3. Line 132: `f.basicWriter.bytes += int(n)` → bytes = 2000 (WRONG)

Calling `BytesWritten()` returns twice the actual bytes sent.

**Example scenario:**
```go
w := NewWrapResponseWriter(w, 1)
var buf bytes.Buffer
w.Tee(&buf)
w.(io.ReaderFrom).ReadFrom(file)  // Copies 1000 bytes
w.BytesWritten()                   // Returns 2000, should return 1000
```

**Fix:** When `tee` is set, do not add `n` to `bytes` since `io.Copy` already incremented it:
```go
if f.basicWriter.tee != nil {
    n, err := io.Copy(&f.basicWriter, r)
    // Don't add n again; io.Copy already called Write() which incremented bytes
    return n, err
}
```

---

## Testing Notes
- These bugs affect monitoring and logging that depend on `Status()` and `BytesWritten()`
- The actual HTTP responses are sent correctly to clients
- Recommend adding regression tests for:
  - `Flush()` before any `Write()` or `WriteHeader()` call
  - `ReadFrom()` with `Tee()` configured
