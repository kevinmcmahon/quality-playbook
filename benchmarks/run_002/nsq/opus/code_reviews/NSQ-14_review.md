# NSQ-14 Code Review: Protocol V2 State Machine

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Files reviewed:** `nsqd/protocol_v2.go`, `nsqd/protocol_v2_test.go`
**Focus Area:** Protocol V2 State Machine (Focus Area 3) and Client Resource Management (Focus Area 8)

---

## nsqd/protocol_v2.go

### Finding 1
- **Line 860:** BUG (Low severity). Duplicated error code in MPUB bad topic error message. The `Desc` argument to `NewFatalClientErr` includes the error code prefix `E_BAD_TOPIC`, which is already passed as the `Code` argument. Since `FatalClientErr.Error()` concatenates `Code + " " + Desc`, the client receives `"E_BAD_TOPIC E_BAD_TOPIC MPUB topic name ... is not valid"`. Compare with PUB at line 809 which correctly omits the code from the description: `fmt.Sprintf("PUB topic name %q is not valid", topicName)`. Expected: `"E_BAD_TOPIC MPUB topic name ... is not valid"`. Actual: `"E_BAD_TOPIC E_BAD_TOPIC MPUB topic name ... is not valid"`.

### Finding 2
- **Line 296 (identifyEventChan) + Lines 383, 668:** QUESTION (Medium severity). IDENTIFY can be called multiple times but messagePump only processes the first identify event. The `IDENTIFY()` handler at line 383 checks `client.State != stateInit` but never transitions state away from `stateInit`. This allows repeated IDENTIFY calls. However, in `messagePump()` at line 296, `identifyEventChan` is set to `nil` after the first event is consumed, so subsequent IDENTIFY settings (heartbeat interval, output buffer timeout, sample rate, msg timeout) are silently ignored by the message pump — even though the IDENTIFY response sent back to the client at line 479 reports the new negotiated values. The `client.Identify()` method (client_v2.go:296) uses a non-blocking send (`select/default`), so at most one subsequent event sits in the buffer unconsumed. The test `TestOutputBufferingValidity` (protocol_v2_test.go:866-877) calls IDENTIFY 4 times, confirming this is exercised but not verifying that settings take effect in the pump. **Risk:** A client that calls IDENTIFY twice believes its second set of settings are active, but the message pump continues using the first set.

### Finding 3
- **Line 88:** QUESTION (Low severity). Unchecked type assertion `err.(protocol.ChildErr).Parent()`. If `Exec()` ever returns an error that does not implement the `protocol.ChildErr` interface, this will panic, crashing the client's IOLoop goroutine. Currently all error return paths from `Exec` and its callees return `*protocol.FatalClientErr` or `*protocol.ClientErr`, both of which implement `ChildErr`, so this is safe in practice. However, the assertion has no comma-ok guard, making it fragile if future changes add a new error return path.

### Finding 4
- **Lines 329-344:** QUESTION (Low severity). Topology-aware message counting attributes all messages received by a zone-local client to `zoneLocalMsgCount`, regardless of which channel (`zoneMsgChan`, `regionMsgChan`, or `memoryMsgChan`) delivered the message. For example, at line 333, a message received from `regionMsgChan` by a zone-local client increments `zoneLocalMsgCount`. Similarly at line 339, a message from `memoryMsgChan` (the global channel) increments `zoneLocalMsgCount` for zone-local clients. This means the metric tracks "messages delivered to zone-local consumers" rather than "messages delivered via the zone-local channel." If the intent is to measure the effectiveness of the topology-aware routing (i.e., how often messages are actually routed via zone/region-local channels), these counters are misleading. If the intent is to track consumer locality, this is correct.

### Finding 5
- **Line 356:** QUESTION (Low severity). Sampling check uses `rand.Int31n(100) > sampleRate` which means a `sampleRate` of 42 delivers messages when the random value is 0-42 (inclusive), i.e., 43% of messages, not 42%. The `>` should arguably be `>=` to deliver exactly `sampleRate`% of messages. This is a 1% discrepancy. The `TestSampling` test at line 1279 uses a `slack` of 5% which masks this off-by-one.

---

## nsqd/protocol_v2_test.go

### Finding 6
- **Line 870-873:** QUESTION (Low severity). `TestOutputBufferingValidity` calls `identify()` 4 times on the same connection. The second and third calls (lines 870-877) succeed, but per Finding 2, their settings are silently not applied in the message pump. The test does not verify that buffer settings actually take effect, so it passes despite the silent ignore. This test may give false confidence that repeated IDENTIFY calls work correctly.

### Finding 7
- **Lines 190-199 (TestMultipleConsumerV2):** QUESTION (Low severity). The goroutine at line 190 calls `test.Nil(t, err)` and `test.Nil(t, err)` from a non-test goroutine. In Go, calling `t.Fatal`/`t.Error` (which the test helpers likely call) from a goroutine other than the test goroutine can cause undefined behavior or missed test failures. If `nsq.ReadResponse` or `decodeMessage` fails, the test assertion may panic the goroutine without properly failing the test. Similar pattern appears in `TestSameZoneConsumerV2` at lines 244-261.

---

## Summary

| Severity | BUG | QUESTION | Total |
|----------|-----|----------|-------|
| Medium   | 0   | 1        | 1     |
| Low      | 1   | 5        | 6     |
| **Total**| **1** | **6**  | **7** |

**BUG findings:** 1 (MPUB duplicated error code — cosmetic but incorrect)
**QUESTION findings:** 6

**Files with no findings:** None (both files had findings)

**Overall assessment:** SHIP IT (with minor fix for the MPUB error message). The protocol state machine is well-structured with correct state checks on all command handlers. Atomic operations are used correctly for state transitions. The `messagePump` correctly handles all client states. The MPUB error code duplication is the only clear defect — low impact since it only affects error message formatting. The multiple-IDENTIFY question (Finding 2) is the most significant concern but may be intentional (IDENTIFY-once contract not enforced at state level for backward compatibility).
