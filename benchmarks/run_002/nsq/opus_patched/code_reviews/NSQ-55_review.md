# NSQ-55 Code Review: nsqd/protocol_v2.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Source:** /tmp/qpb_wt_retest_NSQ-55/nsqd/protocol_v2.go
**Focus Areas:** 9 (Configuration Parameter Validation), 10 (Input Validation Failure Modes), 11 (Exit Path Resource Completeness), 12 (Go Channel Lifecycle in Select Statements)

---

## nsqd/protocol_v2.go

### BUG — DeflateLevel drops client-requested positive values (Focus Area 9: Branch Completeness)

- **Lines 366–371**
- **Severity: High**

```go
deflateLevel := 0
if deflate {
    if identifyData.DeflateLevel <= 0 {
        deflateLevel = 6
    }
    deflateLevel = int(math.Min(float64(deflateLevel), float64(p.context.nsqd.options.MaxDeflateLevel)))
}
```

When the client sends a positive `DeflateLevel` (e.g., 3), the inner `if` on line 368 is false, so `deflateLevel` stays at its zero-value `0`. Line 371 then computes `min(0, MaxDeflateLevel)` = `0`. The client requested level 3 but gets level 0 (no compression).

The `else` branch that assigns `deflateLevel = identifyData.DeflateLevel` is missing. Only the default path (client sends 0 or negative → use 6) works correctly.

**Expected:** Client-requested positive deflate levels are honored (clamped to MaxDeflateLevel).
**Actual:** Any positive client-requested deflate level is silently replaced with 0.

---

### BUG — IDENTIFY response echoes server-default MsgTimeout, not negotiated value (Focus Area 10: Response Field Mapping)

- **Line 394**
- **Severity: Medium**

```go
MsgTimeout: int64(p.context.nsqd.options.MsgTimeout / time.Millisecond),
```

The IDENTIFY response always returns the server's default `MsgTimeout` regardless of what the client negotiated. If the client sends `msg_timeout: 5000` in IDENTIFY, the `client.Identify()` call on line 354 updates the client's MsgTimeout, but the response struct on line 394 reads from `p.context.nsqd.options.MsgTimeout` (the server default, typically 60000ms).

**Expected:** Response `msg_timeout` field reflects the negotiated client value (`client.MsgTimeout`).
**Actual:** Response always echoes the server default, misleading clients about the active timeout.

---

### BUG — Unsafe pointer cast without message ID length validation (Focus Area 10)

- **Lines 535, 557, 695**
- **Severity: Medium**

```go
id := *(*MessageID)(unsafe.Pointer(&params[1][0]))
```

FIN (line 535), REQ (line 557), and TOUCH (line 695) all cast `params[1]` to `MessageID` via unsafe pointer without verifying that `len(params[1]) >= len(MessageID)` (16 bytes). If a client sends a short message ID (e.g., 1 byte), this reads beyond the slice's backing array, causing undefined behavior (out-of-bounds memory read, potential crash).

The parameter count check (`len(params) < 2`) only ensures the parameter exists, not that it has sufficient length.

**Expected:** Validate `len(params[1]) >= MessageIDLength` before the unsafe cast.
**Actual:** Any short param[1] causes an out-of-bounds memory read.

---

### QUESTION — SUB does not check AddClient error return

- **Line 480**
- **Severity: Low**

```go
channel.AddClient(client.ID, client)
```

The return value of `AddClient` is not captured or checked. Per Focus Area 10 (error propagation through layers), if `AddClient` can return an error, it should be propagated. If `AddClient` cannot fail (returns no error), this is not a bug.

---

### QUESTION — REQ timeout out-of-range is FatalClientErr — should it clamp instead? (Focus Area 10: Clamp vs. Disconnect)

- **Lines 565–568**
- **Severity: Low**

```go
if timeoutDuration < 0 || timeoutDuration > p.context.nsqd.options.MaxReqTimeout {
    return nil, util.NewFatalClientErr(nil, "E_INVALID",
        fmt.Sprintf("REQ timeout %d out of range 0-%d", timeoutDuration, p.context.nsqd.options.MaxReqTimeout))
}
```

A client sending an out-of-range REQ timeout gets disconnected (`FatalClientErr`). Per Focus Area 10, out-of-range values for recoverable operations should be clamped rather than causing disconnection. A requeue with a slightly-too-large timeout is a recoverable condition; disconnecting the client forces message redelivery of all its in-flight messages.

The same pattern appears in RDY (lines 513–518) — though the comment there acknowledges the inconsistent-state concern, making that case more justifiable.

---

### QUESTION — messagePump does not wait for completion in IOLoop exit (Focus Area 11)

- **Lines 107–114**
- **Severity: Low**

```go
conn.Close()
close(client.ExitChan)
if client.Channel != nil {
    client.Channel.RemoveClient(client.ID)
}
return err
```

IOLoop signals messagePump to exit via `close(client.ExitChan)` but does not wait (no `sync.WaitGroup` or channel rendezvous) for messagePump to complete before returning. The messagePump goroutine (lines 311–317) stops tickers during its exit. If the caller of IOLoop frees resources or exits the process immediately after IOLoop returns, the messagePump goroutine may still be running, leaking the goroutine or racing on ticker cleanup.

This may be acceptable if the server-level shutdown path separately waits for all connections, but the IOLoop exit path itself does not guarantee messagePump has finished.

---

### Focus Area 12 — Go Channel Lifecycle: No issues found

The `messagePump` select statement correctly applies the nil-channel idiom:
- **Line 263:** `subEventChan = nil` after receiving SUB event — prevents hot loop.
- **Line 266:** `identifyEventChan = nil` after receiving IDENTIFY data — prevents hot loop.
- **Line 291–293:** `clientMsgChan` closure detected with `, ok` pattern and exits cleanly.
- **Lines 273–278:** `heartbeatChan` set to nil when heartbeats disabled, preventing zero-value hot loop on closed ticker channel.
- **Line 306:** `client.ExitChan` closure properly triggers exit.

No channel lifecycle bugs identified.

---

## Summary

| Severity | BUG | QUESTION |
|----------|-----|----------|
| High     | 1   | 0        |
| Medium   | 2   | 0        |
| Low      | 0   | 3        |
| **Total**| **3**| **3**   |

### Key Findings
1. **DeflateLevel branch completeness bug (High)** — Client-requested positive deflate levels silently become 0 due to missing else branch.
2. **IDENTIFY MsgTimeout response mismatch (Medium)** — Response always echoes server default, not negotiated value.
3. **Unsafe MessageID cast without length check (Medium)** — Short message IDs cause out-of-bounds memory reads in FIN/REQ/TOUCH.

### Overall Assessment: **FIX FIRST**

The deflate level bug (finding #1) silently degrades compression for all clients that request a specific level. The unsafe pointer cast (finding #3) is a potential crash vector from malformed client input. Both should be fixed before shipping.
