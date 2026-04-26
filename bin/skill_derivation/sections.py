"""sections.py — SKILL.md / reference-file section enumeration for Phase 3.

Pass A iterates over the section tree rather than over the file
verbatim; this module produces the deterministic enumeration that
defines the iteration unit set. Decisions are encoded here once so
all four passes agree on what counts as a "section" and what counts
as a meta section.

Rules implemented (per the Phase 3 brief "Section enumeration spec"):

  1. Fenced-block-aware. Headings inside ``` fenced blocks are
     template fragments, NOT document structure -- skipped.
  2. Top-level iteration unit is `##`. `###` and below are
     sub-sections within their parent `##`. The split rule (>300
     lines per top-level section) splits at the next heading level
     down (`###`).
  3. Duplicate-heading-tolerant. Sections are indexed by an
     auto-assigned monotonic `section_idx`; heading text is
     informational only.
  4. Meta-section allowlist (META_SECTION_ALLOWLIST). Headings on
     the allowlist are emitted with `skip_reason: "meta-allowlist"`
     and Pass A produces no draft REQs for them. Pass D treats them
     as intentional skips for completeness accounting.

Stdlib-only.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional


# Sections whose presence does not imply requirement coverage. Tuned
# against QPB's own SKILL.md; adjust per Phase 3 brief F.2 if the
# orphan-flagged set diverges from human judgment.
META_SECTION_ALLOWLIST = frozenset({
    "Why This Exists",
    "Overview",
    "Acknowledgments",
    "Quick Start",
    "Glossary",
    "Changelog",
    "What This Skill Produces",  # describes outputs but not testable claims
    "Terminology",
    "Principles",
    "Reference Files",  # index of references; the references themselves carry the claims
})

# All-caps screaming-section pattern (template-output markers like
# `## RUN_METADATA` should be skipped if they ever escape a fenced
# block). Conservative: only fires on plain UPPER_SNAKE.
_ALL_CAPS_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

# Top-level section split threshold (lines). A `##` section longer
# than this is split at the next `###` heading down so each
# subsection becomes its own iteration unit -- keeps per-call prompt
# size bounded.
SECTION_SPLIT_LINE_THRESHOLD = 300


@dataclass
class Section:
    section_idx: int
    document: str  # repo-relative path
    heading: str   # raw heading text without the leading hashes
    heading_level: int  # 2 for ##, 3 for ###, etc.
    line_start: int  # 1-based line number of the heading line
    line_end: int    # 1-based, INCLUSIVE; the last line that belongs to this section
    skip_reason: Optional[str]  # "meta-allowlist" / "screaming" / None when not skipped


def is_meta_heading(heading: str) -> Optional[str]:
    """Return a skip_reason string if the heading is meta, else None."""
    stripped = heading.strip()
    if stripped in META_SECTION_ALLOWLIST:
        return "meta-allowlist"
    if _ALL_CAPS_RE.match(stripped):
        return "screaming"
    return None


def _iter_top_level_headings(text: str) -> Iterator[tuple]:
    """Yield (line_idx_0based, heading_level, heading_text) for top-level
    `##` and `###` headings, skipping anything inside a fenced code block.

    line_idx is 0-based for internal slicing convenience; callers
    convert to 1-based when populating the Section dataclass.
    """
    in_fence = False
    fence_marker: Optional[str] = None
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        stripped = line.lstrip()
        # Fence open/close detection. Both ``` and ~~~ are markdown
        # fences; we only see ``` in QPB's corpus, but supporting both
        # is correct.
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = "```" if stripped.startswith("```") else "~~~"
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif fence_marker == marker:
                in_fence = False
                fence_marker = None
            continue
        if in_fence:
            continue
        if line.startswith("## ") and not line.startswith("### "):
            yield (idx, 2, line[3:].rstrip())
        elif line.startswith("### "):
            yield (idx, 3, line[4:].rstrip())


def enumerate_sections(
    document_path: Path,
    repo_root: Optional[Path] = None,
    *,
    starting_idx: int = 0,
) -> List[Section]:
    """Parse `document_path` and return its Section list.

    Top-level iteration unit is `##`. `##` sections that exceed
    SECTION_SPLIT_LINE_THRESHOLD lines are split at their first child
    `###` heading, producing one Section per `###` subsection (the
    parent `##` becomes a "header-only" section spanning the lines
    from the `##` to the first `###`).

    `starting_idx` lets callers chain enumeration across multiple
    documents while keeping `section_idx` globally monotonic.
    """
    if repo_root is None:
        repo_root = document_path.parent
    rel_doc = str(document_path.resolve().relative_to(repo_root.resolve())) \
        if document_path.resolve().is_relative_to(repo_root.resolve()) \
        else str(document_path)

    text = document_path.read_text(encoding="utf-8")
    total_lines = len(text.splitlines())

    headings = list(_iter_top_level_headings(text))
    if not headings:
        return []

    sections: List[Section] = []
    next_idx = starting_idx

    # Pre-compute the END line (0-based exclusive) for each heading by
    # looking at the next-or-equal-level heading boundary.
    for hi, (line_idx_0, level, heading) in enumerate(headings):
        # The "next-heading-of-any-level" boundary -- used when this
        # section is small enough that subsections aren't emitted
        # separately, so its line span runs to the next heading.
        if hi + 1 < len(headings):
            next_line_idx_0 = headings[hi + 1][0]
        else:
            next_line_idx_0 = total_lines
        # The "next-heading-of-same-or-higher-level" boundary -- used
        # for the split-rule line-count check, so a level-2 section's
        # length includes all of its level-3+ child content.
        next_same_or_higher_idx_0 = total_lines
        for h_idx_0, h_level, _ in headings:
            if h_idx_0 > line_idx_0 and h_level <= level:
                next_same_or_higher_idx_0 = h_idx_0
                break
        section_lines = next_same_or_higher_idx_0 - line_idx_0
        line_start_1 = line_idx_0 + 1
        line_end_1 = next_line_idx_0  # next heading regardless of level
        if level == 2:
            # Top-level section. Decide split.
            should_split = section_lines > SECTION_SPLIT_LINE_THRESHOLD and any(
                inner_level == 3
                and line_idx_0 < inner_idx_0 < next_same_or_higher_idx_0
                for inner_idx_0, inner_level, _ in headings
            )
            if not should_split:
                sections.append(
                    Section(
                        section_idx=next_idx,
                        document=rel_doc,
                        heading=heading,
                        heading_level=2,
                        line_start=line_start_1,
                        line_end=line_end_1,
                        skip_reason=is_meta_heading(heading),
                    )
                )
                next_idx += 1
            # When splitting, the `##` itself is not emitted as its
            # own section -- the contained `###` subsections are. The
            # `###` headings are picked up by the level-3 branch
            # below as we iterate.
        elif level == 3:
            # Only emit a level-3 section if its parent level-2
            # exceeded the split threshold. Find the parent.
            parent_line_idx_0 = -1
            parent_section_lines = 0
            for parent_idx_0, parent_level, _ in headings:
                if parent_level == 2 and parent_idx_0 < line_idx_0:
                    parent_line_idx_0 = parent_idx_0
            if parent_line_idx_0 < 0:
                continue
            # Compute parent's line span (next heading at same-or-higher level).
            parent_end_idx_0 = total_lines
            for h_idx_0, h_level, _ in headings:
                if h_idx_0 > parent_line_idx_0 and h_level <= 2:
                    parent_end_idx_0 = h_idx_0
                    break
            parent_section_lines = parent_end_idx_0 - parent_line_idx_0
            if parent_section_lines <= SECTION_SPLIT_LINE_THRESHOLD:
                continue  # parent fits in one unit; subsection isn't enumerated
            sections.append(
                Section(
                    section_idx=next_idx,
                    document=rel_doc,
                    heading=heading,
                    heading_level=3,
                    line_start=line_start_1,
                    line_end=line_end_1,
                    skip_reason=is_meta_heading(heading),
                )
            )
            next_idx += 1
    return sections


def write_sections_json(sections: List[Section], out_path: Path) -> None:
    """Emit pass_a_sections.json (the deterministic enumeration artifact)."""
    payload = {
        "schema_version": "1.0",
        "sections": [asdict(s) for s in sections],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(out_path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    import os
    os.replace(tmp, out_path)
