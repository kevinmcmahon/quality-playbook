# Code Review: middleware/wrap_writer.go

**Reviewer:** Claude Haiku 4.5
**File:** middleware/wrap_writer.go
**Review Protocol:** chi/haiku/quality/RUN_CODE_REVIEW.md

---

## Summary

Three bugs found in response writer wrapping logic:
- **2 critical tracking bugs** in Flush() implementations that cause Status() to return incorrect values
- **1 byte-counting bug** in ReadFrom() when tee writer is active

---

## Detailed Findings

### BUG #1: flushWriter.Flush() sets wroteHeader without ensuring header emission

**Finding Type:** BUG
**Severity:** High
**File and Line:** middleware/wrap_writer.go:118

**Description:**

The `flushWriter.Flush()` method sets `wroteHeader = true` without calling `maybeWriteHeader()`, breaking the status tracking invariant.

**Code Flow Analysis:**

1. `WriteHeader()` (line 69-75) only sets the `code` field when `!b.wroteHeader`
2. `maybeWriteHeader()` (line 91-95) checks if `wroteHeader` is false before calling `WriteHeader(http.StatusOK)`
3. `Write()` (line 78) always calls `maybeWriteHeader()` first

**The Bug:**

When `Flush()` is called before any `Write()` or explicit `WriteHeader()`:
- Line 118 sets `wroteHeader = true`
- `code` remains 0 (never set)
- Later, if `Write()` is called, `maybeWriteHeader()` (line 92) sees `wroteHeader == true` and returns early
- `WriteHeader()` is never called, so `code` stays 0
- `Status()` (line 97-98) returns 0 instead of the actual 200 OK that the underlying ResponseWriter sends

**Example Scenario:**
```go
fw := NewWrapResponseWriter(w, 1)
fw.Flush()  // Sets wroteHeader=true, but code=0
fw.Write([]byte("hello"))  // maybeWriteHeader returns early, code still 0
fmt.Println(fw.Status())   // Prints 0, but client got 200 OK - BUG!
```

**Fix:** Call `maybeWriteHeader()` before delegating to the underlying Flusher:
```go
func (f *flushWriter) Flush() {
    f.basicWriter.maybeWriteHeader()
    fl := f.basicWriter.ResponseWriter.(http.Flusher)
    fl.Flush()
}
```

---

### BUG #2: httpFancyWriter.Flush() sets wroteHeader without ensuring header emission

**Finding Type:** BUG
**Severity:** High
**File and Line:** middleware/wrap_writer.go:135

**Description:**

Same bug as BUG #1, occurring in the HTTP/1.x fancy writer variant.

**Code:**
```go
func (f *httpFancyWriter) Flush() {
    f.wroteHeader = true        // Bug: doesn't call maybeWriteHeader()

    fl := f.basicWriter.ResponseWriter.(http.Flusher)
    fl.Flush()
}
```

**Impact:** Same as BUG #1 — `Status()` returns 0 when it should return 200 if `Flush()` is called before any explicit `WriteHeader()` or `Write()`.

**Fix:** Same as BUG #1 — call `maybeWriteHeader()` first.

---

### BUG #3: httpFancyWriter.ReadFrom() double-counts bytes when tee is active

**Finding Type:** BUG
**Severity:** High
**File and Line:** middleware/wrap_writer.go:153

**Description:**

The `ReadFrom()` method double-counts bytes written when a tee writer is configured.

**Code Flow Analysis:**

When `tee != nil` (lines 151-154):
1. `io.Copy(&f.basicWriter, r)` is called (line 152)
2. `io.Copy` calls `basicWriter.Write()` multiple times
3. Each `Write()` call increments `f.basicWriter.bytes` (line 87)
4. After `io.Copy` returns with total `n`, bytes are already incremented
5. **Line 153 then increments bytes again:** `f.basicWriter.bytes += int(n)`

**Result:** `BytesWritten()` returns 2× the actual bytes sent.

**Example Scenario:**
```go
fw := NewWrapResponseWriter(w, 1)
fw.Tee(os.Stderr)
fw.ReadFrom(strings.NewReader("hello"))  // 5 bytes

// Execution trace:
// io.Copy -> Write -> bytes += 5 (first count)
// Line 153 -> bytes += 5 (second count, BUG!)

fmt.Println(fw.BytesWritten())  // Prints 10, but actually sent 5 - BUG!
```

**Why it's a bug:** The purpose of `BytesWritten()` is to accurately report bytes sent. When `tee != nil`, the bytes counter is corrupted, breaking middleware that relies on accurate byte counts (e.g., logging, metrics, rate limiting).

**Fix:** Remove the duplicate increment on line 153:
```go
func (f *httpFancyWriter) ReadFrom(r io.Reader) (int64, error) {
    if f.basicWriter.tee != nil {
        n, err := io.Copy(&f.basicWriter, r)
        // Don't increment again - Write() already did it via io.Copy
        return n, err
    }
    // ... rest of method
}
```

---

### BUG #4: http2FancyWriter.Flush() sets wroteHeader without ensuring header emission

**Finding Type:** BUG
**Severity:** High
**File and Line:** middleware/wrap_writer.go:177

**Description:**

Same bug as BUG #1 and BUG #2, occurring in the HTTP/2 fancy writer variant.

**Code:**
```go
func (f *http2FancyWriter) Flush() {
    f.wroteHeader = true        // Bug: doesn't call maybeWriteHeader()

    fl := f.basicWriter.ResponseWriter.(http.Flusher)
    fl.Flush()
}
```

**Impact:** Same as BUG #1 and BUG #2 — `Status()` returns 0 when it should return 200 if `Flush()` is called before any explicit `WriteHeader()` or `Write()`.

**Fix:** Same as BUG #1 — call `maybeWriteHeader()` first.

---

## Summary of Fixes Required

| Line | Issue | Fix |
|------|-------|-----|
| 118 | `flushWriter.Flush()` skips `maybeWriteHeader()` | Call `f.basicWriter.maybeWriteHeader()` before Flush |
| 135 | `httpFancyWriter.Flush()` skips `maybeWriteHeader()` | Call `f.basicWriter.maybeWriteHeader()` before Flush |
| 153 | Double-counting bytes in `ReadFrom()` with tee | Remove `f.basicWriter.bytes += int(n)` |
| 177 | `http2FancyWriter.Flush()` skips `maybeWriteHeader()` | Call `f.basicWriter.maybeWriteHeader()` before Flush |

---

## Verification Steps

1. **Unit test the tracking:** Create tests that:
   - Call `Flush()` before `Write()` and verify `Status()` returns 200 (not 0)
   - Call `ReadFrom()` with tee active and verify `BytesWritten()` matches actual bytes (not 2×)

2. **Regression test pattern:**
   ```go
   func TestFlushStatusTracking(t *testing.T) {
       w := &mockResponseWriter{}
       fw := NewWrapResponseWriter(w, 1)
       fw.Flush()            // Flush before Write
       fw.Write([]byte("x")) // This should trigger WriteHeader internally

       if fw.Status() != 200 {
           t.Errorf("Expected Status=200 after Flush+Write, got %d", fw.Status())
       }
   }

   func TestReadFromBytesCounting(t *testing.T) {
       w := &mockResponseWriter{}
       fw := NewWrapResponseWriter(w, 1)
       fw.Tee(io.Discard)

       n, _ := fw.ReadFrom(strings.NewReader("hello"))
       if fw.BytesWritten() != int(n) {
           t.Errorf("Expected BytesWritten=%d, got %d", n, fw.BytesWritten())
       }
   }
   ```

3. **Integration test:** Verify middleware using `Status()` and `BytesWritten()` produce correct results with the fixed code.

---

## Code Review Sign-Off Checklist

- ✓ Read complete function bodies (not just signatures)
- ✓ Traced data flow for wroteHeader, code, bytes fields
- ✓ Verified wroteHeader invariant is broken in Flush() methods
- ✓ Verified double-counting in ReadFrom with io.Copy
- ✓ Grepped for maybeWriteHeader usage to understand intended patterns
- ✓ Flagged all issues with specific line numbers
- ✓ Flagged correctness issues, not style
