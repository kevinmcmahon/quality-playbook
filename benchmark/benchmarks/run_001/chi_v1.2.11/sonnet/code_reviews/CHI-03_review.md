# Code Review: CHI-03 — middleware/compress.go

## middleware/compress.go

---

### Finding 1

- **Finding type:** BUG
- **File:** middleware/compress.go
- **Line:** 245
- **Severity:** High
- **Description:** `matchAcceptEncoding` uses `strings.Contains(v, encoding)` to match Accept-Encoding tokens, but never strips quality values from the token before comparing. Per RFC 7231, `Accept-Encoding: gzip;q=0` means the client explicitly rejects gzip. `strings.Contains("gzip;q=0", "gzip")` returns true, so the middleware still selects gzip encoding and sets `Content-Encoding: gzip` — sending gzip-compressed data to a client that rejected it. The client will attempt to decompress a response it did not request, resulting in a decompression error or a corrupted response body.

---

### Finding 2

- **Finding type:** BUG
- **File:** middleware/compress.go
- **Line:** 245
- **Severity:** Medium
- **Description:** `strings.Contains(v, encoding)` performs substring matching on raw Accept-Encoding token values, which produces false positive matches when an encoding name is a substring of another token string. For example, if a custom encoder is registered under the name `"br"` (Brotli), then a client sending `Accept-Encoding: brotli` causes `strings.Contains("brotli", "br")` to return true, incorrectly selecting the "br" encoder for a different encoding. Similarly, any encoding name that is a strict substring of another accepted encoding name will spuriously match. The correct approach is to split each token on `;`, trim whitespace, and compare the encoding name exactly.

---

### Finding 3

- **Finding type:** BUG
- **File:** middleware/compress.go
- **Lines:** 232–234 (selectEncoder), 202–204 (Handler)
- **Severity:** High
- **Description:** When a non-pooled encoder function is stored in `c.encoders` and the function returns `nil` at request time (e.g., because the compression level passed to `NewCompressor` is invalid — any value outside `flate.HuffmanOnly`..`flate.BestCompression` causes `gzip.NewWriterLevel`/`flate.NewWriter` to return an error), `selectEncoder` still returns `nil, name, func(){}` — a nil encoder alongside a non-empty encoding name.

  In `Handler` (line 202–204), `cw.w` is only updated when `encoder != nil`, so it remains pointing at the raw `http.ResponseWriter`. But `cw.encoding` is set to the non-empty encoding name (e.g., `"gzip"`). Later, in `WriteHeader` (line 314), the guard `if cw.encoding != ""` evaluates to true, so `compressible` is set to true and `Content-Encoding: gzip` is written to the response headers. Subsequent `Write` calls (line 332–336) route through `cw.writer()`, which returns `cw.w` (the raw ResponseWriter) because `compressible == true`. The result is uncompressed data sent to the client under a `Content-Encoding: gzip` claim. Every client receiving this response will fail to decompress it.

  The root cause in `SetEncoder` (line 163–173): if `fn(ioutil.Discard, c.level)` returns nil, the encoder is not placed in `pooledEncoders`, falls through to `c.encoders[encoding] = fn`, and the nil-producing function is stored without any indication that it will fail at every invocation. No validation of the compression level is performed anywhere in `NewCompressor` or `Compress`.

---

### Finding 4

- **Finding type:** BUG
- **File:** middleware/compress.go
- **Lines:** 297–300
- **Severity:** Low
- **Description:** In `WriteHeader`, when `cw.wroteHeader` is already `true`, the method calls `cw.ResponseWriter.WriteHeader(code)` directly on the underlying writer. However, the underlying writer has already had `WriteHeader` committed via the `defer cw.ResponseWriter.WriteHeader(code)` from the first invocation (line 302). Calling `WriteHeader` on an already-committed `http.ResponseWriter` is a no-op that produces a `superfluous response.WriteHeader call` log warning. The comment "Allow multiple calls to propagate" reflects intent, but the underlying writer cannot act on the second call — the status code and headers are already sent. The correct behavior is to silently ignore subsequent calls (or at minimum not forward them to the already-committed underlying writer).

---

### Finding 5

- **Finding type:** QUESTION
- **File:** middleware/compress.go
- **Line:** 207
- **Severity:** Medium
- **Description:** `defer cw.Close()` in `Handler` silently discards the return error. `Close()` on a gzip or deflate writer finalizes the compressed stream by flushing buffered data and writing the format footer (e.g., the gzip CRC32 + size trailer). If this step fails — for example because the client disconnected mid-response — the client receives a truncated compressed stream. The error is swallowed with no logging, no propagation, and no way for the caller to detect it. Whether this is acceptable middleware behavior or a reliability defect depends on project error-handling policy, but the silent drop means operators have no visibility into these failures.

---

## Summary

| Severity | Count |
|----------|-------|
| High     | 2     |
| Medium   | 2     |
| Low      | 1     |

**Overall assessment: FIX FIRST**

Two High findings produce silent data corruption visible to clients:
- Finding 1 compresses responses for clients that explicitly opted out, causing client-side decompression failures.
- Finding 3 sends uncompressed data under a `Content-Encoding` claim when encoder construction fails, corrupting every response for that encoding.

Both are reachable in production: Finding 1 via any RFC-compliant client that uses `q=0` to negotiate encoding, and Finding 3 via any caller that passes an out-of-range compression level.
