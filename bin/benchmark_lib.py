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
from typing import Iterable, List, Optional, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
QPB_DIR = SCRIPT_DIR.parent
REPOS_DIR = QPB_DIR / "repos"
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
SHORT_VERSIONED_DIR_PATTERN = "{short}-{version}"


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
    base_dir = qpb_dir or QPB_DIR
    return _read_version(base_dir / "SKILL.md")


def detect_repo_skill_version(repo_dir: Path) -> str:
    return _read_version(repo_dir / ".github" / "skills" / "SKILL.md")


def version_key(version: str) -> Tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def find_repo_dir(short: str, version: str, repos_dir: Optional[Path] = None) -> Optional[Path]:
    base_dir = repos_dir or REPOS_DIR
    exact = base_dir / SHORT_VERSIONED_DIR_PATTERN.format(short=short, version=version)
    if exact.is_dir():
        return exact

    pattern = re.compile(rf"^{re.escape(short)}-([0-9]+(?:\.[0-9]+)+)$")
    candidates = []
    if not base_dir.is_dir():
        return None
    for child in base_dir.iterdir():
        if not child.is_dir():
            continue
        match = pattern.match(child.name)
        if match:
            candidates.append((version_key(match.group(1)), child))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[-1][1]


def resolve_repos(version: str, repo_names: Sequence[str], repos_dir: Optional[Path] = None) -> List[Path]:
    resolved: List[Path] = []
    base_dir = repos_dir or REPOS_DIR
    for name in repo_names:
        repo_dir = find_repo_dir(name, version, repos_dir=base_dir)
        if repo_dir is not None:
            resolved.append(repo_dir)
        else:
            print(log(f"SKIP: {name} - no matching directory found"), file=sys.stderr)
    return resolved


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


def cleanup_repo(repo_dir: Path) -> bool:
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

    print(log(f"  Reverting uncommitted changes in {repo_dir.name}"))
    subprocess.run(
        ["git", "checkout", "."],
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


def repo_short_name(repo_dir: Path) -> str:
    match = re.match(r"^(?P<short>.+?)-[0-9]+(?:\.[0-9]+)+$", repo_dir.name)
    return match.group("short") if match else repo_dir.name


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