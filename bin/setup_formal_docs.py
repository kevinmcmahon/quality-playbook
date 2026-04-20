"""setup_formal_docs.py — operator helper that generates .meta.json sidecars
for plaintext files under formal_docs/.

v1.5.1 Item 1.2. Companion reader is bin/formal_docs_ingest.py; this writer
must emit sidecars that the reader accepts unchanged. See schemas.md §1-2
for the underlying contract.

The helper walks a formal_docs/ directory, locates supported plaintext
files (.txt and .md per schemas.md §2), and writes a minimal sidecar at
`<stem>.meta.json` for each file that lacks one. Tier is assigned by a
filename-pattern heuristic; operators can override per-file via interactive
mode or a JSON manifest.

When a sidecar already exists, the prior file is moved to
`formal_docs/.sidecar_backups/<YYYYMMDDTHHMMSSZ>/<stem>.meta.json` before
the new one is written. Operators never lose hand-authored sidecars.
`--overwrite` suppresses the backup step.

CLI:

  python3 bin/setup_formal_docs.py <formal_docs_dir>
      [--interactive] [--overwrite] [--manifest <path>]

Exit codes:
  0 — clean (all sidecars written without heuristic fallback).
  1 — one or more files fell through to the default-Tier-2 "flagged"
      bucket; operator should review the summary and edit tiers that
      are wrong. Non-blocking — rerun after fixing.
  2 — I/O error, JSON-parse error, or manifest validation error.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, TextIO


SUPPORTED_EXTENSIONS = frozenset({".txt", ".md"})
SIDECAR_SUFFIX = ".meta.json"
SKIPPED_FILENAMES = frozenset({"README.md"})
BACKUP_DIRNAME = ".sidecar_backups"

TIER1_TOKENS = ("rfc", "spec", "standard", "behavioral")
TIER2_TOKENS = ("guide", "howto", "tutorial", "example")

# Optional sidecar fields permitted by schemas.md §4.1 beyond the required
# `tier`. A manifest entry may supply any subset.
OPTIONAL_SIDECAR_FIELDS = ("version", "date", "url", "retrieved")


@dataclass
class FileOutcome:
    """What happened to one plaintext file during the setup pass."""

    path: Path
    tier: int
    flagged: bool = False
    backed_up: bool = False
    skipped: bool = False  # interactive skip
    source: str = "heuristic"  # one of: heuristic, manifest, interactive


@dataclass
class SetupResult:
    outcomes: List[FileOutcome] = field(default_factory=list)

    @property
    def generated(self) -> int:
        return sum(1 for o in self.outcomes if not o.skipped)

    @property
    def backed_up(self) -> int:
        return sum(1 for o in self.outcomes if o.backed_up)

    @property
    def flagged(self) -> int:
        return sum(1 for o in self.outcomes if o.flagged and not o.skipped)

    @property
    def skipped(self) -> int:
        return sum(1 for o in self.outcomes if o.skipped)


def _heuristic_tier(name: str) -> tuple[int, bool]:
    """Return (tier, flagged) for a filename using the pattern heuristic.

    Case-insensitive. `flagged=True` means the heuristic fell through to the
    default Tier 2 bucket and the operator should review.
    """
    lowered = name.lower()
    if any(token in lowered for token in TIER1_TOKENS):
        return 1, False
    if any(token in lowered for token in TIER2_TOKENS):
        return 2, False
    return 2, True


def _sidecar_path(doc: Path) -> Path:
    return doc.with_name(doc.stem + SIDECAR_SUFFIX)


def _backup_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _collect_documents(formal_docs_dir: Path) -> List[Path]:
    """Walk the directory and return accepted plaintext files, sorted.

    Matches the convention in bin/formal_docs_ingest.collect_documents but
    does NOT raise on unsupported extensions — those are silently skipped
    here. The ingest step is the enforcement point; this helper only
    prepares sidecars for files it can actually stage.
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
        # Skip files inside the backup directory tree.
        if BACKUP_DIRNAME in path.parts:
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            docs.append(path)
    return docs


def _normalize_manifest(
    manifest: Dict[str, object],
) -> Dict[str, Dict[str, object]]:
    """Normalize a filename -> tier | entry-dict map to filename -> entry-dict.

    Accepts already-normalized entries (the output of _load_manifest) as well
    as the bare-int shape produced by callers that hand-build the mapping
    (e.g. repos/stage_formal_docs.py reading formal_docs_tiers.json directly).
    Silently drops entries with invalid tiers — callers validating via
    _load_manifest will have raised before getting here.
    """
    normalized: Dict[str, Dict[str, object]] = {}
    for filename, entry in manifest.items():
        if isinstance(entry, int) and not isinstance(entry, bool):
            normalized[filename] = {"tier": entry}
        elif isinstance(entry, dict) and "tier" in entry:
            normalized[filename] = dict(entry)
    return normalized


def _load_manifest(path: Path) -> Dict[str, Dict[str, object]]:
    """Load a manifest JSON. Accepts two shapes:

        { "virtio.txt": 1, "guide.md": 2 }

        { "virtio.txt": {"tier": 1, "version": "1.1", ...} }

    Normalizes to the object form. Returns mapping basename -> entry dict.
    Raises ValueError on a bad shape.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(
            f"manifest must be a JSON object mapping filename to tier (or tier-entry); got {type(raw).__name__}"
        )
    normalized: Dict[str, Dict[str, object]] = {}
    for filename, entry in raw.items():
        if not isinstance(filename, str) or not filename:
            raise ValueError(f"manifest key must be a non-empty string; got {filename!r}")
        if isinstance(entry, int) and not isinstance(entry, bool):
            normalized[filename] = {"tier": entry}
            continue
        if isinstance(entry, dict):
            if "tier" not in entry:
                raise ValueError(
                    f"manifest entry for {filename!r} missing required 'tier' field"
                )
            tier = entry["tier"]
            if isinstance(tier, bool) or not isinstance(tier, int) or tier not in {1, 2}:
                raise ValueError(
                    f"manifest entry for {filename!r}: 'tier' must be integer 1 or 2; got {tier!r}"
                )
            normalized[filename] = dict(entry)
            continue
        raise ValueError(
            f"manifest entry for {filename!r} must be an integer tier or an object; got {type(entry).__name__}"
        )
    return normalized


def _build_sidecar_payload(entry: Dict[str, object]) -> Dict[str, object]:
    """Assemble the sidecar JSON body from a manifest entry or heuristic."""
    payload: Dict[str, object] = {"tier": int(entry["tier"])}
    for field_name in OPTIONAL_SIDECAR_FIELDS:
        if field_name in entry and entry[field_name] is not None:
            payload[field_name] = entry[field_name]
    return payload


def _write_sidecar(sidecar: Path, payload: Dict[str, object]) -> None:
    body = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    sidecar.write_text(body, encoding="utf-8")


def _backup_existing_sidecar(
    sidecar: Path,
    formal_docs_dir: Path,
    run_timestamp: str,
) -> None:
    """Move an existing sidecar to .sidecar_backups/<ts>/<stem>.meta.json."""
    backup_root = formal_docs_dir / BACKUP_DIRNAME / run_timestamp
    backup_root.mkdir(parents=True, exist_ok=True)
    destination = backup_root / sidecar.name
    shutil.move(str(sidecar), str(destination))


def _prompt_interactive(
    doc: Path,
    default_tier: int,
    flagged: bool,
    stream_in: TextIO,
    stream_out: TextIO,
) -> Optional[int]:
    """Interactive per-file tier prompt. Returns None on skip.

    Empty input accepts the default. EOF is treated as skip (not a crash).
    """
    marker = " [flagged]" if flagged else ""
    stream_out.write(
        f"{doc.name}{marker}: suggested tier {default_tier}. "
        "Press Enter to accept, '1'/'2' to override, 's' to skip: "
    )
    stream_out.flush()
    try:
        raw = stream_in.readline()
    except (EOFError, KeyboardInterrupt):
        return None
    if raw == "":  # EOF reached without newline
        return None
    response = raw.strip().lower()
    if response == "":
        return default_tier
    if response in {"s", "skip"}:
        return None
    if response in {"1", "2"}:
        return int(response)
    stream_out.write("  (unrecognized response; skipping)\n")
    return None


def setup_sidecars(
    formal_docs_dir: Path,
    *,
    interactive: bool = False,
    overwrite: bool = False,
    manifest: Optional[Dict[str, Dict[str, object]]] = None,
    unknown_manifest_keys: Sequence[str] = (),
    stream_in: Optional[TextIO] = None,
    stream_out: Optional[TextIO] = None,
    run_timestamp: Optional[str] = None,
) -> SetupResult:
    """Core setup pass. Returns a SetupResult describing what happened.

    The CLI is a thin wrapper around this function. Unit tests drive it
    directly with in-memory stdin/stdout streams.
    """
    if stream_in is None:
        stream_in = sys.stdin
    if stream_out is None:
        stream_out = sys.stdout
    if run_timestamp is None:
        run_timestamp = _backup_timestamp()

    manifest = _normalize_manifest(manifest or {})
    result = SetupResult()

    # Warn for manifest keys that don't correspond to any file. This is a
    # warning, not an error — lets operators keep a manifest that covers
    # several repos without erroring on missing-from-this-repo entries.
    for key in unknown_manifest_keys:
        stream_out.write(
            f"WARN: manifest entry '{key}' does not match any file under {formal_docs_dir}\n"
        )

    for doc in _collect_documents(formal_docs_dir):
        heuristic_tier, flagged = _heuristic_tier(doc.name)
        source = "heuristic"
        entry: Dict[str, object] = {"tier": heuristic_tier}

        if doc.name in manifest:
            entry = dict(manifest[doc.name])
            flagged = False
            source = "manifest"

        if interactive:
            default_tier = int(entry["tier"])
            chosen = _prompt_interactive(
                doc, default_tier, flagged, stream_in, stream_out
            )
            if chosen is None:
                result.outcomes.append(
                    FileOutcome(
                        path=doc, tier=default_tier, flagged=flagged, skipped=True, source=source
                    )
                )
                continue
            entry["tier"] = chosen
            # Operator confirmation clears the "flagged" bit — they've looked.
            flagged = False
            source = "interactive"

        sidecar = _sidecar_path(doc)
        backed_up = False
        if sidecar.exists():
            if overwrite:
                sidecar.unlink()
            else:
                _backup_existing_sidecar(sidecar, formal_docs_dir, run_timestamp)
                backed_up = True

        payload = _build_sidecar_payload(entry)
        _write_sidecar(sidecar, payload)
        result.outcomes.append(
            FileOutcome(
                path=doc,
                tier=int(entry["tier"]),
                flagged=flagged,
                backed_up=backed_up,
                source=source,
            )
        )

    return result


def _print_summary(
    result: SetupResult, formal_docs_dir: Path, stream_out: TextIO
) -> None:
    stream_out.write(
        f"{result.generated} sidecars generated, "
        f"{result.backed_up} skipped (existing sidecars backed up), "
        f"{result.flagged} flagged for review\n"
    )
    for outcome in result.outcomes:
        if outcome.flagged and not outcome.skipped:
            try:
                rel = outcome.path.relative_to(formal_docs_dir).as_posix()
            except ValueError:
                rel = outcome.path.name
            stream_out.write(
                f"  FLAGGED  {rel}  -> Tier {outcome.tier} (heuristic default; review)\n"
            )


def _resolve_unknown_manifest_keys(
    manifest: Dict[str, Dict[str, object]], formal_docs_dir: Path
) -> List[str]:
    known_names = {p.name for p in _collect_documents(formal_docs_dir)}
    return sorted(k for k in manifest if k not in known_names)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="setup_formal_docs.py",
        description=(
            "Generate .meta.json sidecars for plaintext files under a "
            "formal_docs/ directory. See schemas.md §4 for the FORMAL_DOC "
            "sidecar contract."
        ),
    )
    parser.add_argument(
        "formal_docs_dir",
        help="Path to the target formal_docs/ directory to set up.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt per file to confirm or override the tier assignment.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Overwrite existing sidecars in place. Default is to move the "
            "prior sidecar to .sidecar_backups/<timestamp>/ before writing."
        ),
    )
    parser.add_argument(
        "--manifest",
        help=(
            "Path to a JSON manifest mapping filename -> tier (or object "
            "with tier + optional version/date/url/retrieved) for "
            "deterministic regeneration."
        ),
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    formal_docs_dir = Path(args.formal_docs_dir).expanduser().resolve()
    if not formal_docs_dir.is_dir():
        print(
            f"ERROR: formal_docs directory does not exist: {formal_docs_dir}",
            file=sys.stderr,
        )
        return 2

    manifest: Dict[str, Dict[str, object]] = {}
    unknown_keys: Sequence[str] = ()
    if args.manifest:
        manifest_path = Path(args.manifest).expanduser().resolve()
        if not manifest_path.is_file():
            print(
                f"ERROR: manifest file not found: {manifest_path}",
                file=sys.stderr,
            )
            return 2
        try:
            manifest = _load_manifest(manifest_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: could not load manifest: {exc}", file=sys.stderr)
            return 2
        unknown_keys = _resolve_unknown_manifest_keys(manifest, formal_docs_dir)

    try:
        result = setup_sidecars(
            formal_docs_dir,
            interactive=args.interactive,
            overwrite=args.overwrite,
            manifest=manifest,
            unknown_manifest_keys=unknown_keys,
        )
    except OSError as exc:
        print(f"ERROR: I/O failure during setup: {exc}", file=sys.stderr)
        return 2

    _print_summary(result, formal_docs_dir, sys.stdout)
    return 1 if result.flagged > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
