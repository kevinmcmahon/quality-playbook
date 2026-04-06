# Spec Audit Protocol: chi

## The Definitive Audit Prompt

Give this prompt identically to three independent AI tools (Claude, GPT-4, Gemini).

---

**Context files to read:**

1. `chi.go` — Router and Routes interface definitions (authoritative specification)
2. `README.md` — URL pattern documentation, feature descriptions, usage examples
3. `quality/QUALITY.md` — Fitness-to-purpose scenarios and coverage targets

**Source directories to audit:**
- `mux.go` — Mux implementation
- `tree.go` — Radix trie routing
- `context.go` — RouteContext and URL parameters
- `chain.go` — Middleware chaining
- `middleware/` — All middleware files

**Task:** Act as the Tester. Read the actual code in the source directories above and compare it against the specifications in chi.go, README.md, and quality/QUALITY.md.

**Requirement confidence tiers:**
Requirements are tagged with `[Req: tier — source]`. Weight your findings by tier:
- **formal** — written in chi.go or README.md. Authoritative. Divergence is a real finding.
- **user-confirmed** — stated explicitly outside formal docs. Treat as authoritative.
- **inferred** — deduced from code behavior or QUALITY.md. Report divergence as NEEDS REVIEW.

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

1. **chi.go Router interface vs Mux implementation:** For every method in the `Router` interface (`Use`, `With`, `Group`, `Route`, `Mount`, `Handle`, `HandleFunc`, `Method`, `MethodFunc`, `Connect`, `Delete`, `Get`, `Head`, `Options`, `Patch`, `Post`, `Put`, `Trace`, `NotFound`, `MethodNotAllowed`) — read the actual Mux method bodies and verify the method does what the interface contract says. Pay particular attention to `With()` — the interface says "adds inline middlewares for an endpoint handler" — verify this is actually per-endpoint, not global.

2. **URL pattern matching rules (chi.go and README.md):** The spec says `{name}` matches "any sequence of characters up to the next / or end of URL." Read `tree.go:patNextSegment()` and `FindRoute()` to verify this is implemented exactly. Specifically: does `{name}` match an empty string? Does it match a string containing a space? Does `{:\\d+}` (anonymous regexp) work as documented?

3. **Wildcard `*` behavior (chi.go):** The spec says the wildcard "matches the rest of the requested URL" and "trailing characters in the pattern are ignored." Read `tree.go` to verify `*` captures `/`-separated segments. Verify that `URLParam(r, "*")` returns the captured wildcard value.

4. **RoutePattern() construction (context.go):** `RoutePattern()` says it builds the routing pattern across all sub-routers. Read `replaceWildcards()` and verify it handles consecutive `*/` wildcards correctly through iteration. Check whether the trailing slash trimming (`TrimSuffix(routePattern, "//")` then `TrimSuffix(routePattern, "/")`) produces correct results for root paths.

5. **sync.Pool correctness in ServeHTTP (mux.go):** The spec (via QUALITY.md Scenario 2) requires that `Reset()` zeros all fields. Read `Reset()` in context.go and verify every field listed in the `Context` struct has a corresponding reset operation. Check for any fields added to the struct that are NOT in `Reset()` — those are bugs.

6. **Middleware ordering in Chain() (chain.go):** The spec (implicit in README examples) shows middleware executing in the order they are listed: `r.Use(mw1); r.Use(mw2)` means mw1 runs before mw2. Read `chain()` in chain.go — it iterates from `len-1` to `0`. Verify this produces the correct (first-registered-runs-first) order, not reverse order.

7. **Mount() duplicate detection (mux.go):** QUALITY.md Scenario 10 states that mounting at a duplicate pattern must panic. Read `Mount()` at the `findPattern` calls and verify that both `pattern+"*"` and `pattern+"/*"` are checked. Check whether a pattern like `/api/` (with trailing slash) and `/api` (without) would be considered duplicates.

8. **Recoverer and ErrAbortHandler (middleware/recoverer.go):** The comment says "we don't recover http.ErrAbortHandler so the response to the client is aborted." Read the actual comparison — is it `rvr == http.ErrAbortHandler` or `errors.Is(rvr, http.ErrAbortHandler)`? For a sentinel error value (not wrapped), `==` is correct. Verify there's no type-assertion or wrapping happening.

9. **Timeout middleware 504 guard (middleware/timeout.go):** The middleware should return 504 only on deadline exceeded, not on client cancel. Read the deferred function and verify the `ctx.Err()` check happens AFTER `next.ServeHTTP(w, r)` returns. A check before `next` would always see nil and never produce 504.

10. **RealIP header priority (middleware/realip.go):** The comment says headers are checked in order: `True-Client-IP` > `X-Real-IP` > `X-Forwarded-For`. Read `realIP()` and verify the if/else if chain matches this order exactly. Verify that the `strings.Cut(xff, ",")` correctly extracts only the first IP from a comma-separated list.

**Output format:**

### [filename.ext]
- **Line NNN:** [MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM] [Req: tier — source] Description.
  Spec says: [quote or reference]. Code does: [what actually happens].

---

## Running the Audit

1. Give the identical prompt above to three independent AI tools: Claude (Opus or Sonnet), GPT-4o, Gemini Pro
2. Each auditor works independently — do not share intermediate results
3. Collect all three reports into `quality/spec_audits/`
4. Name files: `audit-claude-YYYY-MM-DD.md`, `audit-gpt4-YYYY-MM-DD.md`, `audit-gemini-YYYY-MM-DD.md`

## Triage Process

After all three models report, merge findings using this confidence table:

| Confidence | Found By | Action |
|------------|----------|--------|
| Highest | All three | Almost certainly real — fix or update spec immediately |
| High | Two of three | Likely real — verify with probe, then fix |
| Needs verification | One only | Deploy verification probe before acting |

### The Verification Probe

When models disagree on factual claims:

1. Select a model that did NOT make the disputed claim (to avoid confirmation bias)
2. Give it the claim verbatim: "Model X claims that `function_name()` in `file.go` line N does not handle Y"
3. Ask: "Read `file.go` lines N-M and report what actually happens when Y occurs"
4. The probe's reading is authoritative — it read the code with a specific question in mind

Never resolve factual disputes by majority vote. The probe's value is focused re-reading.

### Categorize Each Confirmed Finding

- **Spec bug** — Spec is wrong, code is fine → update spec (README.md or chi.go comments)
- **Design decision** — Human judgment needed → discuss and decide
- **Real code bug** — Fix in small batches by subsystem (one file at a time)
- **Documentation gap** — Feature exists but undocumented → add to README.md

## Fix Execution Rules

When fixing real code bugs:

1. Fix one subsystem at a time (e.g., fix `mux.go` before touching `tree.go`)
2. Run `go test ./...` after each fix — do not batch fixes across files
3. Do not fix and add features in the same commit
4. For each fix, verify the relevant functional test in `quality/functional_test.go` passes
5. Save audit findings to `quality/spec_audits/` for historical record
