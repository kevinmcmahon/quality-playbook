# Regression Replay Cell Record — SCHEMA.md

> v1.5.4 Phase 4 (`docs/design/QPB_v1.5.4_Implementation_Plan.md`).
> Frozen for v1.5.4. Schema-breaking changes go to v1.5.5+ with a
> versioned bump; non-breaking additions go to v1.5.4.x.

## Purpose

The regression-replay apparatus runs current-QPB against historical
benchmark targets to measure recall against the benchmark's
historical bug list. Each invocation produces one **cell record** (a
JSON file) capturing what was run, what was found, and what changed
relative to the baseline.

A **calibration cycle** is a pair (or longer sequence) of cell
records: one before a `IMPROVEMENT_LOOP.md` lever was pulled, one
after. The cycle's diagnostic narrative lives in
`Lever_Calibration_Log.md` and cites the cell records by path.

The schema is a contract between three consumers:

1. `bin/regression_replay.py` (Phase 5) — writes cells.
2. `Lever_Calibration_Log.md` (Phase 6 onward) — cites cells.
3. The cross-benchmark regression check (Phase 8) — reads cells to
   confirm a lever change didn't degrade unrelated benchmarks.

If you're tempted to add a field that one consumer needs but the
other two don't, write it into a cell-local sidecar instead. The
schema's job is to keep the three consumers in agreement, not to
hold every fact about every run.

## File path convention

```
metrics/regression_replay/<run_timestamp>/<benchmark>-<version>-<bug_id>.json
```

- `<run_timestamp>` — UTC timestamp the apparatus started, in
  `YYYYMMDDTHHMMSSZ` form (matches the archive convention used by
  `quality/previous_runs/`). All cells from a single
  `bin/regression_replay.py` invocation share this prefix so
  before/after pairs co-locate naturally.
- `<benchmark>` — the benchmark project's short name (`chi`,
  `virtio`, `express`, `casbin`, etc.) — lowercase, hyphen-free.
- `<version>` — the historical QPB-target version of the benchmark
  the cell ran against (`1.3.45`, `1.3.50`, etc.). NOT the QPB
  version that produced the cell; see `qpb_version_under_test`
  below.
- `<bug_id>` — the historical bug ID this cell measures recall for
  (`BUG-001`, `BUG-007`). When a cell measures recall across the
  benchmark's full historical bug set rather than a single ID, use
  the literal `all` (e.g., `chi-1.3.45-all.json`).

Example: `metrics/regression_replay/20260501T120000Z/chi-1.3.45-all.json`.

The cells under one timestamped directory are append-only — once
the apparatus finishes writing them, they should not be edited. A
re-run of the same apparatus parameters writes a fresh timestamped
directory; comparing across timestamps is how the cross-benchmark
regression check works.

## Cell record JSON schema

```json
{
  "schema_version": "1.5.4",
  "timestamp": "2026-05-01T12:00:00Z",

  "benchmark": "chi",
  "qpb_version_under_test": "1.5.4",
  "historical_qpb_version": "1.3.45",

  "historical_bug_id": "all",
  "historical_bug_count": 10,
  "current_bug_count": 7,
  "current_bug_ids": ["BUG-001", "BUG-002", "BUG-003", "BUG-005", "BUG-007", "BUG-008", "BUG-010"],
  "recovered_bug_ids": ["BUG-001", "BUG-002", "BUG-003", "BUG-007", "BUG-008", "BUG-010"],
  "missed_bug_ids": ["BUG-004", "BUG-005", "BUG-006", "BUG-009"],
  "spurious_bug_ids": ["BUG-005"],
  "recall_against_historical": 0.6,

  "lever_under_test": "lever-2-pattern-tagging",
  "lever_change_summary": "Tightened Cartesian UC rule Gate 2 in references/exploration_patterns.md to require function-body line range similarity within 1.5x median (was 2x); intent: surface mounted-middleware family bugs the wider tolerance was clustering away.",
  "before_lever": null,
  "after_lever": "metrics/regression_replay/20260501T080000Z/chi-1.3.45-all.json",

  "regression_check": {
    "status": "clean",
    "checked_cells": [
      "metrics/regression_replay/20260501T120000Z/virtio-1.5.1-all.json",
      "metrics/regression_replay/20260501T120000Z/express-1.5.1-all.json",
      "metrics/regression_replay/20260501T120000Z/chi-1.5.1-all.json"
    ],
    "regressed_cells": [],
    "noise_floor_threshold": 0.05
  },

  "noise_floor_source": "single-run point estimate; σ unmeasured (acceptable for this 10→0 collapse — recall delta dwarfs σ floor of any plausible repeat-run distribution)",

  "apparatus": {
    "qpb_commit_sha": "abc123def456",
    "target_commit_sha": "deadbeefcafe1234",
    "phase_scope": "1,2,3",
    "iteration_strategies": [],
    "runner": "claude",
    "model": "sonnet",
    "wall_clock_seconds": 873
  },

  "notes": "Smoke cell — first end-to-end exercise of the apparatus per Phase 5 of the v1.5.4 Implementation Plan."
}
```

## Field reference

### Top-level identity (required)

| Field | Type | Semantics |
|-------|------|-----------|
| `schema_version` | string | This document's version. Set by the apparatus from `bin/benchmark_lib.RELEASE_VERSION` at write time. The reader checks it before parsing — major-version mismatch aborts. |
| `timestamp` | ISO-8601 UTC string with explicit `Z` | When the apparatus started this cell's run. Matches the directory `<run_timestamp>` (just in human-readable form). Use `datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")`. |
| `benchmark` | string | Short benchmark name, lowercase, hyphen-free. Same as the `<benchmark>` in the path. |
| `qpb_version_under_test` | string | The QPB version that produced this cell — read from `bin/benchmark_lib.RELEASE_VERSION` at apparatus invocation time. |
| `historical_qpb_version` | string | The benchmark target's historical version label (e.g., `1.3.45`). Same as the `<version>` in the path. This is the benchmark's own version label, NOT a QPB release. |

### Bug measurement (required)

| Field | Type | Semantics |
|-------|------|-----------|
| `historical_bug_id` | string | The historical bug ID this cell scopes to (`BUG-001`), or the literal `all` for cells measuring full-set recall. |
| `historical_bug_count` | int | Count of `### BUG-NNN` headings in the historical baseline `BUGS.md` for the benchmark+version. When `historical_bug_id` is a single ID, this is `1`. |
| `current_bug_count` | int | Count of `### BUG-NNN` headings in the produced `BUGS.md` from the current-QPB run. |
| `current_bug_ids` | array of string | Sorted list of `BUG-NNN` IDs current QPB found. |
| `recovered_bug_ids` | array of string | Subset of `current_bug_ids` that match the historical bug set's spec basis (same REQ + same code site, judged by the apparatus's mechanical matcher). The apparatus's matching contract is documented in `bin/regression_replay.py` — ID renumbering is normal between runs, so matching is by spec basis (`Primary requirement` + `Location`), not by literal ID. |
| `missed_bug_ids` | array of string | Subset of historical bug IDs NOT recovered. The complement of `recovered_bug_ids` against the historical set. |
| `spurious_bug_ids` | array of string | Subset of `current_bug_ids` that don't match any historical bug. NOT necessarily wrong — the current run may have surfaced real bugs the historical run missed. The apparatus reports them; calibration narrative judges them. |
| `recall_against_historical` | float in [0, 1] | `len(recovered_bug_ids) / historical_bug_count`. Two-decimal precision is enough; the apparatus stores the raw float and downstream consumers round for display. |

### Lever attribution (required, may be `null`)

| Field | Type | Semantics |
|-------|------|-----------|
| `lever_under_test` | string or `null` | The `IMPROVEMENT_LOOP.md` lever ID (`lever-1-...` through `lever-5-...`) the cell is measuring against. `null` means this is a baseline cell with no lever pulled — typically the "before" half of a calibration pair. |
| `lever_change_summary` | string or `null` | Human-readable one-paragraph description of the lever change. `null` only when `lever_under_test` is `null`. Format: short imperative noun-phrase + intent. The full diff lives in git history; this field is for cross-cell scanability. |
| `before_lever` | string or `null` | Path (relative to repo root) to the corresponding "before" cell. `null` for baseline cells. The apparatus enforces that before/after cells share the same `benchmark` + `historical_qpb_version` + `historical_bug_id`. |
| `after_lever` | string or `null` | Path to the corresponding "after" cell — the inverse of `before_lever`. Both fields exist so a cell can be cited from either direction without re-walking the directory. Symmetry: if cell A's `after_lever` points at B, then B's `before_lever` must point at A (apparatus-enforced). |

### Cross-benchmark regression check (required)

| Field | Type | Semantics |
|-------|------|-----------|
| `regression_check.status` | string enum: `"clean"`, `"regressed"`, `"skipped"` | `clean` = all check-set cells held recall within `noise_floor_threshold`. `regressed` = at least one fell. `skipped` = the apparatus didn't run the check (legal only on baseline cells; a "after_lever" cell with `skipped` is a workflow defect). |
| `regression_check.checked_cells` | array of string | Paths to the cells the regression check evaluated. Empty when `status == "skipped"`. |
| `regression_check.regressed_cells` | array of string | Subset of `checked_cells` whose recall fell by more than `noise_floor_threshold` against their before-lever counterpart. Empty when `status == "clean"`. |
| `regression_check.noise_floor_threshold` | float in [0, 1] | The recall delta below which a difference is treated as noise rather than regression. v1.5.4 default is 0.05 (5 percentage points); revisit when the apparatus has accumulated multi-run σ measurements per benchmark. |

### Apparatus reproducibility (required)

| Field | Type | Semantics |
|-------|------|-----------|
| `apparatus.qpb_commit_sha` | string | `git rev-parse HEAD` of the QPB repo at apparatus-invocation time. Required for re-running the cell with byte-identical apparatus code. |
| `apparatus.target_commit_sha` | string | `git rev-parse HEAD` of the benchmark target's checkout — the historical commit the cell measured against. |
| `apparatus.phase_scope` | string | The `--phase` argument passed to `bin/run_playbook.py` (e.g., `"1,2,3"`). Phase 5 of the design plan runs `--phase 1,2,3` for replay; later phases may extend. |
| `apparatus.iteration_strategies` | array of string | Iteration strategies run after the phases (e.g., `["gap", "unfiltered"]`). Empty for replay cells; iteration is generally overkill for replay measurement. |
| `apparatus.runner` | string | The CLI runner used (`claude`, `copilot`, `codex`, `cursor`). |
| `apparatus.model` | string | The model name passed to the runner, or empty string when the runner picked its default. |
| `apparatus.wall_clock_seconds` | int | Total wall-clock time the cell run took. Useful for capacity planning and as a sanity check against pathological hangs. |

### Free-form

| Field | Type | Semantics |
|-------|------|-----------|
| `noise_floor_source` | string | Free-form prose describing how the cell's recall measurement should be interpreted in noise terms. v1.5.4 cells use point estimates; future cells may aggregate multiple runs and quote σ here. The `Lever_Calibration_Log.md` cites this verbatim when a recall delta is on the edge of the noise floor. |
| `notes` | string, optional | Anything the apparatus or operator wants to surface but isn't worth a typed field. Empty string OK. |

## Calibration log entry shape

`Quality Playbook/Reviews/Lever_Calibration_Log.md` is the human-readable
narrative that turns cell records into a story. One H2 section per
cycle. Within each section, prose plus citations to the relevant
cell records.

```markdown
## Cycle N — <benchmark>-<version> <→ event> (YYYY-MM-DD)

**Symptom.** Plain-prose statement of what the apparatus showed
about current-QPB's behavior on this benchmark. Quote
`recall_against_historical` from the baseline cell.

**Diagnosis.** Which historical bugs were missed (cite `missed_bug_ids`
from the baseline cell). What category of failure they share (e.g.,
"all four are mounted-middleware bugs whose Cartesian UC clustering
collapsed them into a single umbrella UC"). Hypothesis about which
lever applies and why.

**Lever pulled.** Identify the lever from `IMPROVEMENT_LOOP.md`
(L1..L5). Quote the `lever_change_summary` from the after-cell.
Link the actual diff (commit SHA from the after-cell's
`apparatus.qpb_commit_sha`).

**Before / After.**

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Recall on `<benchmark>-<version>` | 0.40 | 0.70 | +0.30 |
| Cross-benchmark regression status | n/a (baseline) | clean | — |

Cite cell paths inline:

- Before: `metrics/regression_replay/<TS_BEFORE>/<benchmark>-<version>-all.json`
- After:  `metrics/regression_replay/<TS_AFTER>/<benchmark>-<version>-all.json`

**Verdict.** ship / hold-for-more-cycles / lever-pull-failed.
Two-sentence rationale. If `lever-pull-failed`, this is honest data,
not a defect — say so.
```

## What the apparatus does NOT capture

- **Per-bug confidence**. Whether QPB classified a bug as
  "confirmed-open" vs. "TDD-verified" doesn't move the recall
  numerator. If the calibration narrative needs that distinction,
  put it in prose; don't add a typed field.
- **Patch quality**. The apparatus measures bug discovery, not fix
  correctness. Cells don't carry patch deltas.
- **Per-phase timing**. `wall_clock_seconds` is the whole-cell time.
  If a cycle reveals a phase-specific perf concern, capture it in
  the calibration narrative or open a separate issue; don't widen
  the schema for one cycle's question.

## Versioning discipline

- **v1.5.4.x patch**: additive fields with safe defaults. Document
  the addition here AND bump `schema_version` to `"1.5.4.1"` etc.
- **v1.5.5+ minor**: breaking changes (renames, removals, type
  changes). Bump `schema_version` to `"1.5.5"` and write a migration
  note here naming the rename. The cross-benchmark regression check
  must read both old and new schemas (or operators must re-run
  baselines under the new schema before the lever change can ship).

The version string in `schema_version` is the schema's own version,
not a QPB release version. They start aligned at v1.5.4 because the
apparatus is being introduced now; they are free to diverge later.

## Smoke cell example (chi-1.3.45)

The Phase 5 deliverable in the v1.5.4 Implementation Plan is a
working `bin/regression_replay.py` that produces a valid cell.json
for chi at v1.3.45. The historical baseline has 10 bugs (`BUG-001`
through `BUG-010` in `repos/archive/chi-1.3.45/quality/BUGS.md`).
The example record at the top of this document is the shape that
deliverable must produce — populate every field, point
`historical_bug_id` at `"all"`, set `lever_under_test` to `null` for
the first baseline cell.

The first calibration cycle (Phase 6) is `chi-1.3.45 → 1.3.46`: the
known recall collapse from 10 bugs to ~0 between v1.3.45 and v1.3.46.
The "before" cell measures current QPB against v1.3.45 (high recall
expected because the bugs are obvious); the "after" cell measures
current QPB against v1.3.46 (where the same bugs have been fixed
and a different surface is exposed). The diagnostic narrative lives
in `Lever_Calibration_Log.md`; the cell records are the evidence
trail.
