"""Tests for bin/classify_project.py (QPB v1.5.3 Phase 1)."""

from __future__ import annotations

import json
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from bin import classify_project as cp


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "classify_project"
CODE_FIXTURE = FIXTURE_ROOT / "code_fixture"
SKILL_FIXTURE = FIXTURE_ROOT / "skill_fixture"
HYBRID_FIXTURE = FIXTURE_ROOT / "hybrid_fixture"


# ---------------------------------------------------------------------------
# Schema validation helper -- mirrors the JSON shape documented in
# QPB_v1.5.3_Phase1_Brief.md "Deliverables -> 2. quality/project_type.json".
# ---------------------------------------------------------------------------


_TOP_LEVEL_KEYS = {
    "schema_version",
    "classification",
    "rationale",
    "confidence",
    "evidence",
    "classified_at",
    "classifier_version",
    "override_applied",
    "override_rationale",
}

_EVIDENCE_KEYS = {
    "skill_md_present",
    "skill_md_path",
    "skill_md_word_count",
    "total_code_loc",
    "code_languages",
}


def _assert_record_matches_schema(test_case: unittest.TestCase, record: dict) -> None:
    test_case.assertEqual(set(record.keys()), _TOP_LEVEL_KEYS)
    test_case.assertEqual(record["schema_version"], cp.SCHEMA_VERSION)
    test_case.assertIn(record["classification"], cp.VALID_CLASSIFICATIONS)
    test_case.assertIn(record["confidence"], cp.VALID_CONFIDENCES)
    test_case.assertIsInstance(record["rationale"], str)
    test_case.assertGreater(len(record["rationale"]), 0)
    test_case.assertEqual(record["classifier_version"], cp.CLASSIFIER_VERSION)
    test_case.assertIsInstance(record["override_applied"], bool)

    evidence = record["evidence"]
    test_case.assertEqual(set(evidence.keys()), _EVIDENCE_KEYS)
    test_case.assertIsInstance(evidence["skill_md_present"], bool)
    if evidence["skill_md_present"]:
        test_case.assertIsInstance(evidence["skill_md_path"], str)
        # C.2 invariant: skill_md_path is repo-relative (POSIX-style),
        # never absolute, so the JSON record is portable across machines.
        test_case.assertFalse(
            Path(evidence["skill_md_path"]).is_absolute(),
            f"skill_md_path must be repo-relative; got {evidence['skill_md_path']!r}",
        )
        test_case.assertIsInstance(evidence["skill_md_word_count"], int)
        test_case.assertGreaterEqual(evidence["skill_md_word_count"], 0)
    else:
        test_case.assertIsNone(evidence["skill_md_path"])
        test_case.assertIsNone(evidence["skill_md_word_count"])
    test_case.assertIsInstance(evidence["total_code_loc"], int)
    test_case.assertGreaterEqual(evidence["total_code_loc"], 0)
    test_case.assertIsInstance(evidence["code_languages"], list)
    for lang in evidence["code_languages"]:
        test_case.assertIsInstance(lang, str)

    # ISO-8601 UTC, parseable.
    timestamp = record["classified_at"]
    test_case.assertTrue(timestamp.endswith("Z"))
    datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")

    if record["override_applied"]:
        test_case.assertIsInstance(record["override_rationale"], str)
        test_case.assertGreater(len(record["override_rationale"]), 0)
    else:
        test_case.assertIsNone(record["override_rationale"])


# ---------------------------------------------------------------------------
# Fixture-based classification tests
# ---------------------------------------------------------------------------


class FixtureClassificationTests(unittest.TestCase):
    def test_code_fixture_classifies_as_code(self) -> None:
        record = cp.classify_project(CODE_FIXTURE)
        self.assertEqual(record["classification"], "Code")
        self.assertFalse(record["evidence"]["skill_md_present"])
        self.assertGreater(record["evidence"]["total_code_loc"], 0)
        self.assertIn("Python", record["evidence"]["code_languages"])
        _assert_record_matches_schema(self, record)

    def test_skill_fixture_classifies_as_skill(self) -> None:
        record = cp.classify_project(SKILL_FIXTURE)
        self.assertEqual(record["classification"], "Skill")
        self.assertTrue(record["evidence"]["skill_md_present"])
        self.assertGreater(record["evidence"]["skill_md_word_count"], 0)
        self.assertEqual(record["evidence"]["total_code_loc"], 0)
        _assert_record_matches_schema(self, record)

    def test_hybrid_fixture_classifies_as_hybrid(self) -> None:
        record = cp.classify_project(HYBRID_FIXTURE)
        self.assertEqual(record["classification"], "Hybrid")
        self.assertTrue(record["evidence"]["skill_md_present"])
        self.assertGreater(record["evidence"]["skill_md_word_count"], 0)
        self.assertGreater(record["evidence"]["total_code_loc"], 0)
        self.assertIn("Python", record["evidence"]["code_languages"])
        _assert_record_matches_schema(self, record)


# ---------------------------------------------------------------------------
# Edge cases (synthesized at runtime; brief-mandated coverage)
# ---------------------------------------------------------------------------


class EdgeCaseTests(unittest.TestCase):
    def test_empty_directory_classifies_as_code_low_confidence(self) -> None:
        with TemporaryDirectory() as tmp:
            record = cp.classify_project(Path(tmp))
        self.assertEqual(record["classification"], "Code")
        self.assertEqual(record["confidence"], "low")
        self.assertFalse(record["evidence"]["skill_md_present"])
        self.assertEqual(record["evidence"]["total_code_loc"], 0)
        self.assertEqual(record["evidence"]["code_languages"], [])
        _assert_record_matches_schema(self, record)

    def test_empty_skill_md_classifies_as_hybrid_low_confidence(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SKILL.md").write_text("", encoding="utf-8")
            # Add some code so the fall-through doesn't trip on zero LOC.
            (root / "main.py").write_text(
                "def hello():\n    return 'hi'\n", encoding="utf-8"
            )
            record = cp.classify_project(root)
        self.assertEqual(record["classification"], "Hybrid")
        self.assertEqual(record["confidence"], "low")
        self.assertTrue(record["evidence"]["skill_md_present"])
        self.assertEqual(record["evidence"]["skill_md_word_count"], 0)
        _assert_record_matches_schema(self, record)

    def test_massive_code_with_skill_md_classifies_as_hybrid(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SKILL.md").write_text(
                "# Skill\n\nA short skill description.\n", encoding="utf-8"
            )
            # Generate a chunk of code: more than 2x the SKILL.md word count
            # so the heuristic lands in the high-confidence Hybrid band.
            code_lines = "\n".join(f"x{i} = {i}" for i in range(500))
            (root / "big_module.py").write_text(code_lines + "\n", encoding="utf-8")
            record = cp.classify_project(root)
        self.assertEqual(record["classification"], "Hybrid")
        self.assertEqual(record["confidence"], "high")
        self.assertGreater(record["evidence"]["total_code_loc"], 100)
        _assert_record_matches_schema(self, record)

    def test_prose_heavy_non_skill_file_at_root_still_classifies_as_code(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Lots of prose, but not in SKILL.md -- classifier only checks
            # for SKILL.md by exact name at repo root.
            (root / "README.md").write_text(
                ("This is a long README. " * 200) + "\n", encoding="utf-8"
            )
            (root / "INSTRUCTIONS.md").write_text(
                ("Step-by-step prose. " * 100) + "\n", encoding="utf-8"
            )
            # Some code so it's not a totally empty target.
            (root / "tool.py").write_text(
                "\n".join(f"def fn_{i}(): return {i}" for i in range(60)) + "\n",
                encoding="utf-8",
            )
            record = cp.classify_project(root)
        self.assertEqual(record["classification"], "Code")
        self.assertFalse(record["evidence"]["skill_md_present"])
        _assert_record_matches_schema(self, record)

    def test_skill_md_in_subdirectory_classifies_as_code(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            sub = root / "docs"
            sub.mkdir()
            # SKILL.md exists, but NOT at repo root -- classifier should
            # ignore it. Default behavior is non-recursive on this signal.
            (sub / "SKILL.md").write_text(
                "# Misplaced skill prose\n\n" + ("words " * 500), encoding="utf-8"
            )
            (root / "tool.py").write_text(
                "\n".join(f"def fn_{i}(): return {i}" for i in range(60)) + "\n",
                encoding="utf-8",
            )
            record = cp.classify_project(root)
        self.assertEqual(record["classification"], "Code")
        self.assertFalse(record["evidence"]["skill_md_present"])
        _assert_record_matches_schema(self, record)

    def test_pure_skill_with_no_code_classifies_high_confidence(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SKILL.md").write_text(
                "# Skill\n\n" + ("prose words " * 200) + "\n", encoding="utf-8"
            )
            record = cp.classify_project(root)
        self.assertEqual(record["classification"], "Skill")
        self.assertEqual(record["confidence"], "high")
        self.assertEqual(record["evidence"]["total_code_loc"], 0)
        _assert_record_matches_schema(self, record)


# ---------------------------------------------------------------------------
# Override mechanism
# ---------------------------------------------------------------------------


class OverrideTests(unittest.TestCase):
    def test_override_supersedes_heuristic_and_marks_record(self) -> None:
        record = cp.classify_project(
            CODE_FIXTURE,
            override="Skill",
            override_rationale="Council decided the operator's use case is skill-shaped.",
        )
        self.assertEqual(record["classification"], "Skill")
        self.assertTrue(record["override_applied"])
        self.assertEqual(record["confidence"], "high")
        self.assertIsNotNone(record["override_rationale"])
        # The heuristic's evidence is preserved even though the
        # classification is overridden.
        self.assertFalse(record["evidence"]["skill_md_present"])
        self.assertGreater(record["evidence"]["total_code_loc"], 0)
        # The rationale string mentions both the override and the heuristic
        # finding so reviewers can see why the override happened.
        self.assertIn("Override", record["rationale"])
        self.assertIn("Code", record["rationale"])
        _assert_record_matches_schema(self, record)

    def test_override_without_rationale_raises(self) -> None:
        with self.assertRaises(ValueError):
            cp.classify_project(CODE_FIXTURE, override="Skill")

    def test_override_with_invalid_value_raises(self) -> None:
        with self.assertRaises(ValueError):
            cp.classify_project(
                CODE_FIXTURE,
                override="Other",
                override_rationale="not a real category",
            )

    def test_no_override_records_false(self) -> None:
        record = cp.classify_project(CODE_FIXTURE)
        self.assertFalse(record["override_applied"])
        self.assertIsNone(record["override_rationale"])


# ---------------------------------------------------------------------------
# JSON writer
# ---------------------------------------------------------------------------


class WriterTests(unittest.TestCase):
    def test_write_creates_quality_dir_and_json_validates(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            record = cp.classify_project(CODE_FIXTURE)  # arbitrary valid record
            out_path = cp.write_classification(root, record)
            # write_classification resolves the target_dir for the atomic
            # write, so compare on the resolved form (matters on macOS where
            # /var symlinks to /private/var).
            self.assertEqual(out_path, (root / "quality" / "project_type.json").resolve())
            self.assertTrue(out_path.is_file())
            loaded = json.loads(out_path.read_text(encoding="utf-8"))
            _assert_record_matches_schema(self, loaded)
            self.assertEqual(loaded["classification"], record["classification"])

    def test_write_overwrites_existing_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "quality").mkdir()
            (root / "quality" / "project_type.json").write_text(
                "stale content", encoding="utf-8"
            )
            record = cp.classify_project(CODE_FIXTURE)
            cp.write_classification(root, record)
            loaded = json.loads(
                (root / "quality" / "project_type.json").read_text(encoding="utf-8")
            )
            self.assertEqual(loaded["classification"], record["classification"])

    def test_write_no_tmp_file_left_behind(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            record = cp.classify_project(CODE_FIXTURE)
            cp.write_classification(root, record)
            entries = sorted(p.name for p in (root / "quality").iterdir())
            self.assertEqual(entries, ["project_type.json"])


# ---------------------------------------------------------------------------
# Internal helpers (worth exercising directly because the brief calls out
# the heuristic as overridable; tests pin the boundary cases)
# ---------------------------------------------------------------------------


class HeuristicTests(unittest.TestCase):
    def test_no_skill_md_with_substantial_code_is_code_high(self) -> None:
        cls, _, conf = cp._apply_heuristic(
            skill_md_present=False, skill_md_word_count=None, total_code_loc=5000
        )
        self.assertEqual(cls, "Code")
        self.assertEqual(conf, "high")

    def test_no_skill_md_with_tiny_code_is_code_medium(self) -> None:
        cls, _, conf = cp._apply_heuristic(
            skill_md_present=False, skill_md_word_count=None, total_code_loc=10
        )
        self.assertEqual(cls, "Code")
        self.assertEqual(conf, "medium")

    def test_no_skill_md_no_code_is_code_low(self) -> None:
        cls, _, conf = cp._apply_heuristic(
            skill_md_present=False, skill_md_word_count=None, total_code_loc=0
        )
        self.assertEqual(cls, "Code")
        self.assertEqual(conf, "low")

    def test_skill_md_dominant_prose_is_skill_high(self) -> None:
        cls, _, conf = cp._apply_heuristic(
            skill_md_present=True, skill_md_word_count=10000, total_code_loc=100
        )
        self.assertEqual(cls, "Skill")
        self.assertEqual(conf, "high")

    def test_skill_md_moderate_dominant_prose_is_skill_medium(self) -> None:
        # C.3 polish: ratio between SKILL_DOMINANCE_RATIO (2.0) and
        # SKILL_HIGH_CONFIDENCE_RATIO (5.0) lands in the medium-confidence
        # Skill band. 3000 / 1000 = 3.0x, well inside the band.
        cls, _, conf = cp._apply_heuristic(
            skill_md_present=True, skill_md_word_count=3000, total_code_loc=1000
        )
        self.assertEqual(cls, "Skill")
        self.assertEqual(conf, "medium")

    def test_skill_md_dominant_code_is_hybrid_high(self) -> None:
        cls, _, conf = cp._apply_heuristic(
            skill_md_present=True, skill_md_word_count=200, total_code_loc=10000
        )
        self.assertEqual(cls, "Hybrid")
        self.assertEqual(conf, "high")

    def test_skill_md_balanced_is_hybrid_medium(self) -> None:
        cls, _, conf = cp._apply_heuristic(
            skill_md_present=True, skill_md_word_count=1000, total_code_loc=800
        )
        self.assertEqual(cls, "Hybrid")
        self.assertEqual(conf, "medium")

    def test_qpb_self_classifies_as_hybrid(self) -> None:
        # Acceptance-gate item: QPB itself classifies as Hybrid. This guards
        # against a future calibration drift that would silently flip QPB
        # into a different bucket.
        qpb_root = Path(__file__).resolve().parents[2]
        record = cp.classify_project(qpb_root)
        self.assertEqual(record["classification"], "Hybrid")
        self.assertTrue(record["evidence"]["skill_md_present"])
        self.assertGreater(record["evidence"]["total_code_loc"], 0)


if __name__ == "__main__":
    unittest.main()
