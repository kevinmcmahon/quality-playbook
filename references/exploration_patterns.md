# Exploration Patterns for Bug Discovery

This reference defines the exploration patterns that Phase 1 must apply to every core module in scope. These patterns target the bug classes most commonly missed when exploration stays at the subsystem or architecture level.

Requirements problems are the most expensive to fix because they are not caught until after implementation. The exploration phase is requirements elicitation — it determines what the code review and spec audit will look for. A requirement that is never derived is a bug that is never found. These patterns exist to systematically surface requirements that broad exploration misses.

Each pattern includes a definition, the bug class it targets, diverse examples from different domains, and the expected output format for EXPLORATION.md.

---

## Pattern 1: Fallback and Degradation Path Parity

### Definition

When code provides multiple strategies for accomplishing the same goal — a primary path and one or more fallback paths — each fallback must preserve the same behavioral invariants as the primary. The fallback may use a different mechanism, but the observable contract must be equivalent.

### Bug class

Fallback paths are written later, tested less, and reviewed with less scrutiny than primary paths. They often omit steps the primary path performs (validation, cleanup, index assignment, resource release) because the developer copied the primary path and simplified it for the "degraded" case. The result is a function that works correctly in the common case but violates its contract when the fallback activates.

### Examples across domains

- **Authentication:** A web service tries OAuth token validation, falls back to API key lookup, falls back to session cookie. Each fallback must enforce the same authorization scope. Bug: the API key fallback skips scope validation and grants full access.
- **Connection pooling:** A database client tries the primary connection pool, falls back to a secondary pool, falls back to creating a one-off connection. Each path must apply the same timeout and transaction isolation settings. Bug: the one-off connection fallback uses the driver default isolation level instead of the configured one.
- **Resource allocation:** A memory allocator tries a fast slab path, falls back to a slow page-level path. Both must zero-initialize sensitive fields. Bug: the slow path returns uninitialized memory because zero-fill was only in the slab fast path.
- **Interrupt vector setup:** A driver tries per-resource interrupt vectors, falls back to shared vectors, falls back to a single legacy interrupt line. Each fallback must configure all resources (including auxiliary channels) using the device-reported identifiers. Bug: the legacy fallback uses a loop counter for resource indexing instead of querying the device for the correct index.
- **Serialization:** A message broker tries binary serialization, falls back to JSON, falls back to string encoding. Each path must preserve the same field ordering and null-handling semantics. Bug: the JSON fallback silently drops null fields that binary serialization preserves.

### How to apply

For each core module, look for: conditional chains that try one approach then fall through to another, strategy/adapter patterns where multiple implementations are selected at runtime, retry logic with different strategies per attempt, feature-negotiation cascades where capabilities determine which code path runs.

For each cascade found:
1. List the primary path and every fallback.
2. For each fallback, check whether it performs the same critical operations as the primary (validation, resource setup, index assignment, cleanup, error reporting).
3. Any operation present in the primary but missing in a fallback is a candidate requirement.

### EXPLORATION.md output format

```
## Fallback Path Analysis

### [Name of cascade]
- **Primary path:** [function, file:line] — [what it does]
- **Fallback 1:** [function, file:line] — [what it does, what differs]
- **Fallback 2:** [function, file:line] — [what it does, what differs]
- **Parity gaps:** [specific operations present in primary but missing in fallback]
- **Candidate requirements:** REQ-NNN: [fallback must do X]
```

---

## Pattern 2: Dispatcher Return-Value Correctness

### Definition

When a function dispatches on input type or condition and must return a status value, the return value must be correct for every combination of inputs — not just the primary case. Dispatchers that handle multiple event types, request types, or state transitions are particularly prone to return-value bugs in edge combinations.

### Bug class

Dispatchers are typically written and tested for the common case. The return value is correct when the primary event fires. But when an unusual combination occurs (only a secondary event, no events at all, multiple concurrent events), the return-value logic may be wrong — returning "not handled" for a handled event, returning success for a partial failure, or returning a stale value from a previous iteration.

### Examples across domains

- **HTTP middleware:** A request dispatcher checks for authentication, rate-limiting, and routing. When rate-limiting triggers but authentication was already set, the dispatcher returns the auth status code instead of the rate-limit status code. Bug: rate-limited requests get 401 instead of 429.
- **Event loop:** A poll/select loop handles read-ready, write-ready, and error conditions. When only an error condition fires on a socket with no pending reads, the loop returns "no events" because the read-ready check was false. Bug: connection errors are silently ignored.
- **State machine transition:** A state machine dispatch function handles valid transitions, invalid transitions, and no-op transitions. When a no-op transition occurs (current state == target state), the function returns an error code intended for invalid transitions. Bug: idempotent operations fail when they should succeed.
- **Interrupt handler:** A hardware interrupt handler checks for multiple event types (data-ready, configuration-change, error). When only a secondary event fires (e.g., config change with no data), the handler returns "not mine" because the primary event check failed and the secondary path doesn't set the handled flag. Bug: legitimate secondary events are reported as spurious.
- **Command parser:** A CLI dispatcher matches subcommands and flags. When an unknown flag is combined with a valid subcommand, the dispatcher returns the subcommand's success code instead of a flag-error code. Bug: invalid flags are silently ignored.

### How to apply

For each core module, look for: functions with switch/case or if-else chains that return a status, interrupt/event handlers that handle multiple event types, request dispatchers that check multiple conditions before returning, state machine transition functions.

For each dispatcher found:
1. Enumerate all input combinations (not just the ones with explicit case labels — also the implicit "else" and "default" paths).
2. For each combination, trace the return value.
3. Any combination where the return value doesn't match the expected semantics is a candidate requirement.

### EXPLORATION.md output format

```
## Dispatcher Return-Value Analysis

### [Function name] at [file:line]
- **Input types:** [list of conditions/events the function dispatches on]
- **Combinations checked:**
  - [Condition A only]: returns [X] — correct/incorrect because [reason]
  - [Condition B only]: returns [X] — correct/incorrect because [reason]
  - [Both A and B]: returns [X] — correct/incorrect because [reason]
  - [Neither A nor B]: returns [X] — correct/incorrect because [reason]
- **Candidate requirements:** REQ-NNN: [function must return Y when only B fires]
```

---

## Pattern 3: Cross-Implementation Contract Consistency

### Definition

When multiple functions implement the same logical operation for different contexts (different transports, different backends, different protocol versions), they should all satisfy the same specification requirement. A step that is mandatory in the specification must appear in every implementation — a missing step in one implementation that is present in another is a strong bug signal.

### Bug class

When the same operation is implemented in multiple places, each implementation is typically written by a different developer or at a different time. The specification says "reset must wait for completion," and the developer of implementation A writes the wait loop, but the developer of implementation B writes only the reset trigger and forgets the wait. The bug is invisible when testing implementation B in isolation because it "works" on fast hardware — the race condition only manifests under load or on slow devices.

### Examples across domains

- **Device reset:** A spec says "the driver must write zero and then poll until the status register reads back zero." The PCI implementation includes the poll loop. The MMIO implementation writes zero but does not poll. Bug: MMIO reset can race with reinitialization.
- **Database driver:** A connection-close spec says "the driver must send a termination message, wait for acknowledgment, then release the socket." The PostgreSQL driver does all three. The MySQL driver sends the termination message and releases the socket without waiting for acknowledgment. Bug: the server may process the termination after the socket is reused.
- **Serialization format:** A protocol spec says "all strings must be UTF-8 normalized to NFC before comparison." The JSON serializer normalizes. The protobuf serializer does not. Bug: the same logical string compares as different depending on which serializer wrote it.
- **Cache invalidation:** A cache spec says "invalidation must remove the entry and notify all subscribers." The in-memory cache does both. The distributed cache removes the entry but does not broadcast the notification. Bug: other nodes serve stale data.
- **File locking:** A storage spec says "lock acquisition must set a timeout and clean up on failure." The local filesystem implementation sets the timeout. The NFS implementation uses blocking lock with no timeout. Bug: NFS lock contention can hang the process indefinitely.

### How to apply

For each core module, look for: the same operation name implemented in multiple files or classes, interface/trait implementations across different backends, protocol-version-specific implementations of the same message, transport-specific implementations of the same lifecycle operation.

For each pair (or set) of implementations:
1. Identify the specification requirement they share.
2. List the mandatory steps from the spec.
3. Check each implementation for each step.
4. Any step present in one but missing in another is a candidate requirement.

### EXPLORATION.md output format

```
## Cross-Implementation Consistency

### [Operation name] — [spec reference]
- **Implementation A:** [function, file:line] — performs steps: [1, 2, 3]
- **Implementation B:** [function, file:line] — performs steps: [1, 3] (missing step 2)
- **Gap:** [Implementation B missing step 2: description]
- **Candidate requirements:** REQ-NNN: [all implementations of X must perform step 2]
```

---

## Pattern 4: Whitelist/Enumeration Completeness

### Definition

When a function maintains an explicit list of accepted values — a switch/case whitelist, an array of valid constants, a set of recognized enum members — every value that the specification or upstream definition says should be accepted must appear in the list. Values not in the list are silently dropped or rejected, and the absence of an entry is invisible at the call site.

### Bug class

Whitelists are written once and rarely revisited. When a new capability is added to the specification or upstream header, the code that defines the capability (the constant, the feature flag, the enum variant) is updated, and the code that uses the capability is updated, but the whitelist that gates whether the capability survives a filtering step is forgotten. The feature appears to be supported — it's defined, it's negotiated, it's used — but it's silently stripped by a filter function that nobody remembered to update. The bug is invisible in normal testing because the feature simply doesn't activate, and the absence of activation looks like "the other end doesn't support it."

### Examples across domains

- **Feature negotiation filter:** A transport layer maintains a switch/case whitelist of feature bits that should survive filtering. A new feature (`RING_RESET`) is added to the UAPI header and used by higher-level code, but never added to the whitelist. Bug: the feature is silently cleared during negotiation, disabling a capability the driver claims to support.
- **Permission system:** An authorization middleware maintains an array of recognized permission strings. A new permission (`audit:write`) is added to the role definitions but not to the middleware's whitelist. Bug: users with the `audit:write` role are silently denied access because the middleware doesn't recognize the permission.
- **Protocol message types:** A message router maintains a switch/case dispatch for recognized message types. A new message type is added to the protocol spec and the serialization layer, but not to the router. Bug: the new message type is silently dropped by the router's default case, and the sender receives no error.
- **Configuration validator:** A config parser validates keys against a known-good set. A new configuration option is added to the documentation and the consuming code, but not to the validator's accepted-keys list. Bug: the new option is rejected as "unknown" during config validation, even though the code that reads it works fine.
- **Codec registry:** A media framework maintains a set of supported codec identifiers. A new codec is implemented and registered in the codec factory, but not added to the capability-reporting set. Bug: capability negotiation reports the codec as unsupported, so peers never request it.

### How to apply

For each core module, look for: switch/case statements with explicit case labels and a default that drops/clears/rejects, arrays or sets of accepted values used for filtering or validation, registration functions where new entries must be added manually, any function whose purpose is "keep only the recognized items."

For each whitelist found:
1. Identify the authoritative source that defines what values should be valid (a spec, a header file, an upstream enum, a protocol definition).
2. Extract the whitelist mechanically (save the case labels, array entries, or set members to a file).
3. Compare the extracted whitelist against the authoritative source. Every value in the authoritative source that is absent from the whitelist is a candidate requirement.

### EXPLORATION.md output format

```
## Whitelist/Enumeration Completeness

### [Function name] at [file:line]
- **Purpose:** [what this whitelist gates — e.g., "feature bits that survive transport filtering"]
- **Authoritative source:** [where valid values are defined — e.g., "include/uapi/linux/virtio_config.h"]
- **Extracted entries:** [list of values in the whitelist, or reference to mechanical extraction file]
- **Missing entries:** [values present in the authoritative source but absent from the whitelist]
- **Candidate requirements:** REQ-NNN: [whitelist must include X]
```

---

## Extending This List

These patterns were derived from analyzing cases where an AI code review found bugs with seeded requirements but failed to find the same bugs through independent exploration. Each pattern represents a class of requirements that broad architectural summaries consistently miss.

To add a new pattern:
1. Identify a confirmed bug that was missed by exploration but would have been found with a specific analysis technique.
2. Generalize the technique: what question should the explorer have asked about the code?
3. Provide at least 5 diverse examples from different domains (not all from the same project).
4. Define the expected output format for EXPLORATION.md.
5. Add the pattern to this file and add the corresponding section to the EXPLORATION.md template in SKILL.md.

The goal is a library of systematic exploration techniques that accumulate over time as new bug classes are discovered.
