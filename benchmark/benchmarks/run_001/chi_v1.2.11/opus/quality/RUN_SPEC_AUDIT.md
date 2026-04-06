# Spec Audit Protocol: chi

## The Definitive Audit Prompt

Give this prompt identically to three independent AI tools (e.g., Claude Code, Cursor, GitHub Copilot).

---

**Context files to read:**
1. `chi.go` — Router and Routes interface definitions (the specification)
2. `README.md` — User-facing documentation and routing examples
3. `quality/QUALITY.md` — Quality constitution with fitness-to-purpose scenarios

**Source files to audit:**
1. `mux.go` — Core router implementation
2. `tree.go` — Radix trie routing tree
3. `context.go` — RouteContext and URL parameter handling
4. `chain.go` — Middleware chain composition
5. `middleware/recoverer.go` — Panic recovery middleware
6. `middleware/throttle.go` — Rate limiting middleware
7. `middleware/compress.go` — Response compression middleware
8. `middleware/realip.go` — Client IP extraction
9. `middleware/strip.go` — Trailing slash handling
10. `middleware/url_format.go` — URL format extension parsing

**Task:** Act as the Tester. Read the actual code in the source files listed above and compare it against the specifications in `chi.go` (interface contracts) and `README.md` (documented behavior).

**Requirement confidence tiers:**
Requirements are tagged with `[Req: tier — source]`. Weight your findings by tier:
- **formal** — Written in README.md or chi.go interface definitions. Authoritative. Divergence is a real finding.
- **user-confirmed** — Stated in QUALITY.md scenarios. Treat as authoritative unless contradicted by other evidence.
- **inferred** — Deduced from code behavior. Lower confidence. Report divergence as NEEDS REVIEW, not as a definitive defect.

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

1. **Route pattern matching priority:** Read `tree.go` `findRoute()` lines 380-500. The README says patterns match most-specific first. Verify that `/user/{id}` and `/user/{id:[0-9]+}` coexist correctly — does the regex route take priority over the param route when the input matches the regex? What happens when both could match?

2. **sync.Pool context lifecycle:** Read `mux.go` `ServeHTTP()` lines 60-92. The pool Get happens before handler execution and Put happens after. Is there any code path where a panic in the handler causes the context to NOT be returned to the pool (memory leak)? Trace through Recoverer middleware interaction.

3. **Wildcard path consumption in Mount:** Read `mux.go` `Mount()` lines 289-340 and `nextRoutePath()` lines 487-494. When a subrouter is mounted, the wildcard `*` param should be cleared. Verify: (a) the clearing logic handles the case where `URLParams.Keys` is empty, (b) deeply nested mounts (3+ levels) correctly consume their path segments without corrupting sibling params.

4. **methodNotAllowed flag propagation:** Read `mux.go` `routeHTTP()` lines 441-485 and `tree.go` `FindRoute()`. When a path matches but the method doesn't, `rctx.methodNotAllowed` should be true. Does this flag survive through all code paths in `findRoute()`, including regexp and catchall nodes? Is there any traversal path that resets the flag before `routeHTTP()` reads it?

5. **Middleware chain build timing:** Read `mux.go` `Use()` line 100-105 and `handle()` lines 416-437. `Use()` panics if `mx.handler != nil`, but `handle()` sets `mx.handler` via `updateRouteHandler()`. Is there a race condition where two goroutines simultaneously call `Use()` and `handle()` during initialization? (Note: router setup is typically single-threaded, but verify the code doesn't make concurrent-safety promises it can't keep.)

6. **Throttle channel operations:** Read `middleware/throttle.go` lines 74-131. The select statement has three levels of nesting with backlog tokens and processing tokens. Verify: (a) every token acquired is returned on every code path (including context cancellation), (b) the timer is stopped on every code path that exits early, (c) no goroutine leak when backlog is full.

7. **Compress middleware wildcard handling:** Read `middleware/compress.go` `NewCompressor()` lines 63-95. The code accepts `type/*` wildcards but rejects other wildcard patterns. Verify that the wildcard matching in the handler correctly uses `strings.CutSuffix` and doesn't accidentally match against the full content-type string when it should only match the prefix.

8. **Handle() method-pattern parsing:** Read `mux.go` `Handle()` lines 109-117. When a pattern contains whitespace like `"GET /path"`, it splits into method and pattern. Verify: (a) the split handles multiple spaces/tabs correctly, (b) patterns without whitespace still work, (c) patterns with whitespace in URL-encoded paths aren't misinterpreted.

9. **RoutePattern() wildcard cleanup:** Read `context.go` `RoutePattern()` lines 123-134 and `replaceWildcards()` lines 139-144. The function iteratively replaces `/*/` with `/`. Verify: (a) the iteration terminates (no infinite loop), (b) edge cases: pattern is exactly `/`, pattern ends with `/*`, pattern has consecutive wildcards `/*/*/`.

10. **RegisterMethod() overflow protection:** Read `tree.go` `RegisterMethod()` lines 61-77. Custom methods use bit flags (`methodTyp`). The overflow check uses `strconv.IntSize`. Verify: (a) the bit shift `2 << n` doesn't overflow for the maximum number of registered methods, (b) the check fires before the overflow, not after.

**Output format:**

### [filename.ext]
- **Line NNN:** [MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM] [Req: tier — source] Description.
  Spec says: [quote or reference]. Code does: [what actually happens].

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
1. Select a model that did NOT make the disputed claim
2. Quote the finding exactly
3. Ask it to read the specific code and report what actually happens
4. Compare against the original claim

Never resolve factual disputes by majority vote.

### Categorize Each Confirmed Finding

- **Spec bug** — Spec is wrong, code is fine → update spec
- **Design decision** — Human judgment needed → discuss and decide
- **Real code bug** — Fix in small batches by subsystem
- **Documentation gap** — Feature exists but undocumented → update docs
- **Missing test** — Code is correct but no test verifies it → add test
- **Inferred requirement wrong** — Remove or correct it in QUALITY.md

## Fix Execution Rules

- Group fixes by subsystem (tree.go, mux.go, middleware)
- **Batch size: 3–5 fixes per batch**
- Each batch: implement, test with `go test -race ./...`, have all three reviewers verify
- At least two auditors must confirm fixes pass before marking complete

## Output

Save audit reports to `quality/spec_audits/YYYY-MM-DD-[model].md`
Save triage summary to `quality/spec_audits/YYYY-MM-DD-triage.md`
