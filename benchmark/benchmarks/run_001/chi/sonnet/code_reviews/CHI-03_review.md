# Code Review: CHI-03

**File reviewed:** `middleware/compress.go`
**Date:** 2026-03-31

---

## middleware/compress.go

### Finding 1 — BUG | High

**Line 244–246:** `matchAcceptEncoding` uses `strings.Contains` and does not parse RFC 7231 quality values. A `q=0` token explicitly means the encoding is NOT acceptable (RFC 7231 §5.3.4), but `strings.Contains("gzip;q=0", "gzip")` returns `true`, so the middleware will compress with gzip even when the client has refused it.

```go
func matchAcceptEncoding(accepted []string, encoding string) bool {
    for _, v := range accepted {
        if strings.Contains(v, encoding) {  // BUG: matches "gzip;q=0"
            return true
        }
    }
    return false
}
```

**Expected:** `Accept-Encoding: gzip;q=0` should cause gzip to be skipped; another acceptable encoding or no compression should be used.
**Actual:** gzip is selected and the response is encoded against the client's explicit refusal.
**Why it matters:** Sending a compressed body when `q=0` was declared can cause clients (or intermediaries that honour the header) to fail to decompress the response, producing garbled output.

---

### Finding 2 — BUG | Medium

**Line 244–246:** `matchAcceptEncoding` uses `strings.Contains(v, encoding)` as a substring test, which is not the correct way to match an Accept-Encoding token. Two concrete failure modes:

1. **`Accept-Encoding: *`** — the RFC wildcard meaning "any encoding is acceptable". `strings.Contains("*", "gzip")` is `false`, so the middleware never compresses for a client that sends only `*`. The wildcard is silently ignored.

2. **False-positive substring match** — if an encoder with a short name (e.g. hypothetical `"br"`) is registered, `strings.Contains("brotli", "br")` is `true`, so it spuriously matches a completely different token.

**Expected:** Token matching should compare the encoding name against the accepted token stripped of parameters (i.e. split on `;`, trim whitespace, compare case-insensitively).
**Actual:** Substring containment is used; `*` is not recognised; short encoder names can match inside longer token names.
**Why it matters:** Clients sending `Accept-Encoding: *` receive uncompressed responses even though they explicitly declared all encodings acceptable.

---

### Finding 3 — BUG | Low

**Lines 10, 163, 168:** `io/ioutil` is imported and `ioutil.Discard` is used in two places. The package was deprecated in Go 1.16; the direct replacement is `io.Discard`. The project already performed a project-wide cleanup (commit `a36a925 Remove last uses of io/ioutil`) but this file was not updated.

```go
import "io/ioutil"          // line 10  — should be removed
...
encoder := fn(ioutil.Discard, c.level)  // line 163 — should be io.Discard
...
return fn(ioutil.Discard, c.level)      // line 168 — should be io.Discard
```

**Expected:** `io.Discard` from the standard `io` package.
**Actual:** `ioutil.Discard` from the deprecated `io/ioutil` package.
**Why it matters:** The project's stated goal (commit a36a925) was to remove all `io/ioutil` uses; this file defeats that goal and will produce deprecation linter warnings.

---

### Finding 4 — QUESTION | Medium

**Lines 297–299:** When `cw.wroteHeader` is already `true`, a second call to `WriteHeader(code)` is forwarded directly to the underlying `cw.ResponseWriter.WriteHeader(code)`. Go's `net/http` ignores all but the first `WriteHeader` call on the real writer, but it also logs a "http: superfluous response.WriteHeader call" warning to stderr for every extra call.

```go
if cw.wroteHeader {
    cw.ResponseWriter.WriteHeader(code) // Allow multiple calls to propagate.
    return
}
```

**Question:** Is it intentional to forward duplicate WriteHeader calls to the underlying writer (triggering net/http warnings), rather than silently dropping them? If the purpose is introspection by an outer middleware that wraps the compressResponseWriter, the comment "Allow multiple calls to propagate" suggests it is intentional, but this is worth confirming because it diverges from the usual chi middleware pattern of absorbing duplicate calls.

---

### Finding 5 — QUESTION | Low

**Lines 343–357:** `Flush()` has two successive type-assertion branches on `cw.writer()`. If the underlying writer implements **both** `http.Flusher` (method `Flush()`) and `compressFlusher` (method `Flush() error`), both branches fire and the writer's flush method is invoked twice.

```go
func (cw *compressResponseWriter) Flush() {
    if f, ok := cw.writer().(http.Flusher); ok {
        f.Flush()                          // first flush
    }
    if f, ok := cw.writer().(compressFlusher); ok {
        f.Flush()                          // second flush if writer satisfies both
        if f, ok := cw.ResponseWriter.(http.Flusher); ok {
            f.Flush()
        }
    }
}
```

In practice, the standard `gzip.Writer` implements only `compressFlusher`, so the first branch does not fire for compressed responses. However, for a custom encoder that satisfies both interfaces, the double-flush would be a bug. **Question:** Is this double-flush case considered impossible by design (i.e., no registered encoder should implement `http.Flusher`)?

---

## Summary

| # | Type     | Severity | Description                                              |
|---|----------|----------|----------------------------------------------------------|
| 1 | BUG      | High     | `matchAcceptEncoding`: `q=0` not honoured (line 244–246) |
| 2 | BUG      | Medium   | `matchAcceptEncoding`: `*` wildcard ignored; substring false positives (line 244–246) |
| 3 | BUG      | Low      | `ioutil.Discard` still used after project-wide removal (lines 10, 163, 168) |
| 4 | QUESTION | Medium   | `WriteHeader`: duplicate calls forwarded to underlying writer (lines 297–299) |
| 5 | QUESTION | Low      | `Flush`: potential double-flush for writers implementing both flusher interfaces (lines 343–357) |

**Bugs:** 3 (1 High, 1 Medium, 1 Low)
**Questions:** 2 (1 Medium, 1 Low)

**Overall assessment: FIX FIRST** — Finding 1 is a protocol-correctness bug that silently violates RFC 7231 and can produce undecodable responses for clients that explicitly refuse an encoding. Finding 2 means `Accept-Encoding: *` clients never get compression. Both are in the same 7-line function and should be fixed together.
