# Code Review: nsqd/protocol_v2.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Focus:** Protocol V2 State Machine, Client Resource Management (Focus Areas 3 & 8)

---

### nsqd/protocol_v2.go

- **Line 383:** [BUG] **IDENTIFY does not transition client state, allowing re-identification.** `IDENTIFY` checks `stateInit` (line 383) but never calls `atomic.StoreInt32(&client.State, stateConnected)` on success. A client can send IDENTIFY multiple times. The first IDENTIFY's `identifyEvent` is consumed by `messagePump` (line 294), which then sets `identifyEventChan = nil` (line 296). A second IDENTIFY call still passes the state check, calls `client.Identify()` which mutates client fields (HeartbeatInterval, OutputBufferTimeout, MsgTimeout, SampleRate) and tries to send to `IdentifyEventChan` — but the send is dropped by the `default` case (client_v2.go:297) since messagePump's receiver is nil. **Result:** Client struct has updated settings that messagePump never sees. Heartbeat and output buffer tickers continue using stale values. Worse, if TLS or compression was negotiated in the first IDENTIFY, a second IDENTIFY attempts to re-upgrade the connection (lines 484-521), which will corrupt the stream or panic. **Severity: Medium.** Well-behaved clients won't do this, but a malicious or buggy client can cause inconsistent server state.

- **Line 88:** [QUESTION] **Unconditional type assertion `err.(protocol.ChildErr)` could panic.** All current error paths from `Exec` return `*protocol.ClientErr` or `*protocol.FatalClientErr`, both of which implement `ChildErr`. However, if a future code change introduces an error return that doesn't implement `ChildErr`, this line panics with a runtime error instead of disconnecting gracefully. A two-value assertion (`if ce, ok := err.(protocol.ChildErr); ok`) would be defensive. **Severity: Low.** Not currently triggerable but fragile.

- **Line 316-321:** [QUESTION] **Empty topology zone/region causes universal zone-local matching.** When the `TopologyAwareConsumption` experiment is enabled, if neither the server nor the client configures `TopologyZone` (both default to `""`), the condition `identifyData.TopologyZone == p.nsqd.getOpts().TopologyZone` evaluates to `"" == ""` → `true`. All clients would be marked `zoneLocal = true`, causing all messages to be routed through `zoneLocalMsgChan` and counted as zone-local. This may be intentional (feature is opt-in via experiment flag), but could surprise operators who enable the experiment without configuring zones. **Severity: Low.**

- **Line 356:** [QUESTION] **Sample rate off-by-one.** The skip condition `rand.Int31n(100) > sampleRate` delivers `(sampleRate + 1)%` of messages instead of `sampleRate%`. For example, `sampleRate=1` delivers 2% (values 0 and 1 pass), and `sampleRate=99` delivers 100% (identical to `sampleRate=100`). The condition should arguably be `>= sampleRate` for exact percentage semantics. **Severity: Low.** Off by 1% in sampling is unlikely to matter in practice.

- **Lines 869-885:** [QUESTION] **MPUB `bodyLen` is validated but not enforced as a read boundary.** `bodyLen` is read from the wire (line 869) and checked against `MaxBodySize` (line 879), but `readMPUB` (line 884) reads directly from `client.Reader` without a `LimitedReader` bounded to `bodyLen`. If a buggy client sends a `bodyLen` that doesn't match the actual sum of `[4-byte numMessages] + Σ([4-byte msgSize] + msgBody)`, the stream becomes misaligned — leftover bytes are interpreted as the next command, or `readMPUB` consumes bytes from the next command. Compare with `PUB` (line 828-829) which reads exactly `bodyLen` bytes via `io.ReadFull`. **Severity: Low.** Only affects malformed clients; well-formed MPUB bodies are self-consistent.

- **Line 619:** [QUESTION] **SUB checks `stateInit`, not `stateConnected`; `stateConnected` is never used for client_v2.** The `stateConnected` constant is defined (client_v2.go:23) but never set or checked in the client protocol flow. SUB transitions directly from `stateInit` to `stateSubscribed` (line 668). This means IDENTIFY is fully optional — a client can SUB immediately after connecting. This appears intentional (IDENTIFY is for feature negotiation, not authentication gating), but the unused `stateConnected` constant is misleading. **Severity: Informational.**

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (Medium) | 1 |
| QUESTION | 5 |

**Overall assessment:** NEEDS DISCUSSION — The re-IDENTIFY bug (line 383) allows a client to desynchronize its settings from the messagePump goroutine and potentially corrupt TLS/compression-wrapped connections. This should be fixed by either transitioning state out of `stateInit` after IDENTIFY, or adding a flag/guard to prevent re-entry.
