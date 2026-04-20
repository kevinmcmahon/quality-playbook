# Quality Playbook v1.5.1 — Implementation Plan

*Companion to: `QPB_v1.5.1_Design.md`*
*Status: draft — to be reviewed and refined after v1.5.0 ships*
*Depends on: v1.5.0 complete (formal_docs pipeline, phase orchestrator, quality gate, schemas)*
*Followed by: `QPB_v1.5.2_Implementation_Plan.md` (skill-handling)*

v1.5.1 is scoped to operator experience. No changes to the divergence model, citation schema, tier taxonomy, or quality-gate mechanics — v1.5.0's correctness boundaries are preserved. Every change either reduces friction, increases observability, or both.

---

## Operating Principles

- **v1.5.1 is additive.** Every flag, file, and script added is optional. Existing v1.5.0 invocations continue to work unchanged (except where a bug is fixed, e.g., the `isatty()` echo gate).
- **Stdlib-only invariant.** No new dependencies. Python 3.10+ stdlib covers `termios`, `tty`, `msvcrt`, `threading`, `pathlib`, `json`, `subprocess`. No pip installs, no venv, no `requirements.txt`.
- **One deliverable per phase.** Each phase produces code, tests, and documentation that can ship independently if the later phases slip.
- **No regression on the code benchmark.** virtio / chi / cobra / express / httpx must continue to produce bug yields within ±10% of v1.5.0 baseline at every phase gate.
- **Cross-platform from day one.** Every feature is tested on macOS, Linux, and Windows. No "Unix first, Windows later" deferred work.

---

## Phase 0 — v1.5.0 Stabilization

Goal: v1.5.0 is shipped, tagged, and running clean on all five code benchmark repos. Bug yields documented as v1.5.1 baseline.

Work items:
- All v1.5.0 phases complete per `QPB_v1.5.0_Implementation_Plan.md`
- v1.5.0 tagged and released
- Benchmark baselines captured in `previous_runs/v1.5.0/`
- Any outstanding v1.5.0 gate failures dispositioned (fix / defer to v1.5.1 backlog / defer to v1.5.2)

Gate to Phase 1: v1.5.0 self-audit passes cleanly; no pending v1.5.0 bugs without dispositions; baseline bug yields recorded for regression comparison.

---

## Phase 1 — Operator-Flow Fixes

Goal: eliminate the runbook gap and the sidecar-authoring friction.

### Item 1.1 — Plaintext Staging

Work items:
- Extend `setup_repos.sh` with a `stage_formal_docs` step (or add a sibling `stage_formal_docs.sh` that `setup_repos.sh` calls at the end). For each repo in the benchmark, convert `docs_gathered/` content to plaintext in `formal_docs/`:
  - `.rst` → `.txt` via `docutils` equivalent; if `docutils` unavailable (stdlib-only constraint), strip RST directives with a minimal regex-based converter and document the lossiness.
  - `.html` → `.txt` via `html.parser` (stdlib) with tag stripping.
  - `.pdf` → **skip and warn**. PDF-to-plaintext is not stdlib-only; operator must convert manually. Pre-run guard (Item 1.3) catches this.
  - `.md`, `.txt` → passthrough.
- Per-repo converter config (tier assignments per filename pattern) lives in `repos.yml` or equivalent; the script reads it and invokes the setup helper (Item 1.2) after conversion.

Deliverable: staging script, per-repo config entries for all 5 benchmark repos, documented plaintext-conversion behavior per input format.

### Item 1.2 — Sidecar Auto-Setup

Work items:
- Add `bin/setup_formal_docs.py`. CLI:
  ```
  setup_formal_docs.py <formal_docs_dir> [--interactive] [--overwrite] [--manifest <path>]
  ```
- Heuristic tier assignment based on filename patterns:
  - Contains `rfc`, `spec`, `standard`, `behavioral` → Tier 1
  - Contains `guide`, `howto`, `tutorial`, `example` → Tier 2
  - Otherwise → default Tier 2, flagged in output for operator review
- Interactive mode prompts the operator per file (confirm / override tier / skip).
- Manifest mode reads a YAML/JSON file mapping filename → tier for deterministic regeneration.
- When a matching `.meta.json` sibling already exists, move the existing file to `formal_docs/.sidecar_backups/<timestamp>/<stem>.meta.json` before writing the new one. The timestamp is the setup-helper run time (basic ISO 8601 `YYYYMMDDTHHMMSSZ`). Backup directory is created on demand.
- Skip `README.md` (per v1.5.0 `formal_docs_ingest.py` convention).
- Output summary: N sidecars generated, M skipped (existing sidecars backed up), K flagged for review.

Deliverable: setup script (`bin/setup_formal_docs.py`), heuristic pattern list, test fixture covering each pattern class, benchmark repos staged cleanly via `setup_repos.sh` + the setup script.

### Item 1.3 — Pre-Run Guard

Work items:
- Add an early check in `run_playbook.py` (before Phase 1 begins): inspect target repo's `formal_docs/` and produce a loud warning if:
  - Directory is missing
  - Directory is empty
  - Directory contains plaintext files with no matching sidecars
- Warning format: multi-line banner with specific remediation command (`python3 bin/setup_formal_docs.py <path>`) and reference to the staging step in `setup_repos.sh`.
- `--no-formal-docs` flag suppresses the warning for self-audit bootstrap and minimal-repo cases. Flag is recorded in the run manifest.

Deliverable: guard implementation, test coverage for each warning condition, `--no-formal-docs` flag.

Gate to Phase 2: benchmark repos run cleanly end-to-end via `setup_repos.sh` → `run_playbook.py` with zero manual file editing between steps. Phase 0 baseline bug yields reproduce on the new staging pipeline.

---

## Phase 2 — Observability Overhaul

Goal: make runs visible without operator ceremony.

### Item 2.1 — Built-In Logging + Unbuffered Console

Work items:
- Add `configure_logging(repo_dir, timestamp)` to `run_playbook.py` that:
  - Computes canonical log path via existing `log_file_for()`
  - Opens the log file for append
  - Prints the log path to stdout as the first line of run output
  - Installs line-buffered stdout (`sys.stdout.reconfigure(line_buffering=True)`)
- Remove the `isatty()` echo gate from `logboth()` in `benchmark_lib.py`. `logboth` unconditionally writes to both the log file and stdout.
- Tests: run with and without stdout piped through tee; verify identical content in both the built-in log and the tee'd log; verify no silent gaps.

Deliverable: updated `run_playbook.py` and `benchmark_lib.py`, test coverage for piped/unpiped invocations, documentation update removing tee ceremony from canonical invocation.

### Item 2.2 — Live Progress Monitor

Work items:
- Add a background monitor thread that:
  - Polls `quality/PROGRESS.md` at 2-second intervals (stdlib `pathlib.Path.stat()` → `st_mtime`)
  - On modification, reads new content since last poll
  - Prints any `#` or `##` headers that appear in the new content
- `--verbose` flag adds a second monitor that tails the current phase's live transcript file (the per-phase output file written by `run_prompt()`). Transcript tail prints all new lines, not just headers.
- `--quiet` flag suppresses both monitors; only phase-boundary announcements from `run_playbook.py` itself print.
- Thread shuts down cleanly at run end or on `Ctrl-C`.

Deliverable: monitor implementation with clean thread lifecycle, `--verbose` and `--quiet` flags, test coverage verifying header-only vs. full-transcript streaming.

### Item 2.3 — Cross-Platform Command Recipes in Startup Banner

Work items:
- Add a `print_startup_banner()` helper in `run_playbook.py` that emits a single block at run start containing:
  - The absolute path to the run log file (from Item 2.1)
  - Platform-appropriate "watch from another terminal" commands for the log, the live phase transcript, and `PROGRESS.md`
  - The run plan (from Item 3.2)
- Platform detection via `platform.system()`:
  - `Darwin` / `Linux` → `tail -f` for log + transcript, `watch -n 2 'grep "^##\\?" <PROGRESS.md>'` for progress
  - `Windows` → `Get-Content <path> -Wait -Tail 20` for log + transcript, `Get-Content <path> -Wait | Select-String '^##?'` for progress
  - Other → print the Unix recipes with a note that they may need adjustment
- All paths in the banner are absolute so operators can copy-paste directly.
- Banner is written once at run start, goes to both stdout and the built-in log file.

**Explicitly out of scope for Item 2.3** (per design doc Parking Lot): keystroke-based mode switching. No `termios`, no `msvcrt`, no TTY detection gating. Operators who want a different observability mode relaunch with different flags.

Deliverable: startup banner implementation with platform-aware command recipes, verified output on macOS / Linux / Windows PowerShell.

Gate to Phase 3: virtio rerun with `--verbose` produces continuous observable output with no silent gaps >30s. Startup banner prints correct, copy-paste-ready commands on each supported platform.

---

## Phase 3 — Invocation Flexibility

Goal: flexible phase bundling and unified phase + iteration invocation.

### Item 3.1 — `--phase-groups`

Work items:
- Extend argument parser with `--phase-groups "<spec>"` where `<spec>` is `group1,group2,…` and each group is `N` or `N+N+…`.
- Validation:
  - Phase IDs in 1–7
  - Groups in ascending order (`3+2` rejected)
  - No duplicate phase IDs across groups (phase can't appear twice)
  - Empty groups rejected
- Extend `run_one_phased()` / dispatcher at line 952 to iterate over groups instead of phases. For a multi-phase group, call `build_phase_prompt()` once per phase and concatenate prompt bodies with group-scoped headers.
- `--phase all` becomes sugar for `--phase-groups "1,2,3,4,5,6,7"`.
- `--phase N` remains supported; internally becomes `--phase-groups "N"`.
- Mutual exclusion: `--phase-groups` vs. `--phase` (redundant), `--phase-groups` vs. `--full-run` (redundant); `--phase-groups` vs. `--next-iteration` **allowed** (see Item 3.2).

Deliverable: `--phase-groups` parser + dispatcher, per-phase prompt concatenation, test coverage for single-group / multi-group / full-set invocations, no regression on `--phase N` behavior.

### Item 3.2 — Unified `--phase-groups` + Iterations

Work items:
- Loosen the mutual-exclusion constraint between `--phase-groups` and iteration flags. New flag: `--iterations "strat1,strat2,…"` where each strat is one of `gap`, `unfiltered`, `parity`, `adversarial`.
- Orchestrator executes phase groups first, then iteration strategies. Early-stop-on-zero-gain semantics apply between iteration strategies (existing behavior preserved).
- Add `--pace-seconds N` (default 0) inserting a sleep between phase groups and between iteration strategies.
- Print run plan at start:
  ```
  Plan:
    Phase group 1      (phase 1)
    Phase group 2      (phase 2)
    …
    Iteration: gap
    Iteration: unfiltered
    …
    Pace:      Ns between prompts
    Log:       <path>
  ```
- Log file captures the plan as the second block after the "Writing run log to" banner.
- `--full-run` remains supported as sugar for `--phase-groups "1,2,3,4,5,6,7" --iterations "gap,unfiltered,parity,adversarial"`.

Deliverable: unified invocation, plan printer, pace implementation, test coverage for full plan execution with early-stop semantics verified, `--full-run` equivalence check.

Gate to Phase 4: a single `run_playbook.py` invocation with `--phase-groups "1,2,3+4,5+6,7" --iterations "gap,unfiltered,parity,adversarial" --pace-seconds 60` runs the complete 11-prompt sequence end-to-end with correct pacing, correct early-stop, accurate logging, and produces the same artifacts as the equivalent two-command v1.5.0 workflow.

---

## Phase 4 — Benchmark Validation

Goal: run v1.5.1 against all five code benchmark repos and verify no regression.

Work items:
- Run `setup_repos.sh` (with staging) → `run_playbook.py` for each benchmark repo using the canonical v1.5.1 invocation (`python3 bin/run_playbook.py … --phase-groups "1,2,3+4,5+6,7" --iterations "gap,unfiltered,parity,adversarial"`).
- Compare bug yields to the v1.5.0 baseline captured in Phase 0. Tolerance: ±10% per-repo, ±5% aggregate.
- Cross-platform sanity check: the same invocation runs cleanly on macOS + Linux + Windows. Verify progress monitor and keystroke controls behave correctly on each.
- Produce a comparison report: v1.5.0 baseline vs. v1.5.1 for each repo, plus cross-platform notes.

Deliverable: comparison report at `previous_runs/v1.5.1/v1.5.0_vs_v1.5.1_comparison.md`, cross-platform notes, go/no-go decision.

Gate to release: all five benchmark repos pass the ±10% regression bar; cross-platform test matrix is green or documented exceptions.

---

## Phase 5 — Self-Audit Bootstrap

Goal: QPB v1.5.1 audits itself with full v1.5.1 machinery, artifacts committed as bootstrap evidence.

Same pattern as v1.5.0 Phase 8. Because v1.5.1 is purely additive operator-experience work, the self-audit should produce requirements coverage and bug yield comparable to v1.5.0's self-audit. New UX-related REQs may appear (logging behavior, observability flags, setup-helper behavior); these become v1.5.1 REQs tagged appropriately.

Any bugs found go to v1.5.1 post-release patch backlog or v1.5.2 backlog depending on severity.

Deliverable: v1.5.1 self-audit complete, artifacts in `quality/` and archived to `previous_runs/v1.5.1/`.

Gate to release: self-audit completes cleanly OR any failures are explicitly dispositioned.

---

## Release

- Tag v1.5.1
- Update release notes citing:
  - The overnight benchmark failure as runbook-gap evidence
  - Andrew's specific feedback items as design drivers
  - The `isatty()` gate removal as the observability correctness fix
- Update `SKILL.md` to reflect the new canonical invocation (no tee ceremony)
- Update `docs/` with the staging + setup workflow
- Start v1.5.2 work (skill-handling per `QPB_v1.5.2_Implementation_Plan.md`)

---

## Parking Lot (deferred from v1.5.1)

- **Remote run monitoring** (watch a run from a different machine via web dashboard or SSH tunnel)
- **Adaptive rate-limit backoff** (retry with exponential backoff on rate-limit errors instead of hard-failing)
- **PDF-to-plaintext conversion** (stdlib-only doesn't cover it; document as manual step; revisit if a stdlib-compatible approach emerges)
- **Non-English filename heuristics for the setup helper**
- **curses-based progress dashboard** (full-screen multi-pane observability; current design is line-oriented)
- **Keystroke-based observability mode switching** (deferred per design-doc rationale: real AI-sandbox stdin risk, cross-platform test burden, value small relative to cost. Revisit if real usage reveals demand for mid-run mode toggling)
- **LLM-based sidecar tier inference** (use a small model to infer tier from file content; contradicts stdlib-only and adds per-file LLM cost)
- **Web UI for run configuration and monitoring** (out of scope; CLI is the contract)

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| `isatty()` gate removal breaks an AI-sandbox invocation we haven't tested | Low | Add an explicit `--no-stdout-echo` escape hatch; default to echo-everywhere but preserve an opt-out |
| Setup-helper heuristic misfires on edge-case filenames | Medium | Interactive mode prompts for confirmation; manifest mode allows deterministic override; backup-before-regenerate ensures no operator work is ever lost |
| `--phase-groups` concatenation produces prompts too large for a single LLM call | Medium | Document per-group token estimates; operator picks smaller groups if rate-limited. Could add an auto-split fallback if prompts exceed a threshold |
| Progress monitor thread leaks on abnormal termination | Low | `threading.Event`-based shutdown; `try/finally` in orchestrator main |
| Cross-platform test matrix too expensive to maintain | Low (reduced scope) | With keystroke mode deferred, cross-platform surface is just the startup-banner commands and line-buffered stdout — both stdlib-stable and easy to verify |
| `--pace-seconds` interacts badly with long-running phases (operator thinks the run hung during a pace wait) | Low | Progress monitor prints a heartbeat line during pace sleeps (`Pacing: 60s before next prompt…`) |
| Backup subdirectory `.sidecar_backups/` accumulates stale timestamped subfolders over many setup-helper runs | Low | Document manual pruning; consider a `--prune-backups-older-than N` flag as a v1.5.1 post-release patch if it becomes real friction |

---

## Open Questions to Resolve

These need answers during implementation but don't block planning:

1. (Item 1.1) Does v1.5.0's `setup_repos.sh` live in the QPB repo or in a sibling benchmarks repo? Check repo layout before extending.
2. (Item 1.2) Should the setup helper's heuristic pattern list live in code or in a config file? Lean: config file at `bin/setup_formal_docs_patterns.yml` for easy extension without code changes.
3. (Item 2.1) Is `sys.stdout.reconfigure(line_buffering=True)` available on all supported Python versions? Python 3.7+ yes. Verify minimum version target in `SKILL.md`.
4. (Item 2.2) What's the right polling interval for the progress monitor? 2 seconds is responsive enough for human observation; 1 second feels busier; 5 seconds feels slow. Lean: 2s default, `--progress-interval N` flag for tuning.
5. (Item 3.1) Should phase-group headers in the concatenated prompt be visible in the LLM's eyes (aiding context) or hidden (reducing token cost)? Lean: visible, minimal (single line with group spec).
6. (Item 3.2) When `--pace-seconds` is non-zero, should the pacer print a countdown or a single "Pacing: Ns" message? Lean: single message; countdown clutters logs.

---

## Plan Revision Expectations

This plan is provisional. Revisit after Phase 0 closes with:

- Actual v1.5.0 schema / orchestrator shape, which may affect Item 1.3 guard integration
- Any `setup_repos.sh` refactors that change where staging logic belongs
- Cross-platform testing surprises (especially Windows PowerShell `Get-Content -Wait` behavior with rapidly-rotating files)
- Updated benchmark bug yields if v1.5.0 stabilization changes them

The review pass should update this document in place (no separate revision log needed; git history captures changes).
