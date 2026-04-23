# Quality Playbook v1.5.2 — Implementation Plan

*Companion to: `QPB_v1.5.2_Design.md`*
*Status: draft — to be refined once v1.5.1 is merged to main and the v1.5.2 branch is cut*
*Depends on: v1.5.1 shipped (Phase 5 writeup hardening, case-insensitive diff fence gate, 171-test gate suite)*

This plan ships bug-family amplification plus operational polish on top of v1.5.1. The scope is deliberately narrow: prompt-layer changes to Phase 1 and Phase 2, one schema field, one runner behavior fix, a README documentation pass, and a prompt-only runner-reliability improvement. No new iteration strategies, no Council changes, no writeup-gate changes, no code-path restructuring.

The AI-skills work previously numbered v1.5.2 is renumbered to v1.5.3 and lives in `QPB_v1.5.3_Design.md` / `QPB_v1.5.3_Implementation_Plan.md`.

---

## Operating Principles

- **No regression on existing benchmarks.** chi, cobra, virtio, bootstrap must produce bug counts within ±15% of their v1.5.1 baselines. The compensation-grid rule is additive — it surfaces previously-missed bugs, never suppresses existing ones.
- **v1.4.5 RING_RESET family is the canonical validation target.** Any prompt change must be verified by re-running virtio against the current kernel source and recovering the four-bug family.
- **Prompt-layer first, runner-layer second.** Where a prompt-layer fix suffices (incremental candidate-stub writes, explicit-iterations respect via argparse wiring), ship it and park heavier runner changes pending evidence.
- **Benchmark gates every phase.** No phase lands without a fresh virtio run confirming the change behaves as designed.

---

## Phase 0 — v1.5.1 Ship Confirmation

Goal: v1.5.1 merged to main, tagged, pushed; benchmarks from v1.5.1 captured as the regression baseline.

Work items:

- Merge branch `1.5.1` into main (no-ff)
- Tag `v1.5.1`; push tag
- Capture v1.5.1 baselines: virtio-1.5.1 (8 bugs), chi-1.5.1 (9 bugs), cobra-1.5.1 (whatever count), bootstrap-1.5.1 (self-audit clean)
- Document baseline bug counts and overlap notes in `quality/benchmark_history.md` (or equivalent)

Gate to Phase 1: v1.5.1 is the current `main` HEAD; `SKILL.md` reports version 1.5.1; all four baseline bug counts are recorded.

---

## Phase 1 — Schema: `pattern:` tag on requirements

Goal: add an optional `pattern:` field to the requirement spec so Phase 1 can mark whitelist / parity / compensation requirements for Phase 2 grid emission.

Work items:

- `schemas.md`: add `pattern` field to the REQ schema. Valid values: `whitelist`, `parity`, `compensation`, or omitted (default = no grid).
- `.github/skills/quality_gate/quality_gate.py`: extend REQ parsing to read the optional field; gate does not fail if absent; gate does fail if present with an invalid value.
- Add unit tests for the new field (valid values, invalid values, omitted field) — minimum four cases.
- `references/` or `SKILL.md`: document the `pattern:` field with one-paragraph explanation of when each value applies.

**Files touched:** `schemas.md`, `.github/skills/quality_gate/quality_gate.py`, `.github/skills/quality_gate/tests/test_quality_gate.py`, `SKILL.md` (one-paragraph addition).

**Acceptance:** schema doc contains `pattern:` field definition; gate tests pass (175+); requirements with `pattern: whitelist` / `parity` / `compensation` round-trip through the gate; requirements without the field round-trip unchanged.

---

## Phase 2 — Phase 1 cartesian use-case rule

Goal: `phase1_prompt()` emits per-site use cases when a requirement's `References` field names ≥2 files with a shared path-suffix role.

Work items:

- `bin/run_playbook.py::phase1_prompt()`: add a section instructing the reviewer, for each requirement with ≥2 same-suffix references, to also emit one UC per site (UC-N.a, UC-N.b, …) with per-site Actors, Preconditions, Flow, Postconditions.
- Include the REQ-010 / VIRTIO_F_RING_RESET case as the worked example embedded in the prompt (per the Phase 5 hydration pattern established in v1.5.1).
- Add a confirmation checklist to the prompt: "For each requirement I emitted with ≥2 same-suffix references, I also emitted per-site UCs" (per the v1.5.1 hardening pattern).

**Files touched:** `bin/run_playbook.py::phase1_prompt()`. No gate changes (the grid itself is validated at Phase 2).

**Acceptance:** Re-running Phase 1 against `virtio-1.5.2` source produces UC-10a (PCI modern), UC-10b (MMIO), UC-10c (vDPA) for REQ-010 (or whatever the REQ number lands on). Chi and cobra Phase 1 runs produce no new per-site UCs for requirements that don't have symmetric references (regression check: no over-emission).

---

## Phase 3 — Phase 2 mechanical compensation grid

Goal: `phase2_prompt()` produces a compensation grid for any requirement tagged `pattern: whitelist | parity | compensation` and defaults NO cells to BUG.

Work items:

- `bin/run_playbook.py::phase2_prompt()`: add a MANDATORY GRID STEP for pattern-tagged requirements:
  1. Enumerate the authoritative item set (uapi header, spec section, documented constants) — mechanical extraction, not freehand list.
  2. Enumerate the sites from the requirement's per-site UCs.
  3. Produce a grid of (item × site × present?) using code inspection to fill cells.
  4. Apply the BUG-default rule: cells where the item is defined in authoritative source AND absent from shared filter AND absent from site compensation default to BUG. Downgrade to QUESTION requires a per-cell written rationale citing the authoritative source.
  5. Emit one BUG entry per defaulted cell with file:line citation, spec basis, and expected vs actual behavior — the standard BUG format used elsewhere in the playbook.
- Include the RING_RESET grid as the worked example in the prompt (four bits × three transports = 12 cells, six cells BUG by default).
- Add a confirmation checklist to the prompt: "For each `pattern:`-tagged requirement, I produced a grid, applied the BUG-default rule, and wrote one BUG per defaulted cell or a per-cell downgrade rationale."

**Files touched:** `bin/run_playbook.py::phase2_prompt()`. Gate changes: extend `check_code_review` (or equivalent) to fail when a `pattern:`-tagged requirement has no grid or has fewer than (items × sites) cells populated.

**Acceptance:** Re-running Phase 2 only against `virtio-1.5.2` surfaces BUG entries for the RING_RESET family (MMIO RING_RESET, vDPA RING_RESET + ADMIN_VQ, all-transports NOTIF_CONFIG_DATA, vDPA SR_IOV), matching the v1.4.5 BUG-001/002/004/016 findings. Running Phase 2 against chi and cobra produces no spurious BUG-default entries for untagged requirements.

---

## Phase 4 — Respect explicit `--iterations`

Goal: bypass the diminishing-returns early-stop when `--iterations` was provided as an explicit list on the CLI rather than expanded from `--full-run`.

Work items:

- `bin/run_playbook.py` argparse: add an internal marker (e.g., `args._iterations_explicit = True`) set only when `--iterations` appeared in argv directly. `--full-run` expansion sets the marker to `False`.
- Two early-stop sites (`:2241-2244` and `:2306-2309`): guard on the marker. Bypass early-stop when `_iterations_explicit` is `True`.
- New tests in `bin/tests/` covering three fixtures:
  1. Explicit list of 4 strategies, first returns 5 bugs, second returns 0, third returns 2, fourth returns 0. Assert all 4 run.
  2. `--full-run` where the second expanded strategy returns 0 bugs. Assert third and fourth do NOT run.
  3. Explicit list of 1 strategy returning 0 bugs. Assert the strategy completes (regression guard).

**Files touched:** `bin/run_playbook.py`, `bin/tests/test_run_playbook_iterations.py` (new or extended).

**Acceptance:** All existing runner tests pass. New iteration tests pass. `python3 bin/run_playbook.py virtio-1.5.2 --iterations gap,unfiltered,parity,adversarial` runs all four strategies regardless of preceding yields.

---

## Phase 5 — README CLI documentation + rate-limit paragraph

Goal: README fully documents the phase/iteration/full-run interaction and carries the rate-limit warning surfaced by casbin-1.5.1.

Work items:

1. New subsection "Running the playbook: phases, iterations, and macros" after the existing "Run the playbook" step. Content:
   - Phases 1–6 summary (one sentence each), noting that `--phase all` runs them sequentially and `--phase N` or `--phase N,M` runs subsets.
   - Iteration strategies (gap, unfiltered, parity, adversarial) with one-line purpose for each.
   - Three invocation modes:
     - `--phase all`: all six phases, no iterations.
     - `--iterations <list>`: runs named strategies explicitly. Every named strategy completes regardless of yields (honors operator intent).
     - `--full-run`: all phases + all iterations, with early-stop when an iteration returns zero.
   - When to use each: iterative development → `--phase`; full audit → `--full-run`; specific follow-up → `--iterations`.

2. New "Rate limits" paragraph in the existing warnings area:
   - GPT-5.4 Copilot enforces a 54-hour cooldown when a single prompt exceeds ~15M tokens. Observed on casbin-1.5.1 full-run (2026-04-22).
   - Claude Code's plan usage compounds on large repos. A full-run on a Linux kernel driver can consume 5%+ of a Max-plan weekly budget.
   - Recommendations: use `--pace-seconds` for long runs; run iterations as separate prompts via `--iterations <one-strategy>` rather than `--full-run` when rate-limit risk is high; stagger multi-repo runs (2–3 at a time).

**Files touched:** `README.md`.

**Acceptance:** A fresh reader answers "how do I run just adversarial?", "what's the early-stop rule?", and "what rate limits should I plan for?" from the README alone. README CI does not regress; the new sections render cleanly.

---

## Phase 6 — Runner reliability: incremental candidate stubs

Goal: iteration prompts write candidate BUG stubs to disk on identification, not at end-of-review, so mid-prompt termination preserves at minimum the candidate IDs and file:line anchors.

Scope decision: **prompt-only in v1.5.2.** Runner-level checkpointing (heartbeat files, resume tokens) is parked pending evidence the prompt-only approach is insufficient.

Work items:

- `bin/run_playbook.py::iteration_prompt()`: add a MANDATORY INCREMENTAL WRITE STEP:
  - When the agent identifies a candidate bug, immediately append a stub to `quality/code_reviews/<iteration>-candidates.md` with: candidate ID, file:line, one-sentence description, status `candidate`.
  - Details (spec basis, expected/actual, fix) are written after the candidate stub lands, not before.
  - End-of-review consolidation reads the candidates file and promotes stubs to final entries.
- Documentation in the prompt: "The candidates file is your disk ledger. If this session terminates, the file is what survives. Write stubs on identification; fill in details after."

**Files touched:** `bin/run_playbook.py::iteration_prompt()`. No gate changes.

**Acceptance:** A scripted interrupt test — start a chi iteration prompt, kill it after 2 minutes — leaves `quality/code_reviews/<iteration>-candidates.md` on disk with at least one candidate stub (assuming the agent identified at least one candidate before the kill).

---

## Phase 7 — Benchmark re-validation

Goal: confirm v1.5.2 recovers the RING_RESET family without regressing existing benchmark yields.

Work items:

- Fresh `setup_repos.sh virtio chi cobra` → `virtio-1.5.2`, `chi-1.5.2`, `cobra-1.5.2`.
- `python3 bin/run_playbook.py virtio-1.5.2 chi-1.5.2 cobra-1.5.2 --full-run`.
- Diff `virtio-1.5.2/quality/BUGS.md` against `virtio-1.5.1/quality/BUGS.md` (v1.5.1 baseline, 8 bugs) and `benchmark-1.4.5/virtio-1.4.5/quality/BUGS.md` (RING_RESET family reference).
- Diff chi-1.5.2 and cobra-1.5.2 bug counts against their v1.5.1 baselines (regression check).
- Bootstrap self-audit: run v1.5.2 against QPB itself; confirm gate passes.

**Acceptance:**
- virtio-1.5.2 BUGS.md contains the 8 bugs from virtio-1.5.1 (or explicit rationale for any not reproduced) PLUS at least 4 new RING_RESET-family BUGs covering MMIO RING_RESET, vDPA RING_RESET/ADMIN_VQ, NOTIF_CONFIG_DATA, vDPA SR_IOV.
- chi-1.5.2 and cobra-1.5.2 bug counts within ±15% of v1.5.1 baselines.
- Bootstrap self-audit: gate passes, no new regressions from v1.5.2 machinery itself.

---

## Phase 8 — Self-audit bootstrap

Goal: QPB v1.5.2 audits itself one more time with full v1.5.2 machinery; artifacts committed as bootstrap evidence.

Same pattern as v1.5.0 and v1.5.1 Phase 8 (per those plans). Any bugs found go to v1.5.3 backlog.

**Acceptance:** bootstrap self-audit completes; `quality/` artifacts committed; any failures explicitly dispositioned.

---

## Phase 9 — Release

- Bump `version:` in `SKILL.md` to `1.5.2`.
- Update `CHANGELOG.md` with the bug-family amplification summary, operational polish items, and benchmark recovery evidence (virtio RING_RESET family).
- Update `README.md` "What's new in v1.5.2" section (mirror CHANGELOG bullets).
- Update `ai_context/DEVELOPMENT_CONTEXT.md` with a v1.5.2 bullet; update the known-issues section to remove the RING_RESET family entry (now recovered).
- Update `ai_context/TOOLKIT.md` writeup-quality section if any new gate behavior was added in Phase 1 (pattern-tag gate check).
- Tag `v1.5.2`; merge `1.5.2` → `main`; push tag.
- Council-of-Three review: **required** for this release. The two substantive design changes (Levers 1 and 2) are behavioral and deserve a three-model review (gpt-5.4, gpt-5.3-codex, claude-sonnet-4.6) before Phase 7 benchmark re-validation locks in.

---

## Parking Lot (deferred from v1.5.2)

- **Runner-level checkpointing.** Heartbeat files, explicit resume tokens, structured kill-resume protocol. Ships if Phase 6's prompt-only incremental-write proves insufficient.
- **Auto-inference of `pattern:` tag.** Let Phase 1 detect whitelist/parity/compensation patterns from code structure rather than requiring reviewer tagging. Refinement for v1.5.3+.
- **Cross-requirement grid consolidation.** When two requirements share a site set (e.g., feature-bit requirements across transports), produce a consolidated grid rather than separate per-requirement grids. Refinement for v1.5.3+.
- **AI-skills project-type classification and four-pass derivation.** Renumbered to v1.5.3.

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Cartesian UC rule over-emits per-site UCs on requirements that aren't actually symmetric | Medium | Path-suffix heuristic is conservative; reviewer can drop the match by removing references or editing the rule's applicability. Phase 7 regression check on chi/cobra catches over-emission. |
| Compensation grid produces cells the reviewer cannot confidently classify | Medium | BUG-default plus per-cell downgrade rationale means reviewer errs toward BUG; Council-of-Three review catches false positives; Phase 7 spot-check validates bug realism. |
| `pattern:` tag adoption is low in practice; grid rule rarely fires | Medium | SKILL.md and Phase 1 prompt explicitly list `pattern:` values with worked examples; bootstrap self-audit forces at least one use. |
| Incremental candidate-stub writes slow down iteration prompts significantly | Low | Writes are append-only, one stub per candidate (typically <20 per iteration). Negligible overhead. |
| Phase 7 yield check misfires (regression appears due to benchmark variance, not v1.5.2 changes) | Medium | Run each benchmark 3× and use median; ±15% threshold is deliberately wide to absorb natural variance. |
| README rate-limit paragraph becomes stale as provider limits change | Low | Document observed behavior with dates; treat as snapshot, not contract. |

---

## Open Questions to Resolve

1. **Does the `pattern:` field live in the REQ record itself, or in a separate `patterns_manifest.json`?** Lean: REQ record — keeps the grid rule co-located with the requirement that triggers it.

2. **How strict is the path-suffix match in Lever 1?** Candidate rules: exact last-segment match, last-segment-regex match, or explicit reviewer-provided grouping. Lean: exact match on a regex supplied by the prompt (e.g., `.*_finalize_features\.c$`), with reviewer override.

3. **Should the grid emit explicit "not applicable" cells?** Example: VIRTIO_F_SR_IOV is only meaningful for PCI-based transports; calling it absent in "USB-style virtio" would be noise. Lean: yes — N/A is a third cell value beside YES/NO, and the BUG-default rule applies only to NO cells with a present-in-authoritative-source item.

4. **How many authoritative sources does the grid need before a cell can be BUG-defaulted?** One (the uapi header) is the minimum. For requirements spanning multiple headers or specs, does every source need to agree? Lean: one authoritative source suffices per cell; conflicts between sources default to QUESTION with explicit reconciliation rationale.

5. **What's the minimum evidence for a per-cell QUESTION downgrade?** Lean: one-paragraph rationale citing the authoritative source and explaining why the site intentionally does not support the item. A three-word dismissal ("not supported here") is insufficient.
