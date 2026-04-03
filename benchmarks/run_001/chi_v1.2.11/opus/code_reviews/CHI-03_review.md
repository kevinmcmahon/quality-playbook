# CHI-03 Code Review: middleware/compress.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-03-31
**File reviewed:** `/tmp/qpb_v1211_opus_CHI-03/middleware/compress.go`

---

## Findings

### middleware/compress.go

- **Line 245:** [BUG] **Severity: High.** `matchAcceptEncoding` uses `strings.Contains(v, encoding)` for matching, which is a substring match. This has two consequences:
  1. **`q=0` is ignored.** Per RFC 9110 Section 12.5.3, `Accept-Encoding: gzip;q=0` means the client explicitly refuses gzip. The current code splits by `,` yielding `"gzip;q=0"`, and `strings.Contains("gzip;q=0", "gzip")` returns `true`, so the server sends gzip-compressed responses to clients that explicitly rejected gzip. This can cause decode failures on the client.
  2. **False substring matches.** Any encoding whose name is a substring of another accepted encoding or its parameters will match incorrectly. For example, an encoding named `"br"` would match the string `"sbr-custom"` if such an encoding ever appeared. While unlikely with current standard encodings, this is still incorrect matching logic.

  **Expected:** Parse quality values properly; only match when the encoding name is the full token (before any `;` parameters), and respect `q=0` as a rejection.

- **Line 360:** [BUG] **Severity: Medium.** `Hijack()` checks `cw.writer()` for the `http.Hijacker` interface. When compression is active (`compressible == true`), `cw.writer()` returns the gzip/deflate encoder, which never implements `http.Hijacker`. This means `Hijack()` always fails when compression headers have been written, even if the underlying `ResponseWriter` supports hijacking. Compare with `wrap_writer.go:138,156,178` which correctly always delegates to `ResponseWriter`. The fix is to check `cw.ResponseWriter` instead of `cw.writer()`.

- **Line 367:** [BUG] **Severity: Medium.** `Push()` has the same incorrect delegation as `Hijack()`. It checks `cw.writer()` for `http.Pusher`, but compression encoders never implement `http.Pusher`. Should delegate to `cw.ResponseWriter`. Same pattern as the Hijack bug above.

- **Line 218:** [BUG] **Severity: Low.** `Accept-Encoding` header parsing splits by `","` and lowercases, but does not `strings.TrimSpace` each element. A standard `Accept-Encoding: gzip, deflate` header produces `["gzip", " deflate"]` (note leading space). The `strings.Contains` on line 245 happens to still work because `" deflate"` contains `"deflate"`, but this is accidental correctness. If the matching logic were ever fixed to use exact token matching (as it should be per the line 245 finding), this lack of trimming would cause failures for all encodings after the first.

- **Line 179-182:** [BUG] **Severity: Low.** The loop that removes a duplicate encoding from `encodingPrecedence` does not `break` after finding the match. After the `append` modifies the slice in-place, the loop continues iterating with the same index `i`, potentially skipping the element that shifted into position `i`. In practice this only matters if `encodingPrecedence` contained duplicates (which shouldn't happen given the function's own logic), but it's still incorrect iteration over a mutating slice.

  ```go
  for i, v := range c.encodingPrecedence {
      if v == encoding {
          c.encodingPrecedence = append(c.encodingPrecedence[:i], c.encodingPrecedence[i+1:]...)
          // BUG: missing break; next iteration skips an element
      }
  }
  ```

- **Line 71-73:** [QUESTION] **Severity: Low.** The wildcard validation rejects `*/*` (all content types) because after trimming the `/*` suffix, `*` still contains `*`. Is this intentional? `*/*` is a valid media range per RFC 9110 and a user might reasonably pass it to mean "compress everything." If intentional, the panic message should mention that `*/*` is not supported. If unintentional, this is a bug.

- **Line 226-229:** [QUESTION] **Severity: Low.** When a pooled encoder is returned to the pool via `cleanup()` (line 225-227), it still holds a reference to the just-completed request's `http.ResponseWriter` (set by `encoder.Reset(w)` on line 228). This reference persists until the encoder is next retrieved from the pool and `Reset()` is called with a new writer. Under low traffic, this could prevent the old `ResponseWriter` (and its associated buffers) from being garbage collected. Standard practice for sync.Pool encoders is to `Reset(nil)` or `Reset(ioutil.Discard)` before returning to the pool.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 1     |
| Medium   | 2     |
| Low      | 2     |
| QUESTION | 2     |
| **Total**| **7** |

### Key Findings
1. **matchAcceptEncoding substring matching (High)** — Ignores `q=0` quality values and uses loose substring matching, violating RFC 9110. Clients that explicitly refuse an encoding may receive it anyway.
2. **Hijack/Push delegate to wrong writer (Medium x2)** — Both methods check the compression encoder for HTTP interfaces instead of the underlying ResponseWriter, causing them to always fail when compression is active.

### Files with no findings
N/A (single file review)

### Overall Assessment
**FIX FIRST** — The `matchAcceptEncoding` bug (line 245) violates HTTP semantics by ignoring `q=0` and could cause client-side decode failures. The Hijack/Push delegation bugs break WebSocket upgrades and HTTP/2 push when the compress middleware is in the chain. These should be fixed before shipping.
