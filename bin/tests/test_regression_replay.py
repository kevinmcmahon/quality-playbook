"""Tests for the regression-replay apparatus (v1.5.4 Phase 5).

Coverage:
- BUGS.md parser handles both v1.3-era (`- **Requirement:**`) and
  v1.5-era (`- Primary requirement:`) field shapes
- File-citation parser strips line ranges and reduces to basename
- Recall calculator handles perfect-match, partial-match,
  zero-current, zero-historical, and missing-fields cases
- Cell-record builder populates every SCHEMA.md-required field
- write_cell follows the SCHEMA.md path convention
- The CLI's measurement-only mode produces a valid cell.json against
  the chi-1.3.45 archive end-to-end (the Phase 5 smoke deliverable)
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin import regression_replay as rr


REPO_ROOT = Path(__file__).resolve().parents[2]
CHI_1_3_45_BUGS = REPO_ROOT / "repos" / "archive" / "chi-1.3.45" / "quality" / "BUGS.md"
CHI_1_5_1_BUGS = REPO_ROOT / "repos" / "archive" / "chi-1.5.1" / "quality" / "BUGS.md"
BUS_TRACKER_1_5_0_BUGS = REPO_ROOT / "repos" / "bus-tracker-1.5.0" / "quality" / "BUGS.md"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class BugsMdParserTests(unittest.TestCase):

    def test_parses_v13_era_bold_field_shape(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "BUGS.md"
            _write(
                p,
                "### BUG-001: Title one\n"
                "- **Requirement:** REQ-009\n"
                "- **File:** `middleware/compress.go:218-220,240-245`\n"
                "- **Severity:** High\n"
                "\n"
                "### BUG-002: Title two\n"
                "- **Requirement:** REQ-013\n"
                "- **File:** `middleware/route_headers.go:85-92`\n",
            )
            recs = rr.parse_bugs_md(p)
            self.assertEqual(len(recs), 2)
            self.assertEqual(recs[0].bug_id, "BUG-001")
            self.assertEqual(recs[0].requirement, "REQ-009")
            self.assertEqual(recs[0].primary_file, "compress.go")
            self.assertEqual(recs[1].requirement, "REQ-013")
            self.assertEqual(recs[1].primary_file, "route_headers.go")

    def test_parses_v15_era_plain_field_shape(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "BUGS.md"
            _write(
                p,
                "### BUG-001: Title\n"
                "- Source: Phase 3 review\n"
                "- File:line: `middleware/compress.go:214-246`\n"
                "- Primary requirement: REQ-007\n"
                "- Severity: MEDIUM\n",
            )
            recs = rr.parse_bugs_md(p)
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0].requirement, "REQ-007")
            self.assertEqual(recs[0].primary_file, "compress.go")

    def test_strips_line_ranges_from_multifile_citation(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "BUGS.md"
            _write(
                p,
                "### BUG-001: Multi-file\n"
                "- Primary requirement: REQ-005\n"
                "- File:line: `mux.go:127-133`, `mux.go:368-371`\n",
            )
            recs = rr.parse_bugs_md(p)
            # Multi-file citation; primary_file is the FIRST file's basename.
            self.assertEqual(recs[0].primary_file, "mux.go")

    def test_records_with_missing_fields_have_no_match_key(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "BUGS.md"
            _write(
                p,
                "### BUG-001: Bare heading only\n"
                "Some prose, no fields.\n",
            )
            recs = rr.parse_bugs_md(p)
            self.assertIsNone(recs[0].requirement)
            self.assertIsNone(recs[0].primary_file)
            self.assertIsNone(recs[0].match_key)

    def test_missing_file_raises_filenotfounderror(self) -> None:
        with self.assertRaises(FileNotFoundError):
            rr.parse_bugs_md(Path("/nonexistent/BUGS.md"))


class StripLinesTests(unittest.TestCase):

    def test_simple_path_with_line_range(self) -> None:
        self.assertEqual(
            rr._strip_lines("middleware/compress.go:218-220,240-245"),
            "middleware/compress.go",
        )

    def test_multi_file_takes_first(self) -> None:
        self.assertEqual(
            rr._strip_lines("mux.go:127-133`, `mux.go:368-371"),
            "mux.go",
        )

    def test_path_with_no_line_range_passes_through(self) -> None:
        self.assertEqual(
            rr._strip_lines("middleware/route_headers.go"),
            "middleware/route_headers.go",
        )


class RecallMeasurementTests(unittest.TestCase):

    def _rec(self, bug_id: str, req: str, basename: str) -> rr.BugRecord:
        return rr.BugRecord(
            bug_id=bug_id,
            title=f"title for {bug_id}",
            requirement=req,
            primary_file=basename,
            raw_file_field=basename,
        )

    def test_perfect_recall_when_self_matched(self) -> None:
        bugs = [self._rec("BUG-001", "REQ-001", "a.go"),
                self._rec("BUG-002", "REQ-002", "b.go")]
        m = rr.measure_recall(bugs, bugs)
        self.assertEqual(m.recall, 1.0)
        self.assertEqual(m.recovered_ids, ["BUG-001", "BUG-002"])
        self.assertEqual(m.missed_ids, [])
        self.assertEqual(m.spurious_ids, [])

    def test_partial_recall(self) -> None:
        historical = [self._rec("BUG-001", "REQ-001", "a.go"),
                      self._rec("BUG-002", "REQ-002", "b.go"),
                      self._rec("BUG-003", "REQ-003", "c.go")]
        # Current finds REQ-001 and REQ-003 plus one new bug.
        current = [self._rec("BUG-007", "REQ-001", "a.go"),
                   self._rec("BUG-008", "REQ-003", "c.go"),
                   self._rec("BUG-009", "REQ-099", "z.go")]
        m = rr.measure_recall(historical, current)
        self.assertAlmostEqual(m.recall, 2 / 3)
        self.assertEqual(m.recovered_ids, ["BUG-001", "BUG-003"])
        self.assertEqual(m.missed_ids, ["BUG-002"])
        self.assertEqual(m.spurious_ids, ["BUG-009"])

    def test_id_renumbering_does_not_affect_match(self) -> None:
        """Critical contract: BUG-NNN IDs are renumbered between runs;
        match identity is (REQ, file basename), not the ID."""
        historical = [self._rec("BUG-001", "REQ-005", "mux.go")]
        current = [self._rec("BUG-042", "REQ-005", "mux.go")]
        m = rr.measure_recall(historical, current)
        self.assertEqual(m.recall, 1.0)
        self.assertEqual(m.recovered_ids, ["BUG-001"])
        self.assertEqual(m.spurious_ids, [])

    def test_zero_historical_returns_zero_recall(self) -> None:
        m = rr.measure_recall([], [self._rec("BUG-001", "REQ-001", "a.go")])
        self.assertEqual(m.recall, 0.0)
        self.assertEqual(m.recovered_ids, [])
        self.assertEqual(m.spurious_ids, ["BUG-001"])

    def test_zero_current_returns_zero_recall(self) -> None:
        historical = [self._rec("BUG-001", "REQ-001", "a.go")]
        m = rr.measure_recall(historical, [])
        self.assertEqual(m.recall, 0.0)
        self.assertEqual(m.missed_ids, ["BUG-001"])

    def test_records_with_no_match_key_are_treated_as_unmatched(self) -> None:
        historical = [rr.BugRecord("BUG-001", "?", None, None, None)]
        current = [rr.BugRecord("BUG-002", "?", None, None, None)]
        m = rr.measure_recall(historical, current)
        # Neither side matches anything.
        self.assertEqual(m.recall, 0.0)
        self.assertEqual(m.recovered_ids, [])
        # The current bug has no key, so it falls into spurious.
        self.assertEqual(m.spurious_ids, ["BUG-002"])


class CellRecordBuilderTests(unittest.TestCase):
    """Every SCHEMA.md-required field must appear in the built cell."""

    REQUIRED_TOP_FIELDS = (
        "schema_version",
        "timestamp",
        "benchmark",
        "qpb_version_under_test",
        "historical_qpb_version",
        "historical_bug_id",
        "historical_bug_count",
        "current_bug_count",
        "current_bug_ids",
        "recovered_bug_ids",
        "missed_bug_ids",
        "spurious_bug_ids",
        "recall_against_historical",
        "lever_under_test",
        "lever_change_summary",
        "before_lever",
        "after_lever",
        "regression_check",
        "noise_floor_source",
        "apparatus",
        "notes",
    )

    REQUIRED_REGRESSION_CHECK_FIELDS = (
        "status", "checked_cells", "regressed_cells", "noise_floor_threshold"
    )

    REQUIRED_APPARATUS_FIELDS = (
        "qpb_commit_sha", "target_commit_sha", "phase_scope",
        "iteration_strategies", "runner", "model", "wall_clock_seconds",
    )

    def _build(self) -> dict:
        bugs = [
            rr.BugRecord("BUG-001", "t", "REQ-001", "a.go", "a.go:1-2"),
            rr.BugRecord("BUG-002", "t", "REQ-002", "b.go", "b.go:1-2"),
        ]
        m = rr.measure_recall(bugs, bugs)
        with TemporaryDirectory() as tmp:
            inputs = rr.CellInputs(
                benchmark="chi",
                historical_qpb_version="1.3.45",
                historical_bug_id="all",
                historical_path=Path(tmp) / "h.md",
                current_path=Path(tmp) / "c.md",
                target_dir=None,
                qpb_dir=Path(tmp),
            )
            return rr.build_cell_record(inputs, m)

    def test_every_top_level_field_present(self) -> None:
        rec = self._build()
        for field in self.REQUIRED_TOP_FIELDS:
            self.assertIn(field, rec, f"missing {field!r}")

    def test_regression_check_subfields_present(self) -> None:
        rec = self._build()
        for field in self.REQUIRED_REGRESSION_CHECK_FIELDS:
            self.assertIn(field, rec["regression_check"])

    def test_apparatus_subfields_present(self) -> None:
        rec = self._build()
        for field in self.REQUIRED_APPARATUS_FIELDS:
            self.assertIn(field, rec["apparatus"])

    def test_recall_in_cell_matches_measurement(self) -> None:
        rec = self._build()
        self.assertEqual(rec["recall_against_historical"], 1.0)
        self.assertEqual(rec["recovered_bug_ids"], ["BUG-001", "BUG-002"])

    def test_schema_version_is_v154(self) -> None:
        self.assertEqual(self._build()["schema_version"], "1.5.4")


class WriteCellTests(unittest.TestCase):

    def test_path_convention_followed(self) -> None:
        record = {
            "schema_version": "1.5.4",
            "benchmark": "chi",
            "historical_qpb_version": "1.3.45",
            "historical_bug_id": "all",
        }
        with TemporaryDirectory() as tmp:
            out = rr.write_cell(record, Path(tmp), run_timestamp="20260501T120000Z")
            self.assertEqual(
                out,
                Path(tmp) / "20260501T120000Z" / "chi-1.3.45-all.json",
            )
            self.assertTrue(out.is_file())
            on_disk = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(on_disk["benchmark"], "chi")

    def test_per_bug_filename_uses_bug_id(self) -> None:
        record = {
            "schema_version": "1.5.4",
            "benchmark": "virtio",
            "historical_qpb_version": "1.3.50",
            "historical_bug_id": "BUG-007",
        }
        with TemporaryDirectory() as tmp:
            out = rr.write_cell(record, Path(tmp), run_timestamp="20260501T120000Z")
            self.assertEqual(out.name, "virtio-1.3.50-BUG-007.json")


class CorpusRealFileParserTests(unittest.TestCase):
    """Council 2026-04-30 P0-1 regression pin: parse against the
    actual benchmark archive corpus, not synthetic fixtures.

    Methodology lesson from the Council synthesis: ``synthetic-fixture
    coverage masked the real-input failure``. The original v1.5-era
    test (``test_parses_v15_era_plain_field_shape``) hand-wrote
    plain-key fields, so bold-key variants used by real archives
    (``- **Primary requirement:** REQ-NNN``) were never exercised.
    The original heading regex required a colon-then-title that
    chi-1.5.1's bare ``### BUG-001`` doesn't carry.

    This test loads real archive files and asserts non-zero records
    AND non-zero match-keyed records. Loosening the heading regex
    or removing a bold-key variant trips this immediately."""

    def test_chi_1_5_1_archive_parses_with_match_keys(self) -> None:
        """Empirical reproduction of P0-1 claim 1: chi-1.5.1's bare
        ``### BUG-NNN`` headings (no colon, no inline title)."""
        if not CHI_1_5_1_BUGS.is_file():
            self.skipTest(f"missing {CHI_1_5_1_BUGS}")
        recs = rr.parse_bugs_md(CHI_1_5_1_BUGS)
        # The chi-1.5.1 archive carries 9 confirmed bugs.
        self.assertEqual(len(recs), 9, "chi-1.5.1 record count drift")
        keyed = [r for r in recs if r.match_key is not None]
        self.assertEqual(
            len(keyed), 9,
            "every chi-1.5.1 record must have a match_key — bold/plain "
            "field variants must all be recognized"
        )

    def test_bus_tracker_1_5_0_bold_key_variants_recognized(self) -> None:
        """Empirical reproduction of P0-1 claims 2 and 3:
        bus-tracker-1.5.0 uses bold-key Primary requirement / Location
        variants. Removing either bold variant from the regex set
        drops match_key counts to zero."""
        if not BUS_TRACKER_1_5_0_BUGS.is_file():
            self.skipTest(f"missing {BUS_TRACKER_1_5_0_BUGS}")
        recs = rr.parse_bugs_md(BUS_TRACKER_1_5_0_BUGS)
        self.assertEqual(len(recs), 18, "bus-tracker-1.5.0 record count drift")
        keyed = [r for r in recs if r.match_key is not None]
        self.assertEqual(
            len(keyed), 18,
            "every bus-tracker-1.5.0 record must have a match_key — "
            "bold-key Primary requirement / Location variants must work"
        )
        # Spot-check first record's normalized fields.
        self.assertEqual(recs[0].requirement, "REQ-004")
        self.assertEqual(recs[0].primary_file, "bus_tracker.py")

    def test_chi_1_3_45_legacy_bold_key_still_works(self) -> None:
        """Cross-check: the v1.3-era ``- **Requirement:** /
        - **File:**`` shape that worked before P0-1 fix must still
        parse — the bold-key additions for v1.5 must NOT regress
        v1.3 coverage."""
        if not CHI_1_3_45_BUGS.is_file():
            self.skipTest(f"missing {CHI_1_3_45_BUGS}")
        recs = rr.parse_bugs_md(CHI_1_3_45_BUGS)
        self.assertEqual(len(recs), 10)
        self.assertTrue(all(r.match_key is not None for r in recs))


class SmokeTestAgainstChi1345Archive(unittest.TestCase):
    """Phase 5 deliverable: end-to-end run against the chi-1.3.45
    archive. Uses measurement-only mode (the historical baseline IS
    the "current" bug set) so the smoke run is instant and produces
    a perfect-recall cell — useful only as proof the apparatus
    plumbing works end-to-end. Real calibration cycles in Phase 6+
    use a separate "current" path produced by an actual QPB run."""

    def setUp(self) -> None:
        if not CHI_1_3_45_BUGS.is_file():
            self.skipTest(
                f"chi-1.3.45 archive not present at {CHI_1_3_45_BUGS}"
            )

    def test_full_set_recall_against_historical_baseline_is_perfect(self) -> None:
        recs = rr.parse_bugs_md(CHI_1_3_45_BUGS)
        # The chi-1.3.45 archive carries 10 confirmed bugs.
        self.assertEqual(len(recs), 10)
        m = rr.measure_recall(recs, recs)
        self.assertEqual(m.recall, 1.0)
        self.assertEqual(len(m.recovered_ids), 10)

    def test_cli_smoke_run_writes_valid_cell(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            argv = [
                "--benchmark", "chi",
                "--historical-version", "1.3.45",
                "--historical-bugs", str(CHI_1_3_45_BUGS),
                "--current-bugs", str(CHI_1_3_45_BUGS),
                "--bug-id", "all",
                "--output-dir", str(output_dir),
                "--run-timestamp", "20260501T000000Z",
                "--notes", "Phase 5 smoke test cell.",
            ]
            rc = rr.main(argv)
            self.assertEqual(rc, 0)
            cell_path = output_dir / "20260501T000000Z" / "chi-1.3.45-all.json"
            self.assertTrue(cell_path.is_file())
            cell = json.loads(cell_path.read_text(encoding="utf-8"))
            # Smoke contract: every required SCHEMA.md field appears,
            # recall is 1.0 (self-match), and the schema_version is v1.5.4.
            self.assertEqual(cell["schema_version"], "1.5.4")
            self.assertEqual(cell["benchmark"], "chi")
            self.assertEqual(cell["historical_qpb_version"], "1.3.45")
            self.assertEqual(cell["historical_bug_id"], "all")
            self.assertEqual(cell["historical_bug_count"], 10)
            self.assertEqual(cell["current_bug_count"], 10)
            self.assertEqual(cell["recall_against_historical"], 1.0)
            self.assertEqual(len(cell["recovered_bug_ids"]), 10)
            self.assertEqual(cell["missed_bug_ids"], [])


class CliValidationTests(unittest.TestCase):
    """Council 2026-04-30 P1-1: --runner argparse validation must
    reject typos rather than silently dispatching to the default
    --copilot fallback."""

    def test_runner_typo_rejected_by_argparse(self) -> None:
        parser = rr._build_parser()
        # argparse calls sys.exit(2) on choices= violation.
        with self.assertRaises(SystemExit):
            parser.parse_args([
                "--benchmark", "chi",
                "--historical-version", "1.3.45",
                "--historical-bugs", "/tmp/h.md",
                "--current-bugs", "/tmp/c.md",
                "--runner", "cursr",  # typo
            ])

    def test_all_four_supported_runners_accepted(self) -> None:
        parser = rr._build_parser()
        for runner in ("claude", "copilot", "codex", "cursor"):
            args = parser.parse_args([
                "--benchmark", "chi",
                "--historical-version", "1.3.45",
                "--historical-bugs", "/tmp/h.md",
                "--current-bugs", "/tmp/c.md",
                "--runner", runner,
            ])
            self.assertEqual(args.runner, runner)


class InvokeRunnerExitCodeTests(unittest.TestCase):
    """Council 2026-04-30 P1-2: a non-zero runner exit must abort the
    cell write rather than producing a cell against a stale BUGS.md."""

    def test_invoke_runner_returns_returncode(self) -> None:
        from unittest import mock
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=42)
            result = rr._invoke_runner(
                Path("/tmp/target"), "1,2,3", "claude", ""
            )
        self.assertEqual(result.returncode, 42)
        self.assertIsInstance(result.wall_clock_seconds, int)

    def test_main_aborts_on_runner_failure(self) -> None:
        from unittest import mock
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            (target / "quality").mkdir(parents=True)
            (target / "quality" / "BUGS.md").write_text(
                "### BUG-001: existing\n- **Requirement:** REQ-1\n- **File:** `a.go:1`\n",
                encoding="utf-8",
            )
            output_dir = Path(tmp) / "out"
            with mock.patch.object(rr, "_invoke_runner") as mock_inv:
                mock_inv.return_value = rr.RunnerInvocationResult(
                    returncode=99, wall_clock_seconds=5
                )
                rc = rr.main([
                    "--benchmark", "chi",
                    "--historical-version", "1.3.45",
                    "--historical-bugs", str(target / "quality" / "BUGS.md"),
                    "--target-dir", str(target),
                    "--invoke-runner",
                    "--output-dir", str(output_dir),
                ])
            # Should propagate the non-zero exit, not return 0.
            self.assertEqual(rc, 99)
            # No cell written.
            self.assertFalse(list(output_dir.rglob("*.json")))


class QpbVersionFieldSourceTests(unittest.TestCase):
    """Council 2026-04-30 P2-1: qpb_version_under_test must come from
    bin/benchmark_lib.RELEASE_VERSION per SCHEMA.md, not from
    SKILL.md via detect_skill_version (separate source of truth)."""

    def test_cell_record_qpb_version_matches_release_version(self) -> None:
        from bin import benchmark_lib
        with TemporaryDirectory() as tmp:
            inputs = rr.CellInputs(
                benchmark="chi",
                historical_qpb_version="1.3.45",
                historical_bug_id="all",
                historical_path=Path(tmp) / "h.md",
                current_path=Path(tmp) / "c.md",
                target_dir=None,
                qpb_dir=Path(tmp),  # empty dir → no SKILL.md visible
            )
            measurement = rr.measure_recall([], [])
            record = rr.build_cell_record(inputs, measurement)
        self.assertEqual(
            record["qpb_version_under_test"],
            benchmark_lib.RELEASE_VERSION,
            "qpb_version_under_test must come from RELEASE_VERSION "
            "(SCHEMA.md contract), not detect_skill_version fallbacks",
        )


if __name__ == "__main__":
    unittest.main()
