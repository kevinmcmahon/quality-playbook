"""citation_search.py — Pass B's fuzzy text search step (Phase 3).

bin/citation_verifier.py is a byte-equality verifier; it takes a
known (section, line) locator and produces a deterministic excerpt.
It does NOT search for text. Pass B therefore needs a separate
search step that locates candidate matches in SKILL.md / reference
files, after which citation_verifier.extract_excerpt formalizes the
excerpt at the located line.

Stdlib-only: difflib.SequenceMatcher with token-boundary alignment.
The match is "best contiguous window of source lines whose
normalized text best matches the candidate text," where the score
is SequenceMatcher.ratio() and the window slides over the document
line-by-line.

Threshold (default 0.6) is configurable per call. Below threshold
the search returns None (caller treats as `unverified`); above
threshold returns the (document, line, score, line_range) tuple.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable, Optional


# Default similarity threshold below which the search returns no match.
# Tuned empirically: 0.6 is the rough boundary where minor wording
# differences (synonym substitution, phrase reordering) still match
# while genuinely-unrelated content does not.
DEFAULT_SIMILARITY_THRESHOLD = 0.6

# Minimum candidate-window-size in lines. Single-line windows would
# match too aggressively against any short prose fragment; require at
# least 1 line and grow up to N. We slide windows of varying sizes
# from MIN_WINDOW to MAX_WINDOW.
MIN_WINDOW_LINES = 1
MAX_WINDOW_LINES = 10

# Tokenization for similarity computation. We strip punctuation that
# tends to drift between the LLM's draft and the source (em-dashes,
# Markdown emphasis markers, fenced-block backticks) but preserve
# word boundaries.
_PUNCT_RE = re.compile(r"[`*_~\[\]()#>\\\-—]+")
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class SearchHit:
    """A single candidate match returned by find_best_match."""

    document: str  # repo-relative path
    line_start: int  # 1-based
    line_end: int  # 1-based, inclusive
    score: float  # 0.0..1.0 from SequenceMatcher.ratio()
    matched_text: str  # the source-document window that matched


def _normalize(text: str) -> str:
    """Lowercase + strip incidental punctuation + collapse whitespace.

    Preserves word boundaries so SequenceMatcher's ratio remains
    sensible. Used on both the candidate and the source-document
    window before scoring.
    """
    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def find_best_match(
    candidate_text: str,
    documents: Iterable[tuple[str, str]],
    *,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    min_window_lines: int = MIN_WINDOW_LINES,
    max_window_lines: int = MAX_WINDOW_LINES,
) -> Optional[SearchHit]:
    """Find the best matching contiguous window across all documents.

    `documents` is an iterable of (repo_relative_path, document_text)
    tuples. The function slides a window of varying sizes across each
    document, computes SequenceMatcher.ratio() on the normalized
    candidate vs window text, and returns the best hit if its score
    meets `similarity_threshold`. Returns None if no window meets the
    threshold.
    """
    norm_candidate = _normalize(candidate_text)
    if not norm_candidate:
        return None

    best: Optional[SearchHit] = None
    matcher = SequenceMatcher(autojunk=False)
    matcher.set_seq2(norm_candidate)

    for document, text in documents:
        lines = text.splitlines()
        if not lines:
            continue
        for window_size in range(min_window_lines, max_window_lines + 1):
            if window_size > len(lines):
                break
            for start in range(0, len(lines) - window_size + 1):
                window_lines = lines[start : start + window_size]
                window_text = "\n".join(window_lines)
                norm_window = _normalize(window_text)
                if not norm_window:
                    continue
                matcher.set_seq1(norm_window)
                # quick_ratio is an upper bound; skip windows that
                # cannot possibly beat the current best.
                if best is not None and matcher.quick_ratio() <= best.score:
                    continue
                score = matcher.ratio()
                if best is None or score > best.score:
                    best = SearchHit(
                        document=document,
                        line_start=start + 1,
                        line_end=start + window_size,
                        score=score,
                        matched_text=window_text,
                    )

    if best is None or best.score < similarity_threshold:
        return None
    return best


def collect_documents(
    skill_md_path: Path,
    references_dir: Optional[Path],
    repo_root: Path,
) -> list[tuple[str, str]]:
    """Read SKILL.md + each .md file under references/ into a list.

    Returns (repo_relative_path, document_text) tuples ready to feed
    into find_best_match. Missing references_dir is silently empty.
    """
    out: list[tuple[str, str]] = []
    if skill_md_path.is_file():
        rel = str(skill_md_path.resolve().relative_to(repo_root.resolve())) \
            if skill_md_path.resolve().is_relative_to(repo_root.resolve()) \
            else str(skill_md_path)
        out.append((rel, skill_md_path.read_text(encoding="utf-8")))
    if references_dir is not None and references_dir.is_dir():
        for ref in sorted(references_dir.glob("*.md")):
            rel = str(ref.resolve().relative_to(repo_root.resolve())) \
                if ref.resolve().is_relative_to(repo_root.resolve()) \
                else str(ref)
            out.append((rel, ref.read_text(encoding="utf-8")))
    return out
