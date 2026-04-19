"""informal_docs_loader.py — read-only loader for informal_docs/.

Reads plaintext files under <target>/informal_docs/ and returns their
contents so that higher-level orchestration can feed them into an LLM as
Tier 4 (informal documentation) context.

This module is intentionally narrow:

  - No manifest is written. informal_docs do not produce FORMAL_DOC
    records; they are LLM context only.
  - No mutations. The loader is read-only. If the target's
    informal_docs/ is under a gitignore pattern (per the v1.5.0 design),
    this module never causes a write that would surface it.
  - Same plaintext-only policy as formal_docs: only `.txt` and `.md`
    files. Unsupported extensions fail with the same actionable guidance
    messages as formal_docs_ingest.
  - `README.md` anywhere under informal_docs/ is skipped — it's the
    folder-level explanatory doc, not Tier 4 content.

No CLI entry point is exposed; this module is imported by orchestration
code.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from bin import formal_docs_ingest

SUPPORTED_EXTENSIONS = formal_docs_ingest.SUPPORTED_EXTENSIONS
SKIPPED_FILENAMES = formal_docs_ingest.SKIPPED_FILENAMES


class InformalDocsError(Exception):
    """Raised on unsupported extensions or unreadable content under informal_docs/."""


def load_informal_docs(target_repo: Path) -> List[Tuple[str, str]]:
    """Return a sorted list of (repo-relative path, text content) tuples.

    Returns an empty list when informal_docs/ does not exist in target_repo.
    Raises InformalDocsError on an unsupported extension or non-UTF-8 content.
    """
    target_repo = Path(target_repo).resolve()
    root = target_repo / "informal_docs"
    if not root.is_dir():
        return []

    entries: List[Tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in SKIPPED_FILENAMES:
            continue
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise InformalDocsError(formal_docs_ingest._reject_message(path))
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise InformalDocsError(
                f"{path}: informal doc is not valid UTF-8 at byte offset "
                f"{exc.start}: {exc.reason}"
            ) from exc
        relative = path.relative_to(target_repo).as_posix()
        entries.append((relative, text))
    return entries
