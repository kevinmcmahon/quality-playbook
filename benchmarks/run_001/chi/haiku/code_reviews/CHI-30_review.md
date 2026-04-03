# Code Review: middleware/wrap_writer.go

**File:** middleware/wrap_writer.go
**Reviewer:** Claude Code
**Date:** 2026-03-31

## Summary

Found 3 bugs affecting middleware response writer wrapping. Two are correctness issues (type mismatch, byte count corruption), one is a deprecation violation.

---

## Findings

### 1. [BUG] Push method defined on wrong type

**Severity:** Critical
**Lines:** 202-204, 221

**Issue:**
The `Push` method (HTTP/2 server push capability) is defined on `*httpFancyWriter` (HTTP/1.x writer) but the interface assertion on line 221 expects `http2FancyWriter` to implement `http.Pusher`.

**Evidence:**
- Line 202-204: Push method receiver is `*httpFancyWriter`
- Line 221: `var _ http.Pusher = &http2FancyWriter{}`
- Line 228-236: `http2FancyWriter` only defines `Flush()`, not `Push()`

**Consequence:**
Code will not compile. The var assertion requires http2FancyWriter to have a Push method, but it doesn't. Additionally, semantically, Push should only exist on HTTP/2 writers, not HTTP/1.x writers.

**Fix:**
Move the Push method from `*httpFancyWriter` to `*http2FancyWriter` (lines 202-204 should be moved into the http2FancyWriter type definition block).

---

### 2. [BUG] Double-counting of bytes in ReadFrom with tee writer

**Severity:** High
**Line:** 209

**Issue:**
When tee is enabled, the ReadFrom method double-counts bytes written. Line 208 calls `io.Copy(&f.basicWriter, r)` which triggers multiple Write() calls, each incrementing `f.basicWriter.bytes` (line 109). Then line 209 adds the byte count again.

**Evidence:**
```go
// Line 207-210
if f.basicWriter.tee != nil {
    n, err := io.Copy(&f.basicWriter, r)  // Each chunk triggers Write()
    f.basicWriter.bytes += int(n)           // Adds bytes again - DOUBLE COUNT
    return n, err
}
```

When `io.Copy` reads and writes 1000 bytes in chunks:
- Each Write() call increments bytes (line 109)
- io.Copy returns 1000
- Line 209 adds 1000 again → bytes reports 2000 instead of 1000

**Consequence:**
Callers relying on `BytesWritten()` (line 123) get incorrect response size metrics when tee is enabled. This affects middleware that tracks response sizes (logging, metrics, rate limiting).

**Fix:**
When using `io.Copy`, do not add the byte count again. Either use io.Copy directly and rely on Write() to count, or use the underlying ResponseWriter's ReadFrom if available (see lines 212-217 for the correct pattern).

---

### 3. [SUGGESTION] Deprecated io/ioutil usage

**Severity:** Medium
**Lines:** 9, 107

**Issue:**
Code imports and uses deprecated `io/ioutil` package. Recent chi commits ("Remove last uses of io/ioutil") removed io/ioutil from the codebase. This import and usage should be modernized.

**Evidence:**
- Line 9: `import "io/ioutil"`
- Line 107: `ioutil.Discard.Write(buf)`

**Standard replacement:**
Use `io.Discard` (available since Go 1.16) instead of `ioutil.Discard`.

**Fix:**
- Remove "io/ioutil" from imports (line 9)
- Change line 107 from `ioutil.Discard.Write(buf)` to `io.Discard.Write(buf)`
- Note: `io` is already imported on line 8, so no additional import needed

---

## Checklist

- [x] Line numbers provided for all findings
- [x] Read complete function bodies (lines 83-217 traced through)
- [x] Grepped for related patterns (Push method, io.Discard usage)
- [x] Flagged all bugs found (3 total: 1 critical, 1 high, 1 medium)
- [x] Distinguished between BUG and SUGGESTION appropriately

## Recommendation

Do not approve until:
1. Push method is moved to http2FancyWriter (compile error)
2. ReadFrom byte counting is fixed (correctness issue)
3. io/ioutil deprecation is resolved (consistency with recent commits)
