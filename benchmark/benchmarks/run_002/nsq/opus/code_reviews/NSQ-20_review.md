# NSQ Code Review — NSQ-20

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Files reviewed:** nsqd/channel.go, nsqd/topic.go, nsqd/nsqd.go, nsqd/client_v2.go
**Files not found (skipped):** examples/nsq_pubsub/nsq_pubsub.go, nsq/reader.go, nsq/reader_test.go, nsq/writer.go, nsqd/diskqueue.go

---

### nsqd/channel.go

- **Line 206-227:** BUG (Medium). `Empty()` drains `c.zoneLocalMsgChan` and `c.regionLocalMsgChan` unconditionally in the select loop (lines 217-218), but these channels are only initialized when `TopologyZone` / `TopologyRegion` options are set (lines 96-100 in `NewChannel`). When they are `nil`, receiving from a nil channel blocks forever. However, because of the `default` branch at line 220, the select will never actually block — it will fall through. The real problem is that if `zoneLocalMsgChan` is nil but `regionLocalMsgChan` is non-nil (or vice versa), the select cases for nil channels are simply never chosen, which is correct Go semantics. **Downgrading to QUESTION**: is the intent to also drain `zoneLocalMsgChan`/`regionLocalMsgChan` when they're nil? As written, nil channels are silently skipped, which is correct behavior but potentially confusing.

- **Line 232:** QUESTION (Low). `flush()` reads `len(c.zoneLocalMsgChan)`, `len(c.regionLocalMsgChan)`, `len(c.inFlightMessages)`, and `len(c.deferredMessages)` without holding their respective locks. This is used only for a log message so it's not a correctness issue, but the values of `len(c.inFlightMessages)` and `len(c.deferredMessages)` may be stale or inconsistent.

- **Line 332-380:** BUG (Medium). In `put()` when `topologyAwareConsumption` is enabled and `memoryMsgChan` is `nil` (which happens when `MemQueueSize == 0` and the channel is not ephemeral, per line 103-105), the third select block at lines 353-361 includes `c.memoryMsgChan` which is `nil`. Sending to a nil channel blocks forever in a select — so this case is simply never selected, which means the `default` branch is taken and the message goes to backend. This is functionally correct but means the topology-aware priority channels (`zoneLocalMsgChan`, `regionLocalMsgChan`) are also included in that select and could still win, sending the message to an in-memory channel rather than the disk backend, contradicting the stated intent at line 102: "avoid mem-queue if size == 0 for more consistent ordering." **This differs from the non-topology path** (lines 363-369) which correctly skips `memoryMsgChan` when it's nil because the select with a nil channel and default just falls through immediately to backend write.

- **Line 462-479:** BUG (High). `AddClient()` has a TOCTOU race condition. At line 463, it reads `c.clients[clientID]` and `len(c.clients)` under `RLock`. At line 477, it writes `c.clients[clientID] = client` under `Lock`. Between the `RUnlock` and `Lock`, another goroutine could have added the same `clientID` or a different client, making the `numClients` check at line 472 stale. Two concurrent `AddClient` calls with different clientIDs could both pass the `maxChannelConsumers` check and both add, exceeding the limit. Similarly two calls with the same clientID could both see `ok == false` and both proceed to write (though writing the same key twice is idempotent for maps, the consumer count limit would have been checked against a stale value).

- **Line 637:** BUG (Medium). In `processDeferredQueue()`, the message is popped from the PQ at line 624 under `deferredMutex`, but then `popDeferredMessage` is called at line 633 which re-acquires `deferredMutex`. Between lines 625 (unlock) and 633 (re-lock), another goroutine could call `popDeferredMessage` for the same message ID (e.g., via a `RequeueMessage` that internally calls `popDeferredMessage`). If `popDeferredMessage` at line 633 fails (returns error), the code jumps to `exit` at line 635 — but the item has already been removed from the PQ at line 624. The message is now removed from the PQ but still in the `deferredMessages` map, leaving the data structures inconsistent. However, `processDeferredQueue` only processes items whose timeout has expired, and deferred messages should not be concurrently accessed by other paths, so this may be unlikely in practice. **Flagging as QUESTION**: can a deferred message ID be popped by another code path between lines 625-633?

- **Line 674:** BUG (Low). In `processInFlightQueue()`, after `popInFlightMessage` succeeds, `c.put(msg)` is called at line 675 to re-enqueue the timed-out message. If `c.put()` fails (backend write error), the error is silently discarded — the message is lost. The same pattern exists at line 637 in `processDeferredQueue()`.

### nsqd/topic.go

- **Line 376-381:** BUG (Medium). In `exit(deleted=true)`, the code iterates over `t.channelMap` and calls `delete(t.channelMap, channel.name)` on line 379 during iteration. Deleting map entries during range iteration is safe in Go, so this is not a crash bug. However, `channel.Delete()` on line 380 eventually calls `t.DeleteExistingChannel(c.name)` (via the `deleteCallback` set at line 121-123) which tries to acquire `t.Lock()` — but `t.Lock()` is already held at line 377. **This will deadlock.** The callback at line 121 captures `t` and calls `t.DeleteExistingChannel(c.name)` which calls `t.RLock()` at line 144, then `t.Lock()` at line 161. Since `t.Lock()` is held at line 377, `t.RLock()` at 144 will block forever (an RLock blocks if there's a pending or held write Lock). Wait — actually `channel.Delete()` calls `c.exit(true)` which calls `c.nsqd.Notify()` and then the channel's own exit logic; it does NOT call back into the topic's `DeleteExistingChannel`. Let me re-read... The `deleteCallback` is only invoked by `RemoveClient` when ephemeral channel has 0 clients (line 505-506). So `channel.Delete()` here does NOT trigger the `deleteCallback`. This is safe. **Withdrawing this finding.**

- **Line 376-381:** QUESTION (Low). During `exit(deleted=true)`, `channel.Delete()` is called while holding `t.Lock()`. `channel.Delete()` → `channel.exit(true)` → `c.nsqd.Notify(c, !c.ephemeral)` which may attempt `n.PersistMetadata()` which calls `n.GetMetadata()` which calls `topic.Lock()` (line 401 of nsqd.go). But `t.Lock()` is already held at line 377. If `Notify` runs synchronously and tries to acquire `t.Lock()`, this would deadlock. However, `Notify` wraps the persist call in a goroutine (`n.waitGroup.Wrap`), so it runs asynchronously and won't deadlock on the current goroutine. But the goroutine will block on `topic.Lock()` until the deletion loop finishes. This is fine since it will eventually proceed.

- **Line 96-100:** QUESTION (Low). `NewChannel` creates `regionLocalMsgChan` and `zoneLocalMsgChan` as unbuffered channels (`make(chan *Message)`) at lines 96-99. These are zero-capacity channels, meaning every send blocks until a receiver is ready. This is intentional for the topology-aware consumption priority mechanism (channel.put uses cascading select statements). But if no consumer with matching topology is connected, sends to these channels will always fall through to the default case in `put()`, which is correct behavior.

### nsqd/nsqd.go

- **Line 328-339:** BUG (Medium). `writeSyncFile()` is not atomic. It truncates the existing file with `O_TRUNC` on open (line 329), then writes. If the process crashes after truncation but before the write completes, the file is left empty or partially written. However, `PersistMetadata()` at lines 427-438 correctly uses a write-to-temp-then-rename pattern (tmpFileName at line 428, rename at 433), so metadata persistence IS atomic. The concern is that `writeSyncFile` is a general utility that could be called elsewhere unsafely, but currently it's only used by `PersistMetadata` which wraps it atomically. **Downgrading to QUESTION**: `writeSyncFile` itself is not atomic, but its only caller (`PersistMetadata`) compensates. If other callers are added in the future, they could lose data.

- **Line 389-415:** BUG (Medium). `GetMetadata()` iterates over `n.topicMap` (line 393) without holding `n.RLock()`. This is called from `PersistMetadata()` (line 423) which is called from `Notify()` under `n.Lock()` (line 593) and from `Exit()` under `n.Lock()` (line 464). So the lock IS held by the caller. However, `GetMetadata` is a public method and there is no documentation or enforcement that callers must hold the lock. If called from an HTTP handler or other context without the lock, this would be a data race on `n.topicMap`.

- **Line 401:** BUG (Low). Inside `GetMetadata()`, `topic.Lock()` (write lock) is acquired just to read `topic.channelMap`. A `topic.RLock()` (read lock) would suffice since the iteration only reads the map. Using a write lock unnecessarily blocks concurrent readers. This is a correctness issue if the write lock causes unexpected contention or deadlocks.

- **Line 463-472:** QUESTION (Medium). In `Exit()`, `n.PersistMetadata()` is called at line 464 under `n.Lock()`. `PersistMetadata` calls `GetMetadata(false)` which iterates `n.topicMap` and acquires `topic.Lock()` for each topic. Then at line 469, `topic.Close()` is called for each topic. If `PersistMetadata` fails (line 465), execution still continues to close topics. The metadata may be stale or missing on the next restart if the persist failed. This seems intentional (log and continue), but worth noting.

- **Line 581-597:** QUESTION (Low). In `Notify()`, the `loading` variable is captured at line 582 before the goroutine is spawned. If `isLoading` transitions from 1 to 0 between line 582 and when the goroutine executes, the goroutine uses the stale `loading=true` value and skips persistence. During normal startup this is fine since `Notify` calls during loading are expected to skip persistence. But it's a subtle timing dependency.

### nsqd/client_v2.go

- **Line 217:** BUG (High). `outputBufferTicker` in `messagePump` (protocol_v2.go:217) is created with `client.OutputBufferTimeout`, and `heartbeatTicker` (line 218) with `client.HeartbeatInterval`. If `OutputBufferTimeout` is 0 (which happens when the client sets `output_buffer_timeout` to -1 via IDENTIFY, see line 524-525), `time.NewTicker(0)` panics with "non-positive interval for NewTicker". Similarly, if `HeartbeatInterval` is 0 (client sets `heartbeat_interval` to -1, see line 505-506), the ticker creation at line 218 panics. **Cross-referencing with protocol_v2.go lines 298-308**: the identify event handler does check `identifyData.HeartbeatInterval > 0` before creating a new ticker, and `identifyData.OutputBufferTimeout > 0` before creating a new ticker. But the INITIAL tickers at lines 217-218 use the client defaults which could be 0. **Wait** — the defaults are set in `newClientV2`: `HeartbeatInterval` defaults to `nsqd.getOpts().ClientTimeout / 2` (line 232) and `OutputBufferTimeout` defaults to `nsqd.getOpts().OutputBufferTimeout` (line 214). These are from server config options and are validated at startup — checking options.go... The `OutputBufferTimeout` option default is likely >0 and `ClientTimeout` is likely >0. So the initial values should never be 0 unless the server is misconfigured. **Downgrading to QUESTION**: if server options allow `OutputBufferTimeout=0` or `ClientTimeout=0`, the initial ticker creation panics.

- **Line 293-298:** QUESTION (Low). In `Identify()`, the `identifyEvent` is sent to `IdentifyEventChan` with a non-blocking select (lines 296-298). If the channel already has a value (buffer size 1), the new identify event is silently dropped. This means a second IDENTIFY call's settings may not be applied in `messagePump`. However, IDENTIFY is checked to only work in `stateInit` (protocol_v2.go:383), so it can only be called once, making this safe.

- **Line 550-555:** QUESTION (Low). In `SetOutputBuffer()`, when `desiredSize != 0`, `c.Writer.Flush()` is called at line 551 and the Writer is replaced at line 555. This writes directly on the underlying `c.Conn` (or TLS conn). The `writeLock` is held, so this is safe from concurrent writes. No issue found.

- **Line 591:** BUG (Low). In `UpgradeTLS()`, `tlsConn.SetDeadline` is called at line 591 with a 5-second timeout for the handshake, but the deadline is never cleared after a successful handshake. The `SetDeadline` call sets both read and write deadlines. The next read/write in the IOLoop will reset the deadline (IOLoop sets `SetReadDeadline` at line 57 of protocol_v2.go, and `Send` sets `SetWriteDeadline`), so this is effectively harmless. But if there's a gap between the handshake completing and the next IOLoop iteration where a read/write occurs, the stale 5-second deadline could cause a spurious timeout. In practice, IOLoop immediately sets the read deadline, so this is unlikely.

### nsqd/protocol_v2.go (supplementary — reviewed for context on client_v2 and channel interactions)

- **Line 619:** BUG (Medium). `SUB` checks `atomic.LoadInt32(&client.State) != stateInit` at line 619, but IDENTIFY (line 383) also requires `stateInit`. Neither IDENTIFY nor SUB transitions the client to `stateConnected`. SUB jumps directly from `stateInit` to `stateSubscribed` at line 668. The `stateConnected` constant (client_v2.go:22) is defined but never used anywhere in the state machine. This means a client can SUB without ever calling IDENTIFY, skipping feature negotiation. If auth is enabled, `CheckAuth` at line 643 will catch unauthorized clients, but if auth is NOT enabled, a client can subscribe without identifying — this may be intentional for simplicity but means no heartbeat negotiation occurs (defaults are used).

- **Line 329-343:** QUESTION (Low). In `messagePump`, when a message is received from `zoneMsgChan` (line 329), `client.Channel.zoneLocalMsgCount` is incremented. When received from `regionMsgChan` (line 331), if `zoneLocal` is true, `zoneLocalMsgCount` is incremented instead of `regionLocalMsgCount`. This seems intentional — if a consumer is zone-local, all messages it receives count as zone-local regardless of which channel they came from. But it means the `regionLocalMsgCount` stat is never incremented for zone-local consumers, even when they receive region-local messages.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (High) | 1 |
| BUG (Medium) | 4 |
| BUG (Low) | 2 |
| QUESTION (Medium) | 2 |
| QUESTION (Low) | 7 |

**Key findings:**
1. **AddClient TOCTOU race** (channel.go:462-479) — RLock/Unlock/Lock gap allows maxChannelConsumers to be exceeded.
2. **Topology-aware put inconsistency with MemQueueSize=0** (channel.go:332-380) — Messages may go to in-memory priority channels even when MemQueueSize=0 and consistent ordering is desired.
3. **GetMetadata lacks own locking** (nsqd.go:389-415) — Public method relies on callers to hold the lock; a data race if called without it.
4. **SUB skips stateConnected** (protocol_v2.go:619) — stateConnected is defined but never used in the state machine.
5. **processInFlightQueue/processDeferredQueue silently drop put errors** (channel.go:637,674-675) — Timed-out or deferred messages are lost if backend write fails.

**Overall assessment:** NEEDS DISCUSSION — The AddClient race (#1) and the silent message loss on timeout re-enqueue (#5) are the most operationally concerning. The others are edge cases or documentation gaps.
