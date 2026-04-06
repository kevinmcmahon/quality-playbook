# Code Review: middleware/compress.go

## Findings

### middleware/compress.go

- **Line 233:** [BUG] **Severity: High.** `selectEncoder` can return a non-empty `encoding` name with a `nil` encoder. When a non-pooled `EncoderFunc` returns `nil` (e.g., invalid compression level), line 233 returns `fn(w, c.level), name, func(){}` — i.e., `nil, "gzip", noop`. Back in `Handler` (line 202), `encoder` is nil so `cw.w` stays as the raw `ResponseWriter`, but `cw.encoding` is `"gzip"`. In `WriteHeader` (line 314–316), `cw.encoding != ""` is true, so `compressible` is set to `true`, `Content-Encoding: gzip` is written, and `Content-Length` is deleted. The response body is then written uncompressed through the raw `ResponseWriter`, but the client believes it is gzip-encoded and will fail to decode it. **Expected:** Either validate the compression level upfront (reject invalid levels in `NewCompressor`), or check for a nil encoder return before setting the encoding name. **Impact:** Corrupted/unreadable HTTP responses for every request when an invalid compression level is used.

- **Line 245:** [BUG] **Severity: Medium.** `matchAcceptEncoding` uses `strings.Contains(v, encoding)` for matching, which is a substring check rather than a proper token match. This causes two problems: (1) An `Accept-Encoding` value of `gzip;q=0` (quality zero = explicitly rejected) will match `"gzip"` because the string contains the substring, violating RFC 7231 §5.3.4. The middleware will compress with an encoding the client explicitly refused. (2) A hypothetical encoding name that is a substring of another could false-match (e.g., encoding `"br"` would match an accepted value of `"sbr"`). **Expected:** Parse each accepted value by trimming whitespace and splitting on `;` to extract the encoding token, then compare the token exactly. Also respect `q=0` to mean "not accepted." **Impact:** Responses compressed with an encoding the client explicitly rejected, causing decode failures.

- **Line 360:** [BUG] **Severity: Medium.** `Hijack()` delegates to `cw.writer()` which, when compression is active (`cw.compressible == true`), returns the gzip/deflate encoder — not the underlying `http.ResponseWriter`. Compression encoders (gzip.Writer, flate.Writer) do not implement `http.Hijacker`, so `Hijack()` will always fail with an error when the response is compressible. It should check `cw.ResponseWriter.(http.Hijacker)` instead, since the hijack capability belongs to the underlying connection, not the compression layer. **Expected:** `if hj, ok := cw.ResponseWriter.(http.Hijacker); ok { return hj.Hijack() }`. **Impact:** WebSocket upgrades and other connection hijacks fail for any response that would be compressed.

- **Line 367:** [BUG] **Severity: Low.** Same issue as Hijack: `Push()` delegates to `cw.writer()` instead of `cw.ResponseWriter`. The `http.Pusher` interface is implemented by the HTTP/2 server's ResponseWriter, not by compression encoders. When compression is active, `Push()` will always return an error. **Expected:** Check `cw.ResponseWriter.(http.Pusher)` instead. **Impact:** HTTP/2 Server Push is broken for compressible responses. (Note: HTTP/2 Push is deprecated in most browsers, reducing practical severity.)

- **Line 10:** [QUESTION] **Severity: Low.** `io/ioutil` is imported and used at lines 163, 168–169. The `ioutil` package has been deprecated since Go 1.16 in favor of `io.Discard`. Given the project recently bumped the minimum Go version to 1.23 (commit a54874f), this import is stale. The recent commit a36a925 ("Remove last uses of io/ioutil") apparently missed this file. Not a correctness bug — `ioutil.Discard` still works — but inconsistent with the stated project cleanup.

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 1     |
| Medium   | 2     |
| Low      | 2     |

- **Total findings:** 5 (4 BUG, 1 QUESTION)
- **Files with no findings:** N/A (single file review)
- **Overall assessment:** **FIX FIRST** — The nil-encoder-with-encoding-name bug (line 233) can produce corrupted HTTP responses. The Hijack delegation bug (line 360) breaks WebSocket upgrades through compressed endpoints. The `matchAcceptEncoding` substring matching (line 245) violates HTTP content negotiation semantics. These should be addressed before shipping.
