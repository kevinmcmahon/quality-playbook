"""Phase 4 Part F.1 integration fixture: skill internal-prose
contradiction.

A 4-REQ pass_c_formal.jsonl with 2 contradictory cross-section
countable claims. Verifies Part A.1's run_divergence_internal()
detects exactly 1 cross-section-countable divergence and the
emitted record's rationale contains both numeric values."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin.skill_derivation.divergence_internal import (
    InternalDivergenceConfig,
    run_divergence_internal,
)


class Phase4F1IntegrationTests(unittest.TestCase):
    def test_two_sections_with_45_vs_43_emits_one_cross_section_candidate(self):
        """Phase 5 Stage 1 (DQ-5-4): Stage 3 cross-section-countable
        matches now route to pass_e_internal_candidates.jsonl. Both
        excerpts cite quality_gate.py so prong 2 (shared artifact)
        is satisfied."""
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            formal = tmp / "pass_c_formal.jsonl"
            with formal.open("w", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "id": "REQ-PHASE3-001", "section_idx": 1,
                    "source_document": "SKILL.md",
                    "citation_excerpt":
                        "quality_gate.py runs 45 checks across artifacts",
                }) + "\n")
                fh.write(json.dumps({
                    "id": "REQ-PHASE3-002", "section_idx": 1,
                    "source_document": "SKILL.md",
                    "citation_excerpt": "the run is sequenced through 7 phases",
                }) + "\n")
                fh.write(json.dumps({
                    "id": "REQ-PHASE3-003", "section_idx": 5,
                    "source_document": "SKILL.md",
                    "citation_excerpt":
                        "quality_gate.py runs 43 checks today",
                }) + "\n")
                fh.write(json.dumps({
                    "id": "REQ-PHASE3-004", "section_idx": 5,
                    "source_document": "SKILL.md",
                    "citation_excerpt": "Phase 5 reconciliation completes verification",
                }) + "\n")
            ucs = tmp / "pass_c_formal_use_cases.jsonl"
            ucs.write_text("", encoding="utf-8")
            sections = tmp / "pass_a_sections.json"
            sections.write_text(json.dumps({
                "sections": [
                    {"section_idx": 1, "document": "SKILL.md",
                     "heading": "Gate Overview", "line_start": 1,
                     "line_end": 5},
                    {"section_idx": 5, "document": "SKILL.md",
                     "heading": "Quality Gate Detail",
                     "line_start": 50, "line_end": 60},
                ]
            }), encoding="utf-8")
            cfg = InternalDivergenceConfig(
                formal_path=formal,
                formal_use_cases_path=ucs,
                sections_path=sections,
                document_root=tmp,
                output_path=tmp / "pass_e_internal_divergences.jsonl",
            )
            result = run_divergence_internal(cfg)
            candidates_path = tmp / "pass_e_internal_candidates.jsonl"
            cands = [
                json.loads(line)
                for line in candidates_path.read_text().splitlines()
                if line.strip()
            ]
            cross = [
                r for r in cands
                if r["subtype"] == "cross-section-countable-candidate"
            ]
            self.assertEqual(len(cross), 1)
            r = cross[0]
            self.assertIn("45", r["rationale"])
            self.assertIn("43", r["rationale"])
            self.assertIn("quality_gate.py", r["shared_artifacts"])
            # Both REQs are referenced.
            self.assertIn(r["req_a_id"], ("REQ-PHASE3-001", "REQ-PHASE3-003"))
            self.assertIn(r["req_b_id"], ("REQ-PHASE3-001", "REQ-PHASE3-003"))


if __name__ == "__main__":
    unittest.main()
