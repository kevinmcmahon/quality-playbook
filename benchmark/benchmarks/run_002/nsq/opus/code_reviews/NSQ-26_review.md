# Code Review: nsqd/protocol_v2.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Commit:** 9ea5071 (master)
**Focus Areas:** Protocol V2 State Machine, Client Resource Management

---

## nsqd/protocol_v2.go

### Finding 1

- **Line 383:** QUESTION (Medium Severity) — `IDENTIFY` checks that `client.State == stateInit` but never transitions the state afterward. All other state-gated commands either transition the state (`SUB` at line 668 stores `stateSubscribed`) or are gated to a post-transition state. Because `IDENTIFY` leaves the client in `stateInit`, a client can call `IDENTIFY` multiple times. On the second call, `UpgradeTLS()` (line 488), `UpgradeSnappy()` (line 499), or `UpgradeDeflate()` (line 512) would attempt to wrap an already-upgraded connection, producing undefined behavior (TLS-over-TLS, double compression). The second call would likely fail and close the connection, but this is a protocol enforcement gap. Expected: `IDENTIFY` should transition state (e.g., to `stateConnected`, which is defined at `client_v2.go:23` but unused in the client protocol).

### Finding 2

- **Line 88:** QUESTION (Medium Severity) — Unchecked type assertion `err.(protocol.ChildErr).Parent()`. If any error returned by `p.Exec()` does not implement the `protocol.ChildErr` interface, this panics with a runtime error. Currently all command handlers return `protocol.NewFatalClientErr` or `protocol.NewClientErr` which do implement `ChildErr`, so this is safe today. However, the assertion is fragile: any future code path in `Exec` that returns a bare `error` (e.g., from a new command handler) would cause a server panic on a per-client goroutine. Expected: use comma-ok form `if ce, ok := err.(protocol.ChildErr); ok { ... }`.

### Finding 3

- **Line 316-321:** QUESTION (Low Severity) — Topology zone/region matching compares `identifyData.TopologyZone == p.nsqd.getOpts().TopologyZone`. When topology-aware consumption is enabled (`isToplogyAware == true`) but neither the server nor the client has configured `TopologyZone` (both are empty strings `""`), empty strings match and `zoneLocal` is set to `true`. This causes all clients to be treated as zone-local, which defeats the purpose of topology-aware consumption. Expected: the comparison should also require that the zone/region strings are non-empty, e.g., `TopologyZone != "" && identifyData.TopologyZone == p.nsqd.getOpts().TopologyZone`.

### Finding 4

- **Line 330-335:** QUESTION (Low Severity) — When a zone-local client receives a message from `regionMsgChan`, the delivery is counted as `zoneLocalMsgCount` (line 331: `atomic.AddUint64(&client.Channel.zoneLocalMsgCount, 1)`). This conflates message source (region-local channel) with consumer locality (zone-local client). If the intent is to track "which channel delivered the message," this is a misclassification. If the intent is "what kind of consumer received it," it is correct but the metric name `zoneLocalMsgCount` is misleading in this context. Similarly, a region-local client receiving from `memoryMsgChan` counts as `regionLocalMsgCount` (line 341) even though the message came from the global channel.

### Finding 5

- **Line 295-298 (client_v2.go):** QUESTION (Low Severity) — The `IdentifyEventChan <- ie` send in `client.Identify()` uses a `select/default` pattern, silently dropping the event if the channel buffer (size 1) is full. This is related to Finding 1: if `IDENTIFY` is called twice before `messagePump` consumes the first event, the second identify event (with potentially different settings) is silently dropped. The `messagePump` would use stale settings for heartbeat interval, output buffer timeout, sample rate, and message timeout. This is only reachable because IDENTIFY doesn't transition state (Finding 1).

### Finding 6

- **Line 619/668:** QUESTION (Low Severity) — `SUB` transitions state directly from `stateInit` to `stateSubscribed` (line 668), bypassing the defined `stateConnected` state (`client_v2.go:23`). The `stateConnected` constant exists but is never used in the client protocol state machine (only in `lookup_peer.go:95`). This means a client can `SUB` without ever calling `IDENTIFY`, using only the default client settings. While this may be intentional for backward compatibility, it means a client can subscribe with default heartbeat/buffer/timeout settings that were never negotiated. The protocol allows: `connect → SUB` without `IDENTIFY`.

---

## Summary

| Severity | BUG | QUESTION |
|----------|-----|----------|
| Medium   | 0   | 2        |
| Low      | 0   | 4        |

**Total findings:** 6 (0 BUG, 6 QUESTION)

**Files with no findings:** N/A (single file review)

**Overall assessment:** NEEDS DISCUSSION — No definitive bugs found, but the state machine has a notable gap: `IDENTIFY` does not transition client state, allowing repeated calls and leaving `stateConnected` unused. The topology-aware consumption feature has edge cases around empty zone/region strings and ambiguous delivery counting metrics. These warrant discussion with the maintainers to determine if the behavior is intentional.
