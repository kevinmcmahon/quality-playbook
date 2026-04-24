#!/usr/bin/env python3
"""quality_gate.py — Post-run validation gate for Quality Playbook artifacts.

Mechanically checks artifact conformance issues that model self-attestation
persistently misses. Now the sole gate script; the earlier quality_gate.sh
(bash) has been retired. See quality_gate/test_quality_gate.py for the test
suite.

Usage:
    ./quality_gate.py .                          # Check current directory (benchmark mode)
    ./quality_gate.py --general .                # Check with relaxed thresholds
    ./quality_gate.py virtio                     # Check named repo (from repos/)
    ./quality_gate.py --all                      # Check all current-version repos
    ./quality_gate.py --version 1.3.27 virtio    # Check specific version

Exit codes:
    0 — all checks passed
    1 — one or more checks failed

Runs on Python 3.8+ with only the standard library.
"""

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# Allow soft import of bin/citation_verifier for v1.5.1 byte-equality checks.
# The gate lives at .github/skills/quality_gate/quality_gate.py inside the QPB
# install; the repo root is three parents up. When the gate is installed
# standalone into a target repo without bin/, the import fails silently and
# byte-equality is skipped with a WARN rather than a hard FAIL.
_CITATION_VERIFIER = None
try:
    _QPB_ROOT = SCRIPT_DIR.parent.parent.parent
    if str(_QPB_ROOT) not in sys.path:
        sys.path.insert(0, str(_QPB_ROOT))
    from bin import citation_verifier as _CITATION_VERIFIER  # noqa: E402
except Exception:  # noqa: BLE001 — missing / misinstalled bin/ is tolerable
    _CITATION_VERIFIER = None

# Global counters — reset per invocation via main(). Tests that call check_repo
# directly should reset these in setUp.
FAIL = 0
WARN = 0


# v1.5.2 — REQ Pattern field (Lever 2)
VALID_PATTERN_VALUES = frozenset({"whitelist", "parity", "compensation"})

_REQ_PATTERN_RE = re.compile(
    r"^\s*-\s*Pattern:\s*(\S+)\s*$", re.IGNORECASE | re.MULTILINE
)


def extract_req_pattern(req_block):
    """Return the REQ's pattern tag from a REQUIREMENTS.md block, or None.

    Raises ValueError when the block carries an invalid pattern value. Valid
    values are VALID_PATTERN_VALUES. Absent field returns None.
    """
    m = _REQ_PATTERN_RE.search(req_block)
    if not m:
        return None
    value = m.group(1).strip()
    if value not in VALID_PATTERN_VALUES:
        raise ValueError(
            "Invalid REQ pattern '{}'. Expected one of: {}".format(
                value, sorted(VALID_PATTERN_VALUES)
            )
        )
    return value


# v1.5.2 — cardinality gate (Lever 3)

VALID_REASON_CLASSES = frozenset({
    "out-of-scope",
    "deprecated",
    "platform-gated",
    "handled-upstream",
    "intentionally-partial",
})

_CELL_ID_RE = re.compile(r"^REQ-\d+/cell-[A-Za-z0-9_]+-[A-Za-z0-9_]+$")

_COVERS_RE = re.compile(
    r"^\s*-\s*Covers:\s*\[(.*?)\]\s*$", re.IGNORECASE | re.MULTILINE
)

_CONSOLIDATION_RE = re.compile(
    r"^\s*-\s*Consolidation rationale:\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_BUG_HEADING_RE = re.compile(r"^###\s+BUG-(\d+):", re.MULTILINE)


def _parse_covers(bug_block):
    m = _COVERS_RE.search(bug_block)
    if not m:
        return []
    raw = m.group(1).strip()
    if not raw:
        return []
    items = [s.strip() for s in raw.split(",")]
    return [s for s in items if s]


def _parse_consolidation_rationale(bug_block):
    m = _CONSOLIDATION_RE.search(bug_block)
    if not m:
        return None
    text = m.group(1).strip()
    return text or None


def _split_bug_blocks(bugs_md_text):
    """Return list of (bug_id, body) pairs."""
    positions = [(m.start(), m.group(1)) for m in _BUG_HEADING_RE.finditer(bugs_md_text)]
    result = []
    for idx, (start, bug_id) in enumerate(positions):
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(bugs_md_text)
        result.append(("BUG-{}".format(bug_id), bugs_md_text[start:end]))
    return result


def _bug_primary_requirement(block):
    m = re.search(
        r"^\s*-\s*Primary requirement:\s*(REQ-\d+)", block, re.MULTILINE | re.IGNORECASE
    )
    return m.group(1) if m else None


def _load_json_or_none(path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_text_safe(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def validate_cardinality_gate(repo_dir):
    """Run the v1.5.2 cardinality reconciliation gate.

    Returns a list of failure strings. An empty list means the gate passed.
    Caller decides how to surface failures (print / fail()).

    Inputs expected in repo_dir/quality/:
      - REQUIREMENTS.md (source of pattern-tagged REQs)
      - BUGS.md (source of Covers: annotations)
      - compensation_grid.json (source of cell set per REQ)
      - compensation_grid_downgrades.json (optional; source of downgrade cells)
    """
    failures = []
    q = Path(repo_dir) / "quality"

    grid_path = q / "compensation_grid.json"
    grid = _load_json_or_none(grid_path)
    if grid is None:
        # No grid file: only a problem if any pattern-tagged REQs exist.
        req_text = _read_text_safe(q / "REQUIREMENTS.md")
        if _REQ_PATTERN_RE.search(req_text):
            failures.append(
                "cardinality gate: pattern-tagged REQs exist but "
                "quality/compensation_grid.json is missing"
            )
        return failures

    reqs = grid.get("reqs") or {}
    if not isinstance(reqs, dict):
        failures.append("compensation_grid.json: 'reqs' is not an object")
        return failures

    # Load BUGS.md and index covers by REQ
    bugs_text = _read_text_safe(q / "BUGS.md")
    covers_by_req = {}
    for bug_id, block in _split_bug_blocks(bugs_text):
        covers = _parse_covers(block)
        if len(covers) >= 2:
            if not _parse_consolidation_rationale(block):
                failures.append(
                    "{}: Covers has {} entries but 'Consolidation rationale:' is missing or empty".format(
                        bug_id, len(covers)
                    )
                )
        for cell_id in covers:
            if not _CELL_ID_RE.match(cell_id):
                failures.append(
                    "{}: malformed cell ID '{}' (expected REQ-N/cell-<item>-<site>)".format(
                        bug_id, cell_id
                    )
                )
                continue
            req_id = cell_id.split("/", 1)[0]
            covers_by_req.setdefault(req_id, set()).add(cell_id)

    # Load downgrades and validate each record
    downgrades = _load_json_or_none(q / "compensation_grid_downgrades.json") or {"downgrades": []}
    downgrade_cells_by_req = {}
    for rec in downgrades.get("downgrades", []):
        rid = rec.get("cell_id", "")
        if not _CELL_ID_RE.match(rid):
            failures.append("downgrade record: malformed cell_id '{}'".format(rid))
            continue
        for field in ("authority_ref", "site_citation", "reason_class", "falsifiable_claim"):
            value = rec.get(field)
            if not value or not isinstance(value, str) or not value.strip():
                failures.append(
                    "downgrade record {}: missing or empty field '{}'".format(rid, field)
                )
        reason = rec.get("reason_class", "")
        if reason and reason not in VALID_REASON_CLASSES:
            failures.append(
                "downgrade record {}: reason_class '{}' not in {}".format(
                    rid, reason, sorted(VALID_REASON_CLASSES)
                )
            )
        req_id = rid.split("/", 1)[0]
        downgrade_cells_by_req.setdefault(req_id, set()).add(rid)

    # Reconcile per-REQ
    for req_id, entry in reqs.items():
        pattern = entry.get("pattern")
        if pattern not in {"whitelist", "parity", "compensation"}:
            failures.append(
                "compensation_grid.json: {} has invalid or missing pattern '{}'".format(
                    req_id, pattern
                )
            )
            continue
        cells = entry.get("cells") or []
        grid_cell_ids = {c.get("cell_id") for c in cells if isinstance(c, dict)}
        grid_cell_ids.discard(None)
        # Only absent cells require coverage
        absent_cells = {
            c.get("cell_id") for c in cells
            if isinstance(c, dict) and c.get("present") is False
        }
        absent_cells.discard(None)

        covered = covers_by_req.get(req_id, set())
        downgraded = downgrade_cells_by_req.get(req_id, set())
        uncovered = absent_cells - covered - downgraded

        if uncovered:
            failures.append(
                "{}: uncovered cells — {}".format(req_id, ", ".join(sorted(uncovered)))
            )

        # Every covered cell must be in the grid
        stray = (covered | downgraded) - grid_cell_ids
        if stray:
            failures.append(
                "{}: Covers/downgrade cells not in grid — {}".format(
                    req_id, ", ".join(sorted(stray))
                )
            )

    return failures


def _reset_counters():
    global FAIL, WARN
    FAIL = 0
    WARN = 0


def fail(msg, reason=None, *, line=None):
    """Emit a structured failure line and increment FAIL.

    Phase 5 r3 format: `<path>[:<line>]: <reason>` — no "FAIL:" label, so
    output is grep-parseable as `^[^:]+:[0-9]*:? .+$`. The prefix `FAIL:` is
    deliberately removed; the global FAIL counter (summarised in main()) is
    the authoritative count of failures per run.

    Preferred forms:
        fail("quality/INDEX.md", "file missing")
            -> "  quality/INDEX.md: file missing"
        fail("quality/INDEX.md", "missing required field 'x'", line=42)
            -> "  quality/INDEX.md:42: missing required field 'x'"

    Legacy single-arg form (transitional; still supported — most v1.4.x
    messages already embed a path-like token):
        fail("BUGS.md missing or not a file")
            -> "  BUGS.md missing or not a file"
    """
    global FAIL
    if reason is None:
        print(f"  {msg}")
    elif line is None:
        print(f"  {msg}: {reason}")
    else:
        print(f"  {msg}:{line}: {reason}")
    FAIL += 1


def pass_(msg):
    print(f"  PASS: {msg}")


def warn(msg):
    global WARN
    print(f"  WARN: {msg}")
    WARN += 1


def info(msg):
    print(f"  INFO: {msg}")


# --- JSON helpers (proper parsing, not grep-style) ---


def load_json(path):
    """Parse JSON file. Return parsed value, or None on any error."""
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def has_key(data, key):
    """True if `data` is a dict containing `key`."""
    return isinstance(data, dict) and key in data


def get_str(data, key):
    """Return data[key] if it's a string, else empty string."""
    if not isinstance(data, dict):
        return ""
    val = data.get(key)
    return val if isinstance(val, str) else ""


def count_per_bug_field(bugs_list, field):
    """Count bugs in list that have `field` set."""
    if not isinstance(bugs_list, list):
        return 0
    return sum(1 for b in bugs_list if isinstance(b, dict) and field in b)


# --- File helpers ---


def has_file_matching(directory, patterns):
    """True if any file in `directory` (non-recursive) matches any glob pattern."""
    if not directory.is_dir():
        return False
    for pat in patterns:
        for _ in directory.glob(pat):
            return True
    return False


def count_files_matching(directory, pattern):
    """Count files in `directory` (non-recursive) matching glob pattern."""
    if not directory.is_dir():
        return 0
    return sum(1 for _ in directory.glob(pattern))


def first_file_matching(directory, patterns):
    """Return first matching path or None."""
    if not directory.is_dir():
        return None
    for pat in patterns:
        for p in directory.glob(pat):
            return p
    return None


def file_contains(path, pattern):
    """True if any line in file matches pattern (regex string or compiled)."""
    if not path.is_file():
        return False
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if pattern.search(line):
                    return True
    except OSError:
        pass
    return False


def read_first_line_stripped(path):
    """Return first line of file with whitespace stripped."""
    if not path.is_file():
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            line = f.readline()
    except OSError:
        return ""
    return re.sub(r"\s", "", line)


def validate_iso_date(date_str):
    """Return one of: 'valid', 'placeholder', 'future', 'bad_format', 'empty'.

    Placeholders are checked before format so that 'YYYY-MM-DD' is reported
    as 'placeholder' rather than 'bad_format'. The bash version's order was
    flipped, causing 'YYYY-MM-DD' to be misreported — both still FAIL but the
    Python version gives the clearer message.
    """
    if not date_str:
        return "empty"
    if date_str in ("YYYY-MM-DD", "0000-00-00"):
        return "placeholder"
    date_part = date_str[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_part):
        return "bad_format"
    if len(date_str) > 10 and not re.fullmatch(r"T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?", date_str[10:]):
        return "bad_format"
    today = date.today().isoformat()
    if date_part > today:
        return "future"
    return "valid"


def detect_skill_version(locations):
    """Read `version:` value from the first existing SKILL.md-like file."""
    for loc in locations:
        if loc.is_file():
            try:
                with open(loc, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        m = re.match(r"^\s*(?:version:|\*\*Version:\*\*)\s*([0-9]+(?:\.[0-9]+)+)\b",
                                     line, re.IGNORECASE)
                        if m:
                            return m.group(1)
            except OSError:
                continue
    return ""


def read_skill_value_line(path, prefix):
    """Mimic: grep -m1 'prefix' FILE | sed 's/.*prefix *//' | tr -d ' '."""
    if not path.is_file():
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if prefix in line:
                    v = re.sub(rf".*{re.escape(prefix)}\s*", "", line, count=1)
                    return v.replace(" ", "").rstrip("\n").rstrip("\r")
    except OSError:
        pass
    return ""


def detect_project_language(repo_dir):
    """Walk up to 3 dirs deep, return first language whose extension is present.

    Mirrors bash `find -maxdepth 3 -not -path ...` behavior.
    """
    language_order = [
        ("go", ".go"),
        ("py", ".py"),
        ("java", ".java"),
        ("kt", ".kt"),
        ("rs", ".rs"),
        ("ts", ".ts"),
        ("js", ".js"),
        ("scala", ".scala"),
        ("c", ".c"),
        ("agc", ".agc"),
    ]
    excluded = {"vendor", "node_modules", ".git", "quality", "repos"}

    def present(base, target_ext):
        stack = [(Path(base), 1)]
        while stack:
            curr, depth = stack.pop()
            try:
                for entry in os.scandir(curr):
                    name = entry.name
                    if entry.is_dir(follow_symlinks=False):
                        if name in excluded:
                            continue
                        if depth < 3:
                            stack.append((Path(entry.path), depth + 1))
                    elif entry.is_file(follow_symlinks=False):
                        if name.endswith(target_ext):
                            return True
            except (OSError, PermissionError):
                continue
        return False

    for lang, ext in language_order:
        if present(repo_dir, ext):
            return lang
    return ""


def count_source_files(repo_dir):
    """Count source files up to 4 dirs deep, excluding vendor/node_modules/etc."""
    src_count = 0
    exts = {".go", ".py", ".java", ".kt", ".rs", ".ts", ".js", ".scala",
            ".c", ".h", ".agc"}
    excluded = {"vendor", "node_modules", ".git", "quality"}

    def walk(base, current_depth, max_depth):
        nonlocal src_count
        try:
            for entry in os.scandir(base):
                name = entry.name
                if entry.is_dir(follow_symlinks=False):
                    if current_depth < max_depth and name not in excluded:
                        walk(entry.path, current_depth + 1, max_depth)
                elif entry.is_file(follow_symlinks=False):
                    dot = name.rfind(".")
                    if dot >= 0 and name[dot:] in exts:
                        src_count += 1
        except (OSError, PermissionError):
            pass

    walk(str(repo_dir), 1, 4)
    return src_count


# --- Section checks ---


def check_file_existence(repo_dir, q, strictness):
    """File existence section (benchmark 40)."""
    print("[File Existence]")
    for f in ["BUGS.md", "REQUIREMENTS.md", "QUALITY.md", "PROGRESS.md",
              "COVERAGE_MATRIX.md", "COMPLETENESS_REPORT.md"]:
        if (q / f).is_file():
            pass_(f"{f} exists")
        else:
            fail(f"{f} missing")

    for f in ["CONTRACTS.md", "RUN_CODE_REVIEW.md", "RUN_SPEC_AUDIT.md",
              "RUN_INTEGRATION_TESTS.md", "RUN_TDD_TESTS.md"]:
        if (q / f).is_file():
            pass_(f"{f} exists")
        else:
            fail(f"{f} missing")

    if has_file_matching(q, ["test_functional.*", "functional_test.*",
                             "FunctionalSpec.*", "FunctionalTest.*",
                             "functional.test.*"]):
        pass_("functional test file exists")
    else:
        fail("functional test file missing (test_functional.*, functional_test.*, FunctionalSpec.*, FunctionalTest.*, functional.test.*)")

    if (repo_dir / "AGENTS.md").is_file():
        pass_("AGENTS.md exists")
    else:
        fail("AGENTS.md missing (required at project root)")

    if (q / "EXPLORATION.md").is_file():
        pass_("EXPLORATION.md exists")
        _check_exploration_sections(q / "EXPLORATION.md")
    else:
        fail("EXPLORATION.md missing")

    cr_dir = q / "code_reviews"
    if cr_dir.is_dir() and has_file_matching(cr_dir, ["*.md"]):
        pass_("code_reviews/ has .md files")
    else:
        fail("code_reviews/ missing or empty")

    sa_dir = q / "spec_audits"
    if sa_dir.is_dir():
        triage_count = count_files_matching(sa_dir, "*triage*")
        auditor_count = count_files_matching(sa_dir, "*auditor*")
        if triage_count > 0:
            pass_("spec_audits/ has triage file")
        else:
            fail("spec_audits/ missing triage file")
        if auditor_count > 0:
            pass_(f"spec_audits/ has {auditor_count} auditor file(s)")
        else:
            fail("spec_audits/ missing individual auditor files")

        if triage_count > 0:
            has_probes = False
            if (sa_dir / "triage_probes.sh").is_file():
                has_probes = True
                pass_("triage_probes.sh exists (executable triage evidence)")
            elif (q / "mechanical" / "verify.sh").is_file() and \
                 file_contains(q / "mechanical" / "verify.sh", r"probe|triage|auditor"):
                has_probes = True
                pass_("verify.sh contains triage probe assertions")
            if not has_probes:
                msg = "No executable triage evidence found (expected spec_audits/triage_probes.sh or probe assertions in mechanical/verify.sh)"
                if strictness == "benchmark":
                    fail(msg)
                else:
                    warn(msg)
    else:
        fail("spec_audits/ directory missing")


def check_bugs_heading(q):
    """BUGS.md heading-format section (benchmark 39).

    Returns (bug_count, bug_ids).
    """
    print("[BUGS.md Heading Format]")
    bugs_md = q / "BUGS.md"
    if not bugs_md.is_file():
        fail("BUGS.md missing")
        return 0, []

    try:
        bugs_content = bugs_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        bugs_content = ""
    lines = bugs_content.splitlines()

    correct_headings = sum(1 for ln in lines
                           if re.match(r"^### BUG-([HML]|[0-9])[0-9]*", ln))
    wrong_headings = sum(1 for ln in lines
                         if re.match(r"^## BUG-", ln)
                         and not re.match(r"^### BUG-", ln))
    deep_headings = sum(1 for ln in lines
                        if re.match(r"^#{4,} BUG-([HML]|[0-9])", ln))
    bold_headings = sum(1 for ln in lines
                        if re.match(r"^\*\*BUG-([HML]|[0-9])", ln))
    bullet_headings = sum(1 for ln in lines
                          if re.match(r"^- BUG-([HML]|[0-9])", ln))

    bug_count = correct_headings

    if (correct_headings > 0 and wrong_headings == 0 and deep_headings == 0
            and bold_headings == 0 and bullet_headings == 0):
        pass_(f"All {correct_headings} bug headings use ### BUG-NNN format")
    else:
        if wrong_headings > 0:
            fail(f"{wrong_headings} heading(s) use ## instead of ###")
        if deep_headings > 0:
            fail(f"{deep_headings} heading(s) use #### or deeper instead of ###")
        if bold_headings > 0:
            fail(f"{bold_headings} heading(s) use **BUG- format")
        if bullet_headings > 0:
            fail(f"{bullet_headings} heading(s) use - BUG- format")
        if correct_headings == 0 and wrong_headings == 0:
            if re.search(r"^##\s+(No confirmed bugs|Zero confirmed bugs)\s*$",
                         bugs_content, re.MULTILINE | re.IGNORECASE):
                pass_("Zero-bug run — no headings expected")
            else:
                bug_count = wrong_headings + deep_headings + bold_headings + bullet_headings
                warn("No ### BUG-NNN headings found in BUGS.md")
        else:
            bug_count = correct_headings + wrong_headings + bold_headings + bullet_headings

    # Extract canonical bug IDs: BUG-NNN or BUG-HNN / BUG-MNN / BUG-LNN
    raw = re.findall(r"BUG-(?:[HML][0-9]+|[0-9]+)", bugs_content)
    filtered = [b for b in raw if re.fullmatch(r"BUG-(?:[HML][0-9]+|[0-9]+)", b)]
    bug_ids = sorted(set(filtered))

    return bug_count, bug_ids


def check_tdd_sidecar(q, bug_count):
    """TDD sidecar JSON (benchmarks 14, 41)."""
    print("[TDD Sidecar JSON]")
    json_path = q / "results" / "tdd-results.json"

    if bug_count <= 0:
        info("Zero bugs — tdd-results.json not required")
        return None

    if not json_path.is_file():
        fail(f"tdd-results.json missing ({bug_count} bugs require it)")
        return None

    pass_(f"tdd-results.json exists ({bug_count} bugs)")

    data = load_json(json_path)
    if data is None:
        # File exists but unparseable — fail all root key checks
        for key in ["schema_version", "skill_version", "date", "project",
                    "bugs", "summary"]:
            fail(f"missing root key '{key}'")
        fail("schema_version is 'missing', expected '1.1'")
        return None

    for key in ["schema_version", "skill_version", "date", "project",
                "bugs", "summary"]:
        if has_key(data, key):
            pass_(f"has '{key}'")
        else:
            fail(f"missing root key '{key}'")

    sv = get_str(data, "schema_version")
    if sv == "1.1":
        pass_("schema_version is '1.1'")
    else:
        fail(f"schema_version is '{sv or 'missing'}', expected '1.1'")

    bugs_list = data.get("bugs") if isinstance(data, dict) else None
    if not isinstance(bugs_list, list):
        bugs_list = []

    for field in ["id", "requirement", "red_phase", "green_phase",
                  "verdict", "fix_patch_present", "writeup_path"]:
        fcount = count_per_bug_field(bugs_list, field)
        if fcount >= bug_count:
            pass_(f"per-bug field '{field}' present ({fcount}x)")
        elif fcount > 0:
            warn(f"per-bug field '{field}' found {fcount}x, expected {bug_count}")
        else:
            fail(f"per-bug field '{field}' missing entirely")

    # Non-canonical field names (at any level — check root and bugs)
    bad_fields = ["bug_id", "bug_name", "status", "phase", "result"]
    for bad in bad_fields:
        found = has_key(data, bad) or any(
            has_key(b, bad) for b in bugs_list if isinstance(b, dict)
        )
        if found:
            fail(f"non-canonical field '{bad}' found (use standard field names)")

    summary = data.get("summary") if isinstance(data, dict) else None
    if not isinstance(summary, dict):
        summary = {}
    for skey in ["total", "verified", "confirmed_open", "red_failed", "green_failed"]:
        if skey in summary:
            pass_(f"summary has '{skey}'")
        else:
            fail(f"summary missing '{skey}' count")

    # Date validation
    tdd_date = get_str(data, "date")
    status = validate_iso_date(tdd_date)
    if status == "empty":
        fail("tdd-results.json date field missing or empty")
    elif status == "bad_format":
        fail(f"tdd-results.json date '{tdd_date}' is not ISO 8601 (YYYY-MM-DD)")
    elif status == "placeholder":
        fail(f"tdd-results.json date is placeholder '{tdd_date}'")
    elif status == "future":
        fail(f"tdd-results.json date '{tdd_date}' is in the future")
    else:
        pass_(f"tdd-results.json date '{tdd_date}' is valid")

    # Verdict enum
    allowed_verdicts = {"TDD verified", "red failed", "green failed",
                        "confirmed open", "deferred"}
    bad_verdicts = 0
    for b in bugs_list:
        if isinstance(b, dict) and "verdict" in b:
            v = b.get("verdict")
            if v not in allowed_verdicts:
                bad_verdicts += 1
    if bad_verdicts == 0:
        pass_("all verdict values are canonical")
    else:
        fail(f"{bad_verdicts} non-canonical verdict value(s)")

    return data


def check_tdd_logs(q, bug_count, bug_ids, tdd_data):
    """TDD log files and sidecar-to-log cross-validation."""
    print("[TDD Log Files]")
    if bug_count <= 0:
        info("Zero bugs — TDD log files not required")
        return

    patches_dir = q / "patches"
    results_dir = q / "results"
    valid_tags = {"RED", "GREEN", "NOT_RUN", "ERROR"}

    red_found = 0
    red_missing = 0
    green_found = 0
    green_missing = 0
    green_expected = 0
    red_bad_tag = 0
    green_bad_tag = 0

    for bid in bug_ids:
        red_log = results_dir / f"{bid}.red.log"
        if red_log.is_file():
            red_found += 1
            tag = read_first_line_stripped(red_log)
            if tag not in valid_tags:
                red_bad_tag += 1
        else:
            red_missing += 1

        fix_patch = first_file_matching(patches_dir, [f"{bid}-fix*.patch"])
        if fix_patch is not None:
            green_expected += 1
            green_log = results_dir / f"{bid}.green.log"
            if green_log.is_file():
                green_found += 1
                tag = read_first_line_stripped(green_log)
                if tag not in valid_tags:
                    green_bad_tag += 1
            else:
                green_missing += 1

    if red_missing == 0 and red_found > 0:
        pass_(f"All {red_found} confirmed bug(s) have red-phase logs")
    elif red_found > 0:
        fail(f"{red_missing} confirmed bug(s) missing red-phase log (BUG-NNN.red.log)")
    else:
        fail("No red-phase logs found (every confirmed bug needs quality/results/BUG-NNN.red.log)")

    if green_expected > 0:
        if green_missing == 0:
            pass_(f"All {green_found} bug(s) with fix patches have green-phase logs")
        else:
            fail(f"{green_missing} bug(s) with fix patches missing green-phase log (BUG-NNN.green.log)")
    else:
        info("No fix patches found — green-phase logs not required")

    if red_bad_tag > 0:
        fail(f"{red_bad_tag} red-phase log(s) missing valid first-line status tag (expected RED/GREEN/NOT_RUN/ERROR)")
    elif red_found > 0:
        pass_("All red-phase logs have valid status tags")
    if green_bad_tag > 0:
        fail(f"{green_bad_tag} green-phase log(s) missing valid first-line status tag (expected RED/GREEN/NOT_RUN/ERROR)")
    elif green_found > 0:
        pass_("All green-phase logs have valid status tags")

    # Sidecar-to-log cross-validation (BUG-M18)
    if tdd_data is not None and isinstance(tdd_data, dict):
        bugs_list = tdd_data.get("bugs") or []
        if not isinstance(bugs_list, list):
            bugs_list = []
        # Index bugs by id for lookup
        bug_by_id = {}
        for b in bugs_list:
            if isinstance(b, dict) and isinstance(b.get("id"), str):
                bug_by_id[b["id"]] = b

        xv_checked = 0
        xv_mismatch = 0

        for bid in bug_ids:
            bug_obj = bug_by_id.get(bid)
            sidecar_red = get_str(bug_obj, "red_phase") if bug_obj else ""
            sidecar_green = get_str(bug_obj, "green_phase") if bug_obj else ""

            red_log = results_dir / f"{bid}.red.log"
            if sidecar_red and red_log.is_file():
                log_tag = read_first_line_stripped(red_log)
                xv_checked += 1
                if sidecar_red == "fail" and log_tag != "RED":
                    xv_mismatch += 1
                    fail(f"{bid}: sidecar red_phase='{sidecar_red}' but log first-line is '{log_tag}' (expected RED)")
                elif sidecar_red == "pass" and log_tag != "GREEN":
                    xv_mismatch += 1
                    fail(f"{bid}: sidecar red_phase='{sidecar_red}' but log first-line is '{log_tag}' (expected GREEN)")

            green_log = results_dir / f"{bid}.green.log"
            if sidecar_green and green_log.is_file():
                log_tag = read_first_line_stripped(green_log)
                xv_checked += 1
                if sidecar_green == "pass" and log_tag != "GREEN":
                    xv_mismatch += 1
                    fail(f"{bid}: sidecar green_phase='{sidecar_green}' but log first-line is '{log_tag}' (expected GREEN)")
                elif sidecar_green == "fail" and log_tag != "RED":
                    xv_mismatch += 1
                    fail(f"{bid}: sidecar green_phase='{sidecar_green}' but log first-line is '{log_tag}' (expected RED)")

        if xv_checked > 0 and xv_mismatch == 0:
            pass_(f"Sidecar-to-log cross-validation passed ({xv_checked} checks)")
        elif xv_checked == 0:
            info("Sidecar-to-log cross-validation: no matching pairs to check")

    # TDD_TRACEABILITY.md
    if red_found > 0:
        if (q / "TDD_TRACEABILITY.md").is_file():
            pass_(f"TDD_TRACEABILITY.md exists ({red_found} bugs with red-phase results)")
        else:
            fail("TDD_TRACEABILITY.md missing (mandatory when bugs have red-phase results)")


def check_integration_sidecar(q, strictness):
    """Integration sidecar JSON section."""
    print("[Integration Sidecar JSON]")
    ij = q / "results" / "integration-results.json"

    if not ij.is_file():
        if strictness == "benchmark":
            warn("integration-results.json not present")
        else:
            info("integration-results.json not present (optional in general mode)")
        return

    data = load_json(ij)

    for key in ["schema_version", "skill_version", "date", "project",
                "recommendation", "groups", "summary", "uc_coverage"]:
        if has_key(data, key):
            pass_(f"has '{key}'")
        else:
            fail(f"missing key '{key}'")

    summary = data.get("summary") if isinstance(data, dict) else None
    if not isinstance(summary, dict):
        summary = {}
    for iskey in ["total_groups", "passed", "failed", "skipped"]:
        if iskey in summary:
            pass_(f"integration summary has '{iskey}'")
        else:
            fail(f"integration summary missing required sub-key '{iskey}'")

    isv = get_str(data, "schema_version")
    if isv == "1.1":
        pass_("integration schema_version is '1.1'")
    else:
        fail(f"integration schema_version is '{isv or 'missing'}', expected '1.1'")

    int_date = get_str(data, "date")
    if int_date:  # match bash: if [ -n "$int_date" ]
        status = validate_iso_date(int_date)
        if status == "bad_format":
            fail(f"integration-results.json date '{int_date}' is not ISO 8601 (YYYY-MM-DD)")
        elif status == "placeholder":
            fail(f"integration-results.json date is placeholder '{int_date}'")
        elif status == "future":
            fail(f"integration-results.json date '{int_date}' is in the future")
        else:
            pass_(f"integration-results.json date '{int_date}' is valid")

    rec = get_str(data, "recommendation")
    if rec in ("SHIP", "FIX BEFORE MERGE", "BLOCK"):
        pass_(f"recommendation '{rec}' is canonical")
    elif rec:
        fail(f"recommendation '{rec}' is non-canonical (must be SHIP/FIX BEFORE MERGE/BLOCK)")
    else:
        fail("recommendation missing")

    # groups[].result enum
    allowed_results = {"pass", "fail", "skipped", "error"}
    bad_results = 0
    groups = data.get("groups") if isinstance(data, dict) else None
    if isinstance(groups, list):
        for g in groups:
            if isinstance(g, dict) and "result" in g:
                if g.get("result") not in allowed_results:
                    bad_results += 1
    if bad_results == 0:
        pass_("all groups[].result values are canonical")
    else:
        fail(f"{bad_results} non-canonical groups[].result value(s) (must be pass/fail/skipped/error)")

    # uc_coverage value enum
    allowed_uc = {"covered_pass", "covered_fail", "not_mapped"}
    bad_uc = 0
    uc_cov = data.get("uc_coverage") if isinstance(data, dict) else None
    if isinstance(uc_cov, dict):
        for v in uc_cov.values():
            if v not in allowed_uc:
                bad_uc += 1
    if bad_uc == 0:
        pass_("all uc_coverage values are canonical")
    else:
        fail(f"{bad_uc} non-canonical uc_coverage value(s) (must be covered_pass/covered_fail/not_mapped)")


def check_recheck_sidecar(q):
    """Recheck sidecar JSON (schema 1.0, uses 'results' key not 'bugs')."""
    print("[Recheck Sidecar JSON]")
    rj = q / "results" / "recheck-results.json"
    rs = q / "results" / "recheck-summary.md"

    if not rj.is_file():
        info("recheck-results.json not present (only required when recheck mode was run)")
        return

    pass_("recheck-results.json exists")
    data = load_json(rj)

    # SKILL.md recheck template uses 'results' as the array key, not 'bugs'.
    for key in ["schema_version", "skill_version", "date", "project",
                "results", "summary"]:
        if has_key(data, key):
            pass_(f"recheck has '{key}'")
        else:
            fail(f"recheck missing root key '{key}'")

    rsv = get_str(data, "schema_version")
    if rsv == "1.0":
        pass_("recheck schema_version is '1.0'")
    else:
        fail(f"recheck schema_version is '{rsv or 'missing'}', expected '1.0'")

    rdate = get_str(data, "date")
    if rdate:
        status = validate_iso_date(rdate)
        if status == "bad_format":
            fail(f"recheck-results.json date '{rdate}' is not ISO 8601 (YYYY-MM-DD)")
        elif status == "placeholder":
            fail(f"recheck-results.json date is placeholder '{rdate}'")
        elif status == "future":
            fail(f"recheck-results.json date '{rdate}' is in the future")
        else:
            pass_(f"recheck-results.json date '{rdate}' is valid")

    if rs.is_file():
        pass_("recheck-summary.md exists")
    else:
        fail("recheck-summary.md missing (required companion to recheck-results.json)")


def check_use_cases(repo_dir, q, strictness):
    """Use case identifier section (benchmarks 43, 48)."""
    print("[Use Cases]")
    req_md = q / "REQUIREMENTS.md"
    if not req_md.is_file():
        fail("REQUIREMENTS.md missing")
        return

    try:
        req_content = req_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        req_content = ""

    # uc_ids: count of lines matching UC-N (bash grep -cE counts lines)
    uc_ids = sum(1 for ln in req_content.splitlines()
                 if re.search(r"UC-[0-9]+", ln))
    uc_unique = len(set(re.findall(r"UC-[0-9]+", req_content)))

    src_count = count_source_files(repo_dir) if repo_dir.is_dir() else 0
    min_uc = 3 if src_count < 5 else 5

    if uc_unique >= min_uc:
        pass_(f"Found {uc_unique} distinct UC identifiers ({uc_ids} total references, {src_count} source files)")
    elif uc_unique > 0:
        connector = "for" if strictness == "general" else "required for"
        msg = f"Only {uc_unique} distinct UC identifiers (minimum {min_uc} {connector} {src_count} source files)"
        if strictness == "general":
            warn(msg)
        else:
            fail(msg)
    else:
        fail("No canonical UC-NN identifiers in REQUIREMENTS.md")


def check_test_file_extension(repo_dir, q):
    """Test file extension matches project language (benchmark 47)."""
    print("[Test File Extension]")
    func_test = first_file_matching(q, ["test_functional.*", "functional_test.*",
                                        "FunctionalSpec.*", "FunctionalTest.*",
                                        "functional.test.*"])
    reg_test = first_file_matching(q, ["test_regression.*"])

    if func_test is None:
        warn("No functional test file found across the supported naming matrix")
        return

    ext = func_test.suffix.lstrip(".") if func_test.suffix else ""
    detected_lang = detect_project_language(repo_dir) if repo_dir.is_dir() else ""

    if not detected_lang:
        info(f"Cannot detect project language — skipping extension check (test_functional.{ext})")
        return

    lang_to_valid = {
        "go": "go",
        "py": "py",
        "java": "java",
        "kt": "kt java",
        "rs": "rs",
        "ts": "ts",
        "js": "js ts",
        "scala": "scala",
        "c": "c py sh",
        "agc": "py sh",
    }
    valid_ext = lang_to_valid.get(detected_lang, "")
    valid_list = valid_ext.split()
    primary = valid_list[0] if valid_list else ""

    if ext in valid_list:
        pass_(f"{func_test.name} matches project language ({detected_lang})")
    else:
        fail(f"{func_test.name} does not match project language ({detected_lang}) — expected .{primary}")

    if reg_test is not None:
        reg_ext = reg_test.suffix.lstrip(".") if reg_test.suffix else ""
        if reg_ext in valid_list:
            pass_(f"test_regression.{reg_ext} matches project language ({detected_lang})")
        else:
            fail(f"test_regression.{reg_ext} does not match project language ({detected_lang}) — expected .{primary}")


def check_terminal_gate(q):
    """Terminal Gate section in PROGRESS.md."""
    print("[Terminal Gate]")
    progress_md = q / "PROGRESS.md"
    if not progress_md.is_file():
        return
    pat = re.compile(r"^#+ *Terminal", re.IGNORECASE | re.MULTILINE)
    if file_contains(progress_md, pat):
        pass_("PROGRESS.md has Terminal Gate section")
    else:
        fail("PROGRESS.md missing Terminal Gate section")


def check_mechanical(q):
    """Mechanical verification section."""
    print("[Mechanical Verification]")
    mech_dir = q / "mechanical"
    if not mech_dir.is_dir():
        info("No mechanical/ directory")
        return
    verify_sh = mech_dir / "verify.sh"
    if not verify_sh.is_file():
        fail("mechanical/ exists but verify.sh missing")
        return
    pass_("verify.sh exists")

    mv_log = q / "results" / "mechanical-verify.log"
    mv_exit = q / "results" / "mechanical-verify.exit"
    if mv_log.is_file() and mv_exit.is_file():
        try:
            exit_code = mv_exit.read_text(encoding="utf-8", errors="replace")
        except OSError:
            exit_code = ""
        exit_code = re.sub(r"\s", "", exit_code)
        if exit_code == "0":
            pass_("mechanical-verify.exit is 0")
        else:
            fail(f"mechanical-verify.exit is '{exit_code}', expected 0")
    else:
        fail("Verification receipt files missing")


def check_patches(q, bug_count, bug_ids, strictness):
    """Patches section (benchmark 44)."""
    print("[Patches]")
    if bug_count <= 0:
        return

    patches_dir = q / "patches"

    # Regression test file — required when bugs exist
    reg_test_file = None
    if q.is_dir():
        reg_files = sorted(q.glob("test_regression.*"))
        if reg_files:
            reg_test_file = reg_files[0]

    if reg_test_file is not None:
        pass_(f"test_regression.* exists ({bug_count} confirmed bugs require it)")
    else:
        msg = "test_regression.* missing — required when bugs exist (SKILL.md artifact contract)"
        if strictness == "benchmark":
            fail(msg)
        else:
            warn(msg)

    reg_patch_count = 0
    fix_patch_count = 0
    reg_patch_missing = 0
    for bid in bug_ids:
        if first_file_matching(patches_dir, [f"{bid}-regression*.patch"]) is not None:
            reg_patch_count += 1
        else:
            reg_patch_missing += 1
        if first_file_matching(patches_dir, [f"{bid}-fix*.patch"]) is not None:
            fix_patch_count += 1

    if reg_patch_missing == 0 and reg_patch_count > 0:
        pass_(f"{reg_patch_count} regression-test patch(es) for {bug_count} bug(s)")
    elif reg_patch_count > 0:
        fail(f"{reg_patch_missing} bug(s) missing regression-test patch")
    else:
        fail("No regression-test patches found (quality/patches/BUG-NNN-regression-test.patch required)")

    if fix_patch_count > 0:
        pass_(f"{fix_patch_count} fix patch(es)")
    else:
        warn("0 fix patches (fix patches are optional but strongly encouraged)")

    total_patches = reg_patch_count + fix_patch_count
    info(f"Total: {total_patches} patch file(s) in quality/patches/")


# Unfilled-template sentinel phrases produced by the Phase 5 writeup stub.
# Presence of any of these strings in a writeup is strong evidence that the
# template was emitted without hydrating its content fields from BUGS.md.
# See bin/run_playbook.py::phase5_prompt for the generating prompt.
_WRITEUP_TEMPLATE_SENTINELS = (
    "is a confirmed code bug in ``",
    "The affected implementation lives at ``",
    "Patch path: ``",
    "- Regression test: ``",
    "- Regression patch: ``",
)

# Matches a ```diff fenced block and captures its body for content inspection.
_WRITEUP_DIFF_BLOCK_RE = re.compile(r"```diff\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def _writeup_diff_is_non_empty(text):
    """True if any ```diff block in ``text`` contains at least one unified-diff
    line (a `+` or `-` that is not the `+++`/`---` file-header prefix)."""
    for block in _WRITEUP_DIFF_BLOCK_RE.findall(text):
        for line in block.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("+++") or stripped.startswith("---"):
                continue
            if stripped.startswith(("+", "-")):
                return True
    return False


def check_writeups(q, bug_count):
    """Bug writeups section (benchmark 30)."""
    print("[Bug Writeups]")
    if bug_count <= 0:
        return

    writeups_dir = q / "writeups"
    writeup_count = 0
    writeup_diff_count = 0
    empty_diff_writeups = []
    sentinel_writeups = []
    if writeups_dir.is_dir():
        writeup_files = sorted(p for p in writeups_dir.glob("BUG-*.md") if p.is_file())
        writeup_count = len(writeup_files)
        for wf in writeup_files:
            try:
                text = wf.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            # Presence test uses the same regex as the content test so the
            # two can never disagree on whether a fence exists. Case-insensitive
            # match accepts ```diff / ```Diff / ```DIFF uniformly — operators
            # routinely uppercase the fence tag and the gate must not silently
            # skip those writeups (the content non-emptiness check would then
            # never fire, producing a confusing "no inline fix diffs" FAIL on a
            # writeup that visibly contains a unified diff).
            if _WRITEUP_DIFF_BLOCK_RE.search(text):
                writeup_diff_count += 1
                if not _writeup_diff_is_non_empty(text):
                    empty_diff_writeups.append(wf.name)
            if any(s in text for s in _WRITEUP_TEMPLATE_SENTINELS):
                sentinel_writeups.append(wf.name)

    if writeup_count >= bug_count:
        pass_(f"{writeup_count} writeup(s) for {bug_count} bug(s)")
    elif writeup_count > 0:
        fail(f"{writeup_count} writeup(s) for {bug_count} bug(s) — all confirmed bugs require writeups (SKILL.md line 1454)")
    else:
        fail(f"No writeups for {bug_count} confirmed bug(s)")

    if writeup_count > 0:
        if writeup_diff_count >= writeup_count:
            pass_(f"All {writeup_diff_count} writeup(s) have inline fix diffs")
        elif writeup_diff_count > 0:
            fail(f"Only {writeup_diff_count}/{writeup_count} writeup(s) have inline fix diffs (all require section 6 diff)")
        else:
            fail("No writeups have inline fix diffs (section 6 'The fix' must include a ```diff block)")

        # Non-empty-diff content check. A ```diff fence with no `+`/`-` body
        # is a template stub — the legacy presence-only check let these pass.
        if empty_diff_writeups:
            preview = ", ".join(empty_diff_writeups[:5])
            suffix = f" (+{len(empty_diff_writeups) - 5} more)" if len(empty_diff_writeups) > 5 else ""
            fail(
                f"{len(empty_diff_writeups)} writeup(s) have empty ```diff blocks "
                f"(fence present, no +/- lines): {preview}{suffix}"
            )
        else:
            pass_("All writeup ```diff blocks contain unified-diff content")

        # Template-sentinel check. Any of these strings remaining in a writeup
        # means the Phase 5 stub was emitted without hydrating from BUGS.md.
        if sentinel_writeups:
            preview = ", ".join(sentinel_writeups[:5])
            suffix = f" (+{len(sentinel_writeups) - 5} more)" if len(sentinel_writeups) > 5 else ""
            fail(
                f"{len(sentinel_writeups)} writeup(s) contain unfilled template "
                f"sentinels (empty backticks after 'is a confirmed code bug in', "
                f"'The affected implementation lives at', 'Patch path:', "
                f"'Regression test:', or 'Regression patch:'): {preview}{suffix}"
            )
        else:
            pass_("No writeups contain unfilled template sentinels")


def check_version_stamps(repo_dir, q):
    """Version stamp consistency (benchmark 26). Returns detected skill_version."""
    print("[Version Stamps]")
    skill_version = detect_skill_version([
        repo_dir / "SKILL.md",
        repo_dir / ".claude" / "skills" / "quality-playbook" / "SKILL.md",
        repo_dir / ".github" / "skills" / "SKILL.md",
        repo_dir / ".github" / "skills" / "quality-playbook" / "SKILL.md",
        SCRIPT_DIR / ".." / "SKILL.md",
        SCRIPT_DIR / "SKILL.md",
    ])

    if not skill_version:
        warn("Cannot detect skill version from SKILL.md")
        return skill_version

    progress_md = q / "PROGRESS.md"
    if progress_md.is_file():
        pv = read_skill_value_line(progress_md, "Skill version:")
        if pv == skill_version:
            pass_(f"PROGRESS.md version matches ({skill_version})")
        elif pv:
            fail(f"PROGRESS.md version '{pv}' != '{skill_version}'")
        else:
            warn("PROGRESS.md missing Skill version field")

    json_path = q / "results" / "tdd-results.json"
    if json_path.is_file():
        data = load_json(json_path)
        tv = get_str(data, "skill_version")
        if tv == skill_version:
            pass_("tdd-results.json skill_version matches")
        elif tv:
            fail(f"tdd-results.json skill_version '{tv}' != '{skill_version}'")

    return skill_version


def check_cross_run_contamination(repo_dir, q, version_arg, skill_version):
    """Cross-run contamination detection."""
    print("[Cross-Run Contamination]")
    repo_name = repo_dir.name
    if skill_version and version_arg:
        matches = re.findall(r"[0-9]+\.[0-9]+\.[0-9]+", repo_name)
        dir_version = matches[-1] if matches else ""
        if dir_version and dir_version != skill_version:
            fail(f"Directory version '{dir_version}' != skill version '{skill_version}' — possible cross-run contamination")
        else:
            pass_("No version mismatch detected")

    json_path = q / "results" / "tdd-results.json"
    if json_path.is_file() and skill_version:
        data = load_json(json_path)
        json_sv = get_str(data, "skill_version")
        if json_sv and json_sv != skill_version:
            fail(f"tdd-results.json skill_version '{json_sv}' != SKILL.md '{skill_version}' — stale artifacts from prior run?")


def _check_exploration_sections(path):
    """Check that EXPLORATION.md contains all required section titles."""
    required_sections = [
        "## Open Exploration Findings",
        "## Quality Risks",
        "## Pattern Applicability Matrix",
        "## Candidate Bugs for Phase 2",
        "## Gate Self-Check",
    ]
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        fail(f"EXPLORATION.md unreadable: {exc}")
        return
    for section in required_sections:
        if section not in content:
            fail(f"EXPLORATION.md missing required section: {section!r}")


def check_run_metadata(q):
    """Validate the run-metadata sidecar JSON (run-YYYY-MM-DDTHH-MM-SS.json)."""
    print("[Run Metadata]")
    results_dir = q / "results"
    pattern = str(results_dir / "run-*.json")
    import glob as _glob
    matches = _glob.glob(pattern)
    if not matches:
        fail("run-metadata JSON missing (expected quality/results/run-YYYY-MM-DDTHH-MM-SS.json)")
        return
    if len(matches) > 1:
        warn(f"Multiple run-metadata files found: {len(matches)}")
    filename_re = re.compile(r"run-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.json$")
    for path in matches:
        if not filename_re.search(path):
            fail(f"run-metadata filename does not match expected format: {path}")
        data = load_json(Path(path))
        if data is None:
            fail(f"run-metadata JSON parse error: {path}")
            continue
        required_fields = ("schema_version", "skill_version", "project", "model", "runner", "start_time")
        for field in required_fields:
            if not data.get(field):
                fail(f"run-metadata missing or empty field: {field!r}")
    pass_("run-metadata JSON present")


# --- Per-repo entry point ---


# ---------------------------------------------------------------------------
# v1.5.1 Layer-1 mechanical invariants (schemas.md §10).
#
# Each check gracefully no-ops on pre-v1.5.1 runs (absent manifests = legacy
# repo; nothing to enforce). When the v1.5.1 artifacts are present every
# invariant below is enforced mechanically and FAILs with a specific
# <path>: <reason> message so the operator can fix the single artifact
# without re-running the whole playbook.
# ---------------------------------------------------------------------------

_V150_VALID_DISPOSITIONS = (
    "code-fix",
    "spec-fix",
    "upstream-spec-issue",
    "mis-read",
    "deferred",
)
_V150_VALID_FIX_TYPES = ("code", "spec", "both")
_V150_ILLEGAL_FIX_PAIRS = {
    ("code-fix", "spec"),
    ("spec-fix", "code"),
    ("upstream-spec-issue", "code"),
    ("mis-read", "both"),
}
_V150_SUPPORTED_EXTENSIONS = (".txt", ".md")
_V150_REQUIRED_INDEX_FIELDS = (
    "run_timestamp_start",
    "run_timestamp_end",
    "duration_seconds",
    "qpb_version",
    "target_repo_path",
    "target_repo_git_sha",
    "target_project_type",
    "phases_executed",
    "summary",
    "artifacts",
)
_V150_REQUIRED_SUMMARY_KEYS = ("requirements", "bugs", "gate_verdict")


def _v150_manifest(q, name):
    """Return the parsed top-level JSON object or None if absent/invalid."""
    path = q / name
    if not path.is_file():
        return None
    data = load_json(path)
    if isinstance(data, dict):
        return data
    fail(f"{path.name}: not a valid JSON object (schemas.md §1.6)")
    return None


def check_v1_5_0_plaintext_extensions(repo_dir):
    """§10 invariant #9 — formal_docs/ and informal_docs/ contain only .txt/.md."""
    for folder_name in ("formal_docs", "informal_docs"):
        folder = repo_dir / folder_name
        if not folder.is_dir():
            continue
        any_file = False
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            any_file = True
            if path.name == "README.md":
                continue
            if path.name.endswith(".meta.json"):
                continue
            ext = path.suffix.lower()
            if ext not in _V150_SUPPORTED_EXTENSIONS:
                rel = path.relative_to(repo_dir).as_posix()
                fail(
                    f"{rel}: unsupported extension {ext or '(none)'} under {folder_name}/ "
                    "(schemas.md §2 allows only .txt, .md; §10 invariant #9)"
                )
        if any_file:
            pass_(f"{folder_name}/: all files use supported extensions")


def check_v1_5_0_manifest_wrappers(q):
    """§10 invariant #13 — manifest wrapper shape.

    Four record-shaped manifests (formal_docs / requirements / use_cases /
    bugs) use `records`; citation_semantic_check.json uses `reviews`
    (schemas.md §9.1). Every manifest must carry schema_version +
    generated_at as non-empty strings.
    """
    record_shaped = (
        "formal_docs_manifest.json",
        "requirements_manifest.json",
        "use_cases_manifest.json",
        "bugs_manifest.json",
    )
    for name in record_shaped:
        data = _v150_manifest(q, name)
        if data is None:
            continue
        for key in ("schema_version", "generated_at"):
            if not isinstance(data.get(key), str) or not data[key]:
                fail(f"{name}: missing or empty top-level {key!r} (schemas.md §1.6)")
        if not isinstance(data.get("records"), list):
            fail(f"{name}: missing or non-array top-level 'records' (schemas.md §1.6)")
        if "reviews" in data:
            fail(
                f"{name}: has 'reviews' key — reserved for citation_semantic_check.json "
                "per schemas.md §9.1 / §10 invariant #13"
            )
        else:
            pass_(f"{name}: manifest wrapper valid")

    data = _v150_manifest(q, "citation_semantic_check.json")
    if data is not None:
        for key in ("schema_version", "generated_at"):
            if not isinstance(data.get(key), str) or not data[key]:
                fail(
                    f"citation_semantic_check.json: missing or empty top-level {key!r} "
                    "(schemas.md §1.6)"
                )
        if not isinstance(data.get("reviews"), list):
            fail(
                "citation_semantic_check.json: missing or non-array top-level 'reviews' "
                "(schemas.md §9.1 — semantic check uses 'reviews', not 'records')"
            )
        if "records" in data:
            fail(
                "citation_semantic_check.json: has 'records' key — semantic check uses "
                "'reviews' per schemas.md §9.1 / §10 invariant #13"
            )
        else:
            pass_("citation_semantic_check.json: manifest wrapper valid")


def _check_citation_block(repo_dir, req_id, citation, formal_docs_by_path, req_tier):
    excerpt = citation.get("citation_excerpt")
    if not isinstance(excerpt, str) or not excerpt:
        fail(
            "requirements_manifest.json",
            f"record_id={req_id}: citation has empty or missing citation_excerpt "
            "(schemas.md §10 invariant #4)",
        )
        return
    doc_path_str = citation.get("document")
    if not isinstance(doc_path_str, str) or not doc_path_str:
        fail(
            "requirements_manifest.json",
            f"record_id={req_id}: citation missing 'document' field",
        )
        return
    section = citation.get("section")
    line = citation.get("line")
    has_section = isinstance(section, str) and section.strip()
    has_line = isinstance(line, int) and not isinstance(line, bool)
    if not has_section and not has_line:
        fail(
            "requirements_manifest.json",
            f"record_id={req_id}: citation has no section or line locator "
            "(page alone is insufficient; schemas.md §10 invariant #4)",
        )
        return

    fd_rec = formal_docs_by_path.get(doc_path_str)
    if fd_rec is None:
        fail(
            "requirements_manifest.json",
            f"record_id={req_id}: citation document {doc_path_str!r} "
            "not in formal_docs_manifest.json (schemas.md §10 invariant #2)",
        )
        return
    fd_tier = fd_rec.get("tier")
    if fd_tier != req_tier:
        fail(
            "requirements_manifest.json",
            f"record_id={req_id}: tier={req_tier} does not match cited FORMAL_DOC "
            f"tier={fd_tier!r} (schemas.md §10 invariant #14)",
        )
    fd_sha = fd_rec.get("document_sha256")
    cite_sha = citation.get("document_sha256")
    if isinstance(fd_sha, str) and isinstance(cite_sha, str) and fd_sha != cite_sha:
        fail(
            "requirements_manifest.json",
            f"record_id={req_id}: citation.document_sha256 does not match FORMAL_DOC "
            "(schemas.md §10 invariant #3 — citation_stale)",
        )

    if _CITATION_VERIFIER is None:
        warn(
            f"requirements_manifest.json: record_id={req_id}: byte-equality skipped — "
            "bin/citation_verifier unavailable on this install"
        )
        return

    doc_path = repo_dir / doc_path_str
    if not doc_path.is_file():
        fail(
            "requirements_manifest.json",
            f"record_id={req_id}: citation document not on disk: {doc_path_str}",
        )
        return
    try:
        bytes_ = doc_path.read_bytes()
        fresh = _CITATION_VERIFIER.extract_excerpt(
            bytes_, doc_path.suffix.lower(), section if has_section else None,
            line if has_line else None,
        )
    except _CITATION_VERIFIER.CitationResolutionError as exc:
        fail(
            "requirements_manifest.json",
            f"record_id={req_id}: citation location does not resolve in "
            f"{doc_path_str}: {exc.message} (schemas.md §10 invariant #4)",
        )
        return
    except Exception as exc:  # noqa: BLE001 — fail with a real message
        fail(
            "requirements_manifest.json",
            f"record_id={req_id}: citation verifier errored: {exc}",
        )
        return

    if fresh != excerpt:
        fail(
            "requirements_manifest.json",
            f"record_id={req_id}: citation_excerpt is not byte-equal to fresh "
            f"extraction from {doc_path_str} "
            "(schemas.md §10 invariant #11 — Layer-1 anti-hallucination)",
        )


def check_v1_5_0_requirements_manifest(repo_dir, q):
    """§10 invariants #1, #4, #8, #11, #14 — REQ shape, citation gating, functional_section."""
    req_data = _v150_manifest(q, "requirements_manifest.json")
    if req_data is None:
        return
    records = req_data.get("records")
    if not isinstance(records, list):
        return  # wrapper check already reported
    fd_data = _v150_manifest(q, "formal_docs_manifest.json")
    formal_docs_by_path = {}
    if fd_data and isinstance(fd_data.get("records"), list):
        for rec in fd_data["records"]:
            if isinstance(rec, dict) and isinstance(rec.get("source_path"), str):
                formal_docs_by_path[rec["source_path"]] = rec

    for idx, rec in enumerate(records):
        if not isinstance(rec, dict):
            fail(
                "requirements_manifest.json",
                f"record_id=<#{idx}>: not a JSON object",
            )
            continue
        req_id = rec.get("id", f"<#{idx}>")

        fs = rec.get("functional_section")
        if not isinstance(fs, str) or not fs.strip():
            fail(
                "requirements_manifest.json",
                f"record_id={req_id}: has empty or missing functional_section "
                "(schemas.md §10 invariant #8)",
            )

        tier = rec.get("tier")
        citation = rec.get("citation")
        if tier in (1, 2):
            if not isinstance(citation, dict):
                fail(
                    "requirements_manifest.json",
                    f"record_id={req_id}: is tier {tier} but has no citation block "
                    "(schemas.md §10 invariant #1)",
                )
                continue
            _check_citation_block(repo_dir, req_id, citation, formal_docs_by_path, tier)
        elif tier in (3, 4, 5):
            if citation is not None:
                fail(
                    "requirements_manifest.json",
                    f"record_id={req_id}: is tier {tier} but carries a citation block "
                    "(citations are for Tier 1/2 only per schemas.md §10 invariant #1)",
                )
        elif tier is None:
            fail(
                "requirements_manifest.json",
                f"record_id={req_id}: missing 'tier' field",
            )
        else:
            fail(
                "requirements_manifest.json",
                f"record_id={req_id}: has invalid tier {tier!r} (expected integer 1–5)",
            )

        # v1.5.2: validate the optional `pattern` field on the REQ record.
        pattern = rec.get("pattern")
        if pattern is not None and pattern not in VALID_PATTERN_VALUES:
            fail(
                "requirements_manifest.json",
                f"record_id={req_id}: has invalid pattern {pattern!r} "
                f"(expected one of {sorted(VALID_PATTERN_VALUES)})",
            )

    pass_("requirements_manifest.json: v1.5.1 Layer-1 REQ checks complete")


def check_v1_5_0_bugs_manifest(q):
    """§10 invariants #7, #12 — disposition completeness + legal fix_type × disposition."""
    data = _v150_manifest(q, "bugs_manifest.json")
    if data is None:
        return
    records = data.get("records")
    if not isinstance(records, list):
        return
    for idx, rec in enumerate(records):
        if not isinstance(rec, dict):
            continue
        bug_id = rec.get("id", f"<#{idx}>")
        disp = rec.get("disposition")
        if disp not in _V150_VALID_DISPOSITIONS:
            fail(
                "bugs_manifest.json",
                f"record_id={bug_id}: has invalid or missing disposition {disp!r} "
                f"(schemas.md §10 invariant #7, valid: "
                f"{', '.join(_V150_VALID_DISPOSITIONS)})",
            )
            continue
        rationale = rec.get("disposition_rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            fail(
                "bugs_manifest.json",
                f"record_id={bug_id}: has empty or missing disposition_rationale "
                "(schemas.md §10 invariant #7)",
            )
        ft = rec.get("fix_type")
        if ft not in _V150_VALID_FIX_TYPES:
            fail(
                "bugs_manifest.json",
                f"record_id={bug_id}: has invalid or missing fix_type {ft!r}",
            )
            continue
        if (disp, ft) in _V150_ILLEGAL_FIX_PAIRS:
            fail(
                "bugs_manifest.json",
                f"record_id={bug_id}: illegal disposition × fix_type combination "
                f"({disp}, {ft}) per schemas.md §3.4 / §10 invariant #12",
            )

    pass_("bugs_manifest.json: v1.5.1 Layer-1 BUG checks complete")


def check_v1_5_0_index_md(q):
    """§10 invariant #10 — quality/INDEX.md exists with all §11 required fields."""
    path = q / "INDEX.md"
    v150_artifacts = (
        "formal_docs_manifest.json",
        "requirements_manifest.json",
        "use_cases_manifest.json",
        "bugs_manifest.json",
        "citation_semantic_check.json",
    )
    is_v150_run = any((q / name).is_file() for name in v150_artifacts)
    if not path.is_file():
        if is_v150_run:
            fail(
                "quality/INDEX.md does not exist (required on every v1.5.1 run per "
                "schemas.md §10 invariant #10)"
            )
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
    if not match:
        fail("quality/INDEX.md: no fenced JSON block found (schemas.md §11)")
        return
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        fail(f"quality/INDEX.md: fenced JSON block invalid: {exc}")
        return
    if not isinstance(payload, dict):
        fail("quality/INDEX.md: fenced JSON block is not a JSON object")
        return
    for key in _V150_REQUIRED_INDEX_FIELDS:
        if key not in payload:
            fail(f"quality/INDEX.md: missing required field {key!r} (schemas.md §11)")
            continue
        val = payload[key]
        if isinstance(val, str) and not val:
            fail(f"quality/INDEX.md: field {key!r} is empty string (schemas.md §11)")
    summary = payload.get("summary")
    if isinstance(summary, dict):
        for sub in _V150_REQUIRED_SUMMARY_KEYS:
            if sub not in summary:
                fail(
                    f"quality/INDEX.md: summary missing {sub!r} sub-key "
                    "(schemas.md §11)"
                )
    pass_("quality/INDEX.md: §11 fields present")


_V150_VALID_VERDICTS = ("supports", "overreaches", "unclear")


def check_v1_5_0_semantic_check(q):
    """§10 invariant #17 — Council-of-Three majority-overreaches rule.

    Layer-2 semantic check (Phase 6). Gate does NOT re-run the semantic
    review; it parses quality/citation_semantic_check.json and applies
    the majority-overreaches rule:

      - ≥2 of 3 `overreaches` for the same Tier 1/2 REQ → FAIL.
      - isolated 1/3 `overreaches` or `unclear` → WARN.
      - <3 reviews for any Tier 1/2 REQ → FAIL (schemas.md §9.4).
      - review entry for a Tier 3/4/5 REQ → FAIL (only Tier 1/2 are
        semantically reviewable since they carry citations).

    When requirements_manifest.json has zero Tier 1/2 REQs the
    citation_semantic_check.json file is still expected (emitted with
    empty reviews[]); its absence in that case warns rather than
    fails to avoid breaking Spec Gap runs.
    """
    req_data = _v150_manifest(q, "requirements_manifest.json")
    tier_by_req = {}
    if req_data and isinstance(req_data.get("records"), list):
        for rec in req_data["records"]:
            if isinstance(rec, dict):
                rid = rec.get("id")
                tier = rec.get("tier")
                if isinstance(rid, str) and isinstance(tier, int) and not isinstance(tier, bool):
                    tier_by_req[rid] = tier
    tier_12_req_ids = {rid for rid, t in tier_by_req.items() if t in (1, 2)}

    sc_path = q / "citation_semantic_check.json"
    if not sc_path.is_file():
        if tier_12_req_ids:
            fail(
                "quality/citation_semantic_check.json",
                "file missing (schemas.md §10 invariant #17 requires a semantic "
                "check for every Tier 1/2 REQ)",
            )
        else:
            # Spec Gap: no Tier 1/2 REQs to review. File is expected but its
            # absence doesn't break the invariant since there's nothing to
            # enforce. Warn so the orchestrator knows to emit the empty file.
            warn(
                "quality/citation_semantic_check.json: file missing; no Tier 1/2 "
                "REQs present so invariant #17 has nothing to enforce — emit an "
                "empty reviews[] for contract completeness"
            )
        return

    data = _v150_manifest(q, "citation_semantic_check.json")
    if data is None:
        return  # wrapper check already reported the failure
    reviews = data.get("reviews")
    if not isinstance(reviews, list):
        return  # wrapper check already reported

    by_req = {}
    seen_reviewers = {}
    for idx, entry in enumerate(reviews):
        if not isinstance(entry, dict):
            fail(
                "citation_semantic_check.json",
                f"reviews[#{idx}]: not a JSON object",
            )
            continue
        rid = entry.get("req_id")
        reviewer = entry.get("reviewer")
        verdict = entry.get("verdict")
        notes = entry.get("notes")
        if not isinstance(rid, str) or not rid:
            fail(
                "citation_semantic_check.json",
                f"reviews[#{idx}]: missing or non-string req_id",
            )
            continue
        if not isinstance(reviewer, str) or not reviewer:
            fail(
                "citation_semantic_check.json",
                f"record_id={rid}: missing or non-string reviewer",
            )
            continue
        if verdict not in _V150_VALID_VERDICTS:
            fail(
                "citation_semantic_check.json",
                f"record_id={rid}: reviewer={reviewer!r} invalid verdict "
                f"{verdict!r}; expected one of {_V150_VALID_VERDICTS}",
            )
            continue
        if not isinstance(notes, str):
            fail(
                "citation_semantic_check.json",
                f"record_id={rid}: reviewer={reviewer!r} notes must be a string",
            )
            continue
        # §9.4 common-mistake: tier check — review entries must belong to
        # Tier 1/2 REQs only.
        tier = tier_by_req.get(rid)
        if tier is None:
            fail(
                "citation_semantic_check.json",
                f"record_id={rid}: reviewer={reviewer!r} reviews a REQ that does "
                "not exist in requirements_manifest.json",
            )
            continue
        if tier not in (1, 2):
            fail(
                "citation_semantic_check.json",
                f"record_id={rid}: reviewer={reviewer!r} reviews a tier-{tier} "
                "REQ; semantic check applies to Tier 1/2 only (schemas.md §9.4)",
            )
            continue
        # Detect duplicate (req_id, reviewer) pairs — a typo that would slip a
        # vote past the majority computation.
        pair_key = seen_reviewers.setdefault(rid, set())
        if reviewer in pair_key:
            fail(
                "citation_semantic_check.json",
                f"record_id={rid}: duplicate review from reviewer={reviewer!r}",
            )
            continue
        pair_key.add(reviewer)
        by_req.setdefault(rid, []).append(entry)

    # §9.4: every Tier 1/2 REQ needs at least 3 reviews.
    for rid in sorted(tier_12_req_ids):
        entries = by_req.get(rid, [])
        if len(entries) < 3:
            fail(
                "citation_semantic_check.json",
                f"record_id={rid}: fewer than 3 reviews ({len(entries)} present) "
                "— schemas.md §9.4 requires one entry per council member for "
                "every Tier 1/2 REQ",
            )
            continue
        overreach_count = sum(1 for e in entries if e.get("verdict") == "overreaches")
        unclear_count = sum(1 for e in entries if e.get("verdict") == "unclear")
        if overreach_count >= 2:
            reviewers_flagged = ", ".join(
                sorted(
                    str(e.get("reviewer"))
                    for e in entries
                    if e.get("verdict") == "overreaches"
                )
            )
            fail(
                "citation_semantic_check.json",
                f"record_id={rid}: semantic check majority overreaches "
                f"({overreach_count}/{len(entries)} reviewers flagged: "
                f"{reviewers_flagged}) — schemas.md §10 invariant #17",
            )
        elif overreach_count == 1:
            flagged = next(
                str(e.get("reviewer"))
                for e in entries
                if e.get("verdict") == "overreaches"
            )
            warn(
                f"citation_semantic_check.json: record_id={rid}: 1/{len(entries)} "
                f"reviewer ({flagged}) flagged as `overreaches` — surfaced for "
                "human review; not a gate failure unless ≥2 agree"
            )
        if unclear_count >= 1 and overreach_count == 0:
            flagged = ", ".join(
                sorted(
                    str(e.get("reviewer"))
                    for e in entries
                    if e.get("verdict") == "unclear"
                )
            )
            warn(
                f"citation_semantic_check.json: record_id={rid}: "
                f"{unclear_count}/{len(entries)} reviewer(s) flagged as "
                f"`unclear` ({flagged}) — surfaced for human review"
            )

    if not tier_12_req_ids:
        pass_(
            "citation_semantic_check.json: no Tier 1/2 REQs to review "
            "(invariant #17 vacuously satisfied)"
        )
    else:
        pass_(
            f"citation_semantic_check.json: §10 invariant #17 checks complete "
            f"for {len(tier_12_req_ids)} Tier 1/2 REQ(s)"
        )


# --- v1.5.1 Item 5.2: challenge-gate coverage invariant -------------------

# Canonical verdict-line regex from Impl-Plan Item 5.2. Matches a top-level
# "**Verdict:** CONFIRMED/DOWNGRADED/REJECTED" line as a stand-alone line.
_CHALLENGE_VERDICT_RE = re.compile(
    r"^\*\*Verdict:\*\*\s+(CONFIRMED|DOWNGRADED|REJECTED)\s*$",
    re.MULTILINE,
)
# Legacy final-verdict form used by challenge records generated before the
# canonical regex was specified (including the preserved virtio-1.4.6
# evidence at repos/benchmark-1.5.0/virtio-1.4.6/quality/challenge/).
# The briefing says "this invariant only verifies the challenge ran" — the
# legacy form unambiguously records a final verdict, so it satisfies the
# invariant's intent without requiring operators to regenerate baseline
# artifacts. New v1.5.1+ runs should prefer the canonical form.
_CHALLENGE_VERDICT_LEGACY_RE = re.compile(
    r"^\*\*(CONFIRMED|DOWNGRADED|REJECTED)\.?\*\*",
    re.MULTILINE,
)

# Trigger-pattern keyword tables (case-insensitive substring matching).
_CHALLENGE_SECURITY_SEVERITIES = frozenset({"CRITICAL", "HIGH"})
_CHALLENGE_SECURITY_KEYWORDS = (
    "credential", "secret", "auth", "injection", "xss", "csrf",
    "ssrf", "privilege", "bypass", "leak",
)
_CHALLENGE_SIBLING_KEYWORDS = (
    "sibling", "parallel", "parity", "contrasted with", "same concern",
    "in contrast", "other path", "other branch",
)
_CHALLENGE_MISSING_KEYWORDS = (
    "never", "does not", "doesn't", "missing", "absent", "fails to",
)
_CHALLENGE_DESIGN_KEYWORDS = (
    "todo", "why", "ooda", "design decision",
)
_CHALLENGE_ITERATION_KEYWORDS = (
    "gap", "unfiltered", "parity", "adversarial", "iteration",
)


def _bug_writeup_text(q, bug_id):
    """Return lowercased writeup text for ``bug_id`` (empty string if absent).

    Writeups live at quality/writeups/BUG-NNN.md. Reading failures are
    treated as empty text — the invariant still runs on the manifest fields
    (title / summary / source) which are present independently.
    """
    path = q / "writeups" / f"{bug_id}.md"
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return ""


def _bug_req_has_tier_12_citation(req_id, requirements_records):
    """True iff req_id resolves to a REQ with a non-empty citation and
    tier in {1, 2}. Used by the "No spec basis" trigger pattern."""
    if not req_id or not isinstance(requirements_records, list):
        return False
    for rec in requirements_records:
        if not isinstance(rec, dict):
            continue
        if rec.get("id") != req_id:
            continue
        if rec.get("tier") not in (1, 2):
            return False
        citation = rec.get("citation")
        if isinstance(citation, dict) and citation:
            return True
        return False
    return False


def _contains_any(text, keywords):
    """Case-insensitive substring OR across a keyword tuple."""
    if not text:
        return False
    lowered = text.lower()
    return any(kw in lowered for kw in keywords)


def _classify_bug_triggers(rec, q, requirements_records):
    """Return the list of trigger-pattern names that fired for one bug.
    Empty list means the bug does not require a challenge record.

    Patterns mirror Impl-Plan Item 5.2 verbatim. Input aliasing:
      - title: prefers rec['title'], falls back to rec['summary'].
      - requirement: prefers rec['requirement'], falls back to rec['req_id']
        (v1.4.x uses req_id; v1.5.1+ converges on requirement).
      - source_comments: optional, older runs may omit it.
      - source / discovery_phase: substring-matched against the
        iteration-derived keyword list.
    """
    fired = []

    bug_id = rec.get("id", "")
    title = rec.get("title") or rec.get("summary") or ""
    severity = (rec.get("severity") or "").upper()
    writeup = _bug_writeup_text(q, bug_id) if bug_id else ""
    title_plus_writeup = f"{title}\n{writeup}"

    # 1. Security-class.
    if severity in _CHALLENGE_SECURITY_SEVERITIES and _contains_any(
        title_plus_writeup, _CHALLENGE_SECURITY_KEYWORDS
    ):
        fired.append("security-class")

    # 2. No spec basis.
    requirement = rec.get("requirement") or rec.get("req_id")
    has_valid_citation = _bug_req_has_tier_12_citation(requirement, requirements_records)
    if not requirement or not has_valid_citation:
        fired.append("no-spec-basis")

    # 3. Sibling-path divergence.
    if _contains_any(writeup, _CHALLENGE_SIBLING_KEYWORDS):
        fired.append("sibling-path-divergence")

    # 4. Missing functionality.
    if _contains_any(writeup, _CHALLENGE_MISSING_KEYWORDS):
        fired.append("missing-functionality")

    # 5. Design-decision comment (optional field).
    source_comments = rec.get("source_comments")
    if isinstance(source_comments, str) and _contains_any(
        source_comments, _CHALLENGE_DESIGN_KEYWORDS
    ):
        fired.append("design-decision-comment")

    # 6. Iteration-derived.
    source = rec.get("source") or ""
    discovery_phase = rec.get("discovery_phase") or ""
    iter_haystack = f"{source}\n{discovery_phase}"
    if _contains_any(iter_haystack, _CHALLENGE_ITERATION_KEYWORDS):
        fired.append("iteration-derived")

    return fired


def _challenge_record_has_verdict(path):
    """True iff the file exists and contains either the canonical or
    legacy verdict line per the invariant's accept set."""
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    if _CHALLENGE_VERDICT_RE.search(text):
        return True
    if _CHALLENGE_VERDICT_LEGACY_RE.search(text):
        return True
    return False


def check_challenge_gate_coverage(q):
    """v1.5.1 Item 5.2 — every bug whose fingerprints trigger the challenge
    gate must have a quality/challenge/BUG-NNN-challenge.md with a valid
    verdict line.

    N/A when quality/bugs_manifest.json is absent (zero-bug runs can't
    have un-challenged bugs). Runs on the current quality/ tree only;
    no cross-run state.
    """
    data = _v150_manifest(q, "bugs_manifest.json")
    if data is None:
        # N/A — the plan explicitly says "invariant is N/A if the file is
        # absent". Consistent with other quality_gate invariants that silently
        # skip when their input isn't present.
        return
    records = data.get("records")
    if not isinstance(records, list):
        return

    reqs_data = _v150_manifest(q, "requirements_manifest.json") or {}
    req_records = reqs_data.get("records") if isinstance(reqs_data, dict) else None

    challenge_dir = q / "challenge"
    triggered = 0
    missing = []   # list of (bug_id, [pattern names]) for bugs with no record
    bad_verdict = []  # list of (bug_id, [pattern names]) for record w/o verdict

    for rec in records:
        if not isinstance(rec, dict):
            continue
        bug_id = rec.get("id")
        if not bug_id:
            continue
        fired = _classify_bug_triggers(rec, q, req_records)
        if not fired:
            continue
        triggered += 1
        record_path = challenge_dir / f"{bug_id}-challenge.md"
        if not record_path.is_file():
            missing.append((bug_id, fired))
        elif not _challenge_record_has_verdict(record_path):
            bad_verdict.append((bug_id, fired))

    if missing:
        for bug_id, fired in missing:
            fail(
                "quality/challenge/",
                f"{bug_id}: challenge record missing (triggered by: {', '.join(fired)}) "
                f"— expected {bug_id}-challenge.md with a **Verdict:** line",
            )
    if bad_verdict:
        for bug_id, fired in bad_verdict:
            fail(
                f"quality/challenge/{bug_id}-challenge.md",
                f"missing or malformed verdict line (triggered by: {', '.join(fired)}) "
                "— expected a line matching `^\\*\\*Verdict:\\*\\*\\s+(CONFIRMED|DOWNGRADED|REJECTED)` "
                "or the legacy final-verdict form",
            )

    if triggered == 0:
        pass_("challenge gate coverage: no bug triggered the challenge gate (vacuous)")
    elif not missing and not bad_verdict:
        pass_(
            f"challenge gate coverage: {triggered} triggered bug(s) all have valid "
            "challenge records"
        )


def check_v1_5_2_cardinality_gate(repo_dir):
    """v1.5.2 Lever 3: Phase 5 cardinality reconciliation gate.

    Surfaces every failure from validate_cardinality_gate() as a fail() entry.
    """
    failures = validate_cardinality_gate(repo_dir)
    if not failures:
        pass_("compensation_grid.json: v1.5.2 cardinality gate clean")
        return
    for msg in failures:
        fail("compensation_grid.json", msg)


def check_v1_5_0_gate_invariants(repo_dir, q):
    """Dispatcher that runs every Layer-1 mechanical check from schemas.md §10."""
    check_v1_5_0_plaintext_extensions(repo_dir)
    check_v1_5_0_manifest_wrappers(q)
    check_v1_5_0_requirements_manifest(repo_dir, q)
    check_v1_5_0_bugs_manifest(q)
    check_v1_5_0_index_md(q)
    # Phase 6 invariant #17 runs after requirements_manifest so it sees
    # shape-validated REQ records.
    check_v1_5_0_semantic_check(q)
    # v1.5.1 Item 5.2: challenge-gate coverage runs last. It depends on
    # requirements_manifest.json for the "No spec basis" pattern but
    # does not redo schema checks that the prior invariants already cover.
    check_challenge_gate_coverage(q)
    # v1.5.2 Lever 3: cardinality reconciliation gate.
    check_v1_5_2_cardinality_gate(repo_dir)


def check_repo(repo_dir, version_arg, strictness):
    """Run all checks for one repo. Writes output via pass_/fail_/warn/info."""
    repo_dir = Path(repo_dir)
    if str(repo_dir) == ".":
        repo_dir = Path.cwd()
    repo_name = repo_dir.name
    q = repo_dir / "quality"

    print("")
    print(f"=== {repo_name} ===")

    check_file_existence(repo_dir, q, strictness)
    bug_count, bug_ids = check_bugs_heading(q)
    tdd_data = check_tdd_sidecar(q, bug_count)
    check_tdd_logs(q, bug_count, bug_ids, tdd_data)
    check_integration_sidecar(q, strictness)
    check_recheck_sidecar(q)
    check_use_cases(repo_dir, q, strictness)
    check_test_file_extension(repo_dir, q)
    check_terminal_gate(q)
    check_mechanical(q)
    check_patches(q, bug_count, bug_ids, strictness)
    check_writeups(q, bug_count)
    skill_version = check_version_stamps(repo_dir, q)
    check_cross_run_contamination(repo_dir, q, version_arg, skill_version)
    check_run_metadata(q)
    check_v1_5_0_gate_invariants(repo_dir, q)

    print("")


# --- Main ---


def main(argv=None):
    _reset_counters()
    if argv is None:
        argv = sys.argv[1:]

    repo_dirs = []
    version = ""
    check_all = False
    strictness = "benchmark"

    expect_version = False
    for arg in argv:
        if expect_version:
            version = arg
            expect_version = False
            continue
        if arg == "--version":
            expect_version = True
        elif arg == "--all":
            check_all = True
        elif arg == "--benchmark":
            strictness = "benchmark"
        elif arg == "--general":
            strictness = "general"
        else:
            repo_dirs.append(arg)

    if not version:
        version = detect_skill_version([
            SCRIPT_DIR / ".." / "SKILL.md",
            SCRIPT_DIR / "SKILL.md",
            Path("SKILL.md"),
            Path(".claude") / "skills" / "quality-playbook" / "SKILL.md",
            Path(".github") / "skills" / "SKILL.md",
            Path(".github") / "skills" / "quality-playbook" / "SKILL.md",
        ])

    # Resolve repos
    if check_all:
        for entry in sorted(SCRIPT_DIR.glob(f"*-{version}")):
            if (entry / "quality").is_dir():
                repo_dirs.append(str(entry))
    elif len(repo_dirs) == 1 and repo_dirs[0] == ".":
        repo_dirs = [str(Path.cwd())]
    else:
        resolved = []
        for name in repo_dirs:
            p = Path(name)
            if (p / "quality").is_dir():
                resolved.append(name)
            elif (SCRIPT_DIR / f"{name}-{version}").is_dir():
                resolved.append(str(SCRIPT_DIR / f"{name}-{version}"))
            elif (SCRIPT_DIR / name).is_dir():
                resolved.append(str(SCRIPT_DIR / name))
            else:
                print(f"WARNING: Cannot find repo '{name}'")
        repo_dirs = resolved

    if not repo_dirs:
        print(f"Usage: {sys.argv[0]} [--version V] [--all | repo1 repo2 ... | .]")
        return 1

    print("=== Quality Gate — Post-Run Validation ===")
    print(f"Version:    {version or 'unknown'}")
    print(f"Strictness: {strictness}")
    print(f"Repos:      {len(repo_dirs)}")

    for rd in repo_dirs:
        check_repo(rd, version, strictness)

    print("")
    print("===========================================")
    print(f"Total: {FAIL} FAIL, {WARN} WARN")
    if FAIL > 0:
        print(f"RESULT: GATE FAILED — {FAIL} check(s) must be fixed")
        return 1
    else:
        print("RESULT: GATE PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
