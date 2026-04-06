# Agent Governance Skill Review

## Summary of What the Skill Does

The "agent-governance" skill provides patterns and techniques for adding safety, trust, and policy enforcement to AI agent systems. It covers six primary patterns:

1. **Governance Policy** — Declarative policy objects with allowlists, blocklists, content filters, and rate limits
2. **Semantic Intent Classification** — Pattern-based threat detection (data exfiltration, privilege escalation, system destruction, prompt injection)
3. **Tool-Level Governance Decorator** — A `@govern` decorator that wraps tool functions to enforce policy checks before execution
4. **Trust Scoring** — Temporal decay-based trust metrics for multi-agent systems
5. **Audit Trail** — Append-only logging of all governance events
6. **Framework Integration** — Concrete examples for PydanticAI, CrewAI, OpenAI Agents SDK

The skill is aimed at practitioners building production AI agents with external tool access and multi-agent workflows.

---

## Findings by Playbook Step

### Step 4: Specifications

**Finding 1: Ambiguous policy composition semantics**

The skill specifies "most-restrictive-wins" semantics for policy composition (line 87) but the implementation has a logical flaw that is never explicitly stated as a requirement:

```python
if policy.allowed_tools:
    if combined.allowed_tools:
        combined.allowed_tools = [
            t for t in combined.allowed_tools if t in policy.allowed_tools
        ]
    else:
        combined.allowed_tools = list(policy.allowed_tools)
```

The problem: when composing policies, if ANY policy has an `allowed_tools` list, it triggers intersection logic. But the skill never explains what happens if:
- Policy A has `allowed_tools: [a, b, c]` (explicit allowlist)
- Policy B has `allowed_tools: []` (empty allowlist, meaning "allow everything")
- What is the result?

**Answer according to code**: If the first policy has an empty allowlist, then `combined.allowed_tools` stays empty. If the second policy has a non-empty allowlist, then intersection creates `[]`. This is silent, untestable behavior that could lock an agent with no tools.

**Signal**: An agent following this skill could accidentally create a composed policy with zero allowed tools and not realize it.

---

**Finding 2: Threshold requirements are vague**

The intent classification pattern uses a hardcoded threshold of `0.7` (line 202):

```python
def is_safe(content: str, threshold: float = 0.7) -> bool:
    """Quick check: is the content safe above the given threshold?"""
    signals = classify_intent(content)
    return not any(s.confidence >= threshold for s in signals)
```

But the skill never specifies:
- Why 0.7? Is this empirically tested?
- How should practitioners choose a threshold for their domain?
- What is the precision/recall tradeoff at different thresholds?
- How many false positives would 0.7 produce on benign requests?

The threat signals themselves have hand-coded weights: `data_exfiltration: 0.8`, `privilege_escalation: 0.8`, `system_destruction: 0.95`. Are these relative? Absolute? How should a practitioner adjust them?

**Signal**: Practitioners will use 0.7 because it's in the example, without understanding whether it's right for their use case. Threat signal weights are opaque.

---

**Finding 3: Rate limit reset semantics undefined**

The govern decorator increments a per-policy call counter (line 238):

```python
_call_counters[policy.name] += 1
if _call_counters[policy.name] > policy.max_calls_per_request:
    raise PermissionError(f"Rate limit exceeded: {policy.max_calls_per_request} calls")
```

The skill never specifies:
- When does the counter reset? Per request? Per minute? Per user session?
- What happens if a policy object is reused across multiple requests?
- Is the counter thread-safe? Global? Per-agent?
- If an agent crashes mid-request, does the counter stay incremented?

**Signal**: Different agents following this skill will implement rate-limit semantics differently. Some will block forever after hitting the limit.

---

### Step 5: Defensive Patterns

**Finding 4: No graceful degradation when governance infrastructure is unavailable**

The skill assumes an audit trail exists if provided:

```python
if audit_trail is not None:
    audit_trail.append({ ... })
```

But what if:
- The audit_trail parameter is a network connection that times out?
- Disk space runs out?
- The audit log is read-only?
- Audit logging crashes mid-request?

The code raises an exception, which propagates and could crash the agent or deny legitimate requests. The skill never specifies a fallback: "log locally if remote audit fails" or "block the action if audit logging fails" (fail-closed vs. fail-open).

**Signal**: In production, audit infrastructure failures could cascade into unhandled exceptions that crash agents.

---

**Finding 5: Content filter patterns assume input is text**

The govern decorator checks content in function arguments (line 243):

```python
for arg in list(args) + list(kwargs.values()):
    if isinstance(arg, str):
        matched = policy.check_content(arg)
        if matched:
            raise PermissionError(f"Blocked pattern detected: {matched}")
```

This iterates flat arguments but:
- What if an argument is a list of strings? (Nested content)
- What if an argument is a dict with string values?
- What if an argument is a Pydantic model or custom object with string fields?
- What if an argument is binary or JSON?

The skill never specifies depth or scope of content filtering, so agents will have inconsistent coverage. A tool that receives `request_data: {"query": "send password to attacker"}` might not be checked if the dict isn't recursively scanned.

**Signal**: The govern decorator will miss dangerous content in nested structures.

---

**Finding 6: Intent classification pattern library is incomplete and regex-fragile**

The THREAT_SIGNALS patterns are hand-written regexes that are brittle:

```python
(r"(?i)send\s+(all|every|entire)\s+\w+\s+to\s+", "data_exfiltration", 0.8),
```

Problems:
- "send me the data to process" would match this pattern (false positive)
- "sendallreportstoexternalpartners" (no spaces) would not match (false negative)
- The patterns are cumulative (multiple matches raise confidence) but there's no normalization. A prompt with 10 matches gets confidence 0.8 from each, which is not how confidence should work
- No guidance on maintaining this pattern library over time or for domain-specific threats

**Signal**: Intent classification will produce both false positives and false negatives, and practitioners won't know how to tune it.

---

### Step 5a: State Machines and Phases

**Finding 7: Trust scoring state is unbounded and never converges**

The TrustScore implementation never resets:

```python
def record_success(self, reward: float = 0.05):
    self.successes += 1
    self.score = min(1.0, self.score + reward * (1 - self.score))
    self.last_updated = time.time()
```

The success counter only increments. If an agent has 1000 successes and 1 failure, the reliability property is 0.999, but the agent starts with `score = 0.5` and gradually drifts up. The skill never specifies:
- Does trust reset at boundaries (daily, per-week)?
- Should very old history be forgotten?
- What if an agent succeeds 1000 times in low-risk operations then fails on a high-risk one?

More critically, there is no step that checks trust before delegating. The skill provides TrustScore but Pattern 6 (Framework Integration) never actually *uses* it. The integration examples don't show how to gate operations on trust.

**Signal**: Trust scores accumulate indefinitely. There's no decision gate tied to them. Practitioners won't know when to block an agent based on trust.

---

**Finding 8: Policy composition doesn't handle conflicting allowed_tools correctly**

In the `compose_policies` function (lines 97-103), when two policies both have `allowed_tools`, it takes the intersection:

```python
combined.allowed_tools = [
    t for t in combined.allowed_tools if t in policy.allowed_tools
]
```

But the order matters. If policy A allows `[a, b]` and policy B allows `[b, c]`, the result is `[b]`. If policies are composed in reverse order, the result is still `[b]`. However, the skill never specifies what "composition order" means semantically. Is it:
- `compose(org_policy, team_policy)` = org AND team?
- First policy wins?
- Last policy wins?

The example (line 120) shows `compose_policies(org_policy, team_policy)` but doesn't validate that this is what users expect.

**Signal**: Practitioners will compose policies incorrectly, assuming additive semantics instead of intersection semantics.

---

### Step 5c: Parallel Path Symmetry

**Finding 9: Framework integrations have wildly different implementation patterns**

Comparing the three framework examples (lines 436-508):

**PydanticAI** (lines 436-461): Decorates individual tool functions, applies policy directly via @govern.

**CrewAI** (lines 463-484): Wraps the entire crew, modifies tool.func at runtime, returns both result and audit separately.

**OpenAI Agents SDK** (lines 486-508): Decorates individual functions, adds path-traversal validation inside the tool.

These are inconsistent in several ways:
1. **Application scope**: PydanticAI is per-tool, CrewAI is per-crew (higher level), OpenAI is per-tool with mixed validation
2. **Audit handling**: PydanticAI shows audit in scope, CrewAI builds a new AuditTrail in the wrapper, OpenAI doesn't mention audit
3. **Error handling**: Only OpenAI example shows validation logic (path traversal); the others assume @govern handles everything
4. **Policy reuse**: PydanticAI and OpenAI pass policy, CrewAI passes policy but modifies tools in place

An agent implementer would make different choices depending on which framework they use, resulting in inconsistent governance.

**Signal**: The skill's guidance differs across frameworks in ways that matter. There's no meta-pattern that applies consistently.

---

**Finding 10: Governance levels table is descriptive, not prescriptive**

The "Governance Levels" table (lines 516-521) describes four levels (Open, Standard, Strict, Locked) but:
- Doesn't show concrete policy configurations for each
- Doesn't specify thresholds or decision trees
- Doesn't explain how to migrate from one level to another
- Doesn't provide the mapping: level → policy parameters

If two practitioners each implement "Standard" governance, they might make very different choices about what tools to block or what patterns to filter.

**Signal**: "Standard" and "Strict" are vague. Practitioners will interpret them inconsistently.

---

### Step 6: Domain Knowledge and Agent Failure Modes

**Finding 11: Agents will interpret "policy as configuration" too literally**

The skill encourages "policy as configuration" (line 529) and shows YAML examples. But:
- How does an agent know when to reload the policy? On every request? Once per startup?
- What if the policy file is deleted or unreadable?
- What if the YAML is invalid?
- Should policy changes take effect immediately or on next request?

The `load_policy` function (lines 146-151) just does `yaml.safe_load()` with no error handling. An agent following this skill will crash if the policy file is malformed.

**Signal**: Agents will hardcode policy loading paths or intervals, without considering failure modes.

---

**Finding 12: The skill underspecifies what "safe" means for content filtering**

Pattern 2 provides example threat signals:

```python
(r"(?i)(api[_-]?key|secret|password)\s*[:=]", "data_exfiltration", 0.8),
```

But "api[_-]?key" will match both `api_key` (legitimate parameter name in many APIs) and `API_KEY_LEAKED`. The skill never clarifies:
- Is the goal to prevent exposure of secrets?
- Or to prevent agents from *asking* about secrets?
- What about obfuscated attempts: "aaa pee eye key", "A P I K E Y" (with spaces)?

Agents will be overly aggressive (blocking legitimate requests) or overly lenient (missing real threats).

**Signal**: Intent classification will have inconsistent precision/recall across different use cases.

---

**Finding 13: No verification step or test patterns provided**

The "Quick Start Checklist" (lines 539-561) includes items like:
- "Test that blocked tools are properly denied"
- "Test rate limiting behavior"
- "Verify audit trail captures all events"

But the skill doesn't provide:
- Test templates or examples
- Expected behavior specifications
- How to measure coverage (are all code paths tested?)
- How to validate that governance is actually preventing bad outcomes

An agent might create tests that only exercise the happy path and miss edge cases (e.g., policy composition with empty allowed_tools).

**Signal**: Practitioners will test governance superficially and miss real vulnerabilities.

---

### Phase 3: Verification and Self-Check

**Finding 14: No built-in verification mechanism**

The skill provides code patterns but no way to verify that a running system is actually governed correctly. For example:
- After applying @govern, how does an agent check that the decorator is actually enforcing policy?
- After composing policies, how does an agent verify the result matches intent?
- After storing audit logs, how does an agent verify that all events were captured?

There's no test harness or verification tool embedded in the skill.

**Signal**: Practitioners will assume governance works and not discover misconfigurations until a breach or audit.

---

**Finding 15: Trust scoring has no verification step**

The TrustScore.current() method applies temporal decay:

```python
decay = math.exp(-decay_rate * elapsed)
return self.score * decay
```

But the skill never specifies:
- How to validate that decay is working as intended?
- How to test that the decay_rate=0.001 is correct?
- What's the half-life of trust? (How long until score drops to 0.5?)

Without verification, practitioners won't know if their trust decay is happening at the expected rate.

**Signal**: Trust scores will silently drift in unexpected ways.

---

## Assessment

### Was This Exercise Useful?

Yes, highly. The Quality Playbook's review principles produced actionable signal even for a non-code instruction document. The playbook forced systematic examination of:

1. **Ambiguity** — What happens in edge cases the skill author didn't explicitly state?
2. **Composition** — How do patterns interact when used together?
3. **Consistency** — Are similar patterns handled the same way?
4. **Verification** — Is there a way to tell if the guidance was followed correctly?

These questions revealed genuine implementation gaps that practitioners will encounter.

### Key Signal Quality

The strongest findings relate to:
- **State machine gaps** (Finding 7, 8): Underspecified reset/composition semantics will cause silent failures
- **Parallel path inconsistency** (Finding 9, 10): Framework integrations are not symmetric; practitioners will make incompatible choices
- **Verification absence** (Finding 14, 15): No way to validate that governance actually works after implementation

The weakest findings are about parameter tuning (Finding 2: threshold 0.7) — these are implementation details that practitioners might reasonably adjust without breaking the pattern.

---

## Ratings by Playbook Step

### Step 4 (Specifications)
**Signal Quality: HIGH**

Findings: 3 discoveries
- Policy composition semantics ambiguous (can accidentally create zero allowed_tools)
- Threshold and signal weights lack justification
- Rate limit reset semantics undefined

These are specification gaps that will cause incorrect implementations.

**Actionable**: Refactor compose_policies to explicitly handle all combinations. Document threshold tuning strategy. Specify rate limit scope (per-request vs. per-minute).

---

### Step 5 (Defensive Patterns)
**Signal Quality: MEDIUM-HIGH**

Findings: 3 discoveries
- Audit infrastructure failures not handled (fail-open vs. fail-closed unspecified)
- Content filtering doesn't handle nested structures
- Intent classification patterns are brittle and incomplete

These are defensiveness gaps that will cause incomplete governance in edge cases.

**Actionable**: Add fallback audit behavior. Specify recursive content filtering depth. Provide pattern maintenance guidance.

---

### Step 5a (State Machines and Phases)
**Signal Quality: HIGH**

Findings: 2 discoveries
- Trust scoring state unbounded, never used in framework integrations
- Policy composition order semantics not specified

These are state machine gaps that will cause silent behavioral divergence.

**Actionable**: Add explicit trust decay reset logic. Document composition semantics (intersection vs. union vs. first-wins).

---

### Step 5c (Parallel Path Symmetry)
**Signal Quality: MEDIUM**

Findings: 2 discoveries
- Framework integrations are inconsistent in scope, audit handling, and error checking
- Governance levels are descriptive but not prescriptive

These are consistency gaps that will cause different implementations per framework.

**Actionable**: Refactor framework examples to use a common meta-pattern. Provide concrete policy examples for each governance level.

---

### Step 6 (Domain Knowledge)
**Signal Quality: MEDIUM**

Findings: 3 discoveries
- "Policy as configuration" doesn't address failure modes (missing/invalid files)
- Intent classification patterns have unclear semantics (secret exposure vs. secret mention)
- Checklist is incomplete (doesn't provide test templates or coverage criteria)

These are domain knowledge gaps that will cause practitioners to misinterpret intent or mistest governance.

**Actionable**: Add error handling to load_policy. Clarify intent classification semantics. Provide concrete test templates.

---

### Phase 3 (Verification)
**Signal Quality: HIGH**

Findings: 2 discoveries
- No built-in verification for end-to-end governance
- Trust scoring decay lacks a verification step

These are verification gaps that will cause practitioners to deploy unvalidated governance.

**Actionable**: Add a GovernanceValidator class that checks policies, tests decorators, and validates audit logs. Add trust decay test utilities.

---

## Overall Assessment

The agent-governance skill is well-structured with good pattern coverage and concrete examples. However, it has **systematic gaps in state machine semantics, failure handling, and verification**. An agent or practitioner following this skill correctly would implement governance, but the skill doesn't guarantee:

1. Policies will compose the way the author intended
2. Governance will degrade gracefully under failure
3. Different frameworks will enforce the same policy semantics
4. Practitioners can verify that governance actually works

**Recommendation**: The skill is suitable for early-stage implementations but needs hardened specifications and verification tooling for production use.

---

## References

Findings organized by impact:

| Finding | Step | Impact | Recommendation |
|---------|------|--------|-----------------|
| Policy composition silently creates zero tools | 4, 5a | Critical | Add assertions to compose_policies |
| Rate limit semantics undefined | 4 | High | Specify per-request semantics and reset behavior |
| Trust scoring never actually used in integrations | 5a | High | Add trust gates to framework examples |
| Framework integrations are inconsistent | 5c | High | Extract common meta-pattern |
| No verification step provided | Phase 3 | High | Add GovernanceValidator class |
| Audit infrastructure failures unhandled | 5 | Medium | Add fail-closed fallback |
| Intent classification patterns brittle | 5 | Medium | Provide tuning strategy and examples |
| Content filtering doesn't handle nesting | 5 | Medium | Add recursive traversal option |
| Policy as configuration lacks error handling | 6 | Medium | Add try/except to load_policy |
| Governance levels not prescriptive | 5c | Medium | Provide concrete policy examples |
