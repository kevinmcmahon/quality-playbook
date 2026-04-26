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

from pathlib import Path
from typing import Iterable, Optional

CLASSIFIER_VERSION = "1.0"
SCHEMA_VERSION = "1.0"


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
    raise NotImplementedError


def write_classification(target_dir: Path, record: dict) -> Path:
    """Write a classification record to <target>/quality/project_type.json.

    Creates the quality/ directory if it doesn't exist. Atomic write
    (tmp + rename) so a crash mid-write doesn't leave a half-written JSON
    file on disk. Returns the path written.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Internals (private; signatures fixed in skeleton, bodies in next commit)
# ---------------------------------------------------------------------------


def _count_words(path: Path) -> int:
    raise NotImplementedError


def _count_code_loc(target_dir: Path) -> "tuple[int, set[str]]":
    raise NotImplementedError


def _iter_code_files(target_dir: Path) -> Iterable[Path]:
    raise NotImplementedError


def _git_tracked_files(target_dir: Path) -> "Optional[list[str]]":
    raise NotImplementedError


def _apply_heuristic(
    *,
    skill_md_present: bool,
    skill_md_word_count: Optional[int],
    total_code_loc: int,
) -> "tuple[str, str, str]":
    """Apply the classification heuristic.

    Returns (classification, rationale, confidence).
    """
    raise NotImplementedError


def _utc_now_iso() -> str:
    raise NotImplementedError
