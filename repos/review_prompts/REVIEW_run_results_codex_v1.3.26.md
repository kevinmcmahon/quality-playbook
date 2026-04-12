# Review: Quality Playbook v1.3.26 Benchmark Results (Codex)

## Executive Summary

v1.3.26 clearly fixed the artifact-shape problems it targeted, but it still does **not** meet the v2.0 gate.

The good news is concrete:

- all 8 repos reached Phase 2d/Phase 3 closure
- all 8 repos wrote `quality/results/quality-gate.log`
- all 8 repos have canonical `### BUG-NNN` headings
- all 8 repos now contain canonical `UC-01`, `UC-02`, ... identifiers
- the old v1.3.25 “obvious formatting drift” class was materially reduced

The bad news is also concrete:

- `quality_gate.sh` is too shallow to enforce benchmark 41 as written
- it passes `express` even though `quality/results/integration-results.json` is missing
- it passes `gson` even though both sidecars are still non-canonical
- bug-set convergence is still unstable in `chi`, `express`, `httpx`, and partially `cobra`

My bottom line:

- **v1.3.26 is a real closure-hygiene improvement over v1.3.25**
- **it is not yet a benchmark-clean release**
- **the remaining blocker is no longer “did the model format artifacts correctly?” but “did it rediscover the same still-open bugs and prove closure with genuinely conformant executable artifacts?”**

I count **19 confirmed bugs across 8 repos** in this run.

## Verified Snapshot

| Repo | Bugs | quality_gate.sh | 41 | 42 | 43 | Convergence vs v1.3.25 |
|---|---:|---|---|---|---|---|
| `chi` | 1 | PASS (0 FAIL / 1 WARN) | PASS | PASS | PASS | **Regression** |
| `cobra` | 2 | PASS (0 FAIL / 0 WARN) | **FAIL** | PASS | PASS | **Partial** |
| `express` | 2 | PASS (0 FAIL / 0 WARN) | **FAIL** | PASS | PASS | **Regression** |
| `gson` | 2 | PASS (0 FAIL / 0 WARN) | **FAIL** | PASS | PASS | **Strong** |
| `httpx` | 5 | PASS (0 FAIL / 1 WARN) | PASS | PASS | PASS | **Regression** |
| `javalin` | 2 | PASS (0 FAIL / 0 WARN) | PASS | PASS | PASS | **Strong** |
| `serde` | 1 | PASS (0 FAIL / 1 WARN) | PASS | PASS | PASS | **Strong** |
| `virtio` | 4 | PASS (0 FAIL / 1 WARN) | PASS | PASS | PASS | **Strong** |

Notes:

- Benchmark **41** above is my reading of the benchmark text in `references/verification.md`, not the gate script’s reading.
- Benchmark **42** passes mechanically everywhere because the script was executed and exited 0 everywhere.
- Benchmark **43** passes everywhere because canonical `UC-NN` identifiers are now present in every repo.

## What v1.3.26 Clearly Fixed

### 1. Heading format

This is the cleanest visible improvement.

v1.3.25:

- 3/8 repos used `## BUG-NNN`

v1.3.26:

- 8/8 repos use `### BUG-NNN`

That is exactly the kind of issue a script gate should solve, and here it did.

### 2. Use case identifiers

This also improved decisively.

v1.3.25:

- most repos had use-case content but not canonical `UC-01` style identifiers

v1.3.26:

- all 8 repos now contain `UC-NN` identifiers in `REQUIREMENTS.md`

This is a real recovery of ground, including relative to the user’s v1.3.21 observation.

### 3. The gate really did run

This was not just prose.

Evidence:

- all 8 repos have `quality/results/quality-gate.log`
- all 8 `PROGRESS.md` files explicitly record the gate command
- re-running `bash .github/skills/quality_gate.sh .` in `express-1.3.26` and `gson-1.3.26` exits 0 exactly as logged

So benchmark 42 is genuinely being exercised now.

## What quality_gate.sh Still Misses

This is the most important v1.3.26 finding.

The script improved conformance, but it does **not** yet implement benchmark 41 correctly.

### False pass 1: `express`

`repos/express-1.3.26/quality/results/integration-results.json` is missing entirely.

Yet:

- `quality/results/quality-gate.log` says `RESULT: GATE PASSED`
- re-running `bash .github/skills/quality_gate.sh .` in `repos/express-1.3.26` also passes

Why:

- the script only checks `integration-results.json` **if the file already exists**
- it never fails on absence

That means the script currently cannot enforce complete integration-sidecar closure.

### False pass 2: `gson`

`gson` is the clearest benchmark-41 false positive.

Actual problems:

- `tdd-results.json` uses `bug_id` instead of required `id`
- `tdd-results.json` omits required per-bug `requirement` and `fix_patch_present`
- `integration-results.json` is missing `uc_coverage`
- `integration-results.json` uses non-canonical values like `recommendation: "pass-with-open-bugs"` and group `result: "passed"` / `"baseline-passed-via-reactor"`
- `TDD_TRACEABILITY.md` is missing entirely

Yet:

- `quality_gate.sh` still exits 0

Why:

- it checks root-key presence mostly with `grep`
- it does not validate per-bug keys
- it does not validate per-group keys
- it does not validate allowed enum values
- it does not require `uc_coverage`
- it does not require `TDD_TRACEABILITY.md`

### False pass 3: `cobra`

`cobra` is less severe than `gson`, but the script still misses a real problem.

`tdd-results.json` says:

- `verified: 2`
- `confirmed_open: 2`
- `red_failed: 2`

for a run with only 2 bugs, both marked `confirmed open`.

That summary is internally contradictory, but the gate passes because it only checks that `summary` exists.

## Bug Discovery Comparison to v1.3.25

This is where v1.3.26 is still not a v2.0 candidate.

### Stable / convergent repos

These look genuinely good:

- `javalin`: 2 -> 2, same two bugs
- `gson`: 2 -> 2, same two bugs
- `serde`: 1 -> 1, same bug
- `virtio`: 4 -> 4, same core bug set, just reordered

These four repos are the strongest evidence that the playbook can hold a stable bug set across clean runs.

### Regressed repos

These are the main blockers:

#### `chi`: 6 -> 1

This is a large regression in bug-finding depth.

More importantly, several v1.3.25 surfaces are still visibly present in the unchanged source:

- `middleware/compress.go` still uses substring matching for `Accept-Encoding`
- the early-flush/compression path is still structurally unchanged
- `middleware/content_encoding.go` still iterates literal `Content-Encoding` header values without comma-list parsing
- `mux.go` still assigns `r.Pattern = rctx.routePattern`

So this does not look like “the old bugs were fixed.” It looks like they were mostly not rediscovered.

#### `express`: 2 -> 2, but different 2

The new bugs are both real:

- `app.render()` can throw before callback delivery because `new View(...)` happens outside the `tryRender()` wrapper
- `res.jsonp()` can emit malformed JavaScript when callback sanitization empties the callback name

But the two v1.3.25 clean-run bugs are also still visibly present:

- `res.sendFile()` still overwrites `opts.etag` with `this.app.enabled('etag')`
- `res.set('Content-Type', value)` still passes `mime.contentType(value)` directly and can still forward `false`

So `express` did **not** converge. It found two different real bugs while missing two previously found real bugs that still exist.

#### `httpx`: 3 -> 5, but different 5

The 1.3.26 bug set is real and interesting:

- redirect-generated GET retains stale `Content-Type`
- digest auth signs stale URI after redirect challenge
- early `.encoding` access freezes UTF-8 too early
- lazy header encoding + mutation corrupts latin-1
- digest auth drops challenge cookies when request cookies already exist

But the 1.3.25 bug set is also still visibly present:

- WSGI request headers still decode with ASCII
- WSGI response headers still encode with ASCII
- `Headers.__setitem__()` still uses UTF-8 while constructor normalization defaults to ASCII

So this is not convergence. It is a **different real bug set** on the same codebase snapshot.

### Partial repo

#### `cobra`: 2 -> 2, one held, one drifted

`cobra` kept the builtin-help/required-flag bug, but it dropped the older `ArgAliases` manual-entry bug, which is still visible in source:

- `command.go` still documents `ArgAliases` as “accepted if entered manually”
- `OnlyValidArgs` still validates only the static `ValidArgs` slice

Instead, v1.3.26 replaced it with a new dynamic-`ValidArgsFunction` bug, which is also real.

So `cobra` is better than `chi` / `express` / `httpx`, but not fully converged.

## Answers to the Prompt Questions

### 1. Did quality_gate.sh improve conformance?

Yes, clearly, but only for the shallow artifact-shape issues it actually checks.

What improved materially:

- headings: 8/8 correct
- UC IDs: 8/8 present
- gate execution: 8/8 logs, 8/8 exit 0

What did **not** improve enough:

- strict sidecar conformance
- required TDD traceability artifacts
- integration sidecar existence
- bug-set convergence

So the answer is:

- **yes on formatting and presence**
- **no on full schema correctness and closure truthfulness**

### 2. Sidecar JSON schema compliance

This improved a lot at the root-key level, but not enough at the real benchmark-41 level.

My read:

- **Clear PASS:** `chi`, `httpx`, `javalin`, `serde`, `virtio`
- **Clear FAIL:** `express`, `gson`
- **Borderline / I count FAIL:** `cobra` because the summary bookkeeping is contradictory

Representative issues:

- `express`: missing `integration-results.json`
- `gson`: wrong per-bug keys, missing `uc_coverage`, invalid recommendation/result values
- `cobra`: impossible summary counts

So this is better than v1.3.25, but not “fixed.”

### 3. Use case identifier adoption

This is the cleanest success story in the release.

All 8 repos now contain canonical `UC-NN` identifiers.

That said, the script check is weaker than it should be:

- it counts raw `UC-` matches, not unique labeled use cases
- for example `express` reports `24 canonical UC-NN identifiers` in the gate log even though it only has 6 actual use cases

Still, benchmark 43 itself is satisfied in all 8 repos.

### 4. Bug discovery comparison to v1.3.25

Summary:

- `javalin`: same 2 bugs — good
- `virtio`: same 4 core bugs — good
- `gson`: same 2 bugs — good
- `serde`: same 1 bug — good
- `cobra`: partial convergence
- `chi`: strong regression
- `express`: strong regression
- `httpx`: strong regression

Total bug count went from **22** in v1.3.25 to **19** in v1.3.26, but this is **not** because the old bugs disappeared. In several repos, the old bug surfaces are still plainly visible in source.

### 5. Fix patch generation

If we count **actual fix patches**, not regression-test patches, v1.3.26 did **not** improve the fix-patch rate.

v1.3.25 fix-patch repos:

- `express`
- `httpx`
- `javalin`

v1.3.26 fix-patch repos:

- `express`
- `gson`
- `javalin`

So the rate is still effectively **3/8 repos**.

Important nuance:

- `cobra` added patch files, but they are regression-test patches only, not fix patches
- `httpx` regressed from 3 fix patches to 0
- `gson` improved from 0 to 2 fix patches

So patch generation quality moved around, but did not improve overall.

### 6. V2.0 gate assessment

The v2.0 gate is still **not met**.

What a pass would need:

- each repo consistently rediscovers the previously found still-open bugs on the same codebase snapshot

What this run actually shows:

- 4 repos look convergent
- 1 repo is partial
- 3 repos are still unstable

The specific blockers are:

- `chi`
- `express`
- `httpx`
- and to a lesser degree `cobra`

So v1.3.26 is closer on artifact hygiene, but **not** closer on the core convergence criterion that matters for v2.0.

### 7. Regression or progress since v1.3.21?

Both.

Progress on visible conformance:

- use-case IDs: recovered strongly
- heading format: recovered strongly
- `schema_version`: present at the root in all 8 TDD sidecars

But not all the way:

- deeper sidecar correctness is still inconsistent
- bug-set convergence is still weaker than it needs to be

My interpretation:

- **v1.3.26 is better than v1.3.25 on closure mechanics**
- **it is not yet better than the best earlier runs on stable bug discovery**

I do think skill complexity is still part of the problem. The playbook is now asking the model to do deep exploration, artifact generation, TDD, audits, reconciliation, and script cleanup in one sweep. The new script helps with the last piece, but it does not prevent discovery quality from drifting earlier in the run.

### 8. Recommended changes for v1.3.27

#### P0

1. **Upgrade `quality_gate.sh` from grep-based presence checks to real JSON validation.**  
   Use `jq` and validate:
   - required per-bug fields
   - required per-group fields
   - `uc_coverage`
   - allowed enum values
   - required summary fields
   - summary/value consistency where possible

2. **Make the gate fail if `integration-results.json` is missing after Phase 3 closure.**  
   `express` should not have been able to pass the gate.

3. **Add a convergence check against the prior clean unseeded run.**  
   For benchmark mode, compare the current BUG set with the immediately previous clean run and fail closure if previously found still-open bug surfaces disappear without a source change.

4. **Add a discovery-floor / scope-drift guard.**  
   If a repo like `chi` drops from 6 confirmed bugs to 1 on the same source snapshot, force a review of the missed prior surfaces before closure.

5. **Require executable closure artifacts beyond the gate’s current checks.**  
   Missing `TDD_TRACEABILITY.md`, missing committed regression assets, or missing functional test artifacts should block closure.

#### P1

1. **Fix `quality_gate.sh` version detection.**  
   Every gate log currently prints `Version:` blank because the script looks for `../SKILL.md` from `.github/skills/quality_gate.sh`.

2. **Count unique UC IDs, not raw `UC-` matches.**

3. **Distinguish fix patches from regression-test patches in the gate output.**  
   Right now `cobra` looks healthier than it is because the gate counts patch files generically.

4. **Teach the gate to require `TDD_TRACEABILITY.md` whenever confirmed bugs have red-phase evidence.**

5. **Teach the gate to require language-appropriate functional/regression test assets.**  
   `gson` passing the gate with only `quality/test_functional.md` is too weak.

#### P2

1. **Consider splitting benchmark mode into two explicit passes:**  
   discovery first, closure/gating second. That may reduce the current tradeoff where better artifact hygiene correlates with worse bug-set stability.

2. **Emit a small machine-readable convergence summary artifact** with:
   - bug count
   - carried-forward bug count
   - net-new bug count
   - prior-clean-run comparison

3. **Add a benchmark-specific “old bug surfaces” checklist** for the few repos already known to drift (`chi`, `cobra`, `express`, `httpx`).

## Per-Repo Scorecard

This is the compact scorecard I would use. Unlisted applicable benchmarks pass; benchmarks 32-33 are N/A for all repos because `--no-seeds` skipped continuation mode; mechanical benchmarks 23/27/35/36/37 are N/A outside `virtio`.

| Repo | Clear FAIL benchmarks | Notes |
|---|---|---|
| `chi` | none clearly evidenced from the closure checklist | Formally one of the cleaner artifact sets, but bug discovery regressed badly outside the current checklist. |
| `cobra` | 21, 41 | Triage still relies on summarized log outcomes rather than embedded executable assertions; TDD sidecar summary is self-contradictory. |
| `express` | 14, 41 | Missing `integration-results.json`, yet the gate still passes. |
| `gson` | 14, 17, 28, 41 | No discovery pre-flight in integration protocol, no `TDD_TRACEABILITY.md`, and both sidecars are non-canonical despite the passing gate. |
| `httpx` | 21 | Artifact shape is much better, but triage still lacks the stronger explicit executable-assertion style. Main blocker is convergence, not checklist hygiene. |
| `javalin` | none clearly evidenced from the closure checklist | Strongest overall run in the set. |
| `serde` | none clearly evidenced from the closure checklist | Still light on executable closure depth, but the tracked artifacts are materially cleaner than v1.3.25. |
| `virtio` | 37 | Mechanical proof is real and strong, but `PROGRESS.md` still lacks the required `## Phase 3 Mechanical Closure` section. |

## Final Verdict

v1.3.26 is a **worthwhile release**. It fixed a real class of long-running benchmark hygiene problems:

- headings
- use-case identifiers
- visible script-executed closure

But it is **not** the release that crosses the v2.0 line.

The reason is now sharper than before:

- **artifact-shape conformance is improving**
- **bug-set convergence is still not stable enough**
- **and the new script gate is not yet strong enough to prove the closure it claims**

If v1.3.27 upgrades `quality_gate.sh` into a real schema/convergence validator instead of a root-key grep script, it should remove the current false-pass class quickly. After that, the next real challenge is simplifying or restructuring the run so the model keeps enough exploratory depth to rediscover the same bugs consistently across clean runs.
