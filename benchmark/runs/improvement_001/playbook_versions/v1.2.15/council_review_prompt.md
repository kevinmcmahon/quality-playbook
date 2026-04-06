# Council Review: Quality Playbook v1.2.13

## Context

The Quality Playbook is a skill that generates code review protocols for any codebase. We are iteratively improving it using benchmark-driven methodology against the QPB dataset (2,564 real defects across 50+ repos).

**The problem we're solving:** In a controlled experiment on 57 NSQ defects (all using GPT-5.4 via Copilot CLI), the playbook v1.2.12 scored **38.6% direct hit rate** — slightly *worse* than the control condition (no playbook) at **43.9%**. Head-to-head analysis revealed:

- 17 defects caught by both conditions
- **8 defects caught ONLY by the control** (playbook suppressed them)
- 5 defects caught ONLY by v1.2.12 (playbook added value)
- 27 defects missed by both conditions

The core discovery: **the playbook replaces the model's broad scanning ability instead of supplementing it.** The structured focus areas make the model look *only* where they point, suppressing its natural ability to find "normal" bugs through broad code reading.

## What Changed in v1.2.13

Two structural changes:

### Change 1: Two-Pass Review Protocol

Added to `references/review_protocols.md`. The generated code review protocol now instructs the reviewer to perform two passes:

**Pass 1 (Guided):** Follow the focus areas and guardrails as before — this catches the architectural and category-specific defects the playbook targets.

**Pass 2 (Open):** Set aside the focus areas. Re-read each file top to bottom looking for any bug, regardless of category. Guardrails still apply (line numbers, read bodies, grep before claiming), but scope is unrestricted.

The rationale: the two passes produce the *union* of structured and unstructured review, not the intersection. Pass 1 catches what the playbook is optimized for. Pass 2 recovers the "normal" bugs that Pass 1 inadvertently suppresses.

### Change 2: New Focus Area Patterns (from 27-Miss Analysis)

Added to `SKILL.md` Step 5c/5d. Three new pattern categories:

1. **Subtle interaction bugs between configuration and runtime:**
   - Zero/empty config values at runtime boundaries (e.g., `mem-queue-size=0` creates unbuffered channel)
   - Race conditions between subsystem initialization and client requests
   - Flag override semantics (one flag clobbering explicit user settings for another)

2. **Protocol and wire format completeness:**
   - Multi-message binary framing correctness (MPUB-style batched messages)
   - Error response information leakage

3. **Validation completeness for protocol parameters:**
   - Range validation with domain knowledge (not just integer bounds, but sensible bounds)
   - Consistent validation across multiple entry points for the same parameter

## The 8 Suppressed Defects (Control Caught, Playbook Missed)

These are the defects the model finds on a broad scan but misses when constrained by focus areas:

1. **NSQ-06:** `flush()` called without holding the client's mutex — a straightforward data race the model spots when scanning broadly
2. **NSQ-11:** `RequeueMessage` doesn't check `Exiting` flag — missing guard on state transition
3. **NSQ-18:** SUB error silently discarded, client gets success response — error handling gap
4. **NSQ-22:** Infinite retry loop when validation always fails — no max-retry bound
5. **NSQ-30:** IPv6 address parsing doesn't handle bracket notation — string parsing edge case
6. **NSQ-41:** Test helper doesn't close file handles — resource leak in test code
7. **NSQ-44:** gzip/snappy level assignment order matters but isn't enforced — initialization ordering
8. **NSQ-54:** `Close()` filename ordering issue — resource cleanup sequence

**Pattern:** These are all "normal" bugs — wrong mutex usage, missing error checks, resource leaks, initialization ordering. They don't fit neatly into the playbook's structured categories (configuration validation, shutdown completeness, concurrent cleanup). A model doing an open scan finds them naturally.

**Question for the council:** Will the two-pass approach recover these 8 suppressed hits? Are there any that need specific guidance beyond "scan broadly"?

## The 27 Both-Missed Defects (Clustered by Pattern)

### Subtle Interaction Bugs (6)
- **NSQ-03:** `mem-queue-size=0` creates unbuffered channel, fundamentally changes backpressure behavior
- **NSQ-25:** SUB to ephemeral channel races with channel deletion — timing-dependent
- **NSQ-26:** `--tls-required` overrides explicit `--tls=false` — flag interaction
- **NSQ-32:** TLS client auth in `tls-required=tcp-https` mode doesn't enforce for HTTP — mode interaction
- **NSQ-34:** Empty topic/channel name triggers deadlock in `GetTopic("")` — zero-value input at runtime boundary
- **NSQ-56:** `messagePump` notification channel can miss signals — buffered channel signal loss

### Subtle Concurrency (5)
- **NSQ-47:** `Exit()` doesn't close TCP connections — only closes listener, active connections keep process alive
- **NSQ-50:** `SendMessage` reads `IsWriteReady()` without lock — unsafe concurrent read
- **NSQ-51:** `messagePump` reads `SubEventChan` from `Channel` that could be replaced — stale reference
- **NSQ-53:** `PeerInfo.lastUpdate` written from multiple goroutines without sync — data race on struct field
- **NSQ-58:** `TCPServer` goroutines not tracked after listener close — orphaned goroutines

### Validation Completeness (4)
- **NSQ-09:** REQ timeout not validated against `max_req_timeout` — missing bounds check
- **NSQ-15:** E2E processing latency percentile calculation wrong for small samples
- **NSQ-28:** Worker ID range should be 0-1023 per Snowflake spec, no validation
- **NSQ-35:** MPUB binary message framing — message count validation and binary parse correctness

### Error Message Quality / os.Exit (3)
- **NSQ-12, NSQ-23, NSQ-31:** Various error messages that hide the root cause, or `os.Exit` calls that skip cleanup

### Buffer/Resource Reuse (2)
- **NSQ-02:** Buffer reuse after `Flush()` — written data can be overwritten
- **NSQ-55:** Reader body not closed in HTTP client — connection pool leak

### Numeric/Math Edge Cases (2)
- **NSQ-40:** Division by zero when sample count is zero in stats
- **NSQ-42:** (skipped in benchmark — frontend JS)

### Platform-Specific (2)
- **NSQ-36:** Signal handling with `signal.Notify` on unbuffered channel — signals can be dropped
- **NSQ-38:** Windows file path handling differences

### Other (3)
- **NSQ-14:** Frontend notification polling doesn't reconnect on error
- **NSQ-33:** IDENTIFY command doesn't validate hostname field
- **NSQ-46:** `reflect.DeepEqual` for equality when order shouldn't matter — type system fragility

**Question for the council:** Which of these 27 patterns does the v1.2.13 guidance still miss? The new SKILL.md patterns target the "subtle interaction" and "validation completeness" clusters. Are there additional focus area patterns needed for the concurrency, buffer reuse, or platform-specific clusters?

## Specific Asks

1. **Two-pass effectiveness:** Is the two-pass protocol structure (guided + open) the right approach to recover suppressed defects? Are there risks (e.g., the model treating Pass 2 as optional, or the two passes producing redundant findings that dilute signal)?

2. **New pattern coverage:** Do the three new pattern categories (interaction bugs, protocol completeness, validation completeness) adequately cover the 27-miss clusters? What's still missing?

3. **Guidance specificity:** Are the new patterns in SKILL.md specific enough to survive two-hop propagation (skill → generated protocol → review findings)? Or are they too abstract to produce actionable focus areas when the skill generates a protocol for a new project?

4. **Risk of over-specification:** With each iteration, the playbook grows longer. Is there a risk that adding more focus area patterns makes the guided pass so long that the model loses focus? Should we cap the number of focus areas or prioritize differently?

5. **Open pass guidance calibration:** The current open pass instruction says "look for any bug you can find." Is this too vague? Should it include lightweight prompts (e.g., "pay attention to error handling, resource cleanup, and boundary conditions") without being so specific that it becomes a second guided pass?

## Files to Review

The full v1.2.13 changes are in:
- `SKILL.md` — Version bump, new focus area patterns in Step 5c/5d, two-pass reference in File 3 section
- `references/review_protocols.md` — Two-pass review structure added between guardrails and output format

Compare against the v1.2.12 versions to see exactly what changed.
