# Code Review Protocol: chi

## Bootstrap (Read First)

Before reviewing, read these files for context:
1. `quality/QUALITY.md` — Quality constitution and fitness-to-purpose scenarios
2. `chi.go` — Router/Routes interfaces (the public API contract)
3. `mux.go` — HTTP multiplexer (the orchestration layer)
4. `tree.go` — Radix trie (the most complex module)
5. `context.go` — Routing context and URL parameter management

## What to Check

### Focus Area 1: Radix Trie Correctness (tree.go)

**Where:** `tree.go` — `InsertRoute()`, `addChild()`, `findRoute()`, `replaceChild()`
**What:** Node splitting logic when routes share prefixes. Verify `longestPrefix()` correctly computes common prefixes. Check that `replaceChild()` finds the correct child to replace (panics on missing child at line 328). Verify `findRoute()` backtracks correctly when a param node matches but has no handler for the method.
**Why:** A split error silently misroutes requests. Backtracking bugs cause intermittent 404s that depend on route registration order.

### Focus Area 2: URL Parameter Accumulation (tree.go + context.go)

**Where:** `tree.go:387-388` (URLParams append), `tree.go:457-458` (routeParams append), `tree.go:489` (routeParams reset on backtrack), `context.go:100-107` (URLParam reverse lookup)
**What:** Verify that `routeParams.Values` is correctly reset during backtracking (`rctx.routeParams.Values = rctx.routeParams.Values[:prevlen]` at tree.go:489). Check that `URLParams` accumulation across sub-routers preserves parameter ordering for reverse lookup. Check the catch-all default branch at tree.go:493 — it appends an empty string to routeParams.Values even when no catch-all matched.
**Why:** Stale parameter values from a failed backtrack path cause wrong data to be served to the wrong user.

### Focus Area 3: Context Pool Lifecycle (mux.go)

**Where:** `mux.go:60-92` (ServeHTTP pool Get/Put), `context.go:82-96` (Reset)
**What:** Verify `Reset()` clears every mutable field on Context. Check that `pool.Put()` is always called after `pool.Get()`, including when middleware or handlers panic (the Recoverer middleware catches panics, so ServeHTTP's deferred put still runs — but verify this assumption). Check that inline muxes (`mx.inline == true`) share the parent's pool correctly.
**Why:** A missed Reset field leaks routing data from one request to the next. A missed pool.Put leaks Context objects.

### Focus Area 4: Mount Handler Propagation (mux.go)

**Where:** `mux.go:289-340` (Mount), `mux.go:296-298` (duplicate pattern check), `mux.go:301-307` (handler propagation), `mux.go:309-322` (mountHandler closure)
**What:** Verify that NotFound and MethodNotAllowed handlers propagate from parent to child only when the child's handler is nil. Check the mountHandler closure — it modifies `rctx.RoutePath` and resets the wildcard URLParam, but verify these modifications are correct for all nesting depths. Check the three route registrations at mux.go:324-335 — the pattern, pattern+"/", and pattern+"/*" registrations.
**Why:** Missing handler propagation causes generic 404s instead of custom error pages. Wrong RoutePath causes nested routers to match against stale paths.

### Focus Area 5: Method Type Bit Flags (tree.go)

**Where:** `tree.go:17-77` (methodTyp constants, methodMap, RegisterMethod), `tree.go:344-371` (setEndpoint with method bit masks)
**What:** Verify `setEndpoint()` correctly handles the mSTUB, mALL, and individual method flags. Check that `mALL` is updated when `RegisterMethod()` adds custom methods. Verify the `method&mSTUB == mSTUB` and `method&mALL == mALL` bit checks are correct.
**Why:** A wrong bit mask silently drops handlers for specific HTTP methods — GET works but PATCH silently 404s.

### Focus Area 6: Middleware Chain Construction (chain.go + mux.go)

**Where:** `chain.go:36-49` (chain function), `mux.go:100-105` (Use ordering guard), `mux.go:236-257` (With inline mux)
**What:** Verify middleware chain builds right-to-left (last middleware wraps endpoint first). Check that `With()` correctly copies parent middlewares (mux.go:245-248). Verify inline mux shares tree but has independent middleware stack.
**Why:** Wrong chain order means auth middleware runs after handler, or logging misses early-return responses.

## Guardrails

- **Line numbers are mandatory.** If you cannot cite a specific line, do not include the finding.
- **Read function bodies, not just signatures.** Don't assume a function works correctly based on its name.
- **If unsure whether something is a bug or intentional**, flag it as a QUESTION rather than a BUG.
- **Grep before claiming missing.** If you think a feature is absent, search the codebase. If found in a different file, that's a location defect, not a missing feature.
- **Do NOT suggest style changes, refactors, or improvements.** Only flag things that are incorrect or could cause failures.

## Output Format

Save findings to `quality/code_reviews/YYYY-MM-DD-reviewer.md`

For each file reviewed:

### filename.ext
- **Line NNN:** [BUG / QUESTION / INCOMPLETE] Description. Expected vs. actual. Why it matters.

### Summary
- Total findings by severity
- Files with no findings
- Overall assessment: SHIP IT / FIX FIRST / NEEDS DISCUSSION
