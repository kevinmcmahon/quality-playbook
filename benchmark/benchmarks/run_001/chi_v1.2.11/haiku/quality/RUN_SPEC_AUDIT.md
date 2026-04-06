# Spec Audit Protocol: Chi HTTP Router (Council of Three)

This protocol executes a multi-model spec audit of chi's implementation against its documented behavior and HTTP specifications.

## What is the Council of Three?

Three independent AI models audit the same code. Each model has different blind spots and strengths. By comparing their findings, we catch issues that any single model would miss. This is cheaper and more reliable than one powerful model auditing alone.

## Execution Overview

1. **Run Audit 1 (Model A):** Use Claude Haiku (balanced)
2. **Run Audit 2 (Model B):** Use Claude Sonnet (detailed, code-focused)
3. **Run Audit 3 (Model C):** Use Claude Opus (architectural, edge-case)
4. **Triage Findings:** Merge results by confidence, eliminate duplicates
5. **Report:** Document agreed findings, disputed findings, and recommended fixes

## The Audit Prompt

Copy and paste this prompt exactly into each model (modifications only for model name):

---

### Audit Prompt: Chi HTTP Router Specification Compliance

**Context:**

Chi is a lightweight Go HTTP router used in production systems. You are auditing chi's implementation against its documented behavior and HTTP specifications (RFC 7230–7235).

**Files to review:**
- `/sessions/quirky-practical-cerf/mnt/QPB/repos/chi/README.md` (design goals, feature claims)
- `/sessions/quirky-practical-cerf/mnt/QPB/repos/chi/chi.go` (interface definitions, 137 lines)
- `/sessions/quirky-practical-cerf/mnt/QPB/repos/chi/context.go` (request context, 166 lines)
- `/sessions/quirky-practical-cerf/mnt/QPB/repos/chi/mux.go` (router implementation, 526 lines)
- `/sessions/quirky-practical-cerf/mnt/QPB/repos/chi/tree.go` (radix tree, 877 lines)
- `/sessions/quirky-practical-cerf/mnt/QPB/repos/chi/chain.go` (middleware, 49 lines)
- Quality constitution: `/sessions/quirky-practical-cerf/mnt/QPB/benchmarks/run_001/chi_v1.2.11/haiku/quality/QUALITY.md`

**Scrutiny Areas:**

1. **Regex Denial of Service (ReDoS)** — Chi allows user-provided regex patterns in route definitions (e.g., `{id:pattern}`). Are these patterns validated for ReDoS risks before compilation? Does chi apply timeouts to regex matching? Reference tree.go:256 (compilation) and tree.go:449 (matching).

2. **Panic-Based Error Handling** — Chi panics on invalid route patterns (invalid regex, duplicate parameters, wildcard placement). Are panics appropriate for runtime input, or should patterns be validated before registration? If chi assumes patterns are trusted (hardcoded), is this assumption documented?

3. **Context Pool Safety** — Chi reuses Context objects from sync.Pool. Does Reset() (context.go:82–96) fully clear all fields, preventing cross-request leakage? Check: are there new fields added without Reset() updates?

4. **Method Routing Correctness** — Chi distinguishes 404 (route not found) from 405 (method not allowed). Trace tree.go:468–478. Can insertion order or tree structure changes cause this distinction to be lost?

5. **Pattern Matching Precedence** — Chi's radix tree maintains ordering: static nodes, param nodes, catchall. Does later insertion ever change this order in a way that breaks earlier matching? Reference tree.go:793–798 (tailSort).

6. **Middleware Ordering Enforcement** — Chi panics if middlewares are registered after routes (mux.go:101–103). Is this guard sufficient? Can subrouters bypass this guard?

7. **HTTP Spec Compliance** — According to RFC 7231, specific HTTP methods have defined semantics (GET is idempotent, POST is not, DELETE should be idempotent). Does chi enforce these semantics, or is it router-agnostic? Should it be?

8. **Wildcard and Catchall Handling** — Chi allows `/*` (catchall) and `*` (wildcard). The README states "wildcard must be the last pattern." Is this enforced? Can a route like `/files/*/other` be registered?

9. **Empty Segments and Root Path** — How does chi handle the root path `/`? What about double slashes `//`? Are these treated as special cases or normalized?

10. **Parameter Name Collision** — Can a pattern like `/{id}/{id}` be registered? Should chi allow it, and if so, what should URLParam("id") return?

**Guardrails to prevent false findings:**

- Read the actual code, not the docs. If the README says "no external dependencies" but see imports, flag it.
- Cite line numbers. If you claim X is wrong at tree.go:500, verify by reading that exact line.
- Search for defensive code. Before claiming "missing validation," grep for validation and read the relevant functions.
- If unsure, mark as QUESTION. Uncertain findings are less valuable than confident ones.
- No style opinions. Only flag functional issues, not naming, formatting, or subjective quality.

**Output format:**

For each scrutiny area, report:
- **FINDING:** Description of what you observed
- **EVIDENCE:** Line numbers and code snippets (if found), or "no evidence found"
- **CONFIDENCE:** High (obvious), Medium (likely), Low (uncertain)
- **SEVERITY:** Critical (breaks spec), High (design flaw), Medium (risky), Low (marginal)
- **RECOMMENDATION:** What should be done

Example:
```
FINDING: ReDoS Risk in Pattern Compilation
EVIDENCE: tree.go:256 compiles user regex without timeout; tree.go:449 matches with no timeout. No validation prevents patterns like {id:(?:.*)*}.
CONFIDENCE: High
SEVERITY: High (ReDoS can hang goroutines)
RECOMMENDATION: Document that chi assumes regex patterns are trusted, OR add timeout to regexp.MatchString, OR validate patterns against common ReDoS patterns.
```

---

## Running the Three Audits

### Audit 1: Model A (Balanced)

Use Claude Haiku. Paste the prompt above and record findings.

**Output file:** `quality/spec_audits/audit_1_haiku_[timestamp].md`

### Audit 2: Model B (Code-Focused)

Use Claude Sonnet. Paste the prompt above, with emphasis added:

> "Pay special attention to panic handling, nil checks, and boundary conditions in tree.go. This is the most critical module."

**Output file:** `quality/spec_audits/audit_2_sonnet_[timestamp].md`

### Audit 3: Model C (Architectural)

Use Claude Opus. Paste the prompt above, with emphasis added:

> "Focus on architectural trade-offs: Does chi's panic-based error handling align with its design goals? What's the consequence of assuming trusted patterns? How do these choices affect users?"

**Output file:** `quality/spec_audits/audit_3_opus_[timestamp].md`

## Triage Process

After all three audits, create a consolidated finding list:

### Step 1: De-duplicate

Models often flag the same issue differently. Combine identical findings under one entry.

Example:
- Haiku: "Pattern validation missing"
- Sonnet: "tree.go:765 doesn't validate regex complexity"
- Opus: "Panic-based validation is inflexible"

→ **Consolidated:** "Pattern validation relies on panics, no regex complexity limits"

### Step 2: Confidence Scoring

For each consolidated finding:
- **Unanimous (all 3 agree):** Confidence = High
- **2 agree, 1 uncertain:** Confidence = Medium
- **1 flagged, 2 unsure:** Confidence = Low
- **Disputed (models disagree):** Mark as DISPUTED, note divergence

### Step 3: Severity Assessment

| Severity | Criteria | Example |
|----------|----------|---------|
| Critical | Breaks spec or causes silent data loss | ReDoS that hangs requests indefinitely |
| High | Design flaw affecting production use | Panic on untrusted input |
| Medium | Risk under specific conditions | Context pool leakage if new field added |
| Low | Marginal edge case | Normalize double slashes in paths |

## Consolidated Audit Report Template

Create `quality/spec_audits/CONSOLIDATED_FINDINGS.md`:

```markdown
# Consolidated Spec Audit: Chi Router

**Audits conducted:** 3 (Haiku, Sonnet, Opus)
**Date:** [timestamp]
**Time per audit:** ~30 minutes each

## Agreed Findings (High Confidence)

### Finding: [Title]
- **Models:** All 3
- **Severity:** [Critical/High/Medium/Low]
- **Description:** [2–3 sentences]
- **Evidence:** [code references]
- **Recommendation:** [what to do]
- **Priority:** [Critical/High/Medium/Low] for fixing

[Repeat for each agreed finding]

## Disputed Findings (Medium Confidence)

### Finding: [Title]
- **Models:** [2 agree, 1 unsure]; [Haiku says X, Sonnet says Y]
- **Description:** [what's disputed]
- **Haiku finding:** [haiku's claim]
- **Sonnet finding:** [sonnet's claim]
- **Opus finding:** [opus's claim]
- **Recommendation:** [human to decide]

[Repeat for each disputed finding]

## Uncertain Findings (Low Confidence)

### Finding: [Title]
- **Models:** [1 flagged, 2 unsure]
- **Description:** [what's uncertain]
- **Flagged by:** [which model]
- **Reason for uncertainty:** [why not confident]
- **Recommendation:** [ask user or defer]

[Repeat for each uncertain finding]

## Summary

**Critical findings:** [count]
**High findings:** [count]
**Medium findings:** [count]
**Low findings:** [count]

**Recommended actions:**
1. [Priority 1 fix from critical findings]
2. [Priority 2 fix from high findings]
3. [Priority 3 investigation from disputed findings]

---

**Conducted by:** [model names]
**Output:** [timestamp]
```

## Execution Instructions

1. **Run all three audits in parallel** to save time (or sequentially if needed)
2. **Save each audit output** to `quality/spec_audits/audit_[N]_[model]_[timestamp].md`
3. **Consolidate findings** into `quality/spec_audits/CONSOLIDATED_FINDINGS.md`
4. **Report to user** with summary table and prioritized recommendations

## Expected Timeline

- Audit 1 (Haiku): 20 minutes
- Audit 2 (Sonnet): 25 minutes
- Audit 3 (Opus): 30 minutes
- Triage & consolidation: 15 minutes

**Total:** ~90 minutes (or ~30 minutes if parallel)

## When to Escalate Findings

### Critical findings → Immediate action
- ReDoS vulnerability without mitigation
- Cross-request data leakage
- Panic on user input

### High findings → Investigate & document
- Design flaws (e.g., panic-based validation)
- Missing validation
- Architectural misalignment

### Medium findings → Consider for next release
- Edge cases that rarely occur
- Performance trade-offs
- Documentation improvements

### Low findings → Optional
- Marginal cases
- Style suggestions
- Future improvements

## References

- Chi README: `/sessions/quirky-practical-cerf/mnt/QPB/repos/chi/README.md`
- HTTP Spec (RFC 7231–7235): [https://tools.ietf.org/html/rfc7231](https://tools.ietf.org/html/rfc7231)
- QUALITY.md: `quality/QUALITY.md`
- Functional tests: `quality/test_functional.go`
