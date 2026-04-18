"""Python benchmark runner for the Quality Playbook."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import signal
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

try:
    from . import benchmark_lib as lib
except ImportError:
    import benchmark_lib as lib


DEFAULT_REPO_NAMES = ["chi", "cobra", "virtio"]
ALL_STRATEGIES = ["gap", "unfiltered", "parity", "adversarial"]
PID_FILE = lib.REPOS_DIR / ".run_pids"


@dataclass
class GateCheck:
    ok: bool
    messages: List[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Quality Playbook benchmark workflow across versioned repos.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parallel_group = parser.add_mutually_exclusive_group()
    parallel_group.add_argument("--parallel", dest="parallel", action="store_true", default=True, help="Run all repos concurrently (default).")
    parallel_group.add_argument("--sequential", dest="parallel", action="store_false", help="Run repos one after another.")

    runner_group = parser.add_mutually_exclusive_group()
    runner_group.add_argument("--claude", dest="runner", action="store_const", const="claude", default="copilot", help="Use claude -p instead of gh copilot.")
    runner_group.add_argument("--copilot", dest="runner", action="store_const", const="copilot", help="Use gh copilot (default).")

    seed_group = parser.add_mutually_exclusive_group()
    seed_group.add_argument("--no-seeds", dest="no_seeds", action="store_true", default=True, help="Skip Phase 0/0b seed injection (default).")
    seed_group.add_argument("--with-seeds", dest="no_seeds", action="store_false", help="Allow Phase 0/0b seed injection from prior or sibling runs.")

    parser.add_argument("--phase", help="Run specific phase(s): 1-6, all, or comma-separated values like 3,4,5.")
    parser.add_argument("--single-pass", dest="phase", action="store_const", const="", help=argparse.SUPPRESS)
    parser.add_argument("--multi-pass", dest="phase", action="store_const", const="all", help=argparse.SUPPRESS)
    parser.add_argument("--next-iteration", action="store_true", help="Iterate on an existing quality/ run.")
    parser.add_argument(
        "--strategy",
        default="gap",
        choices=["gap", "unfiltered", "parity", "adversarial", "all"],
        help="Iteration strategy to use with --next-iteration.",
    )
    parser.add_argument("--model", help="Runner model override (copilot: gpt-5.4, claude: sonnet/opus/etc).")
    parser.add_argument("--kill", action="store_true", help="Kill processes from the current or last parallel run.")
    parser.add_argument("repos", nargs="*", help="Short repo names to run. Defaults to chi cobra virtio.")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    return parser


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.kill and not args.repos:
        args.repos = list(DEFAULT_REPO_NAMES)
    if args.worker:
        args.parallel = False
    if args.next_iteration and args.phase:
        parser.error("--next-iteration is not compatible with --phase. Iteration uses a single prompt.")
    if args.phase:
        validate_phase_mode(args.phase, parser)
    if not args.next_iteration and args.strategy != "gap":
        print("WARNING: --strategy is ignored without --next-iteration", file=sys.stderr)
    return args


def validate_phase_mode(phase_mode: str, parser: argparse.ArgumentParser) -> None:
    if phase_mode == "all":
        return
    for phase in phase_mode.split(","):
        if phase not in {"1", "2", "3", "4", "5", "6"}:
            parser.error(f"Invalid phase '{phase}'. Must be 1-6 or 'all'.")


def phase_list_from_mode(phase_mode: Optional[str]) -> List[str]:
    if not phase_mode:
        return []
    if phase_mode == "all":
        return ["1", "2", "3", "4", "5", "6"]
    return [phase for phase in phase_mode.split(",") if phase]


def phase_label(phase: str) -> str:
    return {
        "1": "Explore",
        "2": "Generate",
        "3": "Code Review",
        "4": "Spec Audit",
        "5": "Reconciliation",
        "6": "Verification",
    }[phase]


def phase1_prompt(no_seeds: bool) -> str:
    seed_instruction = ""
    if no_seeds:
        seed_instruction = "Skip Phase 0 and Phase 0b entirely - do not look for previous_runs/ or sibling versioned directories. This is a clean benchmark run. Start directly at Phase 1."

    return f"""You are a quality engineer. Read the skill at .github/skills/SKILL.md - but ONLY the sections up through Phase 1 (stop at the \"---\" line before \"Phase 2\"). Also read the reference files in .github/skills/references/ that are relevant to exploration.

{seed_instruction}

Execute Phase 1: Explore the codebase. The docs_gathered/ directory contains gathered documentation - read it to supplement your exploration.

When Phase 1 is complete, write your full exploration findings to quality/EXPLORATION.md. This file must contain:
- Domain and stack identification
- Architecture map (key modules, entry points, data flow)
- Existing test inventory
- Specification summary (from docs_gathered/ and any inline docs)
- Quality risks identified
- Skeleton/dispatch/state-machine analysis (if applicable)
- Testable requirements derived (REQ-NNN format)
- Use cases derived (UC-NN format)

Also initialize quality/PROGRESS.md with the run metadata and mark Phase 1 complete.

IMPORTANT: Do NOT proceed to Phase 2. Your only job is exploration and writing findings to disk. Write thorough, detailed findings - the next phase will read EXPLORATION.md to generate artifacts, so everything important must be captured in that file.
"""


def phase2_prompt() -> str:
    return """You are a quality engineer continuing a phase-by-phase quality playbook run. Phase 1 (exploration) is already complete.

Read these files to get context:
1. quality/EXPLORATION.md - your Phase 1 findings (requirements, risks, architecture)
2. quality/PROGRESS.md - run metadata and phase status
3. .github/skills/SKILL.md - read the Phase 2 section (from \"Phase 2: Generate the Quality Playbook\" through the \"Checkpoint: Update PROGRESS.md after artifact generation\" section). Also read the reference files cited in that section.

Execute Phase 2: Generate all quality artifacts. Use the exploration findings in EXPLORATION.md as your source - do not re-explore the codebase from scratch. Generate:
- quality/QUALITY.md (quality constitution)
- quality/CONTRACTS.md (behavioral contracts)
- quality/REQUIREMENTS.md (with REQ-NNN and UC-NN identifiers from EXPLORATION.md)
- quality/COVERAGE_MATRIX.md
- Functional tests (quality/test_functional.*)
- quality/RUN_CODE_REVIEW.md (code review protocol)
- quality/RUN_INTEGRATION_TESTS.md (integration test protocol)
- quality/RUN_SPEC_AUDIT.md (spec audit protocol)
- quality/RUN_TDD_TESTS.md (TDD verification protocol)
- quality/COMPLETENESS_REPORT.md (baseline, without verdict)
- If dispatch/enumeration contracts exist: quality/mechanical/ with verify.sh and extraction artifacts. Run verify.sh immediately and save receipts.

Update PROGRESS.md: mark Phase 2 complete, update artifact inventory.

IMPORTANT: Do NOT proceed to Phase 3 (code review). Your job is artifact generation only. The next phase will execute the review protocols you generated.
"""


def phase3_prompt() -> str:
    return """You are a quality engineer continuing a phase-by-phase quality playbook run. Phases 1-2 are complete.

Read these files to get context:
1. quality/PROGRESS.md - run metadata, phase status, artifact inventory
2. quality/EXPLORATION.md - Phase 1 findings (especially the \"Candidate Bugs for Phase 2\" section)
3. quality/REQUIREMENTS.md - derived requirements and use cases
4. quality/CONTRACTS.md - behavioral contracts
5. .github/skills/SKILL.md - read the Phase 3 section (\"Phase 3: Code Review and Regression Tests\"). Also read .github/skills/references/review_protocols.md.

Execute Phase 3: Code Review + Regression Tests.
Run the 3-pass code review per quality/RUN_CODE_REVIEW.md. For every confirmed bug:
- Add to quality/BUGS.md with ### BUG-NNN heading format
- Write a regression test (xfail-marked)
- Generate quality/patches/BUG-NNN-regression-test.patch (MANDATORY for every confirmed bug)
- Generate quality/patches/BUG-NNN-fix.patch (strongly encouraged)
- Write code review reports to quality/code_reviews/
- Update PROGRESS.md BUG tracker

Mark Phase 3 (Code review + regression tests) complete in PROGRESS.md.

IMPORTANT: Do NOT proceed to Phase 4 (spec audit). The next phase will run the spec audit with a fresh context window.
"""


def phase4_prompt() -> str:
    return """You are a quality engineer continuing a phase-by-phase quality playbook run. Phases 1-3 are complete.

Read these files to get context:
1. quality/PROGRESS.md - run metadata, phase status, BUG tracker
2. quality/REQUIREMENTS.md - derived requirements
3. quality/BUGS.md - bugs found in Phase 3 (code review)
4. .github/skills/SKILL.md - read the Phase 4 section (\"Phase 4: Spec Audit and Triage\"). Also read .github/skills/references/spec_audit.md.

Execute Phase 4: Spec Audit + Triage.
Run the spec audit per quality/RUN_SPEC_AUDIT.md. Produce:
- Individual auditor reports at quality/spec_audits/YYYY-MM-DD-auditor-N.md (one per auditor)
- Triage synthesis at quality/spec_audits/YYYY-MM-DD-triage.md
- Executable triage probes at quality/spec_audits/triage_probes.sh
- Regression tests and patches for any net-new spec audit bugs
- Update BUGS.md and PROGRESS.md BUG tracker with any new findings

Mark Phase 4 (Spec audit + triage) complete in PROGRESS.md.

IMPORTANT: Do NOT proceed to Phase 5 (reconciliation). The next phase will handle reconciliation and TDD.
"""


def phase5_prompt() -> str:
    return """You are a quality engineer continuing a phase-by-phase quality playbook run. Phases 1-4 are complete.

Read these files to get context:
1. quality/PROGRESS.md - run metadata, phase status, cumulative BUG tracker
2. quality/BUGS.md - all confirmed bugs from code review and spec audit
3. quality/REQUIREMENTS.md - derived requirements
4. .github/skills/SKILL.md - read the Phase 5 section (\"Phase 5: Post-Review Reconciliation and Closure Verification\"). Also read .github/skills/references/requirements_pipeline.md, .github/skills/references/review_protocols.md, and .github/skills/references/spec_audit.md.

Execute Phase 5: Reconciliation + TDD + Closure.

1. Run the Post-Review Reconciliation per references/requirements_pipeline.md. Update COMPLETENESS_REPORT.md.
2. Run closure verification: every BUG in the tracker must have either a regression test or an explicit exemption.
3. Write bug writeups at quality/writeups/BUG-NNN.md for EVERY confirmed bug. Each writeup MUST include an inline fix diff in a ```diff code block - this is gate-enforced.
4. Run the TDD red-green cycle: for each confirmed bug, run the regression test against unpatched code -> quality/results/BUG-NNN.red.log. If a fix patch exists, run against patched code -> quality/results/BUG-NNN.green.log. If the test runner is unavailable, create the log with NOT_RUN on the first line.
5. Generate sidecar JSON: quality/results/tdd-results.json and quality/results/integration-results.json (schema_version \"1.1\", canonical fields: id, requirement, red_phase, green_phase, verdict, fix_patch_present, writeup_path).
6. If mechanical verification artifacts exist, run quality/mechanical/verify.sh and save receipts.
7. Run terminal gate verification, write it to PROGRESS.md.

Mark Phase 5 complete in PROGRESS.md.

IMPORTANT: Do NOT skip writeup inline diffs or TDD logs. The next phase runs quality_gate.py which will FAIL on missing patches, missing diffs, or missing TDD logs.
"""


def phase6_prompt() -> str:
    return """You are a quality engineer doing the verification phase of a quality playbook run. Phases 1-5 are complete.

Read .github/skills/SKILL.md - the Phase 6 section (\"Phase 6: Verify\"). Follow the incremental verification steps (6.1 through 6.5).

Step 6.1: If quality/mechanical/verify.sh exists, run it. Record exit code.
Step 6.2: Run quality_gate.py:
  python3 .github/skills/quality_gate.py .
Read the output carefully. For every FAIL result, fix the issue:
- Missing regression-test patches: generate quality/patches/BUG-NNN-regression-test.patch
- Missing inline diffs in writeups: add a ```diff block
- Non-canonical JSON fields: fix tdd-results.json (use 'id' not 'bug_id', etc.)
- Missing files: create them
After fixing all FAILs, run quality_gate.py again. Repeat until 0 FAIL.
Save final output to quality/results/quality-gate.log.

Step 6.3: Run functional tests if a test runner is available.
Step 6.4: File-by-file verification checklist (read one file at a time, check, move on).
Step 6.5: Metadata consistency check.

Append each step's result to quality/results/phase6-verification.log.
Mark Phase 6 complete in PROGRESS.md.
"""


def build_phase_prompt(phase: str, no_seeds: bool) -> str:
    return {
        "1": phase1_prompt(no_seeds),
        "2": phase2_prompt(),
        "3": phase3_prompt(),
        "4": phase4_prompt(),
        "5": phase5_prompt(),
        "6": phase6_prompt(),
    }[phase]


def single_pass_prompt(no_seeds: bool) -> str:
    seed_instruction = " Skip Phase 0 and Phase 0b - start directly at Phase 1." if no_seeds else ""
    return f"Read the quality playbook skill at .github/skills/SKILL.md and execute the quality playbook for this project.{seed_instruction}"


def iteration_prompt(strategy: str) -> str:
    return f"Read the quality playbook skill at .github/skills/SKILL.md and run the next iteration using the {strategy} strategy."


def next_strategy(strategy: str) -> str:
    return {
        "gap": "unfiltered",
        "unfiltered": "parity",
        "parity": "adversarial",
        "adversarial": "",
    }.get(strategy, "gap")


def count_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def check_phase_gate(repo_dir: Path, phase: str) -> GateCheck:
    quality_dir = repo_dir / "quality"
    messages: List[str] = []

    if phase == "1":
        return GateCheck(ok=True, messages=[])
    if phase == "2":
        exploration = quality_dir / "EXPLORATION.md"
        if not exploration.is_file():
            return GateCheck(ok=False, messages=["GATE FAIL Phase 2: quality/EXPLORATION.md missing - run Phase 1 first"])
        line_count = count_lines(exploration)
        if line_count < 80:
            messages.append(f"GATE WARN Phase 2: EXPLORATION.md is only {line_count} lines (expected 80+)")
        return GateCheck(ok=True, messages=messages)
    if phase == "3":
        missing = [name for name in ["REQUIREMENTS.md", "QUALITY.md", "CONTRACTS.md", "RUN_CODE_REVIEW.md"] if not (quality_dir / name).is_file()]
        if missing:
            return GateCheck(ok=False, messages=[f"GATE FAIL Phase 3: missing {' '.join(missing)} - run Phase 2 first"])
        return GateCheck(ok=True, messages=[])
    if phase == "4":
        if not (quality_dir / "REQUIREMENTS.md").is_file():
            return GateCheck(ok=False, messages=["GATE FAIL Phase 4: REQUIREMENTS.md missing - run Phase 2 first"])
        if not (quality_dir / "RUN_SPEC_AUDIT.md").is_file():
            return GateCheck(ok=False, messages=["GATE FAIL Phase 4: RUN_SPEC_AUDIT.md missing - run Phase 2 first"])
        code_reviews = quality_dir / "code_reviews"
        if not code_reviews.is_dir() or not any(code_reviews.iterdir()):
            messages.append("GATE WARN Phase 4: no code_reviews/ - Phase 3 may not have run")
        return GateCheck(ok=True, messages=messages)
    if phase == "5":
        if not (quality_dir / "PROGRESS.md").is_file():
            return GateCheck(ok=False, messages=["GATE FAIL Phase 5: PROGRESS.md missing"])
        if not (quality_dir / "BUGS.md").is_file() and not (quality_dir / "spec_audits").is_dir():
            messages.append("GATE WARN Phase 5: no BUGS.md and no spec_audits/ - Phases 3-4 may not have run")
        return GateCheck(ok=True, messages=messages)
    if phase == "6":
        if not (quality_dir / "PROGRESS.md").is_file():
            return GateCheck(ok=False, messages=["GATE FAIL Phase 6: PROGRESS.md missing"])
        return GateCheck(ok=True, messages=[])
    raise ValueError(f"Unknown phase: {phase}")


def command_for_runner(runner: str, prompt: str, model: Optional[str]) -> List[str]:
    if runner == "claude":
        command = ["claude"]
        if model:
            command.extend(["--model", model])
        command.extend(["-p", prompt, "--dangerously-skip-permissions"])
        return command
    copilot_model = model or lib.DEFAULT_MODEL
    return ["gh", "copilot", "-p", prompt, "--model", copilot_model, "--yolo"]


def command_preview(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def append_file(source: Path, destination: Path) -> None:
    if not source.is_file():
        return
    with destination.open("a", encoding="utf-8") as out_handle:
        out_handle.write(source.read_text(encoding="utf-8", errors="ignore"))


def run_prompt(repo_dir: Path, prompt: str, pass_name: str, output_file: Path, log_file: Path, runner: str, model: Optional[str]) -> int:
    command = command_for_runner(runner, prompt, model)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write("\n")
        handle.write("=" * 80 + "\n")
        handle.write(f"PLAYBOOK RUNNER - pass: {pass_name}\n")
        handle.write(f"Working directory: {repo_dir}\n")
        handle.write(f"Tool transcript (raw stdout/stderr): {output_file}\n")
        handle.write("=" * 80 + "\n")
        handle.write("SHELL COMMAND (exact invocation - cwd is repo root):\n")
        handle.write(f"  {command_preview(command)}\n\n")
        handle.write(f"--- BEGIN PROMPT ({len(prompt)} bytes) ---\n")
        handle.write(prompt)
        if not prompt.endswith("\n"):
            handle.write("\n")
        handle.write("--- END PROMPT ---\n\n")

    with output_file.open("w", encoding="utf-8") as out_handle:
        try:
            result = subprocess.run(
                command,
                cwd=str(repo_dir),
                stdout=out_handle,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            out_handle.write(f"ERROR: command not found: {command[0]}\n")
            result = subprocess.CompletedProcess(command, returncode=127)

    append_file(output_file, log_file)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"\n--- EXIT CODE: {result.returncode} ---\n")
    return result.returncode


def ensure_runner_available(runner: str) -> bool:
    if runner == "copilot":
        return lib.require_copilot()
    return shutil.which("claude") is not None


def docs_present(repo_dir: Path) -> bool:
    docs_dir = repo_dir / "docs_gathered"
    return docs_dir.is_dir() and any(docs_dir.iterdir())


def archive_previous_run(repo_dir: Path, timestamp: str) -> None:
    quality_dir = repo_dir / "quality"
    control_prompts_dir = repo_dir / "control_prompts"
    if not quality_dir.is_dir():
        return
    archive_dir = repo_dir / "previous_runs" / timestamp / "quality"
    archive_dir.parent.mkdir(parents=True, exist_ok=True)
    if archive_dir.exists():
        shutil.rmtree(archive_dir)
    shutil.copytree(quality_dir, archive_dir)
    shutil.rmtree(quality_dir, ignore_errors=True)
    shutil.rmtree(control_prompts_dir, ignore_errors=True)


def final_artifact_gaps(repo_dir: Path) -> List[str]:
    artifacts = [
        "quality/REQUIREMENTS.md",
        "quality/CONTRACTS.md",
        "quality/COVERAGE_MATRIX.md",
        "quality/COMPLETENESS_REPORT.md",
        "quality/PROGRESS.md",
        "quality/QUALITY.md",
        "quality/RUN_CODE_REVIEW.md",
        "quality/RUN_INTEGRATION_TESTS.md",
        "quality/RUN_SPEC_AUDIT.md",
        "quality/RUN_TDD_TESTS.md",
    ]
    missing = [artifact for artifact in artifacts if not (repo_dir / artifact).is_file()]
    if lib.find_functional_test(repo_dir) is None:
        missing.append("functional test")
    return missing


def run_one_phase(repo_dir: Path, phase: str, phase_list: Sequence[str], args: argparse.Namespace, log_file: Path) -> bool:
    gate = check_phase_gate(repo_dir, phase)
    for message in gate.messages:
        lib.logboth(log_file, lib.log(f"  {message}"))
    if not gate.ok:
        return False

    phase_index = phase_list.index(phase) + 1
    prompt = build_phase_prompt(phase, no_seeds=args.no_seeds)
    output_file = repo_dir / "control_prompts" / f"phase{phase}.output.txt"
    lib.logboth(log_file, lib.log(f"  Phase {phase_index}/{len(phase_list)} ({phase_label(phase)}): {repo_dir.name}"))
    run_prompt(repo_dir, prompt, f"phase{phase}", output_file, log_file, args.runner, args.model)

    quality_dir = repo_dir / "quality"
    if phase == "1":
        lib.logboth(log_file, lib.log(f"  Phase 1 complete: {count_lines(quality_dir / 'EXPLORATION.md')} lines in EXPLORATION.md"))
    elif phase == "2":
        missing = [artifact for artifact in ["quality/REQUIREMENTS.md", "quality/QUALITY.md", "quality/CONTRACTS.md"] if not (repo_dir / artifact).is_file()]
        if missing:
            lib.logboth(log_file, lib.log(f"  WARN Phase 2: missing {' '.join(missing)}"))
        else:
            lib.logboth(log_file, lib.log("  Phase 2 complete: core artifacts generated"))
    elif phase == "3":
        bugs_count = lib.count_matching_lines(quality_dir / "BUGS.md", r"### BUG-")
        patch_count = sum(1 for _ in (quality_dir / "patches").glob("*") if (quality_dir / "patches").is_dir()) if (quality_dir / "patches").is_dir() else 0
        lib.logboth(log_file, lib.log(f"  Phase 3 complete: {bugs_count} bugs, {patch_count} patches"))
    elif phase == "4":
        spec_audits_dir = quality_dir / "spec_audits"
        auditor_reports = sum(1 for path in spec_audits_dir.glob("*auditor*") if path.is_file()) if spec_audits_dir.is_dir() else 0
        lib.logboth(log_file, lib.log(f"  Phase 4 complete: {auditor_reports} auditor reports"))
    elif phase == "5":
        writeups_dir = quality_dir / "writeups"
        results_dir = quality_dir / "results"
        writeups = sum(1 for path in writeups_dir.glob("*") if path.is_file()) if writeups_dir.is_dir() else 0
        red_logs = sum(1 for path in results_dir.glob("BUG-*.red.log") if path.is_file()) if results_dir.is_dir() else 0
        lib.logboth(log_file, lib.log(f"  Phase 5 complete: {writeups} writeups, {red_logs} TDD red-phase logs"))
    elif phase == "6":
        gate_log = quality_dir / "results" / "quality-gate.log"
        gate_result = "unknown"
        if gate_log.is_file():
            lines = gate_log.read_text(encoding="utf-8", errors="ignore").splitlines()
            if lines:
                gate_result = lines[-1]
        lib.logboth(log_file, lib.log(f"  Phase 6 complete: {gate_result}"))
    return True


def run_one_phased(repo_dir: Path, phase_list: Sequence[str], args: argparse.Namespace, timestamp: str) -> int:
    log_file = lib.REPOS_DIR / f"{repo_dir.name}-playbook-{timestamp}.log"
    if not docs_present(repo_dir):
        print(lib.log(f"SKIP: {repo_dir.name} - docs_gathered/ is missing or empty"))
        return 1

    if "1" in phase_list:
        archive_previous_run(repo_dir, timestamp)

    (repo_dir / "control_prompts").mkdir(parents=True, exist_ok=True)
    lib.logboth(log_file, lib.log(f"Starting playbook (phases: {','.join(phase_list)}): {repo_dir.name} (runner={args.runner})"))
    for phase in phase_list:
        if not run_one_phase(repo_dir, phase, phase_list, args, log_file):
            lib.logboth(log_file, lib.log(f"ABORT: Phase {phase} gate failed for {repo_dir.name}"))
            return 1
    lib.logboth(log_file, lib.log(f"Playbook complete (phases: {','.join(phase_list)}): {repo_dir.name}"))

    missing = final_artifact_gaps(repo_dir)
    if missing:
        lib.logboth(log_file, lib.log(f"WARNING: Missing: {' '.join(missing)}"))
    else:
        lib.logboth(log_file, lib.log("All artifacts present"))
    lib.cleanup_repo(repo_dir)
    return 0


def run_one_singlepass(repo_dir: Path, args: argparse.Namespace, timestamp: str) -> int:
    log_file = lib.REPOS_DIR / f"{repo_dir.name}-playbook-{timestamp}.log"
    if not docs_present(repo_dir):
        print(lib.log(f"SKIP: {repo_dir.name} - docs_gathered/ is missing or empty"))
        return 1

    if args.next_iteration:
        if not (repo_dir / "quality" / "EXPLORATION.md").is_file():
            print(lib.log(f"SKIP: {repo_dir.name} - no quality/EXPLORATION.md to iterate on"))
            return 1
        prompt = iteration_prompt(args.strategy)
        pass_label = f"iteration-{args.strategy}"
        lib.logboth(log_file, lib.log(f"Starting iteration ({args.strategy}): {repo_dir.name} (runner={args.runner}, building on existing quality/)"))
    else:
        archive_previous_run(repo_dir, timestamp)
        prompt = single_pass_prompt(no_seeds=args.no_seeds)
        pass_label = "full"
        lib.logboth(log_file, lib.log(f"Starting playbook (single-pass): {repo_dir.name} (runner={args.runner})"))

    control_prompts = repo_dir / "control_prompts"
    control_prompts.mkdir(parents=True, exist_ok=True)
    output_file = control_prompts / "playbook_run.output.txt"
    run_prompt(repo_dir, prompt, pass_label, output_file, log_file, args.runner, args.model)
    lib.logboth(log_file, lib.log(f"Playbook complete: {repo_dir.name}"))

    missing = final_artifact_gaps(repo_dir)
    if missing:
        lib.logboth(log_file, lib.log(f"WARNING: Missing: {' '.join(missing)}"))
    else:
        lib.logboth(log_file, lib.log("All artifacts present"))
    lib.cleanup_repo(repo_dir)
    return 0


def run_one(repo_dir: Path, phase_list: Sequence[str], args: argparse.Namespace, timestamp: str) -> int:
    if phase_list:
        return run_one_phased(repo_dir, phase_list, args, timestamp)
    return run_one_singlepass(repo_dir, args, timestamp)


def count_total_bugs(repo_dirs: Sequence[Path]) -> int:
    return sum(lib.count_bug_writeups(repo_dir) for repo_dir in repo_dirs)


def short_repo_args(repo_dirs: Sequence[Path]) -> List[str]:
    return [lib.repo_short_name(repo_dir) for repo_dir in repo_dirs]


def execute_strategy_all(args: argparse.Namespace, repo_dirs: Sequence[Path], timestamp: str) -> int:
    print("=== Running all iteration strategies: gap -> unfiltered -> parity -> adversarial ===\n")
    for strategy in ALL_STRATEGIES:
        print("=" * 58)
        print(f"  Strategy: {strategy}")
        print("=" * 58)
        before = count_total_bugs(repo_dirs)
        strategy_args = argparse.Namespace(**vars(args))
        strategy_args.strategy = strategy
        status = execute_run(strategy_args, repo_dirs, timestamp=timestamp, suppress_suggestion=True)
        after = count_total_bugs(repo_dirs)
        gained = after - before
        print(f"\n  Strategy {strategy}: {before} -> {after} bugs (+{gained})")
        if status != 0:
            return status
        if gained == 0:
            print("  No new bugs found - stopping early (diminishing returns).")
            break
        print("")
    print("\n=== All-strategy run complete ===")
    print(lib.print_summary(repo_dirs))
    return 0


def display_run_header(args: argparse.Namespace, repo_dirs: Sequence[Path], display_version: str, phase_list: Sequence[str], timestamp: str) -> None:
    print("=== Quality Playbook - Artifact Generation ===")
    print(f"Version:  {display_version}")
    print(f"Runner:   {args.runner}")
    if args.runner == "copilot":
        print(f"Model:    {args.model or lib.DEFAULT_MODEL}")
    else:
        print(f"Model:    {args.model or '(default)'}")
    print(f"No seeds: {args.no_seeds}  (Phase 0/0b skipped when true)")
    print(f"Parallel: {args.parallel}")
    if args.next_iteration:
        print(f"Mode:     next-iteration (strategy: {args.strategy}, builds on existing quality/)")
    elif phase_list:
        print(f"Mode:     phase-by-phase ({','.join(phase_list)}) - separate session per phase with exit gates")
    else:
        print("Mode:     single-prompt (all phases in one session)")
    print(f"Repos:    {' '.join(repo_dir.name for repo_dir in repo_dirs)}")
    print(f"Run ID:   {timestamp}")
    print("")
    print("=== Runner logs (one file per repo) ===")
    for repo_dir in repo_dirs:
        print(lib.REPOS_DIR / f"{repo_dir.name}-playbook-{timestamp}.log")
    print("")


def write_pid_file(entries: Sequence[Tuple[int, str]]) -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PID_FILE.open("w", encoding="utf-8") as handle:
        for pid, repo_name in entries:
            handle.write(f"{pid} {repo_name}\n")


def kill_recorded_processes() -> int:
    if not PID_FILE.is_file():
        print("No PID file found.")
        return 0

    print(f"Killing PIDs from {PID_FILE}:")
    for line in PID_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        pid_text, _, repo_name = line.partition(" ")
        pid = int(pid_text)
        try:
            if os.name != "nt":
                os.killpg(pid, signal.SIGTERM)
            else:
                os.kill(pid, signal.SIGTERM)
            print(f"  kill {pid} [{repo_name}]")
        except ProcessLookupError:
            print(f"  {pid} [{repo_name}] - already exited")
    PID_FILE.unlink(missing_ok=True)
    return 0


def build_worker_command(args: argparse.Namespace, repo_name: str) -> List[str]:
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--sequential"]
    command.append("--claude" if args.runner == "claude" else "--copilot")
    command.append("--no-seeds" if args.no_seeds else "--with-seeds")
    if args.phase:
        command.extend(["--phase", args.phase])
    if args.next_iteration:
        command.append("--next-iteration")
    if args.strategy:
        command.extend(["--strategy", args.strategy])
    if args.model:
        command.extend(["--model", args.model])
    command.append(repo_name)
    return command


def wait_for_processes(processes: Sequence[subprocess.Popen]) -> int:
    failures = 0
    for process in processes:
        if process.wait() != 0:
            failures += 1
    PID_FILE.unlink(missing_ok=True)
    return failures


def execute_run(args: argparse.Namespace, repo_dirs: Sequence[Path], timestamp: Optional[str] = None, suppress_suggestion: bool = False) -> int:
    phase_list = phase_list_from_mode(args.phase)
    run_timestamp = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")

    if args.next_iteration and args.strategy == "all":
        return execute_strategy_all(args, repo_dirs, timestamp=run_timestamp)

    if args.parallel:
        processes = []
        pid_entries = []
        for repo_dir in repo_dirs:
            repo_name = lib.repo_short_name(repo_dir)
            kwargs = {}
            if os.name != "nt":
                kwargs["start_new_session"] = True
            command = build_worker_command(args, repo_name)
            process = subprocess.Popen(command, cwd=str(lib.QPB_DIR), **kwargs)
            processes.append(process)
            pid_entries.append((process.pid, repo_dir.name))
        write_pid_file(pid_entries)
        print(f"PIDs written to {PID_FILE} - stop with: python bin/run_playbook.py --kill\n")
        failures = wait_for_processes(processes)
        print(f"\n=== Parallel run complete. {failures} failures out of {len(repo_dirs)} repos. ===")
        print(lib.print_summary(repo_dirs))
        if not suppress_suggestion:
            print_suggested_next_command(args)
        return 1 if failures else 0

    overall_status = 0
    for repo_dir in repo_dirs:
        overall_status = max(overall_status, run_one(repo_dir, phase_list, args, run_timestamp))
        print("")

    print(lib.print_summary(repo_dirs))
    if not suppress_suggestion:
        print_suggested_next_command(args)
    return overall_status


def print_suggested_next_command(args: argparse.Namespace) -> None:
    runner_flag = " --claude" if args.runner == "claude" else ""
    repo_names = " ".join(args.repos)
    print("-" * 56)
    if args.next_iteration:
        next_name = next_strategy(args.strategy)
        if next_name:
            print("Next iteration suggestion:")
            print(f"  python bin/run_playbook.py{runner_flag} --next-iteration --strategy {next_name} {repo_names}")
        else:
            print("Iteration cycle complete (gap -> unfiltered -> parity -> adversarial).")
            print(f"To start fresh:  python bin/run_playbook.py{runner_flag} {repo_names}")
    else:
        print("Next iteration suggestion:")
        print(f"  python bin/run_playbook.py{runner_flag} --next-iteration --strategy gap {repo_names}")
    print("-" * 56)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.kill:
        return kill_recorded_processes()

    version = lib.detect_skill_version(lib.QPB_DIR)
    if not version:
        print("ERROR: Can't detect version from SKILL.md", file=sys.stderr)
        return 1
    if not ensure_runner_available(args.runner):
        if args.runner == "copilot":
            print("ERROR: 'gh copilot' not available. Install with: gh extension install github/gh-copilot", file=sys.stderr)
        else:
            print("ERROR: 'claude' CLI not found. Install from https://docs.anthropic.com/claude-code", file=sys.stderr)
        return 1

    repo_dirs = lib.resolve_repos(version, args.repos, repos_dir=lib.REPOS_DIR)
    if not repo_dirs:
        print("ERROR: No repos found.", file=sys.stderr)
        return 1

    display_version = lib.detect_repo_skill_version(repo_dirs[0]) or version
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    display_run_header(args, repo_dirs, display_version, phase_list_from_mode(args.phase), timestamp)
    return execute_run(args, repo_dirs, timestamp=timestamp)


if __name__ == "__main__":
    raise SystemExit(main())