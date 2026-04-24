# Quality Playbook v1.5.2 — Implementation Plan

*Companion to: `QPB_v1.5.2_Design.md` (revised 2026-04-23)*
*Status: revised 2026-04-23 — scope expanded with reference_docs refactor and Council-driven redesign*
*Depends on: v1.5.1 shipped (Phase 5 writeup hardening, case-insensitive diff fence gate, 171-test gate suite)*

## Pre-release note: benchmark pinned skill copies (Finding A4)

Round 5 Council Finding A4 flagged that two benchmark repos ship pinned copies
of the v1.5.1-era skill under `.github/skills/` — `repos/virtio-1.5.1/.github/skills/`
and `repos/chi-1.5.1/.github/skills/`. Both copies are byte-identical to each
other: `SKILL.md` carries 14 `formal_docs`/`informal_docs` references and
`quality_gate.py` carries 12. Version metadata in both pinned `SKILL.md` files
reads `version: 1.5.1`. These are the exact skill artifacts that produced each
benchmark's original output — kept for reproducibility, not freshness.

Three possible dispositions for release:

1. **Leave as v1.5.1 pinned copies** (status quo). Reproducibility preserved:
   re-running the benchmark against the pinned skill produces the same output
   that was captured originally. Downside: future readers seeing `formal_docs/`
   in these pinned `SKILL.md` files may get confused about whether live QPB
   still uses that layout.
2. **Replace with v1.5.2 live skill copy.** The v1.5.2 skill expects
   `reference_docs/cite/`, which is the post-migration layout now present in
   those benchmark repos (Phase 1i and C13.6/A3 both moved the tree). But the
   benchmark's captured output (BUGS.md, REQUIREMENTS.md) was produced by the
   v1.5.1 skill against the pre-migration layout, so the captured artifacts
   and the pinned skill would no longer agree on what was ingested. Breaks
   reproducibility.
3. **Delete pinned skill copies entirely.** Benchmarks become layout-only
   snapshots; reproducibility relies on checking out QPB at a historical tag.
   Least permissive, but simplest.

Recommended: **option 1 (leave as-is) for v1.5.2 ship.** The `formal_docs/`
references inside a pinned v1.5.1 `SKILL.md` are historically correct for that
version; a single one-line note at the top of each pinned `SKILL.md` pointing
readers at the live QPB skill would resolve the confusion without touching
the reproducibility-critical body. That one-line note is a v1.5.3 cleanup
task, not a v1.5.2 blocker. Andrew's call.

---

v1.5.2 ships two work streams in one release:

1. **Bug-family amplification** — three levers (Phase 1 cartesian UC rule, Phase 3 compensation grid with BUG-default, cell-identity preservation across Phase 3 and Phase 5) plus operational polish (iteration handling, README CLI docs, candidate-stub writes).

2. **reference_docs refactor** — collapse `formal_docs/` + `informal_docs/` into a single `reference_docs/` folder with a `cite/` subfolder for byte-verified citable material. Consolidate ingest into one bin script. Update schema, skill, README, TOOLKIT, and agent files. Migrate benchmark repos.

The two streams don't conflict structurally (prompt-layer work vs. folder/schema-layer work) so they land together. The reference_docs refactor is a breaking data-contract change; because QPB is pre-1.0 and has no external adopters yet, the breaking change is absorbed in this release rather than deferred.

The AI-skills work previously under v1.5.2 is renumbered to v1.5.3 and continues in `QPB_v1.5.3_Design.md` / `QPB_v1.5.3_Implementation_Plan.md`.

---

## Operating Principles

- **No regression on existing benchmarks.** chi, cobra, virtio, bootstrap must produce bug counts within ±15% of their v1.5.1 baselines. Additive changes only.
- **v1.4.5 RING_RESET family is the canonical validation target, measured at cell coverage.** Success is "every cell covered by a BUG or a structured downgrade," not "≥4 BUG entries." The v1.4.5 baseline had 6 cells → 3 BUGs; the new criterion counts the cells.
- **reference_docs refactor ships first.** It's a schema-level change; the bug-family work references citation records produced by the new ingest script. Land the refactor, verify benchmarks ingest cleanly, then work on prompts.
- **Prompt-layer first, runner-layer second.** Where a prompt-layer fix suffices, ship it and park heavier runner changes pending evidence.
- **Benchmark gates every phase.** No phase lands without a fresh benchmark run confirming the change behaves as designed.
- **Council-of-Three review is mandatory pre-release.** Levers 1, 2, and 3 are behavioral design changes and deserve three-model review (gpt-5.4, gpt-5.3-codex, claude-sonnet-4.6) before the final benchmark re-validation locks in.

---

## Phase 0 — v1.5.1 Ship Confirmation

Goal: v1.5.1 merged to main, tagged, pushed; benchmarks from v1.5.1 captured as the regression baseline.

Work items:

- Verify branch `1.5.1` merged into main (no-ff)
- Verify tag `v1.5.1` pushed
- Capture v1.5.1 baselines: virtio-1.5.1 (8 bugs), chi-1.5.1 (9 bugs), cobra-1.5.1 (record count), bootstrap-1.5.1 (self-audit clean)
- Document baseline bug counts and overlap notes in `quality/benchmark_history.md`

Gate to Phase 1: v1.5.1 is the current `main` HEAD; `SKILL.md` reports version 1.5.1; all four baseline bug counts are recorded.

---

## Phase 1 — reference_docs refactor

Goal: replace the `formal_docs/` + `informal_docs/` split with a single `reference_docs/` folder containing `reference_docs/cite/` for citable material. Consolidate ingest into one walker. Update all docs, schemas, and benchmark repos.

### 1a — Bin script consolidation

- Create `bin/reference_docs_ingest.py`. Walks `reference_docs/` once:
  - Files at top level (`.txt` or `.md`) → load as Tier 4 context, return via `load_tier4_context(target_repo)` returning a sorted list of `(path, text)` tuples (same shape as today's `load_informal_docs`).
  - Files under `cite/` (`.txt` or `.md`) → emit `FORMAL_DOC` records into `quality/formal_docs_manifest.json` with mechanical `citation_excerpt` via `citation_verifier.py` (Tier 1 by default; no sidecar required).
  - Files named `README.md` anywhere under `reference_docs/` → skipped (reserve for optional adopter-local notes).
  - Non-plaintext extensions → rejected with the standard conversion hints (`pdftotext`, `pandoc -t plain`, `lynx -dump`).
- Port all existing tests from `bin/tests/test_formal_docs_ingest.py` and `bin/tests/test_informal_docs_loader.py` into `bin/tests/test_reference_docs_ingest.py`. Adjust fixtures to use `reference_docs/` + `reference_docs/cite/` layout.
- Delete `bin/formal_docs_ingest.py` and `bin/informal_docs_loader.py` (and their test files) only after the new tests pass.

### 1b — Delete old folders

- `rm /Users/andrewstellman/Documents/QPB/formal_docs/README.md`
- `rm /Users/andrewstellman/Documents/QPB/informal_docs/README.md`
- `rmdir /Users/andrewstellman/Documents/QPB/formal_docs`
- `rmdir /Users/andrewstellman/Documents/QPB/informal_docs`
- Verify `.gitignore` — remove any reference to `formal_docs/` or `informal_docs/` (informal_docs had an entry per the old README).

### 1c — Create the new folder (empty)

- `mkdir -p reference_docs/cite` — ship empty, no README. The folder exists so the ingest script has a target to walk in the QPB repo itself; contents are populated by adopters in their own target repos.
- Note: QPB's own `reference_docs/` stays empty. Bootstrap self-audit reads source (Tier 3); no citable specs needed for auditing the skill itself.

### 1d — Update schemas.md

Replace every `formal_docs/` path reference with `reference_docs/cite/`. Specific touchpoints (confirm line numbers against current file):

- §1.1 "scope" mention of `formal_docs/` and `informal_docs/` extensions → single `reference_docs/` extension list
- §4 `FORMAL_DOC` record: "One record per plaintext document in `formal_docs/`" → "One record per plaintext document in `reference_docs/cite/`"
- Example `source_path`: `formal_docs/virtio-v1.1.txt` → `reference_docs/cite/virtio-v1.1.txt`
- §5 citation example `"document": "formal_docs/virtio-v1.1.txt"` → `"document": "reference_docs/cite/virtio-v1.1.txt"`
- §10 invariants #9, #15: path-based assertions update accordingly

Add a new §1.1 paragraph explaining the folder structure:

> Plaintext inputs live under `reference_docs/` in the target repo. Files at the top level are Tier 4 context — loaded into Phase 1 prompts as background but not cited with byte-verification. Files under `reference_docs/cite/` are citable sources — each produces a `FORMAL_DOC` record with a mechanical `citation_excerpt` that `quality_gate.py` byte-verifies against the on-disk bytes. Tier 1 is the default for `cite/` contents; the Tier 1/Tier 2 distinction is internal to the playbook's authority hierarchy and does not require adopter action.

### 1e — Update SKILL.md

Update all 8 touchpoints (line numbers approximate, confirm in-place):

- Line 24 (Phase 1 description): `bin/formal_docs_ingest` and `bin/informal_docs_loader` → `bin/reference_docs_ingest`
- Line 94 (artifact contract table): update ingest script reference
- Line 390-391 (Phase 1 execution): replace the two-script invocation with a single `python -m bin.reference_docs_ingest <target>` call; update folder path references
- Line 393 (sidecar convention): remove. No sidecar in the new design.
- Line 706 (Tier definitions): keep the tier taxonomy but reference the new folder structure
- Line 1054 (manifest table): update ingest script reference
- Line 1834 (Phase 6 gate): update ingest script reference

Add a new actionable message in Phase 1 when `reference_docs/` is missing or empty:

```
> Phase 1 found no documentation in reference_docs/. The playbook will proceed
> using only Tier 3 evidence (the source tree itself). For better results, drop
> plaintext documentation into:
>   reference_docs/            ← AI chats, design notes, retrospectives (Tier 4 context)
>   reference_docs/cite/       ← project specs, RFCs, API contracts (citable, byte-verified)
> See README.md "Providing documentation" for details.
```

Same message fires when the folder exists but is empty. The message is informational, not blocking — the run proceeds.

### 1f — Update root README.md

Remove the `docs_gathered/` confusion. Replace the current Step 1 and the scattered `mkdir -p formal_docs informal_docs` references with a single "Providing documentation" section. Full replacement text for the section:

```markdown
### Step 1: Provide documentation (strongly recommended)

The playbook produces better requirements, fewer false positives, and more specific
bugs when it has written documentation to work from. Plaintext files only —
`.txt` and `.md`. Convert other formats first:

- `pdftotext spec.pdf spec.txt`
- `pandoc -t plain spec.docx -o spec.txt`
- `lynx -dump https://example.org/spec.html > spec.txt`

**Where to put documentation in your target repo:**

    reference_docs/
    ├── claude-chat-2026-03-15.md    ← AI chat logs, design notes (Tier 4 context)
    ├── design-notes.md              ← exploratory writeups, retrospectives
    ├── incident-2026-02-retro.md    ← post-mortems, lessons learned
    └── cite/
        ├── my-project-spec.md       ← your project's own spec (citable)
        └── rfc7807.txt              ← external standards you cite (citable)

**Top-level `reference_docs/`** holds Tier 4 context — chat logs, design notes,
retrospectives, any exploratory material. The playbook reads these into Phase 1
as background but does not byte-verify quotes from them.

**`reference_docs/cite/`** holds citable material — specs, RFCs, API contracts,
published standards. Every file here produces a `FORMAL_DOC` record with a
mechanical citation excerpt that `quality_gate.py` byte-verifies. If you cite
it in a BUG or REQ, the gate checks the quote matches the bytes on disk.

You do not need a sidecar file, a frontmatter header, or any metadata.
Placement in `cite/` is the flag that says "this is citable."

If you have no documentation at all, the playbook still runs. It will operate
from the source tree alone (Tier 3 evidence) and produce Tier 5 inferred
requirements. The results are weaker but valid.

**What does not belong in reference_docs:**

- Binary or formatted files (PDF, DOCX, HTML) — convert first, commit plaintext
- Code excerpts — the source tree is already Tier 3 authority
- Test fixtures or sample data — these are project artifacts, not documentation
- Anything private or sensitive that should not be read by an LLM — `reference_docs/`
  contents are loaded into Phase 1 prompts
```

Also: update the existing shell setup blocks (3 locations, lines ~40, ~52, ~61) from `mkdir -p formal_docs informal_docs` to `mkdir -p reference_docs reference_docs/cite`. Remove the `# formal_docs/README.md and informal_docs/README.md ship with the skill source` comment line — no README ships anymore.

### 1g — Update ai_context/TOOLKIT.md

TOOLKIT.md is read by AI agents (Claude Code, Codex, Cowork, Cursor) setting up the playbook for a user. The agent needs to know where to put files an adopter hands over. Replace the current `docs_gathered/` guidance (lines ~28-29) with:

```markdown
### Add documentation (strongly recommended)

If the user has specs, API docs, design documents, AI chat logs, retrospectives,
or community documentation, place them in a `reference_docs/` directory at the
top of the target repo:

- **Tier 4 context (AI chats, design notes, retrospectives)** → `reference_docs/`
  at the top level. No special treatment — these are read as background.

- **Citable material (project specs, RFCs, API contracts)** → `reference_docs/cite/`
  subfolder. Every file here gets a byte-verified citation record. If a file is
  the adopter's project-internal spec or an authoritative external standard and
  you want the playbook to cite it with rigor, put it in `cite/`.

- **File format** — plaintext only (`.txt` or `.md`). Convert binary/formatted
  sources first: `pdftotext spec.pdf spec.txt`, `pandoc -t plain spec.docx -o spec.txt`,
  `lynx -dump https://example.org/spec.html > spec.txt`. The ingest script
  rejects non-plaintext extensions.

- **No sidecar needed** — folder placement is the flag. If the user asks how to
  mark something citable, tell them to move it into `reference_docs/cite/`.
  Do not create `.meta.json` files; the current schema does not use them.

- **If the user has documentation but is unsure what's citable** — default to
  top-level `reference_docs/` (Tier 4 context). Only move files into `cite/`
  when the adopter confirms the file is an authoritative source they want
  the playbook to cite by quote.

When asked to help an adopter set up the playbook, run:

    mkdir -p reference_docs reference_docs/cite

and then either move files they identify into the appropriate bucket or ask
them to drop files in and classify afterward.
```

### 1h — Update AGENTS.md and agents/quality-playbook.agent.md

AGENTS.md: lines ~33-34 and ~45 contain the stale `# formal_docs/README.md and informal_docs/README.md ship with the skill source` comment plus `mkdir -p formal_docs informal_docs`. Replace with `mkdir -p reference_docs reference_docs/cite`; remove the README comment.

agents/quality-playbook.agent.md: lines ~62-63 have the same pattern. Same replacement.

### 1i — Migrate benchmark repos under /repos/

For each benchmark repo that has populated `formal_docs/` or `informal_docs/`:

- Move contents of `formal_docs/*` (excluding README and `.meta.json` sidecars) → `reference_docs/cite/`
- Move contents of `informal_docs/*` (excluding README) → `reference_docs/`
- The sidecars (`.meta.json` files) are no longer read — delete them. The citation pipeline now uses only the file bytes; tier metadata was a sidecar concept.
- Delete empty `formal_docs/` and `informal_docs/` folders
- Re-run `python -m bin.reference_docs_ingest <repo>` to verify ingest still produces a valid `quality/formal_docs_manifest.json`
- Re-run `python3 bin/quality_gate.py <repo>` to verify the manifest and existing artifacts still gate-pass

Benchmark repos to migrate (non-exhaustive, confirm by `find /repos -type d -name formal_docs -o -name informal_docs`):
- `repos/virtio-1.5.1/` and earlier virtio versions with populated folders
- `repos/chi-1.5.1/` and earlier chi versions
- `repos/cobra-1.5.1/` and earlier cobra versions
- Any bootstrap or benchmark-1.4.5 subdirectory

**Files touched (Phase 1 total):**
- Created: `bin/reference_docs_ingest.py`, `bin/tests/test_reference_docs_ingest.py`
- Deleted: `bin/formal_docs_ingest.py`, `bin/informal_docs_loader.py`, `bin/tests/test_formal_docs_ingest.py`, `bin/tests/test_informal_docs_loader.py`, `formal_docs/README.md`, `informal_docs/README.md`, `formal_docs/`, `informal_docs/`
- Edited: `schemas.md`, `SKILL.md`, `README.md`, `ai_context/TOOLKIT.md`, `AGENTS.md`, `agents/quality-playbook.agent.md`, `.gitignore`
- Benchmark migrations under `repos/` (data moves, sidecar deletions)

**Acceptance:**
- `python -m bin.reference_docs_ingest repos/virtio-1.5.1` runs cleanly, produces a valid `formal_docs_manifest.json`
- `python3 bin/quality_gate.py repos/virtio-1.5.1` passes
- `python -m unittest discover bin/tests` passes (all old + new tests)
- No references to `formal_docs/` or `informal_docs/` remain in `SKILL.md`, `schemas.md`, `README.md`, `TOOLKIT.md`, `AGENTS.md`, or `agents/*.md` (grep confirms)
- SKILL.md contains the new "missing reference_docs" actionable message

---

## Phase 2 — Schema: `pattern:` tag on requirements

Goal: add an optional `pattern:` field to the REQ record so Phase 1 can mark whitelist / parity / compensation requirements for Phase 3 grid emission.

Work items:
- `schemas.md`: add `pattern` field to REQ schema. Valid values: `whitelist`, `parity`, `compensation`, or omitted (default = no grid).
- `.github/skills/quality_gate/quality_gate.py`: extend REQ parsing to read the optional field; gate does not fail if absent; gate does fail if present with an invalid value.
- Add unit tests for the new field (valid values, invalid values, omitted field) — minimum four cases.
- `SKILL.md`: one-paragraph addition documenting the field with when-to-use guidance for each value.

**Acceptance:** schema doc contains `pattern:` field definition; gate tests pass; requirements with `pattern: whitelist` / `parity` / `compensation` round-trip through the gate; requirements without the field round-trip unchanged.

---

## Phase 3 — Lever 1: Phase 1 cartesian UC rule with eligibility check

Goal: `phase1_prompt()` emits per-site use cases when a requirement's `References` field names ≥2 files that pass both eligibility gates.

Work items:

- `bin/run_playbook.py::phase1_prompt()`: add a section instructing the reviewer, for each requirement with ≥2 references, to apply the **Cartesian eligibility check** before emitting per-site UCs:
  1. **Path-suffix match.** At least two references share a path-suffix role (last segment before extension, or matching function-name pattern across files). Example of a match: `virtio_mmio.c`, `virtio_vdpa.c`, `virtio_pci_modern.c` all containing `_finalize_features`. Example of a non-match: `CONFIG_FOO`, `CONFIG_BAR` kconfig flags.
  2. **Function-level similarity.** Each matching reference cites a line range of similar size (within 2× of the median) and each range is inside a function body — not a file-header or a kconfig block.
- If both hold → emit one UC per site (UC-N.a, UC-N.b, UC-N.c, …) with per-site Actors, Preconditions, Flow, Postconditions. Parent REQ-N stays as the umbrella.
- If only path-suffix matches → keep umbrella UC and mark the cluster `heterogeneous` in a comment. Phase 3 can still override.
- Include the REQ-010 / VIRTIO_F_RING_RESET case as the worked example embedded in the prompt.
- Add a confirmation checklist: "For each requirement I emitted with ≥2 references, I ran the Cartesian eligibility check. Where both gates passed, I emitted per-site UCs. Where only path-suffix matched, I marked the cluster heterogeneous."

**Files touched:** `bin/run_playbook.py::phase1_prompt()`. No gate changes (structure validated downstream).

**Acceptance:** Re-running Phase 1 against `virtio-1.5.2` source produces UC-10a (PCI modern), UC-10b (MMIO), UC-10c (vDPA) for the feature-bit requirement. Chi and cobra Phase 1 runs produce no new per-site UCs for requirements that don't pass the eligibility check (regression check: no over-emission).

---

## Phase 4 — Lever 2: Phase 3 compensation grid + BUG-default + structured rationale

Goal: `phase3_prompt()` produces a compensation grid for any requirement tagged `pattern: whitelist | parity | compensation`, defaults absent cells to BUG, and requires structured JSON rationale for QUESTION downgrades.

Note: this targets `phase3_prompt()` (code review), not `phase2_prompt()` (artifact generation). The classification decision happens in Phase 3 where BUGS.md is written.

Work items:

- `bin/run_playbook.py::phase3_prompt()`: add a MANDATORY GRID STEP for pattern-tagged requirements:
  1. Enumerate the authoritative item set (uapi header, spec section, documented constants) — mechanical extraction, not freehand list.
  2. Enumerate the sites from the requirement's per-site UCs.
  3. Produce a grid of (item × site × present?) using code inspection to fill cells.
  4. Apply the BUG-default rule: cells where the item is defined in authoritative source AND absent from shared filter AND absent from site compensation default to BUG.
  5. Downgrade to QUESTION requires a structured JSON record appended to `quality/compensation_grid_downgrades.json`:

```json
{
  "cell_id": "REQ-010/cell-RING_RESET-MMIO",
  "authority_ref": "include/uapi/linux/virtio_config.h:116",
  "site_citation": "drivers/virtio/virtio_mmio.c:109-131",
  "reason_class": "intentionally-partial",
  "falsifiable_claim": "MMIO does not support RING_RESET because <cited rationale> — falsifiable by showing MMIO re-sets bit 40 under condition X"
}
```

  - `reason_class` enum: `out-of-scope | deprecated | platform-gated | handled-upstream | intentionally-partial`
  - Missing any field, or `reason_class` outside the enum, or zero-length `falsifiable_claim` → cell reverts to BUG with no re-prompt loop.
  - 6. Emit one BUG entry per defaulted cell with file:line citation, spec basis, and expected vs actual behavior.

- Include the RING_RESET grid as the worked example (four bits × three transports).
- Add confirmation checklist: "For each `pattern:`-tagged requirement, I produced a grid, applied the BUG-default rule, wrote one BUG per defaulted cell, and for any downgrade emitted a structured record with all required fields."

**Files touched:** `bin/run_playbook.py::phase3_prompt()`. Gate changes: extend the Phase 3 gate check to fail when a `pattern:`-tagged requirement has no grid or fewer than (items × sites) cells populated; and to validate structured downgrade records against the schema.

**Acceptance:** Re-running Phase 3 against `virtio-1.5.2` surfaces BUG entries for the RING_RESET family (MMIO RING_RESET, vDPA RING_RESET + ADMIN_VQ, all-transports NOTIF_CONFIG_DATA, vDPA SR_IOV), matching the v1.4.5 BUG-001/002/004/016 findings. Chi and cobra produce no spurious BUG-default entries for untagged requirements.

---

## Phase 5 — Lever 3: Cell-identity preservation across Phase 3 and Phase 5

Goal: every grid cell gets a deterministic ID; BUGS.md entries that consolidate cells name them; Phase 5 reconciliation verifies every cell is covered by a BUG or a structured downgrade.

Work items:

- **Cell ID scheme.** Phase 3 prompt change: every compensation grid cell gets ID `REQ-N/cell-<item>-<site>`. Mechanical derivation from the grid row/column, not reviewer invention.

- **BUGS.md `Covers:` and `Consolidation rationale:` fields.** Schema addition: BUG records can optionally include:
  - `covers: [<cell_id>, <cell_id>, …]` — array of cell IDs this BUG addresses.
  - `consolidation_rationale: <string>` — required when `covers` has ≥2 entries; explains why the cells share a BUG (shared fix path, same function, etc.).
  - `quality_gate.py` validates: if `covers` has ≥2 entries, `consolidation_rationale` must be present and non-empty.

- **Phase 5 cardinality reconciliation gate.** `bin/run_playbook.py::phase5_prompt()`: for every requirement with a `pattern:` tag, enumerate grid cells from Phase 3's output, walk BUGS.md entries referencing that requirement, build the union of `Covers:` cell IDs, compare to the cell set from the grid. Cells not covered by a BUG and not downgraded via a structured record fail the gate with a cell-coverage report.

- **Phase 3 self-check (advisory).** `phase3_prompt()` adds: after writing BUGS.md and the downgrade records, verify that every grid cell appears in either a BUG's `covers` field or a downgrade record. Self-check is advisory; Phase 5 gate is blocking.

- **Scripted regression test.** Add `bin/tests/test_cardinality_gate.py` with a synthetic fixture: Phase 3 writes a BUGS.md entry with `Covers:` missing one cell from the grid. Phase 5 gate aborts with an explicit coverage report. Assert the abort message lists the uncovered cell ID.

**Files touched:** `schemas.md` (BUG schema `covers` + `consolidation_rationale` fields), `.github/skills/quality_gate/quality_gate.py`, `bin/run_playbook.py::phase3_prompt()`, `bin/run_playbook.py::phase5_prompt()`, `bin/tests/test_cardinality_gate.py` (new).

**Acceptance:** Schema documents the new fields. Gate tests pass (additions + all existing). Scripted cardinality-gate test: Phase 5 aborts when a cell is missing from `covers`. Phase 3 self-check fires (informational) when cells are uncovered.

---

## Phase 6 — Respect explicit `--iterations`

Goal: bypass diminishing-returns early-stop when `--iterations` was provided as an explicit list rather than expanded from `--full-run`.

(No change from the original v1.5.2 plan. See previous Phase 4 content.)

Work items:
- `bin/run_playbook.py` argparse: add internal marker `args._iterations_explicit = True` set only when `--iterations` appeared in argv directly. `--full-run` expansion sets the marker to `False`.
- Early-stop sites: guard on the marker. Bypass early-stop when `_iterations_explicit` is `True`.
- New tests covering three fixtures (explicit list, --full-run, single-strategy).

**Acceptance:** All existing runner tests pass. New iteration tests pass. Explicit `--iterations gap,unfiltered,parity,adversarial` runs all four regardless of preceding yields.

---

## Phase 7 — Adopter-facing documentation

Goal: README documents CLI semantics and rate-limit warnings; the reference_docs guidance from Phase 1 is live in README, TOOLKIT.md, and AGENTS.md.

Work items:

1. README subsection "Running the playbook: phases, iterations, and macros" (phases 1-6 summary, iteration strategies, three invocation modes).
2. README "Rate limits" paragraph: GPT-5.4 Copilot 54-hour cooldown on ~15M-token prompts (casbin-1.5.1 incident), Claude Code plan budget notes, recommendations.
3. Confirm Phase 1's README "Providing documentation" section is in place (lands in Phase 1, verified here).
4. Confirm TOOLKIT.md update is in place (lands in Phase 1, verified here).

**Acceptance:** Fresh reader answers "how do I run just adversarial?", "what's the early-stop rule?", "what rate limits should I plan for?", "where do I put my project's spec?" from README alone. TOOLKIT.md tells an AI agent where to place user-provided docs.

---

## Phase 8 — Runner reliability: incremental candidate stubs

Goal: iteration prompts write candidate BUG stubs to disk on identification, not at end-of-review.

(No change from the original v1.5.2 plan. See previous Phase 6 content.)

Work items: `phase3_prompt()` iteration section adds MANDATORY INCREMENTAL WRITE STEP. Prompt-only in v1.5.2; runner-level checkpointing parked for v1.5.3+.

**Acceptance:** Scripted interrupt test — kill a chi iteration prompt after 2 minutes, verify `quality/code_reviews/<iteration>-candidates.md` has at least one candidate stub on disk.

---

## Phase 9 — Benchmark re-validation

Goal: confirm v1.5.2 recovers the RING_RESET family at cell coverage without regressing existing benchmark yields, and confirms reference_docs ingest works end-to-end.

Work items:
- Fresh `setup_repos.sh virtio chi cobra` → `virtio-1.5.2`, `chi-1.5.2`, `cobra-1.5.2`, now laying out `reference_docs/` + `reference_docs/cite/` instead of the old folders.
- `python3 bin/run_playbook.py virtio-1.5.2 chi-1.5.2 cobra-1.5.2 --full-run`.
- Diff `virtio-1.5.2/quality/BUGS.md` against `virtio-1.5.1/quality/BUGS.md` and `benchmark-1.4.5/virtio-1.4.5/quality/BUGS.md`.
- **Count cell coverage, not BUG entries.** virtio-1.5.2 success = every RING_RESET-family cell from the Phase 3 grid is in a BUG's `Covers:` field or a downgrade record. v1.4.5 had 6 cells in 3 BUGs; v1.5.2 should hit 6+ cells with `Covers:` annotation regardless of entry count.
- Chi and cobra bug counts within ±15% of v1.5.1 baselines.
- Bootstrap self-audit: run v1.5.2 against QPB itself; confirm gate passes (note: QPB's own `reference_docs/` is empty, so ingest should pass with 0 records).

**Acceptance:**
- virtio-1.5.2 cell coverage ≥ v1.4.5's 6 cells across the RING_RESET family
- virtio-1.5.2 retains the 8 bugs from v1.5.1 (or explicit rationale for any not reproduced)
- chi-1.5.2 and cobra-1.5.2 bug counts within ±15% of v1.5.1 baselines
- Bootstrap self-audit: gate passes
- reference_docs ingest: all three benchmarks produce a valid `formal_docs_manifest.json` (empty `records[]` is valid)

---

## Phase 10 — Council-of-Three review

Goal: three-model review (gpt-5.4, gpt-5.3-codex, claude-sonnet-4.6) of the v1.5.2 implementation before merge.

Work items:
- Prepare Council review prompt (follow template at `AI-Driven Development/Quality Playbook/Reviews/QPB_v1.5.2_Council_Review_Prompt.md` pattern; new prompt targets the implementation, not just the design).
- Run three `gh copilot` sessions in separate terminals, each spawning an internal three-reviewer panel.
- Synthesize responses. Store in `AI-Driven Development/Quality Playbook/Reviews/v1.5.2_implementation_responses/` (workspace, not QPB repo, to avoid GitHub exposure).
- Address any blocking concerns before merge; non-blocking concerns become v1.5.3+ backlog.

**Acceptance:** Council synthesis exists; no blocking concerns open.

---

## Phase 11 — Self-audit bootstrap

Goal: QPB v1.5.2 audits itself with full v1.5.2 machinery; artifacts committed as bootstrap evidence.

Same pattern as v1.5.0 and v1.5.1 Phase 8. Any bugs found go to v1.5.3 backlog.

**Acceptance:** bootstrap self-audit completes; `quality/` artifacts committed; any failures explicitly dispositioned.

---

## Phase 12 — Release

- Bump `version:` in `SKILL.md` to `1.5.2`.
- Update `CHANGELOG.md` with: reference_docs refactor (breaking), bug-family amplification (Levers 1-3), operational polish items, benchmark recovery evidence.
- Update `README.md` "What's new in v1.5.2" section.
- Update `ai_context/DEVELOPMENT_CONTEXT.md` with v1.5.2 bullet; remove the RING_RESET family from known-issues.
- Tag `v1.5.2`; merge `1.5.2` → `main`; push tag.

---

## Parking Lot (deferred from v1.5.2)

- Runner-level checkpointing (heartbeat files, resume tokens) — ships if Phase 8's prompt-only approach proves insufficient.
- Auto-inference of `pattern:` tag from code structure.
- Cross-requirement grid consolidation.
- AI-skills project-type classification — continues in v1.5.3.
- Optional first-line URL/retrieved-date comment for `cite/` files — only if adopters ask for Tier 2 audit trail beyond byte-verified citations.

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| reference_docs migration breaks a benchmark repo's existing artifacts | Medium | Phase 1i runs `quality_gate.py` against each migrated repo; any failures caught before Phase 2 begins. |
| Cartesian eligibility check under-fires (misses symmetric sets) | Medium | Reviewer can override by explicit UC emission; false-negative safer than false-positive. |
| Cell-identity `covers` field adoption is ceremonial (reviewer writes `covers: []` to silence gate) | Medium | Phase 5 gate explicitly aborts on empty `covers` for `pattern:`-tagged requirement BUGs; advisory Phase 3 self-check flags early. |
| Structured downgrade schema is too rigid; reviewers can't express legitimate downgrades | Medium | `reason_class` enum has five values covering common cases; if a downgrade doesn't fit, cell stays BUG (fail-safe direction). |
| TOOLKIT.md guidance isn't read by Cowork/Codex agents (they ignore it) | Low | AI agents using TOOLKIT.md already follow it for docs_gathered guidance; switching the target folder is a minimal behavioral change. |
| Phase 7 cell-coverage success criterion is gamed by reviewer auto-covering cells | Low | Council-of-Three review validates that each `covers:` annotation is legitimate; v1.4.5 reference data provides ground truth for RING_RESET family. |
| Benchmark variance produces false regression signal on chi/cobra | Medium | ±15% threshold; re-run 3× and use median if suspect. |

---

## Open Questions to Resolve

1. Should `reference_docs/cite/external/` be a sub-subfolder for Tier 2 material (to preserve internal Tier 1/2 distinction), or should everything in `cite/` be treated as Tier 1? Lean: flat `cite/` for MVP; add `external/` only if Council flags tier-conflict cases during v1.5.2 review.

2. Should `quality_gate.py` require `covers:` on every BUG produced from a `pattern:`-tagged requirement, or only on multi-cell consolidated BUGs? Lean: required on all pattern-tagged BUGs; single-cell BUG still writes `covers: [<single_cell_id>]` for uniform cardinality accounting.

3. How does `phase3_prompt()` signal when a grid cell is legitimately N/A (e.g., PCI-only feature bit on non-PCI transport)? Lean: `reason_class: "out-of-scope"` in a downgrade record; grid cell value becomes N/A after downgrade.

4. For benchmark repos that previously had `.meta.json` sidecars in `formal_docs/`, do we preserve the URL/version/date metadata anywhere? Lean: no — byte-verified citation replaces the audit trail the sidecars provided. If adopters ask for a per-file URL/retrieved annotation later, add an optional first-line comment parser.

5. Should the SKILL.md "missing reference_docs" message be printed once at Phase 1 start, or repeated in every phase that consumes context? Lean: once, at Phase 1 start. Repetition is noise.
