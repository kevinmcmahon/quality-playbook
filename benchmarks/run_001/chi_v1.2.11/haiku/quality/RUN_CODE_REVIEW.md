# Code Review Protocol: Chi Router

This protocol guides a rigorous code review of chi's core routing logic, with focus areas derived from the quality constitution and exploration findings.

## Bootstrap Files

Before reviewing any code:

1. Read QUALITY.md (this directory) — familiarize yourself with chi's fitness requirements
2. Read /sessions/quirky-practical-cerf/mnt/QPB/repos/chi/README.md — understand chi's design principles
3. Verify test file locations: `/sessions/quirky-practical-cerf/mnt/QPB/repos/chi/{mux_test.go, tree_test.go, context_test.go}`
4. Reference the functional tests in quality/test_functional.go for expected behavior

## Review Guardrails

**Non-negotiable rules to prevent hallucinated findings:**

1. **Line numbers are mandatory** — Every finding must cite the exact line number. If you claim "function X has a bug" without a line number, flag as QUESTION, not BUG.
2. **Read the actual function bodies** — Don't assume from name or signature. Read every line of the function you're critiquing.
3. **Grep before claiming missing** — If you claim "X should validate Y", search for validation code first. Use grep to find error checks and assertions.
4. **If unsure: flag as QUESTION** — Uncertain observations become QUESTION entries for human judgment, not BUG findings.
5. **No style changes** — Only flag things that are functionally incorrect, not formatting, naming, or subjective quality.

## Focus Areas by Module

### 1. Radix Tree Insert Logic (tree.go:140–300)

**Why this area matters:** Correctness of route insertion determines all subsequent behavior. A subtle insertion bug causes wrong routes to match, silent parameter mismatches, or unreachable handlers.

**What to check:**

- **Line 145–160:** Path segmentation logic. Does `segStatic()` correctly identify static segments? Verify edge cases: empty segments, segments with regex markers `{`, `[`.
- **Line 255–270:** Regex compilation and node type assignment. Every regex pattern should compile without error OR panic with a clear message. Does the code compile before using?
- **Line 270–300:** Node insertion and ordering. When a new node is inserted, does it maintain the invariant (static first, param, catchall)? Check `tailSort()` call at line 295.
- **Duplicate detection (line 765):** When the same pattern is registered twice, does it update or panic? Current: panics if duplicate parameters. Should it allow re-registering the same pattern with a different handler?

**Search patterns:**
```
grep -n "func (n \*node) insert" tree.go  # Main insert function
grep -n "panic\|recover" tree.go          # Error handling
grep -n "regexp.Compile" tree.go          # Regex validation
```

### 2. Radix Tree Lookup Logic (tree.go:374–500)

**Why this area matters:** Lookup is on the hot path (every request). A bug here affects all requests. Parameter extraction must be exact.

**What to check:**

- **Line 380–420:** Pattern matching precedence. Static nodes before param nodes before catchall. Does the loop respect this order? Check the loop at line 410.
- **Line 449–455:** Regex matching with substring isolation. The code extracts `xsearch[:p]` and matches `rex.MatchString(xsearch[:p])`. Is the boundary `p` correct? Can `p` be zero (empty segment)?
- **Line 464–478:** Method resolution and "method not allowed" flag. When a path matches but method doesn't, is `rctx.methodNotAllowed` set correctly?
- **Line 489–510:** Parameter value extraction and normalization. Are parameter values extracted correctly from the path? Check the loop appending to `routeParams.Values`.

**Search patterns:**
```
grep -n "func (n \*node) findRoute" tree.go
grep -n "methodNotAllowed" tree.go
grep -n "routeParams.Values = append" tree.go
```

### 3. Middleware Ordering Enforcement (mux.go:95–110)

**Why this area matters:** The panic-based guard prevents a class of bugs (middleware registered after routes, changing behavior). But is the check sufficient?

**What to check:**

- **Line 101–103:** The guard `if mx.handler != nil { panic(...) }`. What sets `mx.handler`? It should be set exactly once, when the first route is registered. Find where this happens.
- **Line 205–215:** Does `updateRouteHandler()` actually set `mx.handler`? Verify it's called before every route registration.
- **Subrouters (line 272–295):** When `Route()` creates a subrouter, does the subrouter have its own `handler` field? Or does it inherit from parent? Check line 272.

**Search patterns:**
```
grep -n "mx.handler\s*=" mux.go
grep -n "updateRouteHandler" mux.go
grep -n "subMux\|subRouter" mux.go
```

### 4. Context Pool Management (mux.go:445–490)

**Why this area matters:** Context reuse from sync.Pool is the only mutable shared state. If reset is incomplete, requests can leak data to each other.

**What to check:**

- **Line 449–453:** Context creation from pool. Is `rctx.Reset()` called on every use? Check the call at line 455.
- **Line 455:** Call to `Reset()`. Does this fully initialize all fields? Read context.go:82–96 (Reset function). Verify every field is reset, not just truncated slices.
- **Line 483–485:** Deferred return to pool. The defer ensures return on panic. But is the context reset BEFORE being returned, or AFTER? Current: return before reset is OK (deferred, so reset happens AFTER return). Wait—check the actual code.
- **Panic safety (line 440):** If the handler panics, does the defer still execute? Yes, but does reset happen before pool return?

**Search patterns:**
```
grep -n "sync.Pool\|Get\|Put" mux.go
grep -n "rctx.Reset\|Release" mux.go
grep -n "defer.*rctx" mux.go
```

### 5. Pattern Validation (tree.go:690–770)

**Why this area matters:** Every panic validation must execute before routes are registered. Missing validation allows crashes at runtime.

**What to check:**

- **Line 697:** Regex node method overflow check. `len(methodMap) > strconv.IntSize-2`. Is `strconv.IntSize` correct? It's 64 on 64-bit, 32 on 32-bit. On 32-bit systems, can we safely register 62 custom methods?
- **Line 720–722:** Brace matching. Missing `}` should panic. Is the logic correct? What if `pattern = "{id"`? Trace through the parsing.
- **Line 749–751:** Wildcard position validation. Wildcard must be at the end. The check is `if ws < len(pattern)-1`. Is this correct? What if `ws == -1` (no wildcard)?
- **Line 763–767:** Duplicate parameter key detection. The loop checks all keys already in `paramKeys`. But what if a key appears multiple times in the same pattern? Example: `/{id}/{id}`.

**Search patterns:**
```
grep -n "panic.*pattern\|panic.*param\|panic.*wildcard\|panic.*regex" tree.go
grep -n "ws\s*:=\|strings.Index" tree.go
```

### 6. Handler Assignment and Nil Checks (mux.go:273–295, tree.go:464–478)

**Why this area matters:** Nil handlers should panic at registration, not cause panic at request time.

**What to check:**

- **Line 273–274 (mux.go):** Route() handler nil check. Does `if fn == nil { panic(...) }` execute before the handler is stored?
- **Line 290–291 (mux.go):** Mount() handler nil check. Same check as Route()?
- **Line 464 (tree.go):** Lookup handler nil check. During request routing, is `h.handler` checked before execution?
- **Asymmetry:** Are all handler registration paths (Get, Post, Put, Delete, Mount, Route) equally protected?

**Search patterns:**
```
grep -n "if.*nil.*panic" mux.go tree.go
grep -n "func.*Register\|Route\|Mount" mux.go
grep -n "endpoint.*struct\|handler\s*http.Handler" tree.go
```

### 7. Empty Request Path Handling (mux.go:450–460, tree.go:145–160)

**Why this area matters:** Malformed or edge-case paths could cause index out of bounds or wrong segment matching.

**What to check:**

- **Line 454 (mux.go):** `if routePath == ""` sets default to `"/"`. Is this correct? Should an empty path ever reach here?
- **tree.go segment parsing:** If `pattern = "/"`, is it treated as one empty segment or no segments? Does the code handle this?
- **Boundary case:** What happens if someone registers a route `/` (just the root)? Should it match `/` but not `/users`?

**Search patterns:**
```
grep -n "routePath\s*=\|routePath ==" mux.go
grep -n "pattern\s*==\|len(pattern)" tree.go
```

## Execution Process

### Step 1: Review Core Modules (2 hours)

Review in this order:
1. tree.go (radix tree) — most critical
2. mux.go (handler registry) — second most critical
3. context.go (context management) — third
4. chain.go (middleware) — lowest risk, quick review
5. chi.go (interfaces) — documentation only

For each file, follow the focus areas above. Document every finding as BUG, CONCERN, QUESTION, or OBSERVATION.

### Step 2: Write Regression Tests

For each BUG finding, write a test in `quality/test_regression.go` that reproduces the bug. The test should:
- Fail on the current implementation (confirming the bug is real)
- Pass if the bug is fixed
- Include a comment referencing the BUG finding and QUALITY.md scenario number if applicable

Example template:
```go
// TestRegressionBugX validates BUG-X: [description]
// References: QUALITY.md Scenario N, mux.go:line
func TestRegressionBugX(t *testing.T) {
    r := chi.NewRouter()
    // ... test code that would fail if bug exists
    // Assertion that passes only if bug is fixed
    if bugIsPresent {
        t.Errorf("BUG-X: expected [correct behavior], got [buggy behavior]")
    }
}
```

### Step 3: Categorize Findings

Create a summary table:
| Finding ID | Type | Module | Line | Description | Severity |
|-----------|------|--------|------|-------------|----------|
| BUG-1 | Bug | tree.go | 765 | [description] | High |
| CONCERN-1 | Design concern | mux.go | 101 | [description] | Medium |
| QUESTION-1 | Uncertainty | context.go | 82 | [description] | N/A |

## Reporting Template

After completion, generate a report:

```markdown
## Code Review Summary: Chi Router

**Files reviewed:** tree.go, mux.go, context.go, chain.go, chi.go
**Lines reviewed:** ~1800 LOC
**Time spent:** [estimate]

### Findings by Severity

**High Severity (BUGs):** [count]
**Medium Severity (ConcERNs):** [count]
**Low Severity (QUESTIONs):** [count]

### High-Priority Bugs

[List with line numbers, QUALITY.md references]

### Medium-Priority Concerns

[List with line numbers, QUALITY.md references]

### Regressions to Implement

[Link to quality/test_regression.go test cases]

### Verification Checklist

- [ ] All panic validation guards execute before route registration
- [ ] Context reset fully initializes all fields, no cross-request leakage
- [ ] Regex patterns are compiled and validated at registration time
- [ ] Parameter extraction produces correct keys and values in nested routers
- [ ] Method routing distinguishes 404 (not found) vs 405 (method not allowed)
- [ ] Middleware ordering is enforced (before routes)
- [ ] Wildcard and catchall patterns behave consistently
- [ ] All test regressions pass
```

## When Done

After completing the review:
1. Commit test_regression.go to version control
2. Run `go test quality/... -v` to verify all regression tests pass
3. If any regression test fails, investigate the BUG in chi's code
4. Report findings in code_reviews/[timestamp]_chi_code_review.md
