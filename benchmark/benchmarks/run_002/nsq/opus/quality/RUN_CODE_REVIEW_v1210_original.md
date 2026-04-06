# Code Review Protocol: NSQ

## Bootstrap (Read First)

Before reviewing, read these files for context:
1. `quality/QUALITY.md` — Quality constitution, fitness-to-purpose scenarios, and coverage targets
2. `nsqd/README.md` — nsqd daemon overview
3. `nsqlookupd/README.md` — Lookup service overview
4. `nsqadmin/README.md` — Admin UI overview

## What to Check

### Focus Area 1: Message Lifecycle Integrity (Channel)

**Where:** `nsqd/channel.go` — `PutMessage()`, `put()`, `FinishMessage()`, `RequeueMessage()`, `StartInFlightTimeout()`, `TouchMessage()`
**What:** Verify that every message that enters the channel is either finished (FIN), requeued (REQ), or times out and is returned to the queue. Check that in-flight and deferred message maps stay synchronized with their corresponding priority queues. Verify `exitMutex.RLock()` is held during put operations to prevent messages being added to a closing channel.
**Why:** A message that enters `inFlightMessages` but is never removed is permanently lost. A message in the priority queue but not the map (or vice versa) causes silent data corruption or panics.

### Focus Area 2: Concurrent State Access (Topic & Channel)

**Where:** `nsqd/topic.go` — `messagePump()`, `GetChannel()`, `DeleteExistingChannel()`, `PutMessage()`; `nsqd/channel.go` — `AddClient()`, `RemoveClient()`, `Empty()`
**What:** Verify that all accesses to shared maps (`channelMap`, `clients`, `inFlightMessages`, `deferredMessages`) are protected by the correct lock. Check that atomic operations on `exitFlag`, `paused`, `messageCount` use correct load/store functions. Verify 64-bit atomic fields are first in struct definitions (required for 32-bit platform alignment).
**Why:** Data races in a message queue cause silent message loss or duplication. The Go race detector catches some, but not logic errors like reading `len(clients)` under `RLock` then writing under `Lock` with a gap between them.

### Focus Area 3: Protocol V2 State Machine (Protocol)

**Where:** `nsqd/protocol_v2.go` — `IDENTIFY()`, `SUB()`, `RDY()`, `FIN()`, `REQ()`, `TOUCH()`, `CLS()`, `AUTH()`, `messagePump()`
**What:** Verify each command handler checks `client.State` before executing. Check that state transitions are atomic (using `atomic.StoreInt32`). Verify `messagePump()` correctly handles all client states including `stateClosing`. Check that `FatalClientErr` vs regular error responses are used correctly.
**Why:** A protocol command accepted in the wrong state can crash the client connection, leak resources, or bypass authentication. The SUB command jumping from `stateInit` to `stateSubscribed` (skipping `stateConnected`) is a known concern.

### Focus Area 4: Metadata Persistence and Recovery

**Where:** `nsqd/nsqd.go` — `LoadMetadata()`, `PersistMetadata()`, `GetMetadata()`; `nsqd/topic.go` — `Close()`; `nsqd/channel.go` — `Close()`, `flush()`
**What:** Verify `PersistMetadata()` writes atomically (or documents the risk of partial writes). Check that `LoadMetadata()` handles corrupted/missing metadata gracefully. Verify the `isLoading` flag correctly prevents metadata persistence during startup.
**Why:** Non-atomic metadata writes risk file corruption on crash. Corrupt metadata means topics/channels are lost on restart.

### Focus Area 5: Graceful Shutdown Ordering

**Where:** `nsqd/nsqd.go` — `Exit()`, `Main()`; `nsqd/topic.go` — `Close()`, `Delete()`; `nsqd/channel.go` — `exit()`, `flush()`
**What:** Verify shutdown sequence: close listeners → persist metadata → close topics → close channels → flush in-flight/deferred to disk. Check that `sync.Once` and `atomic.CompareAndSwap` prevent double-close. Verify all goroutines exit cleanly (no goroutine leaks).
**Why:** Wrong shutdown ordering causes message loss: if topics close before channels flush, in-flight messages are dropped. Double-close causes panics.

### Focus Area 6: Disk Queue Integration

**Where:** `nsqd/topic.go` — `NewTopic()`, `put()`; `nsqd/channel.go` — `NewChannel()`, `put()`, `flush()`
**What:** Verify that `writeMessageToBackend()` errors are properly propagated. Check that `SetHealth()` is called on backend failures. Verify ephemeral topics/channels use `dummyBackendQueue` and never write to disk. Check disk queue name generation (`getBackendName()`) for uniqueness.
**Why:** Silent backend write failures cause message loss. Health not being set means the system reports healthy while losing messages.

### Focus Area 7: nsqlookupd Registration Consistency

**Where:** `nsqlookupd/registration_db.go` — `AddProducer()`, `RemoveProducer()`, `FindProducers()`, `FilterByActive()`; `nsqlookupd/lookup_protocol_v1.go`
**What:** Verify that tombstone state transitions are consistent under concurrent access. Check that `FilterByActive()` produces correct results with mixed active/tombstoned/inactive producers. Verify the `RWMutex` is held correctly in all registration DB operations.
**Why:** Inconsistent registration state means clients discover stale or incorrect producer lists, causing connection failures or message loss.

### Focus Area 8: Client Resource Management

**Where:** `nsqd/client_v2.go` — `newClientV2()`, `Identify()`, `Stats()`; `nsqd/protocol_v2.go` — `messagePump()`
**What:** Verify that client resources (buffers, compression writers, TLS connections) are properly cleaned up on disconnect. Check that `ReadyStateChan` (buffer=1) and `SubEventChan` (buffer=1) never block indefinitely. Verify heartbeat intervals are validated against `MaxHeartbeatInterval`.
**Why:** Resource leaks in a long-running server compound over time. A blocked channel signal causes goroutine leaks.

## Guardrails

- **Line numbers are mandatory.** If you cannot cite a specific line, do not include the finding.
- **Read function bodies, not just signatures.** Don't assume a function works correctly based on its name.
- **If unsure whether something is a bug or intentional**, flag it as a QUESTION rather than a BUG.
- **Grep before claiming missing.** If you think a feature is absent, search the codebase. If found in a different file, that's a location defect, not a missing feature.
- **Do NOT suggest style changes, refactors, or improvements.** Only flag things that are incorrect or could cause failures.

## Output Format

Save findings to `quality/code_reviews/YYYY-MM-DD-reviewer.md`

For each file reviewed:

### filename.ext
- **Line NNN:** [BUG / QUESTION / INCOMPLETE] Description. Expected vs. actual. Why it matters.

### Summary
- Total findings by severity
- Files with no findings
- Overall assessment: SHIP IT / FIX FIRST / NEEDS DISCUSSION

## Phase 2: Regression Tests

After the review produces BUG findings, write regression tests in `quality/regression_test.go` that reproduce each bug:

1. For each BUG finding, write a test that targets the exact code path
2. Run with `go test -race ./nsqd/` to confirm data race findings
3. Report results as a confirmation table:

| Finding | Test | Result | Confirmed? |
|---------|------|--------|------------|
| [description] | TestRegression_... | FAILED (expected) | YES — bug confirmed |
| [description] | TestRegression_... | PASSED (unexpected) | NO — needs investigation |
