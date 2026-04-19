"""Python runner for the Quality Playbook.

Invoke with one or more target-directory paths (relative or absolute) or with
no positional args to run against the current working directory. The runner
does not resolve short names against a benchmark folder — every positional
argument is treated literally as a directory path.
"""

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


ALL_STRATEGIES = ["gap", "unfiltered", "parity", "adversarial"]
VALID_STRATEGIES = frozenset(ALL_STRATEGIES)
PID_FILE = lib.QPB_DIR / ".run_pids"


def parse_strategy_list(value: str) -> List[str]:
    """Parse --strategy value into an ordered list of concrete strategies.

    Accepts a single strategy name, a comma-separated list of names, or the
    shorthand ``all`` (expands to the full canonical order). Rules:

    - Every item must be one of ``gap``, ``unfiltered``, ``parity``, ``adversarial``.
    - ``all`` is only valid as a bare value; it may not appear inside a list.
    - Duplicates (e.g. ``gap,gap``) are rejected.
    - Empty values / whitespace-only tokens are rejected.
    """
    if not value or value.strip() == "":
        raise argparse.ArgumentTypeError("strategy value cannot be empty")

    raw_items = [item.strip() for item in value.split(",")]
    if any(not item for item in raw_items):
        raise argparse.ArgumentTypeError(
            f"strategy value '{value}' contains an empty token"
        )

    if len(raw_items) == 1 and raw_items[0] == "all":
        return list(ALL_STRATEGIES)

    if "all" in raw_items:
        raise argparse.ArgumentTypeError(
            "'all' is only valid as a bare value; it cannot appear inside a "
            "comma-separated strategy list. Use --strategy all to run the full "
            "chain, or list the specific strategies you want."
        )

    seen = set()
    for item in raw_items:
        if item not in VALID_STRATEGIES:
            raise argparse.ArgumentTypeError(
                f"invalid strategy '{item}'. Must be one of: "
                f"{', '.join(ALL_STRATEGIES)}, all"
            )
        if item in seen:
            raise argparse.ArgumentTypeError(
                f"strategy '{item}' appears more than once in '{value}'"
            )
        seen.add(item)

    return raw_items


@dataclass
class GateCheck:
    ok: bool
    messages: List[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Quality Playbook against one or more target directories.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parallel_group = parser.add_mutually_exclusive_group()
    parallel_group.add_argument("--parallel", dest="parallel", action="store_true", default=True, help="Run all targets concurrently (default).")
    parallel_group.add_argument("--sequential", dest="parallel", action="store_false", help="Run targets one after another.")

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
        "--full-run",
        action="store_true",
        help="Fresh main run followed by all four iteration strategies sequentially (gap -> unfiltered -> parity -> adversarial).",
    )
    parser.add_argument(
        "--strategy",
        default=["gap"],
        type=parse_strategy_list,
        help=(
            "Iteration strategy (or ordered list) to use with --next-iteration. "
            "Single: 'gap' | 'unfiltered' | 'parity' | 'adversarial'. "
            "Shorthand: 'all' (= gap,unfiltered,parity,adversarial). "
            "Custom list: comma-separated subset, in the order you want, e.g. "
            "'unfiltered,parity,adversarial'. "
            "Lists reject duplicates and do not accept 'all' as a member."
        ),
    )
    parser.add_argument("--model", help="Runner model override (copilot: gpt-5.4, claude: sonnet/opus/etc).")
    parser.add_argument("--kill", action="store_true", help="Kill processes from the current or last parallel run.")
    parser.add_argument(
        "targets",
        nargs="*",
        help="Target directories to run against (relative or absolute paths). Defaults to the current directory.",
    )
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    return parser


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.kill and not args.targets:
        args.targets = ["."]
    if args.worker:
        args.parallel = False
    if args.next_iteration and args.phase:
        parser.error("--next-iteration is not compatible with --phase. Iteration uses a single prompt.")
    if args.full_run and args.next_iteration:
        parser.error("--full-run and --next-iteration are mutually exclusive. --full-run already chains all iterations after the main run.")
    if args.full_run and args.phase:
        parser.error("--full-run is not compatible with --phase. Full-run uses a single-prompt main run followed by all iterations.")
    if args.phase:
        validate_phase_mode(args.phase, parser)
    if not args.next_iteration and not args.full_run and args.strategy != ["gap"]:
        print("WARNING: --strategy is ignored without --next-iteration or --full-run", file=sys.stderr)
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


def _is_bare_name(raw: str) -> bool:
    """True if ``raw`` is eligible for the version-append fallback.

    Bare name = no path separators, no leading ``.`` / ``..`` / ``~``, not
    absolute. Only bare names get the ``<name>-<version>`` retry — anything
    that looks like an explicit path is taken literally.
    """
    if not raw:
        return False
    if raw.startswith(("/", "~", ".")):
        return False
    if "/" in raw or "\\" in raw:
        return False
    # Windows drive letters ("C:..." etc.).
    if len(raw) >= 2 and raw[1] == ":":
        return False
    return True


def resolve_target_dirs(paths: Sequence[str]) -> Tuple[List[Path], List[str], List[str]]:
    """Resolve user-supplied paths into absolute directories.

    Returns (resolved_dirs, warnings, errors). A missing SKILL.md is a warning
    (the directory may still be a valid target); a non-directory path is an
    error and that entry is dropped.

    Version-append fallback: if a bare name (``chi``, ``virtio``) doesn't
    exist as a directory, re-try ``<name>-<skill_version>`` using the
    SKILL.md version at the QPB root. This replaces the short-name lookup
    the retired ``repos/run_playbook.sh`` provided, without bringing back
    the whole benchmark-folder scanning behavior.
    """
    resolved: List[Path] = []
    warnings: List[str] = []
    errors: List[str] = []
    for raw in paths:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        candidate = candidate.resolve()

        if not candidate.is_dir():
            # Only bare names get the version-append retry. Anything path-like
            # is taken literally.
            version = lib.skill_version() if _is_bare_name(raw) else None
            if version:
                versioned_name = f"{raw}-{version}"
                versioned = (Path.cwd() / versioned_name).resolve()
                if versioned.is_dir():
                    print(
                        f"INFO: resolved '{raw}' to '{versioned_name}' (via SKILL.md version)",
                        file=sys.stderr,
                    )
                    candidate = versioned
                else:
                    errors.append(
                        f"ERROR: '{raw}' is not a directory (resolved to {candidate}; "
                        f"also tried '{versioned_name}')"
                    )
                    continue
            else:
                errors.append(f"ERROR: '{raw}' is not a directory (resolved to {candidate})")
                continue

        if lib.find_installed_skill(candidate) is None:
            warnings.append(
                f"WARN: No SKILL.md found for {candidate}. Expected at "
                ".github/skills/SKILL.md, .claude/skills/quality-playbook/SKILL.md, or SKILL.md "
                "at the target root — the playbook may not be installed there."
            )
        resolved.append(candidate)
    return resolved, warnings, errors


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
        if line_count < 120:
            return GateCheck(ok=False, messages=[f"GATE FAIL Phase 2: EXPLORATION.md is only {line_count} lines (expected 120+)"])
        return GateCheck(ok=True, messages=messages)
    if phase == "3":
        required = [
            "REQUIREMENTS.md", "QUALITY.md", "CONTRACTS.md", "RUN_CODE_REVIEW.md",
            "COVERAGE_MATRIX.md", "COMPLETENESS_REPORT.md",
            "RUN_INTEGRATION_TESTS.md", "RUN_SPEC_AUDIT.md", "RUN_TDD_TESTS.md",
        ]
        missing = [name for name in required if not (quality_dir / name).is_file()]
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
        sa_dir = quality_dir / "spec_audits"
        if not sa_dir.is_dir():
            return GateCheck(ok=False, messages=["GATE FAIL Phase 5: spec_audits/ missing - run Phase 4 first"])
        triage_files = list(sa_dir.glob("*triage*"))
        if not triage_files:
            return GateCheck(ok=False, messages=["GATE FAIL Phase 5: spec_audits/ has no triage file - complete Phase 4 triage first"])
        auditor_files = list(sa_dir.glob("*auditor*"))
        if not auditor_files:
            return GateCheck(ok=False, messages=["GATE FAIL Phase 5: spec_audits/ has no auditor files - complete Phase 4 audit first"])
        progress_content = (quality_dir / "PROGRESS.md").read_text(encoding="utf-8", errors="replace")
        if "- [x] Phase 4" not in progress_content:
            return GateCheck(ok=False, messages=["GATE FAIL Phase 5: Phase 4 not marked complete in PROGRESS.md"])
        if not (quality_dir / "BUGS.md").is_file():
            messages.append("GATE WARN Phase 5: no BUGS.md - Phase 3 may not have run")
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


def log_file_for(repo_dir: Path, timestamp: str) -> Path:
    """Return the log path for a given target directory.

    Logs live next to the target: `{parent}/{name}-playbook-{ts}.log`.
    """
    return repo_dir.parent / f"{repo_dir.name}-playbook-{timestamp}.log"


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
    log_file = log_file_for(repo_dir, timestamp)
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
    log_file = log_file_for(repo_dir, timestamp)
    if not docs_present(repo_dir):
        print(lib.log(f"SKIP: {repo_dir.name} - docs_gathered/ is missing or empty"))
        return 1

    if args.next_iteration:
        if not (repo_dir / "quality" / "EXPLORATION.md").is_file():
            print(lib.log(f"SKIP: {repo_dir.name} - no quality/EXPLORATION.md to iterate on"))
            return 1
        # In the single-strategy path, args.strategy is a list with one item;
        # execute_strategy_list handles multi-item lists one strategy at a time.
        strategy_name = args.strategy[0]
        prompt = iteration_prompt(strategy_name)
        pass_label = f"iteration-{strategy_name}"
        lib.logboth(log_file, lib.log(f"Starting iteration ({strategy_name}): {repo_dir.name} (runner={args.runner}, building on existing quality/)"))
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


def execute_strategy_list(
    args: argparse.Namespace,
    repo_dirs: Sequence[Path],
    strategies: Sequence[str],
    timestamp: str,
) -> int:
    """Run each strategy in ``strategies`` in order, with early stop on zero-gain."""
    chain = " -> ".join(strategies)
    print(f"=== Running iteration strategies: {chain} ===\n")
    for strategy in strategies:
        print("=" * 58)
        print(f"  Strategy: {strategy}")
        print("=" * 58)
        before = count_total_bugs(repo_dirs)
        strategy_args = argparse.Namespace(**vars(args))
        strategy_args.strategy = [strategy]
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
    print("\n=== Strategy-list run complete ===")
    print(lib.print_summary(repo_dirs))
    return 0


def display_run_header(args: argparse.Namespace, repo_dirs: Sequence[Path], display_version: str, phase_list: Sequence[str], timestamp: str) -> None:
    print("=== Quality Playbook - Artifact Generation ===")
    print(f"Version:  {display_version or 'unknown'}")
    print(f"Runner:   {args.runner}")
    if args.runner == "copilot":
        print(f"Model:    {args.model or lib.DEFAULT_MODEL}")
    else:
        print(f"Model:    {args.model or '(default)'}")
    print(f"No seeds: {args.no_seeds}  (Phase 0/0b skipped when true)")
    print(f"Parallel: {args.parallel}")
    if getattr(args, "full_run", False):
        print("Mode:     full-run (fresh main run + all four iteration strategies)")
    elif args.next_iteration:
        strategy_display = ",".join(args.strategy)
        print(f"Mode:     next-iteration (strategy: {strategy_display}, builds on existing quality/)")
    elif phase_list:
        print(f"Mode:     phase-by-phase ({','.join(phase_list)}) - separate session per phase with exit gates")
    else:
        print("Mode:     single-prompt (all phases in one session)")
    print("Targets:")
    for repo_dir in repo_dirs:
        print(f"  {repo_dir}")
    print(f"Run ID:   {timestamp}")
    print("")
    print("=== Runner logs (one file per target) ===")
    for repo_dir in repo_dirs:
        print(log_file_for(repo_dir, timestamp))
    print("")


def pid_file_for_parent() -> Path:
    """Return the PID file path for this parent process.

    Each parent uses its own file (``.run_pids.<parent_pid>``) so that
    concurrent parallel launches from different terminals don't overwrite
    each other's worker registrations. ``kill_recorded_processes`` globs
    every matching file to kill workers across all parents.
    """
    return PID_FILE.parent / f"{PID_FILE.name}.{os.getpid()}"


def discover_pid_files() -> List[Path]:
    """Return all per-parent PID files currently on disk."""
    parent = PID_FILE.parent
    if not parent.is_dir():
        return []
    return sorted(parent.glob(f"{PID_FILE.name}.*"))


def write_pid_file(entries: Sequence[Tuple[int, str]]) -> Path:
    """Write this parent's worker PIDs to its own file. Returns the path."""
    path = pid_file_for_parent()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for pid, repo_name in entries:
            handle.write(f"{pid} {repo_name}\n")
    return path


def _pkill_fallback() -> None:
    """Best-effort pattern kill when no PID file is available (e.g. after a crash)."""
    patterns = [
        "bin/run_playbook.py",
        "claude -p",
        "claude --model",
    ]
    for pattern in patterns:
        try:
            result = subprocess.run(
                ["pkill", "-f", pattern],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except FileNotFoundError:
            print("  pkill not available; cannot do pattern-based cleanup")
            return
        if result.returncode == 0:
            print(f"  killed processes matching: {pattern}")
        else:
            print(f"  no processes matched: {pattern}")


def kill_recorded_processes() -> int:
    pid_files = discover_pid_files()
    if not pid_files:
        print("No PID files found. Falling back to pkill:")
        _pkill_fallback()
        return 0

    total_killed = 0
    for pid_file in pid_files:
        print(f"Killing PIDs from {pid_file}:")
        for line in pid_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            pid_text, _, repo_name = line.partition(" ")
            try:
                pid = int(pid_text)
            except ValueError:
                continue
            try:
                if os.name != "nt":
                    os.killpg(pid, signal.SIGTERM)
                else:
                    os.kill(pid, signal.SIGTERM)
                print(f"  kill {pid} [{repo_name}]")
                total_killed += 1
            except ProcessLookupError:
                print(f"  {pid} [{repo_name}] - already exited")
        pid_file.unlink(missing_ok=True)
    if total_killed == 0:
        print("All recorded processes had already exited.")
    return 0


def build_worker_command(args: argparse.Namespace, target_path: str) -> List[str]:
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--sequential"]
    command.append("--claude" if args.runner == "claude" else "--copilot")
    command.append("--no-seeds" if args.no_seeds else "--with-seeds")
    if args.phase:
        command.extend(["--phase", args.phase])
    if args.next_iteration:
        command.append("--next-iteration")
    if getattr(args, "full_run", False):
        command.append("--full-run")
    if args.strategy:
        command.extend(["--strategy", ",".join(args.strategy)])
    if args.model:
        command.extend(["--model", args.model])
    command.append(target_path)
    return command


def wait_for_processes(processes: Sequence[subprocess.Popen], pid_file: Path) -> int:
    failures = 0
    for process in processes:
        if process.wait() != 0:
            failures += 1
    # Remove only this parent's file; peer parents keep their own.
    pid_file.unlink(missing_ok=True)
    return failures


def execute_run(args: argparse.Namespace, repo_dirs: Sequence[Path], timestamp: Optional[str] = None, suppress_suggestion: bool = False) -> int:
    phase_list = phase_list_from_mode(args.phase)
    run_timestamp = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")

    if getattr(args, "full_run", False):
        print("=== Full run: fresh main run + all iteration strategies ===\n")
        main_args = argparse.Namespace(**vars(args))
        main_args.full_run = False
        main_args.next_iteration = False
        main_args.strategy = ["gap"]
        main_status = execute_run(main_args, repo_dirs, timestamp=run_timestamp, suppress_suggestion=True)
        if main_status != 0:
            print("\n=== Full run halted: main run reported failures; skipping iterations. ===")
            return main_status
        iter_args = argparse.Namespace(**vars(args))
        iter_args.full_run = False
        iter_args.next_iteration = True
        iter_args.strategy = list(ALL_STRATEGIES)
        return execute_run(iter_args, repo_dirs, timestamp=run_timestamp, suppress_suggestion=suppress_suggestion)

    # Multi-strategy iteration: chain each strategy in order with early stop.
    # Single-strategy iteration falls through to the regular parallel/sequential path.
    if args.next_iteration and len(args.strategy) > 1:
        return execute_strategy_list(args, repo_dirs, args.strategy, timestamp=run_timestamp)

    if args.parallel:
        processes = []
        pid_entries = []
        for repo_dir in repo_dirs:
            kwargs = {}
            if os.name != "nt":
                kwargs["start_new_session"] = True
            command = build_worker_command(args, str(repo_dir))
            process = subprocess.Popen(command, cwd=str(lib.QPB_DIR), **kwargs)
            processes.append(process)
            pid_entries.append((process.pid, repo_dir.name))
        pid_file_path = write_pid_file(pid_entries)
        print(f"PIDs written to {pid_file_path} - stop with: python bin/run_playbook.py --kill\n")
        failures = wait_for_processes(processes, pid_file_path)
        print(f"\n=== Parallel run complete. {failures} failures out of {len(repo_dirs)} targets. ===")
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
    model_flag = f" --model {shlex.quote(args.model)}" if getattr(args, "model", None) else ""
    interpreter = os.path.basename(sys.executable) if sys.executable else "python"
    script_path = sys.argv[0] if sys.argv and sys.argv[0] else "bin/run_playbook.py"
    invocation = f"{interpreter} {shlex.quote(script_path)}"
    prefix = f"{invocation}{runner_flag}{model_flag}"
    target_args = " ".join(shlex.quote(name) for name in args.targets)
    print("-" * 56)

    # If the user ran a strict subset of phases, the right next step is the
    # remaining phases — NOT an iteration. Iterations only make sense after the
    # full 6-phase cycle has completed. If --phase all was used (or the user
    # covered every phase explicitly), fall through to the iteration logic.
    phase_list = phase_list_from_mode(getattr(args, "phase", None))
    if phase_list:
        all_phases = {"1", "2", "3", "4", "5", "6"}
        ran = set(phase_list)
        remaining = sorted(all_phases - ran, key=int)
        if remaining:
            remaining_spec = ",".join(remaining)
            print("Next phase suggestion:")
            print(f"  {prefix} --phase {remaining_spec} {target_args}".rstrip())
            print("(You can swap --model between phase groups — e.g. Opus for 1-2, Sonnet for 3-6.)")
            print("-" * 56)
            return
        # All six phases covered — fall through to the iteration suggestion.

    if args.next_iteration:
        # Suggestion is based on the successor of the LAST strategy in the list.
        # Single-item lists behave the same as the old single-strategy case.
        last_strategy = args.strategy[-1] if args.strategy else "gap"
        next_name = next_strategy(last_strategy)
        if next_name:
            print("Next iteration suggestion:")
            print(f"  {prefix} --next-iteration --strategy {next_name} {target_args}".rstrip())
        else:
            print("Iteration cycle complete (gap -> unfiltered -> parity -> adversarial).")
            print(f"To start fresh:  {prefix} {target_args}".rstrip())
    else:
        print("Next iteration suggestion:")
        print(f"  {prefix} --next-iteration --strategy gap {target_args}".rstrip())
    print("-" * 56)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.kill:
        return kill_recorded_processes()

    if not ensure_runner_available(args.runner):
        if args.runner == "copilot":
            print("ERROR: 'gh copilot' not available. Install with: gh extension install github/gh-copilot", file=sys.stderr)
        else:
            print("ERROR: 'claude' CLI not found. Install from https://docs.anthropic.com/claude-code", file=sys.stderr)
        return 1

    repo_dirs, warnings, errors = resolve_target_dirs(args.targets)
    for message in warnings:
        print(message, file=sys.stderr)
    for message in errors:
        print(message, file=sys.stderr)
    if errors:
        return 1
    if not repo_dirs:
        print("ERROR: No target directories to run against.", file=sys.stderr)
        return 1

    display_version = lib.detect_repo_skill_version(repo_dirs[0])
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    display_run_header(args, repo_dirs, display_version, phase_list_from_mode(args.phase), timestamp)
    return execute_run(args, repo_dirs, timestamp=timestamp)


if __name__ == "__main__":
    raise SystemExit(main())
