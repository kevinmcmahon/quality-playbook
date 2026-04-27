"""Tests for bin/skill_derivation/divergence_to_bugs.py — Phase 4
Part D.1 (BUG record production) + Round 8 Finding 2 (§8.1
consolidation)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin.skill_derivation.divergence_to_bugs import (
    DivergenceToBugsConfig,
    run_divergence_to_bugs,
)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def _read_output(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class ConsolidationTests(unittest.TestCase):
    """Round 8 Finding 2: prose-to-code divergences sharing
    (code_artifact, claimed_count, actual_count, code_count_pattern)
    consolidate into a single BUG with a `covers` array per
    schemas.md §8.1."""

    def test_three_identical_p2c_divs_consolidate_into_one_bug(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            internal = tmp / "pass_e_internal_divergences.jsonl"
            p2c = tmp / "pass_e_prose_to_code_divergences.jsonl"
            execn = tmp / "pass_e_execution_divergences.jsonl"
            internal.write_text("", encoding="utf-8")
            execn.write_text("", encoding="utf-8")
            # 3 DIV-P2C records with IDENTICAL (code_artifact,
            # claimed_count, actual_count, code_count_pattern). They
            # come from 3 different REQs / sections — consolidation
            # should still collapse them.
            _write_jsonl(p2c, [
                {"divergence_id": "DIV-P2C-001",
                 "divergence_type": "prose-to-code",
                 "subtype": "mechanical-countable",
                 "req_id": "REQ-PHASE3-100",
                 "source_document": "SKILL.md",
                 "section_idx": 1, "section_heading": "S1",
                 "excerpt": "the gate runs 50 tests",
                 "claimed_count": 50, "actual_count": 631,
                 "code_artifact": "bin/tests/",
                 "code_count_pattern": r"^\s*def test_",
                 "provisional_disposition": "spec-fix",
                 "rationale": "claimed 50 vs actual 631",
                 "triage_batch_key": "SKILL.md::1"},
                {"divergence_id": "DIV-P2C-002",
                 "divergence_type": "prose-to-code",
                 "subtype": "mechanical-countable",
                 "req_id": "REQ-PHASE3-101",
                 "source_document": "SKILL.md",
                 "section_idx": 2, "section_heading": "S2",
                 "excerpt": "the gate runs 50 tests",
                 "claimed_count": 50, "actual_count": 631,
                 "code_artifact": "bin/tests/",
                 "code_count_pattern": r"^\s*def test_",
                 "provisional_disposition": "spec-fix",
                 "rationale": "claimed 50 vs actual 631",
                 "triage_batch_key": "SKILL.md::2"},
                {"divergence_id": "DIV-P2C-003",
                 "divergence_type": "prose-to-code",
                 "subtype": "mechanical-countable",
                 "req_id": "REQ-PHASE3-102",
                 "source_document": "SKILL.md",
                 "section_idx": 3, "section_heading": "S3",
                 "excerpt": "the gate runs 50 tests",
                 "claimed_count": 50, "actual_count": 631,
                 "code_artifact": "bin/tests/",
                 "code_count_pattern": r"^\s*def test_",
                 "provisional_disposition": "spec-fix",
                 "rationale": "claimed 50 vs actual 631",
                 "triage_batch_key": "SKILL.md::3"},
            ])
            cfg = DivergenceToBugsConfig(
                internal_path=internal,
                prose_to_code_path=p2c,
                execution_path=execn,
                output_path=tmp / "pass_e_bugs.jsonl",
            )
            result = run_divergence_to_bugs(cfg)
            bugs = _read_output(cfg.output_path)
            # Exactly one BUG, with covers listing all 3 DIV-P2C IDs.
            self.assertEqual(
                len(bugs), 1,
                f"expected 1 consolidated BUG, got {len(bugs)}: "
                f"{[b.get('bug_id') for b in bugs]}",
            )
            bug = bugs[0]
            self.assertIn("covers", bug)
            self.assertEqual(
                set(bug["covers"]),
                {"DIV-P2C-001", "DIV-P2C-002", "DIV-P2C-003"},
            )
            self.assertEqual(len(bug["covers"]), 3)
            self.assertIn("consolidation_rationale", bug)
            self.assertIn("§8.1", bug["consolidation_rationale"])
            # The driving (primary) req_id is the first divergence's
            # req_id; the other two REQs surface in secondary_req_ids.
            self.assertEqual(bug["req_id"], "REQ-PHASE3-100")
            self.assertEqual(
                set(bug.get("secondary_req_ids", [])),
                {"REQ-PHASE3-101", "REQ-PHASE3-102"},
            )
            # Summary counters reflect consolidation.
            self.assertEqual(result["prose_to_code_bugs"], 1)
            self.assertEqual(result["prose_to_code_divergences_in"], 3)
            self.assertEqual(result["prose_to_code_groups_consolidated"], 1)

    def test_two_distinct_p2c_tuples_emit_two_separate_bugs(self) -> None:
        """Sanity guard: divergences with DIFFERENT
        (code_artifact, claimed_count, actual_count, code_count_pattern)
        tuples must NOT consolidate."""
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            internal = tmp / "pass_e_internal_divergences.jsonl"
            p2c = tmp / "pass_e_prose_to_code_divergences.jsonl"
            execn = tmp / "pass_e_execution_divergences.jsonl"
            internal.write_text("", encoding="utf-8")
            execn.write_text("", encoding="utf-8")
            _write_jsonl(p2c, [
                {"divergence_id": "DIV-P2C-001",
                 "divergence_type": "prose-to-code",
                 "subtype": "mechanical-countable",
                 "req_id": "REQ-PHASE3-100",
                 "source_document": "SKILL.md",
                 "section_idx": 1, "section_heading": "S1",
                 "excerpt": "the gate runs 50 tests",
                 "claimed_count": 50, "actual_count": 631,
                 "code_artifact": "bin/tests/",
                 "code_count_pattern": r"^\s*def test_",
                 "provisional_disposition": "spec-fix",
                 "rationale": "x",
                 "triage_batch_key": "SKILL.md::1"},
                {"divergence_id": "DIV-P2C-002",
                 "divergence_type": "prose-to-code",
                 "subtype": "mechanical-countable",
                 "req_id": "REQ-PHASE3-200",
                 "source_document": "SKILL.md",
                 "section_idx": 5, "section_heading": "S5",
                 "excerpt": "the gate runs 45 checks",
                 "claimed_count": 45, "actual_count": 43,
                 "code_artifact": ".github/skills/quality_gate/quality_gate.py",
                 "code_count_pattern": r"^def check_",
                 "provisional_disposition": "code-fix",
                 "rationale": "y",
                 "triage_batch_key": "SKILL.md::5"},
            ])
            cfg = DivergenceToBugsConfig(
                internal_path=internal,
                prose_to_code_path=p2c,
                execution_path=execn,
                output_path=tmp / "pass_e_bugs.jsonl",
            )
            result = run_divergence_to_bugs(cfg)
            bugs = _read_output(cfg.output_path)
            self.assertEqual(len(bugs), 2)
            # Neither carries `covers` (single-divergence groups).
            for bug in bugs:
                self.assertNotIn("covers", bug)
                self.assertNotIn("consolidation_rationale", bug)
            self.assertEqual(result["prose_to_code_bugs"], 2)
            self.assertEqual(result["prose_to_code_groups_consolidated"], 0)


if __name__ == "__main__":
    unittest.main()
