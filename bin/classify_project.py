"""classify_project.py — QPB v1.5.3 Phase 1 project-type classifier.

QPB v1.5.3 introduces a Phase 0 step that classifies a target repository
as Code, Skill, or Hybrid before the playbook's exploration phase begins.
Code projects keep the v1.5.0 divergence pipeline; Skill and Hybrid projects
get the skill-specific four-pass derivation pipeline added in later v1.5.3
phases (Phases 2-7). See `docs/design/QPB_v1.5.3_Design.md` for the full
design and `docs/design/QPB_v1.5.3_Implementation_Plan.md` for the phase
sequencing.

This module is the Phase 1 deliverable: the classifier itself plus a JSON
writer that emits `<target>/quality/project_type.json`. Schema extensions
that wire this output into the broader requirements pipeline come in
Phase 2; divergence detection that consumes the classification comes in
Phases 4-5.

Heuristic (per QPB_v1.5.3_Design.md "Classification Mechanism"):

  - SKILL.md exists at repo root AND prose word count in SKILL.md
    substantially exceeds code line count across the repo => Skill
  - SKILL.md exists at repo root AND substantial code exists alongside it
    => Hybrid
  - No SKILL.md at repo root => Code

The "substantially exceeds" threshold lands at the 2x ratio called out in
QPB_v1.5.3_Implementation_Plan.md Open Question 1; this is calibrated so
that QPB itself classifies as Hybrid (its SKILL.md prose is comparable to
its code LOC, not dominant over it).

Override hook: callers may pass an explicit `override` (with rationale) to
bypass the heuristic. v1.5.3 Phase 4's Council uses this hook to re-verify
classifications and override them with rationale; the heuristic's evidence
is preserved in the output even when an override applies.

Public API:
    classify_project(target_dir, *, override=None, override_rationale=None)
        -> classification record dict
    write_classification(target_dir, record) -> path written

Module is stdlib-only and side-effect-free except for write_classification
and the optional `git ls-files` subprocess invocation used to respect
.gitignore when counting code LOC.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

CLASSIFIER_VERSION = "1.0"
SCHEMA_VERSION = "1.0"

VALID_CLASSIFICATIONS = ("Code", "Skill", "Hybrid")
VALID_CONFIDENCES = ("high", "medium", "low")

# Words-to-LOC ratio thresholds. Calibrated so QPB itself (SKILL.md prose
# comparable to but not dominant over bin/ code) classifies as Hybrid; per
# QPB_v1.5.3_Implementation_Plan.md Open Question 1.
#
# Why these specific values: prose words and code lines are not directly
# comparable units, so the boundaries are picked empirically against real
# targets, not derived from first principles. QPB itself sits at ~1.7
# words-per-LOC, so the SKILL_DOMINANCE_RATIO (Skill vs Hybrid boundary)
# at 2.0 leaves QPB comfortably on the Hybrid side -- a 1× boundary would
# misclassify QPB as Skill, a 5× boundary would miss obvious skill-shaped
# targets that still carry some helper code.
SKILL_DOMINANCE_RATIO = 2.0
# Anything 5× or more is unambiguously skill-dominant regardless of
# absolute code size: even a real engineering codebase tucked under
# extensive skill prose still falls below 5× when its code carries weight,
# so a project crossing this threshold is reliably Skill, not Hybrid. The
# 5× choice (vs 3× or 10×) keeps the medium-confidence Skill band wide
# enough to catch borderline projects and gives QPB at 1.67× a comfortable
# margin from any transition.
SKILL_HIGH_CONFIDENCE_RATIO = 5.0
# Symmetric to SKILL_DOMINANCE_RATIO but on the code-dominant side: a
# project where code outsizes SKILL.md prose by 2× or more is reliably
# Hybrid with high confidence. Picked at 2.0 (not e.g. 3.0) so that the
# medium-confidence Hybrid band stays narrow -- a code-dominant project
# should surface as high-confidence Hybrid quickly, leaving the medium
# band for genuinely balanced cases like QPB.
HYBRID_HIGH_CONFIDENCE_RATIO = 2.0

# Threshold below which a no-SKILL project is "Code with low confidence"
# rather than "Code with high confidence" -- a near-empty directory is not
# a confident Code classification.
SMALL_PROJECT_LOC_THRESHOLD = 50

EXTENSION_LANGUAGE = {
    ".py": "Python",
    ".go": "Go",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".java": "Java",
    ".kt": "Kotlin", ".kts": "Kotlin",
    ".scala": "Scala",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".hpp": "C++", ".cc": "C++", ".cxx": "C++", ".hxx": "C++",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".m": "Objective-C", ".mm": "Objective-C",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".cs": "C#",
    ".fs": "F#",
    ".vb": "Visual Basic",
}
CODE_EXTENSIONS = frozenset(EXTENSION_LANGUAGE.keys())

# Conventional ignore directories for filesystem walk (used when target_dir
# is not a git repo). git ls-files takes precedence when available because
# it already respects .gitignore.
DEFAULT_IGNORE_DIRS = frozenset({
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "target", "build", "dist", ".idea", ".vscode", ".pytest_cache",
    ".mypy_cache", ".tox", ".eggs", "vendor",
})


def classify_project(
    target_dir: Path,
    *,
    override: Optional[str] = None,
    override_rationale: Optional[str] = None,
) -> dict:
    """Classify a target directory as Code, Skill, or Hybrid.

    target_dir: repository root to classify.
    override: optional explicit classification ("Code" / "Skill" / "Hybrid")
        that supersedes the heuristic. The heuristic is still computed so
        its evidence is recorded in the output.
    override_rationale: free-text reason for the override. Required when
        override is non-None.

    Returns a dict matching the JSON schema documented in this module's
    header. Does not write to disk; callers pass the dict to
    write_classification() to persist.
    """
    if override is not None:
        if override not in VALID_CLASSIFICATIONS:
            raise ValueError(
                f"override must be one of {VALID_CLASSIFICATIONS}; got {override!r}"
            )
        if not override_rationale:
            raise ValueError("override_rationale is required when override is set")

    target_dir = Path(target_dir).resolve()
    skill_md_path = target_dir / "SKILL.md"
    skill_md_present = skill_md_path.is_file()
    skill_md_word_count = _count_words(skill_md_path) if skill_md_present else None

    total_code_loc, code_languages = _count_code_loc(target_dir)

    heuristic_class, heuristic_rationale, heuristic_confidence = _apply_heuristic(
        skill_md_present=skill_md_present,
        skill_md_word_count=skill_md_word_count,
        total_code_loc=total_code_loc,
    )

    if override is not None:
        final_classification = override
        final_rationale = (
            f"Override applied: {override_rationale} "
            f"(heuristic suggested {heuristic_class}: {heuristic_rationale})"
        )
        # Explicit override is treated as authoritative; confidence reflects
        # the human/Council judgment, not the underlying signal.
        final_confidence = "high"
    else:
        final_classification = heuristic_class
        final_rationale = heuristic_rationale
        final_confidence = heuristic_confidence

    return {
        "schema_version": SCHEMA_VERSION,
        "classification": final_classification,
        "rationale": final_rationale,
        "confidence": final_confidence,
        "evidence": {
            "skill_md_present": skill_md_present,
            "skill_md_path": str(skill_md_path) if skill_md_present else None,
            "skill_md_word_count": skill_md_word_count,
            "total_code_loc": total_code_loc,
            "code_languages": sorted(code_languages),
        },
        "classified_at": _utc_now_iso(),
        "classifier_version": CLASSIFIER_VERSION,
        "override_applied": override is not None,
        "override_rationale": override_rationale if override is not None else None,
    }


def write_classification(target_dir: Path, record: dict) -> Path:
    """Write a classification record to <target>/quality/project_type.json.

    Creates the quality/ directory if it doesn't exist. Atomic write
    (tmp + rename) so a crash mid-write doesn't leave a half-written JSON
    file on disk. Returns the path written.
    """
    target_dir = Path(target_dir).resolve()
    quality_dir = target_dir / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    out_path = quality_dir / "project_type.json"

    payload = json.dumps(record, indent=2, sort_keys=False) + "\n"
    tmp_path = out_path.with_name(out_path.name + ".tmp")
    tmp_path.write_text(payload, encoding="utf-8")
    os.replace(tmp_path, out_path)
    return out_path


# ---------------------------------------------------------------------------
# Internals (private; signatures fixed in skeleton, bodies in next commit)
# ---------------------------------------------------------------------------


def _count_words(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return len(text.split())


def _count_code_loc(target_dir: Path) -> "tuple[int, set[str]]":
    """Count non-blank lines in code files; identify languages present.

    Defers file enumeration to _iter_code_files (which prefers `git ls-files`
    over a filesystem walk so .gitignore is respected). Counts only
    non-blank lines so generated whitespace doesn't dominate the comparison
    against SKILL.md word count.
    """
    languages: set[str] = set()
    total_loc = 0
    for f in _iter_code_files(target_dir):
        ext = f.suffix.lower()
        lang = EXTENSION_LANGUAGE.get(ext)
        if lang is not None:
            languages.add(lang)
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if line.strip():
                total_loc += 1
    return total_loc, languages


def _iter_code_files(target_dir: Path) -> Iterable[Path]:
    """Yield code file paths under target_dir.

    Uses `git ls-files` when target_dir is a git repo so .gitignore is
    respected (this matters for projects like QPB where vendored benchmark
    targets live under repos/ but are gitignored). Falls back to an
    os.walk that prunes DEFAULT_IGNORE_DIRS.
    """
    git_files = _git_tracked_files(target_dir)
    if git_files is not None:
        for rel in git_files:
            p = target_dir / rel
            if p.suffix.lower() in CODE_EXTENSIONS and p.is_file():
                yield p
        return

    for root, dirs, names in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORE_DIRS]
        for name in names:
            p = Path(root) / name
            if p.suffix.lower() in CODE_EXTENSIONS:
                yield p


def _git_tracked_files(target_dir: Path) -> "Optional[list[str]]":
    """Return tracked relative paths via `git ls-files`, or None if not a repo."""
    git_dir = target_dir / ".git"
    if not git_dir.exists():
        return None
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=str(target_dir),
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.splitlines() if line]


def _apply_heuristic(
    *,
    skill_md_present: bool,
    skill_md_word_count: Optional[int],
    total_code_loc: int,
) -> "tuple[str, str, str]":
    """Apply the classification heuristic.

    Returns (classification, rationale, confidence). See module header for
    the heuristic statement; ratio thresholds are module-level constants.
    """
    if not skill_md_present:
        if total_code_loc == 0:
            return (
                "Code",
                "No SKILL.md at repo root; no code lines observed (empty or "
                "near-empty target).",
                "low",
            )
        if total_code_loc < SMALL_PROJECT_LOC_THRESHOLD:
            return (
                "Code",
                f"No SKILL.md at repo root; only {total_code_loc} non-blank "
                f"code lines observed (small project below the "
                f"{SMALL_PROJECT_LOC_THRESHOLD}-line confidence threshold).",
                "medium",
            )
        return (
            "Code",
            f"No SKILL.md at repo root; {total_code_loc} non-blank code lines "
            f"observed across the repo.",
            "high",
        )

    word_count = skill_md_word_count or 0

    # Empty SKILL.md: it exists but contributes no prose. Treat as Hybrid
    # with low confidence -- the file's presence signals skill-shaped
    # intent, but there's no prose to be the program.
    if word_count == 0:
        return (
            "Hybrid",
            f"SKILL.md exists at repo root but is empty (0 words); "
            f"{total_code_loc} non-blank code lines observed.",
            "low",
        )

    # SKILL.md with prose but no code at all: unambiguously Skill.
    if total_code_loc == 0:
        return (
            "Skill",
            f"SKILL.md exists at repo root with {word_count} prose words and "
            f"no code lines observed.",
            "high",
        )

    ratio_words_to_code = word_count / total_code_loc

    if ratio_words_to_code > SKILL_HIGH_CONFIDENCE_RATIO:
        return (
            "Skill",
            f"SKILL.md prose word count ({word_count}) substantially exceeds "
            f"code line count ({total_code_loc}); "
            f"ratio {ratio_words_to_code:.1f}x.",
            "high",
        )
    if ratio_words_to_code > SKILL_DOMINANCE_RATIO:
        return (
            "Skill",
            f"SKILL.md prose word count ({word_count}) exceeds code line "
            f"count ({total_code_loc}) by more than {SKILL_DOMINANCE_RATIO:g}x "
            f"(actual {ratio_words_to_code:.1f}x).",
            "medium",
        )

    ratio_code_to_words = total_code_loc / word_count
    if ratio_code_to_words > HYBRID_HIGH_CONFIDENCE_RATIO:
        return (
            "Hybrid",
            f"SKILL.md exists at repo root ({word_count} prose words) but "
            f"code dominates ({total_code_loc} non-blank lines; "
            f"ratio {ratio_code_to_words:.1f}x).",
            "high",
        )
    return (
        "Hybrid",
        f"SKILL.md exists at repo root ({word_count} prose words) alongside "
        f"substantial code ({total_code_loc} non-blank lines); "
        f"ratio {ratio_words_to_code:.2f} words/LOC sits within the Hybrid "
        f"band [1/{HYBRID_HIGH_CONFIDENCE_RATIO:g}x, "
        f"{SKILL_DOMINANCE_RATIO:g}x].",
        "medium",
    )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# CLI / benchmark verification entry point
# ---------------------------------------------------------------------------
#
# Usage:
#   python3 -m bin.classify_project --target <path> [--write]
#   python3 -m bin.classify_project --benchmark
#
# --benchmark classifies the v1.5.3 Phase 1 acceptance set: the five code
# benchmark repos plus QPB itself, and writes results to each target's
# quality/project_type.json (skipping QPB's own write so the classifier
# does not introduce a tracked file under quality/ on the QPB repo).


# The acceptance set is fixed; the brief calls these out by name. Paths
# are resolved relative to the QPB repo root (this file's grandparent).
_QPB_ROOT = Path(__file__).resolve().parents[1]

_BENCHMARK_TARGETS: list[tuple[str, Path, str, bool]] = [
    # (label, path-relative-to-QPB-root, expected_classification, write_to_disk)
    ("chi-1.5.1", Path("repos/chi-1.5.1"), "Code", True),
    ("virtio-1.5.1", Path("repos/virtio-1.5.1"), "Code", True),
    ("express-1.5.1", Path("repos/express-1.5.1"), "Code", True),
    ("cobra-latest", Path("repos/cobra-1.3.46"), "Code", True),
    ("casbin-latest", Path("repos/archive/casbin-1.5.1"), "Code", True),
    # QPB itself: classify but do NOT write -- QPB's quality/ subtree is
    # tracked, and the v1.5.3 Phase 1 brief explicitly forbids modifying
    # files outside the Phase 1 surface. The verification log captures the
    # JSON content for the audit trail.
    ("QPB-self", Path("."), "Hybrid", False),
]


def _run_benchmark_verification(
    qpb_root: Path,
    log_path: Optional[Path],
) -> int:
    """Run the classifier against the v1.5.3 Phase 1 acceptance set.

    Returns 0 if every target produced its expected classification, 1 if any
    classification mismatched. Writes a verification log if log_path is set.
    """
    lines: list[str] = []
    lines.append("# QPB v1.5.3 Phase 1 -- Project type classifier verification")
    lines.append("")
    lines.append(f"Classifier version: {CLASSIFIER_VERSION}")
    lines.append(f"Schema version:     {SCHEMA_VERSION}")
    lines.append(f"Run timestamp:      {_utc_now_iso()}")
    lines.append("")
    lines.append("## Per-target results")
    lines.append("")

    overall_ok = True
    for label, rel_path, expected, write_to_disk in _BENCHMARK_TARGETS:
        target = (qpb_root / rel_path).resolve()
        lines.append(f"### {label}")
        lines.append("")
        lines.append(f"- target: `{target}`")
        if not target.exists():
            lines.append("- result: SKIPPED (target path does not exist)")
            lines.append("")
            overall_ok = False
            continue

        record = classify_project(target)
        actual = record["classification"]
        match = "OK" if actual == expected else "FAIL"
        if actual != expected:
            overall_ok = False

        lines.append(f"- expected: `{expected}`")
        lines.append(f"- actual:   `{actual}`  ({record['confidence']})")
        lines.append(f"- result:   {match}")
        lines.append(f"- evidence: {json.dumps(record['evidence'], sort_keys=True)}")

        if write_to_disk:
            out_path = write_classification(target, record)
            lines.append(f"- wrote:    `{out_path}`")
        else:
            lines.append("- wrote:    (skipped; capturing JSON in log)")

        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(record, indent=2))
        lines.append("```")
        lines.append("")

    summary = "PASS" if overall_ok else "FAIL"
    lines.append(f"## Overall: {summary}")
    lines.append("")

    rendered = "\n".join(lines)
    print(rendered)

    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(rendered, encoding="utf-8")

    return 0 if overall_ok else 1


def _parse_args(argv: Optional[list[str]] = None) -> "argparse.Namespace":
    import argparse

    parser = argparse.ArgumentParser(
        prog="classify_project",
        description=(
            "v1.5.3 Phase 1 project-type classifier. "
            "Classifies a target as Code, Skill, or Hybrid."
        ),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--target",
        type=Path,
        help="classify a single target directory",
    )
    mode.add_argument(
        "--benchmark",
        action="store_true",
        help=(
            "run the v1.5.3 Phase 1 acceptance set (5 code benchmarks + QPB) "
            "and emit a verification log"
        ),
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "with --target: also write <target>/quality/project_type.json "
            "(default: print only)"
        ),
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=None,
        help="with --benchmark: path to write the verification log",
    )
    return parser.parse_args(argv)


def _main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    if args.benchmark:
        return _run_benchmark_verification(_QPB_ROOT, args.log)

    record = classify_project(args.target)
    print(json.dumps(record, indent=2))
    if args.write:
        out_path = write_classification(args.target, record)
        print(f"\nwrote: {out_path}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(_main())
