"""divergence_internal.py — Phase 4 Part A.1: internal-prose divergence detection.

Reads pass_c_formal.jsonl + pass_c_formal_use_cases.jsonl from
quality/phase3/ and emits pass_e_internal_divergences.jsonl listing
within-prose contradictions per the v1.5.3 Design "Category A:
Internal Divergence" model.

Three-stage indexing per DQ-4-7 of the Phase 4 brief:

  Stage 1 — Partition by (source_document, section_idx). REQ pairs
            are only compared if they share the same key. UCs and
            REQs with source_document=None partition under
            ("SKILL.md", section_idx).
  Stage 2 — Within each section's REQ list, run pairwise excerpt-
            overlap detection. Emit subtype="intra-section".
  Stage 3 — Cross-section countable-claim index. Extract token-
            countable claims (regex matching "<N> <noun>") from
            acceptance_criteria; group records by
            (source_document, normalized_token); within each token's
            REQ list, compare claimed numeric values. Mismatches
            emit subtype="cross-section-countable".

Plus the DQ-4-6 special case: for any UC with
_metadata.phase_3d_synthesized=true, run anchor verification first;
if the UC's section anchor does not loosely support its
steps/acceptance, emit subtype="un-anchored-uc" and skip pairwise
processing for that UC.

Provisional disposition rules per schemas.md §3.9:
- SKILL.md vs reference-file conflict: SKILL.md wins;
  provisional_disposition="spec-fix", target=reference file.
- Intra-SKILL.md (two SKILL.md sections conflict):
  provisional_disposition=null, target=null. Council decides.
- Reference-file vs reference-file: same as intra-SKILL.md.

The module is pure-mechanical and idempotent on inputs. To re-run,
delete pass_e_internal_divergences.jsonl and re-invoke.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constants and regexes.
# ---------------------------------------------------------------------------


# DQ-4-7 Stage 3 countable-claim regex. Matches "<digit-run> <noun>"
# where the noun is in a curated allow-list of skill-prose-meaningful
# units. The allow-list keeps the regex focused on the units that
# actually appear in QPB SKILL.md prose; ad-hoc nouns ("dogs", "ideas")
# would generate noise.
_COUNTABLE_NOUNS = (
    "checks?",
    "phases?",
    "invariants?",
    "fields?",
    "sections?",
    "passes?",
    "tests?",
    "reqs?",
    "ucs?",
    "use cases?",
    "items?",
    "lines?",
    "findings?",
    "bugs?",
    "rules?",
    "patterns?",
    "anchors?",
    "tiers?",
    "strategies?",
    "categories?",
    "modes?",
    "stages?",
    "branches?",
)
_COUNTABLE_RE = re.compile(
    r"\b(\d+)\s+(" + "|".join(_COUNTABLE_NOUNS) + r")\b",
    re.IGNORECASE,
)

# Excerpt-overlap detection: when two excerpts mention overlapping
# line ranges (per pass_c_formal.jsonl's source_line_range, when
# present) they share the same source. We don't have line ranges on
# every Pass C record; the practical fallback is to detect contradiction
# via different countable-claim values within the same partition's
# excerpts. _excerpts_contradict() implements that.

_TOKEN_NORMALIZE_RE = re.compile(r"s\b", re.IGNORECASE)  # crude singularization


# Phase 5 Stage 1 (DQ-5-4) precision-fix support:
#
# Prong 1 — ordinal-context numbers. The 20 chars before the number
# match are inspected; if they end with `\b(Tier|tier|section|
# Section|Phase|phase)\s*$` the match is skipped. Numbered-list
# prefixes (`^\s*N\.\s+` or `^\s*N\)`) suppress matches anchored on
# the list number itself (the regex captures e.g. `1. Read SKILL.md`
# as `('1', 'read')` only when `read` is in the noun list — but the
# defensive check is here regardless).
_ORDINAL_CONTEXT_RE = re.compile(
    r"\b(?:Tier|tier|section|Section|Phase|phase)\s*$"
)
_NUMBERED_LIST_LINE_RE = re.compile(r"(?m)^\s*\d+[.)]\s")

# Prong 2 — artifact-name proximity. A cross-section-countable match
# fires only when at least one of these artifact names appears within
# ±100 characters of the number AND the SAME artifact name appears
# in the other excerpt of the pair. Hardcoded list keeps the rule
# scope tight; new artifacts get added here as they surface.
_ARTIFACT_NAMES: tuple = (
    "REQUIREMENTS.md", "EXPLORATION.md", "BUGS.md", "PROGRESS.md",
    "QUALITY.md", "CONTRACTS.md", "COVERAGE_MATRIX.md",
    "COMPLETENESS_REPORT.md", "INDEX.md", "SKILL.md", "schemas.md",
    "AGENTS.md", "TOOLKIT.md",
    "project_type.json",
    "pass_a_drafts.jsonl", "pass_a_use_case_drafts.jsonl",
    "pass_a_sections.json", "pass_b_citations.jsonl",
    "pass_c_formal.jsonl", "pass_c_formal_use_cases.jsonl",
    "pass_d_audit.json", "pass_d_council_inbox.json",
    "pass_d_section_coverage.json",
    "pass_e_internal_divergences.jsonl",
    "pass_e_internal_candidates.jsonl",
    "pass_e_prose_to_code_divergences.jsonl",
    "pass_e_execution_divergences.jsonl",
    "pass_e_bugs.jsonl", "pass_e_council_inbox.json",
    "quality_gate.py", "run_playbook.py",
    "benchmark_lib.py", "classify_project.py",
    "citation_search.py", "citation_verifier.py",
    "divergence_internal.py", "divergence_to_bugs.py",
    "phase4_inbox.py",
)
_ARTIFACT_PROXIMITY_CHARS = 100

# Prong 3 — context-qualified claims. Hedge words within 30 chars
# BEFORE the number, OR a parenthetical condition within ±50 chars,
# both filter the match. Examples that should be filtered:
#   "the gate typically yields 35-50 tests"
#   "≈50 tests for a medium project (5-15 source files)"
_HEDGE_WORDS_RE = re.compile(
    r"\b(?:typically|roughly|approximately|approx\.?|about|usually|"
    r"often|commonly|generally|sometimes|may|might)\b",
    re.IGNORECASE,
)
_HEDGE_SYMBOL_RE = re.compile(r"[~≈]")
_PARENTHETICAL_CONDITION_RE = re.compile(
    r"\(\s*[\d\-–]+\s+[a-z]+\s*(?:files?|projects?|modules?|sources?|"
    r"lines?|repos?|targets?)\s*\)",
    re.IGNORECASE,
)
_HEDGE_LOOKBEHIND_CHARS = 30
_PARENTHETICAL_LOOKAROUND_CHARS = 50


# ---------------------------------------------------------------------------
# Anchor-verification (DQ-4-6).
# ---------------------------------------------------------------------------


def _normalize_token(noun: str) -> str:
    """Strip trailing 's' so "checks" / "check" group together for
    the cross-section index."""
    return _TOKEN_NORMALIZE_RE.sub("", noun.lower()).strip()


def _is_ordinal_context(excerpt: str, match_start: int) -> bool:
    """Phase 5 Stage 1 prong 1: True iff the 20 chars before the
    matched number end with a Tier/Section/Phase keyword (so the
    number is an ordinal index, not a countable claim).

    Also returns True when the matched number is the leading number
    of a numbered-list line — `^\\s*N[.)]\\s+...` means N is the
    list ordinal, not a quantity claim.
    """
    look_start = max(0, match_start - 20)
    prefix = excerpt[look_start:match_start]
    if _ORDINAL_CONTEXT_RE.search(prefix):
        return True
    # Numbered-list ordinal: walk back to the line start; if the line
    # starts with the number we just matched followed by `.` or `)`,
    # this is a list ordinal.
    line_start = excerpt.rfind("\n", 0, match_start) + 1
    line_prefix = excerpt[line_start:match_start]
    # Strip leading whitespace; everything else before the number on
    # this line must be empty for the number to be the list ordinal.
    if not line_prefix.strip():
        # The match starts at (or just after) the line's leading whitespace.
        # Check the first character AFTER the match's number for `.` or `)`.
        # _COUNTABLE_RE matches `\b(\d+)\s+<noun>` — the digit run is
        # match_start..match_start+len(digits), then whitespace, then noun.
        # We don't have the match end here; for the conservative case we
        # accept "list ordinal" only when the line prefix is purely
        # whitespace (the number IS the first token on the line) AND a
        # `.` or `)` appears immediately after the digit run in the
        # original excerpt. Find the digit run length:
        m = re.match(r"\d+", excerpt[match_start:])
        if m:
            after_idx = match_start + m.end()
            if after_idx < len(excerpt) and excerpt[after_idx] in ".)":
                return True
    return False


def _has_hedge_or_parenthetical(excerpt: str, match_start: int) -> bool:
    """Phase 5 Stage 1 prong 3: True iff a hedge word
    (typically/roughly/approximately/about/etc.) or symbol (~/≈)
    appears within 30 chars BEFORE the number, OR a parenthetical
    condition like `(5-15 source files)` appears within ±50 chars."""
    hedge_start = max(0, match_start - _HEDGE_LOOKBEHIND_CHARS)
    hedge_window = excerpt[hedge_start:match_start]
    if _HEDGE_WORDS_RE.search(hedge_window):
        return True
    if _HEDGE_SYMBOL_RE.search(hedge_window):
        return True
    paren_start = max(0, match_start - _PARENTHETICAL_LOOKAROUND_CHARS)
    paren_end = min(
        len(excerpt), match_start + _PARENTHETICAL_LOOKAROUND_CHARS,
    )
    paren_window = excerpt[paren_start:paren_end]
    if _PARENTHETICAL_CONDITION_RE.search(paren_window):
        return True
    return False


def _artifact_names_in_proximity(
    excerpt: str, match_start: int,
) -> set:
    """Phase 5 Stage 1 prong 2: return the set of artifact names that
    appear within ±100 characters of the matched number. The artifact
    list is _ARTIFACT_NAMES."""
    win_start = max(0, match_start - _ARTIFACT_PROXIMITY_CHARS)
    win_end = min(
        len(excerpt), match_start + _ARTIFACT_PROXIMITY_CHARS,
    )
    window = excerpt[win_start:win_end]
    return {name for name in _ARTIFACT_NAMES if name in window}


def _filtered_countable_matches(excerpt: str) -> list:
    """Return [(num: int, noun: str, match_start: int, artifacts:
    set), ...] for every _COUNTABLE_RE match that survives prongs 1
    (ordinal-context skip) and 3 (hedge/parenthetical skip). Prong 2
    (artifact proximity) is applied at pair-time, not per-match —
    callers consume the artifacts set returned here.
    """
    out = []
    for m in _COUNTABLE_RE.finditer(excerpt):
        if _is_ordinal_context(excerpt, m.start()):
            continue
        if _has_hedge_or_parenthetical(excerpt, m.start()):
            continue
        artifacts = _artifact_names_in_proximity(excerpt, m.start())
        out.append((int(m.group(1)), m.group(2), m.start(), artifacts))
    return out


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def _normalize_source_document(rec: dict, *, is_uc: bool) -> str:
    """REQs with source_document=None or absent → "SKILL.md".
    UCs (no source_document field) → "SKILL.md"."""
    if is_uc:
        return "SKILL.md"
    sd = rec.get("source_document")
    if sd is None or not isinstance(sd, str) or not sd.strip():
        return "SKILL.md"
    return sd


def _read_section_text(
    document_root: Path, source_document: str, section_idx: int,
    sections_path: Path,
) -> str:
    """Read the body text for the given (document, section_idx)
    from the pass_a_sections.json metadata. Returns empty string
    if the section cannot be located."""
    if not sections_path.is_file():
        return ""
    payload = json.loads(sections_path.read_text(encoding="utf-8"))
    sections = payload.get("sections", [])
    target = next(
        (s for s in sections
         if s.get("section_idx") == section_idx
         and s.get("document") == source_document),
        None,
    )
    if target is None:
        return ""
    doc_path = document_root / target["document"]
    if not doc_path.is_file():
        return ""
    lines = doc_path.read_text(encoding="utf-8").splitlines()
    line_start = target.get("line_start", 1)
    line_end = target.get("line_end", line_start)
    return "\n".join(lines[line_start - 1:line_end])


def _uc_anchor_supports(uc: dict, section_text: str) -> bool:
    """DQ-4-6: a hand-authored UC's `steps` and `acceptance` fields
    are loosely supported by the section anchor if at least one
    distinctive token from the UC text appears verbatim in the
    section body. Conservative: any 5+-character word from
    `steps`+`acceptance` matching a 5+-character word in the section
    counts as support. This catches the obvious un-anchored case
    (UC about "Bootstrap self-audit" in a section that doesn't
    discuss bootstrap or self-audit at all) without false-positiving
    on legitimately-anchored UCs.
    """
    if not section_text:
        return False
    uc_text = " ".join([
        " ".join(uc.get("steps", []) or []),
        uc.get("acceptance", "") or "",
        uc.get("trigger", "") or "",
    ]).lower()
    section_lower = section_text.lower()
    uc_tokens = {
        w for w in re.findall(r"[a-z][a-z0-9_-]{4,}", uc_text)
        if w not in _ANCHOR_STOPWORDS
    }
    section_tokens = set(re.findall(r"[a-z][a-z0-9_-]{4,}", section_lower))
    overlap = uc_tokens & section_tokens
    return len(overlap) >= 2


_ANCHOR_STOPWORDS = frozenset({
    "phase", "section", "skill", "playbook", "quality", "should",
    "would", "will", "must", "shall", "exist", "exists", "produce",
    "produced", "produces", "before", "after", "during", "again",
    "across", "every", "within", "without",
})


# ---------------------------------------------------------------------------
# Stage 2: pairwise excerpt overlap within a partition.
# ---------------------------------------------------------------------------


def _record_excerpt(rec: dict) -> str:
    """Pull the prose excerpt to compare. REQs use citation_excerpt
    when present, falling back to acceptance_criteria. UCs use the
    `acceptance` field (UCs have no citations)."""
    if "uc_id" in rec:
        return rec.get("acceptance", "") or ""
    return (
        rec.get("citation_excerpt")
        or rec.get("acceptance_criteria", "")
        or ""
    )


def _excerpts_contradict(rec_a: dict, rec_b: dict) -> Optional[str]:
    """Return a one-line rationale string if the two records
    contradict each other; None otherwise.

    The intra-section contradiction signal is: both excerpts contain
    the same countable noun but different numeric values. That's the
    same shape Stage 3 detects across sections; intra-section just
    runs it on a shorter list. Pure-prose contradictions (e.g., one
    says "MUST" and the other "MUST NOT" about the same subject) are
    not detected here — they're surfaced by Council triage on the
    section-batched inbox.

    Phase 5 Stage 1 (DQ-5-4): each match is filtered against prongs
    1 (ordinal context) and 3 (hedge/parenthetical). Prong 2
    (artifact-name proximity) does NOT apply intra-section — when two
    records share a section, the section context implicitly grounds
    the claim. Cross-section pairs (Stage 3) DO require artifact
    proximity.
    """
    excerpt_a = _record_excerpt(rec_a)
    excerpt_b = _record_excerpt(rec_b)
    if not excerpt_a or not excerpt_b:
        return None
    claims_a: dict = {}
    for num, noun, _, _ in _filtered_countable_matches(excerpt_a):
        claims_a.setdefault(_normalize_token(noun), num)
    claims_b: dict = {}
    for num, noun, _, _ in _filtered_countable_matches(excerpt_b):
        claims_b.setdefault(_normalize_token(noun), num)
    common = set(claims_a) & set(claims_b)
    for token in sorted(common):
        if claims_a[token] != claims_b[token]:
            return (
                f"Two records in the same section claim different "
                f"counts for {token!r}: {rec_a.get('id') or rec_a.get('uc_id')} "
                f"says {claims_a[token]}, "
                f"{rec_b.get('id') or rec_b.get('uc_id')} says {claims_b[token]}."
            )
    return None


# ---------------------------------------------------------------------------
# Disposition resolution per schemas.md §3.9.
# ---------------------------------------------------------------------------


def _resolve_provisional_disposition(
    rec_a: dict, rec_b: Optional[dict], *,
    doc_a: str, doc_b: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    """Return (provisional_disposition, target).

    SKILL.md vs reference-file: SKILL.md wins; the reference file is
    the side that diverges (target = the reference-file path).

    Intra-SKILL.md, intra-reference-file, or reference-file vs
    reference-file: no automatic precedence (return None, None per
    pre-flight MF-1).
    """
    if doc_b is None:
        # Single-record case (un-anchored-uc); no disposition target.
        return None, None
    a_is_skill = doc_a == "SKILL.md"
    b_is_skill = doc_b == "SKILL.md"
    if a_is_skill and not b_is_skill:
        return "spec-fix", doc_b
    if b_is_skill and not a_is_skill:
        return "spec-fix", doc_a
    return None, None


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------


@dataclass
class InternalDivergenceConfig:
    formal_path: Path
    formal_use_cases_path: Path
    sections_path: Path
    document_root: Path  # repo root for reading section text on UC anchor verification
    output_path: Path
    # Phase 5 Stage 1 (DQ-5-4 prong 4): Stage 3 cross-section
    # countable matches now emit to a separate candidates file. If
    # None, defaults to <output_path with stem replaced>.
    candidates_path: Optional[Path] = None
    starting_div_idx: int = 1


@dataclass
class _ComparisonCounts:
    stage1_partitions: int = 0
    stage2_pairs: int = 0
    stage3_pairs: int = 0


def run_divergence_internal(
    config: InternalDivergenceConfig,
) -> dict:
    """Drive Part A.1 end-to-end. Returns a dict:
        {divergences_emitted: int, comparison_count_by_stage: {...}}
    """
    reqs = _read_jsonl(config.formal_path)
    ucs = _read_jsonl(config.formal_use_cases_path)
    counts = _ComparisonCounts()

    # Tag UCs with is_uc=True so callers can branch on it.
    records: list[tuple[dict, bool]] = (
        [(r, False) for r in reqs] + [(u, True) for u in ucs]
    )

    # ------------------------------------------------------------------
    # DQ-4-6: anchor-verify hand-authored UCs first.
    # ------------------------------------------------------------------
    un_anchored_uc_ids: set = set()
    div_idx = config.starting_div_idx
    output_lines: list[str] = []
    for uc in ucs:
        md = uc.get("_metadata") or {}
        if not isinstance(md, dict) or not md.get("phase_3d_synthesized"):
            continue
        section_text = _read_section_text(
            config.document_root,
            "SKILL.md",
            uc.get("section_idx"),
            config.sections_path,
        )
        if _uc_anchor_supports(uc, section_text):
            continue
        un_anchored_uc_ids.add(uc.get("uc_id"))
        rec = {
            "divergence_id": _div_id(div_idx),
            "divergence_type": "internal-prose",
            "subtype": "un-anchored-uc",
            "req_a_id": uc.get("uc_id"),
            "req_b_id": None,
            "source_document": "SKILL.md",
            "section_idx": uc.get("section_idx"),
            "section_heading": _section_heading(
                config.sections_path, "SKILL.md", uc.get("section_idx"),
            ),
            "excerpt_a": uc.get("acceptance", "") or "",
            "excerpt_b": None,
            "rationale": (
                f"Hand-authored UC {uc.get('uc_id')} carries "
                f"_metadata.phase_3d_synthesized=true but its section "
                f"anchor (section_idx={uc.get('section_idx')}) does not "
                "loosely support the UC's steps/acceptance. Phase 4 "
                "skips prose-to-code divergence checks against this "
                "UC; Council should verify the anchor or re-author the UC."
            ),
            "provisional_disposition": None,
            "provisional_disposition_target": None,
            "triage_batch_key": (
                f"SKILL.md::{uc.get('section_idx')}"
                if uc.get("section_idx") is not None
                else "SKILL.md::unknown"
            ),
            "comparison_count_by_stage": None,
        }
        output_lines.append(json.dumps(rec, sort_keys=False))
        div_idx += 1

    # ------------------------------------------------------------------
    # Stage 1: partition.
    # ------------------------------------------------------------------
    partitions: dict = {}
    for rec, is_uc in records:
        # Skip UCs already flagged un-anchored (no pairwise processing).
        if is_uc and rec.get("uc_id") in un_anchored_uc_ids:
            continue
        section_idx = rec.get("section_idx")
        if section_idx is None:
            continue
        document = _normalize_source_document(rec, is_uc=is_uc)
        partitions.setdefault((document, section_idx), []).append(rec)
    counts.stage1_partitions = len(partitions)

    # ------------------------------------------------------------------
    # Stage 2: pairwise comparison within each partition.
    # ------------------------------------------------------------------
    for (document, section_idx), bucket in partitions.items():
        if len(bucket) < 2:
            continue
        section_heading = _section_heading(
            config.sections_path, document, section_idx,
        )
        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                counts.stage2_pairs += 1
                rec_a = bucket[i]
                rec_b = bucket[j]
                rationale = _excerpts_contradict(rec_a, rec_b)
                if rationale is None:
                    continue
                doc_a = _normalize_source_document(
                    rec_a, is_uc="uc_id" in rec_a,
                )
                doc_b = _normalize_source_document(
                    rec_b, is_uc="uc_id" in rec_b,
                )
                disp, target = _resolve_provisional_disposition(
                    rec_a, rec_b, doc_a=doc_a, doc_b=doc_b,
                )
                rec_dict = {
                    "divergence_id": _div_id(div_idx),
                    "divergence_type": "internal-prose",
                    "subtype": "intra-section",
                    "req_a_id": rec_a.get("id") or rec_a.get("uc_id"),
                    "req_b_id": rec_b.get("id") or rec_b.get("uc_id"),
                    "source_document": document,
                    "section_idx": section_idx,
                    "section_heading": section_heading,
                    "excerpt_a": _record_excerpt(rec_a),
                    "excerpt_b": _record_excerpt(rec_b),
                    "rationale": rationale,
                    "provisional_disposition": disp,
                    "provisional_disposition_target": target,
                    "triage_batch_key": f"{document}::{section_idx}",
                    "comparison_count_by_stage": None,
                }
                output_lines.append(json.dumps(rec_dict, sort_keys=False))
                div_idx += 1

    # ------------------------------------------------------------------
    # Stage 3: cross-section countable-claim index, partitioned by
    # (source_document, normalized_token). Only REQs participate (UCs
    # don't carry numeric claims in their acceptance fields).
    # ------------------------------------------------------------------
    # Round 8 Finding 1 + Phase 5 Stage 1 (DQ-5-4) Stage 3 emission:
    #
    # The token_index is populated from _filtered_countable_matches
    # (prongs 1 + 3 applied per-match). Each (rec, value, artifacts)
    # entry is deduped by (rec_id, token, value) within an excerpt
    # (Round 8 fix).
    #
    # Stage 3 emissions go to a SEPARATE candidates file
    # (pass_e_internal_candidates.jsonl) with subtype
    # "cross-section-countable-candidate" — divergence_to_bugs.py
    # reads only the divergences file, so candidates do not produce
    # BUG records by default. Council can promote candidates to
    # divergences manually.
    #
    # Prong 2 (artifact-name proximity) applies pair-wise: a Stage 3
    # candidate fires only when both excerpts share at least one
    # artifact name within ±100 chars of their respective number
    # matches.
    candidates_lines: list[str] = []
    candidate_idx = 1
    token_index: dict = {}
    for rec in reqs:
        document = _normalize_source_document(rec, is_uc=False)
        excerpt = _record_excerpt(rec)
        if not excerpt:
            continue
        seen_in_excerpt: set = set()
        for value, noun, _, artifacts in _filtered_countable_matches(excerpt):
            token = _normalize_token(noun)
            dedupe_key = (rec.get("id"), token, value)
            if dedupe_key in seen_in_excerpt:
                continue
            seen_in_excerpt.add(dedupe_key)
            token_index.setdefault((document, token), []).append(
                (rec, value, artifacts)
            )

    for (document, token), entries in token_index.items():
        if len(entries) < 2:
            continue
        emitted_pairs: set = set()
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                counts.stage3_pairs += 1
                rec_a, num_a, artifacts_a = entries[i]
                rec_b, num_b, artifacts_b = entries[j]
                if num_a == num_b:
                    continue
                if rec_a.get("section_idx") == rec_b.get("section_idx"):
                    continue
                # Prong 2: require shared artifact name in proximity.
                shared_artifacts = artifacts_a & artifacts_b
                if not shared_artifacts:
                    continue
                pair_key = (
                    rec_a.get("id"), rec_b.get("id"), document, token,
                )
                if pair_key in emitted_pairs:
                    continue
                emitted_pairs.add(pair_key)
                doc_a = _normalize_source_document(rec_a, is_uc=False)
                doc_b = _normalize_source_document(rec_b, is_uc=False)
                disp, target = _resolve_provisional_disposition(
                    rec_a, rec_b, doc_a=doc_a, doc_b=doc_b,
                )
                rec_dict = {
                    "divergence_id": f"DIV-INT-CAND-{candidate_idx:03d}",
                    "divergence_type": "internal-prose",
                    "subtype": "cross-section-countable-candidate",
                    "req_a_id": rec_a.get("id"),
                    "req_b_id": rec_b.get("id"),
                    "source_document": document,
                    "section_idx": rec_a.get("section_idx"),
                    "section_heading": _section_heading(
                        config.sections_path, document, rec_a.get("section_idx"),
                    ),
                    "excerpt_a": _record_excerpt(rec_a),
                    "excerpt_b": _record_excerpt(rec_b),
                    "rationale": (
                        f"Cross-section candidate (Phase 5 Stage 1 "
                        f"prong 4 — Council triage required): records "
                        f"in different sections of {document} claim "
                        f"different counts for {token!r} sharing "
                        f"artifact context "
                        f"{sorted(shared_artifacts)!r}. "
                        f"{rec_a.get('id')} (section "
                        f"{rec_a.get('section_idx')}) says {num_a}; "
                        f"{rec_b.get('id')} (section "
                        f"{rec_b.get('section_idx')}) says {num_b}."
                    ),
                    "provisional_disposition": None,
                    "provisional_disposition_target": None,
                    "shared_artifacts": sorted(shared_artifacts),
                    "triage_batch_key": "cross-section-candidate",
                    "comparison_count_by_stage": None,
                }
                candidates_lines.append(json.dumps(rec_dict, sort_keys=False))
                candidate_idx += 1

    # ------------------------------------------------------------------
    # Atomic write — divergences AND candidates (Phase 5 Stage 1).
    # ------------------------------------------------------------------
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = config.output_path.with_name(config.output_path.name + ".tmp")
    tmp.write_text(
        ("\n".join(output_lines) + "\n") if output_lines else "",
        encoding="utf-8",
    )
    os.replace(tmp, config.output_path)

    # Candidates file: derived from output_path stem if not specified.
    candidates_path = (
        config.candidates_path
        if config.candidates_path is not None
        else config.output_path.with_name(
            "pass_e_internal_candidates.jsonl"
        )
    )
    candidates_tmp = candidates_path.with_name(candidates_path.name + ".tmp")
    candidates_tmp.write_text(
        ("\n".join(candidates_lines) + "\n") if candidates_lines else "",
        encoding="utf-8",
    )
    os.replace(candidates_tmp, candidates_path)

    return {
        "divergences_emitted": len(output_lines),
        "candidates_emitted": len(candidates_lines),
        "un_anchored_uc_ids": sorted(un_anchored_uc_ids),
        "comparison_count_by_stage": {
            "stage1_partitions": counts.stage1_partitions,
            "stage2_pairs": counts.stage2_pairs,
            "stage3_pairs": counts.stage3_pairs,
        },
    }


def _div_id(idx: int) -> str:
    return f"DIV-INT-{idx:03d}"


def _section_heading(sections_path: Path, document: str, section_idx) -> str:
    if section_idx is None or not sections_path.is_file():
        return ""
    payload = json.loads(sections_path.read_text(encoding="utf-8"))
    for s in payload.get("sections", []):
        if s.get("section_idx") == section_idx and s.get("document") == document:
            return s.get("heading", "") or ""
    return ""
