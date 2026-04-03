# Code Review: middleware/compress.go

## Findings

### middleware/compress.go

- **Line 365: [BUG] Hijack() delegates to compression writer instead of underlying ResponseWriter.** Severity: **High**. `cw.writer()` returns the gzip/flate encoder when `compressable` is true. Compression encoders do not implement `http.Hijacker`, so this type assertion always fails when compression is active, making Hijack unusable. The method should check `cw.ResponseWriter.(http.Hijacker)` instead, as `wrap_writer.go` does in similar wrappers. Compare with `wrap_writer.go:139`, `wrap_writer.go:157`, `wrap_writer.go:179` — all correctly delegate Hijack to `f.basicWriter.ResponseWriter`.

- **Line 372: [BUG] Push() delegates to compression writer instead of underlying ResponseWriter.** Severity: **High**. Same issue as Hijack. `cw.writer()` returns the encoder, which does not implement `http.Pusher`. Push should check `cw.ResponseWriter.(http.Pusher)` instead to reach the actual HTTP/2 connection.

- **Line 249: [BUG] matchAcceptEncoding uses substring matching instead of token matching.** Severity: **Medium**. `strings.Contains(v, encoding)` performs a substring check, which can produce false-positive matches. For example, an encoder named `"br"` would incorrectly match an Accept-Encoding value of `"brotli"`, and `"gzip"` would match `"x-gzip"`. Per RFC 7231, Accept-Encoding values are tokens that should be compared as whole values (after trimming whitespace and stripping quality parameters), not as substrings.

- **Line 183-186: [BUG] Slice modified during range iteration without break.** Severity: **Low**. When removing a duplicate encoding from `c.encodingPrecedence`, the slice is mutated via `append([:i], [i+1:]...)` inside a `range` loop, but the loop does not `break` after removal. In Go, `range` captures the original slice length at loop entry. After the removal shifts elements left, the loop continues iterating with stale indices: it skips the element that shifted into position `i`, and on the final iteration reads a duplicate trailing element from the original backing array. Although in practice there should only be one occurrence (since `SetEncoder` removes before adding), the missing `break` makes this fragile and can corrupt the slice if a duplicate somehow exists.

- **Lines 348-361: [QUESTION] Flush() may double-flush custom encoders.** Severity: **Low**. The method first checks if the writer implements `http.Flusher` (line 349) and flushes, then independently checks for `compressFlusher` (line 354) and flushes again. If a custom encoder implements both interfaces (i.e., has both `Flush()` and `Flush() error`), it would be flushed twice. The built-in gzip/flate writers only implement `Flush() error` so this doesn't affect them, but it could affect user-registered encoders via `SetEncoder`.

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 2     |
| Medium   | 1     |
| Low      | 2     |

**Total findings:** 5

**Overall assessment:** **FIX FIRST** — The Hijack and Push delegation bugs (lines 365, 372) mean these HTTP features are broken whenever compression is active. The substring matching in `matchAcceptEncoding` (line 249) is a correctness issue that could cause unexpected encoder selection.
