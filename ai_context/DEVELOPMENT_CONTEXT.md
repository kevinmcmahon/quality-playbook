# Quality Playbook — Development Context

> This file is for AI assistants helping maintain and improve the quality playbook skill.
> It contains the project's architecture, benchmarking methodology, known issues,
> and improvement axes. Read this when working on the skill files themselves.
>
> The project accompanies the O'Reilly Radar article [AI Is Writing Our Code Faster Than We Can Verify It](https://www.oreilly.com/radar/ai-is-writing-our-code-faster-than-we-can-verify-it/).
> The README was coauthored with Claude Cowork.

## Project structure

```
quality-playbook/
├── AGENTS.md                          ← AI coding agent entry point (repo root)
├── SKILL.md                           ← The skill — full operational instructions for running the playbook
├── LICENSE.txt                        ← License terms
├── agents/                            ← Orchestrator agent files for autonomous runs
│   ├── quality-playbook-claude.agent.md   ← Claude Code orchestrator (single-level sub-agent model)
│   └── quality-playbook.agent.md          ← Copilot / generic orchestrator
├── bin/                               ← Standard-library benchmark automation package
│   ├── __init__.py                    ← Package marker
│   ├── benchmark_lib.py               ← Shared helpers (versioned from repos/_benchmark_lib.sh)
│   ├── run_playbook.py                ← Main runner — positional args are target directories (python3 bin/run_playbook.py)
│   └── tests/                         ← Stdlib-only tests for the runner package (92 tests)
├── pytest/                            ← Local stdlib-only shim so python3 -m pytest works without installs
├── references/                        ← Reference files read during specific phases
│   ├── challenge_gate.md              ← False-positive detection challenge gate (v1.4.3+)
│   ├── constitution.md                ← Guidance for drafting the quality constitution
│   ├── defensive_patterns.md          ← Forensic inversion of defensive code (try/except, null guards)
│   ├── exploration_patterns.md        ← Pattern library for Phase 1 exploration
│   ├── functional_tests.md            ← Functional-test generation reference (all languages)
│   ├── iteration.md                   ← Iteration strategies (gap, unfiltered, parity, adversarial)
│   ├── orchestrator_protocol.md       ← Shared hardening rules imported by both agent files (v1.4.4+)
│   ├── requirements_pipeline.md       ← Requirements derivation and post-review reconciliation
│   ├── requirements_refinement.md     ← Coverage / completeness refinement pass
│   ├── requirements_review.md         ← Pre-finalization requirements review
│   ├── review_protocols.md            ← Three-pass code review protocol and regression test conventions
│   ├── schema_mapping.md              ← tdd-results.json / recheck-results.json schema reference
│   ├── spec_audit.md                  ← Council of Three spec audit protocol
│   └── verification.md                ← 45 self-check benchmarks for Phase 6
├── .github/                           ← Installed-copy layout used inside target repos
│   └── skills/
│       ├── SKILL.md                   ← Installed skill entry point
│       ├── references/                ← Installed references bundle
│       ├── quality_gate.py            ← Symlink → quality_gate/quality_gate.py (stable invocation path)
│       └── quality_gate/              ← Gate script package (sole mechanical gate since v1.4.5; bash retired)
│           ├── __init__.py            ← Re-exports public API
│           ├── quality_gate.py        ← Mechanical validation (14 checks, 1100+ lines, Python 3.8+)
│           └── tests/
│               ├── __init__.py
│               └── test_quality_gate.py  ← 108 stdlib-only unit tests
├── ai_context/                        ← AI-readable context files
│   ├── TOOLKIT.md                     ← For users' AI assistants (setup, run, interpret, recheck)
│   ├── DEVELOPMENT_CONTEXT.md         ← For maintainers' AI assistants (this file)
│   └── BENCHMARK_PROTOCOL.md          ← Clean-folder run protocol for contamination-free benchmarks
├── repos/                             ← Benchmark repos and setup tooling
│   ├── setup_repos.sh                 ← Copies skill files into target repos
│   ├── _benchmark_lib.sh              ← Shell helpers shared by setup_repos.sh, run_tdd.sh, etc.
│   └── clean/                         ← Clean clones of benchmark repos
├── quality/                           ← Bootstrap artifacts (playbook run against QPB itself)
└── council-reviews/                   ← Council review briefings and responses (not distributed)
```

**Automation note:** benchmark automation lives in `bin/` and uses only the Python standard library so sandboxed AI agents can run it without creating a virtual environment or installing packages. The shell scripts remaining in `repos/` (`setup_repos.sh`, `_benchmark_lib.sh`, `run_tdd.sh`) handle repo setup and TDD plumbing — they no longer include a runner.

**Running the tests:**

```
# Benchmark runner (92 tests)
python3 -m pytest bin/tests/
python3 -m unittest discover bin/tests

# Quality gate package (108 tests) — invoke from the package dir
cd .github/skills/quality_gate && python3 -m unittest discover -s tests -t .
```

The local `pytest` package is a minimal shim around `unittest` so `python3 -m pytest` works on plain Python 3.8+ with no external dependencies.

## How the skill works

The quality playbook is a long-form instruction document (SKILL.md) that an AI agent reads and follows. It is designed to run one phase at a time, with the user driving each phase forward. Each phase runs in its own session with a clean context window, producing files on disk that the next phase reads.

**Phase 1 (Explore):** The agent explores the codebase using a three-stage approach — open exploration, quality risk analysis, and selected pattern deep-dives. Outputs: EXPLORATION.md with candidate bugs.

**Phase 2 (Generate):** The agent generates nine quality artifacts from the exploration findings: requirements, constitution, functional tests, code review protocol, integration tests, spec audit protocol, TDD protocol, AGENTS.md.

**Phase 3 (Code Review):** Three-pass code review against HEAD. Regression tests for every confirmed bug. Generates patches.

**Phase 4 (Spec Audit):** Three independent AI auditors review the code against requirements. Triage with verification probes. Regression tests for net-new findings.

**Phase 5 (Reconciliation):** Close the loop — every bug tracked, regression-tested. TDD red-green cycle for all confirmed bugs. Writeups, fix patches, completeness report.

**Phase 6 (Verify):** Mechanical verification and 45 self-check benchmarks.

After each phase, the skill prints a prominent end-of-phase message telling the user what happened and what to say next. The user says "keep going" or "run phase N" to continue. This interactive protocol gives much better results than single-session execution because each phase gets the full context window.

**Iteration mode:** After the baseline run, the agent can run additional iterations using strategies defined in references/iteration.md. Each strategy re-explores the codebase with a different approach, then re-runs Phases 2-6 on the merged findings. Iterations typically add 40-60% more confirmed bugs.

**Recheck mode:** After the user fixes bugs, saying "recheck" triggers a lightweight verification pass. Recheck reads BUGS.md, checks each bug against the current source (reverse-applying fix patches, inspecting cited lines, optionally running regression tests), and writes results to `quality/results/recheck-results.json` and `quality/results/recheck-summary.md`. Takes 2-10 minutes instead of a full re-run. Does not find new bugs — only verifies previously found bugs.

## Three improvement axes

When the playbook misses a bug, the miss falls on one of three axes. Identifying which axis tells you what to fix:

### 1. Exploration rules

**Symptom:** The agent never looked at the code containing the bug.

**What to fix:** Exploration patterns in SKILL.md Phase 1, pattern applicability matrix, domain-knowledge questions. Or add a new iteration strategy that targets the unexplored area.

**Example:** The parity sub-type checklist was added to references/iteration.md because the parity strategy wasn't comparing resource lifecycle (setup vs. teardown) — it was only finding "obvious" parallel-path differences.

### 2. Iteration types

**Symptom:** The agent looked at the code but the bug wasn't found by any existing iteration strategy.

**What to fix:** Add a new iteration strategy to references/iteration.md that targets the failure mode. Each strategy exists because a specific class of bugs was being systematically missed.

**History:**
- **gap** (v1.3.44): Baseline only covered subset of codebase
- **unfiltered** (v1.3.44): Structured approach over-constrained exploration
- **parity** (v1.3.45): No strategy explicitly compared parallel code paths
- **adversarial** (v1.3.44): Conservative triage kept dismissing real bugs

### 3. Triage calibration

**Symptom:** The agent found the code, flagged it as a candidate, but dismissed it during triage.

**What to fix:** Triage rules in SKILL.md (evidentiary standards, "what counts as sufficient evidence"), the Demoted Candidates Manifest in references/iteration.md (tracks dismissed findings with re-promotion criteria), adversarial strategy evidentiary bar.

**Example:** Pydantic's AliasPath bug was found and dismissed THREE times before the adversarial strategy recovered it. The triage kept classifying it as a "design choice" because the behavior was "permissive." The fix was lowering the adversarial evidentiary bar: code-path trace + semantic drift is sufficient.

## Benchmarking methodology

### Benchmark repos

The benchmark suite uses open-source codebases across multiple languages. Each repo is cloned once into `repos/clean/` and never modified. For each skill version, `setup_repos.sh` creates a working copy (e.g., `chi-1.4.6`) with the skill files installed.

Active benchmark set (four targets):

- **bootstrap** — the playbook running against its own codebase (self-audit). Bootstrap artifacts live at `quality/` at the QPB repo root, not in `repos/`. Always included; see "Why bootstrap is a benchmark target" below.
- **chi** (Go) — small HTTP router; quick sanity-check runs.
- **cobra** (Go) — larger CLI framework; exercises iteration strategies more heavily.
- **virtio** (C / Linux kernel driver) — hardest repo; reference target for parity strategy and the historical home of the mechanical-verification rules.

60+ additional repos remain in `repos/clean/` for expanded benchmarking when a specific change calls for it (e.g., language-specific regressions, framework-specific exploration patterns). They are not part of the default validation loop for skill changes. `python3 bin/run_playbook.py` treats every positional argument as a directory path (relative or absolute) — no version resolution, no benchmark-folder lookups.

#### Why bootstrap is a benchmark target

Bootstrap is the playbook running against `/Users/andrewstellman/Documents/QPB` itself. It's always included in the active benchmark set because:

1. **Self-referential edge cases.** The gate script validates its own artifacts. SKILL.md is both the instruction set and the subject under audit. Changes to rules about enum validation, heading format, or script-verified closure can break on the very script that enforces them — and only bootstrap catches that class of bug.
2. **Perfect verification.** We wrote the skill and the gate, so we can verify any finding against our own intent quickly. For other repos, we spot-check; for bootstrap, we can confirm every bug.
3. **Reproducibility.** The codebase is stable between runs (our own commits), so convergence trends cleanly across model/runner combinations.

Bootstrap artifacts live at `quality/` at the QPB repo root rather than under `repos/`. To run bootstrap, the agent treats the QPB root as the target directory; the existing `quality/` is the prior-run evidence (phase 0 seed source).

### Running benchmarks

See `ai_context/BENCHMARK_PROTOCOL.md` for the clean-folder run protocol. Benchmark runs must be isolated (no sibling runs visible to the agent) or findings leak between runs and the tuning signal is corrupted.

Positional arguments are directory paths (relative or absolute) — the runner does no short-name resolution and no benchmark-folder lookup. Run from `repos/` so the working-copy directory names produced by `setup_repos.sh` (e.g. `chi-1.4.6`) can be passed as plain relative paths:

```bash
cd repos/
./setup_repos.sh chi cobra virtio                     # copy skill files into the three repo-based targets
python3 ../bin/run_playbook.py chi-1.4.6 cobra-1.4.6 virtio-1.4.6          # baseline runs (Copilot default)
python3 ../bin/run_playbook.py --claude chi-1.4.6 cobra-1.4.6 virtio-1.4.6 # baseline runs (Claude Code)
python3 ../bin/run_playbook.py --next-iteration --strategy all chi-1.4.6 cobra-1.4.6 virtio-1.4.6  # full iteration cycle
```

With no positional args the runner operates on the current directory, which is how bootstrap is invoked:

```bash
cd /Users/andrewstellman/Documents/QPB
python3 bin/run_playbook.py --phase all      # bootstrap: run on the QPB repo itself
```

Bootstrap is the fourth active target but doesn't go through `setup_repos.sh` — the QPB repo already has SKILL.md and references at their canonical locations.

### Interpreting results

**Bug counts vary between runs.** The same skill on the same codebase produces different bug counts due to non-determinism in exploration. A single run isn't definitive. Compare across 5+ runs or use iteration cycles to compensate.

**Baseline vs. iteration yield.** Baseline typically finds 1-3 bugs per repo. Full iteration cycle (gap + unfiltered + parity + adversarial) multiplies by 3-4x. If a skill change doesn't improve baseline yield, it may still improve iteration yield or vice versa.

**Spot-check every new version.** After making skill changes, spot-check 3-5 bugs from the new version against actual source code. Verify the bug is real, the file:line is correct, and the regression test would actually fail. In v1.3.46 benchmarking, 15/15 spot-checked bugs were verified as real.

### Council reviews

For major skill changes, we run a council review: three different AI agents independently analyze the benchmark data, iteration logs, and bug quality, then propose improvements. The agents don't modify code — they write analysis documents.

Council review artifacts go in `council-reviews/`. Each review has:
- `COUNCIL_BRIEFING_VN.md` — data and questions for the council
- `COUNCIL_VN_PROMPTS.md` — prompts for each reviewer (must include "DO NOT modify any code")
- `{AGENT}_RESPONSE_VN.md` — each reviewer's analysis

### Known agent behavior differences

| Agent | Exploration | TDD execution | Known issues |
|-------|------------|---------------|-------------|
| Claude Code / Opus | Strong | Reliable (creates red/green logs) | Expensive (~8% weekly per run) |
| Claude Code / Sonnet | Strong (25 bugs, 3 HIGH) | Reliable | Recommended default (~3% weekly per run) |
| Copilot / gpt-5.4 | Strong | Weak (skips log creation) | 54hr rate limit on heavy use |
| Cursor / Sonnet | Good | Weak first pass, follows up when asked | Workspace scope bleeds to siblings |
| Cursor / Codex 5.3 | Weak (zero bugs) | N/A | Insufficient reasoning depth |

## Version history highlights

- **v1.3.13–v1.3.14:** Early structured approach. Zero bugs found — too rigid.
- **v1.3.21:** Gate hardening. First confirmed bugs (2 total across 10 repos).
- **v1.3.25:** Unfiltered domain-driven exploration. Major breakthrough — 14 bugs.
- **v1.3.40:** Parity patterns. Found 5 virtio bugs using fallback path comparison.
- **v1.3.44:** Iteration mode (gap, unfiltered, adversarial). 3.7x baseline yield.
- **v1.3.45:** references/iteration.md reference file, parity strategy, suggested-next-prompt UX.
- **v1.3.46:** Demoted Candidates Manifest, parity sub-type checklist, adversarial bar adjustment, TDD execution enforcement.
- **v1.3.47:** TDD log enforcement — six insertion points from Cursor diagnostic (artifact contract, closure gate, bash template, progress checkbox, file-existence gate, sidecar contradiction check).
- **v1.4.0** (promoted from v1.3.50)**:** Six-phase interactive architecture (renumbered from 3 phases to 6), interactive phase-by-phase execution with end-of-phase messages, `--phase` flag in runner, quality gate script, four iteration strategies with 40-60% yield boost, TDD enforcement, documentation warning, help system, "keep going" continuation, O'Reilly Radar article, moved ITERATION.md to references/iteration.md, orchestrator agents for Claude Code and Copilot. Benchmarked: Express.js (14 bugs), Gson (9 bugs), Linux virtio (8 bugs) — all with 100% TDD coverage and 0 gate failures.
- **v1.4.1:** Recheck mode for lightweight fix verification (reads BUGS.md, checks each bug against current source, outputs recheck-results.json and recheck-summary.md). Fixed 19 bugs from bootstrap self-audit (second run): eval injection in the gate script (then `quality_gate.sh`, now `quality_gate.py`), bash 3.2 empty array crashes, required artifacts downgraded to WARN, json_key_count false positives, missing artifact checks, documentation inconsistencies. All fixes verified by recheck (19/19 FIXED).
- **v1.4.2:** Fixed 25 bugs from Sonnet 4.6 bootstrap self-audit (3 HIGH, 8 MEDIUM, 14 LOW). Key fixes: nullglob-safe artifact detection (find replaces ls-glob across 7 locations), severity-prefixed bug ID support (BUG-H1/BUG-M3/BUG-L6), TDD sidecar-to-log cross-validation, recheck-results.json gate validation, Phase 5 entry gate, SEED_CHECKS.md in artifact contract table, integration enum validation. Added run metadata JSON spec (`quality/results/run-YYYY-MM-DDTHH-MM-SS.json`) for multi-model comparison — records model, provider, runner, timestamps, phase timings, bug counts, and gate results. All 25 fixes verified by Sonnet recheck (25/25 FIXED). Multi-model comparison: Sonnet found 25 bugs (3 HIGH) at ~3% weekly usage vs Opus's 19 bugs (1 HIGH) at ~8% — Sonnet is the recommended default for playbook runs.
- **v1.4.3:** Challenge gate added for false-positive detection — forces triage to reconsider CRITICAL findings with common-sense review before closure (motivated by edgequake benchmarking where 6/7 "CRITICAL" findings turned out to be documented feature gaps or placeholders). Functional-test reference refactored: split into per-language files, then re-merged into a single `references/functional_tests.md` with import patterns folded in. First pass of orchestrator hardening: `references/orchestrator_protocol.md` extracted as a shared reference imported by both agent files, with critical rules duplicated inline for safety.
- **v1.4.4:** Orchestrator hardening pass — "You are the orchestrator" architecture. Fixes three failure modes observed on casbin benchmarking: (1) single-context collapse (all six phases executed in one context, producing shallow summaries and zero files on disk), (2) `claude -p` subprocess spawning (orchestrator trying to fork fresh CLI processes instead of using the Agent tool), (3) nested Agent-tool stripping (Claude Code strips the Agent tool from nested sub-agents, so the orchestrator must be single-level). The session that reads the agent file IS the orchestrator — it never spawns a new session, only sub-agents. Protocol lives at `references/orchestrator_protocol.md`; critical rules are duplicated inline in each agent file.
- **v1.4.5:** Tooling rebuild plus surface cleanup:
    - **Runner rewritten in Python.** `bin/run_playbook.py` + `bin/benchmark_lib.py` replace the old `repos/run_playbook.sh` (deleted). `repos/_benchmark_lib.sh` remains in use by `setup_repos.sh` and `run_tdd.sh`. Standard library only, Python 3.8+, 36 stdlib-only tests at release (grew to 92 with v1.4.6 regression coverage).
    - **Runner interface redesign.** Positional args are directory paths, not short names. Default is the current directory. No more `DEFAULT_REPO_NAMES`, `REPOS_DIR`, `SHORT_VERSIONED_DIR_PATTERN`, `find_repo_dir`, `resolve_repos`, `repo_short_name`, or version-resolution logic. Missing SKILL.md is a warning rather than a fatal error. Log files live beside each target at `{parent}/{target-name}-playbook-{timestamp}.log` instead of being forced into `repos/`. A narrow **version-append fallback** retries `<name>-<skill_version>` once when a bare name doesn't resolve — lets `cd repos/ && python3 ../bin/run_playbook.py chi` pick up `chi-<version>` without reintroducing the old short-name tables.
    - **Python gate is sole mechanical gate.** `quality_gate.sh` retired; `quality_gate.py` handles JSON via `json.load` instead of grep-style parsing. Moved to `.github/skills/quality_gate/` as a proper package with `__init__.py` and a 108-test `tests/` subdirectory. The stable invocation path `.github/skills/quality_gate.py` is a symlink to the package module.
    - **Benchmark set reduced to four targets.** bootstrap, chi, cobra, virtio — down from 10. Bootstrap runs last because fixes from the first three land before the playbook audits itself. 60+ additional repos remain in `repos/clean/` for expanded benchmarking but aren't part of the default validation loop.
    - **Recheck gate fix.** Root-key check for `recheck-results.json` corrected from `bugs` → `results` to match the SKILL.md schema.
- **v1.4.6:** Lands the 27-bug fix pass from the v1.4.5 self-audit. No structural or behavioral changes beyond the bug fixes themselves; v1.5.0 design work proceeds on this clean baseline.
    - **27-bug bootstrap self-audit fix batch.** Opus self-audit over the v1.4.5 baseline + four iteration strategies (gap, unfiltered, parity, adversarial) confirmed 27 real defects; all 27 are fixed with passing regression tests in `quality/test_regression.py`. Shipped in seven thematic commits. Material behavior changes: Phase 2 gate now FAILs below 120 lines instead of WARNing at 80 (matches SKILL.md §Phase 1 completion gate); Phase 3 gate checks all nine Phase 2 artifacts instead of four; Phase 5 gate enforces SKILL.md:1663-1667 hard-stop (spec_audits triage + auditor files + Phase 4 `[x]`); `archive_previous_run` stages into `previous_runs/<ts>.partial/` then atomically renames, and preserves `control_prompts/` instead of deleting it; `cleanup_repo` adds `AGENTS.md` to its protected-path set via `PROTECTED_EXACT`; child-process exit codes propagate through `run_one_phase` / `run_one_singlepass`; missing `docs_gathered/` WARNs and continues with code-only analysis instead of blocking the run; runner prompts front-load a `SKILL_FALLBACK_GUIDE` constant advertising all four install paths; `check_run_metadata` and `_check_exploration_sections` close two long-standing gate gaps; `validate_iso_date` accepts full ISO 8601 datetimes; `_parse_porcelain_path` unwraps Git's quote-wrapped paths for names with spaces; `detect_project_language` skips `repos/` fixtures so the self-audit classifies correctly; the functional-test filename matrix + extension check now recognize the full `functional_test.*` / `FunctionalTest.*` / `FunctionalSpec.*` / `functional.test.ts` set; `FUNCTIONAL_TEST_PATTERNS` / `REGRESSION_TEST_PATTERNS` narrowed to canonical names only; both orchestrator agents list repo-root `SKILL.md` as install-discovery entry 1 and the general agent's Mode 1 now starts a fresh context for Phase 1. Recheck: 27/27 FIXED (`quality/results/recheck-summary.md`).
    - **Bootstrap artifacts tracked in git.** Reverses the earlier untracking now that `cleanup_repo`'s `PROTECTED_PREFIXES` guards `quality/`, `previous_runs/`, and `control_prompts/` from `git checkout .`. These trees are the proof-of-work for the self-audit and belong in git history so future iterations can diff against them.

## Current known issues

1. **Virtio missing bugs.** Two bugs found in v1.3.40 have never been recovered: MSI-X slow_virtqueues reattach and GFP_KERNEL under spinlock. Both are exploration axis issues — the agent doesn't reach the relevant code. The parity sub-type checklist was designed to address this but hasn't been validated yet.

2. **TDD execution compliance.** Only Claude Code reliably creates red/green log files. Copilot and Cursor skip the step despite v1.3.47's six insertion points (not yet tested on v1.3.47). If v1.3.47 doesn't fix it, a post-run script that mechanically runs the TDD cycle may be needed.

3. **Rate limits.** Running 6+ repos simultaneously through iteration cycles triggers Copilot's 54-hour cooldown. Users need to stagger runs (2-3 repos at a time) or use Claude Code / Cursor.

4. **Cursor workspace contamination.** Cursor reads sibling directories and imports findings from prior runs. Repos must be isolated in their own parent directory.

## Making changes to the skill

**Always back up before editing.** Copy any file you're about to modify to a `.bak` version first.

**Test on at least 2 repos after changes.** One large (virtio or cobra) and one small (chi). Check both baseline and at least one iteration strategy.

**Update the version.** The `version:` field in SKILL.md metadata must be bumped for every change. All generated artifacts stamp this version, and mismatches cause quality_gate.py failures.

**Run quality_gate.py after testing.** The gate validates artifact conformance mechanically. If it passes on your test repos, the change is safe to commit.

**Update TOOLKIT.md and this file.** If your change affects how users run the playbook or how maintainers work on it, update the relevant context file.
