"""role_map.py — QPB v1.5.4 Phase 1 file-role-tagging schema and helpers.

QPB v1.5.4 Part 1 replaces the v1.5.3 mechanical Code/Skill/Hybrid project
classifier with AI-driven file-by-file role tagging produced during Phase 1
exploration. The Phase 1 LLM agent reads SKILL.md (if present) and each
file in the target tree, then emits ``quality/exploration_role_map.json``
with one record per file plus an aggregate ``breakdown``. This module is
the canonical schema definition + reader/validator that all consumers
(INDEX rendering in archive_lib, the four-pass derivation pipeline in
skill_derivation/pass_c, and the skill-side checks in quality_gate.py)
share.

See ``docs/design/QPB_v1.5.4_Design.md`` Part 1 for the rationale that
motivated the redesign and ``docs/design/QPB_v1.5.4_Implementation_Plan.md``
Phase 1 for the work-item breakdown.

Role taxonomy (the fixed surface; new roles must be added here AND in
the Phase 1 prompt's role-taxonomy section in run_playbook.phase1_prompt):

  - ``skill-prose``     SKILL.md / agents/* / declarative skill content.
  - ``skill-reference`` Additional reference docs the skill names
                        (e.g. ``references/exploration_patterns.md``).
  - ``skill-tool``      A script the skill prose explicitly references
                        AND tells the agent to invoke. Distinguished
                        from ``code`` by being subordinate to skill
                        prose; the SKILL.md is the contract, the script
                        is the implementation.
  - ``code``            Independent orchestrator/library code that
                        carries its own behavior contract (e.g. QPB's
                        ``bin/run_playbook.py``).
  - ``test``            Test files and harnesses.
  - ``docs``            README, CHANGELOG, design docs, anything in
                        ``docs/``.
  - ``config``          ``.gitignore``, ``pyproject.toml``, settings.
  - ``fixture``         Test fixtures or example data used by tests.
  - ``formal-spec``     RFCs, external specifications, citable sources.
  - ``playbook-output`` Files inside a target's ``quality/`` subtree
                        from a prior playbook run. Tagging these
                        explicitly prevents the v1.5.3 LOC-pollution
                        bug: prior-run artifacts are no longer counted
                        as the target's own surface.

Schema (``quality/exploration_role_map.json``)::

  {
    "schema_version": "1.0",
    "timestamp_start": "<ISO 8601 UTC>",
    "files": [
      {
        "path": "SKILL.md",
        "role": "skill-prose",
        "size_bytes": 12345,
        "rationale": "..."
        // optional: "skill_prose_reference": "SKILL.md:47" for skill-tool
      },
      ...
    ],
    "breakdown": {
      "files_by_role": {"skill-prose": 5, ...},
      "size_by_role":  {"skill-prose": 12345, ...},
      "percentages":   {"skill_share": 0.18, "code_share": 0.65,
                        "tool_share": 0.04, "other_share": 0.13}
    }
  }

Public API:
    SCHEMA_VERSION                       canonical schema version string
    VALID_ROLES                          frozenset of legal role values
    DEFAULT_FILENAME                     "exploration_role_map.json"
    default_path(repo_dir)               -> Path to quality/<DEFAULT_FILENAME>
    load_role_map(path)                  -> dict | None (None if absent)
    validate_role_map(data)              -> list[str] of validation errors
    compute_breakdown(files)             -> breakdown dict from file entries
    has_skill_prose(role_map)            -> bool   (activation: four-pass pipeline)
    has_code(role_map)                   -> bool   (activation: code-side review)
    has_skill_tools(role_map)            -> bool   (activation: prose-to-code divergence)
    derive_legacy_project_type(role_map) -> "Code" | "Skill" | "Hybrid"

The legacy-project-type derivation exists ONLY to feed the v1.5.3 6-row
disposition table inside pass_c (Branch 5 vs Branch 6 hinges on whether
a behavioral claim can be demoted to a code-derived Tier 5, which in turn
hinges on whether the project has any code surface). It is not a return
of the Code/Skill/Hybrid trichotomy as an input field; it is an internal
mapping used by exactly one consumer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional


SCHEMA_VERSION = "1.0"
DEFAULT_FILENAME = "exploration_role_map.json"

# Roles that count toward the skill's declarative surface (numerator of
# skill_share in the breakdown percentages).
SKILL_PROSE_ROLES = frozenset({"skill-prose", "skill-reference"})
SKILL_TOOL_ROLES = frozenset({"skill-tool"})
CODE_ROLES = frozenset({"code"})

# ROLE_DESCRIPTIONS is the single source of truth for the role taxonomy.
# Both VALID_ROLES (the gate-side enum check) and the Phase 1 prompt's
# role-taxonomy section (constructed in run_playbook.phase1_prompt) read
# from this dict. Adding a new role here automatically updates both.
# v1.5.4 Round 1 Council finding C3-1.
ROLE_DESCRIPTIONS: dict = {
    "skill-prose": (
        "SKILL.md / agents/* / declarative skill content."
    ),
    "skill-reference": (
        "Additional reference docs the skill names "
        "(e.g., references/exploration_patterns.md)."
    ),
    "skill-tool": (
        "A script the skill prose explicitly references AND tells the "
        "agent to invoke. The distinguishing test: does SKILL.md (or a "
        "referenced doc) contain prose that names this script and tells "
        "the agent to call it for a specific subtask? If yes, "
        "skill-tool. If the script is independent code with its own "
        "behavior contract that the SKILL.md doesn't reference, it's "
        "code. (Worked example: QPB's bin/run_playbook.py is code, NOT "
        "skill-tool — SKILL.md does not direct agents to invoke it; it "
        "has its own contract.)"
    ),
    "code": (
        "Independent orchestrator/library code (carries its own behavior "
        "contract; not subordinate to SKILL.md prose)."
    ),
    "test": "Test files and test harnesses.",
    "docs": "README, CHANGELOG, design docs, anything in docs/.",
    "config": ".gitignore, pyproject.toml, settings.",
    "fixture": "Test fixtures or example data used by tests.",
    "formal-spec": "RFCs, external specifications, citable sources.",
    "playbook-output": (
        "Files inside the target's quality/ subtree, or QPB-managed "
        "installations like .github/skills/quality_gate.py, that came "
        "from a prior playbook run rather than the target's intrinsic "
        "surface."
    ),
}

VALID_ROLES = frozenset(ROLE_DESCRIPTIONS.keys())

# Required top-level keys in a role map document.
_REQUIRED_TOP_KEYS = ("schema_version", "files", "breakdown")
_REQUIRED_BREAKDOWN_KEYS = ("files_by_role", "size_by_role", "percentages")
_REQUIRED_PERCENTAGE_KEYS = (
    "skill_share",
    "code_share",
    "tool_share",
    "other_share",
)
_REQUIRED_FILE_ENTRY_KEYS = ("path", "role", "size_bytes", "rationale")


def default_path(repo_dir: Path) -> Path:
    """Return the canonical role-map path for a target repo."""
    return Path(repo_dir) / "quality" / DEFAULT_FILENAME


def load_role_map(path: Path) -> Optional[dict]:
    """Load and JSON-parse a role-map file. Returns ``None`` if the file
    is absent or cannot be parsed as a JSON object. Does NOT validate
    the schema; call :func:`validate_role_map` for that.
    """
    p = Path(path)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def validate_role_map(data: dict) -> list[str]:
    """Return a list of validation errors for ``data``. Empty list ==
    well-formed. Validation covers required keys, role enum, file entry
    shape, and breakdown internal consistency (percentages sum to ~1.0
    when total size > 0).
    """
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["role map is not a JSON object"]

    for key in _REQUIRED_TOP_KEYS:
        if key not in data:
            errors.append(f"missing required key: {key!r}")
    if errors:
        return errors

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"schema_version {data.get('schema_version')!r} does not match "
            f"expected {SCHEMA_VERSION!r}"
        )

    files = data.get("files")
    if not isinstance(files, list):
        errors.append("'files' must be a list")
        return errors

    seen_paths: set[str] = set()
    for idx, entry in enumerate(files):
        if not isinstance(entry, dict):
            errors.append(f"files[{idx}] is not an object")
            continue
        for k in _REQUIRED_FILE_ENTRY_KEYS:
            if k not in entry:
                errors.append(f"files[{idx}] missing required key {k!r}")
        path = entry.get("path")
        if isinstance(path, str):
            if path in seen_paths:
                errors.append(f"files[{idx}] duplicate path {path!r}")
            seen_paths.add(path)
        role = entry.get("role")
        if role not in VALID_ROLES:
            errors.append(
                f"files[{idx}] role {role!r} is not in VALID_ROLES "
                f"({sorted(VALID_ROLES)})"
            )
        size = entry.get("size_bytes")
        if not isinstance(size, int) or size < 0:
            errors.append(
                f"files[{idx}] size_bytes must be a non-negative int "
                f"(got {size!r})"
            )
        # v1.5.4 Round 1 Council finding A2/B2/C1: skill_prose_reference
        # is REQUIRED on every skill-tool entry, not merely validated when
        # present. Without it, the Phase 4 prose-to-code divergence check
        # has no anchor to look up — the cited prose location is the
        # entire point of distinguishing skill-tool from code.
        if role == "skill-tool":
            ref = entry.get("skill_prose_reference")
            if ref is None or not isinstance(ref, str) or not ref.strip():
                errors.append(
                    f"file {entry.get('path')!r} has role='skill-tool' but "
                    "missing or empty 'skill_prose_reference'; required for "
                    "Phase 4 prose-to-code divergence checks"
                )

    breakdown = data.get("breakdown")
    if not isinstance(breakdown, dict):
        errors.append("'breakdown' must be an object")
        return errors
    for k in _REQUIRED_BREAKDOWN_KEYS:
        if k not in breakdown:
            errors.append(f"breakdown missing required key {k!r}")

    percentages = breakdown.get("percentages")
    if isinstance(percentages, dict):
        for k in _REQUIRED_PERCENTAGE_KEYS:
            if k not in percentages:
                errors.append(f"breakdown.percentages missing key {k!r}")
            else:
                v = percentages[k]
                if not isinstance(v, (int, float)) or v < 0 or v > 1.0001:
                    errors.append(
                        f"breakdown.percentages[{k!r}] must be in [0, 1] "
                        f"(got {v!r})"
                    )
        total_size = sum(
            int(e.get("size_bytes", 0))
            for e in files
            if isinstance(e, dict) and isinstance(e.get("size_bytes"), int)
        )
        if total_size > 0:
            psum = sum(
                float(percentages.get(k, 0))
                for k in _REQUIRED_PERCENTAGE_KEYS
                if isinstance(percentages.get(k), (int, float))
            )
            if abs(psum - 1.0) > 0.01:
                errors.append(
                    f"breakdown.percentages do not sum to 1.0 (sum={psum:.4f})"
                )

    return errors


def compute_breakdown(files: Iterable[dict]) -> dict:
    """Aggregate ``files`` into the canonical ``breakdown`` dict.

    Percentages are computed against total size_bytes; when total size is
    zero (e.g. an empty target) all four shares default to 0.0. Roles
    contribute to ``skill_share`` (skill-prose + skill-reference),
    ``code_share`` (code), ``tool_share`` (skill-tool), and
    ``other_share`` (everything else). ``playbook-output`` is bucketed
    into ``other_share`` so prior-run artifacts can't inflate the
    target's apparent skill or code surface.
    """
    files_by_role: dict[str, int] = {}
    size_by_role: dict[str, int] = {}
    total_size = 0
    for entry in files:
        if not isinstance(entry, dict):
            continue
        role = entry.get("role")
        if role not in VALID_ROLES:
            continue
        size = entry.get("size_bytes", 0)
        if not isinstance(size, int) or size < 0:
            size = 0
        files_by_role[role] = files_by_role.get(role, 0) + 1
        size_by_role[role] = size_by_role.get(role, 0) + size
        total_size += size

    def _share(role_set: frozenset[str]) -> float:
        if total_size == 0:
            return 0.0
        return sum(size_by_role.get(r, 0) for r in role_set) / total_size

    skill = _share(SKILL_PROSE_ROLES)
    tool = _share(SKILL_TOOL_ROLES)
    code = _share(CODE_ROLES)
    other = max(0.0, 1.0 - skill - tool - code) if total_size > 0 else 0.0

    return {
        "files_by_role": files_by_role,
        "size_by_role": size_by_role,
        "percentages": {
            "skill_share": skill,
            "code_share": code,
            "tool_share": tool,
            "other_share": other,
        },
    }


def has_skill_prose(role_map: Optional[dict]) -> bool:
    """True iff the role map contains at least one file tagged
    ``skill-prose`` or ``skill-reference``. This is the activation
    condition for the v1.5.3 four-pass derivation pipeline (replacing
    the prior ``project_type in ('Skill', 'Hybrid')`` gate).
    """
    return _any_role(role_map, SKILL_PROSE_ROLES)


def has_code(role_map: Optional[dict]) -> bool:
    """True iff the role map contains at least one file tagged ``code``.
    Activation for the existing code-review pipeline."""
    return _any_role(role_map, CODE_ROLES)


def has_skill_tools(role_map: Optional[dict]) -> bool:
    """True iff the role map contains at least one ``skill-tool`` file.
    Activation for prose-to-code divergence checks."""
    return _any_role(role_map, SKILL_TOOL_ROLES)


def _any_role(role_map: Optional[dict], roles: frozenset[str]) -> bool:
    if not isinstance(role_map, dict):
        return False
    files = role_map.get("files") or []
    if not isinstance(files, list):
        return False
    for entry in files:
        if isinstance(entry, dict) and entry.get("role") in roles:
            return True
    return False


def derive_legacy_project_type(role_map: Optional[dict]) -> str:
    """Return the v1.5.3-equivalent project type string. Used ONLY by
    pass_c's 6-row disposition table (Branch 5 demotes behavioral claims
    to Tier 5 ``code-derived`` when the project has code authority;
    Branch 6 routes to council-review when it does not).

    Mapping:
      - has skill-prose AND has code  -> "Hybrid"
      - has skill-prose, no code      -> "Skill"
      - no skill-prose                -> "Code"
    """
    skill = has_skill_prose(role_map)
    code = has_code(role_map)
    if skill and code:
        return "Hybrid"
    if skill:
        return "Skill"
    return "Code"


def role_breakdown_for_index(role_map: Optional[dict]) -> Optional[dict]:
    """Return the value to write into the INDEX.md ``target_role_breakdown``
    field. ``None`` when the role map is absent (Phase 1 not yet run);
    otherwise a compact summary containing the breakdown subtree.

    The shape exposed in INDEX is intentionally small (the per-file
    rationale set lives only in exploration_role_map.json itself).
    """
    if not isinstance(role_map, dict):
        return None
    breakdown = role_map.get("breakdown")
    if not isinstance(breakdown, dict):
        return None
    return {
        "files_by_role": breakdown.get("files_by_role", {}),
        "size_by_role": breakdown.get("size_by_role", {}),
        "percentages": breakdown.get("percentages", {}),
    }
