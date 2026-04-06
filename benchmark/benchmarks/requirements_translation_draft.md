# QPB Defect → Requirements Translation (Draft)

## Purpose

Translate ground truth defects from patch-note form ("X was broken, fix: Y") into
requirements-violation form ("Requirement R was violated because condition C holds in
location L"). This enables scoring that matches on *requirement violations* rather
than *fix descriptions*, and surfaces cases where the "defect" is actually debatable.

## Translation Format

Each entry has:
- **Requirement**: The implicit contract the code must satisfy
- **Violation**: How the code breaks that contract (location, mechanism, consequence)
- **Detection signals**: What a reviewer would say/notice if they found this
- **Ambiguity notes**: Whether the requirement is universally agreed or debatable

---

## Sample Translations (15 defects, spanning all major categories)

### NSQ-01 [High, concurrency]
**Patch note**: RemoveClient() read c.clients length outside mutex.
**Requirement**: Shared mutable state reads must be synchronized with writes. Specifically: any read of a field that another goroutine may concurrently modify must hold the protecting lock.
**Violation**: In `Channel.RemoveClient()`, `len(c.clients)` is read after `c.Lock()` is released but before the ephemeral deletion decision. A concurrent `AddClient()` can change the count between the unlock and the read.
**Detection signals**: "c.clients accessed without lock", "race condition in RemoveClient", "len(clients) after Unlock", "unsynchronized read of clients"
**Ambiguity**: None — this is a textbook data race.

### NSQ-04 [Critical, error handling]
**Patch note**: NSQD.Exit() closed TCP listener but not active TCP producer connections, causing indefinite wait.
**Requirement**: Graceful shutdown must terminate all active connections, not just stop accepting new ones. A shutdown sequence that closes the listener but leaves established connections open violates the liveness property of shutdown.
**Violation**: `NSQD.Exit()` closes the TCP listener socket but does not close or signal active producer connections. Producer goroutines block on reads that never complete, so `Exit()` hangs waiting for them to finish.
**Detection signals**: "Exit doesn't close active connections", "shutdown hangs", "listener closed but connections remain", "producer connections not terminated on exit"
**Ambiguity**: Low — but could argue "let connections drain" is valid if there's a timeout.

### NSQ-07 [High, missing boundary check]
**Patch note**: PutMessages() failed to update messageCount on partial failure.
**Requirement**: Accounting invariants must be maintained even on partial failure. If a batch operation processes N items and fails on item K, the accounting must reflect exactly K successful operations.
**Violation**: `PutMessages()` increments `messageCount` by `len(msgs)` regardless of how many messages actually succeeded. On partial failure, the count is inflated.
**Detection signals**: "messageCount wrong on partial failure", "count incremented by N instead of actual successes", "PutMessages accounting error"
**Ambiguity**: None — incorrect accounting is a clear defect.

### NSQ-08 [Medium, null safety]
**Patch note**: getMemStats() returned *memStats pointer; calling code could receive nil.
**Requirement**: Functions returning pointers to value types should either guarantee non-nil return or require callers to handle nil. Value semantics (returning by value) eliminate the nil risk entirely.
**Violation**: `getMemStats()` returns `*memStats`. If the underlying stats call fails, nil is returned. Callers (JSON serialization, statsd reporting) dereference without nil checks.
**Detection signals**: "getMemStats returns nil", "nil pointer dereference in stats", "memStats nil check missing"
**Ambiguity**: Low — but some might argue the callers should nil-check rather than the function changing its return type.

### NSQ-12 [High, configuration error]
**Patch note**: When -mem-queue-size=0, Channel and Topic created unbuffered memoryMsgChan instead of disabling it.
**Requirement**: Configuration value 0 for a queue size must mean "disabled" (no queue), not "unbuffered queue" (queue of capacity 0). The distinction matters because an unbuffered channel blocks on send, which is functionally different from disabled.
**Violation**: `NewChannel()` and `NewTopic()` create `make(chan *Message, size)` where size=0 creates an unbuffered channel instead of setting the channel to nil to skip the memory queue path entirely.
**Detection signals**: "mem-queue-size=0 creates unbuffered channel", "memoryMsgChan nil vs unbuffered", "zero queue size blocks"
**Ambiguity**: Moderate — the requirement "0 means disabled" is a design decision, not a universal law. Some systems use 0 to mean unbuffered. The defect is that NSQ's documentation and design intent say "disabled."

### NSQ-14 [High, state machine gap]
**Patch note**: REQ command rejected timeouts outside [0, MaxReqTimeout] with fatal error, disconnecting client.
**Requirement**: Protocol commands with out-of-range parameters should be rejected with a recoverable error, not a fatal error that drops the connection. Disconnecting a client for a bad parameter value is disproportionate.
**Violation**: The REQ handler validates the timeout parameter and, if it's outside bounds, sends `E_INVALID` which is a fatal protocol error. The client is disconnected. The fix clamps the value to the valid range instead.
**Detection signals**: "REQ timeout disconnects client", "fatal error for out-of-range timeout", "REQ should clamp not disconnect"
**Ambiguity**: Moderate — strict validation (reject bad input) vs. permissive (clamp to range) is a design choice. The defect is that disconnection is disproportionate to the error.

### NSQ-19 [Medium, validation gap]
**Patch note**: IDENTIFY deflate level handling logic inverted.
**Requirement**: Negotiated compression parameters must reflect client-requested values, clamped to server limits. The server should not silently replace a valid client request with a default.
**Violation**: IDENTIFY sets deflate level to 6 if the requested level is ≤ 0, then clamps to the configured max. If the client requests level 3 and the server max is 9, the client gets 6 instead of 3. The ordering of default-substitution and clamping is wrong.
**Detection signals**: "deflate level ignored", "deflate level always 6", "IDENTIFY deflate level wrong", "client requested deflate level overridden"
**Ambiguity**: None — the client explicitly requests a value and gets a different one.

### NSQ-23 [Critical, error handling]
**Patch note**: NSQD.Main() and New() called os.Exit(1) on startup errors, bypassing service manager.
**Requirement**: Library/daemon code must propagate errors to the caller, not terminate the process. Calling os.Exit() prevents the service manager (systemd, supervisor, etc.) from performing cleanup, logging, or restart decisions.
**Violation**: Multiple paths in `NSQD.Main()` and `NSQD.New()` call `os.Exit(1)` on configuration and listen errors instead of returning an error.
**Detection signals**: "os.Exit in library code", "NSQD.Main calls os.Exit", "startup errors bypass caller", "process termination instead of error return"
**Ambiguity**: Low — os.Exit() in library code is widely considered an antipattern. But in a standalone daemon that IS the process, it's more debatable.

### NSQ-27 [High, missing boundary check]
**Patch note**: SpreadWriter.Flush() panic on zero writes. Divided by len(s.buf) without bounds check.
**Requirement**: Division operations must guard against zero denominators, especially when the denominator depends on runtime state (buffer contents, collection size, user input).
**Violation**: `SpreadWriter.Flush()` divides by `len(s.buf)`. If no writes occurred, `s.buf` is empty, causing a division-by-zero panic.
**Detection signals**: "SpreadWriter divide by zero", "len(s.buf) zero", "Flush panic on empty buffer"
**Ambiguity**: None — division by zero is always a defect.

### NSQ-33 [High, security]
**Patch note**: nsqadmin tombstoneNodeForTopicHandler missing authorization check.
**Requirement**: All mutating admin endpoints must enforce authorization. Omitting an auth check on one endpoint while checking others creates an authorization bypass.
**Violation**: `tombstoneNodeForTopicHandler` does not call `isAuthorizedAdminRequest()` before processing the tombstone operation. Any unauthenticated request can tombstone a topic node.
**Detection signals**: "tombstone missing auth", "authorization bypass", "tombstoneNodeForTopic no auth check", "unauthenticated tombstone"
**Ambiguity**: None — missing auth on a mutating endpoint is a clear security defect.

### NSQ-37 [Medium, protocol violation]
**Patch note**: IPv6 broadcast address handling — string concat produces invalid host:port for IPv6.
**Requirement**: Network address formatting must use net.JoinHostPort (or equivalent) to correctly handle both IPv4 and IPv6. Raw string concatenation of host + ":" + port breaks when host contains colons.
**Violation**: `Producer.HTTPAddress()` and `TCPAddress()` use `fmt.Sprintf("%s:%d", host, port)` which produces `fd4a::1:4150` for IPv6 — ambiguous parsing (is 4150 part of the address or the port?).
**Detection signals**: "IPv6 address formatting", "JoinHostPort", "host:port concat breaks IPv6", "IPv6 brackets missing"
**Ambiguity**: None if IPv6 support is a requirement. If the system only targets IPv4, this is a feature request.

### NSQ-38 [Medium, missing boundary check]
**Patch note**: E2eProcessingLatencyAggregate division by zero when count is 0.
**Requirement**: Statistical aggregation over potentially empty datasets must handle the zero-count case. Division by count without checking for zero causes panic or NaN propagation.
**Violation**: Percentile aggregation divides by `p[i]["count"]` without checking if count is zero. When no data points exist, division by zero occurs.
**Detection signals**: "division by zero in percentile", "count zero in aggregation", "E2eProcessingLatency divide by zero"
**Ambiguity**: None — arithmetic on empty collections must handle the empty case.

### NSQ-45 [Medium, concurrency]
**Patch note**: Topic.exit() iterated over channelMap without acquiring RLock.
**Requirement**: Map iteration in Go must be synchronized if any other goroutine may concurrently modify the map. Unsynchronized iteration causes undefined behavior (crash, partial reads).
**Violation**: `Topic.exit()` iterates `t.channelMap` without holding `t.RLock()`. Stats collection and channel creation/deletion hold the write lock and modify the map concurrently.
**Detection signals**: "channelMap without lock", "exit iterates map unsynchronized", "Topic.exit race on channelMap"
**Ambiguity**: None — unsynchronized map iteration in Go is a documented runtime crash.

### NSQ-48 [Medium, error handling]
**Patch note**: FileLogger.Close() performed Sync() before closing GZIP writer. Pending data lost.
**Requirement**: Resource cleanup ordering must flush higher-level wrappers before lower-level ones. Syncing the underlying file before closing the GZIP writer loses buffered compressed data.
**Violation**: `FileLogger.Close()` calls `f.Sync()` then `gzipWriter.Close()`. The GZIP writer holds buffered data that hasn't been flushed to the file. Sync writes whatever's in the OS buffer, but the GZIP buffer is still in memory.
**Detection signals**: "Sync before GZIP close", "buffered data lost on close", "cleanup ordering wrong", "GZIP writer close after sync"
**Ambiguity**: Low — but only matters if the GZIP writer actually has buffered data at close time.

### NSQ-51 [High, concurrency]
**Patch note**: Channel.exit() iterated over clients map without lock.
**Requirement**: Same as NSQ-45 — map iteration must be synchronized with concurrent modifications.
**Violation**: `Channel.exit()` iterates `c.clients` without holding `c.RLock()`. Concurrent `AddClient()` / `RemoveClient()` modify the map.
**Detection signals**: "clients map without lock in exit", "Channel.exit race", "unsynchronized client iteration"
**Ambiguity**: None.
