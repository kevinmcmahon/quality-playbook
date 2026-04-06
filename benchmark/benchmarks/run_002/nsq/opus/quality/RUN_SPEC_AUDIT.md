# Spec Audit Protocol: NSQ

## The Definitive Audit Prompt

Give this prompt identically to three independent AI tools (e.g., Claude Code, Cursor, GitHub Copilot).

---

**Context files to read:**
1. `nsqd/README.md` — nsqd daemon description
2. `nsqlookupd/README.md` — Lookup service description
3. `nsqadmin/README.md` — Admin UI description
4. `quality/QUALITY.md` — Quality constitution and fitness-to-purpose scenarios
5. `go.mod` — Dependencies and Go version

**Task:** Act as the Tester. Read the actual code in `nsqd/`, `nsqlookupd/`, `nsqadmin/`, and `internal/` directories and compare it against the specifications listed above and the NSQ protocol documentation at https://nsq.io/clients/tcp_protocol_spec.html.

**Requirement confidence tiers:**
Requirements are tagged with `[Req: tier — source]`. Weight your findings by tier:
- **formal** — written in README or protocol spec. Authoritative. Divergence is a real finding.
- **user-confirmed** — stated by the user but not in a formal doc. Treat as authoritative.
- **inferred** — deduced from code behavior. Lower confidence. Report divergence as NEEDS REVIEW.

**Rules:**
- ONLY list defects. Do not summarize what matches.
- For EVERY defect, cite specific file and line number(s). If you cannot cite a line number, do not include the finding.
- Before claiming missing, grep the codebase.
- Before claiming exists, read the actual function body.
- Classify each finding: MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM
- For findings against inferred requirements, add: NEEDS REVIEW

**Defect classifications:**
- **MISSING** — Spec requires it, code doesn't implement it
- **DIVERGENT** — Both spec and code address it, but they disagree
- **UNDOCUMENTED** — Code does it, spec doesn't mention it
- **PHANTOM** — Spec describes it, but it's actually implemented differently than described

**Project-specific scrutiny areas:**

1. **Message lifecycle completeness in `nsqd/channel.go`:** Read `PutMessage()`, `FinishMessage()`, `RequeueMessage()`, `StartInFlightTimeout()`, and `TouchMessage()`. For every message that enters `inFlightMessages`, trace all possible exit paths. Is there any path where a message stays in `inFlightMessages` permanently? What happens when `TouchMessage()` is called on a message whose timeout has already expired? [Req: inferred — from Channel in-flight tracking]

2. **Protocol V2 state machine in `nsqd/protocol_v2.go`:** Read every command handler (IDENTIFY, SUB, RDY, FIN, REQ, TOUCH, CLS, AUTH, NOP, PUB, MPUB, DPUB). For each, verify that the state check at the top matches the documented protocol requirements. Can a client send SUB without IDENTIFY? Can a client send RDY before SUB? What happens if FIN is called in `stateClosing`? [Req: formal — protocol spec]

3. **Metadata persistence atomicity in `nsqd/nsqd.go`:** Read `PersistMetadata()`. Is the write atomic (temp file + rename pattern)? What happens if the process crashes mid-write? Read `LoadMetadata()` — what happens if the metadata file is corrupted (partial JSON, zero bytes)? [Req: inferred — from PersistMetadata() behavior]

4. **Topic `messagePump()` distribution correctness in `nsqd/topic.go`:** Read the `messagePump()` goroutine. When distributing a message to N channels, the first channel gets the original and subsequent channels get copies. What happens if channel deletion occurs between getting the channel list and distributing? Is the `RLock` held across the entire distribution? What happens if `NewMessage()` fails during copy? [Req: inferred — from messagePump() logic]

5. **nsqlookupd registration database consistency in `nsqlookupd/registration_db.go`:** Read `AddProducer()`, `RemoveProducer()`, `FindProducers()`, and `FilterByActive()`. Is the tombstone mechanism safe under concurrent access? Can a producer be simultaneously tombstoned and re-registered? Does `FilterByActive()` handle the transition correctly? [Req: inferred — from RegistrationDB concurrent access]

6. **Channel topology-aware consumption in `nsqd/channel.go`:** Read the `put()` method's topology-aware path. The code uses cascading `select` statements to try zone-local, region-local, then global delivery. Is this priority strictly enforced, or can a global message be delivered when a zone-local slot is available? What happens when topology configuration changes at runtime? [Req: inferred — from channel.put() topology logic]

7. **Graceful shutdown ordering in `nsqd/nsqd.go`:** Read `Exit()`. Verify: listeners closed first (stop accepting new connections), then metadata persisted, then topics closed, then channels flushed. Is there a race between `Exit()` and in-progress message publishing? Does the `WaitGroupWrapper` actually wait for all goroutines? [Req: inferred — from Exit() shutdown sequence]

8. **Queue scan loop timing in `nsqd/nsqd.go`:** Read `queueScanLoop()` and related functions. Under high deferred message volume (1000+ messages), can the scan loop fall behind? What's the worst-case latency between a deferred message's timeout expiring and its redelivery? Is `QueueScanSelectionCount` sufficient? [Req: inferred — from queueScanLoop behavior]

9. **Client authentication flow in `nsqd/protocol_v2.go`:** Read `IDENTIFY()` and `AUTH()` handlers. If `AuthHTTPAddresses` is configured but a client never sends AUTH, what happens? Can a client send PUB without authenticating? Is the `AuthState` correctly checked on every command that requires it? [Req: inferred — from auth.State usage]

10. **Ephemeral topic/channel deletion safety in `nsqd/channel.go` and `nsqd/topic.go`:** Read `RemoveClient()` for ephemeral channels and the `deleteCallback` chain. Is there a race between the last client disconnecting and a new client subscribing? Does `sync.Once` on `deleter` prevent this race, or does it make it worse (irreversible deletion)? [Req: inferred — from ephemeral deletion logic]

**Output format:**

### [filename.ext]
- **Line NNN:** [MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM] [Req: tier — source] Description. Spec says: [quote or reference]. Code does: [what actually happens].

---

## Running the Audit

1. Give the identical prompt above to three AI tools
2. Each auditor works independently — no cross-contamination
3. Collect all three reports

## Triage Process

After all three models report, merge findings:

| Confidence | Found By | Action |
|------------|----------|--------|
| Highest | All three | Almost certainly real — fix or update spec |
| High | Two of three | Likely real — verify and fix |
| Needs verification | One only | Could be real or hallucinated — deploy verification probe |

### The Verification Probe

When models disagree on factual claims:

1. **Select a model** — preferably one that did NOT make the disputed claim
2. **Give it the claim** — quote the finding exactly: "Model X claims that `PersistMetadata()` in `nsqd.go` does not use atomic file writes."
3. **Ask it to read the code** — "Read `nsqd.go` `PersistMetadata()` and report what actually happens."
4. **Compare** the probe result against the original claim

Never resolve factual disputes by majority vote — the probe reads the code with a specific question.

### Categorize Each Confirmed Finding

- **Spec bug** — Spec is wrong, code is fine → update spec
- **Design decision** — Human judgment needed → discuss and decide
- **Real code bug** — Fix in small batches by subsystem
- **Documentation gap** — Feature exists but undocumented → update docs
- **Missing test** — Code is correct but no test verifies it → add to functional tests
- **Inferred requirement wrong** — Inferred requirement doesn't match intent → correct in QUALITY.md

## Fix Execution Rules

- Group fixes by subsystem (`nsqd/`, `nsqlookupd/`, `internal/`), not by defect number
- **Batch size: 3–5 fixes per batch.** More than 5 risks introducing new bugs.
- Each batch: implement, run `go test -race ./...`, have all three auditors verify the diff
- At least two auditors must confirm fixes pass before marking complete

## Output

Save audit reports to `quality/spec_audits/YYYY-MM-DD-[model].md`
Save triage summary to `quality/spec_audits/YYYY-MM-DD-triage.md`
