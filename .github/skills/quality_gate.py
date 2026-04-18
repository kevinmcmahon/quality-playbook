#!/usr/bin/env python3
"""quality_gate.py — Python port of quality_gate.sh.

**CANDIDATE — NOT A REPLACEMENT YET.** The bash version (quality_gate.sh) remains
the authoritative source of truth. Per ai_context/DEVELOPMENT_CONTEXT.md, full
replacement requires validation across the 10 benchmark repos:
chi, cobra, httpx, pydantic, javalin, gson, express, axum, serde, zod.

This script must produce byte-identical stdout to quality_gate.sh for the same
inputs. If you change this file, run both against the same quality/ directory
and diff their stdout — the diff must be empty before committing.

Runs on Python 3.8+ with only the standard library (no pip dependencies).

Usage:
    ./quality_gate.py .                          # Check current directory (benchmark mode)
    ./quality_gate.py --general .                # Check with relaxed thresholds
    ./quality_gate.py virtio                     # Check named repo (from repos/)
    ./quality_gate.py --all                      # Check all current-version repos
    ./quality_gate.py --version 1.3.27 virtio    # Check specific version

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

import os
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FAIL = 0
WARN = 0

# --- Counters and report helpers ---

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

# --- JSON grep-style helpers (match bash semantics, not real JSON parsing) ---

def json_has_key(path, key):
    """Return True if any line in file matches `"key"\\s*:`."""
    if not path.exists():
        return False
    pat = re.compile(rf'"{re.escape(key)}"\s*:')
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if pat.search(line):
                    return True
    except OSError:
        pass
    return False

def json_str_val(path, key):
    """Extract first quoted string value for key.

    Returns empty string if key absent, '__NOT_STRING__' if key exists but value
    is not a quoted string. Mirrors bash json_str_val semantics.
    """
    if not path.exists():
        return ""
    quoted_pat = re.compile(rf'"{re.escape(key)}"\s*:\s*"([^"]*)"')
    key_pat = re.compile(rf'"{re.escape(key)}"\s*:')
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    # Process line by line to match grep | head -1 behavior
    for line in content.splitlines():
        m = quoted_pat.search(line)
        if m:
            return m.group(1)
    for line in content.splitlines():
        if key_pat.search(line):
            return "__NOT_STRING__"
    return ""

def json_key_count(path, key):
    """Count LINES (not matches) containing `"key"\\s*:` — matches `grep -c` semantics."""
    if not path.exists():
        return 0
    pat = re.compile(rf'"{re.escape(key)}"\s*:')
    count = 0
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if pat.search(line):
                    count += 1
    except OSError:
        return 0
    return count

# --- File/dir helpers ---

def has_file_matching(directory, patterns):
    """True if any file in `directory` (non-recursive) matches any glob pattern.

    Mirrors `find DIR -maxdepth 1 \\( -name PAT1 -o -name PAT2 ... \\) -print -quit`.
    """
    if not directory.is_dir():
        return False
    for pat in patterns:
        for _ in directory.glob(pat):
            return True
    return False

def count_files_matching(directory, pattern):
    """Count files in `directory` (non-recursive) matching glob pattern.

    Mirrors `find DIR -maxdepth 1 -name PAT | wc -l`.
    """
    if not directory.is_dir():
        return 0
    return sum(1 for _ in directory.glob(pattern))

def first_file_matching(directory, patterns):
    """Return first matching path or None. Mirrors `find -name PAT -print -quit`."""
    if not directory.is_dir():
        return None
    for pat in patterns:
        for p in directory.glob(pat):
            return p
    return None

def file_contains(path, pattern):
    """True if any line in file matches pattern (compiled regex or string)."""
    if not path.exists():
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
    """Return first line with all whitespace stripped (tr -d '[:space:]')."""
    if not path.exists():
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            line = f.readline()
    except OSError:
        return ""
    return re.sub(r"\s", "", line)

# --- Main per-repo check ---

def check_repo(repo_dir, version_arg, strictness):
    """Run all checks for one repo. Mirrors bash check_repo() verbatim."""
    repo_dir = Path(repo_dir)
    if str(repo_dir) == ".":
        repo_dir = Path.cwd()
    repo_name = repo_dir.name
    q = repo_dir / "quality"

    print("")
    print(f"=== {repo_name} ===")

    # --- File existence (benchmark 40) ---
    print("[File Existence]")
    for f in ["BUGS.md", "REQUIREMENTS.md", "QUALITY.md", "PROGRESS.md",
              "COVERAGE_MATRIX.md", "COMPLETENESS_REPORT.md"]:
        if (q / f).is_file():
            pass_(f"{f} exists")
        else:
            fail(f"{f} missing")

    # Additional required artifacts
    for f in ["CONTRACTS.md", "RUN_CODE_REVIEW.md", "RUN_SPEC_AUDIT.md",
              "RUN_INTEGRATION_TESTS.md", "RUN_TDD_TESTS.md"]:
        if (q / f).is_file():
            pass_(f"{f} exists")
        else:
            fail(f"{f} missing")

    # Functional test file — any naming pattern
    if has_file_matching(q, ["test_functional.*", "FunctionalSpec.*",
                             "FunctionalTest.*", "functional.test.*"]):
        pass_("functional test file exists")
    else:
        fail("functional test file missing (test_functional.*, FunctionalSpec.*, FunctionalTest.*, functional.test.*)")

    # AGENTS.md at project root
    if (repo_dir / "AGENTS.md").is_file():
        pass_("AGENTS.md exists")
    else:
        fail("AGENTS.md missing (required at project root)")

    # EXPLORATION.md
    if (q / "EXPLORATION.md").is_file():
        pass_("EXPLORATION.md exists")
    else:
        fail("EXPLORATION.md missing")

    # Code reviews dir
    cr_dir = q / "code_reviews"
    if cr_dir.is_dir() and has_file_matching(cr_dir, ["*.md"]):
        pass_("code_reviews/ has .md files")
    else:
        fail("code_reviews/ missing or empty")

    # Spec audits
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

        # Triage executable evidence
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

    # --- BUGS.md heading format (benchmark 39) ---
    print("[BUGS.md Heading Format]")
    bug_count = 0
    bugs_md = q / "BUGS.md"
    if bugs_md.is_file():
        try:
            bugs_content = bugs_md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            bugs_content = ""
        lines = bugs_content.splitlines()

        correct_headings = sum(1 for ln in lines if re.match(r'^### BUG-([HML]|[0-9])[0-9]*', ln))
        # wrong_headings: lines matching ^## BUG- but NOT ^### BUG-
        # bash: grep -E '^## BUG-' | grep -cvE '^### BUG-'
        # This counts lines with ^## BUG- that don't ALSO start with ^### BUG-
        # Since a line starting with ^### BUG- also starts with ^## BUG- (## is prefix of ###),
        # we need lines that start with ^## BUG- but not ^### BUG-
        wrong_headings = sum(1 for ln in lines
                             if re.match(r'^## BUG-', ln) and not re.match(r'^### BUG-', ln))
        deep_headings = sum(1 for ln in lines if re.match(r'^#{4,} BUG-([HML]|[0-9])', ln))
        bold_headings = sum(1 for ln in lines if re.match(r'^\*\*BUG-([HML]|[0-9])', ln))
        bullet_headings = sum(1 for ln in lines if re.match(r'^- BUG-([HML]|[0-9])', ln))

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
                if re.search(r'(No confirmed|zero|0 confirmed)', bugs_content):
                    pass_("Zero-bug run — no headings expected")
                else:
                    bug_count = wrong_headings + deep_headings + bold_headings + bullet_headings
                    warn("No ### BUG-NNN headings found in BUGS.md")
            else:
                bug_count = correct_headings + wrong_headings + bold_headings + bullet_headings
    else:
        fail("BUGS.md missing")

    # Extract canonical bug IDs (used by later sections) — sorted, unique
    bug_ids = []
    if bugs_md.is_file():
        try:
            bugs_content = bugs_md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            bugs_content = ""
        raw = re.findall(r'BUG-(?:[HML][0-9]+|[0-9]+)', bugs_content)
        # Filter to ensure each matches the full pattern
        filtered = [b for b in raw if re.fullmatch(r'BUG-(?:[HML][0-9]+|[0-9]+)', b)]
        bug_ids = sorted(set(filtered))

    # --- TDD sidecar JSON ---
    print("[TDD Sidecar JSON]")
    json_file = q / "results" / "tdd-results.json"
    if bug_count > 0:
        if json_file.is_file():
            pass_(f"tdd-results.json exists ({bug_count} bugs)")

            for key in ["schema_version", "skill_version", "date", "project", "bugs", "summary"]:
                if json_has_key(json_file, key):
                    pass_(f"has '{key}'")
                else:
                    fail(f"missing root key '{key}'")

            sv = json_str_val(json_file, "schema_version")
            if sv == "1.1":
                pass_("schema_version is '1.1'")
            else:
                fail(f"schema_version is '{sv or 'missing'}', expected '1.1'")

            for field in ["id", "requirement", "red_phase", "green_phase",
                          "verdict", "fix_patch_present", "writeup_path"]:
                fcount = json_key_count(json_file, field)
                if fcount >= bug_count:
                    pass_(f"per-bug field '{field}' present ({fcount}x)")
                elif fcount > 0:
                    warn(f"per-bug field '{field}' found {fcount}x, expected {bug_count}")
                else:
                    fail(f"per-bug field '{field}' missing entirely")

            for bad_field in ["bug_id", "bug_name", "status", "phase", "result"]:
                if json_has_key(json_file, bad_field):
                    fail(f"non-canonical field '{bad_field}' found (use standard field names)")

            for skey in ["total", "verified", "confirmed_open", "red_failed", "green_failed"]:
                scount = json_key_count(json_file, skey)
                if scount > 0:
                    pass_(f"summary has '{skey}'")
                else:
                    fail(f"summary missing '{skey}' count")

            # Date validation
            tdd_date = json_str_val(json_file, "date")
            if tdd_date:
                if re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', tdd_date):
                    if tdd_date in ("YYYY-MM-DD", "0000-00-00"):
                        fail(f"tdd-results.json date is placeholder '{tdd_date}'")
                    else:
                        today = date.today().isoformat()
                        if tdd_date > today:
                            fail(f"tdd-results.json date '{tdd_date}' is in the future")
                        else:
                            pass_(f"tdd-results.json date '{tdd_date}' is valid")
                else:
                    fail(f"tdd-results.json date '{tdd_date}' is not ISO 8601 (YYYY-MM-DD)")
            else:
                fail("tdd-results.json date field missing or empty")

            # Verdict enum
            try:
                json_content = json_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                json_content = ""
            verdict_values = re.findall(r'"verdict"\s*:\s*"([^"]*)"', json_content)
            allowed_verdicts = {"TDD verified", "red failed", "green failed",
                                "confirmed open", "deferred"}
            bad_verdicts = sum(1 for v in verdict_values if v not in allowed_verdicts)
            if bad_verdicts == 0:
                pass_("all verdict values are canonical")
            else:
                fail(f"{bad_verdicts} non-canonical verdict value(s)")
        else:
            fail(f"tdd-results.json missing ({bug_count} bugs require it)")
    else:
        info("Zero bugs — tdd-results.json not required")

    # --- TDD log files (v1.3.49) ---
    print("[TDD Log Files]")
    if bug_count > 0:
        red_found = 0
        red_missing = 0
        green_found = 0
        green_missing = 0
        green_expected = 0
        red_bad_tag = 0
        green_bad_tag = 0

        patches_dir = q / "patches"
        results_dir = q / "results"
        valid_tags = {"RED", "GREEN", "NOT_RUN", "ERROR"}

        for bid in bug_ids:
            red_log = results_dir / f"{bid}.red.log"
            if red_log.is_file():
                red_found += 1
                tag = read_first_line_stripped(red_log)
                if tag not in valid_tags:
                    red_bad_tag += 1
            else:
                red_missing += 1

            # Green log required only if fix patch exists
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
        if json_file.is_file():
            try:
                json_content = json_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                json_content = ""
            json_lines = json_content.splitlines()
            xv_mismatch = 0
            xv_checked = 0

            for bid in bug_ids:
                # Find line index where "id": "BUG-NNN" appears
                id_pat = re.compile(rf'"id"\s*:\s*"{re.escape(bid)}"')
                id_line_idx = -1
                for i, ln in enumerate(json_lines):
                    if id_pat.search(ln):
                        id_line_idx = i
                        break
                if id_line_idx < 0:
                    continue

                # Extract red_phase from next 5 lines (grep -A5)
                red_window = "\n".join(json_lines[id_line_idx:id_line_idx + 6])
                red_match = re.search(r'"red_phase"\s*:\s*"([^"]*)"', red_window)
                sidecar_red = red_match.group(1) if red_match else ""

                # Extract green_phase from next 10 lines (grep -A10)
                green_window = "\n".join(json_lines[id_line_idx:id_line_idx + 11])
                green_match = re.search(r'"green_phase"\s*:\s*"([^"]*)"', green_window)
                sidecar_green = green_match.group(1) if green_match else ""

                red_log = results_dir / f"{bid}.red.log"
                if sidecar_red and red_log.is_file():
                    log_red_tag = read_first_line_stripped(red_log)
                    xv_checked += 1
                    if sidecar_red == "fail" and log_red_tag != "RED":
                        xv_mismatch += 1
                        fail(f"{bid}: sidecar red_phase='{sidecar_red}' but log first-line is '{log_red_tag}' (expected RED)")
                    elif sidecar_red == "pass" and log_red_tag != "GREEN":
                        xv_mismatch += 1
                        fail(f"{bid}: sidecar red_phase='{sidecar_red}' but log first-line is '{log_red_tag}' (expected GREEN)")

                green_log = results_dir / f"{bid}.green.log"
                if sidecar_green and green_log.is_file():
                    log_green_tag = read_first_line_stripped(green_log)
                    xv_checked += 1
                    if sidecar_green == "pass" and log_green_tag != "GREEN":
                        xv_mismatch += 1
                        fail(f"{bid}: sidecar green_phase='{sidecar_green}' but log first-line is '{log_green_tag}' (expected GREEN)")
                    elif sidecar_green == "fail" and log_green_tag != "RED":
                        xv_mismatch += 1
                        fail(f"{bid}: sidecar green_phase='{sidecar_green}' but log first-line is '{log_green_tag}' (expected RED)")

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
    else:
        info("Zero bugs — TDD log files not required")

    # --- Integration sidecar JSON ---
    print("[Integration Sidecar JSON]")
    ij = q / "results" / "integration-results.json"
    if ij.is_file():
        for key in ["schema_version", "skill_version", "date", "project",
                    "recommendation", "groups", "summary", "uc_coverage"]:
            if json_has_key(ij, key):
                pass_(f"has '{key}'")
            else:
                fail(f"missing key '{key}'")

        for iskey in ["total_groups", "passed", "failed", "skipped"]:
            iscount = json_key_count(ij, iskey)
            if iscount > 0:
                pass_(f"integration summary has '{iskey}'")
            else:
                fail(f"integration summary missing required sub-key '{iskey}'")

        isv = json_str_val(ij, "schema_version")
        if isv == "1.1":
            pass_("integration schema_version is '1.1'")
        else:
            fail(f"integration schema_version is '{isv or 'missing'}', expected '1.1'")

        int_date = json_str_val(ij, "date")
        if int_date:
            if re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', int_date):
                if int_date in ("YYYY-MM-DD", "0000-00-00"):
                    fail(f"integration-results.json date is placeholder '{int_date}'")
                else:
                    today_int = date.today().isoformat()
                    if int_date > today_int:
                        fail(f"integration-results.json date '{int_date}' is in the future")
                    else:
                        pass_(f"integration-results.json date '{int_date}' is valid")
            else:
                fail(f"integration-results.json date '{int_date}' is not ISO 8601 (YYYY-MM-DD)")

        rec = json_str_val(ij, "recommendation")
        if rec in ("SHIP", "FIX BEFORE MERGE", "BLOCK"):
            pass_(f"recommendation '{rec}' is canonical")
        elif rec:
            fail(f"recommendation '{rec}' is non-canonical (must be SHIP/FIX BEFORE MERGE/BLOCK)")
        else:
            fail("recommendation missing")

        try:
            ij_content = ij.read_text(encoding="utf-8", errors="replace")
        except OSError:
            ij_content = ""
        result_values = re.findall(r'"result"\s*:\s*"([^"]*)"', ij_content)
        allowed_results = {"pass", "fail", "skipped", "error"}
        bad_results = sum(1 for v in result_values if v not in allowed_results)
        if bad_results == 0:
            pass_("all groups[].result values are canonical")
        else:
            fail(f"{bad_results} non-canonical groups[].result value(s) (must be pass/fail/skipped/error)")

        # uc_coverage value enum — replicate the bash pipeline
        # grep -oE '"uc_coverage"\s*:\s*\{[^}]*\}'  → inner-object block
        # | grep -oE '"[a-z_]+"\s*:\s*"[^"]*"'  → key:"value" pairs
        # | grep -v '"uc_coverage"'  → exclude the outer key itself
        # | grep -oE '"[^"]*"$'  → extract trailing quoted string
        # | tr -d '"'  → strip quotes
        # | grep -cvE '^(covered_pass|covered_fail|not_mapped)$'  → count bad
        bad_uc_vals = 0
        for block_m in re.finditer(r'"uc_coverage"\s*:\s*\{[^}]*\}', ij_content):
            block = block_m.group(0)
            # Find key:"value" pairs (each on its own line in standard JSON)
            for line_m in re.finditer(r'"[a-z_]+"\s*:\s*"[^"]*"', block):
                pair = line_m.group(0)
                if '"uc_coverage"' in pair:
                    continue
                # Extract trailing quoted string
                tail = re.search(r'"([^"]*)"$', pair)
                if tail:
                    v = tail.group(1)
                    if v not in ("covered_pass", "covered_fail", "not_mapped"):
                        bad_uc_vals += 1
        if bad_uc_vals == 0:
            pass_("all uc_coverage values are canonical")
        else:
            fail(f"{bad_uc_vals} non-canonical uc_coverage value(s) (must be covered_pass/covered_fail/not_mapped)")
    else:
        if strictness == "benchmark":
            warn("integration-results.json not present")
        else:
            info("integration-results.json not present (optional in general mode)")

    # --- Recheck sidecar JSON ---
    print("[Recheck Sidecar JSON]")
    rj = q / "results" / "recheck-results.json"
    rs = q / "results" / "recheck-summary.md"
    if rj.is_file():
        pass_("recheck-results.json exists")

        for key in ["schema_version", "skill_version", "date", "project", "bugs", "summary"]:
            if json_has_key(rj, key):
                pass_(f"recheck has '{key}'")
            else:
                fail(f"recheck missing root key '{key}'")

        rsv = json_str_val(rj, "schema_version")
        if rsv == "1.0":
            pass_("recheck schema_version is '1.0'")
        else:
            fail(f"recheck schema_version is '{rsv or 'missing'}', expected '1.0'")

        rdate = json_str_val(rj, "date")
        if rdate:
            if re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', rdate):
                if rdate in ("YYYY-MM-DD", "0000-00-00"):
                    fail(f"recheck-results.json date is placeholder '{rdate}'")
                else:
                    today_rck = date.today().isoformat()
                    if rdate > today_rck:
                        fail(f"recheck-results.json date '{rdate}' is in the future")
                    else:
                        pass_(f"recheck-results.json date '{rdate}' is valid")
            else:
                fail(f"recheck-results.json date '{rdate}' is not ISO 8601 (YYYY-MM-DD)")

        if rs.is_file():
            pass_("recheck-summary.md exists")
        else:
            fail("recheck-summary.md missing (required companion to recheck-results.json)")
    else:
        info("recheck-results.json not present (only required when recheck mode was run)")

    # --- Use cases (benchmark 43, 48) ---
    print("[Use Cases]")
    req_md = q / "REQUIREMENTS.md"
    if req_md.is_file():
        try:
            req_content = req_md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            req_content = ""
        # uc_ids = count of lines matching UC-N (grep -cE counts lines)
        uc_ids = sum(1 for ln in req_content.splitlines() if re.search(r'UC-[0-9]+', ln))
        # uc_unique = distinct UC identifiers
        uc_unique_set = set(re.findall(r'UC-[0-9]+', req_content))
        uc_unique = len(uc_unique_set)

        # Source file count for size-aware UC threshold
        src_count = 0
        if repo_dir.is_dir():
            src_extensions = {".go", ".py", ".java", ".kt", ".rs", ".ts", ".js",
                              ".scala", ".c", ".h", ".agc"}
            excluded_parts = {"vendor", "node_modules", ".git", "quality"}
            # Walk up to maxdepth 4 (find -maxdepth 4 counts from the target dir)
            # find -maxdepth 4 means target and 3 levels below
            def _walk(base, current_depth, max_depth, ext_set, excluded):
                nonlocal src_count
                try:
                    for entry in os.scandir(base):
                        rel = entry.name
                        if entry.is_dir(follow_symlinks=False):
                            if current_depth < max_depth and rel not in excluded:
                                _walk(entry.path, current_depth + 1, max_depth, ext_set, excluded)
                        elif entry.is_file(follow_symlinks=False):
                            # Check extension
                            dot = rel.rfind('.')
                            if dot >= 0:
                                ext = rel[dot:]
                                if ext in ext_set:
                                    src_count += 1
                except (OSError, PermissionError):
                    pass
            _walk(str(repo_dir), 1, 4, src_extensions, excluded_parts)

        min_uc = 3 if src_count < 5 else 5

        if uc_unique >= min_uc:
            pass_(f"Found {uc_unique} distinct UC identifiers ({uc_ids} total references, {src_count} source files)")
        elif uc_unique > 0:
            msg = f"Only {uc_unique} distinct UC identifiers (minimum {min_uc} "
            msg += f"{'for' if strictness == 'general' else 'required for'} {src_count} source files)"
            if strictness == "general":
                warn(msg)
            else:
                fail(msg)
        else:
            fail("No canonical UC-NN identifiers in REQUIREMENTS.md")
    else:
        fail("REQUIREMENTS.md missing")

    # --- Test file extension matches project language (benchmark 47) ---
    print("[Test File Extension]")
    func_test = first_file_matching(q, ["test_functional.*"])
    reg_test = first_file_matching(q, ["test_regression.*"])
    if func_test is not None:
        ext = func_test.suffix.lstrip(".") if func_test.suffix else ""

        # Detect project language with -maxdepth 3 find (top + 2 levels)
        # Excludes: vendor, node_modules, .git, quality
        language_order = [("go", ".go"), ("py", ".py"), ("java", ".java"),
                          ("kt", ".kt"), ("rs", ".rs"), ("ts", ".ts"),
                          ("js", ".js"), ("scala", ".scala"),
                          ("c", ".c"), ("agc", ".agc")]
        detected_lang = ""
        excluded_parts = {"vendor", "node_modules", ".git", "quality"}

        def _find_lang(base, target_ext, max_depth):
            try:
                for entry in os.scandir(base):
                    # find -maxdepth 3 means top level counts as depth 1
                    # We start at depth 1 in base's children = depth 2
                    # Let's do a proper walk with depth tracking
                    pass
            except (OSError, PermissionError):
                pass
            return False

        def _lang_present(base, target_ext):
            # find -maxdepth 3: base at depth 1, children at depth 2, etc.
            # So max recursion is 3 levels from base.
            stack = [(Path(base), 1)]
            while stack:
                curr, depth = stack.pop()
                try:
                    for entry in os.scandir(curr):
                        name = entry.name
                        if entry.is_dir(follow_symlinks=False):
                            # Skip excluded directories
                            if name in excluded_parts:
                                continue
                            if depth < 3:
                                stack.append((Path(entry.path), depth + 1))
                        elif entry.is_file(follow_symlinks=False):
                            if name.endswith(target_ext):
                                return True
                except (OSError, PermissionError):
                    continue
            return False

        for lang, target_ext in language_order:
            if _lang_present(repo_dir, target_ext):
                detected_lang = lang
                break

        if detected_lang:
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
        else:
            info(f"Cannot detect project language — skipping extension check (test_functional.{ext})")
    else:
        warn("No test_functional.* found")

    # --- Terminal Gate in PROGRESS.md ---
    print("[Terminal Gate]")
    progress_md = q / "PROGRESS.md"
    if progress_md.is_file():
        # grep -qiE '^#+ *Terminal' — case-insensitive regex
        if file_contains(progress_md, re.compile(r'^#+ *Terminal', re.IGNORECASE | re.MULTILINE)):
            pass_("PROGRESS.md has Terminal Gate section")
        else:
            fail("PROGRESS.md missing Terminal Gate section")

    # --- Mechanical verification ---
    print("[Mechanical Verification]")
    mech_dir = q / "mechanical"
    if mech_dir.is_dir():
        verify_sh = mech_dir / "verify.sh"
        if verify_sh.is_file():
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
        else:
            fail("mechanical/ exists but verify.sh missing")
    else:
        info("No mechanical/ directory")

    # --- Patches for confirmed bugs (benchmark 44) ---
    print("[Patches]")
    if bug_count > 0:
        patches_dir = q / "patches"
        reg_test_file = None
        if q.is_dir():
            # ls quality/test_regression.* | head -1 — sorted alphabetically by default
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

    # --- Writeups (benchmark 30) ---
    print("[Bug Writeups]")
    if bug_count > 0:
        writeups_dir = q / "writeups"
        writeup_count = 0
        writeup_diff_count = 0
        if writeups_dir.is_dir():
            writeup_files = [p for p in writeups_dir.glob("BUG-*.md") if p.is_file()]
            writeup_count = len(writeup_files)
            for wf in writeup_files:
                if file_contains(wf, r'```diff'):
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

    # --- Version stamps (benchmark 26) ---
    print("[Version Stamps]")
    skill_version = detect_skill_version([
        repo_dir / "SKILL.md",
        repo_dir / ".claude" / "skills" / "quality-playbook" / "SKILL.md",
        repo_dir / ".github" / "skills" / "SKILL.md",
        repo_dir / ".github" / "skills" / "quality-playbook" / "SKILL.md",
        SCRIPT_DIR / ".." / "SKILL.md",
        SCRIPT_DIR / "SKILL.md",
    ])

    if skill_version:
        if progress_md.is_file():
            pv = read_first_match_value(progress_md, r'Skill version:', r'.*Skill version: *')
            if pv == skill_version:
                pass_(f"PROGRESS.md version matches ({skill_version})")
            elif pv:
                fail(f"PROGRESS.md version '{pv}' != '{skill_version}'")
            else:
                warn("PROGRESS.md missing Skill version field")
        if json_file.is_file():
            tv = json_str_val(json_file, "skill_version")
            if tv == skill_version:
                pass_("tdd-results.json skill_version matches")
            elif tv:
                fail(f"tdd-results.json skill_version '{tv}' != '{skill_version}'")
    else:
        warn("Cannot detect skill version from SKILL.md")

    # --- Cross-run contamination ---
    print("[Cross-Run Contamination]")
    if skill_version and version_arg:
        # Extract trailing X.Y.Z from repo_name
        version_matches = re.findall(r'[0-9]+\.[0-9]+\.[0-9]+', repo_name)
        dir_version = version_matches[-1] if version_matches else ""
        if dir_version and dir_version != skill_version:
            fail(f"Directory version '{dir_version}' != skill version '{skill_version}' — possible cross-run contamination")
        else:
            pass_("No version mismatch detected")

    if json_file.is_file() and skill_version:
        json_sv = json_str_val(json_file, "skill_version")
        if json_sv and json_sv != skill_version:
            fail(f"tdd-results.json skill_version '{json_sv}' != SKILL.md '{skill_version}' — stale artifacts from prior run?")

    print("")


def detect_skill_version(locations):
    """Read version: line from first existing SKILL.md-like file."""
    for loc in locations:
        if loc.is_file():
            try:
                with open(loc, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if 'version:' in line:
                            # sed 's/.*version: *//' → everything after "version:" and optional spaces
                            # tr -d ' ' → remove all spaces
                            v = re.sub(r'.*version:\s*', '', line, count=1)
                            v = v.replace(' ', '').rstrip('\n').rstrip('\r')
                            if v:
                                return v
                            break
            except OSError:
                continue
    return ""


def read_first_match_value(path, contains_str, sed_pattern):
    """Mimic: grep -m1 'contains_str' | sed 's/sed_pattern//' | tr -d ' '."""
    if not path.is_file():
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if contains_str in line:
                    v = re.sub(sed_pattern, '', line, count=1)
                    v = v.replace(' ', '').rstrip('\n').rstrip('\r')
                    return v
    except OSError:
        pass
    return ""


def main():
    global FAIL, WARN
    repo_dirs = []
    version = ""
    check_all = False
    strictness = "benchmark"

    # Parse args — match bash logic exactly
    expect_version = False
    for arg in sys.argv[1:]:
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

    # Detect version from SKILL.md if not provided
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
        # Glob for *-VERSION/ dirs in SCRIPT_DIR, keep those with quality/
        for entry in sorted(SCRIPT_DIR.glob(f"*-{version}")):
            if (entry / "quality").is_dir():
                repo_dirs.append(str(entry))
    elif len(repo_dirs) == 1 and repo_dirs[0] == ".":
        repo_dirs = [str(Path.cwd())]
    else:
        resolved = []
        for name in repo_dirs:
            name_path = Path(name)
            if (name_path / "quality").is_dir():
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

    for repo_dir in repo_dirs:
        check_repo(repo_dir, version, strictness)

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
