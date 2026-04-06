# Requirement Derivation Experiment

## Goal
For each of 24 NSQ defects (in api-contract, input-validation, security, resource-lifecycle categories), attempt to write a testable requirement using ONLY what's available in NSQ's documentation — README, ChangeLog, source code comments, and public docs. Do NOT look at fix commits.

## Classification
- **(a) Explicit**: The requirement is clearly stated in documentation or code comments
- **(b) Inferable**: The requirement is inferable from docs/comments but not explicitly stated
- **(c) Insufficient**: The docs don't contain enough signal to derive the requirement

## Documentation Sources Available
1. README.md — minimal, mostly links
2. ChangeLog.md — release notes with feature/bug descriptions
3. Source code comments — inline documentation, TODOs, design notes
4. options.go — default configuration values and ranges
5. nsqd.go — validation rules in New() function
6. protocol_v2.go — protocol handler comments
7. Public features & guarantees page (web) — at-least-once delivery, non-durable default

---

## API-CONTRACT (7 defects)

### NSQ-08: getMemStats() nil pointer handling
**Requirement attempt**: Functions returning pointers must handle the nil case, and callers must check for nil.
**Doc evidence**: options.go shows StatsdMemStats defaults to true (line ~144). nsqd.go shows getMemStats is called in stats reporting path. No comment documents what happens when MemStats is disabled.
**Classification**: **(c) Insufficient** — There's no documentation stating what getMemStats() should return when stats are disabled. The nil pointer hazard is a pure implementation detail not derivable from docs. You'd need to read the code path to see this.

### NSQ-12: mem-queue-size=0 semantics
**Requirement attempt**: When --mem-queue-size=0, messages should go directly to disk (no in-memory buffering).
**Doc evidence**: channel.go:102 comment says "avoid mem-queue if size == 0 for more consistent ordering". ChangeLog #1159: "don't buffer messages when `--mem-queue-size=0`" (1.2.1 feature). ChangeLog #1376: "allow unbuffered memory chan if ephemeral or deferred" (1.3.0 feature).
**Classification**: **(a) Explicit** — The code comment directly states the intent: size=0 means no memory queue. The ChangeLog entry describes the fix. The requirement is: "When mem-queue-size=0 and the channel is not ephemeral, no memory channel should be created — messages go directly to the backend disk queue."

**Derived requirement**: When `--mem-queue-size=0` and the topic/channel is not ephemeral, the implementation must not create a memory channel. Messages must be routed directly to the backend (disk) queue. An unbuffered channel (make(chan, 0)) is not equivalent to "no channel."

### NSQ-19: IDENTIFY deflate level negotiation
**Requirement attempt**: Server must honor the client's requested deflate level within the configured maximum.
**Doc evidence**: ChangeLog #927 (1.1.0): "fix deflate level handling". options.go: MaxDeflateLevel defaults to 6. protocol_v2.go: IDENTIFY feature negotiation sets DeflateLevel in response.
**Classification**: **(b) Inferable** — The ChangeLog mentions "fix deflate level handling" without specifying the exact bug. The IDENTIFY response includes DeflateLevel, implying the server should negotiate and honor it. The maximum is documented in options. The requirement that the server must use the client's level (clamped to max) is inferable but not explicitly stated.

**Derived requirement**: When a client negotiates deflate compression via IDENTIFY, the server must use the client's requested deflate level, clamped to the configured `--max-deflate-level`. The server must not substitute a default level when the client's request is valid.

### NSQ-37: IPv6 address formatting (Producer)
**Requirement attempt**: Network address strings must be valid for both IPv4 and IPv6 hosts.
**Doc evidence**: clusterinfo/types.go uses net.JoinHostPort() — the fixed version. ChangeLog #1186 (1.2.1): "fix nodes list with ipv6 addresses". The Go standard library documents that net.JoinHostPort properly brackets IPv6 addresses.
**Classification**: **(b) Inferable** — The ChangeLog explicitly mentions IPv6 address fixes. Go's net package documentation makes the JoinHostPort requirement well-known. The requirement is inferable: any code formatting host:port strings must handle IPv6 properly. But the specific location (Producer.HTTPAddress/TCPAddress using fmt.Sprintf) is not documented.

**Derived requirement**: All host:port address formatting must use `net.JoinHostPort()` or equivalent to produce valid addresses for both IPv4 and IPv6 hosts. Using `fmt.Sprintf("%s:%d")` is incorrect for IPv6.

### NSQ-42: IPv6 in nsqadmin URLs
**Requirement attempt**: Same as NSQ-37 but for admin UI links.
**Doc evidence**: Same ChangeLog #1186 (1.2.1): "fix nodes list with ipv6 addresses". nsqadmin is documented as an admin interface.
**Classification**: **(b) Inferable** — Same reasoning as NSQ-37. If the project has IPv6 support and the ChangeLog documents IPv6 fixes in nsqadmin, the requirement that URLs must handle IPv6 is inferable.

**Derived requirement**: URL construction in nsqadmin must bracket IPv6 addresses. Node list links must produce valid URLs regardless of whether the node's address is IPv4 or IPv6.

### NSQ-55: IDENTIFY response must reflect negotiated values
**Requirement attempt**: The IDENTIFY response must contain the actual negotiated parameter values, not server defaults.
**Doc evidence**: protocol_v2.go documents the IDENTIFY response fields including MsgTimeout. The protocol spec (web search) indicates IDENTIFY is for "feature negotiation." The response JSON includes the negotiated values for the client to use.
**Classification**: **(b) Inferable** — "Feature negotiation" implies a two-way process where the response tells the client what was agreed. If MsgTimeout is in the response, it should reflect what the client will experience. But no doc explicitly says "the response must contain the negotiated value, not the default."

**Derived requirement**: The IDENTIFY response must return the actual negotiated values for all client-configurable parameters (including msg_timeout). If the client requests a specific value and the server accepts it, the response must confirm that value, not the server's default.

### NSQ-57: Topic creation must notify messagePump for proactive channels
**Requirement attempt**: When a topic creates channels proactively, the messagePump must be notified so those channels receive messages.
**Doc evidence**: nsqd.go:512 comment: "topic is created but messagePump not yet started". topic.go documents the messagePump pattern with channel update notifications. The comment about startup ordering implies awareness of the race between topic creation and pump startup.
**Classification**: **(c) Insufficient** — The "not yet started" comment describes a timing constraint but doesn't state a requirement about proactive channel notification. The messagePump design is documented in code structure, but the specific requirement that pre-existing channels must be notified isn't stated anywhere. This is an emergent bug from the interaction of two correct subsystems.

**Derived requirement**: N/A — cannot derive from documentation alone.

---

## INPUT-VALIDATION (4 defects)

### NSQ-14: REQ timeout out-of-range should be recoverable error
**Requirement attempt**: Out-of-range parameters on protocol commands should produce non-fatal errors.
**Doc evidence**: protocol_v2.go:770 log comment: "REQ timeout %d out of range 0-%d. Setting to %d" — this is the FIXED behavior (clamping). ChangeLog #868 (1.1.0): "clamp requeue timeout to range instead of dropping connection". The protocol spec distinguishes E_INVALID (fatal) from E_BAD_BODY (recoverable).
**Classification**: **(a) Explicit** — The ChangeLog DIRECTLY states the fix: "clamp requeue timeout to range instead of dropping connection." This tells us the requirement: out-of-range timeouts should be clamped, not cause disconnection. The pre-fix code sent E_INVALID (fatal), which is documented as a connection-dropping error.

**Derived requirement**: When a REQ command specifies a timeout outside the valid range [0, MaxReqTimeout], the server must clamp the value to the valid range and continue processing. It must not send a fatal error (E_INVALID) that disconnects the client.

### NSQ-36: E2E latency percentile validation
**Requirement attempt**: Configuration values with domain constraints must be validated at parse time.
**Doc evidence**: nsqd.go:142-146 validates: "E2e processing latency percentile must be > 0 and <= 1.0". ChangeLog #988 (1.1.0): "fix e2e timings config example, add range validation".
**Classification**: **(a) Explicit** — The ChangeLog explicitly mentions "add range validation" for e2e timings. The nsqd.go validation code (which is the fix) states the constraint: must be in (0, 1]. The requirement is clearly documented in both the ChangeLog and the validation code.

**Derived requirement**: E2E processing latency percentile configuration values must be validated at parse time to ensure they are in the range (0, 1.0]. Values outside this range (including 0, negative numbers, or values > 1.0) must be rejected with a clear error message at startup.

### NSQ-39: Worker ID validation range vs bit width
**Requirement attempt**: Worker ID validation must match the actual bit width used in GUID generation.
**Doc evidence**: guid.go: nodeIDBits = 10 (max 1023). nsqd.go:115-116 validates ID in [0, 1024). The validation code in the repo (nsqd.go) already shows the corrected range. guid.go clearly documents the 10-bit field width.
**Classification**: **(b) Inferable** — guid.go documents the bit layout (nodeIDBits = 10, meaning max 1023). The validation in nsqd.go shows [0, 1024). The requirement that validation must match bit width is inferable from the GUID structure documentation. But no doc explicitly says "the old validation was wrong."

**Derived requirement**: Worker ID validation must reject values >= 2^nodeIDBits (1024). The valid range is [0, 1023] to match the 10-bit worker ID field in the GUID format. Accepting values 1024+ produces silent ID collisions.

### NSQ-56: MPUB binary parameter validation
**Requirement attempt**: Binary protocol parameters must be validated as the expected type.
**Doc evidence**: The TCP protocol spec describes MPUB format with numeric parameters (message count, sizes). protocol_v2.go parses these from binary. No specific comment about validating numeric fields in binary protocol commands.
**Classification**: **(c) Insufficient** — The binary protocol format is documented but the specific validation of numeric fields in MPUB isn't mentioned in any documentation. The requirement that non-numeric input should be rejected is a general programming principle, not something derivable from NSQ-specific docs.

**Derived requirement**: N/A — cannot derive from documentation alone.

---

## SECURITY (3 defects)

### NSQ-33: Admin endpoint authorization check
**Requirement attempt**: All mutating admin endpoints must enforce authorization.
**Doc evidence**: ChangeLog #1462 (1.3.0): "add admin check for topic/node tombstone endpoint". ChangeLog #914 (1.1.0): "X-Forwarded-User based 'admin' permission". nsqadmin uses isAuthorizedAdminRequest() pattern for admin actions.
**Classification**: **(a) Explicit** — The ChangeLog DIRECTLY documents: "add admin check for topic/node tombstone endpoint." This tells us the tombstone endpoint was missing the auth check. The X-Forwarded-User admin permission system is documented. The requirement is explicit: all admin-mutating endpoints must call isAuthorizedAdminRequest().

**Derived requirement**: All mutating admin endpoints in nsqadmin must call isAuthorizedAdminRequest() before processing. Endpoints that skip this check allow unauthenticated users to perform administrative operations (like tombstoning nodes).

### NSQ-41: TLS flag interaction (tls-client-auth-policy vs tls-required)
**Requirement attempt**: TLS configuration flags must not silently override each other in unexpected ways.
**Doc evidence**: nsqd.go:119-121 shows: "if TLSClientAuthPolicy is set but TLSRequired is NotRequired, auto-upgrade to TLSRequired." options.go documents both flags. The interaction between -tls-required and -tls-client-auth-policy is partially documented in the validation code.
**Classification**: **(b) Inferable** — The validation code documents the auto-upgrade behavior, which IS the fix. The interaction between the two flags is inferable from reading the configuration validation logic. An operator reading the code would expect that setting -tls-required should not be overridden by -tls-client-auth-policy.

**Derived requirement**: When -tls-required is explicitly set to true, setting -tls-client-auth-policy must not downgrade or override that setting. If -tls-client-auth-policy is set but -tls-required is not, the system should auto-upgrade -tls-required. The flags must not produce contradictory configurations.

### NSQ-44: Auth server TLS must use configured root CA
**Requirement attempt**: Outbound TLS connections to the auth server must use the configured root CA.
**Doc evidence**: ChangeLog #1473 (1.3.0): "use --tls-root-ca-file in nsqauth request". This directly documents the requirement. nsqd.go shows TLS configuration with RootCAs support.
**Classification**: **(a) Explicit** — The ChangeLog directly states: "use --tls-root-ca-file in nsqauth request." This tells us the auth server client was NOT using the configured root CA. The requirement is explicit.

**Derived requirement**: The HTTP client used for auth server (nsqauth) requests must use the TLS configuration specified by --tls-root-ca-file. It must not fall back to system default CAs when a custom root CA is configured.

---

## RESOURCE-LIFECYCLE (10 defects)

### NSQ-04: Graceful shutdown must close active connections
**Requirement attempt**: Server shutdown must close all active client connections, not just stop accepting new ones.
**Doc evidence**: ChangeLog #1198/#1190/#1262 (1.2.1): "synchronize close of all connections on Exit". nsqd.go Exit() sequence documented in comments. ChangeLog #1319/#1331/#1361 (1.2.1): "handle SIGTERM". The features page states NSQ supports "graceful shutdown."
**Classification**: **(a) Explicit** — The ChangeLog directly states "synchronize close of all connections on Exit." The Exit() function's documented sequence (close listeners → persist → close topics → exit) confirms the intended behavior. The requirement that all connections must be closed on exit is explicit.

**Derived requirement**: NSQD.Exit() must close all active TCP connections (both producer and consumer), not just close the listener. Connections that are not explicitly closed will block goroutines waiting on reads, preventing clean shutdown.

### NSQ-13: Close() on nil connection must not panic
**Requirement attempt**: Close() must be nil-safe for uninitialized resources.
**Doc evidence**: No documentation about nil-safety of lookupPeer.Close(). This is a general Go programming practice (nil pointer checks before method calls) but not documented for this specific case.
**Classification**: **(c) Insufficient** — There's no documentation about this specific nil-safety requirement. It's a general defensive programming practice. You'd need to trace the code to see that the connection might be nil.

**Derived requirement**: N/A — cannot derive from documentation alone.

### NSQ-15: Requeue must check channel exit state
**Requirement attempt**: Operations that modify channel state must check whether the channel is shutting down.
**Doc evidence**: channel.go documents Exiting() as an atomic flag check (lines 155-158). The channel lifecycle (Delete/Close) is documented. No specific comment about checking Exiting() before requeue operations.
**Classification**: **(c) Insufficient** — While the Exiting() mechanism is documented in code, there's no requirement document stating "all operations must check Exiting() before proceeding." The specific interaction between RequeueMessage() with timeout=0 and the exit state is not documented.

**Derived requirement**: N/A — cannot derive from documentation alone.

### NSQ-22: Server shutdown must wait for handler goroutines
**Requirement attempt**: The server must track and wait for all spawned goroutines before returning from shutdown.
**Doc evidence**: nsqd.go uses waitGroup pattern (line 476: "Waits for all waitGroup goroutines"). The TCPServer spawns handlers per connection. Go's general pattern of using WaitGroup for goroutine lifecycle is well-known.
**Classification**: **(b) Inferable** — nsqd.go documents the WaitGroup pattern for its own subsystems. The requirement that TCPServer should also track its handler goroutines is inferable from the established pattern, but the specific gap (TCPServer doesn't use WaitGroup for per-connection goroutines) isn't documented.

**Derived requirement**: TCPServer must track all spawned per-connection handler goroutines using a WaitGroup or equivalent mechanism, and wait for them to complete during shutdown. Goroutines that outlive the server can access freed resources.

### NSQ-29: HTTP client created inside loop should be hoisted
**Requirement attempt**: Resources allocated in a loop that should be allocated once must be hoisted.
**Doc evidence**: ChangeLog #935 (1.1.0): "fix connection leaks when using `--topic-pattern`" (nsq_to_file). ChangeLog #946 (1.1.0): "update internal http client with new go http.Transport features (keepalives, timeouts, dualstack)".
**Classification**: **(c) Insufficient** — While the ChangeLog mentions connection leak fixes in nsq_to_file, it doesn't describe the specific pattern of creating HTTP clients inside a loop. The requirement is a general programming principle (don't allocate loop-invariant resources inside loops) that isn't documented as a project-specific requirement.

**Derived requirement**: N/A — cannot derive from documentation alone.

### NSQ-46: Test code must close file handles (WEAK)
**Requirement attempt**: Test code should close all opened resources.
**Doc evidence**: No documentation about test resource cleanup standards. Strength is WEAK.
**Classification**: **(c) Insufficient** — No docs, and marked WEAK.

**Derived requirement**: N/A

### NSQ-47: Shutdown must close active client connections (duplicate of NSQ-04)
**Requirement attempt**: Same as NSQ-04.
**Doc evidence**: Same ChangeLog entries as NSQ-04.
**Classification**: **(a) Explicit** — Same as NSQ-04.

**Derived requirement**: Same as NSQ-04.

### NSQ-48: FileLogger must flush GZIP before file sync
**Requirement attempt**: Layered resource cleanup must flush higher-level wrappers before lower-level ones.
**Doc evidence**: file_logger.go documents the Sync behavior: "Sync flushes gzip writer and closes/reopens it (maintaining concatenated gzip stream)" (lines 233-247). ChangeLog #1117/#1120/#1123 (1.2.0): "big refactor, more robust file switching and syncing and error handling".
**Classification**: **(b) Inferable** — The file_logger.go sync code documents the flush-then-sync pattern. The ChangeLog mentions a "big refactor" for "more robust file switching and syncing." The requirement that GZIP must be flushed before the underlying file is synced is inferable from the layered I/O architecture, but the specific bug (syncing the file before flushing the GZIP buffer) isn't explicitly documented.

**Derived requirement**: When closing or syncing a compressed file, the GZIP writer must be flushed/closed before syncing or closing the underlying file. Syncing the file first loses buffered compressed data still in the GZIP writer.

### NSQ-49: FileLogger must close at correct point in sequence
**Requirement attempt**: Resource close must happen before reading dependent state.
**Doc evidence**: file_logger.go documents rotation behavior with revision handling (lines 208-221, 289-291). The updateFile() function handles file rotation.
**Classification**: **(c) Insufficient** — The file rotation logic is documented but the specific ordering bug (reading filename after the wrong close point) is not described in any documentation. This is a subtle sequencing issue only visible in the code.

**Derived requirement**: N/A — cannot derive from documentation alone.

### NSQ-50: OS signal channels must be buffered
**Requirement attempt**: Signal channels must have capacity >= 1 to avoid dropping signals.
**Doc evidence**: Go's signal.Notify documentation states: "Package signal will not block sending to c: the caller must ensure that c has sufficient buffer space to keep up with the expected signal rate." The apps/nsqd/main.go pattern shows the correct usage. nsq_to_file.go is the buggy version.
**Classification**: **(b) Inferable** — Go's signal.Notify contract is well-documented in the standard library: the channel must be buffered. NSQ's own main nsqd app uses buffered channels for signals. The requirement is inferable from Go's standard library documentation and from the pattern established elsewhere in the NSQ codebase.

**Derived requirement**: All channels passed to signal.Notify() must be buffered (capacity >= 1). Go's signal package documentation requires this: "the caller must ensure that c has sufficient buffer space." Unbuffered signal channels silently drop signals.

---

## Summary Distribution

| Classification | Count | Defect IDs |
|---|---|---|
| **(a) Explicit** — requirement clearly stated in docs | 7 | NSQ-12, NSQ-14, NSQ-36, NSQ-33, NSQ-44, NSQ-04, NSQ-47 |
| **(b) Inferable** — requirement derivable from docs | 9 | NSQ-19, NSQ-37, NSQ-42, NSQ-55, NSQ-39, NSQ-41, NSQ-22, NSQ-48, NSQ-50 |
| **(c) Insufficient** — docs don't contain signal | 8 | NSQ-08, NSQ-57, NSQ-56, NSQ-13, NSQ-15, NSQ-29, NSQ-46, NSQ-49 |

**Distribution: 7 explicit (29%), 9 inferable (38%), 8 insufficient (33%)**

Of the 8 "insufficient" defects:
- 1 is WEAK (NSQ-46) — debatable whether it's a real defect
- 3 are general programming practices not specific to NSQ (NSQ-08, NSQ-13, NSQ-29)
- 2 are emergent from subsystem interactions (NSQ-57, NSQ-15)
- 2 are subtle implementation details (NSQ-56, NSQ-49)

**Key finding**: 16 of 24 defects (67%) have requirements derivable from documentation — 7 explicit and 9 inferable. This suggests the intent harvesting approach has a solid foundation even with relatively sparse documentation. The 33% that can't be derived from docs are mostly general programming practices or emergent interaction bugs — exactly the kind of thing where broader intent sources (Stack Overflow, library docs, Go best practices) would help.
