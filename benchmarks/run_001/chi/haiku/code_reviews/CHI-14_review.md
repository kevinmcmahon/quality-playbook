# Code Review: middleware/compress.go (CHI-14)

## Summary
Reviewed compress.go middleware for correctness, proper error handling, and Go language best practices. Found 3 bugs and 1 question.

---

## Findings

### BUG #1: Deprecated ioutil.Discard Usage
- **File**: middleware/compress.go
- **Lines**: 167, 172
- **Severity**: High
- **Description**:
  - Line 167: `encoder := fn(ioutil.Discard, c.level)`
  - Line 172: `return fn(ioutil.Discard, c.level)`

  The `io/ioutil` package is deprecated since Go 1.16. Code should use `io.Discard` instead. The project already imports "io" on line 9 and has bumped minimum Go version to 1.23 (per recent commit a54874f), so `io.Discard` is available.

---

### BUG #2: Incorrect Accept-Encoding Header Matching Logic
- **File**: middleware/compress.go
- **Line**: 249
- **Severity**: Medium
- **Description**:
  The `matchAcceptEncoding` function uses substring matching instead of proper token matching:
  ```go
  if strings.Contains(v, encoding) {
      return true
  }
  ```

  This causes false positives. For example, when checking if encoding "gzip" is in the Accept-Encoding header:
  - If header contains "x-gzip", the function incorrectly returns true (false positive)
  - "gzip" is a substring of "x-gzip", but they are different encodings per RFC 7231

  The correct approach should:
  1. Trim spaces from each value (v has leading space from split on line 222)
  2. Split by semicolon to separate encoding token from quality parameters
  3. Compare the token part exactly (case-insensitive comparison already done on line 222)

  Impact: If a client supports "x-gzip" but not "gzip", the middleware would incorrectly attempt to use "gzip" compression.

---

### BUG #3: Unhandled Error from compressFlusher.Flush()
- **File**: middleware/compress.go
- **Line**: 355
- **Severity**: Medium
- **Description**:
  The `Flush()` method ignores the error returned by `compressFlusher.Flush()`:
  ```go
  if f, ok := cw.writer().(compressFlusher); ok {
      f.Flush()  // Line 355: error is ignored
  ```

  The `compressFlusher` interface (line 345) defines `Flush() error`, meaning it can return an error. This error could indicate I/O failures in the compression writer (e.g., gzip.Writer or flate.Writer) that should not be silently ignored.

  Impact: Real flush errors in compression writers are masked, potentially resulting in incomplete or corrupted compressed output being sent to the client without warning.

---

### QUESTION: Accept-Encoding Header Parsing - Spaces Not Trimmed
- **File**: middleware/compress.go
- **Line**: 222
- **Severity**: Low
- **Description**:
  Line 222 splits the Accept-Encoding header by comma without trimming spaces:
  ```go
  accepted := strings.Split(strings.ToLower(header), ",")
  ```

  According to RFC 7231, the header format is: `Accept-Encoding = 1#codings`. After the split, values like `" deflate"` contain leading whitespace. While the substring matching logic (line 249) works despite this, it's not proper header parsing.

  Question: Should spaces be explicitly trimmed from each token, or is the current lenient parsing intentional to handle non-compliant clients?

---

## Code Review Checklist
- [x] Read complete function bodies, not just signatures
- [x] Verified line numbers for all findings
- [x] Grepped to confirm issues are present
- [x] Checked against chi router quality scenarios where applicable:
  - Scenario #7 (Context/resource pool safety): SetEncoder creates pooled encoders - cleanup logic and reset semantics verified as correct
  - Scenario #10 (Handler nil checks): Encoder nil checks present (line 168, 179)
- [x] Flagged issues with mandatory line numbers

## Files Examined
- middleware/compress.go (lines 1-400)
- go.mod (minimum Go version verification)

## Notes
The Flush() method logic (lines 348-362) was analyzed and found to be correct: it properly flushes both the compression writer and the underlying response writer in the appropriate code paths. The issue is only with the error return value being ignored.

The pool management in SetEncoder (lines 159-189) is correct: old pooled encoders are properly cleared before adding new ones, and the precedence ordering is updated correctly.
