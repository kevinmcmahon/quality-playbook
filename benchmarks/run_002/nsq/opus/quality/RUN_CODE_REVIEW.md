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

### Focus Area 9: Configuration Parameter Validation

**Where:** All configuration parsing — `nsqd/nsqd.go` New(), `nsqd/protocol_v2.go` IDENTIFY(), `nsqd/http.go` parameter handling
**What:** For each configuration parameter:
1. **Flag interaction guards:** When one flag modifies another, verify it checks the current value first. Pattern: `if flagA != "" && flagB == DefaultValue { modify flagB }`. An unconditional `if flagA != "" { flagB = X }` clobbers explicit user settings — this is always a bug.
2. **Whitelist validation for semantic parameters:** URL/HTTP parameters accepting boolean or enum values must use an explicit allowed-value map (e.g., `map[string]bool{"true": true, "1": true, "false": false, "0": false}`). Treating parameter existence or any non-empty value as "true" is a validation gap.
3. **Disable-value semantics:** When a parameter value of 0, empty, or false means "disable this feature," verify the code creates a **nil** resource, not a zero-capacity resource. In Go, `make(chan T)` (unbuffered) is NOT the same as a nil channel — unbuffered blocks on send/receive, nil blocks forever in select. A disabled feature must use nil, not zero-capacity.
4. **Branch completeness:** For each if/else chain that assigns a config value, verify ALL branches assign the output variable. A missing `else` clause leaves the variable at its zero value — trace the default path.
**Why:** Configuration bugs are silent — the system runs with wrong settings and the operator has no error to debug.

### Focus Area 10: Input Validation Failure Modes

**Where:** `nsqd/protocol_v2.go` — all command handlers (SUB, RDY, FIN, REQ, TOUCH, MPUB, IDENTIFY)
**What:** For each validation check in a protocol command handler:
1. **Clamp vs. disconnect:** When client sends an out-of-range value (timeout too large, invalid count), verify the handler **clamps to valid range and logs a warning** rather than returning FatalClientErr. Disconnecting a client for a recoverable data validation error is a bug. Exception: authentication/authorization failures MAY be fatal.
2. **Response field mapping:** When a protocol handler builds a response struct, verify each field echoes or confirms the corresponding request field. If the client sends `MsgTimeout: 5000` in IDENTIFY, the response must contain `MsgTimeout: 5000`, not the server's default value. Map every request field to its response field.
3. **Error propagation through layers:** When a handler calls a function that returns an error (e.g., `channel.AddClient()`), verify the error is propagated to the protocol response, not silently discarded and replaced with a generic error.
**Why:** Protocol handlers that over-punish or mis-echo create subtle client misbehavior that is extremely hard to diagnose in production.

### Focus Area 11: Exit Path Resource Completeness

**Where:** `nsqd/nsqd.go` Exit(), `nsqd/topic.go` Close(), `nsqd/channel.go` exit(), `nsqlookupd/nsqlookupd.go` Exit()
**What:** For each Exit()/Close() method, enumerate ALL resource types the component owns and verify explicit cleanup for each:
1. **TCP listeners** — verify Close() called
2. **Active TCP connections** (both producer AND consumer) — closing a listener does NOT close existing connections. Verify the code iterates active connections and closes each one explicitly.
3. **HTTP/HTTPS listeners and connections** — same pattern as TCP
4. **Goroutines** — verify all spawned goroutines are tracked (sync.WaitGroup) and waited on
5. **Backend stores** (disk queues, files) — verify Sync() and Close() in correct order
6. **Registration/lookup connections** — verify deregistration from nsqlookupd
The pattern is always: (a) close listener to stop new connections, (b) iterate and close all active connections, (c) wait for goroutines, (d) close backends. If step (b) is missing, the server hangs waiting for connections that will never close.
**Why:** Missing one resource type in Exit() causes indefinite hang on shutdown — the most common "graceful shutdown isn't graceful" bug.

### Focus Area 12: Go Channel Lifecycle in Select Statements

**Where:** Any select statement that receives from channels which may close — `nsqd/channel.go`, `nsqd/protocol_v2.go` messagePump(), `nsqd/topic.go` messagePump()
**What:**
1. **Nil-channel idiom:** When a channel in a select may close, verify the code sets it to nil after detecting closure (`if !ok { ch = nil }`). A nil channel blocks forever in select, gracefully disabling that case. Without this, a closed channel returns zero-values in a hot loop or a send to a closed channel panics.
2. **Goroutine exit ordering:** When multiple goroutines share cleanup responsibilities (e.g., messagePump and readLoop both call RemoveClient), verify cleanup executes in a location guaranteed to run regardless of which goroutine exits first. Move cleanup to the common parent (e.g., IOLoop exit handler) rather than a specific goroutine's exit path.
3. **Buffered signal channels:** When a buffered channel carries a one-shot signal (like SubEventChan), verify the signal is consumed in ALL exit paths. A signal stuck in a buffer because the receiver already exited is a resource leak.
**Why:** Go channel lifecycle bugs cause deadlocks, goroutine leaks, and panics — all of which are intermittent and extremely hard to reproduce.

## Guardrails

- **Line numbers are mandatory.** If you cannot cite a specific line, do not include the finding.
- **Read function bodies, not just signatures.** Don't assume a function works correctly based on its name.
- **If unsure whether something is a bug or intentional**, flag it as a QUESTION rather than a BUG.
- **Grep before claiming missing.** If you think a feature is absent, search the codebase. If found in a different file, that's a location defect, not a missing feature.
- **Do NOT suggest style changes, refactors, or improvements.** Only flag things that are incorrect or could cause failures.
- **Exhaust the sibling set.** When you find a bug in one method of a type, grep for every other method on that type and check them for the same bug pattern.
- **Check validation failure modes, not just validation existence.** For each validation check, ask: "What happens when this fails? Is it the right failure mode (clamp vs. fatal)?"
- **Enumerate all resource types in Exit().** Don't stop at "listeners are closed." List every resource type (listeners, active connections, goroutines, backends) and verify each has explicit cleanup.

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
