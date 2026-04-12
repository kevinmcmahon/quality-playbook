# Review: v1.3.26 Run Results
**Reviewer:** GitHub Copilot (Claude Sonnet 4.6)  
**Date:** 2026-04-11  
**Version:** 1.3.26  
**Repos:** 8 (virtio, httpx, express, javalin, chi, cobra, gson, serde)  
**Runner:** `run_playbook.sh --copilot --parallel --no-seeds`  
**Total bugs found:** 19 (virtio 4, httpx 5, express 2, javalin 2, chi 1, cobra 2, gson 2, serde 1)

---

## Executive Summary

v1.3.26's quality_gate.sh is the most significant quality improvement since v1.3.21. **All 8 repos pass the gate with 0 FAIL** — a dramatic turnaround from v1.3.25's pervasive non-compliance. The three v1.3.25 regression targets (BUGS.md heading, sidecar JSON, UC identifiers) are fully resolved at the structural level. Two long-standing benchmark failures (express regression skip guard, chi skip guard) are also fixed.

The gate has meaningful blind spots in schema depth validation that leave some internal conformance issues undetected (gson per-bug fields, cobra summary inconsistency, non-standard recommendation enum values). These are not detected because the gate checks key presence but not key names inside nested structures or enum validity.

Chi's bug count dropped from 6 to 1 — the most concerning finding in this batch. This is a discovery regression, not a quality gate issue. Five previously-confirmed chi bugs are absent from the v1.3.26 run.

### Run Summary

| Repo | Bugs | Gate | Fix Patches | TDD Verdict |
|------|------|------|-------------|-------------|
| virtio | 4 | PASS (1 WARN) | 0 | confirmed open |
| httpx | 5 | PASS (1 WARN) | 0 | confirmed open |
| express | 2 | PASS (0 WARN) | 4 (2 fix + 2 regr) | **TDD verified** |
| javalin | 2 | PASS (0 WARN) | 4 (2 fix + 2 regr) | **TDD verified** |
| chi | 1 | PASS (1 WARN) | 0 | confirmed open |
| cobra | 2 | PASS (0 WARN) | 2 (regr only) | confirmed open |
| gson | 2 | PASS (0 WARN) | 4 (2 fix + 2 regr) | confirmed open |
| serde | 1 | PASS (1 WARN) | 0 | confirmed open |

---

## Q1 — Did quality_gate.sh improve conformance?

**Yes, dramatically — at the structural level.**

The gate ran on all 8 repos and all 8 passed with 0 FAIL. The three v1.3.25 failures that the gate was designed to catch:

| Issue | v1.3.25 | v1.3.26 |
|-------|---------|---------|
| Wrong `## BUG-NNN` heading | 3/8 FAIL | **0/8 FAIL** |
| Non-conformant tdd-results.json (top-level) | 6/8+ non-conformant | **0/8 FAIL at top-level** |
| No canonical UC identifiers | 7/8 missing | **0/8 FAIL** |
| No regression skip guards (express) | FAIL | **PASS** — now uses `it.skip(...)` |
| Chi regression positive-only without t.Skip | FAIL | **PASS** — now uses `t.Skip("BUG-001...")` |
| Empty writeups/ dir (cobra, gson) | FAIL | **PASS** — writeups present for all bugs |

The model clearly ran the gate and fixed issues before closure. This is evidenced by PROGRESS.md entries like: `"Closure gate: bash .github/skills/quality_gate.sh . — passed with 0 FAIL, 1 WARN"`.

**However, the gate has meaningful depth blind spots:**

The gate validates presence of top-level JSON keys but does not validate:
1. **Per-bug field names** — gson uses `"bug_id"` (non-standard) instead of `"id"` in tdd-results.json. Gate says PASS.
2. **Summary field names** — gson uses `"fixed"` instead of `"verified"` in summary. Gate says PASS.
3. **Recommendation enum values** — gson integration-results.json uses `"pass-with-open-bugs"` (invalid; allowed: `"SHIP"`, `"FIX BEFORE MERGE"`, `"BLOCK"`). Gate says PASS.
4. **Cobra summary inconsistency** — cobra tdd-results.json has `"verified": 2` in the summary but all bugs have `"verdict": "confirmed open"`. Gate says PASS.
5. **Missing integration-results.json** — express has no integration-results.json at all. The gate doesn't check for it (express's gate log only covers tdd-results.json checks; the integration-results.json block is absent). Gate says PASS.
6. **Empty mechanical-verify.log** — virtio's mechanical-verify.log is 0 bytes. The gate checks that the file exists and that `mechanical-verify.exit` is 0, but does not check that the log contains confirmation output. Gate says PASS.

Additionally: the gate is invoked without a `--version` flag (`bash .github/skills/quality_gate.sh .`), so the "Version:" field in every gate log is empty. The version stamp comparison then compares PROGRESS.md against itself (self-referential), not against a canonical SKILL.md version. The checks still pass because the artifacts are internally consistent.

**Verdict on Q1:** The gate works. It caught and forced correction of the v1.3.25 structural failures. The remaining issues are schema depth gaps that require the gate to validate field names and enum values inside nested JSON structures, not just root key existence.

---

## Q2 — Sidecar JSON schema compliance

**tdd-results.json: major improvement. Integration-results.json: partial.**

### tdd-results.json

All 8 repos now have `schema_version: "1.1"` and `skill_version: "1.3.26"` (massive improvement from v1.3.25 where httpx and serde were missing both). Per-repo assessment:

| Repo | Top-level ✓ | Per-bug `id` field | Summary `verified` key | Verdict |
|------|------------|---------------------|------------------------|---------|
| virtio | ✓ | ✓ (`id`) | ✓ | Conformant |
| httpx | ✓ | ✓ (`id`) | missing `total` | Conformant (minor) |
| express | ✓ | ✓ (`id`) | missing `total`, `confirmed_open: 0` | Conformant |
| javalin | ✓ | ✓ (`id`) | missing `total` | Conformant (minor) |
| chi | ✓ | ✓ (`id`) | ✓ | Conformant |
| cobra | ✓ | ✓ (`id`) | `verified: 2` **contradicts** bugs (all `confirmed open`) | PARTIAL |
| gson | ✓ | **`bug_id`** (non-standard) | `fixed`/`notes` (non-standard) | NON-CONFORMANT |
| serde | ✓ | ✓ (`id`) | ✓ | Conformant |

**Gson issues:** `bugs[*].bug_id` instead of `bugs[*].id`; `summary.fixed` instead of `summary.verified`; `summary.notes` (extra undocumented key); missing `summary.red_failed` and `summary.green_failed`. The gate doesn't catch these because it only checks that the `bugs` and `summary` keys exist at the root level.

**Cobra contradiction:** `summary.verified: 2` implies two bugs were verified with patches. The actual bug verdicts are both `"confirmed open"`. The `verified` count in summary should be 0 (not 2). This is an internal consistency error the gate doesn't check.

### integration-results.json

| Repo | Exists | Recommendation | Groups schema | Issues |
|------|--------|---------------|---------------|--------|
| virtio | ✓ | `BLOCK` ✓ | standard | Conformant |
| httpx | ✓ | **`SHIP`** (5 confirmed bugs?) | standard | Recommendation questionable but valid enum |
| express | **MISSING** | N/A | N/A | Gate does not check for it |
| javalin | ✓ | `FIX BEFORE MERGE` ✓ | standard | Conformant |
| chi | ✓ | **`SHIP`** (1 confirmed bug?) | standard | Recommendation questionable but valid enum |
| cobra | ✓ | `SHIP` | standard | Conformant |
| gson | ✓ | **`pass-with-open-bugs`** | non-standard `name`/`result: "passed"` | NON-CONFORMANT |
| serde | ✓ | `FIX BEFORE MERGE` ✓ | standard | Conformant |

**Express:** Missing integration-results.json entirely. The quality gate does not flag this absence because the gate script only checks for tdd-results.json when confirmed bugs exist; it does not enumerate integration-results.json as a required artifact.

**Gson:** Non-standard recommendation `"pass-with-open-bugs"` (not in allowed enum). Groups use `"name"` instead of `"group"`, and `"result": "passed"` instead of `"result": "pass"` (valid enum is `pass`, not `passed`). Also missing `uc_coverage` field.

**Overall sidecar compliance vs v1.3.25:** The top-level structural compliance is 100% improved. The schema depth compliance shows remaining issues in gson (tdd + integration), cobra (tdd summary), and express (missing integration). These are 3 of 8 repos with inside-structure issues, vs v1.3.25 which had 6/8+ with top-level or structural failures.

---

## Q3 — Use case identifier adoption

**Fully adopted: 8/8 repos have canonical UC-NN identifiers.**

This is the most complete fix from v1.3.25 (7/8 missing UC identifiers → 0/8 missing). All repos have proper use case sections with `UC-01`, `UC-02`, etc. More importantly, multiple repos have backreferences from requirements to use cases:

| Repo | UC count | Backreferences |
|------|----------|----------------|
| virtio | 19 UC-NN identifiers | Requirements link to UC-NN |
| httpx | 6 canonical (6 use cases) | Linked in requirements |
| express | 6 canonical (UC-01 through UC-06) | 18 backreferences in requirements |
| javalin | 6 canonical | Linked in requirements |
| chi | 6 canonical | Linked in requirements |
| cobra | 6 canonical | Linked in requirements |
| gson | 6 canonical | Linked in requirements |
| serde | 14 UC-NN identifiers | Linked in requirements |

Express is the gold standard: 6 use cases defined (`UC-01: Build a route-oriented web app`, `UC-02: Deploy behind proxies`, `UC-03: Return HTTP-correct responses`, `UC-04: Support JSONP/browser integrations`, `UC-05: Render server-side views`, `UC-06: Upgrade Express 4-era apps`) with every requirement carrying a `"Linked use cases: UC-NN"` field.

The model ran `quality_gate.sh` which checks for UC-NN identifiers and would have caught any run that tried to skip this. The gate shows: `PASS: Found N canonical UC-NN identifiers` for all repos.

---

## Q4 — Bug discovery comparison to v1.3.25

**19 total bugs (vs 22 in v1.3.25). Mixed convergence.**

### Per-repo comparison

| Repo | v1.3.25 bugs | v1.3.26 bugs | Convergence |
|------|-------------|-------------|-------------|
| virtio | 4 (vm_reset readback, INTx admin VQ, config INTx, RING_RESET) | **4 (same)** | ✅ Converged |
| httpx | 3 (WSGI latin-1 ×2, Headers constructor/mutation) | **5 (completely different)** | ❌ Different set |
| express | 2 (sendFile etag, Content-Type false) | **2 (completely different)** | ❌ Different set |
| javalin | 2 (HEAD metadata, CORS 200) | **2 (same)** | ✅ Converged |
| chi | 6 (compress q=0, compress header, Recoverer upgrade, AllowContentEncoding, r.Pattern prefix, Allow dups) | **1 (Recoverer upgrade only)** | ❌ Major regression |
| cobra | 2 (required flags/help, OnlyValidArgs/ArgAliases) | **2 (same)** | ✅ Converged |
| gson | 2 (trailing null, duplicate null key) | **2 (same)** | ✅ Converged |
| serde | 1 (Buffered 128-bit) | **1 (same)** | ✅ Converged |

**Converged: 5/8 repos** (virtio, javalin, cobra, gson, serde).  
**Not converged: 3/8 repos** (httpx, express, chi).

### Notable per-repo findings

**httpx (5 bugs):** v1.3.26 found a completely different, arguably richer bug set. The v1.3.25 WSGI latin-1 crashes are absent; instead: redirect Content-Type leak (BUG-001), Digest auth signing wrong URI after redirect (BUG-002), `Response.encoding` early access freezing UTF-8 (BUG-003), lazy header encoding + mutation corruption (BUG-004), and Digest auth dropping challenge cookies (BUG-005). These are all HTTP/auth-level bugs. Neither run appears to be exploring the same area — this is genuine discovery variance, not a quality problem.

**express (2 bugs):** Both are different from v1.3.25. `app.render()` throwing synchronously on View construction failure (BUG-001) and `res.jsonp()` emitting malformed JS when callback sanitization empties the name (BUG-002). The v1.3.25 bugs (sendFile etag mode, Content-Type false) are not present. Four runs of express (v1.3.21, v1.3.24, v1.3.25, v1.3.26) have found different bugs each time — express is the least converged of the 8 repos.

**chi (1 bug):** The major regression. v1.3.25 found 6 bugs: Compress q=0, Compress flush-without-header, Recoverer strict upgrade, AllowContentEncoding comma, r.Pattern drops prefix, Method-not-allowed duplicates Allow. v1.3.26 found only BUG-001 (Recoverer upgrade check — `Connection: Upgrade` exact string match failing for tokenized values). The other 5 bugs are absent from the audit. This is not a gate issue — it reflects the spec audit finding only 1 bug from auditor-3. The chi spec audit was less thorough in v1.3.26.

---

## Q5 — Fix patch generation

**Major improvement from v1.3.25.**

| Repo | v1.3.25 fix patches | v1.3.26 fix patches |
|------|--------------------|--------------------|
| virtio | 0 | 0 (no patches dir) |
| httpx | 0 | 0 (patches dir exists, empty) |
| express | 0 | **2 fix + 2 regression** (gate: PASS, 4 patches) |
| javalin | 4 (2 fix + 2 regr) | **4 (2 fix + 2 regr)** (consistent) |
| chi | 0 | 0 (no patches dir) |
| cobra | 0 | **2 regression test patches** (gate: PASS, 2 patches) |
| gson | 0 | **4 (2 fix + 2 regression)** (gate: PASS, 4 patches) |
| serde | 0 | 0 (no patches dir) |

v1.3.25: 1/8 repos with fix patches.  
v1.3.26: **3/8 repos with fix patches** (express, javalin, gson), plus cobra now has regression test patches.

The improvement is significant and likely indirect — the script-verified closure gate forced the model to complete Phase 2d properly, and fix patch generation comes naturally when the full TDD closure sequence runs. Express and gson now have both fix patches AND TDD-verified (express) or confirmed-open-with-fix (gson) closures.

**Virtio** (4 kernel bugs, 0 patch proposals): kernel patches require physical hardware testing and are explicitly noted as out-of-scope for the automated run. This is correct and expected.

**httpx**: 5 bugs, 0 fix patches. The patches dir exists but is empty. The httpx bugs involve complex client-side HTTP behavior (Digest auth, encoding state machines) that may require more context to patch than the playbook run budget allows. The gate registers this as WARN (not FAIL), which is appropriate policy.

---

## Q6 — V2.0 gate assessment

**5/8 repos converging. V2.0 is within reach for those repos.**

The V2.0 gate requires a clean run that catches all bugs previously found. Using v1.3.25 as the prior baseline:

| Repo | v1.3.25 bugs refound? | Fix patches? | TDD verified? | V2.0 status |
|------|----------------------|-------------|---------------|-------------|
| virtio | ✅ All 4 same | ❌ | ❌ | Near — same bugs, no patches |
| httpx | ❌ Different 5 | ❌ | ❌ | Not converged |
| express | ❌ Different 2 | ✅ | ✅ TDD verified | Not converged (different bugs) |
| javalin | ✅ Same 2 | ✅ | ✅ TDD verified | **Near V2.0** |
| chi | ❌ 5 missing | ❌ | ❌ | Regressed |
| cobra | ✅ Same 2 | partial | ❌ | Near — same bugs, regression patches |
| gson | ✅ Same 2 | ✅ | ❌ | Near — same bugs + fix patches |
| serde | ✅ Same 1 | ❌ | ❌ | Near — same bug, no patch |

**Javalin** is the closest to V2.0: same 2 bugs found for two consecutive clean runs (v1.3.25 and v1.3.26), TDD verified with fix patches in both runs. If a third run finds the same 2 bugs, javalin has converged.

**Express and chi** remain unblocked for V2.0: express finds different bugs each run; chi had a discovery regression. These need another clean run to determine if the new bug sets stabilize.

**Critical remainders per repo for V2.0:**
- All: Fix patch generation for kernel/systems languages (virtio, serde)
- Chi: Recover the 5 missing bugs from v1.3.25 via a more thorough spec audit
- httpx, express: Establish a stable bug set across two clean runs

---

## Q7 — Regression or progress since v1.3.21?

**v1.3.26 has fully recovered and in several dimensions surpassed v1.3.21.**

| Metric | v1.3.21 | v1.3.25 | v1.3.26 |
|--------|---------|---------|---------|
| Use cases in REQUIREMENTS.md | 9/9 | 1/8 | **8/8** |
| schema_version present | 6/9 | 2/8 | **8/8** |
| Canonical UC-NN identifiers | partial | 1/8 | **8/8** |
| Correct BUGS.md heading (H3) | N/A | 5/8 | **8/8** |
| Regression skip guards | N/A | 6/8 | **8/8** |
| Writeups for all confirmed bugs | N/A | 6/8 | **8/8** |
| Fix patches generated | some | 1/8 | **3/8 + 1 partial** |
| Gate script compliance | N/A | N/A | **8/8** |

The v1.3.25 regression from v1.3.21 was caused by instruction drift — the model stopped following text instructions for use cases and JSON schema as the SKILL.md grew more complex. v1.3.26 fixes this structurally: `quality_gate.sh` enforces conformance mechanically.

The remaining v1.3.21 advantage — better bug discovery breadth for chi (which wasn't benchmarked in v1.3.21) — is a content issue, not a structural one. The v1.3.26 skill complexity is no longer the barrier to structural compliance. It may still affect the depth of spec audit exploration.

---

## Q8 — Recommended changes for v1.3.27

### P0 — Extend gate to validate JSON schema depth

The gate currently checks top-level key presence only. Add per-entry validation:
- `tdd-results.json bugs[*]`: require `id`, `requirement`, `red_phase`, `green_phase`, `verdict`, `fix_patch_present`, `writeup_path`
- `tdd-results.json summary`: require `verified`, `confirmed_open`, `red_failed`, `green_failed` (not `fixed`, not `notes`)
- `integration-results.json groups[*]`: require `group`, `name`, `use_cases`, `result`
- `integration-results.json recommendation`: validate against allowed enum (`SHIP`, `FIX BEFORE MERGE`, `BLOCK`)
- `integration-results.json`: add to gate's required-file check

**Root cause of gap:** gson's tdd-results.json uses `bug_id`/`fixed` without detection, cobra has contradictory `verified` count, express has no integration-results.json — all pass the current gate.

### P0 — Require integration-results.json when RUN_INTEGRATION_TESTS.md exists

Express has RUN_INTEGRATION_TESTS.md but no integration-results.json. The gate must check: if `RUN_INTEGRATION_TESTS.md` exists in quality/, then `quality/results/integration-results.json` is required. Add this check to the file-existence gate section.

### P1 — Add "OK:" echo to verify.sh template

The `verify.sh` script uses `diff -u` which produces zero output on a clean match. This results in a 0-byte `mechanical-verify.log`. Benchmark #37 expects "lines like 'OK: ...' or 'MISMATCH: ...'". Add an explicit echo: `echo "OK: $(basename $EXPECTED)"` before the diff command, so the log is non-empty and confirms the script ran. A 0-byte log is indistinguishable from a pre-seeded empty file.

### P1 — Chi spec audit depth regression investigation

Chi found 6 bugs in v1.3.25 and 1 in v1.3.26. Five real bugs disappeared between runs. This is not a gate issue — the spec audit was less thorough. The playbook should include a continuity check: if a prior run found N bugs and the current run finds fewer than N, flag this in the triage as "candidate missing bug" with a pre-flight check against prior BUGS.md entries. This is essentially continuation-mode seed logic applied to the spec audit phase, not just Phase 0.

### P1 — Gate invocation with --version flag

The gate is invoked with `bash .github/skills/quality_gate.sh .` without a `--version` flag. The VERSION variable is empty. All version stamp comparisons are self-referential (artifacts compared to each other). Add the version to the run instruction: `bash .github/skills/quality_gate.sh --version 1.3.27 .` so the gate verifies against the actual current release version, not just internal consistency.

### P2 — Cobra's contradictory summary

Cobra `summary.verified: 2` with all bugs `confirmed open` is a logical contradiction. The gate should check: `summary.verified == count(bugs where verdict == "TDD verified")`. If the count doesn't match, this should be a FAIL or WARN. This is a simple arithmetic consistency check.

### P2 — Express convergence investigation

Express has found different bugs in every run (v1.3.21, v1.3.24, v1.3.25, v1.3.26). This may reflect genuine bug density and variability in a large, well-used framework. Or it may reflect insufficient spec audit depth. Consider establishing Express as a convergence benchmark target for v1.3.27: run with `--seeds` containing v1.3.26 bugs to see if the same bugs are refound under seed guidance. This would distinguish "bugs exist but exploration variance is high" from "bugs get fixed between runs."

---

## Per-Repo Scorecards

### virtio (4 bugs confirmed, kernel C)

**v1.3.26 bugs found:**
- BUG-001: `vm_reset()` zeros STATUS but never reads back zero before reinit
- BUG-002: INTx admin VQ uses `queue_idx++` instead of `avq->vq_index`
- BUG-003: `vp_interrupt()` returns only vring handler result for config-only interrupts → IRQ_NONE
- BUG-004: `vring_transport_features()` missing `case VIRTIO_F_RING_RESET:` → default clears queue-reset support

Same 4 bugs as v1.3.25 (v1.3.25 numbered them differently but the bugs are identical). Converged.

**Mechanical artifacts:**
- `verify.sh` exits 0 (live confirmed)
- `vring_transport_features_cases.txt`: 8 case labels present, RING_RESET absent → consistent with BUG-004
- `mechanical-verify.log`: **0 bytes** (diff has no output on clean match). Benchmark #37 requires "lines like 'OK: ...' or 'MISMATCH: ...'" — this log fails that requirement. The exit code is correct (0), but no confirmation line exists.

| Benchmark | Status | Notes |
|-----------|--------|-------|
| #14 tdd-results schema (top-level) | PASS | schema_version 1.1, skill_version 1.3.26 |
| #14 tdd-results per-bug | PASS | id/requirement/phases/verdict all present |
| #16 regression skip guards | PASS | `@unittest.expectedFailure` |
| #23 mechanical artifacts | PASS | verify.sh + cases artifact present |
| #26 version stamp | PASS | 1.3.26 throughout |
| #30 writeups | PASS | BUG-001.md through BUG-004.md |
| #35 immediate mech gate | PASS | exit 0 receipt present |
| #36 no circular triage probes | PASS | |
| #37 Phase 3 bash closure log | **PARTIAL** | Exit 0 confirmed; log is 0 bytes (no "OK:" line) |
| #38 individual auditor files | PASS | 3 auditors + triage |
| #39 ### BUG-NNN heading | PASS | All H3 ✓ |
| #41 sidecar JSON post-write | PASS | All required root keys present |
| #42 quality_gate.sh PASS | PASS | 0 FAIL, 1 WARN (no fix patches) |
| #43 UC-NN identifiers | PASS | 19 canonical UC-NN references |

**Overall: ~42/43.** One partial (benchmark #37, empty mechanical log). All v1.3.25 failures resolved.

---

### httpx (5 bugs confirmed, Python)

**v1.3.26 bugs found (all NEW vs v1.3.25):**
- BUG-001: Redirect-generated GET retains `Content-Type` header from the dropped body
- BUG-002: Digest auth retries sign the original URI after a redirect challenge
- BUG-003: Early access to `Response.encoding` freezes UTF-8 before callable autodetection
- BUG-004: Lazy header encoding then mutation corrupts ISO-8859-1 header values
- BUG-005: Digest auth drops challenge cookies when request already has cookies

None of the v1.3.25 WSGI latin-1 bugs appear. Discovery variance is high for httpx — different areas (auth vs transport) explored each run.

| Benchmark | Status | Notes |
|-----------|--------|-------|
| #14 tdd-results schema (top-level) | PASS | schema_version 1.1, skill_version 1.3.26 |
| #14 tdd-results per-bug | PASS | All required fields present |
| #16 regression skip guards | PASS | `@pytest.mark.xfail(strict=True)` |
| #26 version stamp | PASS | 1.3.26 |
| #30 writeups | PASS | 5 writeups for 5 bugs |
| #38 individual auditor files | PASS | 3 auditors + triage |
| #39 ### BUG-NNN heading | PASS | H3 ✓ (was H2 in v1.3.25) |
| #41 sidecar JSON post-write | PASS | All keys present |
| #42 quality_gate.sh | PASS | 0 FAIL, 1 WARN (no fix patches) |
| #43 UC-NN identifiers | PASS | 6 canonical use cases |

**Overall: ~42/43.** Missing fix patches is WARN; no FAILs. Prior v1.3.25 failures (H2 heading, schema missing keys) fully resolved.

---

### express (2 bugs, TDD verified with patches, JavaScript)

**v1.3.26 bugs found (both NEW vs v1.3.25):**
- BUG-001: `app.render()` throws synchronously when `View` construction fails (should pass error to callback)
- BUG-002: `res.jsonp()` emits malformed JavaScript when callback sanitization empties the callback name

Best-performing non-kernel repo alongside javalin. TDD verified (green phase passed with fix patches applied). Has fix patches for both bugs.

**Missing:** `integration-results.json` — the gate did not flag this. Express has `RUN_INTEGRATION_TESTS.md` but no `quality/results/integration-results.json`.

| Benchmark | Status | Notes |
|-----------|--------|-------|
| #14 tdd-results schema | PASS | schema_version 1.1, `"verified": 2` ✓ |
| #14 integration-results.json | **FAIL** | File absent; gate did not check |
| #16 regression skip guards | PASS | `it.skip(...)` (was plain `it()` in v1.3.25) |
| #26 version stamp | PASS | 1.3.26 |
| #30 writeups | PASS | BUG-001.md, BUG-002.md ✓ |
| #38 individual auditor files | PASS | 3 auditors + triage |
| #39 ### BUG-NNN heading | PASS | H3 ✓ (was H2 in v1.3.25) |
| #41 sidecar JSON (tdd) | PASS | |
| #41 sidecar JSON (integration) | **FAIL** | integration-results.json absent |
| #42 quality_gate.sh | PASS | 0 FAIL, 0 WARN |
| #43 UC-NN identifiers | PASS | 6 use cases (UC-01 through UC-06), 18 backreferences |

**Overall: ~41/43.** Missing integration-results.json is a genuine conformance gap the gate doesn't catch.

---

### javalin (2 bugs, TDD verified with patches, Kotlin)

**v1.3.26 bugs found (same as v1.3.25 — converged):**
- BUG-001: HEAD→GET fallback loses matched endpoint metadata and route roles in `beforeMatched`
- BUG-002: Disallowed CORS OPTIONS preflight can be normalized back to HTTP 200

Javalin is the most consistent repo in the benchmark suite. Found the same 2 bugs in v1.3.24, v1.3.25, and now v1.3.26. TDD verified with fix patches in all three runs. Consistently achieves 40+ benchmark score.

| Benchmark | Status | Notes |
|-----------|--------|-------|
| #14 tdd-results schema | PASS | schema_version 1.1, `"verified": 2` ✓ |
| #16 regression skip guards | PASS | `@Disabled("BUG-001: ...")` |
| #26 version stamp | PASS | 1.3.26 |
| #30 writeups + patches | PASS | 4 files (2 fix + 2 regression) |
| #38 individual auditor files | PASS | 3 auditors + triage |
| #39 ### BUG-NNN heading | PASS | H3 ✓ |
| #41 sidecar JSON | PASS | All keys conformant |
| #42 quality_gate.sh | PASS | 0 FAIL, 0 WARN |
| #43 UC-NN identifiers | PASS | 6 use cases |

**Overall: ~43/43.** No failures identified. Best structural result in this batch.

---

### chi (1 bug confirmed, Go)

**v1.3.26 bugs found:** Only BUG-001 (Recoverer checks `Connection: Upgrade` as exact string match, misses tokenized values). v1.3.25 found 6 bugs in chi.

The structural quality is correct — the single bug was found, confirmed, documented, and closed properly with `t.Skip`. But the discovery regression (6→1) is significant.

| Benchmark | Status | Notes |
|-----------|--------|-------|
| #14 tdd-results schema | PASS | schema_version 1.1 ✓ |
| #16 regression skip guards | PASS | `t.Skip("BUG-001...")` ✓ (was positive-only pattern in v1.3.25) |
| #26 version stamp | PASS | 1.3.26 |
| #30 writeups | PASS | BUG-001.md ✓ (was missing in v1.3.25 for some bugs) |
| #38 individual auditor files | PASS | 3 auditors + triage |
| #39 ### BUG-NNN heading | PASS | H3 ✓ |
| #41 sidecar JSON | PASS | All keys conformant; `green_phase: "skipped"` correct for unfixed bug |
| #42 quality_gate.sh | PASS | 0 FAIL, 1 WARN (no fix patches) |
| #43 UC-NN identifiers | PASS | 6 use cases |

**Overall: ~42/43.** Structural quality good. Discovery regression is the primary concern — not measurable by benchmarks.

---

### cobra (2 bugs confirmed, Go)

**v1.3.26 bugs found (same as v1.3.25 — converged):**
- BUG-001: The generated `help` subcommand is treated as a normal business command, so required persistent root flags block `app help`
- BUG-002: `OnlyValidArgs` validates only static `ValidArgs` and ignores `ValidArgsFunction`

First cobra run with regression test patches. Fix patches still absent, but regression test patches confirm the bugs are captured.

**tdd-results.json contradiction:** `summary.verified: 2` but all bugs have `verdict: "confirmed open"`. The `verified` count should be 0.

| Benchmark | Status | Notes |
|-----------|--------|-------|
| #14 tdd-results (top-level) | PASS | schema_version 1.1, all root keys |
| #14 tdd-results (summary) | **PARTIAL** | `verified: 2` contradicts `verdict: "confirmed open"` on all bugs |
| #16 regression skip guards | PASS | `t.Skipf("BUG-001 open: ...")` |
| #26 version stamp | PASS | 1.3.26 |
| #30 writeups | PASS | BUG-001.md, BUG-002.md ✓ (was empty dir in v1.3.25) |
| #38 individual auditor files | PASS | 3 auditors + triage |
| #39 ### BUG-NNN heading | PASS | H3 ✓ |
| #41 sidecar JSON | PASS (gate) / PARTIAL (actual) | Gate passes; summary.verified count is internally inconsistent |
| #42 quality_gate.sh | PASS | 0 FAIL, 0 WARN |
| #43 UC-NN identifiers | PASS | 6 use cases |

**Overall: ~42/43.** Gate passes fully. The `verified` count inconsistency in tdd-results.json is a gate depth blind spot. All v1.3.25 failures (empty writeups dir) resolved.

---

### gson (2 bugs confirmed, Java)

**v1.3.26 bugs found (same as v1.3.25 — converged):**
- BUG-001: High-level parsing accepts trailing data after top-level `null`
- BUG-002: Duplicate map keys not rejected when the earlier value is `null`

Most-improved repo from v1.3.25. V1.3.25 gson had 7 failures (no writeups, H2 heading, test_functional.md as index, REQ ##/### mismatch, stray audit). v1.3.26 has fix patches, proper writeups, and H3 headings.

**tdd-results.json:** Uses `"bug_id"` instead of `"id"` for per-bug entries. Summary uses `"fixed"` instead of `"verified"`, has extra `"notes"` key, missing `"red_failed"` and `"green_failed"`. The gate doesn't catch these internal field name issues.

**integration-results.json:** `"recommendation": "pass-with-open-bugs"` (non-standard enum). Per-group fields use `"name"` instead of `"group"` and `"result": "passed"` instead of `"result": "pass"`. Missing `uc_coverage` field.

| Benchmark | Status | Notes |
|-----------|--------|-------|
| #14 tdd-results (top-level) | PASS | schema_version 1.1 |
| #14 tdd-results (per-bug/summary) | **FAIL** | `bug_id` (not `id`); `fixed` (not `verified`); missing `red_failed`/`green_failed` |
| #14 integration-results | **FAIL** | `pass-with-open-bugs` not in enum; `name`/`passed` not conformant; missing `uc_coverage` |
| #16 regression skip guards | PASS | `@Ignore` in production test files (non-standard location note) |
| #26 version stamp | PASS | 1.3.26 |
| #30 writeups + patches | PASS | 4 patch files, 2 writeups ✓ (was no writeups dir in v1.3.25) |
| #38 individual auditor files | PASS | 3 auditors + triage |
| #39 ### BUG-NNN heading | PASS | H3 ✓ (was H2 in v1.3.25) |
| #41 sidecar JSON post-write validation | **FAIL** | Gate accepted non-conformant fields; internal schema non-conformant |
| #42 quality_gate.sh | PASS | 0 FAIL, 0 WARN (gate blind spot) |
| #43 UC-NN identifiers | PASS | 6 use cases |

**Overall: ~39/43.** Massively improved from v1.3.25 (~33/40). Remaining issues are in JSON schema depth — the gate's blind spot.

---

### serde (1 bug confirmed, Rust)

**v1.3.26 bug found (same as v1.3.25 — converged):**
- BUG-001: Buffered untagged enum deserialization drops `i128`/`u128` support

Same bug as v1.3.25. Consistent across runs.

Rust-specific paths correct: functional test at `test_suite/tests/test_functional.rs`, regression at `test_suite/tests/regression/quality_bug_001.rs`, `#[ignore = "BUG-001: ..."]` skip marker.

| Benchmark | Status | Notes |
|-----------|--------|-------|
| #14 tdd-results schema | PASS | schema_version 1.1, skill_version 1.3.26, all keys |
| #16 regression skip guards | PASS | `#[ignore = "BUG-001: ..."]` |
| #26 version stamp | PASS | 1.3.26 |
| #30 writeups | PASS | BUG-001.md ✓ |
| #38 individual auditor files | PASS | 3 auditors + triage |
| #39 ### BUG-NNN heading | PASS | H3 ✓ |
| #41 sidecar JSON | PASS | All keys conformant |
| #42 quality_gate.sh | PASS | 0 FAIL, 1 WARN (no fix patches) |
| #43 UC-NN identifiers | PASS | 14 UC-NN identifiers |

**Overall: ~42/43.** No failures. No fix patches is a WARN. Consistent with prior runs.

---

## System-Wide Benchmark Summary

| Benchmark | v1.3.25 (8 repos) | v1.3.26 (8 repos) |
|-----------|------------------|------------------|
| #14 tdd-results top-level schema | 6/8 FAIL | **0/8 FAIL** (gate blind spots revealed in gson, cobra) |
| #16 regression skip guard | 2/8 FAIL | **0/8 FAIL** |
| #30 writeups | 2/8 FAIL | **0/8 FAIL** |
| #38 individual auditor files | 0/8 FAIL | **0/8 FAIL** |
| #39 ### BUG-NNN heading | 3/8 FAIL | **0/8 FAIL** |
| #41 sidecar JSON (actual depth) | N/A | 2/8 non-conformant (gson, express missing) |
| #42 quality_gate.sh gate | N/A benchmark | **8/8 PASS** |
| #43 UC-NN identifiers | 7/8 FAIL | **0/8 FAIL** |
| Fix patches present | 1/8 | **3/8** |
| TDD verified | 1/8 (javalin) | **2/8** (javalin + express) |

---

## Appendix: Quality Gate Log Summary

All 8 quality-gate.log files present. All exit with `RESULT: GATE PASSED`.

| Repo | FAIL | WARN | Result |
|------|------|------|--------|
| virtio | 0 | 1 (no fix patches) | GATE PASSED |
| httpx | 0 | 1 (no fix patches) | GATE PASSED |
| express | 0 | 0 | GATE PASSED |
| javalin | 0 | 0 | GATE PASSED |
| chi | 0 | 1 (no fix patches) | GATE PASSED |
| cobra | 0 | 0 | GATE PASSED |
| gson | 0 | 0 | GATE PASSED |
| serde | 0 | 1 (no fix patches) | GATE PASSED |
