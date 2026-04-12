# Council review: Quality Playbook v1.3.26 benchmark results

**Reviewer:** Cursor  
**Prompt:** `repos/review_prompts/REVIEW_run_results_v1.3.26.md`  
**Evidence:** `repos/*-1.3.26/quality/`, `references/verification.md` (benchmarks 1–43)

---

## Executive summary

v1.3.26’s **script-verified closure** (`quality_gate.sh` → `quality/results/quality-gate.log`) delivers a **clear step-change** on the issues the v1.3.25 councils flagged: **`### BUG-NNN` headings**, **canonical `UC-NN` strings in REQUIREMENTS.md**, **root-level `tdd-results.json` keys**, and **presence of a Terminal Gate section** are now **mechanically enforced** and show **8/8 `RESULT: GATE PASSED`**.

Remaining gaps are **stricter than the current script**: **benchmark 41** still allows **gson** to pass the gate while using **`bug_id` instead of `id`** in `bugs[]`, and **gson `integration-results.json`** omits **`uc_coverage`** and uses a **non-standard `groups` shape** vs `references/verification.md` §14/§41 — the gate checks **key presence**, not **full schema conformance**.

---

## Per-repo scorecard (43 benchmarks)

Scoring uses **PASS / FAIL / N/A**; **1–40** are summarized by **band** (heuristic benchmarks **1–7** = PASS* unless noted). **41–43** are explicit.

| Repo | 1–40 (summary) | 41 Sidecar JSON | 42 quality_gate.sh | 43 UC identifiers |
|------|----------------|-----------------|----------------------|---------------------|
| **virtio** | PASS* (virtio: mechanical **PASS** if `verify.sh` + receipts OK) | **PASS** — root keys + per-bug fields present | **PASS** — log shows 0 FAIL | **PASS** — gate: 19 UC matches |
| **httpx** | PASS* | **PASS** | **PASS** | **PASS** (6 UC) |
| **express** | PASS* | **PASS** | **PASS** | **PASS** (6 UC) |
| **javalin** | PASS* | **PASS** | **PASS** | **PASS** (6 UC) |
| **chi** | PASS* | **PASS** | **PASS** (0 FAIL, 1 WARN patches) | **PASS** (6 UC) |
| **cobra** | PASS* | **PASS** | **PASS** | **PASS** (6 UC) |
| **gson** | **PARTIAL** — integration sidecar shape vs §14 | **FAIL** — `bugs[]` uses **`bug_id`** not **`id`**; **`fix_patch_present` / `requirement` absent** | **PASS** (script did not fail) | **PASS** (6 UC) |
| **serde** | **PARTIAL** — no dedicated `quality/test_functional*` glob (benchmark **8** risk) | **PASS** | **PASS** (1 WARN) | **PASS** (6 UC) |

**Band notes:** **N/A** for **32–33** (no seeds); **virtio** **19–23** mechanical path **PASS** on spot-check; **gson** **benchmark 12** Field Reference Table may be **N/A**-ish for non-schema APIs but **§14 integration JSON** still expects **`uc_coverage`** — **FAIL** vs spec until normalized.

---

## Run totals (filled from disk)

| Metric | v1.3.26 |
|--------|---------|
| **Repos completed** | 8/8 |
| **Total bugs (sum of per-repo BUGS.md claims)** | **19** (4+5+2+2+1+2+2+1) |
| **`quality-gate.log` present** | 8/8 |
| **Gate exit (tail)** | **0 FAIL** on all eight (some **WARN** on 0 fix patches) |
| **`^## BUG-` in BUGS.md** | **0** (all use `### BUG-…`) |
| **`tdd-results.json` root keys** | All eight include `schema_version`, `skill_version`, `date`, `project`, `bugs`, `summary` with `confirmed_open` in `summary` |

**vs v1.3.25 prompt table:** **3/8 wrong headings → 0/8** (**fixed**). **6/8 bad JSON → 7/8 structurally fixed**; **gson** still **non-conformant** on per-bug field **names** (**benchmark 41** strict). **7/8 missing UC → 0/8** at the **“has UC-NN grep”** level (**fixed**).

---

## Question 1 — Did `quality_gate.sh` improve conformance?

**Yes, materially** — for everything the **current script actually checks**: file existence, **`###` bug headings**, **TDD root keys + `schema_version: "1.1"`**, **integration root keys**, **UC substring presence**, **Terminal Gate section**, **mechanical receipts when `mechanical/` exists**, **version stamps**.

**Caveat:** The model **did** run the script — each repo has **`quality/results/quality-gate.log`** ending in **`RESULT: GATE PASSED`**. The script **did not** catch **gson**’s **`bug_id` vs `id`** mismatch because the gate validates **presence of keys**, not **canonical per-bug field names** from §41.

---

## Question 2 — Sidecar JSON schema compliance

| Repo | `schema_version` 1.1 | Required root keys | Per-bug `id`, `requirement`, … |
|------|----------------------|---------------------|--------------------------------|
| virtio, httpx, express, javalin, chi, cobra, serde | ✓ | ✓ | ✓ (spot-checked / Python sweep) |
| **gson** | ✓ | ✓ | ✗ uses **`bug_id`**, omits **`id`**, **`requirement`**, **`fix_patch_present`** |

**Post-write validation (benchmark 41)** is **not fully achieved** until **`quality_gate.sh` (or CI) asserts exact per-bug key set** against a **JSON Schema** or **`jq`** template — not only “`bugs` array exists.”

---

## Question 3 — Use case identifiers (`UC-01` …)

**Recovered vs v1.3.25 narrative.** Every repo’s **`quality-gate.log`** reports **PASS** on canonical UC grep (typical **6–19** matches per repo). **Benchmark 43** is **met** for **machine-readable identifiers** in **REQUIREMENTS.md** in this run.

---

## Question 4 — Bug discovery vs v1.3.25

| Repo | v1.3.25 (prior review) | v1.3.26 (this tree) | Note |
|------|-------------------------|------------------------|------|
| **virtio** | 4 bugs (RING_RESET + MMIO + INTx + …) | **4** bugs — same **themes** (MMIO reset, INTx admin, config IRQ, transport bits) | Ordering/IDs may differ; **same class** |
| **httpx** | 3 (WSGI latin-1) | **5** — redirect **Content-Type**, digest **URI**, **encoding** freeze, etc. | **Different surface** — exploration variance |
| **express** | etag + Content-Type false | **2** — **`app.render` sync throw** + **second bug** in BUGS | **Different** from v1.3.25 row |
| **javalin** | HEAD metadata + CORS | **Same two classes** (BUG-001 / BUG-002 titles align) | **Strong repeatability** |
| **chi** | 6 bugs | **1** bug | **Large drop** — not a script issue; **scope/audit luck** |
| **cobra** | 2 | **2** | Stable count |
| **gson** | 2 | **2** | Stable count |
| **serde** | 1 | **1** | Stable |

**Total:** **19** vs **22** — fewer, not “worse,” given **different express/chi/httpx** findings.

---

## Question 5 — Fix patch generation

**Improved where TDD + patches were already a norm:**

- **express:** `quality/patches/` — **4** files (fix + regression per bug).
- **javalin:** **4** files (fix + regression per bug).
- **gson:** **4** files.
- **cobra:** **2** regression-test patches (no `BUG-*-fix.patch` in listing).

**Still weak:** **virtio** — no `quality/patches/` dir; **httpx** — empty patches dir; **chi** — no patches dir; **serde** — no patches dir. **Gate WARN** on **0 fix patches** appears on **virtio** (and similar) — so the **script surfaces** the gap but does **not block** closure.

---

## Question 6 — V2.0 gate

**Not met** as “same bugs every clean run.” **Javalin** is the best **repeatability** signal; **express / httpx / chi** **diverge** strongly between v1.3.25 and v1.3.26. **Blockers:** (1) **non-deterministic exploration** without **frozen scope** or **deterministic checklist**, (2) **no automated diff** of `BUGS.md` vs a **pinned manifest** per repo.

---

## Question 7 — Regression or progress since v1.3.21?

| Dimension | v1.3.21-ish pain | v1.3.26 |
|-----------|------------------|---------|
| **Use cases** | Broad coverage in some 9-repo story | **UC-NN canonical** — **recovered** in **REQUIREMENTS** |
| **`schema_version`** | Mixed | **8/8** on **`tdd-results.json`** roots |
| **Closure honesty** | Model-only | **Script + log file** — **major progress** |
| **Skill complexity** | High | **Higher** — but **more is now machine-checkable** |

**Net:** **Progress** on **verifiability**; **regression risk** remains where the **gate is shallow** (gson keys) or **tests absent** (serde **quality/** test glob).

---

## Question 8 — Recommended changes for v1.3.27 (prioritized)

| Priority | Change |
|----------|--------|
| **P0** | Extend **`quality_gate.sh`** (or CI) to validate **`tdd-results.json` `bugs[]`** with **`jq`** against required keys **`id`, `requirement`, `red_phase`, `green_phase`, `verdict`, `fix_patch_present`, `writeup_path`** — **reject `bug_id`**. |
| **P0** | Validate **`integration-results.json`** includes **`uc_coverage`** and **`groups[].group`** per §41 — catches **gson**-style flat command lists. |
| **P1** | **WARN → FAIL** (or separate **CI tier**) when **confirmed bugs > 0** and **`quality/patches/BUG-*-fix.patch`** missing — align with v2.0 “fix evidence” goals (optional exemption field). |
| **P1** | **Serde / repos without `quality/` functional tests:** explicit **exemption** in PROGRESS or **require** minimal `test_functional*` — benchmark **8**. |
| **P2** | **Simplify SKILL** presentation: one **“Closure checklist”** page pointing to **`quality_gate.sh`** only — reduce prose duplication. |

**Simplify the skill?** **Simplify the closure path**, not necessarily the **exploration** depth: users run **one script**; the SKILL can **link** to it instead of re-listing 43 benchmarks in prose.

---

## Files cited (representative)

- `repos/*-1.3.26/quality/results/quality-gate.log` — all eight end with **`RESULT: GATE PASSED`**.  
- `repos/gson-1.3.26/quality/results/tdd-results.json` — **`bug_id`** keys.  
- `repos/gson-1.3.26/quality/results/integration-results.json` — no **`uc_coverage`**.  
- `repos/httpx-1.3.26/quality/results/integration-results.json` — includes **`uc_coverage`**.  
- `references/verification.md` — benchmarks **41–43**.
