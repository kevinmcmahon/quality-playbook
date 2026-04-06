# Code Review: CHI-14 — middleware/compress.go

## middleware/compress.go

### Finding 1

- **Finding type:** BUG
- **File and line:** `middleware/compress.go:247–253`
- **Severity:** Medium

**Description:** `matchAcceptEncoding` uses `strings.Contains` to match Accept-Encoding tokens, which does not parse quality values (`q=0`). RFC 7231 §5.3.4 specifies that `q=0` means the encoding is explicitly **not acceptable**. When a client sends `Accept-Encoding: gzip;q=0`, `strings.Contains("gzip;q=0", "gzip")` returns `true`, so the server incorrectly selects gzip compression despite the client explicitly rejecting it. The client will receive a gzip-encoded body it may not be able to decompress.

**Expected:** A token of `gzip;q=0` must NOT match the `"gzip"` encoder.
**Actual:** `strings.Contains("gzip;q=0", "gzip")` → `true`; gzip selected.

```go
// line 247–253
func matchAcceptEncoding(accepted []string, encoding string) bool {
    for _, v := range accepted {
        if strings.Contains(v, encoding) {  // BUG: matches "gzip;q=0"
            return true
        }
    }
    return false
}
```

---

### Finding 2

- **Finding type:** BUG
- **File and line:** `middleware/compress.go:236–237`
- **Severity:** High

**Description:** In `selectEncoder`, when a registered `EncoderFunc` is stored in `c.encoders` (not pooled) and returns `nil` at request time, the function returns `(nil, name, func(){})` where `name` is the non-empty encoding string (e.g., `"gzip"`). This path is reached whenever `SetEncoder` registers an encoder whose probe call (`fn(ioutil.Discard, c.level)`) returns `nil` — which occurs for the standard gzip/deflate encoders when an invalid compression level is passed (e.g., `NewCompressor(10, ...)` since `gzip.NewWriterLevel` rejects levels > 9). Because the probe returns `nil`, the encoder is not added to `pooledEncoders` (line 169–175), but it IS added to `c.encoders` (line 180).

At request time, `fn(w, c.level)` is called again (line 237), returns `nil`, and `selectEncoder` returns `(nil, "gzip", func(){})`. Back in `Handler` (line 206–208), since `encoder == nil`, `cw.w` is left as the raw `ResponseWriter`. However, `encoding = "gzip"` is non-empty, so `WriteHeader` (line 318–320) sets `Content-Encoding: gzip` and marks `cw.compressable = true`. Because `compressable` is true, `writer()` returns `cw.w` (line 337–338), which is the plain `ResponseWriter` — not a compression encoder. The response body is written **uncompressed** while the header claims `Content-Encoding: gzip`. The client will attempt gzip decompression of raw data and fail.

**Expected:** When the encoder function returns `nil` at request time, `selectEncoder` should return `("", "", func(){})` (no encoding), or `SetEncoder` should detect and reject a probe-nil encoder function at registration time.
**Actual:** `selectEncoder` returns `(nil, "gzip", func(){})` → `WriteHeader` sets `Content-Encoding: gzip` → response body written uncompressed.

```go
// line 236–237 (selectEncoder)
if fn, ok := c.encoders[name]; ok {
    return fn(w, c.level), name, func() {}  // BUG: fn() can return nil; name is still returned
}
```

```go
// line 167–180 (SetEncoder — how the nil encoder ends up in c.encoders)
encoder := fn(ioutil.Discard, c.level)
if encoder != nil {                          // skipped when fn returns nil
    if _, ok := encoder.(ioResetterWriter); ok {
        // ... add to pooledEncoders
    }
}
if _, ok := c.pooledEncoders[encoding]; !ok {
    c.encoders[encoding] = fn               // fn (returning nil) still registered here
}
```

---

## Summary

| Severity | Count |
|----------|-------|
| High     | 1     |
| Medium   | 1     |
| Low      | 0     |

| Type       | Count |
|------------|-------|
| BUG        | 2     |
| QUESTION   | 0     |
| SUGGESTION | 0     |

**Overall assessment: FIX FIRST**

Both findings involve `selectEncoder` returning a non-empty encoding name in situations where compression either should not be applied (q=0) or will produce a malformed response (nil encoder with Content-Encoding header set). Finding 2 can cause client-side decompression failures for any server using `NewCompressor` with an out-of-range compression level.
