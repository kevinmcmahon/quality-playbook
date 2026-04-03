# Council Member Review: Proposed Playbook v1.2.11 Changes
**Reviewer:** Sonnet (Council Member)
**Date:** 2026-03-31
**Scope:** v1.2.10 → v1.2.11 proposed changes derived from 3 benchmark misses (CHI-03, CHI-04, CHI-12)

---

## Summary Table

| Change | Target | Verdict | Risk |
|--------|--------|---------|------|
| 1: Accessor method consistency | Step 5c | REVISE | Low — needs tighter scoping to avoid redundancy with existing symmetry guidance |
| 2: String normalization on minimal inputs | Step 5d | REVISE | Low — content is sound, but Go-specific examples undermine the 10-language mandate |
| 3: Test setup temporal ordering | Step 3 | APPROVE | Low-medium — well-scoped, but surface overlap with Change 4 must be resolved |
| 4: Test harness concurrency | Step 5 | REJECT | Medium — redundant with Change 3; misfiled in defensive patterns (Step 5 is for production code) |

---

## Change 1: Accessor Method Consistency (→ Step 5c)

**Verdict: REVISE**

**Reasoning:**

The underlying insight is correct and well-motivated by CHI-03: when a type implements multiple methods that delegate to an underlying resource, updating one method to use the correct accessor without auditing its siblings is a reliable bug pattern. This is worth teaching.

However, Step 5c already contains a "Parallel path symmetry" section that covers exactly this class of bug — the section explicitly calls out "when one path was updated and its sibling was forgotten." Adding a separate paragraph on accessor methods creates structural redundancy and may confuse reviewers about where to look for this guidance.

More critically, the proposed wording ("verify each uses the correct accessor") assumes the reviewer already knows which accessor is "correct" — but in the case of CHI-03, the problem *is* that a method was using a helper (`cw.writer()`) that returns a state-dependent value when it should have used the raw field (`cw.w`). The wording needs to direct reviewers to ask *why* multiple accessors exist in the first place, not just that they should match.

**Risk:** Low. The pattern is narrow enough that false positives (flagging intentional accessor divergence as a bug) should be rare — but the phrase "verify each uses the correct accessor" without context guidance could send reviewers looking for consistency where intentional divergence is the design.

**Suggested rewording (integrate into the existing "Parallel path symmetry" block in Step 5c):**

> **Sibling method accessor audit.** When a type provides multiple methods that perform the same class of operation (close, flush, write, lock), check that all sibling methods delegate to the same underlying resource — not a mix of raw fields and state-dependent helpers. A common miss: one method is updated to use the correct accessor (`cw.w`), but sibling methods still use a convenience wrapper (`cw.writer()`) that returns a different object depending on state. When reviewing any method that looks suspicious, enumerate *all* methods on that type and verify each makes the same accessor choice with the same rationale.

This makes the detection mechanism explicit (enumerate all methods on the type, check the *reason* for the accessor choice, not just whether they match), and slots cleanly into the existing parallel-path framework without duplicating it.

---

## Change 2: String Normalization on Minimal Inputs (→ Step 5d)

**Verdict: REVISE**

**Reasoning:**

The addition is valuable and fills a real gap. The existing Step 5d boundary condition guidance covers integer underflow and empty chunks but says nothing about transformation chains that destroy minimal valid string inputs. CHI-04 is a clean example of a whole class of bugs: individually correct string operations that together destroy a canonical minimal value (`"/"` → `""`).

The content and the list of destruction patterns are accurate and useful. The problem is that all three examples in the proposed wording are Go standard library calls (`TrimSuffix`, `strings.Replace`, `strings.Join`). This is a 10-language playbook. A reviewer working in Python, Java, or Ruby will read this guidance and either skip it ("that's a Go thing") or fail to apply it to their equivalent (`str.rstrip("/")`, `String.replaceAll("//", "/")`, `String#sub`).

The guard clause heuristic — "their absence on normalization chains is a bug signal" — is the most transferable piece and deserves prominence across all languages.

**Risk:** Low. The pattern is narrow (string normalization chains, not all string operations), and the guard clause signal is a reliable indicator rather than noise-generator.

**Suggested rewording:**

> **String normalization on minimal inputs.** When code applies string transformations in sequence (trim, replace, join, split, strip), trace the transformation chain with the shortest valid input. Common destruction patterns (illustrated with Go; apply the equivalent in your language): `TrimSuffix("/", "/")` → `""`, `strings.Replace(s, "//", "/", -1)` on `"//"` → `"/"` → different semantics. In Python: `"/".rstrip("/")` → `""`. In Java: `"/".replaceAll("/$", "")` → `""`. Each transformation is individually correct but the chain destroys the minimal valid value. Look for guard clauses like `if x != "/" { ... }` (or equivalent) wrapping normalization chains — their absence is a bug signal. Route path normalization, URL canonicalization, and slug generation are high-probability locations for this pattern.

---

## Change 3: Test Setup Temporal Ordering (→ Step 3)

**Verdict: APPROVE**

**Reasoning:**

Step 3 already has a "Test harness consistency audit" block that checks for framework-level annotation gaps. Adding temporal ordering of resource creation is a natural and well-scoped extension of that audit. The guidance is concrete (creation vs. configuration line numbers), the canonical example (`httptest.NewServer` vs `NewUnstartedServer`) is unambiguous, and the generalization to DB pools, HTTP clients, and message consumers makes it applicable beyond Go.

The instruction "If the resource is 'live' at creation, the configuration races" provides a clear decision rule that reviewers can apply without deep knowledge of every library.

One concern: Change 4 covers essentially the same pattern and is targeted at Step 5. These two changes together create the same guidance appearing in two different steps. I'm recommending rejection of Change 4 (see below) — if that recommendation is accepted, Change 3 stands without duplication.

**Risk:** Low-medium. False positives are possible when a reviewer applies this to resources that *are* safe to configure post-construction (most pure objects), but the qualifier "if the resource is 'live' at creation" should suppress most false flags. Consider adding one example of a *safe* post-construction configuration pattern to sharpen the discriminator.

---

## Change 4: Test Harness Concurrency (→ Step 5)

**Verdict: REJECT**

**Reasoning:**

Step 5 (defensive patterns, `references/defensive_patterns.md`) is explicitly scoped to *production code patterns*. The file's opening line states: "Defensive code patterns are evidence of past failures or known risks." The section on Concurrency Issues in `defensive_patterns.md` focuses on production-code race conditions — goroutines, mutexes, shared mutable state. Test harness setup ordering is not a production code defensive pattern; it is a test code structural defect.

More critically, Change 4 is substantively redundant with Change 3. The `httptest.NewServer` vs `NewUnstartedServer` example appears in both; the creation-configuration-start sequence is described in both; the generalization to other resource types is in both. If Change 3 is approved and lives in Step 3 (where test code review already belongs), Change 4 adds nothing except confusion about where to look.

If the Council wishes to preserve the Step 5 angle on this pattern, the appropriate framing is *production code* resource initialization ordering (e.g., opening a database connection before configuring its connection pool, creating an HTTP server before setting its TLS config), not test harness setup. That framing would be genuinely additive to Step 5 and would not duplicate Change 3.

**Suggested disposition:** Reject Change 4 as written. If the production-code variant of this pattern is considered valuable, commission a separate Change 4' targeting Step 5 with a production-code focus (no test harness examples, no `httptest` references).

---

## Cross-Cutting Observations

### Language agnosticism

Changes 1, 3, and 4 are adequately language-agnostic. Change 2 fails the 10-language standard and requires revision (addressed above). The council should establish a standing rule: any proposed change containing language-specific function calls must include at least one additional language example, or must be framed as "illustrated with X; apply the equivalent in your language."

### Structural pattern the three misses reveal

All three missed defects share a meta-pattern the proposals address individually but not collectively: **local confirmation bias**. In all three cases, the models found the suspicious code (the `Hijack()`/`Push()` methods, the normalization function, the test setup) and stopped after confirming the first suspicious-looking thing looked plausible — without completing the audit.

- CHI-03: Models confirmed `Hijack()` and `Push()` use the correct accessor, stopped there.
- CHI-04: Models confirmed the normalization function works for typical inputs, stopped there.
- CHI-12: Models confirmed the test has the right handler, stopped there.

None of the proposed changes directly address this review behavior. Consider adding a general audit-completion directive to `RUN_CODE_REVIEW.md`: *"When a suspicious pattern is investigated and found acceptable in one location, that finding is a trigger to check all analogous locations — not a reason to stop looking."* This meta-rule would have caught all three misses more directly than any of the four individual additions.

### Should any changes be merged?

Changes 3 and 4 address the same defect (CHI-12) and should not both be added. Merge them into the single, stronger Change 3 (Step 3 placement) and reject Change 4.

Changes 1 and the existing "Parallel path symmetry" guidance in Step 5c should be merged as described in the Change 1 revision above.

### Additional patterns these misses reveal

**CHI-04 (boundary destruction)** also points toward a gap in the existing boundary condition checklist: the current Step 5d text instructs reviewers to check empty strings but does not mention *canonical minimal values* that are semantically meaningful (like `"/"` for route paths, `"."` for current directory, `"*"` for wildcards). An empty string check would not have caught CHI-04 — `"/"` is not empty. The revision to Change 2 should emphasize "shortest *valid* input" rather than "empty input" to capture this distinction.

**CHI-12 (temporal ordering)** also implies a gap in the existing Concurrency Issues grep table in `defensive_patterns.md`: the current patterns (`goroutine`, `go `, `chan`, `mutex`, `sync.Mutex`, `atomic`) focus on explicit synchronization primitives. A resource that starts a goroutine at construction time (like `httptest.NewServer`) won't appear in any of these patterns. Consider adding `httptest.NewServer`, `net.Listen`, `http.Server{}.ListenAndServe` and their equivalents as a secondary grep target under Concurrency Issues — not as a replacement for Change 3/4 but as a code-search complement.
