"""Regression-replay SCHEMA.md prose-contract tests (v1.5.4 Phase 4).

The schema is a contract between three consumers:

1. ``bin/regression_replay.py`` (Phase 5) — writes cells.
2. ``Quality Playbook/Reviews/Lever_Calibration_Log.md`` (Phase 6+) —
   cites cells.
3. The cross-benchmark regression check (Phase 8) — reads cells to
   confirm a lever change didn't degrade unrelated benchmarks.

These tests pin the schema's load-bearing prose so a future edit
that drops a required field, renames a path-convention element, or
silently widens the type set fires before the apparatus drifts.

The tests do NOT validate cell records themselves — that's
``bin/regression_replay.py``'s job. These are coarse string-presence
assertions on the SCHEMA.md document.
"""

from __future__ import annotations

import unittest
from pathlib import Path


SCHEMA_MD = (
    Path(__file__).resolve().parents[2]
    / "metrics"
    / "regression_replay"
    / "SCHEMA.md"
)


def _read_schema_md() -> str:
    return SCHEMA_MD.read_text(encoding="utf-8")


class SchemaPresenceTests(unittest.TestCase):
    """File-presence contract: SCHEMA.md must live at the canonical
    path so ``bin/regression_replay.py`` can find it."""

    def test_schema_md_exists_at_canonical_path(self) -> None:
        self.assertTrue(
            SCHEMA_MD.is_file(),
            f"missing schema at {SCHEMA_MD}",
        )

    def test_schema_md_has_a_purpose_section(self) -> None:
        self.assertIn("## Purpose", _read_schema_md())


class FieldInventoryTests(unittest.TestCase):
    """Every required field from the v1.5.4 Implementation Plan
    Phase 4 work-items list must be documented in SCHEMA.md."""

    REQUIRED_FIELDS = (
        "schema_version",
        "timestamp",
        "benchmark",
        "qpb_version_under_test",
        "historical_qpb_version",
        "historical_bug_id",
        "historical_bug_count",
        "current_bug_count",
        "recall_against_historical",
        "lever_under_test",
        "lever_change_summary",
        "before_lever",
        "after_lever",
        "regression_check",
        "noise_floor_source",
    )

    def test_every_planned_field_documented(self) -> None:
        text = _read_schema_md()
        for field in self.REQUIRED_FIELDS:
            # Object fields (regression_check, apparatus) are
            # documented via their nested children — accept either
            # the bare backtick form or any documented child accessor.
            patterns = (f"`{field}`", f"`{field}.")
            found = any(p in text for p in patterns)
            self.assertTrue(
                found,
                f"SCHEMA.md missing documentation for required field {field!r}",
            )


class FilePathConventionTests(unittest.TestCase):
    """Phase 4 work-items name a specific path convention. Pin it
    here so the apparatus can't ship cells under an arbitrary layout
    without the schema changing first."""

    def test_documents_path_convention(self) -> None:
        text = _read_schema_md()
        self.assertIn(
            "metrics/regression_replay/<run_timestamp>/<benchmark>-<version>-<bug_id>.json",
            text,
        )

    def test_documents_run_timestamp_format(self) -> None:
        text = _read_schema_md()
        # The apparatus uses YYYYMMDDTHHMMSSZ to match the existing
        # quality/previous_runs/ archive convention.
        self.assertIn("YYYYMMDDTHHMMSSZ", text)

    def test_documents_all_bug_id_sentinel(self) -> None:
        """Cells that measure full-set recall use the literal `all`
        in place of a single BUG-NNN ID — pin this so the apparatus
        and the calibration log agree."""
        self.assertIn("`all`", _read_schema_md())


class CalibrationLogShapeTests(unittest.TestCase):
    """Phase 4 work-items require SCHEMA.md to define the
    calibration-log entry shape so the cells and the narrative align
    field-by-field."""

    def test_documents_calibration_log_section(self) -> None:
        text = _read_schema_md()
        self.assertIn("## Calibration log entry shape", text)

    def test_calibration_log_template_names_required_subsections(self) -> None:
        text = _read_schema_md()
        for header in (
            "**Symptom.**",
            "**Diagnosis.**",
            "**Lever pulled.**",
            "**Before / After.**",
            "**Verdict.**",
        ):
            self.assertIn(header, text)


class ExampleRecordTests(unittest.TestCase):
    """Gate criterion from Phase 4: SCHEMA.md ships with at least
    one example record demonstrating every field populated. Pin
    that example's presence and rough shape."""

    def test_example_record_present(self) -> None:
        text = _read_schema_md()
        # The example is fenced as ```json. Search for the literal
        # opening that anchors the example.
        self.assertIn('"schema_version": "1.5.4"', text)
        self.assertIn('"benchmark": "chi"', text)

    def test_example_demonstrates_lever_attribution_pair(self) -> None:
        """The example must show a populated `after_lever` pointer
        (the symmetry contract in field-reference prose claims
        before/after cells reference each other)."""
        text = _read_schema_md()
        self.assertIn("metrics/regression_replay/", text)
        self.assertIn('"after_lever":', text)


class VersioningDisciplineTests(unittest.TestCase):
    """Phase 4 deliverable freezes the field set for v1.5.4. Pin
    the versioning rules so future changes follow the documented
    discipline (additive → patch bump, breaking → minor bump)."""

    def test_documents_versioning_section(self) -> None:
        text = _read_schema_md()
        self.assertIn("## Versioning discipline", text)
        self.assertIn("v1.5.4.x patch", text)
        self.assertIn("v1.5.5+", text)


if __name__ == "__main__":
    unittest.main()
