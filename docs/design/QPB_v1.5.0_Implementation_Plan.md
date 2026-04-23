# Quality Playbook v1.5.0 — Implementation Plan

*Companion to: `QPB_v1.5.0_Design.md`*
*Status: planned, not started*

This document describes how to build v1.5.0. The design doc answers "what" and "why"; this doc answers "how" and "in what order." No timelines — phases are ordered by dependency, not duration.

---

## Operating Principles

Before starting any phase:

- Each phase produces a concrete deliverable that can be committed independently.
- Phases run in order. Later phases depend on earlier phase deliverables.
- The v1.4.x benchmark baseline must be preserved as a comparison point for v1.5.0 runs. Don't delete the v1.4.5 benchmark artifacts. (Note: Phase 5 migrates `previous_runs/` → `quality/runs/` — preservation means "keep the content," not "keep the path.")
- Every phase ends with a self-audit run of QPB against its own new behavior. If the playbook can't validate its own v1.5.0 changes, it's not ready.

---

## Phase 0 — Baseline Stabilization

Goal: land the v1.4.6 bug fixes from the v1.4.5 self-audit, archive the v1.4.5 self-audit artifacts as bootstrap evidence, and tag a clean baseline before structural changes begin.

**Status: complete as of 2026-04-19.** v1.4.6 is tagged; `quality/`, `previous_runs/`, and `control_prompts/` are tracked as bootstrap evidence (commits on `main`). Note that `previous_runs/` is still at the repo root — it gets migrated to `quality/runs/` in Phase 5, not here.

Work items (historical record):
- ✅ Send the 27-bug fix prompt to Claude Code
- ✅ Verify all 27 fixes land with tests (27/27 Fixed per recheck)
- ✅ Bump version to v1.4.6
- ✅ Commit v1.4.5 self-audit artifacts as bootstrap evidence (gitignore updated to track `quality/`, `previous_runs/`, `control_prompts/`; `docs_gathered/` stays ignored)
- ✅ Tag v1.4.6 in git — comparison baseline for v1.5.0
- ⏳ Run the full 5-repo benchmark against v1.4.6 to confirm no regression from v1.4.5 *(optional; can be deferred to Phase 7 comparison)*

Deliverable: tagged v1.4.6 release, tracked self-audit history. Benchmark re-run optional.

Gate to Phase 1: all 27 bugs resolved (✅); benchmark re-run either clean or explicitly deferred.

---

## Phase 1 — Schema Design

Goal: produce `schemas.md` — the static data contract that the rest of v1.5.0 references.

Schemas to define:

1. **`FORMAL_DOC`** — one per document in `formal_docs/`
   - `source_path` (required; must be a plaintext file — `.txt`, `.md`, etc.)
   - `document_sha256`, `version`, `date`, `url`, `retrieved`, `tier` (1 or 2)
   - Note: no `plaintext_path` field. Per Document Format Policy, source IS plaintext.

2. **`REQ`** — a requirement record
   - `id`, `title`, `description`, `tier` (1-5), `functional_section`, `citation` (required for Tier 1/2), `use_cases[]` (one-way link forward), `disposition` (populated when bug filed)

3. **`UC`** — a use case record
   - `id`, `title`, `description`, `formal_doc_refs[]`, `actors`, `steps`

4. **`BUG`** — a bug record
   - `id`, `title`, `severity`, `divergence_description`, `documented_intent`, `code_behavior`, `disposition` (enum), `disposition_rationale`, `req_id` (which REQ revealed the divergence), `proposed_fix`, `fix_type` (code | spec | both)

5. **`citation`** — embedded in REQ
   - `document`, `document_sha256`, `version`, `date`, `section`, `line`, `page`, `url`, `retrieved`, `citation_excerpt` (required, extracted at ingest)

6. **Enums**
   - `tier`: {1, 2, 3, 4, 5}
   - `disposition`: {code-fix, spec-fix, upstream-spec-issue, mis-read, deferred}
   - `severity`: {HIGH, MEDIUM, LOW}

Each schema entry in `schemas.md` includes: field definitions, required vs. optional, a complete example, a common-mistake note.

Deliverable: `schemas.md` in the skill directory, reviewed and committed.

Gate to Phase 2: schemas.md passes a Council-of-Three review for completeness and clarity.

---

## Phase 2 — Document Ingest Infrastructure

Goal: build the ingest pipeline that reads `formal_docs/` and `informal_docs/`, validates citations mechanically, and produces the `formal_docs_manifest.json` per run.

**Constraint: stdlib-only Python** (see design doc). No PDF library, no YAML library, no pip install.

Components:

1. **`formal_docs_ingest.py`**
   - Walks `formal_docs/` directory using `pathlib`
   - Accepts only plaintext files (extensions: `.txt`, `.md`; list in `schemas.md`)
   - Fails hard with a clear error if any non-text file is present (PDF, DOCX, etc.) — message directs user to extract to plaintext outside the playbook
   - Computes `document_sha256` via `hashlib`
   - Populates `FORMAL_DOC` records into `formal_docs_manifest.json` using stdlib `json`

2. **`citation_verifier.py`**
   - Given a REQ with a citation, extracts text at the cited location directly from the source plaintext file
   - Populates `citation_excerpt`
   - Fails the REQ if the location doesn't exist
   - Returns structured result for downstream gate consumption

3. **`informal_docs_loader.py`**
   - Reads `informal_docs/` into the LLM's context for Tier 4 derivation
   - Respects gitignore (never commits content, only reads)
   - Plaintext only — same format policy as formal_docs

Deliverable: three ingest modules (stdlib-only), unit tests, integration test against the virtio benchmark.

Gate to Phase 3: ingest passes against virtio's real spec (plaintext form), rejects a deliberately malformed citation in a test fixture, and rejects a PDF placed in `formal_docs/` with the expected error message.

---

## Phase 3 — SKILL.md Update

Goal: update the skill's instruction prose to use the new schemas and enforce the new protocols inline.

Revisions needed:

- Phase 1 (documentation intake): instructs LLM to run ingest first, then derive REQs with tier + citation
- Phase 2 (requirements derivation): reorganizes output by functional section with introductions
- Phase 3 (use case derivation): one-way REQ → UC link only
- Phase 4 (Council): adds semantic citation check (Layer 2 of hallucination mitigation)
- Phase 5 (quality gate): checks citation_excerpt was populated, checks all Tier 1/2 REQs have valid citations, checks disposition field is populated on all bugs
- Phase 6 (bug report): uses divergence framing, includes disposition and proposed fix

Key constraint from the design doc: **protocols stay inline in SKILL.md**, not split into separate reference files. Only `schemas.md` is a separate reference.

Deliverable: updated SKILL.md, reviewed for length and context-coherence.

Gate to Phase 4: SKILL.md under a reasonable line budget (target: avoid exceeding current v1.4.x size by more than 20%; prefer tighter if possible).

---

## Phase 4 — Gitignore, README, and Scaffolding

Goal: set up the project-side file structure expected by v1.5.0.

Work items:

- Update the skill's template gitignore to include:
  ```
  informal_docs/
  !informal_docs/README.md
  ```
- Create `informal_docs/README.md` template explaining the folder's purpose, what Tier 4 context is, examples of what to put there
- Create `formal_docs/README.md` template explaining tier, plaintext companion requirement, citation schema
- Update the bootstrap instructions so new projects get both folders pre-created

Deliverable: updated skill template, documented folder conventions.

Gate to Phase 5: a fresh clone of a benchmark repo has the right folder structure and knows what goes where.

---

## Phase 5 — Unified `quality/` Layout + Quality Gate Mechanical Checks

Goal: consolidate all skill output under `quality/`, implement the run-archival contract, and wire the gate to enforce the new schema.

### 5a. Layout consolidation and migration

- Update every write path in the orchestrator, phase scripts, and `quality_gate.py` so that output lands under `quality/` only (no more root-level `control_prompts/` or `previous_runs/`)
- Move `control_prompts/` to `quality/control_prompts/`
- Rename `previous_runs/` → `quality/runs/`
- Build a one-time migration script `bin/migrate_v1_5_0_layout.py`:
  - Moves `control_prompts/` → `quality/control_prompts/`
  - Renames `previous_runs/` → `quality/runs/`
  - For each pre-existing run folder under `quality/runs/`, backfill `INDEX.md` from available metadata (git log, timestamps on files, surviving artifacts) — best-effort, fields may be `unknown` for old runs
  - Generates the initial top-level `quality/RUN_INDEX.md`
  - Idempotent: safe to re-run
- Update Phase 0 (Prior Run Analysis) glob from `previous_runs/*/quality/BUGS.md` → `quality/runs/*/BUGS.md`. Grep the codebase for any other reference to `previous_runs/` and update.

### 5b. Archival and INDEX generation

- `write_timestamped_result(basename, content)` helper for `quality/results/` writes — produces `<basename>-YYYYMMDDTHHMMSSZ.<ext>` + `<basename>-latest.<ext>` pointer (symlink where supported, copy fallback)
- At end of each run, orchestrator writes `quality/INDEX.md` (for the current run) with all required fields (see design doc)
- `archive_run()` function in the orchestrator: snapshots `quality/` (excluding `quality/runs/` itself) to `quality/runs/<start-timestamp>/`, appends row to `quality/RUN_INDEX.md`
- Trigger: auto-invoked on successful gate pass. Overwrite behavior on failed-run detection: orchestrator checks `quality/results/gate-report-latest.json` verdict; if non-pass or missing, next run overwrites without prompting (non-interactive safety)
- Explicit `quality_playbook archive [--status=failed|partial]` CLI command for operator-driven archival. Failed/partial runs get suffix on folder name: `...-FAILED` / `...-PARTIAL`

### 5c. `.gitignore` policy

- Skill template `.gitignore` gets a new section:
  ```
  # Archived QPB runs — bulk history; uncomment to track as project evidence.
  quality/runs/
  !quality/RUN_INDEX.md
  ```
- QPB's own `.gitignore` does NOT add `quality/runs/` (tracks bootstrap evidence, as established in v1.4.6)
- `quality/README.md` template explains the tradeoff so adopters can opt in knowingly

### 5d. Gate mechanical checks (Layer 1 of hallucination mitigation)

- Every Tier 1/2 REQ has a citation
- Every citation has a `citation_excerpt`
- Every citation's location resolves in the plaintext companion (re-verify at gate time, not just at ingest, to catch post-ingest tampering)
- Every BUG has a disposition field with a valid enum value
- Every REQ belongs to a functional section
- No non-plaintext file in `formal_docs/` or `informal_docs/` (only `.txt`, `.md`, etc. allowed; see schemas.md for the supported-extensions list)
- `quality/INDEX.md` exists and has all required fields

Failure mode: gate fails with specific file+line references so the issue can be fixed without re-running the whole playbook.

Deliverable: migrated layout, updated orchestrator + gate, migration script, timestamped-results helper, `quality/README.md` template, test fixtures.

Gate to Phase 6:
- Migration script run against a copy of QPB's own repo produces the expected `quality/runs/` structure with a valid backfilled `INDEX.md`
- A full run end-to-end writes only under `quality/`, archives on success, overwrites the prior failed run when detected
- Gate correctly flags deliberately broken fixtures (fabricated citation, missing disposition, orphan REQ, missing INDEX.md)
- `-latest` pointer resolves to the newest file in `quality/results/`
- Non-interactive run (`run_playbook` / benchmark harness) completes without prompting even when a prior failed run is present

---

## Phase 6 — Council-of-Three Semantic Citation Check

Goal: implement Layer 2 of hallucination mitigation in the Phase 4 Council.

The Council prompt gets a new required sub-check: for each Tier 1/2 REQ, review the `citation_excerpt` and answer one question: "Does this excerpt support this requirement as stated, or does the requirement overreach what the excerpt actually says?"

**Prompt strategy: one prompt per Council member, structured per-REQ response.** All Tier 1/2 REQs fit in one prompt, but the response schema forces per-REQ reasoning — a JSON array with one object per REQ ID, each containing `verdict` (supports | overreaches | unclear) and `reasoning`. Forces the LLM to process each REQ individually within one response rather than pattern-matching "these all look fine." Keeps prompt count at 3 total (one per Council member) instead of 3×N.

Batching threshold: if Tier 1/2 REQ count exceeds 15 in a single run, split into batches of 5 REQs per prompt per Council member. The 15-REQ threshold is a guardrail, not a gate — can be tuned based on observed behavior.

Output: `citation_semantic_check.json` with per-REQ verdicts from each Council member. Gate fails if any REQ is flagged `overreaches` by two or more members (majority rule). Single-member `unclear` verdicts flagged for human review but don't fail the gate.

Deliverable: updated Council prompts, structured response schema, gate integration, test fixture where citation exists but doesn't support the claim.

Gate to Phase 7: semantic check correctly flags the fixture; prompt count stays at 3 for sub-15-REQ runs; batching triggers correctly at the 15-REQ threshold.

---

## Phase 7 — Benchmark Validation

Goal: run v1.5.0 against all five benchmark repos and compare to the v1.4.6 baseline.

Expected outcomes (these are the falsifiable hypotheses that tell us whether v1.5.0 is working):

- **virtio** (has formal spec): significant improvement in bug analysis quality; bugs now have Tier 1 citations and dispositions. Raw bug count may go up or down — analysis depth is what matters.
- **chi, cobra, express, httpx** (no formal spec): clean Tier 3/4/5 runs. Citation gate has nothing to check (no Tier 1/2 REQs). Bug count should be comparable to v1.4.6. Meta-finding reported: "0 Tier 1/2 requirements."
- Across all repos: zero unverified Tier 1/2 citations in any artifact.

Variations to test:
- Deliberately malformed citations in a fixture repo → gate rejects
- Virtio spec bumped to a fabricated v1.2 with checksum change → old citations flagged stale
- Empty `informal_docs/` → Tier 4 pass skips cleanly

Deliverable: benchmark comparison report, any bugs found in v1.5.0 itself filed, decision to ship or iterate.

Gate to release: all 5 repos complete runs without gate failures on legitimate content; all deliberately-broken test fixtures are correctly rejected.

---

## Phase 8 — Self-Audit

Goal: run QPB v1.5.0 against the QPB repository itself (the bootstrap loop) to prove the playbook can validate its own v1.5.0 changes.

This is the same bootstrap pattern used for v1.4.5. Expectation: v1.5.0 should find its own requirements file and use case file, verify its own citations (if any Tier 1/2 exist), and produce a clean run. Any bugs found get added to the v1.5.1 backlog.

Deliverable: v1.5.0 self-audit artifacts committed to `quality/` and archived to `previous_runs/v1.5.0/`.

Gate to release: self-audit completes without gate failures. Bug yield documented as bootstrap evidence.

---

## Release

- Tag v1.5.0 in git
- Update release notes referencing `QPB_v1.5.0_Design.md` for design rationale
- Announce to any downstream users (if applicable)
- Start v1.5.1 backlog from self-audit findings

---

## Parking Lot (explicitly deferred from v1.5.0)

- Project-specific schema extensions (`schemas.local.md`)
- Disposition accuracy tracking / calibration dashboard
- Bidirectional REQ ↔ UC traceability
- Cross-project requirement reuse
- Automatic spec-version diffing (manual version bumps only in v1.5.0)

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| SKILL.md becomes unwieldy after protocol additions | Medium | Measure line count during Phase 3; aggressively cut redundant prose if growth exceeds 20% |
| LLM hallucinates `citation_excerpt` to match a fabricated citation | Low (excerpt extracted mechanically, not by LLM) | Excerpt extraction is a deterministic text slice, not an LLM task |
| No benchmark repo has rich enough formal docs to really test Tier 1/2 | Medium | virtio is the one with spec; if insufficient, add a synthetic benchmark with known spec+code divergences |
| Plaintext extraction quality (done outside QPB) breaks line-number citations | Medium | Gate uses `section` and a fuzzy-match excerpt rather than strict line numbers when extraction is lossy; document best-practice extraction steps in `formal_docs/README.md` |
| Benchmark yield drops on doc-poor projects because Tier 5 REQs get filtered too aggressively | Medium | Validate on chi/cobra early in Phase 7; adjust Tier 5 handling if needed |
| Stdlib-only constraint blocks a feature that would otherwise be trivial | Low-Medium | If it happens, escalate before taking a dependency — might need a design adjustment instead |

---

## Resolved Design Questions

The four open questions from earlier drafts have been resolved and their answers are now embedded in the relevant phase bodies:

1. **Phase 2 — ingest and PDF handling.** No `pdftotext`, no PDF acceptance. Core Python is stdlib-only so it runs anywhere without a venv. Plaintext-only policy. (Phase 2 body; "Stdlib-Only Python" + "Document Format Policy" sections in design doc.)
2. **Phase 3 — functional sections.** LLM-derived, reviewed by Phase 4 Council. No predefined ontology. (Phase 3 body.)
3. **Phase 5 — Tier 5 gate behavior.** No hard fail. Tier 5 is valid when no better source exists; report tier distribution as a metric. (Phase 5 body.)
4. **Phase 6 — Council semantic check prompt structure.** One prompt per Council member (3 total), structured per-REQ JSON response. Batches of 5 REQs per prompt if Tier 1/2 count exceeds 15 in a run. (Phase 6 body.)
