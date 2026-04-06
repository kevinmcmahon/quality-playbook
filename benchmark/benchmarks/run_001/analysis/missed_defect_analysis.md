# Missed Defect Analysis — Chi Benchmark Run 001

## Scoring Correction

CHI-15 was incorrectly scored as MISS for Sonnet. Sonnet's review (lines 122-125) explicitly identified "RoutePattern() is missing the trailing slash cleanup after replaceWildcards" — the exact defect. Corrected score: Sonnet = DIRECT HIT.

**Corrected miss count: 3 defects (not 4)**

## The 3 True Misses

### CHI-03: Method Accessor Confusion

**Defect:** `Close()` called `cw.writer()` (which returns the compression encoder when compressible) instead of `cw.w` (the raw underlying writer). This means Close() tries to close the encoder rather than the actual io.WriteCloser, preventing proper resource cleanup.

**Fix:** One character change: `cw.writer()` → `cw.w` on line 374.

**What the reviews found instead:** All 3 models found 3-5 OTHER bugs in compress.go (nil encoder with non-empty encoding name, substring Accept-Encoding matching, Hijack/Push delegating to wrong writer). They caught the Hijack delegation bug (same pattern — wrong accessor) but NOT the Close delegation bug (same pattern, different method).

**Why it was missed:** The models traced Hijack() and Push() call paths but not Close(). The bug is in the same family as the Hijack bug (delegating to `cw.writer()` when you should use `cw.ResponseWriter` or `cw.w`), but the models didn't generalize the pattern across all methods.

**Root cause pattern:** When a type has multiple accessor methods that return different views of the same data depending on state (here: `writer()` returns the encoder when compressible, `w` is always the raw writer), every call site needs to use the right one. The models checked some call sites but not all.

**Proposed playbook change:** Add to Step 5c (Parallel Code Paths):

> **Accessor method consistency.** When a type provides multiple accessor methods that return different views of the same underlying resource (e.g., a raw field vs. a state-dependent method), audit ALL call sites to verify each uses the correct accessor. A common bug: one method is updated to use the correct accessor but sibling methods in the same type are not. Check every method on the type, not just the one that looks suspicious.

---

### CHI-04: Boundary Value Destruction in String Normalization

**Defect:** `RoutePattern()` applied `strings.TrimSuffix(routePattern, "/")` unconditionally. For the root route "/", this produces an empty string — destroying the route identity.

**Fix:** Guard the trim with `if routePattern != "/" { ... }`.

**What the reviews found instead:** Opus and Haiku both found a real bug in the same file (methodsAllowed not reset in Reset()), but neither examined what TrimSuffix does to the minimal input "/".

**Why it was missed:** The models didn't mentally execute string operations on edge-case inputs. They read the code structurally (what does Reset() clear? what does URLParam() guard?) but didn't ask "what happens when the input to this string chain is the shortest possible valid value?"

**Root cause pattern:** String normalization (trim, replace, join) that works correctly on typical inputs can destroy minimal/empty/root inputs. "/" trimmed of "/" is "". A path trimmed of "//" and then "/" may lose meaningful content. The models don't systematically check normalization chains against boundary inputs.

**Proposed playbook change:** Add to Step 5d (Boundary conditions with empty and zero values):

> **String normalization on minimal inputs.** When code applies string transformations in sequence (trim, replace, join, split), trace the transformation chain with the shortest valid input. Common destruction patterns: `TrimSuffix("/", "/")` → `""`, `strings.Replace(s, "//", "/", -1)` on `"//"` → `"/"` → different semantics, `strings.Join([]string{"/"}, "")` → `"/"` but `TrimSuffix` then destroys it. Each transformation is individually correct but the chain destroys minimal values. Look for guard clauses like `if x != "/" { ... }` — their absence on normalization chains is a bug signal.

---

### CHI-12: Test Setup Temporal Ordering

**Defect:** `httptest.NewServer(r)` starts listening immediately. The test then sets `ts.Config.BaseContext` on the already-running server, causing a data race between the listening goroutine and the config write.

**Fix:** `httptest.NewUnstartedServer(r)` → configure → `ts.Start()`.

**What the reviews found instead:** Opus found other test-level bugs (Fatalf format strings, deprecated ioutil, test helper bugs). None of the models identified the temporal ordering issue.

**Why it was missed:** The models reviewed test code for coding errors (wrong types, missing guards, deprecated APIs) but didn't analyze the temporal semantics of API calls. `NewServer` vs `NewUnstartedServer` is not a coding error visible from reading the function body — it requires knowing that `NewServer` starts a goroutine immediately and that subsequent config changes race with it.

**Root cause pattern:** Test setup code that initializes resources in the wrong order. The pattern is: create-then-configure vs. create-configure-then-start. This shows up with HTTP servers, database connections, client configurations, and any resource that becomes "live" at construction time.

**Proposed playbook change:** Add to Step 3 (Read Existing Tests):

> **Test setup ordering.** In test files, check whether resource creation and configuration happen in the correct temporal order. A common bug: `httptest.NewServer(handler)` starts accepting connections immediately — configuring the server *after* creation races with incoming requests. The same pattern appears with database pools (opening before configuring), HTTP clients (sending before setting auth), and message consumers (subscribing before setting handlers). Look for the pattern: resource created on line N, resource configured on line N+k. If the resource is "live" at creation, the configuration races. The fix is always the same: use the unstarted/builder variant, configure, then start.

Also add to Step 5 (defensive patterns), category for test-specific bugs:

> **Test harness concurrency.** When test setup creates servers, clients, or concurrent resources, check that the creation → configuration → start sequence is correct. `httptest.NewServer()` vs `httptest.NewUnstartedServer()` is the canonical example, but the pattern generalizes: any test resource that spawns goroutines at construction time must be fully configured before construction, not after.

---

## Summary of Proposed Changes

| Change | Location | Addresses |
|--------|----------|-----------|
| Accessor method consistency audit | Step 5c | CHI-03 |
| String normalization on minimal inputs | Step 5d | CHI-04 |
| Test setup ordering | Step 3 | CHI-12 |
| Test harness concurrency | Step 5 | CHI-12 |

## Methodology Note

These proposals are derived from exactly 3 missed defects in a single Go repo (chi). Before incorporating into v1.2.11, they should be:

1. Reviewed by council of three (do these changes improve detection without adding noise?)
2. Tested: re-run the 3 missed defects with updated review protocol to see if the new guidance catches them
3. Validated across a second language/repo to ensure they're not Go-specific
