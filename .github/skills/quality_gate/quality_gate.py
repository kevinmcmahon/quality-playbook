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

# Global counters — reset per invocation via main(). Tests that call check_repo
# directly should reset these in setUp.
FAIL = 0
WARN = 0


def _reset_counters():
    global FAIL, WARN
    FAIL = 0
    WARN = 0


def fail(msg):
    global FAIL
    print(f"  FAIL: {msg}")
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
    func_test = first_file_matching(q, ["test_functional.*"])
    reg_test = first_file_matching(q, ["test_regression.*"])

    if func_test is None:
        warn("No test_functional.* found")
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
        pass_(f"test_functional.{ext} matches project language ({detected_lang})")
    else:
        fail(f"test_functional.{ext} does not match project language ({detected_lang}) — expected .{primary}")

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


def check_writeups(q, bug_count):
    """Bug writeups section (benchmark 30)."""
    print("[Bug Writeups]")
    if bug_count <= 0:
        return

    writeups_dir = q / "writeups"
    writeup_count = 0
    writeup_diff_count = 0
    if writeups_dir.is_dir():
        writeup_files = sorted(p for p in writeups_dir.glob("BUG-*.md") if p.is_file())
        writeup_count = len(writeup_files)
        for wf in writeup_files:
            if file_contains(wf, r"```diff"):
                writeup_diff_count += 1

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
