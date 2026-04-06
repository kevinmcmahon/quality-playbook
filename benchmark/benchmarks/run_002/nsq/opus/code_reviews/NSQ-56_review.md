# NSQ-56 Code Review: nsqd/http.go and nsqd/http_test.go

## nsqd/http.go

- **Line 639:** [BUG] Incorrect HTTP status code for empty config body. The condition `int64(len(body)) == readMax || len(body) == 0` returns `http_api.Err{413, "INVALID_VALUE"}` for both cases. HTTP 413 ("Request Entity Too Large") is correct when the body exceeds the size limit, but wrong when the body is empty. An empty body should return HTTP 400 ("Bad Request"). API consumers inspecting status codes will get a misleading "too large" error when the real problem is a missing body. Severity: **Low** — functional impact is limited since the error message is generic, but it violates HTTP semantics.

- **Line 289:** [QUESTION] Binary mode MPUB reads directly from `req.Body` without a `LimitReader`. In text mode (line 298), the body is wrapped with `io.LimitReader(req.Body, readMax)` to enforce `MaxBodySize`. In binary mode, `readMPUB` is called with `req.Body` directly. The `readMPUB` function (protocol_v2.go:1001) calculates `maxMessages = (maxBodySize - 4) / 5`, assuming each message occupies at least 5 bytes (4-byte length + 1-byte body). However, individual messages can be up to `maxMessageSize` bytes. If `maxMessageSize` is much larger than 5 bytes (default 1MB), the actual total bytes read could far exceed `maxBodySize` (default 5MB). For example: `maxMessages ≈ 1M`, each up to 1MB, yields ~1TB of reads. This is mitigated by `req.ContentLength` check on line 270, but `ContentLength` is -1 for chunked/unknown transfer-encoding, bypassing that guard. Severity: **Medium** — could allow memory exhaustion via crafted chunked requests.

- **Line 333:** [QUESTION] `topic.PutMessages(msgs)` is called even when `msgs` may be empty in text mode. If the request body contains only newlines or whitespace, all lines are silently discarded (line 320-322), resulting in an empty `msgs` slice. `PutMessages` with an empty slice succeeds and returns `nil`, so the client receives HTTP 200 "OK" despite publishing zero messages. By contrast, `/pub` returns HTTP 400 "MSG_EMPTY" for empty bodies (line 232). This inconsistency could mask client errors. Severity: **Low** — no data corruption, but misleading success response.

## nsqd/http_test.go

- **Line 256:** [QUESTION] TLS config in `TestHTTPSRequire` sets `MinVersion: 0`, which allows all TLS versions including deprecated TLS 1.0/1.1. While this is test code and doesn't affect production, the explicit `MinVersion: 0` (vs. simply omitting it, which defaults to TLS 1.2 in Go 1.18+) is unusual and may have been intentional to test backward compatibility. The `TestHTTPSRequireVerify` test at line 301 omits `MinVersion` entirely, using the safer Go default. Severity: **Low** — test-only, no production impact.

## Summary

| Severity | Count |
|----------|-------|
| BUG (Low) | 1 |
| QUESTION (Medium) | 1 |
| QUESTION (Low) | 2 |

**Total findings:** 4 (1 BUG, 3 QUESTION)

**Overall assessment:** SHIP IT — The one confirmed bug (wrong HTTP status for empty config body) is low-severity and cosmetic. The binary MPUB memory concern deserves investigation but is partially mitigated by ContentLength checks for non-chunked requests. No data integrity or correctness issues found in the core message publishing paths.
