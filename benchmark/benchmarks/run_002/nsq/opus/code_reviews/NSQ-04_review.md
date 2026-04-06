# NSQ-04 Code Review: nsqd/nsqd.go and nsqd/tcp.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Files reviewed:** `nsqd/nsqd.go`, `nsqd/tcp.go`

---

## nsqd/nsqd.go

### Finding 1

- **Line 82:** **BUG** — Severity: Medium
- `os.Getwd()` error is silently discarded with `cwd, _ := os.Getwd()`. If `Getwd` fails (e.g., current directory has been deleted), `cwd` is an empty string, making `dataPath` empty. This propagates to `dirlock.New("")` (line 96) and `newMetadataFile` (line 315), causing the directory lock to target an invalid path and metadata to be written to an unintended location. Expected: the error should be checked and returned. Actual: error is silently ignored.

### Finding 2

- **Lines 389–393:** **QUESTION** — Severity: Medium
- `GetMetadata` iterates `n.topicMap` (line 393) without acquiring `n.RLock()`. All current callers within this file hold `n.Lock()` before calling (`PersistMetadata` from `Exit` at line 464 and `Notify` at line 590; HTTP handlers at `http.go:424` and `http.go:495` also hold the lock). However, `GetMetadata` is an exported public method with no documentation requiring the caller to hold the lock. A future caller without the lock would cause a data race on map iteration, which is undefined behavior in Go and can crash the process. Is the lack of internal locking intentional (caller-must-lock pattern), or should `GetMetadata` acquire `n.RLock()` itself?

### Finding 3

- **Lines 737, 749:** **QUESTION** — Severity: Low
- In `buildTLSConfig`, the variable `tlsClientAuthPolicy` is initialized to `tls.VerifyClientCertIfGiven` at line 737, but this value is dead code — it is unconditionally overwritten by the `switch` statement (lines 743–750). The `default` case (line 749) silently sets `tls.NoClientCert` for any unrecognized `TLSClientAuthPolicy` string. This means a configuration typo (e.g., `"requir"` instead of `"require"`) silently disables client certificate verification with no warning, which is a security-sensitive silent failure. Expected: unrecognized values should produce an error or warning. Actual: silent downgrade to no client cert.

### Finding 4

- **Line 339:** **QUESTION** — Severity: Low
- `writeSyncFile` calls `f.Close()` but ignores its return value. On certain filesystems (especially NFS), `Close()` can return errors indicating data was not flushed. Since `f.Sync()` is called immediately before (line 337), this is likely safe for local filesystems. However, formally the close error could indicate data loss for the temp file used in `PersistMetadata`. Is this an acceptable trade-off?

---

## nsqd/tcp.go

### Finding 5

- **Lines 64–65:** **QUESTION** — Severity: Low
- In `Handle`, `p.conns.Delete(conn.RemoteAddr())` is called before `client.Close()`. If `tcpServer.Close()` (lines 68–73) runs concurrently between these two lines, it will not see this client in the `conns` map, and `client.Close()` has not yet been called. Since `prot.IOLoop` has already returned (meaning the client protocol handler has finished), and `net.Conn.Close()` is idempotent, this is safe in practice. However, the ordering is inverted from the expected "close first, then remove from tracking map" pattern. Was this ordering intentional?

### Finding 6

- **Lines 65, 69–72:** **QUESTION** — Severity: Low
- `client.Close()` can be called twice on the same client: once by `tcpServer.Close()` (line 70, during shutdown) which iterates `p.conns` and calls `Close()` on all clients, and once by `Handle()` (line 65) after `IOLoop` returns. The `clientV2` type embeds `net.Conn` (client_v2.go:153), so `Close()` is `net.Conn.Close()`, which is safe to call multiple times (second call returns error). This works correctly but relies on the implicit idempotency of `net.Conn.Close()` rather than explicit once-guard logic. Is the double-close intentional?

---

## Summary

| Severity | BUG | QUESTION |
|----------|-----|----------|
| Medium   | 1   | 1        |
| Low      | 0   | 4        |
| **Total**| **1** | **5**  |

### Findings by file
- **nsqd/nsqd.go:** 1 BUG, 3 QUESTION
- **nsqd/tcp.go:** 0 BUG, 2 QUESTION

### Overall assessment: **NEEDS DISCUSSION**

The one BUG (ignored `os.Getwd()` error) is a real defect but low probability in practice — the current directory being deleted while `nsqd` starts is unusual. The QUESTION findings around `GetMetadata` missing internal locking (relying on callers) and the silent TLS policy downgrade are worth discussing with maintainers, as they represent latent risks that could manifest as data races or security misconfigurations.
