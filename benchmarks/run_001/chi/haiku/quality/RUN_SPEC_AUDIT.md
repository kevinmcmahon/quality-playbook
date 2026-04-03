# Spec Audit Protocol: Council of Three

## Overview

This protocol uses three independent AI models to audit the chi router codebase against its specification and design requirements. No single model catches everything; different models have different strengths and blind spots. Cross-referencing findings catches defects any single model would miss.

The audit covers:
- **Specification compliance** — Does code implement documented behavior?
- **Design correctness** — Does code follow the intended architecture?
- **Defensive pattern coverage** — Are failure modes properly handled?
- **Edge case handling** — Do boundaries and corner cases work correctly?

## Audit Prompt for Council of Three

Use this prompt with Claude, Claude Code, Cursor, Copilot, or other AI models.

```
# Chi HTTP Router Specification Audit

You are auditing the chi HTTP router (Go) against its specification.
Review the codebase and identify gaps, violations, or edge cases.

## Context

- **Repository**: /sessions/quirky-practical-cerf/mnt/QPB/repos/chi
- **Language**: Go (v1.20+)
- **Architecture**: Radix tree HTTP router with middleware composition
- **Key Files**: chi.go, mux.go, tree.go, context.go, chain.go, middleware/

## Specification & Requirements to Verify

### 1. Pattern Matching Specification
Read chi.go lines 30-54 (pattern documentation):
- Named placeholder {name} matches any sequence up to / or end
- Regexp patterns {number:\\d+} use Go RE2 syntax
- Asterisk /* matches rest of URL including /
- Verify the implementation matches these guarantees

Scrutiny areas:
- Are regex patterns correctly anchored with ^ and $ (see tree.go lines 737-741)?
- Does catch-all really match / characters (line 497)?
- Do param patterns correctly reject cross-slash matches (line 452)?

### 2. Routing Algorithm Specification
The radix trie should provide O(k) matching where k = key length.
Verify:
- Prefix sharing doesn't change routing semantics (InsertRoute method)
- Route matching is deterministic regardless of insertion order
- Node splitting correctly preserves existing routes while adding new ones
- Backtracking correctly manages parameter state (lines 489, 537)

Scrutiny areas:
- In findRoute (lines 401-544), verify all code paths return correct handlers
- Check that parameter accumulation never leaks between failed branches
- Verify tree traversal order is correct (static → param → regexp → catchall)

### 3. Middleware Composition Specification
Middleware should execute in declaration order: first declared runs first.
Verify:
- Use() registers global middleware before routes
- With() adds inline middleware correctly
- Group() creates fresh middleware stacks
- Parent middleware always runs before sub-router middleware
- Middleware wraps handlers right-to-left (innermost handler last)

Scrutiny areas:
- In mux.go, does With() preserve parent middleware (lines 243-257)?
- Does Route() or Mount() preserve parent middleware?
- Is the middleware chain built correctly (updateRouteHandler method)?

### 4. Request Context Lifecycle Specification
Each request must have isolated, properly-reset routing context.
Verify:
- Context is fetched from pool (line 81)
- Context is completely reset (line 82)
- Reset clears ALL state: patterns, params, method tracking, flags
- Context is returned to pool after request (line 91)
- No state leaks between requests

Scrutiny areas:
- In mux.go line 82, does Reset() clear all necessary fields (see context.go)?
- Are RoutePatterns and methodsAllowed properly cleared?
- Can concurrent requests share a context before full reset?

### 5. Handler Resolution Specification
Handlers must be resolved in priority order: specific → general.
Verify:
- Static routes match before param routes (ntStatic=0, ntParam=2)
- Param routes match before catch-all (ntParam=2, ntCatchAll=3)
- Method-specific routes match before method-all routes
- 405 (method not allowed) is returned when path matches but method doesn't
- 404 (not found) is returned only when no path matches

Scrutiny areas:
- In findRoute, does the node type loop (lines 405-427) check static first?
- Does methodNotAllowed flag get set correctly when path matches but method doesn't (lines 478, 524)?
- Is 405 response generated only when methodNotAllowed is true?

### 6. Parameter Handling Specification
URL parameters must be extracted correctly and matched against patterns.
Verify:
- Parameter names match pattern definitions
- Parameter values are correctly extracted from path
- Regexp patterns validate parameter values
- Parameters don't leak between overlapping patterns
- Multiple parameters in one route maintain correct order and values

Scrutiny areas:
- In tree.go, does patParamKeys() correctly extract all param names?
- Are param keys stored in correct order in paramKeys array (line 465)?
- Does parameter value extraction (lines 457-459) handle all cases?
- When backtracking occurs (line 489), are parameters correctly reset?

### 7. Panic Safety Specification
Panic should occur at registration time for invalid patterns, never at request time for valid routes.
Verify:
- Invalid patterns panic with actionable messages
- Valid patterns never panic during routing
- Handler nil checks prevent nil pointer dereferences
- Bounds checking prevents index out of range

Scrutiny areas:
- Pattern validation (tree.go lines 687-752): Do all error cases panic?
- Param key duplication check (line 765): Does it panic?
- Handler registration: Are nil handlers detected (mux.go lines 209, 229, 290)?
- Path indexing (line 416): Is bounds checking present before search[0]?

### 8. Middleware Stack Freezing Specification
Middleware stack must be frozen after first route is added.
Verify:
- Use() panics if called after routes are added (line 102-104)
- This prevents subtle bugs where middleware order depends on registration sequence
- The first route registration triggers handler compilation (updateRouteHandler)

Scrutiny areas:
- Does line 101-104 correctly panic on late middleware registration?
- Is mx.handler set to non-nil to trigger the check?
- Can any code path bypass the middleware freeze check?

### 9. Context Value Propagation Specification
Context values set by middleware must be visible to handlers and subsequent middleware.
Verify:
- Middleware can set context values using context.WithValue()
- Handlers receive modified context
- Sub-router handlers see parent middleware's context values

Scrutiny areas:
- In mux.go ServeHTTP, is the context passed correctly (line 87)?
- Does r.WithContext() create a new request with modified context?
- Are context values preserved through Mount/Route (check sub-router handlers)?

### 10. NotFound and MethodNotAllowed Handling Specification
These handlers must be customizable and apply to all routes unless overridden.
Verify:
- NotFound() sets custom 404 handler
- MethodNotAllowed() sets custom 405 handler
- These handlers are inherited by sub-routers unless overridden
- NotFound is invoked when no route matches
- MethodNotAllowed is invoked when path matches but method doesn't

Scrutiny areas:
- In mux.go lines 197-213, does NotFound correctly propagate to sub-routers?
- Does MethodNotAllowed do the same (lines 217-233)?
- In findRoute, is methodNotAllowed flag checked to return MethodNotAllowed handler?

## How to Perform the Audit

1. **Read the specification sections** above
2. **Examine the codebase** for each requirement
3. **Note any findings** using the format below
4. **Flag edge cases** you identify

## Finding Format

**For each finding:**

```
[VIOLATION / QUESTION / EDGE CASE] — [Component] — [Severity: Critical/High/Medium/Low]

**What:** One-sentence description of the finding

**Evidence:** Code location (file:line) and relevant code snippet

**Impact:** What breaks or what's the risk?

**How to verify:** How would you test this finding?

**Recommendation:** How should this be fixed? (if applicable)
```

Example:
```
[VIOLATION] — tree.go findRoute — Severity: High

**What:** Parameter values accumulate without bounds in routeParams.Values

**Evidence:** tree.go:458, line `rctx.routeParams.Values = append(...)` has no size limit.
Over 1000 concurrent requests with deep nesting could cause memory exhaustion.

**Impact:** Denial of service via memory exhaustion; unbounded growth of parameter slice

**How to verify:** Serve 10,000 requests with deeply nested params (/a/b/c/d/.../z),
check memory usage doesn't grow linearly

**Recommendation:** Add configurable maximum parameter depth or pre-allocate slice capacity
```

## Triage: Merge Findings Across Models

After all three models complete audits, merge findings:

1. **Consensus violations** — All three models flag the same issue
   - Confidence: Very High
   - Action: Must fix immediately

2. **Multi-model findings** — Two models flag similar issues
   - Confidence: High
   - Action: Investigate and likely fix

3. **Single-model findings** — One model flags an issue
   - Confidence: Medium
   - Action: Double-check before fixing; might be false positive

4. **Contradictory findings** — Models disagree
   - Confidence: Low
   - Action: Investigate to determine which is correct

## Fix Execution

For each finding that must be fixed:

1. **Create regression test** in quality/test_functional.go that fails on buggy code
2. **Fix the code** in the identified location
3. **Verify regression test passes**
4. **Run full test suite:** `go test ./quality -v`
5. **Run with race detector:** `go test -race ./quality -v`

## Example Audit Session

**Model 1 (Claude):**
- Flags parameter leakage risk in backtracking (line 489)
- Questions whether catch-all always matches / (line 497)
- Finds no consensus issues

**Model 2 (GPT-4):**
- Flags same parameter leakage risk (high confidence match)
- Flags middleware order issue in With() (line 247)
- Finds no issues with catch-all

**Model 3 (Gemini):**
- Flags parameter leakage risk again (consensus)
- Confirms catch-all is correct
- Agrees middleware order is suspicious

**Merge result:**
- Consensus: Parameter leakage in backtracking (Very High confidence, must fix)
- Multi-model: Middleware ordering edge case (High confidence, investigate)
- Single-model: None

## Running the Audit

Copy the audit prompt above and paste into your preferred AI model. For each model, save findings to:
- Model 1: `quality/spec_audit_model1.md`
- Model 2: `quality/spec_audit_model2.md`
- Model 3: `quality/spec_audit_model3.md`

Then merge findings into: `quality/spec_audit_merged.md`

Example command to run all three audits in parallel:

```bash
# Assuming you have access to three different AI models via CLI or API
for model in claude gpt4 gemini; do
  echo "Running audit with $model..."
  cat quality/RUN_SPEC_AUDIT.md | \
    AI_MODEL=$model ai_audit > quality/spec_audit_$model.md &
done
wait
echo "All audits complete. Review quality/spec_audit_*.md"
```

## Questions for Council Review

The three models should specifically address:

1. **Does the implementation match the documented pattern syntax?** (chi.go lines 30-54)
2. **Is the radix tree algorithm implemented correctly?** (tree.go InsertRoute & findRoute)
3. **Is middleware always executed in declaration order?** (mux.go middleware chain)
4. **Can a request context leak to another request?** (mux.go pool management)
5. **Does the router distinguish 404 from 405?** (findRoute method tracking)
6. **Can invalid patterns cause panics at request time?** (pattern validation)
7. **Are parameter values correctly isolated between requests?** (context reset)
8. **Can parameters overflow or corrupt state?** (parameter list bounds)
9. **Is middleware stack freezing enforced correctly?** (Use method guard)
10. **Do NotFound and MethodNotAllowed handlers work correctly?** (handler resolution)

## Output

After audit, save findings to `/sessions/quirky-practical-cerf/mnt/QPB/benchmarks/run_001/chi/haiku/quality/spec_audit_results.md` with format:

```markdown
# Spec Audit Results

## Consensus Findings (Very High Confidence)
[List violations all three models flagged]

## Multi-Model Findings (High Confidence)
[List issues two or more models flagged]

## Single-Model Findings (Medium Confidence)
[List issues from individual models worth investigating]

## Required Fixes
1. [Issue and line numbers]
2. [Expected fix approach]

## Optional Improvements
1. [Non-critical improvements]
2. [Performance optimizations]
```
