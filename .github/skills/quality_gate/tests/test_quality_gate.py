#!/usr/bin/env python3
"""Test suite for quality_gate.py.

Uses unittest.TestCase, which both `unittest` and `pytest` can run.
Each test is self-contained: synthetic fixtures in temp directories,
no dependency on any real repo's quality/ folder.

Run from the QPB repo root with either:
    python3 -m pytest .github/skills/quality_gate/tests/test_quality_gate.py
    python3 -m unittest discover .github/skills/quality_gate/tests
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PACKAGE_DIR / "quality_gate.py"

# Import the module for direct helper tests.
# Insert the package dir first so `import quality_gate` resolves to the module
# file (quality_gate.py) rather than the package (quality_gate/__init__.py).
sys.path.insert(0, str(PACKAGE_DIR))
import quality_gate  # noqa: E402


def run_gate(repo_dir, args=()):
    """Run the gate script as a subprocess. Return (stdout, returncode)."""
    cmd = [sys.executable, str(SCRIPT_PATH), *args, str(repo_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.returncode


def write_tree(root, files):
    """Create files from a dict: {relative_path: content}.

    content of None means "create as empty directory".
    Parents are created automatically.
    """
    for rel, content in files.items():
        p = Path(root) / rel
        if content is None:
            p.mkdir(parents=True, exist_ok=True)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)


def today_iso():
    return date.today().isoformat()


def future_iso():
    return (date.today() + timedelta(days=7)).isoformat()


def minimal_zero_bug_tree(version="1.4.4"):
    """Return a dict describing a zero-bug all-pass repo tree."""
    return {
        "SKILL.md": f"---\nversion: {version}\n---\n",
        "AGENTS.md": "# Agents\n",
        "main.py": "print('hi')\n",  # a source file so language detection finds py
        "quality/BUGS.md": "# Bugs\n\nNo confirmed source-code bugs found.\n",
        "quality/REQUIREMENTS.md": (
            "# Requirements\n\n"
            "UC-01 Foo\n"
            "UC-02 Bar\n"
            "UC-03 Baz\n"
        ),
        "quality/QUALITY.md": "# Quality\n",
        "quality/PROGRESS.md": (
            f"# Progress\n\n"
            f"Skill version: {version}\n\n"
            "## Terminal Gate Verification\n"
        ),
        "quality/COVERAGE_MATRIX.md": "# Coverage\n",
        "quality/COMPLETENESS_REPORT.md": "# Completeness\n",
        "quality/CONTRACTS.md": "# Contracts\n",
        "quality/RUN_CODE_REVIEW.md": "# RCR\n",
        "quality/RUN_SPEC_AUDIT.md": "# RSA\n",
        "quality/RUN_INTEGRATION_TESTS.md": "# RIT\n",
        "quality/RUN_TDD_TESTS.md": "# RTT\n",
        "quality/test_functional.py": "# test\n",
        "quality/EXPLORATION.md": "# Exploration\n",
        "quality/code_reviews/r.md": "# Review\n",
        "quality/spec_audits/2026-01-01-triage.md": "# Triage\n",
        "quality/spec_audits/2026-01-01-auditor-1.md": "# Auditor\n",
        "quality/spec_audits/triage_probes.sh": "#!/bin/bash\n",
    }


def add_one_bug(tree, version="1.4.4", bug_id="BUG-001"):
    """Mutate a tree dict to include one confirmed bug with all required artifacts."""
    tree["quality/BUGS.md"] = (
        "# Bugs\n\n"
        f"### {bug_id}: Example bug\n\n"
        "Description of the bug.\n"
    )
    tree[f"quality/patches/{bug_id}-regression-test.patch"] = "--- /dev/null\n+++ b/test\n"
    tree[f"quality/patches/{bug_id}-fix.patch"] = "--- a/f\n+++ b/f\n"
    tree[f"quality/writeups/{bug_id}.md"] = (
        f"# {bug_id}\n\n"
        "## The fix\n\n"
        "```diff\n"
        "- old\n"
        "+ new\n"
        "```\n"
    )
    tree[f"quality/results/{bug_id}.red.log"] = "RED\nCommand: test\nExit code: 1\n"
    tree[f"quality/results/{bug_id}.green.log"] = "GREEN\nCommand: test\nExit code: 0\n"
    tree["quality/test_regression_test.go"] = "package quality\n"
    tree["quality/test_regression.py"] = "# Mirror as test_regression.*\n"
    tree["quality/TDD_TRACEABILITY.md"] = "# Traceability\n"
    tree["quality/results/tdd-results.json"] = json.dumps({
        "schema_version": "1.1",
        "skill_version": version,
        "date": today_iso(),
        "project": "testproj",
        "bugs": [
            {
                "id": bug_id,
                "requirement": "REQ-001",
                "red_phase": "fail",
                "green_phase": "pass",
                "verdict": "TDD verified",
                "fix_patch_present": True,
                "writeup_path": f"quality/writeups/{bug_id}.md",
            }
        ],
        "summary": {
            "total": 1,
            "verified": 1,
            "confirmed_open": 0,
            "red_failed": 0,
            "green_failed": 0,
        },
    }, indent=2)
    return tree


class FixtureBase(unittest.TestCase):
    """Base class: creates a tempdir and provides helpers."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, tree):
        write_tree(self.repo, tree)

    def gate(self, args=()):
        return run_gate(self.repo, args)


# --- JSON helper tests ---


class TestLoadJson(unittest.TestCase):
    def test_missing_file_returns_none(self):
        self.assertIsNone(quality_gate.load_json(Path("/nonexistent/file.json")))

    def test_valid_json_returns_dict(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"a": 1}')
            tmp_path = Path(f.name)
        try:
            self.assertEqual(quality_gate.load_json(tmp_path), {"a": 1})
        finally:
            tmp_path.unlink()

    def test_malformed_json_returns_none(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{not valid json")
            tmp_path = Path(f.name)
        try:
            self.assertIsNone(quality_gate.load_json(tmp_path))
        finally:
            tmp_path.unlink()

    def test_array_returns_list(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('[1, 2, 3]')
            tmp_path = Path(f.name)
        try:
            self.assertEqual(quality_gate.load_json(tmp_path), [1, 2, 3])
        finally:
            tmp_path.unlink()


class TestHasKey(unittest.TestCase):
    def test_dict_with_key(self):
        self.assertTrue(quality_gate.has_key({"a": 1}, "a"))

    def test_dict_without_key(self):
        self.assertFalse(quality_gate.has_key({"a": 1}, "b"))

    def test_none_returns_false(self):
        self.assertFalse(quality_gate.has_key(None, "a"))

    def test_list_returns_false(self):
        self.assertFalse(quality_gate.has_key([], "a"))

    def test_empty_dict(self):
        self.assertFalse(quality_gate.has_key({}, "a"))


class TestGetStr(unittest.TestCase):
    def test_string_value(self):
        self.assertEqual(quality_gate.get_str({"a": "hello"}, "a"), "hello")

    def test_number_value_returns_empty(self):
        self.assertEqual(quality_gate.get_str({"a": 42}, "a"), "")

    def test_bool_value_returns_empty(self):
        self.assertEqual(quality_gate.get_str({"a": True}, "a"), "")

    def test_none_value_returns_empty(self):
        self.assertEqual(quality_gate.get_str({"a": None}, "a"), "")

    def test_missing_key_returns_empty(self):
        self.assertEqual(quality_gate.get_str({"a": "x"}, "b"), "")

    def test_non_dict_returns_empty(self):
        self.assertEqual(quality_gate.get_str(None, "a"), "")
        self.assertEqual(quality_gate.get_str([], "a"), "")


class TestValidateIsoDate(unittest.TestCase):
    def test_valid_today(self):
        self.assertEqual(quality_gate.validate_iso_date(today_iso()), "valid")

    def test_past_date(self):
        self.assertEqual(quality_gate.validate_iso_date("2020-01-01"), "valid")

    def test_future_date(self):
        self.assertEqual(quality_gate.validate_iso_date(future_iso()), "future")

    def test_placeholder_YYYY(self):
        self.assertEqual(quality_gate.validate_iso_date("YYYY-MM-DD"), "placeholder")

    def test_placeholder_zeros(self):
        self.assertEqual(quality_gate.validate_iso_date("0000-00-00"), "placeholder")

    def test_bad_format(self):
        self.assertEqual(quality_gate.validate_iso_date("2026/04/18"), "bad_format")
        self.assertEqual(quality_gate.validate_iso_date("18-04-2026"), "bad_format")
        self.assertEqual(quality_gate.validate_iso_date("not a date"), "bad_format")

    def test_empty(self):
        self.assertEqual(quality_gate.validate_iso_date(""), "empty")


class TestCountPerBugField(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(quality_gate.count_per_bug_field([], "id"), 0)

    def test_all_have_field(self):
        bugs = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        self.assertEqual(quality_gate.count_per_bug_field(bugs, "id"), 3)

    def test_some_missing_field(self):
        bugs = [{"id": "a"}, {"foo": "b"}, {"id": "c"}]
        self.assertEqual(quality_gate.count_per_bug_field(bugs, "id"), 2)

    def test_non_dict_items_skipped(self):
        bugs = [{"id": "a"}, "not a dict", None, {"id": "b"}]
        self.assertEqual(quality_gate.count_per_bug_field(bugs, "id"), 2)

    def test_non_list_input(self):
        self.assertEqual(quality_gate.count_per_bug_field(None, "id"), 0)
        self.assertEqual(quality_gate.count_per_bug_field({}, "id"), 0)


# --- Integration tests per check section ---


class TestAllPassBaseline(FixtureBase):
    """A clean zero-bug run should PASS with no failures."""

    def test_zero_bug_all_pass(self):
        self.write(minimal_zero_bug_tree())
        stdout, code = self.gate()
        self.assertEqual(code, 0, f"Expected PASS, got:\n{stdout}")
        self.assertIn("RESULT: GATE PASSED", stdout)
        # No individual FAIL: lines in the per-check output (before the summary).
        body = stdout.split("===========================================")[0]
        self.assertNotIn("  FAIL:", body)

    def test_one_bug_all_pass(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        self.write(tree)
        stdout, code = self.gate()
        self.assertEqual(code, 0, f"Expected PASS, got:\n{stdout}")
        self.assertIn("RESULT: GATE PASSED", stdout)


class TestFileExistence(FixtureBase):
    def test_missing_bugs_md(self):
        tree = minimal_zero_bug_tree()
        del tree["quality/BUGS.md"]
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("FAIL: BUGS.md missing", stdout)
        self.assertEqual(code, 1)

    def test_missing_requirements_md(self):
        tree = minimal_zero_bug_tree()
        del tree["quality/REQUIREMENTS.md"]
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("FAIL: REQUIREMENTS.md missing", stdout)
        self.assertEqual(code, 1)

    def test_missing_agents_md(self):
        tree = minimal_zero_bug_tree()
        del tree["AGENTS.md"]
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("FAIL: AGENTS.md missing (required at project root)", stdout)
        self.assertEqual(code, 1)

    def test_missing_exploration_md(self):
        tree = minimal_zero_bug_tree()
        del tree["quality/EXPLORATION.md"]
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("FAIL: EXPLORATION.md missing", stdout)
        self.assertEqual(code, 1)

    def test_missing_code_reviews(self):
        tree = minimal_zero_bug_tree()
        del tree["quality/code_reviews/r.md"]
        self.write(tree)
        # Create empty code_reviews dir
        (self.repo / "quality" / "code_reviews").mkdir(parents=True, exist_ok=True)
        stdout, code = self.gate()
        self.assertIn("FAIL: code_reviews/ missing or empty", stdout)

    def test_missing_spec_audits_triage(self):
        tree = minimal_zero_bug_tree()
        del tree["quality/spec_audits/2026-01-01-triage.md"]
        # triage_probes.sh also matches '*triage*' glob, so remove it too
        # so the check sees a genuine absence of any triage file.
        del tree["quality/spec_audits/triage_probes.sh"]
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("FAIL: spec_audits/ missing triage file", stdout)

    def test_missing_auditor_files(self):
        tree = minimal_zero_bug_tree()
        del tree["quality/spec_audits/2026-01-01-auditor-1.md"]
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("FAIL: spec_audits/ missing individual auditor files", stdout)

    def test_functional_test_scala_variant(self):
        tree = minimal_zero_bug_tree()
        del tree["quality/test_functional.py"]
        del tree["main.py"]
        tree["quality/FunctionalSpec.scala"] = "// spec"
        tree["main.scala"] = "// scala"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("PASS: functional test file exists", stdout)

    def test_missing_functional_test(self):
        tree = minimal_zero_bug_tree()
        del tree["quality/test_functional.py"]
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: functional test file missing", stdout)


class TestBugsHeading(FixtureBase):
    def test_correct_heading(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree, bug_id="BUG-001")
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("PASS: All 1 bug headings use ### BUG-NNN format", stdout)
        self.assertEqual(code, 0)

    def test_wrong_double_hash(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        tree["quality/BUGS.md"] = "## BUG-001: bad format\n"
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("FAIL: 1 heading(s) use ## instead of ###", stdout)
        self.assertEqual(code, 1)

    def test_deep_heading(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        tree["quality/BUGS.md"] = "#### BUG-001: too deep\n"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: 1 heading(s) use #### or deeper instead of ###", stdout)

    def test_bold_format(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        tree["quality/BUGS.md"] = "**BUG-001**: bold\n"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: 1 heading(s) use **BUG- format", stdout)

    def test_bullet_format(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        tree["quality/BUGS.md"] = "- BUG-001: bullet\n"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: 1 heading(s) use - BUG- format", stdout)

    def test_zero_bug_run(self):
        tree = minimal_zero_bug_tree()
        # Default BUGS.md already says "No confirmed"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("PASS: Zero-bug run — no headings expected", stdout)

    def test_severity_prefix_heading(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree, bug_id="BUG-H1")
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("PASS: All 1 bug headings use ### BUG-NNN format", stdout)


class TestTDDSidecar(FixtureBase):
    def test_valid_sidecar_passes(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("PASS: tdd-results.json exists (1 bugs)", stdout)
        self.assertIn("PASS: schema_version is '1.1'", stdout)
        self.assertIn("PASS: all verdict values are canonical", stdout)

    def test_missing_sidecar_with_bugs(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        del tree["quality/results/tdd-results.json"]
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("FAIL: tdd-results.json missing", stdout)
        self.assertEqual(code, 1)

    def test_wrong_schema_version(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        data = json.loads(tree["quality/results/tdd-results.json"])
        data["schema_version"] = "1.0"
        tree["quality/results/tdd-results.json"] = json.dumps(data)
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("FAIL: schema_version is '1.0', expected '1.1'", stdout)
        self.assertEqual(code, 1)

    def test_placeholder_date(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        data = json.loads(tree["quality/results/tdd-results.json"])
        data["date"] = "YYYY-MM-DD"
        tree["quality/results/tdd-results.json"] = json.dumps(data)
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: tdd-results.json date is placeholder", stdout)

    def test_future_date(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        data = json.loads(tree["quality/results/tdd-results.json"])
        data["date"] = future_iso()
        tree["quality/results/tdd-results.json"] = json.dumps(data)
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("is in the future", stdout)

    def test_bad_date_format(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        data = json.loads(tree["quality/results/tdd-results.json"])
        data["date"] = "2026/04/18"
        tree["quality/results/tdd-results.json"] = json.dumps(data)
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("is not ISO 8601", stdout)

    def test_invalid_verdict(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        data = json.loads(tree["quality/results/tdd-results.json"])
        data["bugs"][0]["verdict"] = "bogus"
        tree["quality/results/tdd-results.json"] = json.dumps(data)
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: 1 non-canonical verdict value(s)", stdout)

    def test_non_canonical_field_name(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        data = json.loads(tree["quality/results/tdd-results.json"])
        data["bugs"][0]["bug_id"] = "BUG-001"  # bad field name
        tree["quality/results/tdd-results.json"] = json.dumps(data)
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("non-canonical field 'bug_id' found", stdout)

    def test_missing_summary_subkey(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        data = json.loads(tree["quality/results/tdd-results.json"])
        del data["summary"]["confirmed_open"]
        tree["quality/results/tdd-results.json"] = json.dumps(data)
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: summary missing 'confirmed_open' count", stdout)

    def test_missing_root_key(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        data = json.loads(tree["quality/results/tdd-results.json"])
        del data["project"]
        tree["quality/results/tdd-results.json"] = json.dumps(data)
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: missing root key 'project'", stdout)


class TestTDDLogs(FixtureBase):
    def test_all_logs_present(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("PASS: All 1 confirmed bug(s) have red-phase logs", stdout)
        self.assertIn("PASS: All 1 bug(s) with fix patches have green-phase logs", stdout)
        self.assertEqual(code, 0)

    def test_missing_red_log(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        del tree["quality/results/BUG-001.red.log"]
        self.write(tree)
        stdout, code = self.gate()
        # With only one bug and its red log missing, the "No red-phase logs
        # found" branch fires. With mixed presence, the "N missing" branch
        # fires. Either is a FAIL.
        self.assertTrue(
            "missing red-phase log" in stdout
            or "No red-phase logs found" in stdout,
            stdout,
        )
        self.assertEqual(code, 1)

    def test_invalid_status_tag(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        tree["quality/results/BUG-001.red.log"] = "INVALID_TAG\nstuff\n"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("missing valid first-line status tag", stdout)

    def test_green_log_not_required_without_fix_patch(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        del tree["quality/patches/BUG-001-fix.patch"]
        del tree["quality/results/BUG-001.green.log"]
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("No fix patches found — green-phase logs not required", stdout)

    def test_sidecar_red_log_mismatch(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        # sidecar says red_phase: "fail" (RED expected in log), but log says GREEN
        tree["quality/results/BUG-001.red.log"] = "GREEN\nactual\n"
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("sidecar red_phase='fail' but log first-line is 'GREEN' (expected RED)", stdout)
        self.assertEqual(code, 1)

    def test_tdd_traceability_required_with_red_logs(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        del tree["quality/TDD_TRACEABILITY.md"]
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: TDD_TRACEABILITY.md missing", stdout)


class TestIntegrationSidecar(FixtureBase):
    def test_absent_benchmark_warns(self):
        tree = minimal_zero_bug_tree()
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("WARN: integration-results.json not present", stdout)
        self.assertEqual(code, 0)  # WARN doesn't fail

    def test_absent_general_info(self):
        tree = minimal_zero_bug_tree()
        self.write(tree)
        stdout, code = self.gate(args=["--general"])
        self.assertIn("INFO: integration-results.json not present (optional in general mode)", stdout)
        self.assertEqual(code, 0)

    def test_valid_sidecar(self):
        tree = minimal_zero_bug_tree()
        tree["quality/results/integration-results.json"] = json.dumps({
            "schema_version": "1.1",
            "skill_version": "1.4.4",
            "date": today_iso(),
            "project": "testproj",
            "recommendation": "SHIP",
            "groups": [{"group": 1, "name": "g", "use_cases": ["UC-01"], "result": "pass"}],
            "summary": {"total_groups": 1, "passed": 1, "failed": 0, "skipped": 0},
            "uc_coverage": {"UC-01": "covered_pass"},
        })
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("PASS: recommendation 'SHIP' is canonical", stdout)
        self.assertIn("PASS: all groups[].result values are canonical", stdout)
        self.assertIn("PASS: all uc_coverage values are canonical", stdout)

    def test_bad_recommendation(self):
        tree = minimal_zero_bug_tree()
        tree["quality/results/integration-results.json"] = json.dumps({
            "schema_version": "1.1",
            "skill_version": "1.4.4",
            "date": today_iso(),
            "project": "t",
            "recommendation": "MAYBE",
            "groups": [],
            "summary": {"total_groups": 0, "passed": 0, "failed": 0, "skipped": 0},
            "uc_coverage": {},
        })
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: recommendation 'MAYBE' is non-canonical", stdout)

    def test_bad_result_value(self):
        tree = minimal_zero_bug_tree()
        tree["quality/results/integration-results.json"] = json.dumps({
            "schema_version": "1.1",
            "skill_version": "1.4.4",
            "date": today_iso(),
            "project": "t",
            "recommendation": "SHIP",
            "groups": [{"group": 1, "name": "g", "use_cases": [], "result": "bogus"}],
            "summary": {"total_groups": 1, "passed": 0, "failed": 0, "skipped": 0},
            "uc_coverage": {},
        })
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: 1 non-canonical groups[].result value(s)", stdout)

    def test_bad_uc_coverage_value(self):
        tree = minimal_zero_bug_tree()
        tree["quality/results/integration-results.json"] = json.dumps({
            "schema_version": "1.1",
            "skill_version": "1.4.4",
            "date": today_iso(),
            "project": "t",
            "recommendation": "SHIP",
            "groups": [],
            "summary": {"total_groups": 0, "passed": 0, "failed": 0, "skipped": 0},
            "uc_coverage": {"UC-01": "NOT_A_VALID_STATUS"},
        })
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: 1 non-canonical uc_coverage value(s)", stdout)


class TestRecheckSidecar(FixtureBase):
    def test_absent_is_info(self):
        tree = minimal_zero_bug_tree()
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("INFO: recheck-results.json not present", stdout)

    def test_uses_results_key_not_bugs(self):
        """SKILL.md recheck template uses 'results' as array key."""
        tree = minimal_zero_bug_tree()
        tree["quality/results/recheck-results.json"] = json.dumps({
            "schema_version": "1.0",
            "skill_version": "1.4.4",
            "date": today_iso(),
            "project": "t",
            "source_run": {"bugs_md_date": today_iso(), "total_bugs": 1},
            "results": [{"id": "BUG-001", "severity": "HIGH", "status": "FIXED"}],
            "summary": {"total": 1, "fixed": 1, "partially_fixed": 0,
                        "still_open": 0, "inconclusive": 0},
        })
        tree["quality/results/recheck-summary.md"] = "# Recheck\n"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("PASS: recheck has 'results'", stdout)
        self.assertIn("PASS: recheck schema_version is '1.0'", stdout)

    def test_wrong_schema_version(self):
        tree = minimal_zero_bug_tree()
        tree["quality/results/recheck-results.json"] = json.dumps({
            "schema_version": "1.1",  # wrong, should be 1.0
            "skill_version": "1.4.4",
            "date": today_iso(),
            "project": "t",
            "results": [],
            "summary": {},
        })
        tree["quality/results/recheck-summary.md"] = "# s\n"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: recheck schema_version is '1.1', expected '1.0'", stdout)

    def test_missing_summary_md(self):
        tree = minimal_zero_bug_tree()
        tree["quality/results/recheck-results.json"] = json.dumps({
            "schema_version": "1.0",
            "skill_version": "1.4.4",
            "date": today_iso(),
            "project": "t",
            "results": [],
            "summary": {},
        })
        # No recheck-summary.md
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: recheck-summary.md missing", stdout)


class TestUseCases(FixtureBase):
    def test_sufficient_ucs_pass(self):
        tree = minimal_zero_bug_tree()
        # Default has UC-01, UC-02, UC-03 and 1 source file → min_uc=3
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("PASS: Found 3 distinct UC identifiers", stdout)

    def test_too_few_ucs_benchmark_fails(self):
        tree = minimal_zero_bug_tree()
        # 10+ source files to trigger min_uc=5
        for i in range(10):
            tree[f"src_{i}.py"] = "pass\n"
        # Requirements has only 3 UCs (from default), need 5
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("FAIL: Only 3 distinct UC identifiers", stdout)
        self.assertEqual(code, 1)

    def test_too_few_ucs_general_warns(self):
        tree = minimal_zero_bug_tree()
        for i in range(10):
            tree[f"src_{i}.py"] = "pass\n"
        self.write(tree)
        stdout, code = self.gate(args=["--general"])
        self.assertIn("WARN: Only 3 distinct UC identifiers", stdout)
        self.assertEqual(code, 0)

    def test_no_ucs_fails(self):
        tree = minimal_zero_bug_tree()
        tree["quality/REQUIREMENTS.md"] = "# No UCs\n"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: No canonical UC-NN identifiers", stdout)


class TestTestFileExtension(FixtureBase):
    def test_py_project_py_test_passes(self):
        tree = minimal_zero_bug_tree()
        # Default has main.py and test_functional.py
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("PASS: test_functional.py matches project language (py)", stdout)

    def test_go_project_py_test_fails(self):
        tree = minimal_zero_bug_tree()
        del tree["main.py"]
        tree["main.go"] = "package main\n"
        # test_functional.py remains — mismatch
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: test_functional.py does not match project language (go)", stdout)

    def test_no_language_detected(self):
        tree = minimal_zero_bug_tree()
        del tree["main.py"]
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("INFO: Cannot detect project language", stdout)


class TestTerminalGate(FixtureBase):
    def test_terminal_section_present(self):
        tree = minimal_zero_bug_tree()
        # Default PROGRESS.md has "## Terminal Gate Verification"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("PASS: PROGRESS.md has Terminal Gate section", stdout)

    def test_terminal_section_missing(self):
        tree = minimal_zero_bug_tree()
        tree["quality/PROGRESS.md"] = "# Progress\n\nSkill version: 1.4.4\n"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: PROGRESS.md missing Terminal Gate section", stdout)

    def test_terminal_section_case_insensitive(self):
        tree = minimal_zero_bug_tree()
        tree["quality/PROGRESS.md"] = (
            "# Progress\n\nSkill version: 1.4.4\n\n## TERMINAL GATE\n"
        )
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("PASS: PROGRESS.md has Terminal Gate section", stdout)


class TestMechanicalVerification(FixtureBase):
    def test_no_mechanical_dir_is_info(self):
        tree = minimal_zero_bug_tree()
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("INFO: No mechanical/ directory", stdout)

    def test_dir_without_verify_sh_fails(self):
        tree = minimal_zero_bug_tree()
        tree["quality/mechanical/placeholder"] = ""
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: mechanical/ exists but verify.sh missing", stdout)

    def test_verify_sh_with_exit_0_passes(self):
        tree = minimal_zero_bug_tree()
        tree["quality/mechanical/verify.sh"] = "#!/bin/bash\n"
        tree["quality/results/mechanical-verify.log"] = "output\n"
        tree["quality/results/mechanical-verify.exit"] = "0\n"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("PASS: verify.sh exists", stdout)
        self.assertIn("PASS: mechanical-verify.exit is 0", stdout)

    def test_verify_sh_with_exit_nonzero_fails(self):
        tree = minimal_zero_bug_tree()
        tree["quality/mechanical/verify.sh"] = "#!/bin/bash\n"
        tree["quality/results/mechanical-verify.log"] = "output\n"
        tree["quality/results/mechanical-verify.exit"] = "1\n"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: mechanical-verify.exit is '1', expected 0", stdout)


class TestPatches(FixtureBase):
    def test_both_patches_present(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("PASS: 1 regression-test patch(es) for 1 bug(s)", stdout)
        self.assertIn("PASS: 1 fix patch(es)", stdout)

    def test_missing_regression_patch(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        del tree["quality/patches/BUG-001-regression-test.patch"]
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL", stdout)
        # Either "1 bug(s) missing regression-test patch" or "No regression-test patches found"
        self.assertTrue(
            "missing regression-test patch" in stdout
            or "No regression-test patches found" in stdout
        )

    def test_missing_test_regression_benchmark_fails(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        del tree["quality/test_regression_test.go"]
        del tree["quality/test_regression.py"]
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("FAIL: test_regression.* missing", stdout)
        self.assertEqual(code, 1)

    def test_missing_test_regression_general_warns(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        del tree["quality/test_regression_test.go"]
        del tree["quality/test_regression.py"]
        self.write(tree)
        stdout, code = self.gate(args=["--general"])
        self.assertIn("WARN: test_regression.* missing", stdout)


class TestWriteups(FixtureBase):
    def test_all_writeups_with_diffs(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("PASS: 1 writeup(s) for 1 bug(s)", stdout)
        self.assertIn("PASS: All 1 writeup(s) have inline fix diffs", stdout)

    def test_writeup_without_diff_fails(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        tree["quality/writeups/BUG-001.md"] = "# BUG-001\n\nNo diff block here.\n"
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL", stdout)

    def test_missing_writeup(self):
        tree = minimal_zero_bug_tree()
        add_one_bug(tree)
        del tree["quality/writeups/BUG-001.md"]
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: No writeups for 1 confirmed bug(s)", stdout)


class TestVersionStamps(FixtureBase):
    def test_matching_versions_pass(self):
        tree = minimal_zero_bug_tree()
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("PASS: PROGRESS.md version matches (1.4.4)", stdout)

    def test_mismatched_progress_version(self):
        tree = minimal_zero_bug_tree()
        tree["quality/PROGRESS.md"] = (
            "# Progress\n\nSkill version: 1.3.99\n\n## Terminal Gate Verification\n"
        )
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("FAIL: PROGRESS.md version '1.3.99' != '1.4.4'", stdout)

    def test_missing_version_in_progress(self):
        tree = minimal_zero_bug_tree()
        tree["quality/PROGRESS.md"] = (
            "# Progress\n\n## Terminal Gate Verification\n"
        )
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("WARN: PROGRESS.md missing Skill version field", stdout)


class TestCrossRunContamination(FixtureBase):
    def test_matching_directory_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            versioned = Path(tmpdir) / "myrepo-1.4.4"
            versioned.mkdir()
            write_tree(versioned, minimal_zero_bug_tree())
            stdout, code = run_gate(versioned, args=["--version", "1.4.4"])
            self.assertIn("PASS: No version mismatch detected", stdout)

    def test_mismatched_directory_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            versioned = Path(tmpdir) / "myrepo-1.3.99"
            versioned.mkdir()
            write_tree(versioned, minimal_zero_bug_tree())  # SKILL.md says 1.4.4
            stdout, code = run_gate(versioned, args=["--version", "1.3.99"])
            self.assertIn("possible cross-run contamination", stdout)
            self.assertEqual(code, 1)


class TestStrictnessModes(FixtureBase):
    def test_benchmark_default(self):
        tree = minimal_zero_bug_tree()
        self.write(tree)
        stdout, _ = self.gate()
        self.assertIn("Strictness: benchmark", stdout)

    def test_general_flag(self):
        tree = minimal_zero_bug_tree()
        self.write(tree)
        stdout, _ = self.gate(args=["--general"])
        self.assertIn("Strictness: general", stdout)

    def test_triage_probes_missing_benchmark_fails(self):
        tree = minimal_zero_bug_tree()
        del tree["quality/spec_audits/triage_probes.sh"]
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("FAIL: No executable triage evidence found", stdout)
        self.assertEqual(code, 1)

    def test_triage_probes_missing_general_warns(self):
        tree = minimal_zero_bug_tree()
        del tree["quality/spec_audits/triage_probes.sh"]
        self.write(tree)
        stdout, code = self.gate(args=["--general"])
        self.assertIn("WARN: No executable triage evidence found", stdout)
        self.assertEqual(code, 0)


class TestExitCodes(FixtureBase):
    def test_all_pass_exit_zero(self):
        tree = minimal_zero_bug_tree()
        self.write(tree)
        _, code = self.gate()
        self.assertEqual(code, 0)

    def test_any_fail_exit_one(self):
        tree = minimal_zero_bug_tree()
        del tree["quality/BUGS.md"]
        self.write(tree)
        _, code = self.gate()
        self.assertEqual(code, 1)

    def test_warn_only_exit_zero(self):
        tree = minimal_zero_bug_tree()
        # absence of integration-results.json is a WARN (benchmark mode)
        self.write(tree)
        stdout, code = self.gate()
        self.assertIn("WARN:", stdout)
        self.assertEqual(code, 0)

    def test_no_args_prints_usage_exit_one(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True, text=True
        )
        self.assertIn("Usage:", result.stdout)
        self.assertEqual(result.returncode, 1)


class TestSkillVersionDetection(unittest.TestCase):
    def test_detects_from_frontmatter(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nname: quality-playbook\nversion: 1.5.0\n---\n")
            path = Path(f.name)
        try:
            self.assertEqual(quality_gate.detect_skill_version([path]), "1.5.0")
        finally:
            path.unlink()

    def test_returns_empty_when_no_file(self):
        self.assertEqual(
            quality_gate.detect_skill_version([Path("/nonexistent/SKILL.md")]),
            "",
        )

    def test_first_matching_location_wins(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p1 = Path(tmpdir) / "first.md"
            p2 = Path(tmpdir) / "second.md"
            p1.write_text("---\nversion: 1.1.1\n---\n")
            p2.write_text("---\nversion: 2.2.2\n---\n")
            self.assertEqual(
                quality_gate.detect_skill_version([p1, p2]),
                "1.1.1",
            )


if __name__ == "__main__":
    unittest.main()
