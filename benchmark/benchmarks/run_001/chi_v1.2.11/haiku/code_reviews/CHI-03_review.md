# Code Review: middleware/compress.go

**File reviewed:** middleware/compress.go (v1.2.11)
**Lines reviewed:** 399 LOC
**Review date:** 2026-03-31

## Summary

Review of chi router's compression middleware. Found one critical bug in Accept-Encoding header matching, one misleading error message, and two code quality concerns.

---

## Findings by Severity

### Critical Bugs

| ID | File | Line | Severity | Finding |
|-----|------|------|----------|---------|
| BUG-1 | compress.go | 245 | **Critical** | Substring matching in Accept-Encoding header parsing causes false positives |

### Questions & Medium Severity

| ID | File | Line | Severity | Finding |
|-----|------|------|----------|---------|
| QUESTION-1 | compress.go | 72 | Medium | Panic message misleading about supported wildcard patterns |
| QUESTION-2 | compress.go | 224 | Medium | Type assertion without explicit error handling |
| SUGGESTION-1 | compress.go | 343-357 | Low | Potential duplicate Flush() calls |

---

## Detailed Findings

### BUG-1: Critical — Incorrect Accept-Encoding Header Matching (Line 245)

**Location:** `matchAcceptEncoding()` function, line 243-250

**Severity:** Critical

**Description:**
The function uses substring matching (`strings.Contains()`) instead of exact token matching or proper HTTP header parsing. This causes false positives when custom encoding names contain other encoding names as substrings.

```go
func matchAcceptEncoding(accepted []string, encoding string) bool {
	for _, v := range accepted {
		if strings.Contains(v, encoding) {  // Line 245: BUG
			return true
		}
	}
	return false
}
```

**Why it's a bug:**
- If a client sends `Accept-Encoding: x-gzip`, the code splits it to `["x-gzip"]`
- When checking for "gzip", `strings.Contains("x-gzip", "gzip")` returns `true`
- The code incorrectly accepts "gzip" when the client only accepted "x-gzip"
- This violates HTTP content negotiation semantics (RFC 7231)

**Impact:**
- Incorrect compression decisions based on malformed or crafted Accept-Encoding headers
- Potential compression of responses with non-standard encodings

**Example scenario:**
```
Client: Accept-Encoding: deflate-custom
Server checks for "deflate": strings.Contains("deflate-custom", "deflate") = true
Result: Server applies deflate compression, but client only accepts "deflate-custom"
```

**Recommended fix:**
Parse tokens properly by splitting on semicolons first (to remove quality factors), then trimming whitespace, then comparing exact strings:

```go
func matchAcceptEncoding(accepted []string, encoding string) bool {
	for _, v := range accepted {
		// Extract encoding name (before quality factor)
		parts := strings.Split(v, ";")
		encodingName := strings.TrimSpace(parts[0])
		if encodingName == encoding {  // Exact match, not substring
			return true
		}
	}
	return false
}
```

---

### QUESTION-1: Misleading Panic Message (Line 72)

**Location:** `NewCompressor()` function, line 71-72

**Severity:** Medium

**Description:**
The panic message claims "Only '/*' supported" but the code actually supports wildcard patterns like `"text/*"`, `"application/*"`, etc.

```go
if strings.Contains(strings.TrimSuffix(t, "/*"), "*") {
	panic(fmt.Sprintf("middleware/compress: Unsupported content-type wildcard pattern '%s'. Only '/*' supported", t))
}
```

**What the code does:**
1. Trims the trailing `"/*"` from the pattern
2. Checks if any `*` remains in the middle
3. Panics only if `*` is found elsewhere (e.g., `"text*html"`)

**What it actually supports:**
- Exact types: `"text/html"` ✓
- Wildcard types: `"text/*"`, `"application/*"` ✓
- Invalid wildcards: `"text*html"` ✗ (panics)

**Impact:**
- Low risk, but the error message is confusing for developers trying to understand supported wildcard syntax
- Users might think only the root wildcard `"/*"` is supported, when actually `<type>/*` patterns are fully supported

---

### QUESTION-2: Unsafe Type Assertion on Pool Item (Line 224)

**Location:** `selectEncoder()` function, line 223-229

**Severity:** Medium

**Description:**
The code performs an unsafe type assertion on a pooled encoder without explicit error handling:

```go
if pool, ok := c.pooledEncoders[name]; ok {
	encoder := pool.Get().(ioResetterWriter)  // Line 224: Unsafe assertion
	cleanup := func() {
		pool.Put(encoder)
	}
	encoder.Reset(w)
	return encoder, name, cleanup
}
```

**Risk:**
- If `pool.Get()` returns something that doesn't implement `ioResetterWriter`, the type assertion will panic
- While the code verifies the type at line 165, there's an implicit assumption that encoder functions are pure and always return the same type
- No defense against corrupted state or encoding function bugs

**Mitigation:**
The code is **probably safe in practice** because:
1. The pool's `New` function uses the same encoder function that was type-checked at line 165
2. Standard encoders (gzip, flate) have consistent behavior
3. The pool only contains items of the registered type

**Recommendation:**
Add explicit type assertion with error handling:

```go
encoder, ok := pool.Get().(ioResetterWriter)
if !ok {
	// Fallback or error handling
	return nil, "", func() {}
}
```

---

### SUGGESTION-1: Potential Duplicate Flush Calls (Lines 343-357)

**Location:** `Flush()` method on `compressResponseWriter`

**Severity:** Low

**Description:**
The Flush method calls `cw.writer()` twice and performs two separate type assertions that could both succeed on the same writer:

```go
func (cw *compressResponseWriter) Flush() {
	if f, ok := cw.writer().(http.Flusher); ok {
		f.Flush()  // First flush
	}
	if f, ok := cw.writer().(compressFlusher); ok {
		f.Flush()  // Second flush of same writer
		// ...
	}
}
```

**Impact:**
- If a writer implements both `http.Flusher` and `compressFlusher`, it's flushed twice
- Inefficient but not functionally incorrect (Flush should be idempotent)
- Violates DRY principle

**Example:** If gzip.Writer implements both interfaces, it's flushed at line 345 and again at line 350.

**Recommendation:**
Combine type checks to avoid duplicate flushes:

```go
func (cw *compressResponseWriter) Flush() {
	w := cw.writer()

	// Try compression-specific flush first
	if f, ok := w.(compressFlusher); ok {
		f.Flush()
		if f, ok := cw.ResponseWriter.(http.Flusher); ok {
			f.Flush()
		}
		return
	}

	// Fall back to standard flush
	if f, ok := w.(http.Flusher); ok {
		f.Flush()
	}
}
```

---

## Verification Checklist

- [x] All line numbers verified against source code
- [x] Function bodies fully read (not assumed from signatures)
- [x] Grep verification performed for critical functions
- [x] Panic messages and error handling reviewed
- [x] Type assertions and interface usage validated
- [x] Header parsing and matching logic examined
- [x] Sibling methods checked for consistency (Hijack, Push, Close all follow same pattern)

## Code Quality Notes

**Positive aspects:**
- Clear documentation comments
- Proper use of sync.Pool for encoder reuse
- Good separation of concerns (Compressor vs. compressResponseWriter)
- Correct wildcard type matching logic (despite misleading message)
- Proper cleanup with defer

**Areas for improvement:**
- Accept-Encoding header parsing needs RFC-compliant token matching
- Error messages could be more precise about supported patterns
- Type assertions could include explicit error handling
- Flush logic could be optimized to avoid redundant calls

---

## Files That Need Testing

Test the following scenarios to verify the bug:

1. **Accept-Encoding header with custom encodings containing standard encoding names**
   - Test: `Accept-Encoding: x-gzip` should NOT activate gzip compression
   - Test: `Accept-Encoding: gzip-custom` should NOT activate gzip compression
   - Test: `Accept-Encoding: gzip` should activate gzip compression

2. **Wildcard content type registration**
   - Test: `NewCompressor(5, "text/*")` should not panic
   - Test: `NewCompressor(5, "text*html")` should panic with misleading message

3. **Flush behavior with dual-interface writers**
   - Verify that writers implementing both Flusher and compressFlusher are only flushed once

---

**Report generated:** 2026-03-31
**Reviewer notes:** The critical bug in Accept-Encoding matching could cause incorrect compression behavior in production. Recommend immediate fix using proper token-based header parsing.
