"""formal_docs_ingest.py — walks formal_docs/ and writes formal_docs_manifest.json.

Implements schemas.md §4 (FORMAL_DOC record shape), §1.6 (manifest wrapper),
and §10 invariant #15 (source_path uniqueness). Stdlib-only.

Sidecar metadata convention (introduced in v1.5.0, Phase 2)
-----------------------------------------------------------

The FORMAL_DOC schema requires a `tier` field (1 or 2) for every record,
plus optional `version`, `date`, `url`, `retrieved`. schemas.md does not
mandate where that metadata lives on disk. This module introduces the
minimal extension:

  For each plaintext document at  formal_docs/<stem>.<ext>  (with <ext>
  in {.txt, .md}), a sidecar JSON file at
                 formal_docs/<stem>.meta.json
  provides the per-document metadata.

Sidecar shape:

  {
    "tier": 1,
    "version": "1.1",
    "date": "2019-06-05",
    "url": "https://...",
    "retrieved": "2026-04-15"
  }

Only `tier` is required; every other field is optional. Fields that ingest
computes itself — `source_path`, `document_sha256`, `bytes` — MUST NOT
appear in the sidecar; if present, they are ignored.

Files named `README.md` anywhere under `formal_docs/` are intentionally
skipped: they are folder-level documentation about the formal_docs
convention, not specifications to be cited. Files ending in `.meta.json`
are treated as sidecars and are not themselves ingested.

If two plaintext files share the same stem (e.g., `foo.txt` and `foo.md`),
they would collide on a single `<stem>.meta.json` sidecar; ingest fails
with a clear error in that case.

On a case-insensitive filesystem two source paths that differ only in
case are a uniqueness violation per §10 invariant #15 — ingest fails.

CLI:

  python -m bin.formal_docs_ingest <target_repo_path>

Exit 0 on success (prints a one-line summary). Exit 1 on an IngestError
(validation failure with actionable message). Exit 2 on usage errors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from bin import benchmark_lib

SUPPORTED_EXTENSIONS = frozenset({".txt", ".md"})
SIDECAR_SUFFIX = ".meta.json"
SKIPPED_FILENAMES = frozenset({"README.md"})

# Per-extension guidance for rejected binary/formatted inputs. Keys are
# lowercased file extensions including the leading dot. {path} and
# {path_txt} are substituted when the message is formatted.
REJECT_GUIDANCE = {
    ".pdf": (
        "Convert to plaintext outside the playbook:\n"
        "    pdftotext {path} {path_txt}\n"
        "  Then commit the .txt and re-run."
    ),
    ".docx": (
        "Export to plaintext outside the playbook:\n"
        "    pandoc -t plain {path} -o {path_txt}\n"
        "  Then commit the .txt and re-run."
    ),
    ".doc": (
        "Export to plaintext outside the playbook (LibreOffice or Word → Save As Plain Text);\n"
        "  commit the resulting .txt and re-run."
    ),
    ".rtf": (
        "Export to plaintext outside the playbook (e.g. `pandoc -t plain`); commit the .txt and re-run."
    ),
    ".html": (
        "Convert to plaintext outside the playbook:\n"
        "    pandoc -t plain {path} -o {path_txt}\n"
        "  or\n"
        "    lynx -dump {path} > {path_txt}\n"
        "  Then commit the .txt and re-run."
    ),
    ".htm": (
        "Convert to plaintext outside the playbook:\n"
        "    pandoc -t plain {path} -o {path_txt}\n"
        "  or\n"
        "    lynx -dump {path} > {path_txt}\n"
        "  Then commit the .txt and re-run."
    ),
    ".odt": (
        "Export to plaintext outside the playbook (LibreOffice → Save As Text);\n"
        "  commit the .txt and re-run."
    ),
    ".epub": (
        "Convert to plaintext outside the playbook:\n"
        "    pandoc -t plain {path} -o {path_txt}\n"
        "  Then commit the .txt and re-run."
    ),
}
DEFAULT_REJECT_GUIDANCE = (
    "Convert to plaintext outside the playbook (pandoc/pdftotext/lynx); commit the .txt or .md and re-run."
)


class IngestError(Exception):
    """Recoverable validation failure surfaced to the CLI with exit code 1."""


def _reject_message(path: Path) -> str:
    """Build the extension-specific error message for a rejected file."""
    ext = path.suffix.lower()
    template = REJECT_GUIDANCE.get(ext, DEFAULT_REJECT_GUIDANCE)
    txt_path = path.with_suffix(".txt")
    body = template.format(path=path, path_txt=txt_path)
    return f"{path}: unsupported extension.\n  {body}"


def _sidecar_path(doc: Path) -> Path:
    """Return the sidecar path for a plaintext document."""
    return doc.with_name(doc.stem + SIDECAR_SUFFIX)


def _generated_at() -> str:
    """ISO 8601 UTC timestamp with a 'Z' suffix, second precision."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _schema_version(qpb_root: Path) -> str:
    version = benchmark_lib.detect_skill_version(qpb_root)
    if not version:
        raise IngestError(
            f"could not read playbook version from {qpb_root / 'SKILL.md'}; "
            "schema_version in the manifest requires a valid SKILL.md `metadata.version`."
        )
    return version


def _load_sidecar(sidecar: Path, doc: Path) -> Dict[str, object]:
    """Read and validate a sidecar JSON file per the convention above."""
    if not sidecar.is_file():
        raise IngestError(
            f"{doc}: missing sidecar {sidecar.name}.\n"
            f"  Create {sidecar} with at minimum {{\"tier\": 1}} or {{\"tier\": 2}}.\n"
            "  See schemas.md §4.1 for the full FORMAL_DOC field list."
        )
    try:
        raw = sidecar.read_text(encoding="utf-8")
    except OSError as exc:
        raise IngestError(f"{sidecar}: could not read sidecar: {exc}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise IngestError(f"{sidecar}: invalid JSON: {exc}")
    if not isinstance(data, dict):
        raise IngestError(
            f"{sidecar}: sidecar must be a JSON object; got {type(data).__name__}."
        )

    tier = data.get("tier")
    if tier is None:
        raise IngestError(
            f"{sidecar}: missing required 'tier' (integer 1 or 2). See schemas.md §3.1."
        )
    # bool is a subclass of int in Python; exclude it explicitly.
    if not isinstance(tier, int) or isinstance(tier, bool) or tier not in {1, 2}:
        raise IngestError(
            f"{sidecar}: 'tier' must be integer 1 or 2 (FORMAL_DOC records are "
            f"Tier 1/2 only per schemas.md §4.1); got {tier!r}."
        )

    for field_name in ("version", "date", "url", "retrieved"):
        if field_name in data and data[field_name] is not None:
            if not isinstance(data[field_name], str):
                raise IngestError(
                    f"{sidecar}: optional '{field_name}' must be a string when "
                    f"present; got {type(data[field_name]).__name__}."
                )

    return data


def _build_record(
    doc: Path,
    repo_root: Path,
    sidecar_data: Dict[str, object],
) -> Dict[str, object]:
    """Produce one FORMAL_DOC record per schemas.md §4.1."""
    try:
        source_path = doc.relative_to(repo_root).as_posix()
    except ValueError:
        source_path = str(doc)
    raw = doc.read_bytes()
    record: Dict[str, object] = {
        "source_path": source_path,
        "document_sha256": hashlib.sha256(raw).hexdigest(),
        "tier": sidecar_data["tier"],
    }
    for field_name in ("version", "date", "url", "retrieved"):
        if field_name in sidecar_data and sidecar_data[field_name] is not None:
            record[field_name] = sidecar_data[field_name]
    record["bytes"] = len(raw)
    return record


def collect_documents(formal_docs_dir: Path) -> List[Path]:
    """Walk formal_docs_dir, sorted, returning accepted plaintext files.

    Raises IngestError on an unsupported extension so that the caller can
    surface the specific guidance message.
    """
    if not formal_docs_dir.is_dir():
        return []
    docs: List[Path] = []
    for path in sorted(formal_docs_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name in SKIPPED_FILENAMES:
            continue
        if path.name.endswith(SIDECAR_SUFFIX):
            continue
        ext = path.suffix.lower()
        if ext in SUPPORTED_EXTENSIONS:
            docs.append(path)
            continue
        raise IngestError(_reject_message(path))
    return docs


def ingest(
    target_repo: Path,
    *,
    qpb_root: Optional[Path] = None,
) -> Tuple[Path, List[Dict[str, object]]]:
    """Run ingest against target_repo/formal_docs/ and write the manifest.

    Arguments:
      target_repo — the repo being audited. Its formal_docs/ is scanned and
                    its quality/formal_docs_manifest.json is written.
      qpb_root    — the playbook's own repo root (for reading SKILL.md).
                    Defaults to benchmark_lib.QPB_DIR.

    Returns (manifest_path, records). Raises IngestError on validation
    failures.
    """
    target_repo = Path(target_repo).resolve()
    qpb_root = Path(qpb_root).resolve() if qpb_root is not None else benchmark_lib.QPB_DIR

    formal_docs_dir = target_repo / "formal_docs"
    documents = collect_documents(formal_docs_dir)

    records: List[Dict[str, object]] = []
    seen_lowercase_paths: Dict[str, str] = {}
    seen_sidecars: Dict[Path, Path] = {}

    for doc in documents:
        sidecar = _sidecar_path(doc)
        prior_doc = seen_sidecars.get(sidecar)
        if prior_doc is not None:
            raise IngestError(
                f"{doc}: would share sidecar {sidecar} with {prior_doc}.\n"
                "  Two plaintext documents cannot share a stem within the same "
                "directory; rename one of them."
            )
        seen_sidecars[sidecar] = doc

        sidecar_data = _load_sidecar(sidecar, doc)
        record = _build_record(doc, target_repo, sidecar_data)
        source_path = str(record["source_path"])

        lc = source_path.lower()
        prior_source = seen_lowercase_paths.get(lc)
        if prior_source is not None and prior_source != source_path:
            raise IngestError(
                "FORMAL_DOC source_path uniqueness violation "
                "(schemas.md §10 invariant #15): "
                f"{prior_source!r} and {source_path!r} collide on case-insensitive "
                "filesystems. Rename one of them."
            )
        seen_lowercase_paths[lc] = source_path
        records.append(record)

    manifest = {
        "schema_version": _schema_version(qpb_root),
        "generated_at": _generated_at(),
        "records": records,
    }

    quality_dir = target_repo / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = quality_dir / "formal_docs_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return manifest_path, records


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Walk formal_docs/ in a target repo and write "
            "quality/formal_docs_manifest.json per schemas.md §4 and §1.6."
        ),
    )
    parser.add_argument(
        "target_repo",
        help="Path to the target repository to ingest.",
    )
    parser.add_argument(
        "--qpb-root",
        default=None,
        help="Path to the QPB repo root (reads SKILL.md for schema_version). "
        "Defaults to the QPB repo containing this script.",
    )
    args = parser.parse_args(argv)

    target = Path(args.target_repo)
    if not target.is_dir():
        print(
            f"{target}: target repository directory does not exist",
            file=sys.stderr,
        )
        return 2

    qpb_root = Path(args.qpb_root) if args.qpb_root else None
    try:
        manifest_path, records = ingest(target, qpb_root=qpb_root)
    except IngestError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Ingested {len(records)} FORMAL_DOC records to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
