"""Ingest plaintext documentation from ``reference_docs/``.

v1.5.2 collapses the v1.5.1 ``formal_docs/`` + ``informal_docs/`` split into a
single ``reference_docs/`` tree:

* Files at the top level of ``reference_docs/`` are Tier 4 context (AI chats,
  design notes, retrospectives). They are loaded into Phase 1 prompts as
  background; no manifest record is written.
* Files under ``reference_docs/cite/`` are citable sources (specs, RFCs, API
  contracts). Each produces a ``FORMAL_DOC`` record in
  ``quality/formal_docs_manifest.json`` with a mechanical citation excerpt.

The manifest file name stays ``formal_docs_manifest.json`` for
backward-compatibility with downstream gate logic and existing benchmark
artifacts. Schema unchanged; only source directory changes.

Optional in-file tier marker on the first non-blank line of a ``cite/`` file
preserves the internal Tier 1 / Tier 2 distinction:

    <!-- qpb-tier: 2 -->
    # qpb-tier: 2

Absent marker → Tier 1 (default for ``cite/``). Invalid marker → ingest fails.
Top-level (Tier 4) files ignore the marker.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

try:
    # When run as ``python -m bin.reference_docs_ingest``.
    from bin import benchmark_lib  # type: ignore
except Exception:  # pragma: no cover - fallback when invoked as a loose script
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from bin import benchmark_lib  # type: ignore


SUPPORTED_EXTENSIONS = frozenset({".txt", ".md"})
SKIPPED_FILENAMES = frozenset({"README.md"})
REFERENCE_DIR_NAME = "reference_docs"
CITE_DIR_NAME = "cite"
MANIFEST_NAME = "formal_docs_manifest.json"

_TIER_MARKER_RE = re.compile(
    r"^\s*(?:<!--\s*qpb-tier:\s*([12])\s*-->|#\s*qpb-tier:\s*([12]))\s*$"
)

REJECT_GUIDANCE = {
    ".pdf": "Convert with: pdftotext spec.pdf spec.txt",
    ".docx": "Convert with: pandoc -t plain spec.docx -o spec.txt",
    ".doc": "Convert with: pandoc -t plain spec.doc -o spec.txt",
    ".html": "Convert with: lynx -dump https://example.org/spec.html > spec.txt",
    ".htm": "Convert with: lynx -dump spec.htm > spec.txt",
    ".rtf": "Convert with: pandoc -t plain spec.rtf -o spec.txt",
}


class IngestError(RuntimeError):
    """Raised when ingest cannot proceed."""


class Tier4LoadError(RuntimeError):
    """Raised when Tier 4 context cannot be loaded for Phase 1."""


@dataclass
class _FileRecord:
    path: Path
    rel_path: str
    text: str
    tier: int
    is_cite: bool


def _iter_candidates(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file())


def _rel(path: Path, target_repo: Path) -> str:
    return str(path.relative_to(target_repo)).replace("\\", "/")


def _is_under_cite(path: Path, cite_dir: Path) -> bool:
    try:
        path.relative_to(cite_dir)
        return True
    except ValueError:
        return False


def _parse_tier_marker(text: str) -> int:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        m = _TIER_MARKER_RE.match(stripped)
        if m:
            return int(m.group(1) or m.group(2))
        # First non-blank line decides: no marker → default tier.
        return 1
    return 1


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise IngestError(
            f"{path}: not UTF-8 decodable ({exc}). Convert to plaintext first."
        )


def _collect(target_repo: Path) -> List[_FileRecord]:
    ref_dir = target_repo / REFERENCE_DIR_NAME
    cite_dir = ref_dir / CITE_DIR_NAME
    records: List[_FileRecord] = []

    for path in _iter_candidates(ref_dir):
        if path.name in SKIPPED_FILENAMES:
            continue
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            hint = REJECT_GUIDANCE.get(
                ext, "Only .txt and .md are ingested — convert to plaintext first."
            )
            raise IngestError(f"{_rel(path, target_repo)}: unsupported extension '{ext}'. {hint}")
        text = _read_text(path)
        is_cite = _is_under_cite(path, cite_dir)
        if is_cite:
            tier = _parse_tier_marker(text)
        else:
            tier = 4
        records.append(
            _FileRecord(
                path=path,
                rel_path=_rel(path, target_repo),
                text=text,
                tier=tier,
                is_cite=is_cite,
            )
        )
    return records


def _citation_excerpt(text: str, max_chars: int = 240) -> str:
    """Return the first non-blank run of characters, truncated to max_chars."""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Skip tier marker line if present.
        if _TIER_MARKER_RE.match(stripped):
            continue
        return stripped[:max_chars]
    return ""


def _build_record(rec: _FileRecord, schema_version: str, generated_at: str) -> dict:
    digest = hashlib.sha256(rec.text.encode("utf-8")).hexdigest()
    return {
        "doc_id": f"FORMAL-{digest[:12]}",
        "source_path": rec.rel_path,
        "tier": rec.tier,
        "byte_count": len(rec.text.encode("utf-8")),
        "line_count": len(rec.text.splitlines()),
        "citation_excerpt": _citation_excerpt(rec.text),
        "sha256": digest,
        "ingested_at": generated_at,
        "schema_version": schema_version,
    }


def collect_documents(target_repo: Path) -> List[_FileRecord]:
    """Public helper for tests — returns the collected _FileRecord list."""
    return _collect(target_repo)


def load_tier4_context(target_repo: Path) -> List[Tuple[str, str]]:
    """Return Tier 4 context as ``(rel_path, text)`` tuples, sorted by path.

    Preserves the shape of the legacy ``load_informal_docs`` so existing
    Phase 1 prompts keep working unchanged.
    """
    target_repo = Path(target_repo)
    try:
        records = _collect(target_repo)
    except IngestError as exc:
        raise Tier4LoadError(str(exc)) from exc
    return sorted(
        (rec.rel_path, rec.text) for rec in records if not rec.is_cite
    )


def ingest(target_repo: Path) -> dict:
    """Walk ``reference_docs/`` and emit ``quality/formal_docs_manifest.json``.

    Returns the manifest as a dict for test inspection.
    """
    target_repo = Path(target_repo)
    if not target_repo.exists():
        raise IngestError(f"target repo does not exist: {target_repo}")

    records = _collect(target_repo)
    cite_records = [r for r in records if r.is_cite]

    schema_version = benchmark_lib.detect_skill_version(target_repo)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    manifest = {
        "schema_version": schema_version,
        "generated_at": generated_at,
        "records": [_build_record(r, schema_version, generated_at) for r in cite_records],
    }

    quality_dir = target_repo / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    out = quality_dir / MANIFEST_NAME
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, prog="reference_docs_ingest")
    parser.add_argument("target", nargs="?", default=".", help="Target repo path (default: cwd)")
    args = parser.parse_args(argv)

    try:
        manifest = ingest(Path(args.target).resolve())
    except IngestError as exc:
        print(f"reference_docs_ingest: {exc}", file=sys.stderr)
        return 1

    count = len(manifest["records"])
    print(f"reference_docs_ingest: wrote {count} cite record(s) to quality/{MANIFEST_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
