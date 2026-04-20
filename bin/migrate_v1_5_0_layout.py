"""migrate_v1_5_0_layout.py — idempotent one-shot for the v1.5.0 layout move.

Brings a pre-v1.5.0 repo into compliance with the consolidated `quality/`
layout expected by the orchestrator, gate, and SKILL.md prose after Phase 5a.

Pre-v1.5.0 layout (the source shape this script migrates):

    <repo>/
      control_prompts/             # per-phase prompt captures at repo root
      previous_runs/<ts>/quality/  # archived prior runs, nested one level
      quality/                     # current run artifacts

v1.5.0 target layout:

    <repo>/
      quality/
        control_prompts/           # moved from <repo>/control_prompts/
        runs/<ts>/quality/         # renamed from <repo>/previous_runs/<ts>/quality/
        ... current run artifacts  # unchanged
        RUN_INDEX.md               # generated here, append-only across future runs

For each subfolder that lands under `quality/runs/<ts>/`, a best-effort
`INDEX.md` is backfilled from git log (for timestamp bounds) and surviving
artifacts (BUGS.md / REQUIREMENTS.md / PROGRESS.md) for the tier / severity /
disposition counts. Fields that cannot be recovered from the archived
content are stored as the string `"unknown"`.

Idempotent semantics: running the script twice is identical to running it
once. Already-migrated state is detected by looking at repo-root
`control_prompts/` and `previous_runs/` — absent = already done, present =
execute the move(s). Half-migrated state (one missing, one present)
completes the remaining half rather than erroring.

Dry-run mode (`--dry-run`) prints the planned moves and writes without
touching the filesystem.

Usage:

    python -m bin.migrate_v1_5_0_layout <repo-path>        # execute
    python -m bin.migrate_v1_5_0_layout <repo-path> --dry-run

`<repo-path>` defaults to the current working directory.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SEVERITY_LITERALS = ("HIGH", "MEDIUM", "LOW")
DISPOSITION_LITERALS = (
    "code-fix",
    "spec-fix",
    "upstream-spec-issue",
    "mis-read",
    "deferred",
)
TIER_LITERALS = ("1", "2", "3", "4", "5", "unknown")

_VERSION_HEADER_PATTERN = re.compile(r"Quality Playbook v([0-9]+(?:\.[0-9]+)+)", re.IGNORECASE)
_BUG_HEADING_PATTERN = re.compile(r"^###\s+BUG-([A-Za-z0-9]+)\s*$", re.MULTILINE)
_REQ_HEADING_PATTERN = re.compile(r"^###\s+REQ-([A-Za-z0-9]+)", re.MULTILINE)
_SEVERITY_PATTERN = re.compile(r"\*\*Severity\*\*\s*[:.-]\s*(HIGH|MEDIUM|LOW)", re.IGNORECASE)
_PHASE_CHECK_PATTERN = re.compile(r"^-\s*\[x\]\s*Phase\s*([0-9a-zA-Z]+)", re.MULTILINE)
_GATE_VERDICT_PATTERN = re.compile(r"gate_result['\"]?\s*[:=]\s*['\"](PASS|FAIL|WARN)['\"]?", re.IGNORECASE)


class MigrationError(Exception):
    """Raised on unrecoverable migration failures."""


# ---------------------------------------------------------------------------
# Plan / state detection
# ---------------------------------------------------------------------------


def _legacy_previous_runs(repo: Path) -> Path:
    return repo / "previous_runs"


def _legacy_control_prompts(repo: Path) -> Path:
    return repo / "control_prompts"


def _quality_runs(repo: Path) -> Path:
    return repo / "quality" / "runs"


def _quality_control_prompts(repo: Path) -> Path:
    return repo / "quality" / "control_prompts"


def already_migrated(repo: Path) -> bool:
    """Return True iff every legacy location is absent and at least one v1.5.0 location exists.

    A repo that never had the legacy folders is also considered migrated (nothing to do).
    """
    legacy_absent = (
        not _legacy_previous_runs(repo).exists()
        and not _legacy_control_prompts(repo).exists()
    )
    return legacy_absent


# ---------------------------------------------------------------------------
# Git + filesystem helpers for INDEX backfill
# ---------------------------------------------------------------------------


def _git_available(repo: Path) -> bool:
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=repo,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return True


def _git_log_timestamps(repo: Path, folder: Path) -> Tuple[Optional[str], Optional[str]]:
    """Return (first_commit_iso, last_commit_iso) for commits touching `folder`.

    Both entries are None if git log returns nothing (folder untracked) or git
    is not available.
    """
    try:
        rel = folder.relative_to(repo).as_posix()
    except ValueError:
        return None, None
    try:
        proc = subprocess.run(
            ["git", "log", "--reverse", "--format=%aI", "--", rel],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None, None
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        return None, None
    return lines[0], lines[-1]


def _fs_mtimes(folder: Path) -> Tuple[str, str]:
    """Fallback (min mtime, max mtime) as ISO 8601 UTC timestamps."""
    mtimes: List[float] = []
    for path in folder.rglob("*"):
        if path.is_file():
            try:
                mtimes.append(path.stat().st_mtime)
            except OSError:
                continue
    if not mtimes:
        try:
            stat = folder.stat()
            mtimes.append(stat.st_mtime)
        except OSError:
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            return now, now
    first = datetime.fromtimestamp(min(mtimes), tz=timezone.utc).replace(microsecond=0)
    last = datetime.fromtimestamp(max(mtimes), tz=timezone.utc).replace(microsecond=0)
    return first.isoformat().replace("+00:00", "Z"), last.isoformat().replace("+00:00", "Z")


def _resolve_run_bounds(repo: Path, run_folder: Path) -> Tuple[str, str, int]:
    start: Optional[str] = None
    end: Optional[str] = None
    if _git_available(repo):
        start, end = _git_log_timestamps(repo, run_folder)
    if start is None or end is None:
        fs_start, fs_end = _fs_mtimes(run_folder)
        start = start or fs_start
        end = end or fs_end
    duration = _duration_seconds(start, end)
    return start, end, duration


def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        # fromisoformat handles `+00:00` but not `Z`; normalize.
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _duration_seconds(start: str, end: str) -> int:
    a = _parse_iso(start)
    b = _parse_iso(end)
    if a is None or b is None:
        return 0
    delta = int((b - a).total_seconds())
    return max(delta, 0)


# ---------------------------------------------------------------------------
# Content extraction for the summary block
# ---------------------------------------------------------------------------


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _extract_qpb_version(run_folder: Path) -> str:
    for name in ("BUGS.md", "REQUIREMENTS.md", "PROGRESS.md", "QUALITY.md"):
        text = _read_text(run_folder / "quality" / name)
        if not text:
            text = _read_text(run_folder / name)
        if not text:
            continue
        match = _VERSION_HEADER_PATTERN.search(text)
        if match:
            return match.group(1)
    return "unknown"


def _extract_bug_counts(run_folder: Path) -> Dict[str, int]:
    text = _read_text(run_folder / "quality" / "BUGS.md") or _read_text(run_folder / "BUGS.md")
    counts: Dict[str, int] = {level: 0 for level in SEVERITY_LITERALS}
    counts.update({d: 0 for d in DISPOSITION_LITERALS})
    if not text:
        return counts

    bug_segments = _split_by_heading(text, _BUG_HEADING_PATTERN)
    for segment in bug_segments:
        sev_match = _SEVERITY_PATTERN.search(segment)
        if sev_match:
            counts[sev_match.group(1).upper()] += 1
        # Legacy BUGS.md has no disposition field; v1.5.0 will populate these.
        for disposition in DISPOSITION_LITERALS:
            if re.search(rf"\*\*disposition\*\*\s*[:.-]\s*{re.escape(disposition)}", segment, re.IGNORECASE):
                counts[disposition] += 1
    return counts


def _extract_req_tier_counts(run_folder: Path) -> Dict[str, int]:
    text = _read_text(run_folder / "quality" / "REQUIREMENTS.md") or _read_text(run_folder / "REQUIREMENTS.md")
    counts: Dict[str, int] = {tier: 0 for tier in TIER_LITERALS}
    if not text:
        return counts
    segments = _split_by_heading(text, _REQ_HEADING_PATTERN)
    for segment in segments:
        # Try to match explicit "tier N" markers; pre-v1.5.0 REQs have none.
        tier_match = re.search(r"\*\*Tier\*\*\s*[:.-]\s*([1-5])", segment, re.IGNORECASE)
        if tier_match:
            counts[tier_match.group(1)] += 1
        else:
            counts["unknown"] += 1
    return counts


def _split_by_heading(text: str, pattern: re.Pattern) -> List[str]:
    positions = [m.start() for m in pattern.finditer(text)]
    if not positions:
        return []
    positions.append(len(text))
    return [text[positions[i]:positions[i + 1]] for i in range(len(positions) - 1)]


def _extract_phases_executed(run_folder: Path) -> List[Dict[str, str]]:
    text = _read_text(run_folder / "quality" / "PROGRESS.md") or _read_text(run_folder / "PROGRESS.md")
    if not text:
        return []
    phases: List[Dict[str, str]] = []
    for match in _PHASE_CHECK_PATTERN.finditer(text):
        phases.append(
            {
                "phase_id": match.group(1),
                "model": "unknown",
                "start": "unknown",
                "end": "unknown",
                "exit_status": "unknown",
            }
        )
    return phases


def _extract_gate_verdict(run_folder: Path) -> str:
    # Prefer run-metadata JSON when present.
    results_dir = run_folder / "quality" / "results"
    if results_dir.is_dir():
        for candidate in sorted(results_dir.glob("run-*.json")):
            raw = _read_text(candidate)
            match = _GATE_VERDICT_PATTERN.search(raw)
            if match:
                return {"PASS": "pass", "FAIL": "fail", "WARN": "partial"}.get(match.group(1).upper(), "partial")
    progress = _read_text(run_folder / "quality" / "PROGRESS.md") or _read_text(run_folder / "PROGRESS.md")
    if "Terminal Gate Verification" in progress:
        # Heuristic — v1.4.x marks runs PASS under this section for successful gates.
        if re.search(r"gate_result\s*[:.-]?\s*pass|PASS\b", progress[progress.find("Terminal Gate"):]):
            return "pass"
    return "unknown"


def _collect_artifacts(run_folder: Path) -> List[str]:
    artifacts: List[str] = []
    for path in sorted(run_folder.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "INDEX.md" and path.parent == run_folder:
            continue
        try:
            artifacts.append(path.relative_to(run_folder).as_posix())
        except ValueError:
            continue
    return artifacts


# ---------------------------------------------------------------------------
# INDEX.md + RUN_INDEX.md rendering
# ---------------------------------------------------------------------------


def build_index_payload(repo: Path, run_folder: Path) -> Dict[str, object]:
    start, end, duration = _resolve_run_bounds(repo, run_folder)
    gate_verdict = _extract_gate_verdict(run_folder)
    if gate_verdict not in ("pass", "fail", "partial"):
        gate_verdict = "partial"
    return {
        "run_timestamp_start": start,
        "run_timestamp_end": end,
        "duration_seconds": duration,
        "qpb_version": _extract_qpb_version(run_folder),
        "target_repo_path": ".",
        "target_repo_git_sha": "unknown",
        "target_project_type": "Code",  # TODO(v1.5.1): detect Code / Skill / Hybrid.
        "phases_executed": _extract_phases_executed(run_folder),
        "summary": {
            "requirements": _extract_req_tier_counts(run_folder),
            "bugs": _extract_bug_counts(run_folder),
            "gate_verdict": gate_verdict,
        },
        "artifacts": _collect_artifacts(run_folder),
    }


def render_index_markdown(run_id: str, payload: Dict[str, object]) -> str:
    body = json.dumps(payload, indent=2, sort_keys=False)
    return (
        f"# Run Index — {run_id}\n\n"
        f"Playbook run archived to `quality/runs/{run_id}/`. This file was\n"
        f"backfilled by `bin/migrate_v1_5_0_layout.py` from git log and the\n"
        "surviving artifacts; fields marked `\"unknown\"` could not be recovered\n"
        "from the archived content.\n\n"
        "```json\n"
        f"{body}\n"
        "```\n"
    )


def render_run_index_row(run_id: str, payload: Dict[str, object]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    bugs = summary.get("bugs", {}) if isinstance(summary.get("bugs"), dict) else {}
    bug_count = sum(int(bugs.get(s, 0)) for s in SEVERITY_LITERALS if isinstance(bugs.get(s, 0), int))
    return (
        f"| {run_id} "
        f"| {payload.get('qpb_version', 'unknown')} "
        f"| {payload.get('target_project_type', 'Code')} "
        f"| {summary.get('gate_verdict', 'partial')} "
        f"| {bug_count} "
        f"| [INDEX.md](quality/runs/{run_id}/INDEX.md) |"
    )


def render_run_index_header() -> str:
    return (
        "# QPB RUN_INDEX\n\n"
        "Append-only index of every archived run under `quality/runs/`. One row\n"
        "per archived run. Maintained by `bin/migrate_v1_5_0_layout.py` at\n"
        "migration time and by the orchestrator's `archive_run()` at run time.\n"
        "Rows are never rewritten; a run's `INDEX.md` is the authoritative per-run\n"
        "record.\n\n"
        "| Run | QPB version | Project type | Gate verdict | Bug count | Per-run INDEX |\n"
        "|-----|-------------|--------------|--------------|-----------|----------------|\n"
    )


# ---------------------------------------------------------------------------
# Plan + execute
# ---------------------------------------------------------------------------


class Planner:
    """Collect planned moves and writes; execute or print them."""

    def __init__(self, repo: Path, *, dry_run: bool = False) -> None:
        self.repo = repo
        self.dry_run = dry_run
        self.actions: List[str] = []

    def _log(self, msg: str) -> None:
        self.actions.append(msg)
        prefix = "[dry-run]" if self.dry_run else "[migrate]"
        print(f"{prefix} {msg}")

    def move_tree(self, src: Path, dst: Path) -> None:
        self._log(f"move {src.relative_to(self.repo)} -> {dst.relative_to(self.repo)}")
        if self.dry_run:
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            raise MigrationError(
                f"cannot move {src} -> {dst}: destination already exists. Manual "
                "cleanup required."
            )
        shutil.move(str(src), str(dst))

    def write_text(self, path: Path, content: str) -> None:
        self._log(f"write {path.relative_to(self.repo)} ({len(content)} bytes)")
        if self.dry_run:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def migrate(repo: Path, *, dry_run: bool = False) -> Planner:
    repo = repo.resolve()
    if not repo.is_dir():
        raise MigrationError(f"{repo} is not a directory")
    planner = Planner(repo, dry_run=dry_run)
    legacy_prev = _legacy_previous_runs(repo)
    legacy_cp = _legacy_control_prompts(repo)

    if not legacy_prev.exists() and not legacy_cp.exists():
        planner._log("no legacy directories present — nothing to move")
    else:
        if legacy_prev.exists():
            planner.move_tree(legacy_prev, _quality_runs(repo))
        if legacy_cp.exists():
            planner.move_tree(legacy_cp, _quality_control_prompts(repo))

    runs_dir = _quality_runs(repo)
    run_payloads: List[Tuple[str, Dict[str, object]]] = []
    if runs_dir.is_dir():
        for run_folder in sorted(p for p in runs_dir.iterdir() if p.is_dir()):
            index_path = run_folder / "INDEX.md"
            if index_path.exists():
                planner._log(f"keep existing {index_path.relative_to(repo)}")
                continue
            # For dry-run, build the payload only when the real filesystem state
            # lets us — folders that haven't been moved yet won't be under
            # quality/runs/ in dry-run mode.
            try:
                payload = build_index_payload(repo, run_folder)
            except Exception as exc:  # noqa: BLE001 — best-effort backfill
                planner._log(f"skip INDEX.md for {run_folder.name}: {exc}")
                continue
            planner.write_text(index_path, render_index_markdown(run_folder.name, payload))
            run_payloads.append((run_folder.name, payload))
    elif legacy_prev.exists() and dry_run:
        # Dry-run: enumerate the legacy entries that would produce run folders.
        for run_folder in sorted(p for p in legacy_prev.iterdir() if p.is_dir()):
            planner._log(f"dry-run would backfill INDEX.md for quality/runs/{run_folder.name}/")

    if run_payloads:
        rows = [render_run_index_row(run_id, payload) for run_id, payload in run_payloads]
        existing = _read_text(repo / "quality" / "RUN_INDEX.md")
        if existing and "| Run |" in existing:
            content = existing.rstrip() + "\n" + "\n".join(rows) + "\n"
        else:
            content = render_run_index_header() + "\n".join(rows) + "\n"
        planner.write_text(repo / "quality" / "RUN_INDEX.md", content)
    elif runs_dir.is_dir() and not (repo / "quality" / "RUN_INDEX.md").exists():
        # Runs directory exists but no new INDEX.md was backfilled this
        # invocation (re-run on an already-migrated repo) — still ensure the
        # top-level index exists by rebuilding from existing INDEX.md files.
        rebuilt_rows: List[str] = []
        for run_folder in sorted(p for p in runs_dir.iterdir() if p.is_dir()):
            index_path = run_folder / "INDEX.md"
            payload = _load_existing_index_payload(index_path)
            if payload is not None:
                rebuilt_rows.append(render_run_index_row(run_folder.name, payload))
        if rebuilt_rows:
            planner.write_text(
                repo / "quality" / "RUN_INDEX.md",
                render_run_index_header() + "\n".join(rebuilt_rows) + "\n",
            )

    return planner


def _load_existing_index_payload(path: Path) -> Optional[Dict[str, object]]:
    text = _read_text(path)
    if not text:
        return None
    match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Idempotently migrate a pre-v1.5.0 QPB target repo to the consolidated "
            "quality/ layout. Moves control_prompts/ and previous_runs/ under "
            "quality/ and backfills per-run INDEX.md + top-level RUN_INDEX.md."
        ),
    )
    parser.add_argument(
        "repo",
        nargs="?",
        default=".",
        help="Target repository to migrate (default: current working directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned moves and writes without touching the filesystem.",
    )
    args = parser.parse_args(argv)

    try:
        migrate(Path(args.repo), dry_run=args.dry_run)
    except MigrationError as exc:
        print(f"migrate: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
