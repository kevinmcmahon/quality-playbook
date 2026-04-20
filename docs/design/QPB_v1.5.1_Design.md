# Quality Playbook v1.5.1 — Design Document

*Status: design captured, awaiting v1.5.0 completion before implementation*
*Authored: April 2026*
*Owner: Andrew Stellman*
*Depends on: `QPB_v1.5.0_Design.md` (formal_docs pipeline, plaintext + sidecar convention, phase orchestrator, quality gate)*
*Predecessor of: `QPB_v1.5.2_Design.md` (skill-handling)*

## Purpose of This Document

v1.5.1 addresses a category of friction that v1.5.0 surfaced but did not solve: operator experience. The playbook is correct on the benchmark but painful to run. Every sharp edge discovered during the v1.5.0 overnight benchmark campaign and the subsequent manual re-staging becomes a design item here.

This doc captures the problems, the root causes, and the design for fixing them. A companion file `QPB_v1.5.1_Implementation_Plan.md` covers execution.

**Sequencing note.** v1.5.2 (skill-handling) builds on v1.5.1, not the other way around. The operator-flow pain this document addresses will compound with v1.5.2's additional skill-classification and four-pass derivation complexity; fixing it first means v1.5.2 can be built and benchmarked without also fighting the runner. v1.5.2's Phase 0 gate ("v1.5.0 Stabilization" in its plan as currently written) should in practice read as "v1.5.1 Stabilization" once v1.5.1 ships — the schema in v1.5.2's Phase 2 extends the v1.5.1 schema that inherits from v1.5.0.

---

## The Gap — Evidence

### The overnight benchmark failure (2026-04-18)

The v1.5.0 overnight run on five benchmark repos (virtio, chi, cobra, express, httpx) completed without errors but produced systematically bad outputs: all five repos reported Spec Gap, `citation_semantic_check.json` was empty across the board, and 100% of derived REQs were classified as Tier 3. The runs technically passed the gate but produced no v1.5.0 divergence content — the whole reason v1.5.0 existed.

Root cause on investigation: `setup_repos.sh` places RFC/spec plaintext into `docs_gathered/`, but nothing in the v1.5.0 pipeline converts `docs_gathered/` content into `formal_docs/` with the required plaintext + `.meta.json` sidecar layout. The plaintext staging step is documented as an operator responsibility in the prose of `SKILL.md` but is neither automated nor surfaced by any scaffold. Five of five repos fell into the gap silently.

This is a **runbook gap**: the playbook has an implicit prerequisite that is neither automated nor loud enough for an operator to notice before the run starts.

### The manual virtio re-staging (2026-04-19)

Manually staging virtio required creating three plaintext files (`virtio.txt`, `writing_virtio_drivers.txt`, `virtio-spec-behavioral-contracts.md`) and three matching `.meta.json` sidecars. Writing the sidecar JSON by hand — even with only `tier` required — is irritating per-file work that scales linearly with formal_doc count and carries no value beyond satisfying the parser. Andrew's direct feedback: "just providing a bunch of json files is also real friction."

### The rerun observability gap (2026-04-19)

The virtio rerun used a phase-by-phase invocation (`--phase all`) to distribute rate-limit pressure. During the run:

- The orchestrator produced no console output for minutes at a stretch. Python's stdout block-buffering when piped through `tee`, combined with `logboth()`'s `isatty()` echo gate, silently suppressed all visible progress. Operators couldn't distinguish "running normally" from "hung."
- `PROGRESS.md` appeared halted because it's only updated at phase boundaries, not continuously. The live phase transcript (written by the orchestrator to a per-phase output file) carried the real-time signal but was not surfaced anywhere in the invocation UX.
- Watching progress required opening a second terminal and running `tail -f` or `fswatch` recipes manually — cross-platform complexity the operator has to remember while a 15M-token run is in flight.

### The invocation-control gap

For rate-limit-conscious runs, operators want fine-grained control over how many prompts to burn: sometimes one prompt per phase (conservative), sometimes one prompt for two bundled phases (when prior phases have low token count), sometimes the full multi-phase run plus iterations in one invocation. v1.5.0's `run_playbook.py` parser treats `--phase`, `--next-iteration`, and `--full-run` as mutually exclusive — a correct constraint for its current design but one that forces operators into two-command workflows ("run phases, wait, then run iterations") that risk forgetting step two or producing inconsistent state if step two is forgotten.

### The tee ceremony

v1.5.0's canonical run command looked like:

```
PYTHONUNBUFFERED=1 python3 -u bin/run_playbook.py ... 2>&1 | tee some-logfile.log
```

Every component of that ceremony is necessary: `PYTHONUNBUFFERED=1` / `-u` to defeat block-buffering when piped, `tee` to capture a log that the orchestrator ought to be writing itself, `2>&1` to merge stderr into the log. The orchestrator already knows the run's timestamp and target repo — it has every piece of information needed to write its own timestamped log file. Asking the operator to supply all of this at the shell is v1.5.0 pushing responsibility outward that belongs inward.

---

## Root Cause — Why v1.5.0 Ships With These Sharp Edges

v1.5.0 optimized for correctness on the benchmark. That was the right priority: without divergence working, operator-flow improvements don't matter because the tool has no value. With v1.5.0 correct, the operator experience is the next-most-important thing between the tool and adopters.

Three specific v1.5.0 decisions created the current friction:

1. **Plaintext staging was deferred.** The formal_docs pipeline assumes plaintext + sidecars exist. The conversion from arbitrary RFC/spec formats (HTML, PDF, reST, Markdown) to plaintext was pushed to operator responsibility with the assumption that operators would handle it manually per-repo. The `setup_repos.sh` script stops at `docs_gathered/` — one layer short of what the pipeline needs. No pre-run check loudly warns "formal_docs/ is empty, did you run the staging step?"

2. **Sidecar JSON was a convention, not a scaffold.** The `.meta.json` file format was chosen for parse simplicity (plain JSON, no new DSL, stdlib-only) but no tool was built to generate it. Every sidecar is authored by hand. The format is small today (only `tier` required), but the friction still dominates because it's per-file manual work.

3. **Orchestrator observability followed the "AI runs this, not a human" assumption.** The `logboth()` function's `isatty()` gate is correct for AI-sandbox execution (don't print to non-existent TTY) but subtly wrong for the human-in-terminal case (operator sees nothing when piping through tee for log capture). The logging architecture assumed the operator would be either (a) an AI with no TTY or (b) a human watching a plain TTY — not (c) a human watching a TTY that's piped into tee for durability.

These decisions were defensible at v1.5.0 scope. v1.5.1 revisits them now that v1.5.0 ships.

---

## Design — The Seven UX Items

Seven items, grouped into three phases by nature of the fix.

### Item 1: Plaintext Staging Runbook Gap (Phase 1)

**Problem.** `docs_gathered/` populates but `formal_docs/` does not; operator must manually convert.

**Design.** Two complementary fixes:

- **Automated conversion.** Extend `setup_repos.sh` (or add a sibling `stage_formal_docs.sh`) with a converter that reads `docs_gathered/`, converts each file to plaintext (`.txt` for `.rst`, `.html`, `.pdf`; passthrough for `.md`, `.txt`), and writes the output to `formal_docs/`. Sidecar scaffolding (Item 2) handles the `.meta.json` generation.
- **Pre-run guard.** Add a check early in `run_playbook.py` that inspects `formal_docs/` and, if empty or missing, emits a loud warning with the exact command to run and an explicit pointer to `docs_gathered/`. The warning is loud enough to notice but does not block the run — some runs legitimately have no formal docs (minimal repos, self-audit bootstrap).

**Why both.** Automation prevents the common case; the guard catches edge cases where the operator has an exotic staging flow or a format the converter doesn't handle. The guard is the last line of defense against silent Spec Gap runs.

### Item 2: Sidecar Auto-Scaffolding (Phase 1)

**Problem.** Writing `.meta.json` by hand is per-file friction with no operator value.

**Design.** Add a `bin/scaffold_formal_docs.py` script (or a subcommand of an existing CLI) that:

1. Scans a target directory for supported plaintext files (`.txt`, `.md` per v1.5.0 `schemas.md` §2) that lack sibling `.meta.json` sidecars.
2. For each, generates a sidecar with `tier` populated via a heuristic: filename-pattern matching against known markers (`rfc`, `spec`, `standard` → Tier 1; `guide`, `howto`, `tutorial` → Tier 2; otherwise a prompt or a default).
3. Optional interactive mode: prompts the operator to confirm each tier assignment.
4. Optional batch mode with a manifest file specifying tier per-file for deterministic regeneration.

**Scope discipline.** This is a scaffolder, not a magic inferencer. The sidecar only needs `tier`; optional fields (`version`, `date`, `url`, `retrieved`) are left blank for the operator to fill in if they want. The heuristic is explicit and adjustable; there is no LLM call.

**Integration.** The staging pipeline in Item 1 calls the scaffolder by default. A plain operator workflow becomes: drop plaintext files in `formal_docs/`, run the scaffolder, edit tiers if the heuristic is wrong, proceed to run.

### Item 3: Built-In Logging + Unbuffered Console (Phase 2)

**Problem.** The tee ceremony is ceremony. Operators shouldn't have to remember `PYTHONUNBUFFERED=1`, `-u`, `2>&1`, and a hand-picked log filename.

**Design.**

- **`run_playbook.py` opens its own log file.** At run start, it computes a canonical path using the same naming convention as `log_file_for()` (`{parent}/{repo-name}-playbook-{timestamp}.log`) and opens it for append. All `log()` and `logboth()` output goes to this file unconditionally.
- **Stdout unconditionally echoes log content.** Remove the `isatty()` gate from `logboth()`. The orchestrator always writes to both the log file and stdout, and never second-guesses whether the operator can see stdout.
- **Unbuffered stdout by default.** Invoke `sys.stdout.reconfigure(line_buffering=True)` on entry, or detect piped-stdout and switch to line-buffering explicitly. Equivalent to `-u` / `PYTHONUNBUFFERED=1` but built in.
- **Announce the log path at start.** The first line of console output is `Writing run log to: <absolute path>` so the operator knows where durable output lives without having to find it.

**Backward compatibility.** Operators who already pipe through tee continue to work; the built-in log and the tee'd log will be identical content. Guidance in documentation moves from "you must pipe through tee" to "you can optionally pipe through tee; the playbook already writes its own log."

**AI-sandbox safety.** The removal of the `isatty()` gate is safe because AI sandboxes either have a TTY (Claude Code) or a capturing parent process that will collect stdout anyway. The gate was solving a non-problem.

### Item 4: Live Progress Monitor (Phase 2)

**Problem.** `PROGRESS.md` updates only at phase boundaries; the live phase transcript is where real-time signal lives but isn't surfaced.

**Design.**

- **Default mode.** Print `#` and `##` headers from `PROGRESS.md` to the console as they're written, using a file watcher (stdlib `os.stat` polling, 2-second interval — no `fswatch` / `inotify` dependency). Operator sees phase-level progress without doing anything.
- **`--verbose` mode.** Additionally tail the current phase's live transcript file (the per-phase output file `run_prompt()` writes to) and stream it to the console.
- **`--quiet` mode.** Suppress all stdout echo except startup banner, phase boundaries, and errors. For operators who want a clean log file.

**Implementation.** A background thread in `run_playbook.py` polls `PROGRESS.md` and the active phase transcript file, printing new content as it appears. No external dependency; stdlib `threading` + `time.sleep` + `pathlib.Path.stat()`.

**Interaction with Item 3.** The progress monitor writes to the same stdout stream that gets echoed to the canonical log file. Console output and log file content remain identical.

### Item 5: Cross-Platform Command Recipes in Startup Banner (Phase 2)

**Problem.** Operators who want to watch a run from a second terminal need to remember platform-specific commands (`tail -f` on Unix, `Get-Content -Wait` on Windows) for the log file, the live phase transcript, and `PROGRESS.md`. The commands are short but the operator is busy watching a 15M-token run; reaching for documentation or Stack Overflow mid-run is its own friction.

**Design.** At run start, `run_playbook.py` prints a block in the startup banner listing the platform-appropriate commands for watching each artifact. The block is detected by `platform.system()` and contains:

- macOS / Linux:
    ```
    Watch from another terminal:
      Log:         tail -f <absolute log path>
      Transcript:  tail -f <absolute phase transcript path>
      Progress:    watch -n 2 'grep "^##\\?" <absolute PROGRESS.md path>'
    ```
- Windows PowerShell:
    ```
    Watch from another terminal:
      Log:         Get-Content <absolute log path> -Wait -Tail 20
      Transcript:  Get-Content <absolute phase transcript path> -Wait -Tail 20
      Progress:    Get-Content <absolute PROGRESS.md path> -Wait | Select-String '^##?'
    ```

**Why this is Item 5's whole scope.** Keystroke-based observability mode switching was considered and deferred. It adds stdlib keystroke handling (`termios` + `tty` on Unix, `msvcrt` on Windows), TTY detection, per-platform test burden, and genuine AI-sandbox risk (non-TTY stdin could block the main thread). The value — toggling observability modes without restarting — is small relative to the cost; operators who want a different mode can relaunch with different flags. Deferred to the Parking Lot; revisit if real usage reveals demand.

**Cross-platform command recipes live in the code, not in prose docs.** The startup banner is the canonical source for "how do I watch this run from another terminal?" — it prints the right command for the operator's platform. Doc prose references the banner rather than duplicating the commands.

### Item 6: `--phase-groups` for Flexible Phase Bundling (Phase 3)

**Problem.** Operators want per-phase prompt control (one prompt per phase for heavy phases, one prompt per several phases for light phases), but v1.5.0's parser offers only `--phase N`, `--phase all`, and `--full-run`.

**Design.** Add `--phase-groups` as an alternative to `--phase`. Syntax:

```
--phase-groups "1,2,3+4,5+6,7"
```

Each group runs as a single prompt; groups separated by commas run sequentially. Legal group elements are phase IDs (1–7) joined with `+`. Validation rejects out-of-order groups (`3+2`) and unknown phase IDs.

The orchestrator's `build_phase_prompt()` is extended to handle multi-phase group prompts by concatenating per-phase prompt bodies with group-scoped headers and a merged Phase 0 setup block.

**Backward compatibility.** `--phase 3` continues to work identically; `--phase-groups "3"` is the equivalent. `--phase all` becomes sugar for `--phase-groups "1,2,3,4,5,6,7"`. The existing mutual-exclusion constraints (`--phase-groups` vs. `--full-run`, `--phase-groups` vs. `--next-iteration`) remain.

### Item 7: Unified `--phase-groups` + Iterations Invocation (Phase 3)

**Problem.** v1.5.0 forces a two-command workflow (phases first, iterations second). Operators forget step two or produce inconsistent state if they swap in a different repo between steps.

**Design.** Loosen the mutual-exclusion constraint to allow `--phase-groups` plus `--iterations`:

```
--phase-groups "1,2,3+4,5+6,7" --iterations "gap,unfiltered,parity,adversarial"
```

The orchestrator runs each phase group in sequence, then runs each iteration strategy in sequence, respecting the existing early-stop-on-zero-gain semantics between iteration strategies. All of it is one invocation producing one canonical log file.

**Rate-limit pacing.** Add `--pace-seconds N` (default 0) that inserts a sleep between phase groups and between iteration strategies. Operators worried about per-minute rate limits can set `--pace-seconds 60`; operators on burst-friendly rate limits can leave it at 0.

**Combinatorics sanity.** `--phase-groups` + `--iterations` + `--pace-seconds` produces a fully-specified declarative run plan. The orchestrator prints the plan at start:

```
Plan:
  Phase group 1      (phase 1)
  Phase group 2      (phase 2)
  Phase group 3+4    (phases 3,4)
  Phase group 5+6    (phases 5,6)
  Phase group 7      (phase 7)
  Iteration: gap
  Iteration: unfiltered
  Iteration: parity
  Iteration: adversarial
  Pace:      60s between prompts
  Log:       /path/to/virtio-playbook-20260420T140000Z.log
```

Operator sees the full scope before anything executes.

---

## Success Criteria

v1.5.1 is successful if:

1. **Runbook gap closed.** A fresh repo cloned from `setup_repos.sh` + `stage_formal_docs.sh` runs cleanly through v1.5.0 with no manual file editing. The five benchmark repos (virtio, chi, cobra, express, httpx) produce the v1.5.0 expected bug yield with no operator intervention between clone and run.

2. **Sidecar friction eliminated.** For each benchmark repo, the sidecar scaffolder produces correct tier assignments on its heuristic in ≥80% of cases, or operator-interactive mode completes tier assignment in <60 seconds per repo.

3. **No silent runs.** The `logboth()` `isatty()` gate is removed and no run-playbook invocation produces a period longer than 30 seconds of no stdout output under normal operation. (Exception: LLM thinking time, but the heartbeat from Item 4's progress monitor fills gaps.)

4. **Tee ceremony eliminated.** The canonical v1.5.1 invocation is `python3 bin/run_playbook.py …` with no surrounding ceremony. The built-in log matches the content that `tee` would have captured.

5. **Progress is visible.** A run of virtio with `--phase-groups "1,2,3+4,5+6,7"` produces console output at every phase boundary, plus (in `--verbose`) transcript tail output during each phase. Operators can identify the current phase and its approximate progress without opening a second terminal.

6. **Platform-appropriate command recipes appear in the startup banner.** macOS and Linux runs print `tail -f` / `watch` forms; Windows runs print `Get-Content -Wait` / `Select-String` forms. Recipe paths are absolute so operators can copy-paste into a second terminal directly.

7. **`--phase-groups` + `--iterations` runs in one invocation.** A full 11-prompt run (7 phase groups + 4 iteration strategies) completes as a single `run_playbook.py` invocation with accurate per-step logging and a correct early-stop on zero-gain iterations.

8. **No regression on code benchmarks.** Bug yield on virtio / chi / cobra / express / httpx within ±10% of v1.5.0 baseline. The five benchmark repos that ran cleanly on v1.5.0 must also run cleanly on v1.5.1.

---

## Provenance

### The overnight benchmark campaign (2026-04-18 → 2026-04-19)

The v1.5.0 overnight run across five repos produced systematically bad outputs and triggered the diagnostic work that surfaced the runbook gap. Raw artifacts live at `~/Documents/QPB/previous_runs/v1.5.0/2026-04-18-overnight/`. The diagnostic conversation is preserved in the Cowork session transcript for 2026-04-18 → 2026-04-19.

### Andrew's feedback during the virtio re-staging (2026-04-19)

Key quotes driving the design:

- On sidecar authoring: *"yes, that's real friction, and just providing a bunch of json files is also real friction. we'll do this run now, but we need to talk about adding a feature to 1.5.0 to let users just dump their files into a folder and have it scan it and create its own sidecars."*
- On phase granularity: *"the main pass will still be very heavy, is it possible to split up the main pass into its separate phases? i don't love burning 11 prompts for this, but i want to be careful about rate limiting for now."*
- On combined invocation: *"for all those 7 to 10 prompts, do i need to issue it in two separate commands, one for the phases and the other for the iterations? is it possible to combine them?"*
- On built-in logging: *"maybe we should include in 1.5.1 a modification to `run_playbook.py` so that it prints its output to the console and also writes it to a timestamped file in the right location, so we don't have to mess with 'tee' — and it can print the filename at the beginning of the run so the user knows."*
- On progress visibility: *"it would be great to give more status output so the user knows it's running. it doesn't have to be too verbose (but it would be really good to add a --verbose option), but it should tell them what it's doing as it goes so they know it's progressing. i wonder if we can have it monitor PROGRESS.md and print # and ## headers as they get generated."*
- On cross-platform observability: *"this is the kind of observability that people want while their runs are executing. we should find a way to give them these options. is it possible with cross-platform python to let them switch between observability modes in real time by pressing a key? or is reading console keystrokes a bad idea because it could mess with AI sandbox runs? we could also print commands for them to use, although we will need to show powershell commands and not unix commands for windows."*

Each item in this design traces to a specific piece of that feedback; none is invented.

### The tee + Python buffering discovery

The `isatty()` gate in `logboth()` was discovered while diagnosing the silent virtio rerun on 2026-04-19. Invocation was:

```
python3 -m bin/run_playbook.py … 2>&1 | tee virtio-run.log
```

Console output was empty for minutes. Investigation revealed two concurrent causes: Python's stdout block-buffering when piped (fixable with `-u`), and `logboth()`'s deliberate echo suppression when `sys.stdout.isatty()` returns false (which it does when piped through tee). The `-u` flag partially fixed it but the echo gate remained — content was in the log file but invisible to the operator.

The correct fix is to remove the echo gate unconditionally and make line-buffering the default. Item 3 captures this.

---

## Out of Scope for v1.5.1

- **Skill-handling features.** Project-type classification, four-pass skill derivation, divergence taxonomy — all in v1.5.2.
- **Interactive LLM chat within the orchestrator.** v1.5.1's observability is read-only (the operator watches the run; the run doesn't take mid-flight operator input beyond keystroke mode switches).
- **Remote run monitoring.** Watching a run from a different machine (web dashboard, SSH tunnel). v1.5.1 is strictly local-terminal observability.
- **Automatic rate-limit backoff.** `--pace-seconds` is a static pacer, not an adaptive backoff. If a prompt fails with a rate-limit error, v1.5.1 fails the run; adaptive retry is a future enhancement.
- **Non-English locale handling for the scaffolder's filename heuristics.** The `rfc`/`spec`/`guide`/`howto` pattern list is English-only. Operators with non-English filenames fall through to the manual-tier path.
- **Keystroke-based observability mode switching.** Considered and rejected for v1.5.1 — adds platform-specific stdlib keystroke handling (`termios` + `tty` on Unix, `msvcrt` on Windows), genuine AI-sandbox risk when stdin isn't a TTY, and a cross-platform test matrix. Value (toggle modes without restarting) is small relative to cost; operators who want a different mode can relaunch with different flags. Revisit if real usage reveals demand.

---

## Open Questions

These don't block v1.5.1 design but need answers during implementation:

1. **When the sidecar scaffolder encounters existing `.meta.json` files, should it skip them or regenerate?** **Resolved:** always regenerate, but back up the previous version to a timestamped subdirectory (e.g., `formal_docs/.sidecar_backups/20260420T140000Z/<stem>.meta.json`). Operators never lose hand-edited work; no `--overwrite` flag needed because the default behavior is safe. Restoring a backup is a manual copy.

2. **Should the pre-run guard's "formal_docs empty" warning be suppressible?** Lean: yes, via `--no-formal-docs` to signal "I know, run anyway." Self-audit bootstrap and minimal-repo cases legitimately have empty formal_docs.

3. **Does `--phase-groups` break any v1.5.0 bug-manifest schema assumption?** **Resolved:** no. Phases still do the same work and produce the same per-phase artifacts; only the prompt boundary changes. A group of phases is just "run these phases in a single prompt" — the artifact schema and gate checks are unaffected.

4. **Should `--pace-seconds` apply between phases in a single phase-group invocation?** Lean: no, only between phase groups and between iteration strategies. Phases within a group run as one prompt, so there's nothing to pace.
