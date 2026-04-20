"""council_semantic_check.py — Phase 6 Layer-2 hallucination mitigation.

Assembles the Council-of-Three semantic review output into
`quality/citation_semantic_check.json` per schemas.md §9.

Layer 1 (Phase 5d) re-runs the deterministic excerpt extraction at gate
time to catch fabricated excerpts — a purely mechanical check.

Layer 2 (Phase 6) asks three independent AI reviewers whether each Tier
1/2 REQ's `citation_excerpt` actually supports the requirement as
stated, or whether the requirement overreaches what the excerpt says.
Three values per REQ:

    supports     — excerpt clearly supports the requirement.
    overreaches  — citation exists but requirement claims more than
                   the excerpt says.
    unclear      — reviewer cannot tell.

Gate rule (schemas.md §10 invariant #17): ≥2 of 3 `overreaches` for the
same REQ fails the gate; isolated `overreaches` / `unclear` surface as
warnings. See `.github/skills/quality_gate/quality_gate.py` for the
mechanical check implementation.

This module is deliberately structured as pure functions with the
module-level boundary at "assemble the reviews array" — actually
invoking the LLMs lives in the orchestrator (Phase 4 Council machinery).
That separation keeps the module testable without an LLM round-trip.

Public surface:

    collect_tier_12_reqs(quality_dir) -> list[ReqRecord]
        Extract the Tier 1/2 REQs that need semantic review.

    build_prompts_for_member(member_id, reqs, *, batch_size=5, threshold=15)
        Return the list of prompt strings the member should see. One
        prompt for ≤15 REQs; batches of up to `batch_size` for >15.

    parse_member_response(member_id, response_text, expected_req_ids)
        Validate and coerce a JSON response into review entries.

    assemble_reviews(responses_by_member) -> list[ReviewEntry]
        Flatten per-member review lists into one reviews[] array.

    write_semantic_check(repo_dir, reviews, *, schema_version=..., now=None)
        Emit quality/citation_semantic_check.json per §9 wrapper shape.

CLI (for operator re-assembly from captured per-member JSON files):

    python -m bin.council_semantic_check <repo_dir> \
        --member claude-opus-4.7 --response path/to/claude.json \
        --member gpt-5.4          --response path/to/gpt.json \
        --member gemini-2.5-pro   --response path/to/gemini.json
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from . import archive_lib
    from . import benchmark_lib as lib
    from .council_config import council_members, DEFAULT_COUNCIL_MEMBERS
except ImportError:  # running as a script from the repo root
    import archive_lib
    import benchmark_lib as lib
    from council_config import council_members, DEFAULT_COUNCIL_MEMBERS


VALID_VERDICTS = ("supports", "overreaches", "unclear")


class SemanticCheckError(Exception):
    """Raised on unrecoverable assembly failures."""


@dataclass(frozen=True)
class ReqRecord:
    """Minimal subset of a REQ needed for semantic review."""

    req_id: str
    tier: int
    description: str
    citation_excerpt: str
    citation_document: str
    citation_locator: str  # rendered "section=X line=Y" string


@dataclass(frozen=True)
class ReviewEntry:
    """One row of the citation_semantic_check.json reviews[] array."""

    req_id: str
    reviewer: str
    verdict: str
    notes: str


# ---------------------------------------------------------------------------
# REQ extraction
# ---------------------------------------------------------------------------


def collect_tier_12_reqs(quality_dir: Path) -> List[ReqRecord]:
    """Load Tier 1/2 REQs from quality/requirements_manifest.json.

    REQs without a well-formed citation are skipped silently — Layer-1
    (Phase 5d) already flags them. This function's job is to assemble
    the Layer-2 review set, not to re-validate citation shape.
    """
    path = quality_dir / "requirements_manifest.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, dict):
        return []
    records = data.get("records")
    if not isinstance(records, list):
        return []
    result: List[ReqRecord] = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        tier = rec.get("tier")
        if tier not in (1, 2):
            continue
        req_id = rec.get("id")
        if not isinstance(req_id, str) or not req_id:
            continue
        citation = rec.get("citation")
        if not isinstance(citation, dict):
            continue
        excerpt = citation.get("citation_excerpt")
        if not isinstance(excerpt, str) or not excerpt:
            continue
        document = citation.get("document")
        if not isinstance(document, str):
            document = ""
        section = citation.get("section")
        line = citation.get("line")
        locator_bits: List[str] = []
        if isinstance(section, str) and section:
            locator_bits.append(f"section={section}")
        if isinstance(line, int) and not isinstance(line, bool):
            locator_bits.append(f"line={line}")
        description = rec.get("description") or rec.get("title") or ""
        if not isinstance(description, str):
            description = str(description)
        result.append(
            ReqRecord(
                req_id=req_id,
                tier=int(tier),
                description=description,
                citation_excerpt=excerpt,
                citation_document=document,
                citation_locator=" ".join(locator_bits) or "(no locator)",
            )
        )
    return result


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


_PROMPT_HEADER = (
    "You are {member} reviewing citation support for {count} Tier 1/2 "
    "requirements extracted from a target repo. For each requirement below, "
    "read the citation_excerpt and decide whether the excerpt supports the "
    "requirement as stated or whether the requirement overreaches what the "
    "excerpt says.\n"
    "\n"
    "Respond with a single JSON array. One object per requirement, in the "
    "same order as given. Each object MUST have exactly these keys:\n"
    '  "req_id": string matching the input\n'
    '  "verdict": "supports" | "overreaches" | "unclear"\n'
    '  "reasoning": brief explanation (may be empty string)\n'
    "\n"
    "Do not include any prose outside the JSON array. Do not add extra keys."
    "\n\n"
    "--- Requirements ---\n"
)


def _render_req_block(req: ReqRecord) -> str:
    return (
        f"req_id: {req.req_id}\n"
        f"tier: {req.tier}\n"
        f"description: {req.description.strip()}\n"
        f"citation_document: {req.citation_document}\n"
        f"citation_locator: {req.citation_locator}\n"
        f"citation_excerpt: |\n  "
        + req.citation_excerpt.replace("\n", "\n  ")
        + "\n"
    )


def build_prompts_for_member(
    member_id: str,
    reqs: Sequence[ReqRecord],
    *,
    batch_size: int = 5,
    threshold: int = 15,
) -> List[str]:
    """Return one or more prompt strings for a Council member.

    - If `len(reqs) <= threshold`: one prompt containing every REQ.
    - Else: batches of up to `batch_size` REQs, in `req_id`-stable order
      so multiple reviewers see the same partition across their batch
      sequences.

    Empty reqs returns an empty list (no prompts to send — Spec Gap
    run; semantic check file will have `reviews: []`).
    """
    reqs_list = list(reqs)
    if not reqs_list:
        return []
    if len(reqs_list) <= threshold:
        return [_render_single_prompt(member_id, reqs_list)]
    # Stable partitioning: sort by req_id so each reviewer sees the same
    # batch boundaries.
    ordered = sorted(reqs_list, key=lambda r: r.req_id)
    prompts: List[str] = []
    for start in range(0, len(ordered), batch_size):
        batch = ordered[start : start + batch_size]
        prompts.append(_render_single_prompt(member_id, batch))
    return prompts


def _render_single_prompt(member_id: str, reqs: Sequence[ReqRecord]) -> str:
    header = _PROMPT_HEADER.format(member=member_id, count=len(reqs))
    body = "\n".join(_render_req_block(r) for r in reqs)
    return header + body


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def parse_member_response(
    member_id: str,
    response_text: str,
    expected_req_ids: Iterable[str],
) -> List[ReviewEntry]:
    """Parse a Council member's JSON-array response into review entries.

    Validation:
      - Response is (or contains) a JSON array.
      - Each element is a dict with `req_id`, `verdict`, `reasoning`.
      - `verdict` is in the `VALID_VERDICTS` enum.
      - Every `expected_req_ids` member appears in the response.

    Missing / invalid entries raise SemanticCheckError with a specific
    message naming the offending REQ id.
    """
    payload = _extract_first_json_array(response_text)
    if payload is None:
        raise SemanticCheckError(
            f"{member_id}: response does not contain a JSON array"
        )
    if not isinstance(payload, list):
        raise SemanticCheckError(
            f"{member_id}: top-level JSON is {type(payload).__name__}, expected array"
        )
    seen: Dict[str, ReviewEntry] = {}
    expected = list(expected_req_ids)
    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            raise SemanticCheckError(
                f"{member_id}: response[#{idx}] is {type(item).__name__}, expected object"
            )
        req_id = item.get("req_id")
        if not isinstance(req_id, str) or not req_id:
            raise SemanticCheckError(
                f"{member_id}: response[#{idx}] missing or non-string req_id"
            )
        verdict = item.get("verdict")
        if verdict not in VALID_VERDICTS:
            raise SemanticCheckError(
                f"{member_id}: response[#{idx}] (req_id={req_id}) invalid "
                f"verdict {verdict!r}; expected one of {VALID_VERDICTS}"
            )
        reasoning = item.get("reasoning", "")
        if reasoning is None:
            reasoning = ""
        if not isinstance(reasoning, str):
            raise SemanticCheckError(
                f"{member_id}: response[#{idx}] (req_id={req_id}) reasoning is "
                f"{type(reasoning).__name__}, expected string"
            )
        if req_id in seen:
            raise SemanticCheckError(
                f"{member_id}: duplicate review for req_id={req_id!r}"
            )
        seen[req_id] = ReviewEntry(
            req_id=req_id, reviewer=member_id, verdict=verdict, notes=reasoning
        )
    missing = [rid for rid in expected if rid not in seen]
    if missing:
        raise SemanticCheckError(
            f"{member_id}: response missing review(s) for {missing}"
        )
    # Preserve the expected order so downstream assembly is stable.
    return [seen[rid] for rid in expected]


_JSON_ARRAY_PATTERN = re.compile(r"\[[\s\S]*\]")


def _extract_first_json_array(text: str):
    """Return the first JSON array in `text`, or None.

    Models sometimes wrap responses in markdown code fences or brief
    prose. Tolerate that by scanning for the first `[...]` balanced
    block.
    """
    # Fast path: whole payload is a JSON array.
    stripped = text.strip()
    if stripped.startswith("["):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
    # Fallback: find the outermost `[...]` that parses.
    match = _JSON_ARRAY_PATTERN.search(text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Assembly + emission
# ---------------------------------------------------------------------------


def assemble_reviews(
    responses_by_member: Dict[str, List[ReviewEntry]],
) -> List[ReviewEntry]:
    """Flatten {member_id: [ReviewEntry, ...], ...} into one reviews[] array.

    Order: iterate members in insertion order (typically the council
    roster order), emitting each member's entries in the order parsed
    (stable by req_id per `parse_member_response`). This produces
    deterministic output suitable for diffing across runs.
    """
    flat: List[ReviewEntry] = []
    for member_id, entries in responses_by_member.items():
        for entry in entries:
            if entry.reviewer != member_id:
                raise SemanticCheckError(
                    f"assemble_reviews: entry reviewer={entry.reviewer!r} does "
                    f"not match outer member_id={member_id!r}"
                )
            flat.append(entry)
    return flat


def _schema_version(qpb_root: Optional[Path] = None) -> str:
    version = lib.detect_skill_version(qpb_root)
    return version or "unknown"


def write_semantic_check(
    repo_dir: Path,
    reviews: List[ReviewEntry],
    *,
    schema_version: Optional[str] = None,
    now: Optional[datetime] = None,
    qpb_root: Optional[Path] = None,
) -> Path:
    """Emit quality/citation_semantic_check.json per schemas.md §9 wrapper.

    Returns the written path. Overwrites an existing file (one emission
    per run).
    """
    quality_dir = Path(repo_dir) / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": schema_version or _schema_version(qpb_root),
        "generated_at": archive_lib.utc_extended_timestamp(now),
        "reviews": [
            {
                "req_id": e.req_id,
                "reviewer": e.reviewer,
                "verdict": e.verdict,
                "notes": e.notes,
            }
            for e in reviews
        ],
    }
    path = quality_dir / "citation_semantic_check.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# CLI (operator-driven assembly from captured member JSON responses)
# ---------------------------------------------------------------------------


def _parse_member_response_file(
    member_id: str, response_path: Path, expected_req_ids: Sequence[str]
) -> List[ReviewEntry]:
    try:
        text = response_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SemanticCheckError(
            f"{member_id}: could not read {response_path}: {exc}"
        )
    return parse_member_response(member_id, text, expected_req_ids)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Assemble citation_semantic_check.json from three Council members' "
            "JSON responses. Each --member/--response pair must be adjacent; "
            "order matches the Council roster."
        ),
    )
    parser.add_argument("repo", help="Target repository root.")
    parser.add_argument(
        "--member",
        action="append",
        default=[],
        help="Council member identifier (repeatable; one per --response).",
    )
    parser.add_argument(
        "--response",
        action="append",
        default=[],
        help="Path to the member's JSON response file (repeatable).",
    )
    args = parser.parse_args(argv)

    if len(args.member) != len(args.response):
        print(
            "--member and --response must appear in equal count",
            file=sys.stderr,
        )
        return 2
    if not args.member:
        print("no Council members supplied; nothing to assemble", file=sys.stderr)
        return 2

    repo = Path(args.repo).resolve()
    quality_dir = repo / "quality"
    reqs = collect_tier_12_reqs(quality_dir)
    expected_ids = [r.req_id for r in reqs]

    responses_by_member: Dict[str, List[ReviewEntry]] = {}
    try:
        for member_id, response_path in zip(args.member, args.response):
            entries = _parse_member_response_file(
                member_id, Path(response_path), expected_ids
            )
            responses_by_member[member_id] = entries
    except SemanticCheckError as exc:
        print(f"semantic_check: {exc}", file=sys.stderr)
        return 1

    reviews = assemble_reviews(responses_by_member)
    path = write_semantic_check(repo, reviews)
    print(f"Wrote {path} with {len(reviews)} review entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
