# NSQ-56 Code Review: nsqd/http.go and nsqd/http_test.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Focus Areas:** 9 (Configuration Parameter Validation), 10 (Input Validation Failure Modes), 11 (Exit Path Resource Completeness), 12 (Go Channel Lifecycle in Select Statements)

---

## nsqd/http.go

### Finding 1
- **Line 279-285:** [QUESTION] **Medium** — Unrecognized `binary` parameter values silently default to `true`. When `binary` param is present but its value is not in `boolParams` (e.g., `binary=yes`, `binary=maybe`), the code sets `binaryMode = true` and logs a deprecation warning. This means any typo or unexpected value for the `binary` parameter is treated as `true`, which changes the parsing mode from text (newline-delimited) to binary (length-prefixed). A user who mistakenly sends `binary=false_please` would get binary parsing mode, likely causing a parse failure or corrupt message ingestion. Per Focus Area 9.2, semantic boolean parameters should reject unrecognized values rather than treating them as truthy. However, this is documented as intentional deprecated behavior — flagging as QUESTION rather than BUG.

### Finding 2
- **Line 292:** [BUG] **Medium** — Unchecked type assertion `err.(*protocol.FatalClientErr)` will panic if `readMPUB` ever returns an error that is not a `*protocol.FatalClientErr`. Currently all error paths in `readMPUB` (protocol_v2.go:994-1034) wrap errors with `protocol.NewFatalClientErr`, so this is safe **today**. However, this is a latent panic: any future change to `readMPUB` that returns a different error type (e.g., a raw `io.ErrUnexpectedEOF` leaking through) will cause a nil-pointer dereference panic in the HTTP handler. A safe type assertion (`fce, ok := err.(*protocol.FatalClientErr)`) should be used. Flagging as BUG because a panic in an HTTP handler crashes the request goroutine and can leak resources.

### Finding 3
- **Line 333:** [BUG] **Medium** — `doMPUB` text mode can call `topic.PutMessages(msgs)` with a nil/empty `msgs` slice. If the request body consists entirely of empty lines (e.g., `\n\n\n`), the loop on lines 300-330 will skip all blocks (line 320-322 `continue` on zero-length), resulting in `msgs` remaining `nil`. `PutMessages` (topic.go:196) will then execute with an empty slice: it acquires an RLock, iterates zero messages, and calls `atomic.AddUint64(&t.messageCount, 0)` — a no-op. While this doesn't crash, it returns `"OK"` to the client, falsely indicating messages were published when zero messages were actually enqueued. The handler should check `len(msgs) == 0` and return a 400 error.

### Finding 4
- **Line 217-218:** [QUESTION] **Low** — `doPUB` checks `req.ContentLength > MaxMsgSize` before reading the body. When `ContentLength` is -1 (chunked transfer encoding), this check passes (since -1 is not > MaxMsgSize), and the handler falls through to `LimitReader` on line 224 which correctly enforces the size limit. This is safe but worth noting: the `ContentLength` pre-check provides no protection for chunked requests. The TODO comment on line 214-215 acknowledges this.

### Finding 5
- **Line 270:** [QUESTION] **Low** — Same chunked transfer encoding concern for `doMPUB`. When `ContentLength` is -1, the check `req.ContentLength > MaxBodySize` passes. For binary mode (line 287-292), the body is read through `req.Body` directly without any size limiter — `readMPUB` reads individual messages up to `maxMessageSize` and caps total message count via `maxMessages` calculation, but the raw stream from `req.Body` is not wrapped in a `LimitReader`. A malicious client could send a very large body in binary mode with chunked encoding that exceeds `MaxBodySize`. For text mode (line 297-298), a `LimitReader` is correctly applied.

### Finding 6
- **Line 634:** [QUESTION] **Low** — `doConfig` PUT handler uses `MaxMsgSize` as the read limit for config body values. Config values (like `nsqlookupd_tcp_addresses` which is a JSON array of addresses) could theoretically exceed `MaxMsgSize` (default 1MB). This is unlikely to be a practical issue since config values are small, but it's a semantic mismatch — config body size is being limited by a message-size parameter.

### Finding 7
- **Line 643:** [QUESTION] **Low** — `doConfig` copies opts with `opts := *s.nsqd.getOpts()` (shallow copy), modifies, and swaps. For `NSQLookupdTCPAddresses` (a string slice), `json.Unmarshal` replaces the slice pointer, so no aliasing issue. This is safe but worth noting: if a field were a map or pointer type, the shallow copy would create aliased state.

---

## nsqd/http_test.go

### Finding 8
- **Line 256-257:** [QUESTION] **Low** — `TestHTTPSRequire` sets `MinVersion: 0` in `tls.Config`, which means TLS 1.0 is the minimum. This is a test-only concern and doesn't affect production code, but accepting TLS 1.0 in tests may mask compatibility issues if the server enforces a minimum TLS version. Not a correctness bug.

### Finding 9
- **Line 906-937:** [QUESTION] **Low** — `BenchmarkHTTPpub` does not call `defer nsqd.Exit()` in the deferred cleanup path — it calls `nsqd.Exit()` at line 937 after `wg.Wait()` and `b.StopTimer()`. If the benchmark panics between `mustStartNSQD` and line 937, the nsqd instance leaks. However, `defer os.RemoveAll(opts.DataPath)` is also missing. The benchmark does have `defer os.RemoveAll(opts.DataPath)` on line 905 but no `defer nsqd.Exit()`. Compare with all other test functions which use `defer nsqd.Exit()`. This is a minor test hygiene issue — if the benchmark panics, the nsqd goroutines leak until process exit.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 0     |
| Medium   | 3 (Findings 1, 2, 3) |
| Low      | 6 (Findings 4, 5, 6, 7, 8, 9) |

| Type     | Count |
|----------|-------|
| BUG      | 2 (Findings 2, 3) |
| QUESTION | 7 (Findings 1, 4, 5, 6, 7, 8, 9) |

**Overall Assessment: NEEDS DISCUSSION**

The two BUG findings are:
1. **Unsafe type assertion (line 292)** — latent panic if `readMPUB` error types change. Currently safe but fragile.
2. **Empty MPUB text mode (line 333)** — returns "OK" when zero messages are published from an all-empty-lines body.

Neither is a data-loss or crash bug in the current code path, but both represent correctness gaps that could manifest under edge-case inputs or future code changes. The binary-mode missing `LimitReader` (Finding 5) deserves investigation but is mitigated by the per-message size checks within `readMPUB`.
