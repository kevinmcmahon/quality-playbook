# Code Review Protocol for Chi Router

## Overview

This protocol guides code review of the chi HTTP router, focusing on correctness of the routing algorithm, middleware composition, and request context lifecycle. The router handles request-critical operations: pattern matching, parameter extraction, and handler invocation. Silent bugs here route requests to wrong handlers or corrupt request context.

## Bootstrap Files

Before reviewing changes to chi, read these files to understand the codebase:

- **AGENTS.md** — Project description, setup, architecture overview
- **quality/QUALITY.md** — Quality constitution with 10 fitness-to-purpose scenarios
- **chi.go** — Router interface definitions
- **mux.go** — HTTP multiplexer core logic
- **tree.go** — Radix tree routing algorithm
- **context.go** — Request routing context
- **chain.go** — Middleware composition

## Focus Areas by Architecture Component

### 1. Radix Tree Algorithm (tree.go)

**What to focus on:**
- Pattern insertion logic (`InsertRoute` method, lines 138-227)
- Route matching logic (`findRoute` method, lines 401-544)
- Node splitting and prefix handling
- Parameter and regexp pattern compilation
- Edge traversal order and backtracking

**Key guardrails:**
- Line numbers are mandatory — flag exact lines where issues occur
- Trace the complete matching path through the tree for any edge case
- Grep for calls to `append` that modify `rctx.routeParams` — verify reset logic
- Verify that node splitting doesn't change routing semantics

**Red flags:**
- Boundary conditions: empty paths, single-char segments, very long paths
- Regex patterns with special characters or nested groups
- Backtracking logic in `findRoute` — verify parameter rollback (line 489)
- Node type ordering (line 405-427) — static before param before wildcard

### 2. Request Multiplexing (mux.go)

**What to focus on:**
- Handler computation and middleware chaining (`updateRouteHandler` method)
- Request context lifecycle (ServeHTTP method, lines 63-92)
- Sync pool management for routing context reuse
- Handler resolution through method types and endpoint registration
- NotFound and MethodNotAllowed handler logic

**Key guardrails:**
- Check that middleware stack is frozen after first route (line 101-104)
- Trace context pool Get/Put operations — verify reset completeness
- Verify nil handler checks (line 65-66, 209, 229, 290, 301-306)
- Check that sub-router handlers preserve parent middleware

**Red flags:**
- Middleware added after routes — should panic with clear message
- Handler nil without proper default fallback
- Pool reuse without full reset — state leakage between requests
- Middleware wrapping order — should be right-to-left (innermost first)

### 3. Routing Context (context.go)

**What to focus on:**
- URL parameter accumulation and ordering (RouteParams structure)
- Routing pattern tracking (RoutePatterns slice)
- Method allowed tracking for 405 responses
- Context reset logic (Reset method)

**Key guardrails:**
- Grep for `routeParams.Keys` and `routeParams.Values` — verify they stay in sync
- Check parameter key order matches pattern order
- Verify `methodNotAllowed` flag is set correctly (when path matches but method doesn't)
- Check `methodsAllowed` list is accurate and complete

**Red flags:**
- Parameter lists growing unbounded across requests (pool reuse leakage)
- Pattern list containing duplicates or incomplete patterns
- Method allowed list including unsupported methods
- Context reset not clearing all fields

### 4. Middleware Composition (chain.go)

**What to focus on:**
- Handler wrapping order in middleware chains
- Middleware execution sequence through nested routers
- Inline vs. global middleware stacking

**Key guardrails:**
- Verify middleware wraps handlers right-to-left (innermost handler executes last)
- Check that `With()` middleware prepends correctly, not appends
- Verify parent middleware executes before sub-router middleware

**Red flags:**
- Middleware executing out of declaration order
- Auth or critical middleware bypassed due to wrapping order
- Context values from parent middleware not visible to sub-router handlers

## How to Perform a Code Review

### Step 1: Read the changed code

For changes to core files (tree.go, mux.go, context.go, chain.go):
1. Read the entire function or section being changed
2. Understand the data flow — what data enters, how it transforms, what exits
3. Identify any side effects (pool operations, context mutations, parameter list changes)

### Step 2: Check against Fitness Scenarios

Map the change against each scenario in quality/QUALITY.md:

| Scenario | Review Questions |
|----------|------------------|
| #1: Insertion order independence | Does the change affect node splitting or insertion order? Will routing results change based on insertion order? |
| #2: Parameter corruption | Does the change touch parameter accumulation? Are parameter resets complete? |
| #3: Middleware ordering | Does the change affect middleware wrapping or execution order? |
| #4: Regex edge cases | Does the change modify pattern parsing or regex compilation? |
| #5: Catch-all specificity | Does the change affect how catch-all patterns are matched? |
| #6: 405 detection | Does the change affect method tracking or 405 response generation? |
| #7: Context pool safety | Does the change touch context creation or reset? Are concurrent requests safe? |
| #8: Boundary paths | Does the change handle empty segments, trailing slashes, single-char paths? |
| #9: Pattern validation | Does the change validate patterns early? Are panic messages actionable? |
| #10: Handler nil checks | Does the change add or remove nil checks? Are defaults set? |

### Step 3: Verify against defensive patterns

Check for these patterns in the changed code:

1. **Panic-based validation** — Pattern registration should panic on errors, not silently fail
2. **Nil checks** — Handler nil checks, context nil checks, endpoint nil checks
3. **Reset completeness** — Context reset must clear all fields, not just some
4. **Boundary safety** — Code must handle empty/zero inputs without panics
5. **Regex safety** — Compiled regexes must be cached; don't recompile on every request

### Step 4: Test the change

Before approving:

1. **Run the functional test suite:** `go test ./quality -v`
   - All tests must pass
   - Pay attention to test duration — significant slowdown suggests performance regression

2. **Test boundary cases manually** if the change affects routing:
   - Empty path: `/`
   - Single segment: `/users`
   - Parameter types: numeric, alphabetic, regexp, catch-all
   - Overlapping patterns that force backtracking
   - High-concurrency request load

3. **Regression test for the bug fix** (if this is a bug fix):
   - Write a test that fails on old code, passes on new code
   - Add it to quality/test_functional.go

### Step 5: Flag findings appropriately

**BUG**: A clear violation of requirements or defensive patterns
- Example: "Line 247: backtracking doesn't reset routeParams — parameter leakage risk"
- Include line number, code snippet, and consequence

**QUESTION**: Something you're uncertain about, not a definite bug
- Example: "Line 156: Is label always in search[0]? What if search is empty?"
- Ask for clarification before marking as bug

**FALSE POSITIVE**: Something that looks wrong but isn't
- Never mark this in your output; instead, investigate fully before flagging anything

## Guardrails

**Line numbers are mandatory** — Flag a line number or don't flag it. "The middleware code has an issue" is not actionable. "line 247, the parameter reset is incomplete" is.

**Read function bodies, not just signatures** — Skimming is dangerous. Read the complete function and trace the data flow.

**Grep before claiming missing** — If you claim a nil check is missing, grep to verify it's truly absent. Don't assume.

**Do NOT suggest style changes** — Chi has a style; we respect it. Flag incorrectness, not style.

**Do NOT suggest hypothetical refactors** — If the code is correct but could be cleaner, leave it alone. Only flag things that are broken.

## Regression Test Generation

After code review produces BUG findings:

1. For each BUG, write a test in `quality/test_regression.go` that reproduces the bug
2. The test should fail on the current (broken) code
3. Run the test: `go test ./quality -run TestRegression -v`
4. Verify that the test fails (confirming the bug is real)
5. Have the developer fix the code
6. Verify the test now passes

Example regression test structure:
```go
func TestRegressionIssueXXX_ParameterLeakageUnderBacktracking(t *testing.T) {
    // Setup that triggers the bug: overlapping patterns + backtracking
    r := chi.NewRouter()
    r.Get("/{a:\\d+}", handler1)
    r.Get("/{b:[a-z]+}", handler2)

    // Request that should trigger backtracking
    req := httptest.NewRequest("GET", "/abc", nil)
    w := httptest.NewRecorder()
    r.ServeHTTP(w, req)

    // Assertion that should fail on buggy code, pass on fixed code
    if chi.URLParam(req, "a") != "" {
        t.Error("bug: parameter from failed branch leaked")
    }
}
```

## Example Review Session

**Change:** Modified `findRoute` method in tree.go to use a new backtracking approach

**Review steps:**
1. Read the modified `findRoute` method (lines 401-544)
2. Trace an example: request `/articles/abc-def` against patterns `/articles/{id:\d+}` and `/articles/{slug:[a-z-]+}`
3. Check Scenario #2 (Parameter corruption under overlapping routes) — does the new backtracking reset parameters correctly?
4. Grep for `routeParams.Values = routeParams.Values[:` to find all reset points
5. Run `go test ./quality -v` — verify all tests pass
6. Run concurrent test: `go test ./quality -run TestScenario7 -v -race` to check for race conditions
7. Verify line numbers in flagged issues

## Files to Check

When reviewing any change:

- **tree.go** — Most critical; the routing algorithm is the core
- **mux.go** — Request lifecycle and handler resolution
- **context.go** — Parameter management and state tracking
- **chain.go** — Middleware wrapping logic
- **quality/test_functional.go** — Functional tests must pass

When reviewing middleware:

- **middleware/*.go** — Individual middleware modules
- **quality/test_functional.go** — Middleware tests must pass

## Sign-Off

Do NOT approve a change without:
1. ✓ Reading the complete function being changed
2. ✓ Mapping against at least 5 fitness scenarios
3. ✓ Running the functional test suite successfully
4. ✓ Testing boundary cases if the change affects routing
5. ✓ Flagging issues with line numbers or marking as none
