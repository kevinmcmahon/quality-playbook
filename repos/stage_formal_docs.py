"""stage_formal_docs.py — convert docs_gathered/<repo>/ into <repo>/formal_docs/.

v1.5.1 Item 1.1. Closes the runbook gap the overnight benchmark campaign
(2026-04-18) surfaced: setup_repos.sh stopped at docs_gathered/, one layer
short of what the v1.5.0 formal_docs pipeline expects.

For each supported input file this helper produces a plaintext .txt / .md
under formal_docs/ and then invokes bin/setup_formal_docs.py to write the
.meta.json sidecars. A per-repo manifest
(repos/formal_docs_tiers.json) pins the tier for benchmark files where the
heuristic is not good enough (e.g. writing_virtio_drivers.txt).

Supported conversions:

  .md, .txt  → passthrough (copy)
  .rst       → .txt via minimal stdlib regex converter (lossy; see docstring
               below). Does NOT attempt to be a full RST parser — spec text
               content is the goal, not fidelity.
  .html      → .txt via html.parser-based tag stripper.
  .pdf       → skip with a warning. PDF-to-plaintext needs pdftotext or
               pandoc; Item 1.3's pre-run guard catches the resulting
               orphan-plaintext / empty-formal_docs state.
  anything else → skip with a warning.

Stdlib-only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


PASSTHROUGH_EXTENSIONS = frozenset({".md", ".txt"})
CONVERTED_EXTENSIONS = frozenset({".rst", ".html", ".htm"})
SKIP_WITH_WARNING = frozenset({".pdf", ".docx", ".doc", ".rtf", ".odt", ".epub"})


# ---------------------------------------------------------------------------
# RST → plaintext (minimal, lossy)
# ---------------------------------------------------------------------------
#
# The goal is to produce plaintext that preserves the prose and structure
# well enough for the citation gate to resolve line-based anchors and for
# REQ derivation to quote meaningful spec text. It is explicitly NOT a
# full reStructuredText implementation.
#
# Supported transforms:
#   - Drop ".. directive::" lines and their indented bodies (SPDX headers,
#     toctree, rubric, footnote defs, labels).
#   - Drop lines that are purely section underlines (=, -, ~, ^, *, +).
#   - "::" at the end of a line introduces a literal block; replace with ":".
#   - Inline markup:
#       ``foo``          → foo
#       :role:`target`   → target
#       _`label`         → label
#       `text <uri>`_    → text (uri)
#   - Collapse 3-or-more consecutive blank lines to two.

_DIRECTIVE_RE = re.compile(r"^\.\.\s+[A-Za-z0-9_-]+::.*$")
_COMMENT_OR_LABEL_RE = re.compile(r"^\.\.\s+.*$")
_UNDERLINE_RE = re.compile(r"^[=\-~\^\*\+`]{3,}\s*$")
_INLINE_LITERAL_RE = re.compile(r"``([^`]+)``")
_INLINE_ROLE_RE = re.compile(r":[A-Za-z0-9_]+:`([^`]+)`")
_INLINE_LABEL_RE = re.compile(r"_`([^`]+)`")
_INLINE_EXTLINK_RE = re.compile(r"`([^`<]+?)\s*<([^>]+)>`_")
_INLINE_EMPHASIS_RE = re.compile(r"\*\*([^*]+)\*\*|\*([^*]+)\*")


def _strip_inline_markup(text: str) -> str:
    text = _INLINE_EXTLINK_RE.sub(r"\1 (\2)", text)
    text = _INLINE_LITERAL_RE.sub(r"\1", text)

    def _role(match: re.Match) -> str:
        # RST roles like :ref:`Display Text <target>` render as "Display Text";
        # strip a trailing " <target>" when present.
        content = match.group(1)
        return re.sub(r"\s*<[^>]+>\s*$", "", content).strip()

    text = _INLINE_ROLE_RE.sub(_role, text)
    text = _INLINE_LABEL_RE.sub(r"\1", text)

    def _emph(match: re.Match) -> str:
        return match.group(1) or match.group(2) or ""

    text = _INLINE_EMPHASIS_RE.sub(_emph, text)
    return text


def convert_rst_to_plaintext(rst: str) -> str:
    """Convert a reStructuredText string to a lossy plaintext approximation.

    The output keeps section titles, paragraphs, and literal-block content.
    Directives, underlines, roles, and inline markup are stripped.
    """
    out_lines: List[str] = []
    lines = rst.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        # Directive opener ("..  name:: …"): skip the directive line and its
        # indented body. RST directive bodies can span blank lines as long
        # as the next non-blank line is still indented; only the first
        # non-indented content line closes the directive.
        if _DIRECTIVE_RE.match(line) or _COMMENT_OR_LABEL_RE.match(line):
            i += 1
            while i < len(lines):
                if lines[i].strip() == "":
                    # Blank: look ahead to the next non-blank line.
                    j = i + 1
                    while j < len(lines) and lines[j].strip() == "":
                        j += 1
                    if j < len(lines) and lines[j].startswith((" ", "\t")):
                        i = j  # body continues after the blank run
                        continue
                    break
                if lines[i].startswith((" ", "\t")):
                    i += 1
                    continue
                break
            continue

        # Pure-underline lines (section adornments).
        if _UNDERLINE_RE.match(line):
            i += 1
            continue

        # Literal-block opener "foo::" → "foo:"
        stripped = line.rstrip()
        if stripped.endswith("::") and not stripped.endswith(":::"):
            line = stripped[:-2] + ":"

        out_lines.append(_strip_inline_markup(line))
        i += 1

    collapsed: List[str] = []
    blank_run = 0
    for line in out_lines:
        if line.strip() == "":
            blank_run += 1
            if blank_run <= 2:
                collapsed.append("")
        else:
            blank_run = 0
            collapsed.append(line.rstrip())

    while collapsed and collapsed[0] == "":
        collapsed.pop(0)
    while collapsed and collapsed[-1] == "":
        collapsed.pop()
    return "\n".join(collapsed) + "\n"


# ---------------------------------------------------------------------------
# HTML → plaintext (html.parser based)
# ---------------------------------------------------------------------------

_BLOCK_TAGS = frozenset(
    {
        "p", "div", "section", "article", "header", "footer", "nav", "aside",
        "li", "tr", "pre", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6",
        "hr", "br", "ul", "ol", "dl", "dt", "dd", "table", "thead", "tbody",
        "tfoot", "caption", "figure", "figcaption", "main",
    }
)
_IGNORED_TAGS = frozenset({"script", "style", "head", "meta", "link", "title"})


class _HtmlToText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: List[str] = []
        self._suppress_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in _IGNORED_TAGS:
            self._suppress_depth += 1
            return
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _IGNORED_TAGS:
            if self._suppress_depth > 0:
                self._suppress_depth -= 1
            return
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_startendtag(self, tag: str, attrs) -> None:
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._suppress_depth > 0:
            return
        self._chunks.append(data)

    def text(self) -> str:
        raw = "".join(self._chunks)
        # Normalize whitespace: collapse runs of blanks within a line,
        # then collapse 3+ blank lines to two.
        cleaned_lines: List[str] = []
        for line in raw.splitlines():
            squashed = re.sub(r"[ \t]+", " ", line).strip()
            cleaned_lines.append(squashed)
        collapsed: List[str] = []
        blank_run = 0
        for line in cleaned_lines:
            if line == "":
                blank_run += 1
                if blank_run <= 2:
                    collapsed.append("")
            else:
                blank_run = 0
                collapsed.append(line)
        while collapsed and collapsed[0] == "":
            collapsed.pop(0)
        while collapsed and collapsed[-1] == "":
            collapsed.pop()
        return "\n".join(collapsed) + "\n"


def convert_html_to_plaintext(html: str) -> str:
    parser = _HtmlToText()
    parser.feed(html)
    parser.close()
    return parser.text()


# ---------------------------------------------------------------------------
# Staging pipeline
# ---------------------------------------------------------------------------


def _target_name(source: Path) -> Optional[str]:
    """Map an input filename to its output filename, or None to skip."""
    ext = source.suffix.lower()
    if ext in PASSTHROUGH_EXTENSIONS:
        return source.name
    if ext == ".rst":
        return source.stem + ".txt"
    if ext in {".html", ".htm"}:
        return source.stem + ".txt"
    return None


def stage_directory(
    source_dir: Path,
    destination_dir: Path,
    *,
    warn: Optional[List[str]] = None,
) -> Tuple[int, int]:
    """Convert/copy supported files from source_dir into destination_dir.

    Returns (converted_count, skipped_count). Warnings (PDFs, unknown
    extensions, empty results) are appended to ``warn`` when provided.
    """
    if warn is None:
        warn = []
    destination_dir.mkdir(parents=True, exist_ok=True)
    converted = 0
    skipped = 0
    for entry in sorted(source_dir.iterdir()):
        if not entry.is_file():
            continue
        if entry.name.startswith("."):
            continue
        ext = entry.suffix.lower()
        if ext in SKIP_WITH_WARNING:
            warn.append(
                f"SKIP: {entry.name} — {ext} inputs are not stdlib-convertible. "
                "Convert outside the playbook (pdftotext/pandoc) and drop the "
                ".txt into formal_docs/ directly."
            )
            skipped += 1
            continue

        target_name = _target_name(entry)
        if target_name is None:
            warn.append(
                f"SKIP: {entry.name} — unrecognized extension {ext or '(none)'}. "
                "Only .rst, .html, .md, .txt are converted automatically."
            )
            skipped += 1
            continue

        target_path = destination_dir / target_name
        try:
            raw = entry.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            warn.append(f"SKIP: {entry.name} — read failure: {exc}")
            skipped += 1
            continue

        if ext in PASSTHROUGH_EXTENSIONS:
            body = raw if raw.endswith("\n") else raw + "\n"
        elif ext == ".rst":
            body = convert_rst_to_plaintext(raw)
        else:  # .html / .htm
            body = convert_html_to_plaintext(raw)

        if body.strip() == "":
            warn.append(
                f"SKIP: {entry.name} — conversion produced empty output."
            )
            skipped += 1
            continue

        target_path.write_text(body, encoding="utf-8")
        converted += 1
    return converted, skipped


def _repo_manifest(tiers_path: Path, repo_name: str) -> Dict[str, object]:
    if not tiers_path.is_file():
        return {}
    try:
        data = json.loads(tiers_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(
            f"WARN: {tiers_path} is not valid JSON ({exc}); skipping tier overrides.",
            file=sys.stderr,
        )
        return {}
    if not isinstance(data, dict):
        return {}
    entry = data.get(repo_name)
    return entry if isinstance(entry, dict) else {}


def _invoke_setup_helper(
    formal_docs_dir: Path,
    manifest: Dict[str, object],
    setup_helper: Path,
) -> int:
    command = [sys.executable, str(setup_helper), str(formal_docs_dir)]
    scratch: Optional[Path] = None
    if manifest:
        # Write a scratch manifest inside the target repo (outside formal_docs/
        # so ingest never sees it) for setup_formal_docs.py to consume.
        scratch = formal_docs_dir.parent / ".formal_docs_manifest.json"
        scratch.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        command.extend(["--manifest", str(scratch)])
    try:
        # setup_formal_docs exits 1 on "any file flagged" — we surface that but
        # don't treat it as a fatal failure (operators can rerun after fixing).
        result = subprocess.run(command, check=False)
    finally:
        if scratch is not None:
            scratch.unlink(missing_ok=True)
    return result.returncode


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stage_formal_docs.py",
        description=(
            "Convert docs_gathered/<repo>/ into <repo>/formal_docs/ and "
            "generate .meta.json sidecars via bin/setup_formal_docs.py."
        ),
    )
    parser.add_argument(
        "--source",
        required=True,
        help="docs_gathered/<repo>/ directory to read from.",
    )
    parser.add_argument(
        "--destination",
        required=True,
        help="<repo>/formal_docs/ directory to write to.",
    )
    parser.add_argument(
        "--repo-name",
        required=True,
        help=(
            "Short repo name (e.g. 'virtio') used to look up per-repo tier "
            "overrides in repos/formal_docs_tiers.json."
        ),
    )
    parser.add_argument(
        "--tiers-config",
        help=(
            "Path to repos/formal_docs_tiers.json. Defaults to the file next "
            "to this script."
        ),
    )
    parser.add_argument(
        "--setup-helper",
        help=(
            "Path to bin/setup_formal_docs.py. Defaults to ../bin/setup_formal_docs.py "
            "relative to this script."
        ),
    )
    args = parser.parse_args(argv)

    source_dir = Path(args.source).expanduser().resolve()
    destination_dir = Path(args.destination).expanduser().resolve()
    if not source_dir.is_dir():
        print(f"ERROR: source directory does not exist: {source_dir}", file=sys.stderr)
        return 2

    script_dir = Path(__file__).resolve().parent
    tiers_path = (
        Path(args.tiers_config).expanduser().resolve()
        if args.tiers_config
        else script_dir / "formal_docs_tiers.json"
    )
    setup_helper = (
        Path(args.setup_helper).expanduser().resolve()
        if args.setup_helper
        else script_dir.parent / "bin" / "setup_formal_docs.py"
    )
    if not setup_helper.is_file():
        print(
            f"ERROR: setup helper not found: {setup_helper}",
            file=sys.stderr,
        )
        return 2

    warnings: List[str] = []
    converted, skipped = stage_directory(source_dir, destination_dir, warn=warnings)
    for message in warnings:
        print(message)
    print(
        f"Staged {converted} formal_docs file(s) into {destination_dir} "
        f"({skipped} skipped)."
    )
    if converted == 0:
        print(
            "WARN: no formal_docs files were staged. Pre-run guard "
            "(bin/run_playbook.py) will warn at invocation.",
            file=sys.stderr,
        )
        return 0

    manifest = _repo_manifest(tiers_path, args.repo_name)
    exit_code = _invoke_setup_helper(destination_dir, manifest, setup_helper)
    if exit_code == 1:
        # Flagged files present; operator should review. Non-fatal.
        print(
            "NOTE: one or more sidecars fell through to the heuristic default "
            "and were flagged. Review the summary above and update "
            f"{tiers_path} to pin the tier if needed."
        )
        return 0
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
