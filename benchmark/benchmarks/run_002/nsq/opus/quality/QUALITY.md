# Quality Constitution: NSQ

## Purpose

NSQ is a realtime distributed messaging platform designed to operate at scale, handling billions of messages per day with guaranteed delivery and no single points of failure. Quality for NSQ means **fitness for use as a production message queue**: messages published must be delivered exactly once under normal operation, must never be silently lost, and the system must degrade gracefully under load, network partitions, and process crashes.

**Deming** ("quality is built in, not inspected in") — Quality is embedded in NSQ's architecture through atomic operations for state transitions, priority queues for timeout management, and disk-backed persistence for overflow. This quality constitution and the accompanying playbook ensure every AI session inherits the same understanding of what "correct" means for a distributed messaging system.

**Juran** ("fitness for use") — Fitness for NSQ is not "tests pass" but: (1) every published message is delivered to every subscribed channel, (2) in-flight messages are either finished or requeued within their timeout, never leaked, (3) metadata survives process restarts, (4) the system handles concurrent producers and consumers without data races, and (5) graceful shutdown persists all state without message loss.

**Crosby** ("quality is free") — The cost of a message queue bug in production — silent message loss, stuck consumers, corrupted metadata — far exceeds the cost of comprehensive upfront testing. A single lost message in a financial or event-driven system can cascade into hours of debugging and data reconciliation.

## Coverage Targets

| Subsystem | Target | Why |
|-----------|--------|-----|
| `nsqd/channel.go` (Channel) | 90–95% | Most complex module: manages in-flight/deferred queues, client tracking, message lifecycle state machine. A bug here silently loses messages or causes stuck consumers. Scenario 1 (in-flight leak) and Scenario 3 (deferred queue stall) originate here. |
| `nsqd/topic.go` (Topic) | 90% | Message distribution hub: `messagePump()` copies messages to channels. First channel gets original, others get copies. A bug in copy logic silently drops messages to some consumers. Scenario 2 (message copy loss). |
| `nsqd/protocol_v2.go` (Protocol) | 85–90% | Binary TCP protocol handler: client state machine (init→connected→subscribed→closing), command validation, auth checks. Protocol bugs cause client disconnects or auth bypasses. Scenario 4 (state machine gap). |
| `nsqd/nsqd.go` (NSQD core) | 85% | Server lifecycle: metadata persistence, topic/channel management, graceful shutdown. Scenario 5 (metadata corruption) originates here. |
| `nsqlookupd/` (Lookup) | 80% | Topology discovery: registration, tombstoning, producer filtering. Less complex but critical for cluster coordination. Scenario 7 (tombstone race). |
| `internal/` (Shared) | 75–80% | Protocol framing, HTTP API helpers, priority queue, auth. Well-tested utilities with fewer edge cases. |

## Coverage Theater Prevention

The following test patterns provide false confidence and must be avoided in this project:

- **Asserting a message was published without checking delivery.** A test that calls `PutMessage()` and asserts no error proves the enqueue path works, not that the message reaches consumers. The message could be stuck in the memory channel or lost during `messagePump()` distribution.
- **Testing with MemQueueSize=0 only.** Many tests force all messages to disk by setting `MemQueueSize=0`. This exercises the `BackendQueue` path but misses bugs in the in-memory `memoryMsgChan` path, which is the hot path in production (default 10,000 messages).
- **Asserting channel count without checking message flow.** Creating a channel and verifying it exists in `channelMap` doesn't prove messages flow through it. The `messagePump()` goroutine may not have started yet (needs `startChan` signal).
- **Testing protocol commands without verifying client state transitions.** Sending SUB and getting OK doesn't prove the client reached `stateSubscribed`. The atomic state field must be checked explicitly.
- **Mock-heavy tests that replace BackendQueue.** NSQ's `dummyBackendQueue` in tests is fine for unit isolation, but the interaction between `memoryMsgChan` and `BackendQueue` overflow is where real bugs live. Tests that mock the backend miss overflow behavior entirely.
- **Asserting `nsqd.Exit()` succeeds without checking metadata persistence.** Graceful shutdown calls `PersistMetadata()`, but a test that only checks the process exits cleanly misses whether topics/channels survive restart.

## Fitness-to-Purpose Scenarios

### Scenario 1: In-Flight Message Leak on Client Disconnect

**Requirement tag:** [Req: inferred — from Channel.FinishMessage() and inFlightMessages map behavior]

**What happened:** When a consumer disconnects unexpectedly (network drop, process kill) while holding in-flight messages, those messages must be returned to the queue for redelivery. The `inFlightMessages` map in `channel.go` tracks messages by `MessageID`, and the `inFlightPQ` priority queue tracks their timeouts. If the cleanup path in `RemoveClient()` doesn't properly process all in-flight messages for the disconnected client, those messages become permanently stuck — neither delivered nor requeued. In a system processing 100,000 messages/minute across 50 consumers, a single consumer crash could strand 2,000+ messages (the client's `MaxInFlight` worth) with no detection mechanism. The messages would appear in `Depth()` counts but never be delivered.

**The requirement:** When a client disconnects (gracefully via CLS or ungracefully via connection drop), all messages in-flight for that client must be requeued or returned to the channel's message queue within `MsgTimeout` (default 60s). Zero messages may remain in `inFlightMessages` mapped to a disconnected client ID.

**How to verify:** Connect a consumer, deliver N messages, disconnect without FINishing. Verify all N messages are redelivered to another consumer within MsgTimeout. Check `inFlightMessages` map is empty for the disconnected client ID.

### Scenario 2: Silent Message Loss During Topic messagePump Distribution

**Requirement tag:** [Req: inferred — from Topic.messagePump() channel distribution logic]

**What happened:** `Topic.messagePump()` in `topic.go` distributes each message to all subscribed channels. The first channel receives the original `*Message`, while subsequent channels receive copies via `NewMessage()`. If `messagePump()` encounters an error or panic during the copy-and-distribute loop — for example, if a channel is deleted mid-iteration while `channelMap` is being read with `RLock()` — messages already sent to some channels but not others create inconsistent state. With 5 channels and 10,000 messages/second, a single failed distribution cycle could deliver a message to channels 1-3 but not 4-5, violating the at-least-once delivery guarantee. The `messageCount` atomic counter would still increment, masking the loss.

**The requirement:** Every message published to a topic must be distributed to every channel that existed at the time of publication. The `messagePump()` must handle channel additions/deletions during distribution without losing messages. If a channel is deleted mid-distribution, messages to remaining channels must still be delivered.

**How to verify:** Create a topic with 3+ channels, publish N messages concurrently with channel creation/deletion. Verify each surviving channel received exactly N messages (minus any published after channel deletion). Cross-check `messageCount` atomics across topic and channels.

### Scenario 3: Deferred Message Queue Stall After Requeue Storm

**Requirement tag:** [Req: inferred — from Channel.processInFlightQueue() and deferredPQ behavior]

**What happened:** When consumers requeue messages with timeouts (REQ command with delay), messages enter the `deferredMessages` map and `deferredPQ` priority queue in `channel.go`. The `queueScanLoop` in `nsqd.go` periodically processes these deferred messages by checking if their timeout has expired. If a burst of requeues (e.g., 5,000 messages requeued simultaneously with varying timeouts) causes the priority queue to grow faster than `queueScanLoop` can process it — limited by `QueueScanSelectionCount` (default 20) and `QueueScanWorkerPoolMax` (default 4) — messages with expired timeouts may wait multiple scan intervals before being redelivered. At `QueueScanInterval` of 100ms, a backlog of 5,000 deferred messages processed 20 at a time takes 25 seconds to drain, during which consumers see no messages despite expired timeouts.

**The requirement:** Deferred messages must be redelivered within `QueueScanInterval` (100ms) of their timeout expiring, even under high requeue volume. The `queueScanLoop` must scale processing to handle bursts without introducing delivery latency beyond one scan interval.

**How to verify:** Requeue 1,000+ messages with short timeouts (100ms). Measure actual redelivery latency. Verify all messages are redelivered within 2× `QueueScanInterval` of their timeout expiry. Check no messages are permanently stuck in `deferredMessages`.

### Scenario 4: Protocol State Machine Allows Commands in Wrong State

**Requirement tag:** [Req: inferred — from protocolV2 command handlers state checks]

**What happened:** The client V2 protocol defines states: `stateInit` (0), `stateDisconnected` (1), `stateConnected` (2), `stateSubscribed` (3), `stateClosing` (4). Each command handler checks `atomic.LoadInt32(&client.State)` and returns `FatalClientErr` for invalid states. However, the SUB command transitions state from `stateInit` directly to `stateSubscribed` (skipping `stateConnected`), while IDENTIFY transitions from `stateInit` to `stateConnected`. If a client sends SUB without IDENTIFY, it jumps to `stateSubscribed` without feature negotiation — missing heartbeat configuration, compression setup, and auth. This means the client operates with default timeouts and no heartbeat, which can cause it to be silently disconnected after `ClientTimeout` (60s) with no indication to the application.

**The requirement:** The protocol must enforce valid state transitions. SUB must require state `stateInit` (which it does check), but the documentation implies IDENTIFY should precede SUB. If IDENTIFY is optional, the default configuration applied to non-identified clients must be documented and safe. If IDENTIFY is required, SUB in `stateInit` should fail with an error guiding the client to IDENTIFY first.

**How to verify:** Connect to nsqd, send SUB without IDENTIFY. Verify the client either (a) receives an error requiring IDENTIFY first, or (b) operates correctly with default configuration including heartbeats. Check that the client doesn't silently timeout after 60s.

### Scenario 5: Metadata Corruption on Crash During PersistMetadata

**Requirement tag:** [Req: inferred — from NSQD.PersistMetadata() file write pattern]

**What happened:** `PersistMetadata()` in `nsqd.go` writes the current topic/channel state to `nsqd.dat` as JSON. The write uses `os.WriteFile()` (or equivalent) which is not atomic — if the process crashes mid-write, the file will be truncated or contain partial JSON. On the next startup, `LoadMetadata()` will fail to parse the corrupted file with a JSON decode error. With 50 topics and 200 channels, the metadata file is several KB; a crash during the write window leaves the node unable to recover its topic/channel configuration automatically. An operator must manually reconstruct the metadata or delete it (losing all channel positions).

**The requirement:** Metadata persistence must be atomic: either the complete new state is written, or the previous state is preserved. The standard pattern is write-to-temp-file + atomic rename. `LoadMetadata()` must handle corrupted files gracefully — either using the previous backup or starting fresh with a clear warning.

**How to verify:** Write metadata, simulate crash by truncating `nsqd.dat` mid-write. Restart and verify `LoadMetadata()` either recovers the previous state or starts fresh with a logged warning (not a panic or unrecoverable error).

### Scenario 6: Memory Queue Overflow Loses Messages When Backend Write Fails

**Requirement tag:** [Req: inferred — from Topic.put() and Channel.put() overflow to backend logic]

**What happened:** When the in-memory `memoryMsgChan` is full (default capacity: `MemQueueSize` = 10,000), messages overflow to the `BackendQueue` (disk-based `go-diskqueue`). The `put()` method in both `topic.go` and `channel.go` uses a `select` statement: try memory channel first, fall through to backend. If the backend write fails (disk full, permissions error, I/O error), the message is dropped with only a log message. At 10,000 messages/second with a full memory queue, a disk I/O error lasting 1 second silently loses 10,000 messages. The `messageCount` atomic still increments (it's updated before the `put()` call), so monitoring shows messages were "published" but they were never durably stored.

**The requirement:** When both memory queue and backend queue reject a message, `PutMessage()` must return an error to the publisher. The publisher can then retry or handle the failure. Silent message drops with only logging must not occur for durable (non-ephemeral) topics.

**How to verify:** Fill the memory queue to capacity. Simulate backend write failure. Attempt to publish. Verify `PutMessage()` returns an error (not nil). Verify the failed message's count is not included in `messageCount`.

### Scenario 7: Tombstone Race in nsqlookupd Registration

**Requirement tag:** [Req: inferred — from Producer.Tombstone() and IsTombstoned() behavior]

**What happened:** In `nsqlookupd/registration_db.go`, tombstoning is a soft-delete mechanism: `Producer.Tombstone()` sets `tombstoned=true` and records `tombstonedAt` time. `IsTombstoned()` returns true only if `tombstonedAt` is within `TombstoneLifetime`. `FilterByActive()` filters producers by both activity timeout and tombstone status. However, tombstoning and registration are not atomic: a producer can be tombstoned by one goroutine (HTTP handler) while simultaneously re-registering via the TCP REGISTER command from a different connection. The `RegistrationDB.RWMutex` protects the map, but tombstone state and re-registration happen in separate locked sections. A producer that tombstones and immediately re-registers may appear active to some lookupd queries and tombstoned to others during the transition window.

**The requirement:** Tombstoning must be visible to all subsequent lookupd queries once applied. If a producer re-registers after being tombstoned, the tombstone must be cleared. The `FilterByActive()` method must produce consistent results — a producer is either active or tombstoned, never both depending on query timing.

**How to verify:** Tombstone a producer, immediately re-register it. Query the registration DB from multiple goroutines. Verify all queries see the producer as either consistently tombstoned or consistently active.

### Scenario 8: Ephemeral Topic/Channel Deletion Race

**Requirement tag:** [Req: inferred — from Channel.RemoveClient() ephemeral deletion and Topic deleteCallback behavior]

**What happened:** Ephemeral channels are auto-deleted when the last consumer disconnects. In `Channel.RemoveClient()`, after removing the client from the `clients` map, if the channel is ephemeral and `len(clients) == 0`, `deleteCallback` is invoked. This triggers `Topic.DeleteExistingChannel()`, which acquires the topic's write lock. If two clients disconnect simultaneously, both goroutines may check `len(clients) == 0` before either invokes the callback — but `deleteCallback` is protected by `sync.Once`, so only one deletion occurs. The race is in the check: between `RemoveClient()` releasing the channel lock and `deleteCallback` acquiring the topic lock, a new client could connect and subscribe. If the deletion proceeds, the new client's subscription is invalidated, and its messages vanish into a deleted channel.

**The requirement:** Ephemeral channel deletion must be atomic with respect to new client subscriptions. If a new client subscribes between the last-client-disconnect check and the actual deletion, the deletion must be cancelled and the channel must remain alive.

**How to verify:** Create an ephemeral channel with one consumer. Disconnect the consumer and simultaneously connect a new consumer to the same channel. Verify the channel survives and the new consumer receives messages.

### Scenario 9: Pause/UnPause Race with messagePump

**Requirement tag:** [Req: inferred — from Topic.Pause()/UnPause() and messagePump() pause handling]

**What happened:** `Topic.Pause()` sets `paused` atomically to 1 and signals `pauseChan`. The `messagePump()` goroutine checks `IsPaused()` in its select loop. However, between the atomic store and the `messagePump()` checking the pause state, messages currently being distributed continue to flow. More critically, if `Pause()` and `UnPause()` are called in rapid succession (e.g., admin toggling in nsqadmin), the `pauseChan` signal may be consumed by the first state change, and the `messagePump()` may never see the unpause — remaining paused indefinitely. With thousands of messages buffered in `memoryMsgChan`, a stuck pause means all consumers starve despite the topic being "unpaused" in the admin UI.

**The requirement:** After `UnPause()` returns, the `messagePump()` must resume message distribution within one loop iteration. Rapid Pause/UnPause cycles must not cause the messagePump to get stuck in a paused state.

**How to verify:** Pause a topic, publish messages, unpause. Verify messages flow to consumers within 1 second. Rapidly toggle pause/unpause 100 times. Verify the final state (paused or unpaused) matches the last operation and messages flow accordingly.

### Scenario 10: MaxChannelConsumers Bypass via Concurrent AddClient

**Requirement tag:** [Req: inferred — from Channel.AddClient() maxChannelConsumers check]

**What happened:** `Channel.AddClient()` checks `maxChannelConsumers` against `len(c.clients)` under the channel's write lock. This is correctly synchronized. However, the check happens after acquiring the lock — if `maxChannelConsumers` is dynamically changed via runtime options update (through the `optsNotificationChan`), there's a window where the limit changes between when a client decides to subscribe and when `AddClient()` checks. More importantly, the `MaxChannelConsumers` check uses `len(c.clients)` which includes clients in `stateClosing` — clients that have sent CLS but haven't been fully removed yet. This means the effective consumer limit can be lower than configured: if 5 clients are closing and `MaxChannelConsumers` is 10, only 5 new clients can connect even though the 5 closing clients will free slots momentarily.

**The requirement:** `MaxChannelConsumers` should count only active consumers (not those in `stateClosing`). If the option is changed at runtime, existing connections that exceed the new limit should not be forcibly disconnected, but new connections should be rejected until the count drops below the limit.

**How to verify:** Set `MaxChannelConsumers=5`. Connect 5 consumers. Send CLS on 3 of them. Before they fully disconnect, attempt to connect 3 new consumers. Verify all 3 new connections succeed (because closing clients should not count against the limit).

## AI Session Quality Discipline

1. Read `quality/QUALITY.md` before starting any work on NSQ.
2. Run the full test suite (`go test ./...`) before marking any task complete.
3. Add tests for new functionality — not just happy path, include edge cases for concurrency, timeouts, and state transitions.
4. Update this file if new failure modes are discovered during development.
5. Output a Quality Compliance Checklist before ending a session.
6. Never remove a fitness-to-purpose scenario. Only add new ones.
7. Pay special attention to atomic operations — 64-bit atomics must be first in struct definitions for alignment on 32-bit platforms.
8. When modifying channel or topic code, verify both the memory path (`memoryMsgChan`) and the backend path (`BackendQueue`) are handled consistently.
9. When modifying protocol handlers, verify client state checks are correct for all valid states.

## The Human Gate

The following require human judgment and cannot be fully automated:

- **Message ordering guarantees** — NSQ provides no ordering guarantees by design. Whether reordering under specific conditions is acceptable requires application-level domain knowledge.
- **Performance tuning** — `QueueScanInterval`, `MemQueueSize`, `MaxRdyCount` tradeoffs depend on deployment-specific workload patterns.
- **TLS/Auth configuration** — Security policy decisions (required vs. optional TLS, auth service endpoints) require operational context.
- **Cluster topology decisions** — Number of nsqlookupd instances, nsqd placement, replication strategy require infrastructure knowledge.
- **Backward compatibility** — Protocol changes that affect existing clients require understanding of the deployed client ecosystem.
- **Ephemeral vs. durable topic/channel policy** — Whether a given use case should use ephemeral topics depends on the application's data loss tolerance.
