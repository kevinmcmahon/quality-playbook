# Quality Playbook v1.5.2 — Design Document

*Status: revised 2026-04-23 after Council-of-Three review*
*Authored: April 2026*
*Owner: Andrew Stellman*
*Depends on: `QPB_v1.5.0_Design.md` (schemas, citation schema), `QPB_v1.5.1_Design.md` (Phase 5 writeup hardening)*
*Supersedes earlier v1.5.2 scope (AI skills) which is renumbered to v1.5.3.*

> **Scope-revision note (2026-04-23).** The original draft targeted two levers at `phase1_prompt()` and `phase2_prompt()`. Council-of-Three review (9 reviews across 3 sessions — see `AI-Driven Development/Quality Playbook/Reviews/QPB_v1.5.2_Council_Synthesis.md`) combined with a code audit of the actual pipeline surfaced two structural problems: (1) the "Phase 2" classification behavior the design wanted to modify actually happens in `phase3_prompt()` (Phase 2 generates artifacts; Phase 3 classifies), and (2) even in the v1.4.5 successful run, cell identity was lost between the compensation table and BUGS.md (6 cells → 3 BUG entries). This revision corrects Lever 2 to target Phase 3, adds a third lever for cell-identity preservation spanning Phases 3 and 5, and replaces the free-text downgrade rationale with a structured schema. The motivation, evidence, and operational polish items stand.

---

## Motivation

### The goal: close a specific miss-mode the v1.5.1 virtio run exposed

v1.4.5 found the RING_RESET bug family on virtio — four bugs tracing to one omission in `vring_transport_features()` at `drivers/virtio/virtio_ring.c:3505-3533`. The `VIRTIO_F_RING_RESET`, `VIRTIO_F_NOTIF_CONFIG_DATA`, `VIRTIO_F_ADMIN_VQ`, and `VIRTIO_F_SR_IOV` feature bits are defined in the uapi header and handled for PCI modern transport at `virtio_pci_modern.c:367-381`, but missing from both the shared feature filter (MMIO path) and the vDPA feature filter. Four bugs, one symmetrical pattern.

v1.5.1 re-ran virtio and **recognized the pattern** — then filed it as a single `QUESTION-001` ("architectural asymmetry worth investigating") instead of four BUG entries. The playbook didn't fail to see the asymmetry; it failed to decompose it. One umbrella verdict ate N bugs.

This isn't a recall regression (the playbook already sees the whitelist). It's a classification regression: when the playbook encounters a whitelist-pattern gap, the current prompts nudge it toward architectural-question framing, and there's no mechanical rule forcing decomposition into per-cell bug entries. The regression happens in Phase 3 (code review), which is where BUGS.md entries are written and where `QUESTION-001` was recorded.

### Why bug-family amplification matters beyond virtio

RING_RESET is the concrete instance; the pattern generalizes. Any codebase with a filter-and-compensate architecture — cobra's command registry, chi's middleware map, kernel feature flags broadly, config-key dispatch tables, plugin hooks — has the same shape: an authoritative set on one side, a per-site compensation on the other, and gaps that are objective bugs rather than subjective "architectural questions." If the playbook collapses each such pattern into one verdict, it systematically undercounts on a specific and common structural shape. The existing gate covers leaf-level bugs well; this is where the playbook misses at scale.

### Why three levers and not two

The miss-mode has three separable failure points. The original design identified two; Council review and a pipeline audit surfaced a third.

First, the requirements model doesn't distinguish "this requirement touches one site" from "this requirement touches N symmetric sites" — so Phase 3 has nothing to verify site-by-site against. **Lever 1 (cartesian UC rule at Phase 1)** fixes that: when a requirement references ≥2 sites with symmetric roles, `phase1_prompt()` emits per-site UCs so downstream phases have structural anchors.

Second, Phase 3's current prompt defaults ambiguity toward QUESTION and provides no mechanical-grid obligation for symmetric requirements. That default is correct for single-site bugs where the reviewer legitimately doesn't know. It's wrong for multi-site pattern gaps where the authoritative source is right there in the uapi header. **Lever 2 (mechanical compensation grid + BUG-default at Phase 3)** inverts the default for exactly this case. If an item is in the authoritative source and absent from both the shared filter and the site's compensation hook, the cell's default verdict is BUG, and downgrading to QUESTION requires structured rationale (not free text). The "authoritative source + compensation hook" framing is narrow enough that it doesn't fire on arbitrary ambiguity elsewhere.

Third — and this is the lever the original draft missed — even in the v1.4.5 successful run, the compensation table had 6 BUG cells but BUGS.md had only 3 entries (two cells combined into BUG-002 because they shared NOTIF_CONFIG_DATA; two combined into BUG-004 because they lived in the same vDPA function). That's a 50% cell→BUG compression, editorially reasonable but unacknowledged. Without cell-identity preservation, any release criterion that counts BUG entries instead of covered cells underreports the true cardinality. **Lever 3 (cell-identity preservation across Phases 3 and 5)** gives each grid cell a stable ID, requires BUGS.md entries to carry a `Covers:` field listing the cell IDs they address, and adds a Phase 5 reconciliation check that every live cell has either a BUG covering it or an audit-trail downgrade.

None of the three alone suffices. Lever 1 without Lever 2 produces better-structured QUESTIONs that still get collapsed. Lever 2 without Lever 1 has no grid to fill. Levers 1+2 without Lever 3 can still compress cells into BUG entries without a trail, defeating the acceptance-test discipline. Together the three turn the miss-mode from "one QUESTION eating four BUGs" into "every cell accounted for — either by a BUG with a named cell cover, or by a structured downgrade that survives audit."

### The measurable outcome

The acceptance test isn't "did benchmark counts go up" — that would invite gaming. It's specifically: *does Phase 7's virtio-1.5.2 run produce grid-cell coverage for the four RING_RESET-family cells that v1.4.5 found and v1.5.1 lost, without inflating chi/cobra bug counts outside ±15%?* "Coverage" means every cell has a cell-ID present in a BUGS.md `Covers:` field or a structured downgrade record. If yes, the levers addressed the specific miss-mode without introducing a false-positive tax. If the virtio run leaves any RING_RESET-family cell uncovered, or chi/cobra go over the regression band, the design needs tuning before ship.

### The operational polish items are adjacent, not core

`--iterations` respect, README CLI docs, incremental candidate-stub writes — these all surfaced during the v1.5.1 casbin/virtio runs as distinct friction. They pay rent in the same release because they're small, they're independent of the levers, and shipping them separately would be wasted ceremony. But they're not the reason v1.5.2 exists. The reason is closing the undercounted-pattern miss-mode.

### What v1.5.2 is not

Not a recall push (playbook already sees whitelist patterns). Not a re-architecture of the Council protocol. Not touching the writeup gate. Not the AI-skills work (that's v1.5.3). Not trying to catch pattern categories outside whitelist/parity/compensation — if Phase 7 shows the mechanism works, we can extend the tag taxonomy in later releases. Narrow, measurable, anchored to one known failure.

---

## Purpose of This Document

v1.5.2 addresses a specific recurring failure mode in the playbook: families of bugs that share a common architectural root cause disappear from `BUGS.md` because a single judgment call at the requirement or review layer collapses N mechanical findings into one narrative verdict — often a QUESTION rather than a BUG — and even when cells are correctly classified, cell-to-BUG consolidation erodes cardinality without a trail.

The v1.4.5 virtio run caught a four-bug family around the VIRTIO feature-bit whitelist. The v1.4.6 and v1.5.1 runs identified the exact same architectural asymmetry in Phase 3 (code review), worded it almost identically, and then classified it as `QUESTION-001` rather than escalating four distinct bugs. The root cause is not exploration coverage (the code was read), not triage calibration (the finding was considered), not iteration gaps (the baseline had it). The root cause is that Phase 1 produces one umbrella use case for a symmetric problem, Phase 3 produces one prose verdict for that umbrella, Phase 5 reconciliation has no identity trail to check against, and the BUGS.md pipeline populates from BUG verdicts — not QUESTION verdicts or umbrella findings.

v1.5.2 fixes this with three surgical prompt-layer levers and a small set of operational polish items. A companion file `QPB_v1.5.2_Implementation_Plan.md` covers execution (needs a refresh to reflect this revision).

---

## The Gap — Evidence

### v1.4.5 run: four bugs from one mechanical table — but only three BUG entries on disk

The v1.4.5 virtio benchmark produced 17 bugs in the baseline (the highest single-version yield on record for virtio). Four of those bugs — BUG-001, BUG-002, BUG-004, and BUG-016 — share a root cause: the shared `vring_transport_features()` whitelist in `drivers/virtio/virtio_ring.c:3505-3533` default-clears every feature bit not in its closed set; transports with their own `finalize_features` hook (PCI modern, MMIO, vDPA) must compensate for bits they actually support. PCI modern's `vp_transport_features()` at `virtio_pci_modern.c:367-381` does this work. MMIO's `vm_finalize_features()` at `virtio_mmio.c:109-131` does not. vDPA's `virtio_vdpa_finalize_features()` at `virtio_vdpa.c:389-396` does not.

The v1.4.5 Phase 3 reviewer caught this by constructing a mechanical compensation table in `code_reviews/2026-04-18-reviewer.md`:

```
| Feature bit              | PCI modern | MMIO | vDPA |
| VIRTIO_F_RING_RESET      | YES        | NO   | NO   |
| VIRTIO_F_NOTIF_CONFIG_DATA | NO       | NO   | NO   |
| VIRTIO_F_ADMIN_VQ        | YES        | YES  | NO   |
| VIRTIO_F_SR_IOV          | YES        | YES  | NO   |
```

The table contains six `NO` cells. Each `NO` is an authoritative-bit-missing-compensation case. Every cell was escalated — but on disk the BUGS.md ledger has only BUG-001 (RING_RESET/MMIO), BUG-002 (NOTIF_CONFIG_DATA/all-transports, a single BUG for three cells), and BUG-004 (RING_RESET/vDPA + ADMIN_VQ/vDPA, a single BUG for two cells). Six cells, three BUG entries. The consolidation was editorially reasonable — NOTIF_CONFIG_DATA cells share a single fix path; the two vDPA cells share a single function to patch — but the BUGS.md entries carry no `Covers:` field and no cell-to-BUG audit trail. If the success criterion counts BUG entries, v1.4.5 scored 3. If it counts covered cells, v1.4.5 scored 6. Today the playbook has no way to tell them apart.

### v1.5.1 run: same finding, different verdict

The v1.5.1 virtio benchmark correctly identified the same architectural asymmetry. `virtio-1.5.1/quality/code_reviews/2026-04-22-review.md` (a Phase 3 artifact) contains REQ-010 ("Do not silently drop supported transport feature bits"), status `PARTIALLY SATISFIED`, analysis: "Modern PCI compensates after the shared whitelist; MMIO/vDPA do not."

The verdict table row:

```
| Pass 1 / REQ-010 | QUESTION-001 — MMIO/vDPA transport-feature restoration gap | MEDIUM | QUESTION | N/A |
```

`QUESTION-001` is a question, not a bug. The BUGS.md hydration step reads BUG entries, not QUESTION entries. Four real kernel bugs disappeared from the ledger despite being identified structurally correctly, one review layer up. Same code, same reviewer quality, identical architectural reasoning — but a single prose verdict replaced a per-cell mechanical grid, and the escalation machinery had nothing to latch onto.

This is a systemic miss, not a one-off. The v1.4.6 run had the same downgrade pattern. Any symmetric pattern (`whitelist`, `parity`, `compensation`) where Phase 1 produces one umbrella requirement and Phase 3 produces one umbrella verdict will collapse the same way.

---

## Root Cause — Why One Verdict Eats N Bugs

Three structural issues combine to produce the miss:

**1. Phase 1 emits one use case per requirement, not one per implementation site.** REQ-010 references three finalize hooks (`virtio_pci_modern.c`, `virtio_mmio.c`, `virtio_vdpa.c`). The requirement is scoped at the architectural level — "supported transport feature bits preserved." Phase 3 receives a single UC and produces a single verdict. A Phase 3 reviewer asked "does MMIO comply with REQ-010?" has to produce a per-site judgment; a reviewer asked "are feature bits preserved across transports?" can and does hedge with "partially — PCI modern compensates; MMIO/vDPA do not," which reads as ambiguous and invites a QUESTION classification.

**2. Phase 3 has no mechanical-grid obligation for symmetric requirements.** The v1.4.5 reviewer produced the compensation table on initiative. Nothing in `phase3_prompt()` requires it. When the v1.5.1 reviewer encountered the same requirement, they wrote the architectural finding as prose without enumerating cells. Missing cells had no place to go — the BUG-vs-QUESTION decision was made once for the umbrella rather than per cell. The batch-context structure of `phase3_prompt()` (a single monolithic LLM call running a 3-pass review across all requirements) means the LLM sees the whole cluster in shared context; without a prompt-level discipline forcing per-cell decomposition, the LLM's natural tendency is to synthesize one narrative verdict.

**3. Even when the grid is constructed, cells collapse into BUG entries without a trail.** v1.4.5 demonstrates this: 6 cells → 3 BUG entries, justified by shared fix paths but not recorded anywhere in a form the pipeline can audit. Phase 5 reconciliation has no way to verify every cell was addressed, so silent under-coverage is indistinguishable from explicit consolidation.

All three failure modes are at the prompt layer plus a small schema addition. All are fixable without changing iteration strategies, without Council changes, without schema additions that ripple through the rest of the stack.

---

## Design — Three Levers

### Lever 1: Phase 1 cartesian use-case rule

**Rule.** When Phase 1 emits a requirement whose `References` field names ≥2 files that share a path-suffix role (e.g., `virtio_mmio.c`, `virtio_vdpa.c`, `virtio_pci_modern.c` all containing `_finalize_features`) AND each reference points to a function-level line range of similar size, `phase1_prompt()` also emits one use case per site. The parent REQ-N stays as the umbrella; UC-N.a, UC-N.b, UC-N.c (etc.) are the per-site use cases, each with its own Actors, Preconditions, Flow, and Postconditions.

**Cartesian eligibility check.** The Council identified a false-positive risk: a reviewer might populate `References` with lexically-similar but semantically-unrelated sites (e.g., `CONFIG_*` kconfig flags, error-code enums, unrelated plugin hooks). To avoid that, expansion fires only when both conditions hold:

- **Path-suffix match**: at least two references share a path-suffix role (last segment before extension, or matching function-name pattern across files).
- **Function-level similarity**: each matching reference cites a line range of similar size (within 2× of the median) and each range is inside a function body — not a file-header or a kconfig block.

If only the first holds, Phase 1 keeps the umbrella UC and marks the cluster `heterogeneous` in a comment. Phase 3 reviewer judgment can still override by explicit UC emission. Auto-detection precision is tunable; missing a symmetric set is safer than generating false per-site UCs.

**Worked example.** REQ-010 has `References: virtio_pci_modern.c:367-381, virtio_mmio.c:109-131, virtio_vdpa.c:389-396`. All three hooks match the `*_finalize_features` pattern; each range is 14-22 lines inside a function body. Eligibility holds. Phase 1 emits:

- UC-10a: PCI modern feature preservation (actor: PCI modern transport; precondition: whitelist cleared RING_RESET / SR_IOV / ADMIN_VQ; flow: vp_transport_features restores them; postcondition: all three bits present in final features).
- UC-10b: MMIO feature preservation (same structure; postcondition tests against vm_finalize_features).
- UC-10c: vDPA feature preservation (same structure; postcondition tests against virtio_vdpa_finalize_features).

Phase 3 now sees three concrete per-transport use cases plus the umbrella requirement, rather than one generic requirement.

### Lever 2: Phase 3 mechanical compensation grid with BUG-default

**Rule.** For any requirement tagged with a `pattern:` value from the set `{whitelist, parity, compensation}`, `phase3_prompt()` requires the reviewer to produce a compensation grid of (item × site × present?) before writing any BUG or QUESTION entries for that requirement, and applies this classification rule verbatim:

> If an item is defined in the authoritative source (uapi header, spec section, or equivalent) AND is absent from the shared filter/whitelist AND is absent from the site's compensation hook, the default verdict for that cell is **BUG**. Downgrade to QUESTION requires a structured per-cell record (see below). Downgrades without all required fields are rejected; the cell stays BUG.

**BUG-default, not QUESTION-default.** This is the central inversion. v1.5.1 defaulted missing cells to QUESTION and required evidence to upgrade to BUG. v1.5.2 defaults missing cells to BUG and requires structured rationale to downgrade to QUESTION. Four real kernel bugs disappear under the old default; they surface automatically under the new one. Review thoroughness is unchanged — only the direction of the default flips.

**BUG-default is narrow by construction.** The trigger requires `pattern: {whitelist, parity, compensation}` to be set on the requirement by Phase 1. Requirements without a `pattern:` tag — which is most of them — stay on QUESTION-default. This addresses the Council's "flood of BUGs on external code" concern: BUG-default only fires inside requirements the reviewer has explicitly tagged as symmetric, and the cartesian-eligibility check in Lever 1 defends against the tag being applied to heterogeneous clusters.

**Structured downgrade rationale.** Free-text rationale is unenforceable; all 9 Council reviewers flagged this independently. Every downgrade-to-QUESTION record is a JSON object with required fields:

```json
{
  "cell_id": "REQ-010/cell-RING_RESET-MMIO",
  "authority_ref": "include/uapi/linux/virtio_config.h:116",
  "site_citation": "drivers/virtio/virtio_mmio.c:109-131",
  "reason_class": "intentionally-partial",
  "falsifiable_claim": "MMIO does not support RING_RESET because <specific cited rationale> — falsifiable by showing MMIO re-sets bit 40 under condition X"
}
```

`reason_class` is drawn from a closed enum: `out-of-scope | deprecated | platform-gated | handled-upstream | intentionally-partial`. Missing any field, or a `reason_class` outside the enum, or a `falsifiable_claim` of zero length → cell reverts to BUG with no re-prompt loop. This replaces the earlier "written per-cell exception" text, which was flagged as unenforceable by every reviewer in the Council.

**Worked example.** REQ-010 with `pattern: whitelist` produces:

```
| Missing bit                | PCI modern  | MMIO        | vDPA        |
| VIRTIO_F_SR_IOV (37)       | YES :372    | NO — BUG    | NO — BUG    |
| VIRTIO_F_NOTIF_CONFIG_DATA | NO — BUG    | NO — BUG    | NO — BUG    |
| VIRTIO_F_RING_RESET (40)   | YES :376    | NO — BUG    | NO — BUG    |
| VIRTIO_F_ADMIN_VQ (41)     | YES :379    | NO — BUG    | NO — BUG    |
```

Eight cells BUG by default. The reviewer can downgrade any cell to QUESTION with a structured record, but each downgrade stands on its own evidentiary basis — the whole family can no longer collapse into one umbrella QUESTION.

### Lever 3: Cell-identity preservation across Phase 3 and Phase 5

The Council's unanimous finding was that identity loss *after* classification is the biggest unaddressed risk. The v1.4.5 data confirms it: 6 grid cells → 3 BUG entries with no audit trail. Lever 3 installs that trail.

**Cell IDs.** Every grid cell gets a deterministic identifier from its coordinates:

```
REQ-N/cell-<item>-<site>
```

For REQ-010's grid: `REQ-010/cell-RING_RESET-MMIO`, `REQ-010/cell-RING_RESET-vDPA`, `REQ-010/cell-ADMIN_VQ-vDPA`, etc. The ID is derived mechanically from the `item` and `site` columns; the reviewer does not invent it.

**BUGS.md `Covers:` field.** Every BUG entry written from a compensation grid includes a `Covers:` field listing the cell IDs it addresses. Consolidation is permitted — a BUG can cover multiple cells when they share a fix path — but the covered cells must be named. Example:

```
### BUG-004
**Title:** VIRTIO_F_RING_RESET and VIRTIO_F_ADMIN_VQ silently cleared in vDPA transport
**Severity:** HIGH
**Status:** Open
**Requirements:** REQ-010
**Covers:** REQ-010/cell-RING_RESET-vDPA, REQ-010/cell-ADMIN_VQ-vDPA
**Consolidation rationale:** Both bits missing in the same function (virtio_vdpa_finalize_features); a single compensation block restores both.
```

When multiple cells are consolidated into one BUG, a `Consolidation rationale:` field is required. The rationale is free-text but its presence is mechanically checked; empty or missing rationale fails the Phase 5 reconciliation gate.

**Phase 5 cardinality reconciliation.** `phase5_prompt()` gains an obligation: for every requirement with a `pattern:` tag, enumerate the cells from Phase 3's grid, walk every BUGS.md entry that references that requirement, build the union of `Covers:` cell IDs, and compare to the cell set from the grid. Any cell not covered by a BUG and not downgraded via a structured rationale record fails the gate — the run aborts with a cell-coverage report.

This is the Council's "cardinality conservation gate" made concrete. It doesn't forbid consolidation; it forbids *invisible* consolidation. A reviewer can legitimately collapse 6 cells into 3 BUGs (v1.4.5's pattern) — but only by naming which cells each BUG covers.

### Out of scope for these levers

No changes to iteration strategies. No changes to Council. No changes to the Tier taxonomy. No changes to the writeup hydration gate (v1.5.1's work stands). This is a prompt-layer change to Phase 1, Phase 3, and Phase 5, with a single schema addition for the `pattern:` field on requirements and a structured-record format for downgrade rationales.

---

## Design — Operational Polish

Three smaller items ship alongside the bug-family work. Each stands on its own evidence.

### Respect explicit --iterations

**Observed failure.** `bin/run_playbook.py:2241-2244` and `:2306-2309` apply a diminishing-returns early-stop rule when an iteration strategy returns zero new bugs. The rule is correct for the `--full-run` macro (which is semantically "run until returns diminish") but surprising when the operator named strategies explicitly: `--iterations gap,unfiltered,parity,adversarial` can stop after parity returns +0, silently skipping adversarial despite the operator asking for it.

**Rule.** Early-stop applies only when `--iterations` was expanded from `--full-run`. When the operator names strategies as an explicit list, every named strategy runs to completion regardless of preceding results. Operator intent wins over the macro heuristic.

**Implementation scope.** argparse wiring distinguishes explicit-list from full-run-expanded. Two early-stop sites guard on the flag. No other runner changes.

### README CLI documentation

**Observed gap.** The current README explains how to run the playbook but does not document the interaction between `--phase`, `--iterations`, `--full-run`, and `--next-iteration`. A user running `--full-run` on a large repo overnight and hitting a 54-hour rate-limit has no warning in the README that this is a possibility. The documentation exists in CLAUDE.md and in ai_context, but not in the README.

**Content to add.**

1. New subsection "Running the playbook: phases, iterations, and macros" after the existing "Run the playbook" step, explaining the six phases, the four iteration strategies, and the three top-level invocation modes (`--phase all`, `--iterations <list>`, `--full-run`).
2. New "Rate limits" paragraph in the warnings area, documenting the GPT-5.4 Copilot 54-hour cooldown observed on a 15M-token single prompt during the casbin 1.5.1 run, with recommendations to stagger iterations and use `--pace-seconds`.

### Runner reliability for long iteration prompts

**Observed failure.** During the chi-1.5.1 adversarial iteration, the Copilot prompt consumed ~5 minutes 17 seconds and ~1.6M tokens before terminating. The agent had identified BUG-010 and BUG-011 candidates in its internal plan, but the session terminated between the "plan" and "write" phases with `Changes +0 -0` on disk. Two real findings lost.

**Design direction.** Incremental write during iteration prompts. After the agent identifies a candidate bug, it writes a stub entry to `quality/code_reviews/<iteration>.md` immediately with at minimum a candidate ID and file:line anchor. Full details are filled in subsequently. If the session terminates mid-prompt, at least the candidate IDs survive to disk.

**Scope decision.** v1.5.2 ships this as a **prompt-only** change — add a "write candidate stubs on identification, not at end-of-review" instruction to `iteration_prompt()`. Runner-level checkpointing (heartbeat files, explicit resume tokens) is parked for v1.5.3 pending evidence that the prompt-only fix is insufficient.

---

## Success Criteria

v1.5.2 is successful if:

1. **RING_RESET family recovers on virtio, measured at the cell level.** A fresh `virtio-1.5.2` benchmark run produces a compensation grid for REQ-010 (or its v1.5.2 equivalent) containing cells for VIRTIO_F_RING_RESET (MMIO), VIRTIO_F_RING_RESET (vDPA), VIRTIO_F_NOTIF_CONFIG_DATA (all transports), VIRTIO_F_ADMIN_VQ (vDPA), and VIRTIO_F_SR_IOV (vDPA), and every such cell appears in a BUGS.md `Covers:` field or a structured downgrade record. Target: cell coverage ≥ v1.4.5's 6 cells, regardless of how many BUG entries the cells consolidate into. BUG-entry count is secondary.

2. **Phase 5 cardinality gate fires on a hand-crafted regression.** A synthetic test where Phase 3 writes a BUGS.md entry missing one cell from its `Covers:` list aborts the run with a cell-coverage report. Verified by scripted test.

3. **No yield regression on other benchmarks.** chi-1.5.2, cobra-1.5.2, and bootstrap produce bug counts within ±15% of their v1.5.1 baselines. The compensation-grid rule is purely additive — it surfaces previously-missed bugs without suppressing existing ones. Because Lever 2 fires only on `pattern:`-tagged requirements, unrelated codebases should see no effect.

4. **Explicit --iterations is honored.** `python3 bin/run_playbook.py virtio-1.5.2 --iterations gap,unfiltered,parity,adversarial` runs all four strategies even when one returns +0. `python3 bin/run_playbook.py virtio-1.5.2 --full-run` preserves early-stop behavior.

5. **README documents CLI semantics.** A fresh reader can answer "how do I run just adversarial?", "what happens on `--full-run` overnight?", and "what's the rate-limit risk?" from the README alone.

6. **Candidate-stub writes survive interruption.** A forced kill of an iteration prompt mid-run leaves at least the candidate IDs and file:line anchors of bugs identified before the kill point on disk in `quality/code_reviews/`. Verified by scripted interrupt test.

7. **Self-audit passes cleanly on v1.5.2.** QPB's bootstrap self-audit with v1.5.2 machinery passes the gate with no new regressions and surfaces any real v1.5.2-introduced prose/code drift for triage.

---

## Out of Scope for v1.5.2

- **AI-skill project handling** (project-type classification, skill-specific four-pass derivation, Haiku-parity requirements). Renumbered to v1.5.3 in a separate scope doc.
- **Runner-level checkpointing** (heartbeat files, resume tokens, structured kill-resume protocol). Parked for v1.5.3 or later pending evidence that the prompt-only incremental-write fix is insufficient.
- **New iteration strategies.** The four existing strategies (gap, unfiltered, parity, adversarial) stand. Bug-family amplification operates at Phase 1, Phase 3, and Phase 5 regardless of which iteration is running.
- **Changes to the writeup hydration gate.** v1.5.1's five-sentinel and empty-diff-fence checks stand unchanged.
- **`pattern:` tag auto-inference from code structure.** v1.5.2 requires `pattern:` to be populated by the Phase 1 reviewer (with guidance from the prompt). Auto-inference from references structure is a possible future refinement but not required for recovery of the RING_RESET family.
- **Retroactive cell-identity coverage on past releases.** Lever 3 applies to v1.5.2 and later runs. Prior benchmark data stays as-is; the 6-cells/3-BUGs ambiguity in v1.4.5 is a known historical artifact.

---

## Open Questions

These don't block v1.5.2 design but need answers during implementation:

1. **Does every requirement need a `pattern:` tag, or only a subset?** Lean: optional field, populated when the architecture implies a pattern (whitelist / parity / compensation / none). Default is none, which means no grid is produced. The grid is opt-in via the tag.

2. **How does Phase 1's cartesian rule detect "symmetric sites" automatically?** Lean: path-suffix match on the `References` field plus function-level similarity check is the v1.5.2 implementation. If Phase 1 judgment disagrees, the reviewer can override by explicit UC emission or by dropping the suffix match. Auto-detection precision is tunable; missing a symmetric set is safer than generating false per-site UCs.

3. **How does the cartesian rule interact with existing REQ numbering?** Lean: REQ-N stays as the umbrella, UC-N.a/b/c are sub-use-cases. `use_cases_manifest.json` already supports free-form IDs. No schema change for numbering.

4. **What counts as "authoritative source" for the BUG-default rule in Lever 2?** Lean: uapi headers, explicit spec text (RFC sections, API reference docs), or documented constants with a definition citation. Speculative lists assembled by the reviewer do not qualify. The compensation grid's authority floor is the same as the playbook's existing Tier-1/Tier-2 citation discipline.

5. **Where do structured downgrade records live on disk?** Lean: a per-run file at `quality/compensation_grid_downgrades.json` that Phase 3 appends to and Phase 5 reads. Alternatives — inline in the BUGS.md ledger, or as per-requirement subdirectories — add more schema churn than the tightly-scoped release wants.

6. **Should the cell-identity check be enforced in Phase 3 or only Phase 5?** Lean: Phase 5 is authoritative (the reconciliation gate), but Phase 3's prompt should self-check before emitting artifacts so the failure is discovered early. Two checks, not one — the Phase 3 self-check is advisory, the Phase 5 gate is blocking.

7. **Should the runner reliability fix write stubs for ALL candidates, or only confirmed ones?** Lean: all candidates with file:line anchors, marked `status: candidate`. Filtering to confirmed-only defeats the survival purpose — the whole point is to preserve intent before confirmation machinery runs.

---

## Council Review Outcomes (2026-04-23)

A Council-of-Three review was run on the original v1.5.2 design, using three `gh copilot` sessions (gpt-5.4, gpt-5.3-codex, claude-sonnet-4.6) each of which spawned three internal reviewers. The 9 independent reviews are in `AI-Driven Development/Quality Playbook/Reviews/v1.5.2_responses/`; a synthesis is in `QPB_v1.5.2_Council_Synthesis.md`. This revision folds in the council's findings plus a subsequent pipeline code audit that corrected phase-numbering in the original design.

**Unanimous findings the redesign addresses:**

- *Lexical-only cartesian expansion is insufficient.* Lever 1 now gates expansion on path-suffix match PLUS function-level line-range similarity (the "Cartesian eligibility check").
- *Free-text downgrade rationale is unenforceable.* Lever 2 now requires a structured JSON record with `authority_ref`, `site_citation`, `reason_class` (closed enum), and `falsifiable_claim`. Missing fields revert the cell to BUG without a re-prompt loop.
- *Identity loss after classification is the biggest unaddressed risk.* Lever 3 (new) introduces deterministic cell IDs, a `Covers:` field on BUGS.md entries, a `Consolidation rationale:` field when multiple cells merge, and a Phase 5 cardinality gate that aborts the run if any cell is neither covered nor downgraded.

**Pipeline-audit findings the redesign corrects:**

- *Lever 2 targets the wrong phase.* The original design said `phase2_prompt()` produces the compensation grid, but Phase 2 in the actual pipeline generates quality artifacts (REQUIREMENTS.md, CONTRACTS.md, etc.) — classification happens in `phase3_prompt()`. All Lever 2 prose now correctly targets Phase 3.
- *The v1.4.5 "success" baseline had cell→BUG consolidation the original acceptance test didn't notice.* 6 grid cells → 3 BUG entries, editorially reasonable but unrecorded. Success criterion 1 now counts covered cells, not raw BUG entries, so the acceptance test matches the actual failure mode.

**Council findings the redesign does *not* adopt, with rationale:**

- *"Ship with modifications" vs. "don't ship" split (7 vs 2):* The 2 don't-ship verdicts came from reviewers whose identity matched the orchestrating model, suggesting self-doubt bias rather than independent signal. The three structural changes above address the substantive concerns both dissenters raised, so the release proceeds.
- *Phase 2 batch-context isolation (`--isolated-uc-eval` flag):* The Sonnet-unique proposal to evaluate each cartesian UC in an isolated prompt context was rejected after pipeline audit. The v1.4.5 successful run demonstrated the grid can be constructed correctly within a single monolithic Phase 3 prompt (same batch context that failed in v1.5.1). The failure mode isn't batch-context sharing; it's absence of prompt-level discipline forcing per-cell decomposition. Lever 2's mandatory grid plus Lever 3's cardinality gate address that directly without the complexity of per-UC LLM calls.
- *Three-level confidence band (C1/C2/C3) for BUG-default:* Rejected as too granular for a prompt-based system. BUG-default is already gated to `pattern:`-tagged requirements, which is a sufficient and auditable trigger. Extending to graded confidence requires scoring infrastructure that isn't in scope.

---

## Provenance

### The 1.5.1 RING_RESET miss (2026-04-22)

During the v1.5.1 benchmark review, the chi-1.5.1 and virtio-1.5.1 runs were compared against v1.4.5 and v1.4.6 baselines. virtio-1.5.1 produced 8 bugs matching the v1.4.6 baseline, but the v1.4.5 four-bug RING_RESET family was absent. Investigation of `virtio-1.5.1/quality/code_reviews/2026-04-22-review.md` found REQ-010 correctly identifying the MMIO/vDPA compensation gap but classified as `QUESTION-001`. Cross-reference against `benchmark-1.4.5/virtio-1.4.5/quality/code_reviews/2026-04-18-reviewer.md` showed the mechanical compensation table that caught the four bugs in v1.4.5.

### The chi-1.5.1 adversarial data loss (2026-04-22)

During the chi-1.5.1 adversarial iteration on Copilot, a 5m17s / 1.6M-token prompt terminated with `Changes +0 -0`. The agent's transcript contained plans for BUG-010 (ContentCharset quoted charset) and BUG-011 (RouteHeaders uppercase exact-match), but no disk writes. This motivated the runner-reliability scope.

### The casbin-1.5.1 rate-limit hit (same window)

During a parallel casbin-1.5.1 full-run, a single Copilot prompt exceeded 15M tokens and triggered the GPT-5.4 54-hour cooldown. This motivated the README rate-limit paragraph.

### Scope split from AI-skills v1.5.2

The prior v1.5.2 scope (AI skills: project-type classification, four-pass derivation, Haiku benchmark) was renumbered to v1.5.3 on 2026-04-22 so bug-family amplification could ship as a tightly-scoped release without waiting on the larger AI-skills work. See `QPB_v1.5.3_Design.md`.

### Council review and redesign (2026-04-23)

Council-of-Three review produced 9 independent reviews across 3 sessions. A subsequent pipeline code audit identified phase-numbering errors in the original draft (Lever 2 targeted `phase2_prompt()` but classification happens in `phase3_prompt()`) and surfaced cell-to-BUG consolidation in the v1.4.5 baseline (6 cells → 3 BUG entries, unrecorded). The redesign added Lever 3 for cell-identity preservation, corrected Lever 2's target phase, replaced free-text downgrade rationale with a structured schema, and revised success criterion 1 to count covered cells rather than raw BUG entries. The v1.5.2 Implementation Plan (`QPB_v1.5.2_Implementation_Plan.md`) needs a corresponding refresh before Phase 1 implementation begins.
