# Code Review Protocol: NSQ

## Bootstrap (Read First)

Before reviewing, read these files for context:
1. `quality/QUALITY.md` — Quality constitution and fitness-to-purpose scenarios
2. `nsqd/options.go` — All configuration parameters and their defaults (184 lines)
3. `nsqd/nsqd.go` — Core daemon struct, lifecycle (New/Main/Exit), topic management, queue scan loop
4. `nsqd/protocol_v2.go` — TCP protocol: IDENTIFY negotiation, SUB/PUB/MPUB/DPUB commands, messagePump per-client goroutine
5. `nsqd/topic.go` — Topic struct, messagePump fan-out to channels, put/flush/exit lifecycle
6. `nsqd/channel.go` — Channel struct, in-flight/deferred priority queues, client management, topology-aware put
7. `nsqd/client_v2.go` — Client state machine (stateInit→stateSubscribed→stateClosing), IDENTIFY parameter validation, connection upgrades (TLS/Snappy/Deflate)
8. `nsqd/http.go` — HTTP API handlers: PUB, MPUB, topic/channel CRUD, config endpoint, stats
9. `nsqlookupd/nsqlookupd.go` — Lookup daemon lifecycle and Exit() pattern
10. `nsqd/lookup.go` — lookupLoop goroutine, peer connection management, topic/channel registration
11. `nsqd/tcp.go` — tcpServer.Handle (protocol magic routing) and tcpServer.Close (graceful client shutdown)

## What to Check

### Focus Area 1: Configuration Parameter Validation and Flag Interactions

**Where:** `nsqd/options.go` (all fields), `nsqd/nsqd.go:77-193` (New constructor validation), `nsqd/client_v2.go:500-584` (client-side IDENTIFY validation: SetHeartbeatInterval, SetOutputBuffer, SetSampleRate, SetMsgTimeout)

**What:**
- For each config parameter in `Options`, verify: (a) whether a validation check exists in `New()`, (b) whether the zero value has explicit semantics vs. being silently accepted, (c) whether flag interactions are guarded (e.g., `TLSClientAuthPolicy` forces `TLSRequired` at line 119 — does this overwrite an explicit user setting of `TLSNotRequired`?).
- For client-overridable parameters (heartbeat interval, output buffer size/timeout, msg timeout, sample rate): verify that the validation in `SetHeartbeatInterval`, `SetOutputBuffer`, `SetSampleRate`, `SetMsgTimeout` correctly handles the disable value (-1), the default-passthrough value (0), and the valid range. Check whether out-of-range values return an error (which becomes a FatalClientErr disconnecting the client) vs. clamping.
- Check `doConfig` in `http.go:628-670` — the PUT handler only allows `nsqlookupd_tcp_addresses` and `log_level`. Verify all other option names hit the `INVALID_OPTION` path. Check whether `swapOpts` at line 660 creates a proper copy or mutates shared state.
- Verify `boolParams` map in `http.go:28-33` covers all expected boolean representations. Check what happens when an unrecognized value is passed to `/mpub?binary=` (line 282-284 — unrecognized values default to `true` with a deprecation warning).

**Why:** Incorrect flag interaction can silently force TLS when the operator intended no TLS, or vice versa. Client IDENTIFY validation that disconnects instead of clamping causes unnecessary client churn. The `/config` endpoint mutating shared Options could cause data races.

### Focus Area 2: Input Validation Failure Modes (Clamp vs. Disconnect)

**Where:** `nsqd/protocol_v2.go:676-711` (RDY), `nsqd/protocol_v2.go:739-783` (REQ), `nsqd/protocol_v2.go:903-949` (DPUB), `nsqd/client_v2.go:500-584` (IDENTIFY parameter setters), `nsqd/http.go:213-261` (doPUB), `nsqd/http.go:263-339` (doMPUB)

**What:**
- **RDY command (line 700-706):** Out-of-range count returns `FatalClientErr` (disconnects the client). Compare with REQ command (line 762-773) which clamps timeout to `[0, MaxReqTimeout]` and logs the clamping. Determine whether RDY should also clamp rather than fatally disconnect — this is a key behavioral difference.
- **IDENTIFY validation setters:** Each setter (SetHeartbeatInterval, SetOutputBuffer, SetSampleRate, SetMsgTimeout) returns an error on invalid values. In `client.Identify()` at `client_v2.go:254-301`, errors propagate to `protocol_v2.go:419` which wraps them as `FatalClientErr`. Verify that every setter's valid range is documented and that the IDENTIFY response (line 442-474) echoes the *client's negotiated* values, not the server's defaults.
- **HTTP PUB/MPUB:** Check that `MaxMsgSize` enforcement in `doPUB` (line 217-230) and `MaxBodySize` enforcement in `doMPUB` (line 270-273) are consistent in error codes and off-by-one handling of the `readMax = max + 1` pattern.
- **DPUB defer timeout (line 922-927):** Returns `FatalClientErr` for out-of-range values. Compare with HTTP PUB defer validation (http.go line 247-250) which returns a 400 error. Verify the boundary conditions match (both use `[0, MaxDeferTimeout]`).

**Why:** Inconsistent validation failure modes (disconnect vs. clamp vs. HTTP error) across equivalent parameters creates confusing client behavior. A producer that sends a slightly-too-large RDY count gets fatally disconnected, losing all in-flight state, when a clamp-and-warn would be safer.

### Focus Area 3: Graceful Shutdown Resource Completeness

**Where:** `nsqd/nsqd.go:442-480` (NSQD.Exit), `nsqlookupd/nsqlookupd.go:86-99` (NSQLookupd.Exit), `nsqd/tcp.go` (tcpServer.Close), `nsqd/topic.go:356-403` (Topic.exit), `nsqd/channel.go:170-204` (Channel.exit), `nsqd/lookup.go` (lookupLoop exit path)

**What:**
- **NSQD.Exit (line 442-480):** Enumerate every resource type: (1) tcpListener — closed at line 449, (2) tcpServer (active TCP connections) — closed at line 453, (3) httpListener — closed at line 457, (4) httpsListener — closed at line 461, (5) topics and their channels — closed at lines 469-471, (6) exitChan — closed at line 475 to signal goroutines, (7) waitGroup — waited at line 476, (8) dirlock — unlocked at line 477, (9) context — cancelled at line 479. Verify ordering: listeners close before topics, topics flush before exitChan signals goroutines, goroutines finish before dirlock release.
- **NSQLookupd.Exit (line 86-99):** Check whether the DB (RegistrationDB) needs cleanup. Verify that tcpServer.Close() iterates and closes all active client connections (not just the listener). Check whether httpListener close also terminates active HTTP connections or only stops accepting new ones.
- **Topic.exit (line 356-403):** Verify that `close(t.exitChan)` at line 371 unblocks both the `messagePump` goroutine AND any goroutines blocked on `channelUpdateChan` or `pauseChan`. Check whether `t.waitGroup.Wait()` at line 375 correctly waits for `messagePump` to exit before flushing.
- **Channel.exit (line 170-204):** Verify that `client.Close()` at line 191 is called for ALL clients before flushing messages to backend. Check whether the `exitMutex` prevents new messages from being put after exit starts.
- **lookupLoop:** Verify that when `exitChan` is closed, all lookupPeer connections are explicitly closed. Check for goroutine leaks in the Notify path (line 581-598 in nsqd.go) — each Notify wraps a goroutine that selects on exitChan.

**Why:** Incomplete shutdown causes: (a) data loss if in-flight/deferred messages aren't flushed, (b) connection leaks if active connections aren't closed after listener stops, (c) goroutine leaks if background goroutines aren't signaled, (d) lock file left behind if dirlock isn't released.

### Focus Area 4: Concurrent Cleanup Ordering and Channel Lifecycle in Select

**Where:** `nsqd/topic.go:249-344` (messagePump select loop), `nsqd/protocol_v2.go:203-378` (client messagePump select loop), `nsqd/nsqd.go:676-728` (queueScanLoop select loop), `nsqd/channel.go:332-380` (Channel.put with topology-aware select), `nsqd/nsqd.go:576-598` (Notify goroutine)

**What:**
- **Topic messagePump (line 281-316):** When `exitChan` fires, `messagePump` exits — but messages may still be in `memoryMsgChan` or `backendChan`. Verify that `Topic.exit(false)` flushes these after messagePump exits (line 401-403 calls `t.flush()`). Check for a race: can a new message be put into `memoryMsgChan` between messagePump exit and `flush()`?
- **Client messagePump (protocol_v2.go line 203-378):** The select statement at line 278-347 has many cases. When `client.ExitChan` fires (line 345), the goroutine exits. Check whether in-flight messages for this client are properly cleaned up. The IOLoop at line 116-121 closes ExitChan and removes client from channel — verify no race between messagePump and IOLoop on client state.
- **queueScanLoop (nsqd.go line 676-728):** The `loop:` label with `goto loop` at line 719 re-enters the inner loop without re-checking `exitChan`. If channels are persistently dirty, this loop never checks for exit. Verify whether `workCh` or `responseCh` operations could block indefinitely during shutdown.
- **Channel.put topology-aware select (channel.go line 332-380):** The three nested selects (lines 341-363) attempt zone→region→memory channels with fallthrough. Check whether a nil channel (when topology is not configured) causes a panic in select. Verify that `memoryMsgChan` being nil (when `MemQueueSize == 0` and not ephemeral, line 103-105) doesn't cause the non-topology path (line 365-369) to always fall through to backend.
- **Notify goroutine (nsqd.go line 576-598):** Each call to `Notify` spawns a new goroutine via `waitGroup.Wrap`. This goroutine selects on `exitChan` or `notifyChan`. Check whether rapid topic/channel creation could spawn unbounded goroutines waiting on the single `notifyChan` (capacity 1, unbuffered — line 69 `make(chan interface{})`).

**Why:** Select statement ordering bugs cause: (a) lost messages during shutdown, (b) goroutines that never exit, (c) panics on nil channels, (d) unbounded goroutine growth under load.

### Focus Area 5: Topic and Channel Lifecycle — Delete vs. Close Paths

**Where:** `nsqd/topic.go:347-403` (Topic.Delete/Close/exit), `nsqd/channel.go:161-204` (Channel.Delete/Close/exit), `nsqd/nsqd.go:552-574` (DeleteExistingTopic), `nsqd/topic.go:143-177` (DeleteExistingChannel), `nsqd/channel.go:454-507` (AddClient/RemoveClient)

**What:**
- **Topic.exit delete path (line 376-387):** Iterates `channelMap` with `t.Lock()`, calling `delete(t.channelMap, channel.name)` while iterating — this is safe in Go, but verify. Then calls `channel.Delete()` which in turn calls `c.nsqd.Notify(c, ...)` — check whether this Notify can deadlock since we hold `t.Lock()` and Notify accesses `notifyChan`.
- **DeleteExistingTopic (nsqd.go line 552-574):** Takes `n.RLock()` to check existence, then `n.RUnlock()`, then calls `topic.Delete()`, then takes `n.Lock()` to remove from map. Check for TOCTOU: can another goroutine delete the same topic between the existence check and the `topic.Delete()` call? What happens if `topic.Delete()` is called twice (the `CompareAndSwap` at topic.go line 357 should prevent double-delete, but verify).
- **Channel ephemeral deletion (channel.go line 504-507):** When last client disconnects from ephemeral channel, `c.deleter.Do` runs `c.deleteCallback(c)` in a new goroutine. This calls `t.DeleteExistingChannel`. Check whether the channel might already be deleted (via Topic.exit delete path) causing a "channel does not exist" error.
- **Topic ephemeral deletion (topic.go line 172-173):** Same pattern. Check the race between the last channel being deleted (triggering topic delete callback) and a new SUB arriving that creates a new channel on the same topic.
- **SUB retry loop (protocol_v2.go line 650-667):** The retry loop handles the race between GetChannel and AddClient for ephemeral channels/topics. Verify that the retry limit (2 iterations with 100ms sleep) is sufficient and that the error path at line 664 doesn't leak the channel.

**Why:** Delete/close lifecycle bugs cause: (a) double-free panics, (b) use-after-close on channels, (c) orphaned disk queue files if Delete() isn't called, (d) goroutine leaks if messagePump isn't stopped before resources are freed.

### Focus Area 6: Message Delivery, In-Flight Tracking, and Timeout Processing

**Where:** `nsqd/channel.go:388-409` (TouchMessage), `nsqd/channel.go:411-422` (FinishMessage), `nsqd/channel.go:430-452` (RequeueMessage), `nsqd/channel.go:509-520` (StartInFlightTimeout), `nsqd/channel.go:644-679` (processInFlightQueue), `nsqd/channel.go:613-642` (processDeferredQueue), `nsqd/protocol_v2.go:355-367` (message delivery in messagePump)

**What:**
- **TouchMessage (line 388-409):** Pops the message from in-flight (removes from map), removes from PQ, calculates new timeout, then pushes back. Check for a race: between `popInFlightMessage` and `pushInFlightMessage`, the message is in neither structure — if `processInFlightQueue` runs concurrently, could it miss the message? Verify that `popInFlightMessage` checks `clientID` ownership (line 554).
- **processInFlightQueue (line 644-679):** Locks `inFlightMutex` to `PeekAndShift`, then unlocks, then calls `popInFlightMessage` which re-locks `inFlightMutex`. Check whether a concurrent `FinishMessage` could remove the message between `PeekAndShift` and `popInFlightMessage`, causing the `popInFlightMessage` to return "ID not in flight" error — and then `goto exit` stops processing (line 665), potentially leaving remaining timed-out messages unprocessed.
- **processDeferredQueue (line 613-642):** Same pattern — `PeekAndShift` under lock, then `popDeferredMessage` re-locks. Same race condition potential. When `popDeferredMessage` fails, `goto exit` at line 636 stops processing remaining items.
- **Message delivery (protocol_v2.go line 355-367):** After `StartInFlightTimeout`, calls `client.SendingMessage()` (increments InFlightCount), then `p.SendMessage`. If `SendMessage` fails, the goroutine goes to `exit` — but the message is already in the in-flight queue. Verify that `IOLoop` cleanup (line 116-121) handles orphaned in-flight messages for the disconnecting client.
- **Sample rate filtering (protocol_v2.go line 356-357):** When `sampleRate > 0` and the random check fails, `continue` skips the message entirely — it's consumed from the channel but never delivered or returned. Verify this is intentional (message is lost by design for sampling).

**Why:** In-flight tracking bugs cause: (a) message loss (consumed but never delivered or requeued), (b) message duplication (delivered to client but also requeued by timeout), (c) stuck deferred queues that stop processing after one race condition.

### Focus Area 7: HTTP API Input Handling and Error Consistency

**Where:** `nsqd/http.go:213-339` (doPUB, doMPUB), `nsqd/http.go:341-499` (topic/channel CRUD handlers), `nsqd/http.go:628-670` (doConfig), `nsqd/http.go:173-211` (getExistingTopicFromQuery, getTopicFromQuery)

**What:**
- **doPUB (line 213-261):** Check that `req.ContentLength` check at line 217 handles the case where `ContentLength` is -1 (chunked encoding, as noted in the TODO at line 214). When `ContentLength` is -1, the `> MaxMsgSize` check is skipped, but `readMax` at line 223 still limits the read. Verify consistency.
- **doMPUB text mode (line 294-331):** Messages are split by newline. Empty lines are silently discarded (line 320). Individual message size is checked against `MaxMsgSize` (line 324). Check: what happens if `msgs` is empty after all lines are processed (all empty)? `PutMessages` at line 333 would receive an empty slice.
- **getTopicFromQuery (line 193-211):** Creates topic if it doesn't exist via `s.nsqd.GetTopic(topicName)`. This is used by `doPUB`, `doMPUB`, and `doCreateTopic`. Verify that auto-creation is intentional for PUB/MPUB (it is — but confirm that topic name validation at line 206 prevents creation of invalid topic names).
- **getExistingTopicFromQuery (line 173-191):** Returns the topic only if it exists. Used by channel operations. Check that `channelName` validation occurs for operations that need it (doCreateChannel at line 430-437 uses `getExistingTopicFromQuery` which calls `GetTopicChannelArgs` — verify that channel name is validated there).
- **doConfig PUT (line 631-661):** Uses `MaxMsgSize + 1` as readMax for the config body. This seems like a copy-paste from doPUB. Config values shouldn't need the message size limit. Check whether this creates an artificial limit on config value size.
- **doPauseTopic/doPauseChannel:** Both use `strings.Contains(req.URL.Path, "unpause")` to distinguish pause from unpause (line 412, 483). Verify this is robust — a path like `/topic/pause?unpause=1` would match incorrectly (but the router should prevent this since routes are distinct).

**Why:** HTTP API bugs cause: (a) bypassing size limits via chunked encoding, (b) silent data loss when all messages in MPUB are empty, (c) auto-creating topics with invalid names, (d) config endpoint with wrong size limits.

### Focus Area 8: TLS, Authentication, and Connection Upgrade Ordering

**Where:** `nsqd/nsqd.go:119-131` (TLS config in New), `nsqd/nsqd.go:730-771` (buildTLSConfig), `nsqd/protocol_v2.go:380-524` (IDENTIFY with TLS/Snappy/Deflate upgrades), `nsqd/client_v2.go:586-642` (UpgradeTLS, UpgradeDeflate, UpgradeSnappy), `nsqd/protocol_v2.go:526-616` (AUTH, CheckAuth), `nsqd/client_v2.go:664-724` (QueryAuthd, IsAuthorized)

**What:**
- **buildTLSConfig (line 730-771):** The `default` case in the switch at line 749 sets `NoClientCert`. This means if `TLSClientAuthPolicy` is any unrecognized string (not "require" or "require-verify"), no client cert is required. Check whether this should validate against an allowed-value set and reject unknown values.
- **IDENTIFY upgrade ordering (protocol_v2.go line 484-523):** TLS upgrade happens first (line 484), then Snappy (line 497), then Deflate (line 510). After each upgrade, an OK response is sent. Check whether each upgrade's Reader/Writer replacement (client_v2.go line 598-599, 615-619, 635-637) correctly layers on top of the previous upgrade (TLS → Snappy/Deflate). Verify that `UpgradeDeflate` at line 610-611 checks for `tlsConn` to use the TLS connection, not the raw `Conn`.
- **AUTH state management (client_v2.go line 702-716):** `IsAuthorized` checks if auth is expired and re-queries. If `QueryAuthd` fails, it returns `false, err`. Check that the caller (CheckAuth at protocol_v2.go line 596-616) handles this error — at line 605, the error is logged and a `FatalClientErr` is returned. Verify that a transient auth server failure doesn't permanently disconnect a previously-authorized client.
- **TLS enforcement (protocol_v2.go line 172-173):** `enforceTLSPolicy` is called for all commands except IDENTIFY. Check what happens if a client sends SUB before IDENTIFY — does the TLS check work correctly when the client hasn't negotiated TLS yet?
- **UpgradeTLS deadline (client_v2.go line 591):** Sets a 5-second deadline for TLS handshake. Check whether this deadline is cleared after the handshake completes, or whether it persists and causes subsequent reads/writes to timeout after 5 seconds.

**Why:** TLS/auth bugs cause: (a) unencrypted connections when TLS is required, (b) authorization bypass when auth server is transiently unavailable, (c) connection failures from stale deadlines after TLS upgrade, (d) compression applied to raw connection instead of TLS connection.

### Focus Area 9: Queue Scan Loop and Worker Pool Management

**Where:** `nsqd/nsqd.go:616-640` (resizePool), `nsqd/nsqd.go:644-661` (queueScanWorker), `nsqd/nsqd.go:676-728` (queueScanLoop)

**What:**
- **resizePool (line 616-640):** Pool size is `max(1, min(numChannels * 0.25, QueueScanWorkerPoolMax))`. When contracting, sends to `closeCh` to terminate workers. Check whether the workers that receive the close signal are the *most recently started* ones or arbitrary ones. Since `closeCh` is unbuffered (line 679), verify that each send at line 630 blocks until a worker receives it — this means contraction is serialized and correct, but could be slow if workers are busy processing a channel.
- **queueScanLoop dirty loop (line 706-719):** The `goto loop` at line 719 re-enters the channel selection without checking `exitChan`. If the dirty percentage stays above the threshold, this loop runs indefinitely without checking for exit. Verify whether this is a shutdown hang risk.
- **Stale channel list (line 684-685, 692-693):** The channel list is refreshed every `QueueScanRefreshInterval` (default 5s). Between refreshes, deleted channels may still be in the list. `queueScanWorker` calls `c.processInFlightQueue(now)` and `c.processDeferredQueue(now)` — check whether these methods handle the case where the channel is exiting (both check `c.Exiting()` — verify this is sufficient).
- **Worker goroutine leak on shutdown (line 723-727):** `close(closeCh)` sends a zero value to all workers, causing them to return. But the `waitGroup.Wrap` at line 634-636 registers these workers. Verify that `n.waitGroup.Wait()` in `Exit()` correctly waits for all scan workers to finish.

**Why:** Queue scan bugs cause: (a) shutdown hangs if the dirty loop never yields, (b) processing messages on deleted/closed channels, (c) goroutine leaks if workers aren't properly signaled.

### Focus Area 10: NSQLookupd Registration Database and Peer Lifecycle

**Where:** `nsqlookupd/nsqlookupd.go:86-99` (Exit), `nsqlookupd/registration_db.go` (RegistrationDB operations), `nsqd/lookup.go` (lookupLoop, connectCallback), `nsqd/lookup_peer.go` (lookupPeer Connect/Close/Command)

**What:**
- **NSQLookupd.Exit (line 86-99):** Closes tcpListener, tcpServer, httpListener, then waits. Check whether the RegistrationDB has stale entries after exit — if nsqd instances were connected, their registrations persist in memory. Verify whether this matters (it shouldn't since the process is exiting, but check for any persistence).
- **lookupPeer reconnection:** Check whether `lookupLoop` handles peer disconnection and reconnection. If a lookupd peer goes down, does nsqd retry connections? Check the heartbeat ticker interval and whether failed heartbeats trigger reconnection or just log errors.
- **connectCallback topic/channel registration:** When nsqd connects to a new lookupd, `connectCallback` must register all existing topics and channels. Check whether this registration holds the nsqd lock (potential deadlock with topic/channel operations) and whether ephemeral topics/channels are correctly excluded.
- **Concurrent map access in RegistrationDB:** Check whether RegistrationDB operations are thread-safe. If multiple nsqd instances connect simultaneously, verify that registration operations don't race.

**Why:** Lookup registration bugs cause: (a) consumers unable to discover topics after lookupd restart, (b) deadlocks during nsqd→lookupd reconnection under load, (c) stale registrations causing consumers to connect to decommissioned nsqd instances.

## Guardrails

- **Line numbers are mandatory.** If you cannot cite a specific line, do not include the finding.
- **Read function bodies, not just signatures.** Don't assume a function works correctly based on its name.
- **If unsure whether something is a bug or intentional**, flag it as a QUESTION rather than a BUG.
- **Grep before claiming missing.** If you think a feature is absent, search the codebase. If found in a different file, that's a location defect, not a missing feature.
- **Do NOT suggest style changes, refactors, or improvements.** Only flag things that are incorrect or could cause failures.
- **Exhaust the sibling set.** When you find a bug in one method of a type, grep for every other method on that type and check them for the same bug pattern. When you find a boundary condition that breaks one call site, check every other call site that processes the same kind of input. The most common miss pattern: finding a bug once and not checking whether the same bug appears in sibling methods, sibling call sites, or sibling test fixtures.
- **Check validation failure modes, not just validation existence.** For each validation check you encounter, ask: "What happens when this fails?" If a client sends an out-of-range value, does the handler clamp it (correct) or fatally disconnect the client (almost always wrong)? If a protocol handler builds a response, does each field echo the client's negotiated value or the server's default? Don't stop at "validation exists" — trace the failure path.
- **Enumerate all resource types in Exit()/Close().** When reviewing shutdown code, list every resource type the component creates: listeners, active connections, goroutines/threads, backend stores, registration entries. Verify each has an explicit close call in the exit path. Closing a listener does NOT close active connections — if you see a listener close without a corresponding loop that iterates and closes active connections, that's a shutdown hang bug.
- **Audit configuration parameter completeness.** For each config parameter: (a) if one flag modifies another, check for a guard that prevents overwriting explicit user settings; (b) if a parameter accepts semantic values (booleans, enums), check for an explicit allowed-value map; (c) for if/else chains that assign config values, verify all branches assign the variable — a missing else clause silently uses the zero value.

## Output Format

Save findings to `quality/code_reviews/YYYY-MM-DD-reviewer.md`

For each file reviewed:

### filename.ext
- **Line NNN:** [BUG / QUESTION / INCOMPLETE] Description. Expected vs. actual. Why it matters.

### Summary
- Total findings by severity
- Files with no findings
- Overall assessment: SHIP IT / FIX FIRST / NEEDS DISCUSSION
