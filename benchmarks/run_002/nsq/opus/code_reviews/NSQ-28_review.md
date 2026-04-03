# NSQ-28 Code Review: nsqd/protocol_v2.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `nsqd/protocol_v2.go` (1059 lines)
**Commit:** 9ea5071 (master)

---

## nsqd/protocol_v2.go

### Finding 1

- **Line 88:** QUESTION — Unchecked type assertion `err.(protocol.ChildErr)` will panic if `Exec()` ever returns an error that does not implement the `ChildErr` interface. Currently all code paths in `Exec` return `*protocol.ClientErr` or `*protocol.FatalClientErr`, both of which implement `ChildErr`, so this is safe today. However, any future command handler that returns a bare `error` (e.g., from a standard library call) would cause a runtime panic in the IOLoop, crashing the client connection ungracefully. A safe type assertion with `, ok` would be more defensive. **Severity: Low.**

### Finding 2

- **Line 316-321:** QUESTION — Topology zone/region matching compares empty strings as equal. If the `topology-aware-consumption` experiment is enabled but neither the server nor the client has configured `TopologyZone` or `TopologyRegion`, the condition `identifyData.TopologyZone == p.nsqd.getOpts().TopologyZone` evaluates to `"" == ""` → `true`, setting `zoneLocal = true`. This means all clients would receive zone-local message priority even though no topology is actually configured, which could silently change message distribution behavior when the experiment flag is enabled without zone configuration. **Severity: Medium.**

### Finding 3

- **Line 332-334:** QUESTION — When a zone-local client (`zoneLocal == true`) receives a message from `regionMsgChan`, the code increments `zoneLocalMsgCount` (line 333). However, the message was delivered via the region-local channel, not the zone-local channel. This inflates zone-local delivery stats with region-local messages. The apparent intent is "this client is zone-local, so count everything it receives as zone-local," but this conflates client locality with message routing path. If the stat is meant to track how many messages were delivered via zone-local routing, this is incorrect. Similarly at lines 338-339, a zone-local client receiving from the general `memoryMsgChan` also increments `zoneLocalMsgCount`. **Severity: Low.**

### Finding 4

- **Line 356:** BUG — Off-by-one in sample rate filtering. The condition `rand.Int31n(100) > sampleRate` delivers `sampleRate + 1` percent of messages instead of `sampleRate` percent. `rand.Int31n(100)` returns values in `[0, 99]`. For `sampleRate = 50`, values `0-50` (51 values) pass the filter, delivering 51% instead of 50%. The correct comparison should be `>= sampleRate` to deliver exactly `sampleRate` percent. For `sampleRate = 99`, this delivers 100% instead of 99% (since `rand.Int31n(100)` never returns 100, the condition `> 99` is never true). **Severity: Low.**

### Finding 5

- **Line 867:** QUESTION — In `MPUB`, `p.nsqd.GetTopic(topicName)` is called at line 867 *before* reading and validating the message body (lines 869-882). `GetTopic` auto-creates topics that don't exist. If the body is subsequently invalid (wrong size, too big, etc.), the error is returned but the topic has already been created as a side effect. By contrast, `PUB` (line 838) and `DPUB` (line 954) call `GetTopic` *after* body validation. A malicious or buggy client could create arbitrary topics by sending MPUB with valid topic names but invalid bodies. **Severity: Low.**

### Finding 6

- **Line 619 + 668:** QUESTION — `SUB` checks that `client.State == stateInit` (line 619) and transitions directly to `stateSubscribed` (line 668), skipping `stateConnected` entirely. The `stateConnected` constant is defined in `client_v2.go:23` but is never used in any client state transition. This means `IDENTIFY` does not advance the state, and a client can `SUB` without ever having sent `IDENTIFY`. While this appears intentional (IDENTIFY is optional in the NSQ protocol), it means `stateConnected` is dead code for clientV2. If there was ever intent to require IDENTIFY before SUB, this transition is wrong. **Severity: Low.**

### Finding 7

- **Line 863-864:** QUESTION — In `MPUB`, `CheckAuth` is called at line 863 *before* the body is read from the network stream (lines 869+). If auth fails and the function returns an error, the body bytes remain unread in the client's read buffer. The next iteration of `IOLoop` will attempt to parse those leftover body bytes as a new command, which will almost certainly fail with a confusing error or be misinterpreted. Compare with `PUB` (lines 828-836) where the body is read first and auth is checked after, avoiding this desynchronization. `DPUB` (lines 944-952) also reads the body before checking auth. **Severity: Medium.**

### Finding 8

- **Line 297-298:** QUESTION — The `IdentifyEventChan` send uses a non-blocking select with a default case (in `client_v2.go:296-298`). If the channel buffer (size 1) is already full from a prior send, the identify event is silently dropped. In `messagePump` at line 294-296, `identifyEventChan` is set to `nil` after the first receive, so a second IDENTIFY would be blocked by the state check at line 383. However, if there's ever a timing edge case where the channel is full but not yet received, the identify data (heartbeat, buffer timeout, sample rate changes) would be silently lost. In practice, the `messagePumpStartedChan` synchronization (lines 51-53) ensures messagePump is ready before IDENTIFY can be processed, making this safe. **Severity: Low.**

---

## Summary

| Severity | Count |
|----------|-------|
| BUG      | 1     |
| QUESTION | 7     |

**BUG findings:**
1. Off-by-one sample rate (line 356) — delivers sampleRate+1 percent

**Notable QUESTIONs:**
1. MPUB body desync on auth failure (line 863) — medium severity, can corrupt protocol stream
2. Empty-string topology matching (line 316) — medium severity, changes behavior when experiment enabled without config

**Overall assessment: NEEDS DISCUSSION** — The one confirmed bug (sample rate off-by-one) is low-severity and long-standing. The MPUB auth-before-read ordering (Finding 7) is the most concerning issue as it can desynchronize the protocol stream, but it only manifests when auth is enabled and fails for an MPUB command specifically. The topology empty-string matching deserves verification of intended behavior before the experiment graduates from experimental status.
