"""Shared helpers for Quality Playbook benchmark tooling."""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
QPB_DIR = SCRIPT_DIR.parent
DEFAULT_MODEL = os.environ.get("QPB_MODEL", "gpt-5.4")

FUNCTIONAL_TEST_PATTERNS = (
    "test_functional.*",
    "functional.test.*",
    "functional_test.*",
    "FunctionalTest.*",
    "FunctionalSpec.*",
    "test_functional_test.*",
)

REGRESSION_TEST_PATTERNS = (
    "test_regression.*",
    "regression_test.*",
    "test_regression_test.*",
    "RegressionTest.*",
)

EXCLUDED_PARTS = {"target", "node_modules", "__pycache__"}
EXCLUDED_SUFFIXES = {".class", ".pyc"}
VERSION_PATTERN = re.compile(r"^\s*(?:version:|\*\*Version:\*\*)\s*([0-9]+(?:\.[0-9]+)+)\b", re.IGNORECASE)

SKILL_INSTALL_LOCATIONS = (
    Path(".github") / "skills" / "SKILL.md",
    Path(".claude") / "skills" / "quality-playbook" / "SKILL.md",
    Path("SKILL.md"),
)


@dataclass(frozen=True)
class SummaryRow:
    name: str
    requirements: str
    bugs: str
    tdd: str
    integration: str
    functional: str
    regression: str
    tier1: int
    tier2: int
    tier3: int


def log(message: str) -> str:
    return f"{datetime.now():%H:%M:%S} {message}"


def logboth(log_file: Path, message: str, echo: Optional[bool] = None) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(message.rstrip("\n") + "\n")
    if echo is None:
        echo = sys.stdout.isatty()
    if echo:
        print(message)


def _read_version(path: Path) -> str:
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = VERSION_PATTERN.match(line)
        if match:
            return match.group(1)
    return ""


def detect_skill_version(qpb_dir: Optional[Path] = None) -> str:
    """Read the `version:` value from the root SKILL.md (utility helper)."""
    base_dir = qpb_dir or QPB_DIR
    return _read_version(base_dir / "SKILL.md")


def detect_repo_skill_version(repo_dir: Path) -> str:
    """Read the `version:` value from an installed-copy SKILL.md for display."""
    for rel in SKILL_INSTALL_LOCATIONS:
        version = _read_version(repo_dir / rel)
        if version:
            return version
    return ""


def find_installed_skill(target_dir: Path) -> Optional[Path]:
    """Return the first installed SKILL.md beneath `target_dir`, or None.

    Searched in the same order as the skill's own fallback list:
    `.github/skills/SKILL.md`, `.claude/skills/quality-playbook/SKILL.md`,
    then a plain `SKILL.md` at the directory root.
    """
    for rel in SKILL_INSTALL_LOCATIONS:
        candidate = target_dir / rel
        if candidate.is_file():
            return candidate
    return None


def _iter_quality_files(repo_dir: Path) -> Iterable[Path]:
    quality_dir = repo_dir / "quality"
    if not quality_dir.is_dir():
        return []
    return quality_dir.rglob("*")


def _matches_patterns(path: Path, patterns: Sequence[str]) -> bool:
    if not path.is_file():
        return False
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    return any(fnmatch.fnmatch(path.name, pattern) for pattern in patterns)


def _find_test_file(repo_dir: Path, patterns: Sequence[str]) -> Optional[Path]:
    matches = [path for path in _iter_quality_files(repo_dir) if _matches_patterns(path, patterns)]
    return sorted(matches)[0] if matches else None


def find_functional_test(repo_dir: Path) -> Optional[Path]:
    return _find_test_file(repo_dir, FUNCTIONAL_TEST_PATTERNS)


def find_regression_test(repo_dir: Path) -> Optional[Path]:
    return _find_test_file(repo_dir, REGRESSION_TEST_PATTERNS)


# Paths that cleanup_repo MUST NOT revert. These are playbook run outputs and
# inputs: reverting them after a run would destroy the very artifacts we just
# produced (quality/, control_prompts/), the archive from the prior run
# (previous_runs/), or the docs that feed the next run (docs_gathered/). For
# bootstrap targets where these trees are tracked in git, the difference matters.
PROTECTED_PREFIXES = (
    "quality/",
    "control_prompts/",
    "previous_runs/",
    "docs_gathered/",
)


def _parse_porcelain_path(line: str) -> Optional[str]:
    """Extract the affected path from a ``git status --porcelain`` line.

    Returns the post-rename path for rename rows (``R  old -> new``), the plain
    filename otherwise, or None if the line is too short to carry a path.
    """
    if len(line) < 4:
        return None
    rest = line[3:]
    if "->" in rest:
        rest = rest.split("->", 1)[1].strip()
    return rest.strip()


def _is_protected(path: str) -> bool:
    """True if a porcelain path falls under a run-output directory we must not revert."""
    return any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def cleanup_repo(repo_dir: Path) -> bool:
    """Revert incidental tracked-file edits the agent made, leaving run outputs alone.

    Only tracked files OUTSIDE the protected run-output directories are considered.
    Untracked files are never touched (``git checkout`` cannot affect them anyway).
    Returns True iff at least one file was reverted; False (and prints nothing) if
    the repo was either clean or only had protected-path changes.
    """
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(repo_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if status.returncode != 0 or not status.stdout.strip():
        return False

    to_revert: List[str] = []
    for line in status.stdout.splitlines():
        if not line:
            continue
        xy = line[:2]
        if xy == "??":
            continue  # untracked — not reachable via git checkout
        path = _parse_porcelain_path(line)
        if path is None or _is_protected(path):
            continue
        if path not in to_revert:
            to_revert.append(path)

    if not to_revert:
        return False

    preview = ", ".join(to_revert[:3])
    if len(to_revert) > 3:
        preview += f", +{len(to_revert) - 3} more"
    print(log(f"  Tidied {len(to_revert)} tracked file(s) in {repo_dir.name}: {preview}"))
    subprocess.run(
        ["git", "checkout", "--", *to_revert],
        cwd=str(repo_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return True


def require_copilot() -> bool:
    try:
        result = subprocess.run(
            ["gh", "copilot", "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


def count_matching_lines(path: Path, pattern: str) -> int:
    if not path.is_file():
        return 0
    regex = re.compile(pattern)
    return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if regex.search(line))


def count_bug_writeups(repo_dir: Path) -> int:
    writeups_dir = repo_dir / "quality" / "writeups"
    if not writeups_dir.is_dir():
        return 0
    return sum(1 for path in writeups_dir.glob("BUG-*.md") if path.is_file())


def _marker(path: Path, exists_marker: str = "Y", missing_marker: str = "N") -> str:
    return exists_marker if path.exists() else missing_marker


def build_summary_rows(repo_dirs: Sequence[Path]) -> List[SummaryRow]:
    rows: List[SummaryRow] = []
    for repo_dir in repo_dirs:
        requirements = _marker(repo_dir / "quality" / "REQUIREMENTS.md")
        bugs = "Y" if (repo_dir / "quality" / "BUGS.md").is_file() else "."
        tdd = "Y" if (repo_dir / "quality" / "TDD_TRACEABILITY.md").is_file() else "."
        integration = _marker(repo_dir / "quality" / "RUN_INTEGRATION_TESTS.md")
        functional = "Y" if find_functional_test(repo_dir) else "N"
        regression = "Y" if find_regression_test(repo_dir) else "."
        requirements_file = repo_dir / "quality" / "REQUIREMENTS.md"
        rows.append(
            SummaryRow(
                name=repo_dir.name,
                requirements=requirements,
                bugs=bugs,
                tdd=tdd,
                integration=integration,
                functional=functional,
                regression=regression,
                tier1=count_matching_lines(requirements_file, r"\[Tier 1\]"),
                tier2=count_matching_lines(requirements_file, r"\[Tier 2\]"),
                tier3=count_matching_lines(requirements_file, r"\[Tier 3\]"),
            )
        )
    return rows


def print_summary(repo_dirs: Sequence[Path]) -> str:
    lines = ["", "=== Artifact Summary ==="]
    lines.append(f"{'Repo':<22} {'REQS':>4} {'BUGS':>4} {'TDD':>4} {'INTG':>4} {'FUNC':>4} {'REGR':>4} {'T1':>5} {'T2':>5} {'T3':>5}")
    lines.append("-" * 78)
    for row in build_summary_rows(repo_dirs):
        lines.append(
            f"{row.name:<22} {row.requirements:>4} {row.bugs:>4} {row.tdd:>4} {row.integration:>4} {row.functional:>4} {row.regression:>4} {row.tier1:>5} {row.tier2:>5} {row.tier3:>5}"
        )

    lines.append("")
    lines.append("=== Quality Checks ===")
    for repo_dir in repo_dirs:
        requirements_file = repo_dir / "quality" / "REQUIREMENTS.md"
        if not requirements_file.is_file():
            continue
        integration_file = repo_dir / "quality" / "RUN_INTEGRATION_TESTS.md"
        tdd_file = repo_dir / "quality" / "TDD_TRACEABILITY.md"
        ag = count_matching_lines(requirements_file, r"architectural-guidance")
        req = count_matching_lines(requirements_file, r"### REQ-")
        uc = count_matching_lines(requirements_file, r"### UC-")
        uc_int = count_matching_lines(integration_file, r"UC-")
        infra_int = count_matching_lines(integration_file, r"\[Infrastructure\]")
        tdd_verified = count_matching_lines(tdd_file, r"TDD verified")
        tdd_failed = count_matching_lines(tdd_file, r"Green failed|Red failed")
        flags = []
        if ag > 3:
            flags.append("WARN:arch-guidance>3")
        if uc == 0:
            flags.append("WARN:no-use-cases")
        if uc_int == 0:
            flags.append("WARN:no-UC-traceability")
        if tdd_failed > 0:
            flags.append(f"WARN:tdd-failures={tdd_failed}")
        suffix = f" {' '.join(flags)}" if flags else ""
        lines.append(
            f"{repo_dir.name}: {req} reqs, {uc} UCs, {ag} arch-guidance, intg(UC={uc_int} infra={infra_int}), tdd(verified={tdd_verified} failed={tdd_failed}){suffix}"
        )
    lines.append("")
    return "\n".join(lines)
