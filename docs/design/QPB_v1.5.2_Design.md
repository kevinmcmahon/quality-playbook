# Quality Playbook v1.5.2 — Design Document

*Status: design captured, implementation follows v1.5.1 ship*
*Authored: April 2026*
*Owner: Andrew Stellman*
*Depends on: `QPB_v1.5.0_Design.md` (schemas, citation schema), `QPB_v1.5.1_Design.md` (Phase 5 writeup hardening)*
*Supersedes earlier v1.5.2 scope (AI skills) which is renumbered to v1.5.3.*

## Purpose of This Document

v1.5.2 addresses a specific recurring failure mode in the playbook: families of bugs that share a common architectural root cause disappear from `BUGS.md` because a single judgment call at the requirement or review layer collapses N mechanical findings into one narrative verdict — often a QUESTION rather than a BUG.

The v1.4.5 virtio run caught a four-bug family around the VIRTIO feature-bit whitelist. The v1.4.6 and v1.5.1 runs identified the exact same architectural asymmetry in Phase 2, worded it almost identically, and then classified it as `QUESTION-001` rather than escalating four distinct bugs. The root cause is not exploration coverage (the code was read), not triage calibration (the finding was considered), not iteration gaps (the baseline had it). The root cause is that Phase 1 produces one umbrella use case for a symmetric problem, Phase 2 produces one prose verdict for that umbrella, and the BUGS.md pipeline populates from BUG verdicts — not QUESTION verdicts or umbrella findings.

v1.5.2 fixes this with two surgical prompt-layer levers and a small set of operational polish items. A companion file `QPB_v1.5.2_Implementation_Plan.md` covers execution.

---

## The Gap — Evidence

### v1.4.5 run: four bugs from one mechanical table

The v1.4.5 virtio benchmark produced 17 bugs in the baseline (the highest single-version yield on record for virtio). Four of those bugs — BUG-001, BUG-002, BUG-004, and BUG-016 — share a root cause: the shared `vring_transport_features()` whitelist in `drivers/virtio/virtio_ring.c:3505-3533` default-clears every feature bit not in its closed set; transports with their own `finalize_features` hook (PCI modern, MMIO, vDPA) must compensate for bits they actually support. PCI modern's `vp_transport_features()` at `virtio_pci_modern.c:367-381` does this work. MMIO's `vm_finalize_features()` at `virtio_mmio.c:109-131` does not. vDPA's `virtio_vdpa_finalize_features()` at `virtio_vdpa.c:389-396` does not.

The v1.4.5 Phase 2 reviewer caught this by constructing a mechanical compensation table in `code_reviews/2026-04-18-reviewer.md`:

```
| Feature bit              | PCI modern | MMIO | vDPA |
| VIRTIO_F_RING_RESET      | YES        | NO   | NO   |
| VIRTIO_F_NOTIF_CONFIG_DATA | NO       | NO   | NO   |
| VIRTIO_F_ADMIN_VQ        | YES        | YES  | NO   |
| VIRTIO_F_SR_IOV          | YES        | YES  | NO   |
```

Every `NO` cell was escalated to a bug. Four bugs. The table's presence is the mechanical artifact that made escalation automatic rather than discretionary.

### v1.5.1 run: same finding, different verdict

The v1.5.1 virtio benchmark correctly identified the same architectural asymmetry. `virtio-1.5.1/quality/code_reviews/2026-04-22-review.md` contains REQ-010 ("Do not silently drop supported transport feature bits"), status `PARTIALLY SATISFIED`, analysis: "Modern PCI compensates after the shared whitelist; MMIO/vDPA do not."

The verdict table row:

```
| Pass 1 / REQ-010 | QUESTION-001 — MMIO/vDPA transport-feature restoration gap | MEDIUM | QUESTION | N/A |
```

`QUESTION-001` is a question, not a bug. The BUGS.md hydration step reads BUG entries, not QUESTION entries. Four real kernel bugs disappeared from the ledger despite being identified structurally correctly, one review layer up. Same code, same reviewer quality, identical architectural reasoning — but a single prose verdict replaced a per-cell mechanical grid, and the escalation machinery had nothing to latch onto.

This is a systemic miss, not a one-off. The v1.4.6 run had the same downgrade pattern. Any symmetric pattern (`whitelist`, `parity`, `compensation`) where Phase 1 produces one umbrella requirement and Phase 2 produces one umbrella verdict will collapse the same way.

---

## Root Cause — Why One Verdict Eats N Bugs

Two structural issues combine to produce the miss:

**1. Phase 1 emits one use case per requirement, not one per implementation site.** REQ-010 references three finalize hooks (`virtio_pci_modern.c`, `virtio_mmio.c`, `virtio_vdpa.c`). The requirement is scoped at the architectural level — "supported transport feature bits preserved." Phase 2 receives a single UC and produces a single verdict. A Phase 2 reviewer asked "does MMIO comply with REQ-010?" has to produce a per-site judgment; a reviewer asked "are feature bits preserved across transports?" can and does hedge with "partially — PCI modern compensates; MMIO/vDPA do not," which reads as ambiguous and invites a QUESTION classification.

**2. Phase 2 has no mechanical-grid obligation for symmetric requirements.** The v1.4.5 reviewer produced the compensation table on initiative. Nothing in `phase2_prompt()` requires it. When the v1.5.1 reviewer encountered the same requirement, they wrote the architectural finding as prose without enumerating cells. Missing cells had no place to go — the BUG-vs-QUESTION decision was made once for the umbrella rather than per cell.

Both failure modes are at the prompt layer. Both are fixable without changing iteration strategies, without Council changes, without schema additions that ripple through the rest of the stack.

---

## Design — Two Levers

### Lever 1: Phase 1 cartesian use-case rule

**Rule.** When Phase 1 emits a requirement whose `References` field names ≥2 files that share a path-suffix role (e.g., `virtio_mmio.c`, `virtio_vdpa.c`, `virtio_pci_modern.c` all containing `_finalize_features`), `phase1_prompt()` also emits one use case per site. The parent REQ-N stays as the umbrella; UC-N.a, UC-N.b, UC-N.c (etc.) are the per-site use cases, each with its own Actors, Preconditions, Flow, and Postconditions.

**Detection heuristic.** Path-suffix role match is the starting heuristic: group references by last-segment-before-extension or by matching function-name pattern across files. A future refinement is an explicit `pattern:` tag on the requirement (see Open Questions).

**Worked example.** REQ-010 has `References: virtio_pci_modern.c:367-381, virtio_mmio.c:109-131, virtio_vdpa.c:389-396`. All three hooks match the `*_finalize_features` pattern. Phase 1 also emits:

- UC-10a: PCI modern feature preservation (actor: PCI modern transport; precondition: whitelist cleared RING_RESET / SR_IOV / ADMIN_VQ; flow: vp_transport_features restores them; postcondition: all three bits present in final features).
- UC-10b: MMIO feature preservation (same structure; postcondition tests against vm_finalize_features).
- UC-10c: vDPA feature preservation (same structure; postcondition tests against virtio_vdpa_finalize_features).

Phase 2 now sees three concrete per-transport use cases plus the umbrella requirement, rather than one generic requirement.

### Lever 2: Phase 2 mechanical compensation grid

**Rule.** For any requirement tagged with a `pattern:` value from the set `{whitelist, parity, compensation}`, `phase2_prompt()` produces a compensation grid of (item × site × present?) and applies this classification rule verbatim:

> If an item is defined in the authoritative source (uapi header, spec section, or equivalent) AND is absent from the shared filter/whitelist AND is absent from the site's compensation hook, the default verdict for that cell is **BUG**. Downgrade to QUESTION requires a written per-cell "not-supported-in-scope" exception citing the authoritative source and explaining why the site intentionally does not support the item.

**BUG-default, not QUESTION-default.** This is the central inversion. v1.5.1 defaulted missing cells to QUESTION and required evidence to upgrade to BUG. v1.5.2 defaults missing cells to BUG and requires evidence to downgrade to QUESTION. Four real kernel bugs disappear under the old default; they surface automatically under the new one. Review thoroughness is unchanged — only the direction of the default flips.

**Worked example.** REQ-010 with `pattern: whitelist` produces:

```
| Missing bit                | PCI modern  | MMIO        | vDPA        |
| VIRTIO_F_SR_IOV (37)       | YES :372    | NO — BUG-A  | NO — BUG-B  |
| VIRTIO_F_NOTIF_CONFIG_DATA | NO — BUG-C  | NO — BUG-C  | NO — BUG-C  |
| VIRTIO_F_RING_RESET (40)   | YES :376    | NO — BUG-D  | NO — BUG-E  |
| VIRTIO_F_ADMIN_VQ (41)     | YES :379    | NO — BUG-F  | NO — BUG-F  |
```

Six cells BUG by default. The reviewer can downgrade any cell to QUESTION with a per-cell rationale, but each downgrade stands on its own evidentiary basis — the whole family can no longer collapse into one umbrella QUESTION.

**Out of scope for this lever.** No changes to iteration strategies. No changes to Council. No changes to the Tier taxonomy. No changes to the writeup hydration gate (v1.5.1's work stands). This is a prompt-layer change to Phase 1 and Phase 2 only, with a schema addition for the `pattern:` field.

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

1. **RING_RESET family recovers on virtio.** A fresh `virtio-1.5.2` benchmark run produces BUGS.md entries covering VIRTIO_F_RING_RESET (MMIO), VIRTIO_F_RING_RESET (vDPA), VIRTIO_F_NOTIF_CONFIG_DATA (all transports), VIRTIO_F_ADMIN_VQ (vDPA), and VIRTIO_F_SR_IOV (vDPA). Target: at least four BUG entries traceable to the compensation grid for REQ-010 (or its v1.5.2 equivalent).

2. **No yield regression on other benchmarks.** chi-1.5.2, cobra-1.5.2, and bootstrap produce bug counts within ±15% of their v1.5.1 baselines. The compensation-grid rule is purely additive — it surfaces previously-missed bugs without suppressing existing ones.

3. **Explicit --iterations is honored.** `python3 bin/run_playbook.py virtio-1.5.2 --iterations gap,unfiltered,parity,adversarial` runs all four strategies even when one returns +0. `python3 bin/run_playbook.py virtio-1.5.2 --full-run` preserves early-stop behavior.

4. **README documents CLI semantics.** A fresh reader can answer "how do I run just adversarial?", "what happens on `--full-run` overnight?", and "what's the rate-limit risk?" from the README alone.

5. **Candidate-stub writes survive interruption.** A forced kill of an iteration prompt mid-run leaves at least the candidate IDs and file:line anchors of bugs identified before the kill point on disk in `quality/code_reviews/`. Verified by scripted interrupt test.

6. **Self-audit passes cleanly on v1.5.2.** QPB's bootstrap self-audit with v1.5.2 machinery passes the gate with no new regressions and surfaces any real v1.5.2-introduced prose/code drift for triage.

---

## Out of Scope for v1.5.2

- **AI-skill project handling** (project-type classification, skill-specific four-pass derivation, Haiku-parity requirements). Renumbered to v1.5.3 in a separate scope doc.
- **Runner-level checkpointing** (heartbeat files, resume tokens, structured kill-resume protocol). Parked for v1.5.3 or later pending evidence that the prompt-only incremental-write fix is insufficient.
- **New iteration strategies.** The four existing strategies (gap, unfiltered, parity, adversarial) stand. Bug-family amplification operates at Phase 1 and Phase 2 regardless of which iteration is running.
- **Changes to the writeup hydration gate.** v1.5.1's five-sentinel and empty-diff-fence checks stand unchanged.
- **`pattern:` tag auto-inference from code structure.** v1.5.2 requires `pattern:` to be populated by the Phase 1 reviewer (with guidance from the prompt). Auto-inference from references structure is a possible future refinement but not required for recovery of the RING_RESET family.

---

## Open Questions

These don't block v1.5.2 design but need answers during implementation:

1. **Does every requirement need a `pattern:` tag, or only a subset?** Lean: optional field, populated when the architecture implies a pattern (whitelist / parity / compensation / none). Default is none, which means no grid is produced. The grid is opt-in via the tag.

2. **How does Phase 1's cartesian rule detect "symmetric sites" automatically?** Lean: path-suffix match on the `References` field is the v1.5.2 implementation. If Phase 1 judgment disagrees, the reviewer can override by explicit UC emission or by dropping the suffix match. Auto-detection precision is tunable; missing a symmetric set is safer than generating false per-site UCs.

3. **How does the cartesian rule interact with existing REQ numbering?** Lean: REQ-N stays as the umbrella, UC-N.a/b/c are sub-use-cases. `use_cases_manifest.json` already supports free-form IDs. No schema change for numbering.

4. **What counts as "authoritative source" for the BUG-default rule in Lever 2?** Lean: uapi headers, explicit spec text (RFC sections, API reference docs), or documented constants with a definition citation. Speculative lists assembled by the reviewer do not qualify. The compensation grid's authority floor is the same as the playbook's existing Tier-1/Tier-2 citation discipline.

5. **Should the runner reliability fix write stubs for ALL candidates, or only confirmed ones?** Lean: all candidates with file:line anchors, marked `status: candidate`. Filtering to confirmed-only defeats the survival purpose — the whole point is to preserve intent before confirmation machinery runs.

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
