# Code Review: middleware/compress.go

## Summary
Reviewed compress.go middleware module. Found 2 critical bugs in encoder selection and matching logic, and 2 questions about edge cases.

---

## Findings

### BUG #1: Nil encoder returned with non-empty encoding name
**File:** middleware/compress.go
**Line:** 233
**Severity:** High

**Issue:**
The `selectEncoder` method returns `fn(w, c.level), name, func() {}` on line 233, where `fn(w, c.level)` can return `nil` (per the EncoderFunc documentation on line 255: "In case of failure, the function should return nil").

When `fn` returns nil:
- Line 192: `encoder, encoding, cleanup := c.selectEncoder(r.Header, w)` receives `(nil, "gzip", func() {})`
- Line 202-203: The nil check `if encoder != nil { cw.w = encoder }` fails, so `cw.w` remains the uncompressed ResponseWriter
- Line 199: But `cw.encoding` is set to the encoding name (e.g., "gzip")
- Line 314-316: In WriteHeader, the check `if cw.encoding != ""` passes, so it sets `cw.compressible = true` and adds the Content-Encoding header
- Line 333-337: In `writer()`, when `cw.compressible` is true, it returns the uncompressed `cw.w`

**Result:** Response is written uncompressed but marked with Content-Encoding header, causing clients to decompress already-uncompressed data.

**Example:**
```
Client receives: Content-Encoding: gzip, but body is uncompressed
Client gzip decoder fails or corrupts the data
```

---

### BUG #2: Loose Accept-Encoding matching allows incorrect encoder selection
**File:** middleware/compress.go
**Line:** 245
**Severity:** High

**Issue:**
The `matchAcceptEncoding` function uses `strings.Contains(v, encoding)` to match encodings. This is too loose because substring matching incorrectly matches:

Example scenario:
- Client sends: `Accept-Encoding: gzip`
- Server has custom encoder registered: `SetEncoder("zip", customFn)`
- `matchAcceptEncoding(["gzip"], "zip")` checks: `strings.Contains("gzip", "zip")` → **true** (last 3 chars match)
- Server uses "zip" encoding even though client didn't request it

The header value "gzip" contains the substring "zip", so the match succeeds incorrectly.

**Result:** Server may use wrong compression algorithm, potentially incompatible with client.

---

### QUESTION #1: Accept-Encoding header parsing doesn't handle q-values
**File:** middleware/compress.go
**Line:** 218
**Severity:** Medium

**Issue:**
Line 218 splits the Accept-Encoding header only by comma:
```go
accepted := strings.Split(strings.ToLower(header), ",")
```

This doesn't handle q-values (quality factors) specified in RFC 7231. Example:
- Client sends: `Accept-Encoding: gzip;q=0.5, deflate;q=1`
- After split: `["gzip;q=0.5", " deflate;q=1"]`
- matchAcceptEncoding tries to match "gzip;q=0.5" which won't exist in the encoders map

Additionally, spaces aren't trimmed, though the loose string matching happens to work around this.

**Question:** Should q-value parsing be implemented to handle client preferences correctly?

---

### QUESTION #2: Range loop modifying slice during iteration
**File:** middleware/compress.go
**Lines:** 179-182
**Severity:** Low

**Issue:**
The SetEncoder method removes an encoding from the precedence list using a range loop that modifies the slice:
```go
for i, v := range c.encodingPrecedence {
    if v == encoding {
        c.encodingPrecedence = append(c.encodingPrecedence[:i], c.encodingPrecedence[i+1:]...)
    }
}
```

While this works for single occurrences (the typical case), the pattern of modifying a slice during a range loop over it is potentially fragile. If the encoding appeared multiple times in the precedence list, only the first would be removed in practice, and the remaining ones might cause unexpected behavior.

**Note:** This is unlikely to cause issues in normal usage since encodings are set once during initialization, but it's a code pattern that could be clearer.

**Question:** Is it intentional that only the first occurrence is removed, or should all occurrences be removed?

---

## Recommendations

1. **Fix BUG #1:** Check if encoder is nil after calling fn, and if so, don't set encoding in selectEncoder:
   ```go
   if fn, ok := c.encoders[name]; ok {
       encoder := fn(w, c.level)
       if encoder != nil {
           return encoder, name, func() {}
       }
   }
   ```

2. **Fix BUG #2:** Use proper Accept-Encoding matching (e.g., trim spaces and check for exact match or implement proper RFC 7231 parsing):
   ```go
   func matchAcceptEncoding(accepted []string, encoding string) bool {
       for _, v := range accepted {
           parts := strings.Split(strings.TrimSpace(v), ";")
           if parts[0] == encoding {
               return true
           }
       }
       return false
   }
   ```

3. **Clarify QUESTION #1:** Decide if q-value support is needed. If so, implement proper parsing.

4. **Improve QUESTION #2:** Either document the behavior or refactor the removal loop for clarity.

---

## Files Reviewed
- middleware/compress.go (lines 1-399)

## Test Recommendations
- Test encoder failure scenarios: what happens when gzip.NewWriterLevel fails
- Test with custom "zip" encoding registered and client sending only "gzip" in Accept-Encoding
- Test with q-values in Accept-Encoding header
