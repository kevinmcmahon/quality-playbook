# Spec Audit Protocol: chi

## The Definitive Audit Prompt

Give this prompt identically to three independent AI tools (e.g., Claude, GPT-4, Gemini). Each auditor works independently.

---

**Context files to read:**
1. `README.md` — Feature description, URL pattern syntax, middleware documentation, benchmark results
2. `chi.go` — The `Router` and `Routes` interface definitions (the formal contract)
3. `mux.go` — The `Mux` struct implementing `Router`
4. `tree.go` — Patricia Radix trie: route insertion, traversal, and pattern parsing
5. `context.go` — `Context` struct, `URLParam`, `RoutePattern`, `RouteContext`
6. `chain.go` — Middleware chain construction
7. `quality/QUALITY.md` — Fitness-to-purpose scenarios and coverage targets

**Task:** Act as the Tester. Read the actual source code in the files listed above and compare it against the specifications in `README.md` and `chi.go`. Identify defects: places where the code diverges from, fails to implement, or implements differently than specified.

**Requirement confidence tiers:**
Requirements are tagged with `[Req: tier — source]`. Weight your findings by tier:
- **formal** — written in `README.md` or `chi.go` interface docs. Authoritative. Divergence is a real finding.
- **inferred** — deduced from code behavior (see `quality/QUALITY.md` scenarios). Lower confidence. Report divergence as NEEDS REVIEW, not as a definitive defect.

**Rules:**
- ONLY list defects. Do not summarize what matches.
- For EVERY defect, cite specific file and line number(s). If you cannot cite a line number, do not include the finding.
- Before claiming missing, grep the codebase. Before claiming exists, read the actual function body.
- Classify each finding: MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM
- For findings against inferred requirements, add: NEEDS REVIEW

**Defect classifications:**
- **MISSING** — Spec requires it, code doesn't implement it
- **DIVERGENT** — Both spec and code address it, but they disagree
- **UNDOCUMENTED** — Code does it, spec doesn't mention it
- **PHANTOM** — Spec describes it, but it's actually implemented differently than described

**Project-specific scrutiny areas:**

1. **Anonymous regexp params** — `chi.go` documents `{:\\d+}` (empty name before colon) as a valid pattern. Read `patNextSegment()` in `tree.go` lines 685–753 specifically for the case where the key before `:` is an empty string. Does `strings.Cut(key, ":")` produce `key=""` when the pattern is `{:\\d+}`? What key is stored in `routeParams.Keys` for an anonymous param? What does `URLParam(r, "")` return?

2. **Wildcard param key name** — `README.md` says "fetch `chi.URLParam(r, "*")` for a wildcard parameter." Read `patParamKeys()` in `tree.go` lines 755–769. What key name does the catch-all node store? Verify it is `"*"` and not `""` or some other value.

3. **Pool context reset completeness** — Read `Context.Reset()` in `context.go` lines 82–96. List every field of the `Context` struct (lines 46–79). Verify that every field is explicitly zeroed in `Reset()`. If any field is missing, that is a defect — a pooled context from a previous request would carry stale state into the next request.

4. **Middleware order under inline muxes** — `README.md` describes middleware registered via `Use()` as executing "before searching for a matching route." Read `Mux.With()` in `mux.go` lines 236–257. When `With()` creates an inline mux and registers it with additional middlewares, those middlewares are prepended from the parent's stack. Verify that the middleware execution order for an inline mux handler is: [parent middlewares] → [With() middlewares] → [handler]. Read `chain()` in `chain.go` lines 36–49 and verify the wrapping order.

5. **NotFound handler propagation to subrouters** — `README.md` documents `NotFound()` as setting a custom 404 handler. Read `Mux.NotFound()` in `mux.go` lines 197–213 and `updateSubRoutes()` in `mux.go` lines 497–504. Verify that a custom NotFound set on the root router propagates to all mounted subrouters that haven't set their own. Check whether the propagation happens at `NotFound()` call time or at `Mount()` call time (or both). Check the `Mount()` code at lines 300–307 for the inline propagation path.

6. **Percent-encoded URL path handling** — `mux.go` `routeHTTP()` at lines 447–458 checks `r.URL.RawPath` before `r.URL.Path`. Read this logic and compare to Go's `net/http` URL parsing behavior. If a client sends `/users/%2F/profile` (encoded slash), `RawPath` is `/users/%2F/profile` and `Path` is `/users//profile`. Verify which value chi uses for routing and whether this matches the README's documentation of URL pattern matching.

7. **`Find()` vs `Match()` contract** — `chi.go` defines both `Find(rctx, method, path) string` and `Match(rctx, method, path) bool`. Read `Mux.Match()` at `mux.go` lines 359–361 — it delegates to `Find()` and returns `Find() != ""`. Verify that `Match()` returns `true` if and only if `Find()` returns a non-empty pattern. Is there any case where `Find()` could return `""` for a validly matched route?

8. **`Routes()` return value for stub nodes** — `tree.go` `routes()` at lines 620–660 skips nodes where `eps[mSTUB] != nil && subroutes == nil`. Read this condition carefully. What exactly constitutes a "stub" endpoint? Verify that `Routes()` output for a router with both mounted subrouters and direct handlers is complete — i.e., that direct `Get()` handlers registered on the same mux as a `Mount()` are not accidentally excluded.

9. **RegisterMethod capacity limit** — `tree.go` `RegisterMethod()` at lines 60–77 checks `if n > strconv.IntSize-2`. The comment says "max number of methods reached." Verify: with 9 default methods defined, the bitmask uses 9 bits. `strconv.IntSize` is 32 or 64. Confirm whether the effective limit is 30 or 62 additional custom methods, and whether the panic message accurately reflects the limit.

10. **Pattern `{name}` trailing slash behavior** — `chi.go` documents: `"/user/{name}"` matches `"/user/jsmith"` but not `"/user/jsmith/"`. Read `findRoute()` in `tree.go` specifically the `ntParam` branch (lines 427–491). When the request path is `/user/jsmith/` and the pattern is `/user/{name}`, the param matching finds `jsmith` up to the `/` tail. The remaining path is `/` — does this match the empty endpoint, or fall through to 404? Verify the behavior is consistent with the README spec.

**Output format:**

### filename.go
- **Line NNN:** [MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM] [Req: tier — source] Description.
  Spec says: [quote or reference]. Code does: [what actually happens].

---

## Running the Audit

1. Give the identical prompt above to three independent AI tools
2. Each auditor works independently — no cross-contamination
3. Collect all three reports in `quality/spec_audits/`

Naming convention:
- `quality/spec_audits/YYYY-MM-DD-claude.md`
- `quality/spec_audits/YYYY-MM-DD-gpt.md`
- `quality/spec_audits/YYYY-MM-DD-gemini.md`

## Triage Process

After all three models report, merge findings:

| Confidence | Found By | Action |
|------------|----------|--------|
| Highest | All three | Almost certainly real — fix or update spec |
| High | Two of three | Likely real — verify and fix |
| Needs verification | One only | Deploy a verification probe |

### The Verification Probe

When models disagree, select a model that did NOT make the disputed claim. Give it:

> "Model X claims that `[function]()` in `[file]` line [N] does not handle [case]. Read `[file]` lines [N-10]–[N+10] and report what actually happens when [input]."

Compare the probe result against the original claim. If the probe confirms: finding is real. If the probe contradicts: the original finding was likely hallucinated.

Never resolve factual disputes by majority vote. The probe reads the code with a specific question in mind.

## Fix Execution Rules

- Group fixes by subsystem: tree.go fixes together, context.go fixes together, etc.
- **Batch size: 3–5 fixes per batch.** For trivial fixes (missing doc comment, typo), batch up to 8.
- Each batch: implement → `go test ./...` → have at least two auditors verify the diff
- At least two auditors must confirm fixes pass before marking complete

## Output

Save audit reports to `quality/spec_audits/YYYY-MM-DD-[model].md`
Save triage summary to `quality/spec_audits/YYYY-MM-DD-triage.md`
