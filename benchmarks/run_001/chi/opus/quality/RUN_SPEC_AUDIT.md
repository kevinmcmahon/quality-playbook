# Spec Audit Protocol: chi

## The Definitive Audit Prompt

Give this prompt identically to three independent AI tools (e.g., Claude, GPT, Gemini).

---

**Context files to read:**
1. `chi.go` — Package documentation, Router and Routes interfaces
2. `README.md` — Project overview, usage examples, URL pattern syntax
3. `quality/QUALITY.md` — Quality constitution and fitness-to-purpose scenarios

**Source code to audit:**
- `chi.go` — Public interfaces
- `mux.go` — HTTP multiplexer implementation
- `tree.go` — Radix trie routing implementation
- `context.go` — Routing context and URL parameters
- `chain.go` — Middleware chain composition
- `middleware/` — All 29 built-in middleware files

**Task:** Act as the Tester. Read the actual code in the source files listed above and compare it against the specifications in the documentation (README.md, chi.go package documentation) and the quality scenarios in QUALITY.md.

**Requirement confidence tiers:**
Requirements are tagged with `[Req: tier — source]`. Weight your findings by tier:
- **formal** — written in README.md or chi.go package documentation. Authoritative. Divergence is a real finding.
- **user-confirmed** — stated by the user but not in a formal doc. Treat as authoritative unless contradicted by other evidence.
- **inferred** — deduced from code behavior. Lower confidence. Report divergence as NEEDS REVIEW, not as a definitive defect.

**Rules:**
- ONLY list defects. Do not summarize what matches.
- For EVERY defect, cite specific file and line number(s).
  If you cannot cite a line number, do not include the finding.
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

1. **URL Pattern Matching (tree.go:401-544):** Read the `findRoute()` function body completely. The README says `"/user/{name}"` matches `"/user/jsmith"` but not `"/user/jsmith/info"` or `"/user/jsmith/"`. Verify that param node matching at tree.go:427-491 enforces the cross-segment boundary (no `/` in param values) for regular params but allows `/` in catch-all. Does the code at tree.go:452 (`strings.IndexByte(xsearch[:p], '/') != -1`) correctly prevent cross-segment matching?

2. **Regexp Pattern Syntax (tree.go:257-260 and chi.go:39-42):** The README says "The regular expression syntax is Go's normal regexp RE2 syntax, except that / will never be matched." Read `findRoute()` — does the regexp matching actually prevent `/` from matching? The code at tree.go:449 uses `xn.rex.MatchString(xsearch[:p])` where `p` is the position of the tail delimiter — but is the tail delimiter always `/`? What if the pattern has a non-`/` tail?

3. **Mount Behavior (mux.go:289-340):** The README and chi.go documentation say Mount attaches a handler "along ./pattern/*". Read the mountHandler closure at mux.go:309-322. Does it correctly advance `rctx.RoutePath` for nested routing? Does the wildcard URLParam reset at mux.go:317-319 handle the case where there are no URLParams (n < 0)?

4. **Context Pooling Safety (mux.go:60-92):** Read `ServeHTTP()` completely. When a Context already exists on the request (line 71-75), the function calls the handler without pool.Get/pool.Put — but does this mean inline sub-routers bypass context pooling entirely? Trace the lifecycle: what happens to the parent Context when a mounted sub-router's ServeHTTP also tries to get from the pool?

5. **Handle() Method-Pattern Parsing (mux.go:109-117):** The code parses patterns with spaces as "method pattern" pairs (e.g., `"GET /path"`). This matches Go 1.22's ServeMux syntax. But is this documented anywhere in chi? If not, this is an UNDOCUMENTED feature. Also verify: what happens if the pattern is just a space-separated string that's not a valid method?

6. **Middleware Ordering Invariant (mux.go:100-105):** The `Use()` function panics if `mx.handler != nil`. Read `handle()` at mux.go:416-437 — it calls `mx.updateRouteHandler()` which sets `mx.handler`. Verify: is there any code path where `mx.handler` is set without `handle()` being called? Can `With()` at mux.go:236-257 cause `updateRouteHandler()` on the parent?

7. **405 vs 404 Determination (tree.go:469-479 + mux.go:480-484):** When `findRoute()` returns nil, `routeHTTP()` checks `rctx.methodNotAllowed`. But `methodNotAllowed` is set inside the param node matching loop at tree.go:478 — which only runs when `len(xsearch) == 0`. Does this correctly detect 405 for routes where the path matches but only via a static or regexp node, not a param node?

8. **replaceWildcards Correctness (context.go:139-143):** The function iterates `strings.ReplaceAll(p, "/*/", "/")` until no `"/*/"` remains. This handles consecutive wildcards like `"/*/*/*/"`. But what about a pattern that legitimately contains `"/*/"`? The tests at context_test.go show this is handled by checking for `*special_path` — verify that the implementation correctly preserves wildcards that are part of named segments.

9. **RegisterMethod Thread Safety (tree.go:61-77):** `RegisterMethod()` modifies the global `methodMap`, `reverseMethodMap`, and `mALL` without any synchronization. If called concurrently (e.g., during init in multiple packages), this is a data race. Is this documented as "must be called during init before any routing"?

10. **Walk/Routes Traversal (mux.go:344-351 + tree.go routes()):** The `Routes()` method returns `[]Route` by traversing the tree. Verify: does this correctly include routes registered via `Mount()`? Are mounted sub-router routes included in the parent's `Routes()` output, or are they separate? This affects documentation generators and introspection tools.

**Output format:**

### [filename.ext]
- **Line NNN:** [MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM] [Req: tier — source] Description.
  Spec says: [quote or reference]. Code does: [what actually happens].

---

## Running the Audit

1. Give the identical prompt to three AI tools
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

When models disagree on factual claims, deploy a read-only probe:

1. **Select a model** — preferably one that did NOT make the disputed claim.
2. **Give it the claim** — quote the finding exactly.
3. **Ask it to read the code** — "Read [file] lines X-Y and report what actually happens when [condition]."
4. **Compare the probe result** against the original claim.

Never resolve factual disputes by majority vote — the probe reads code with a specific question.

### Categorize Each Confirmed Finding

- **Spec bug** — Spec is wrong, code is fine → update spec
- **Design decision** — Human judgment needed → discuss and decide
- **Real code bug** — Fix in small batches by subsystem
- **Documentation gap** — Feature exists but undocumented → update docs
- **Missing test** — Code is correct but no test verifies it → add to functional tests
- **Inferred requirement wrong** — The inferred requirement doesn't match actual intent → correct in QUALITY.md

## Fix Execution Rules

- Group fixes by subsystem, not by defect number
- **Batch size: 3–5 fixes per batch.**
- Never one mega-prompt for all fixes
- Each batch: implement, test, have all three reviewers verify the diff
- At least two auditors must confirm fixes pass before marking complete

## Output

Save audit reports to `quality/spec_audits/YYYY-MM-DD-[model].md`
Save triage summary to `quality/spec_audits/YYYY-MM-DD-triage.md`
