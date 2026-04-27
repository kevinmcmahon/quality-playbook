"""Phase 4 Part F.2 integration fixture: Hybrid prose-to-code
divergence.

A tmpdir with a synthetic pass_c_formal.jsonl + a synthetic
quality_gate.py-shaped Python file. SKILL.md prose REQ claims '45
checks'; the synthetic quality_gate.py defines 43 def check_*
functions. Verifies Part A.2 (mechanical) emits exactly 1
divergence with claimed_count=45, actual_count=43, and the right
provisional_disposition."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin.skill_derivation.divergence_prose_to_code_mechanical import (
    ProseToCodeMechanicalConfig,
    run_divergence_prose_to_code_mechanical,
)


class Phase4F2IntegrationTests(unittest.TestCase):
    def test_45_vs_43_checks_emits_one_mechanical_divergence(self):
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            # Synthesize the gate file at the path the mechanical
            # token resolver expects.
            gate_dir = tmp / ".github" / "skills" / "quality_gate"
            gate_dir.mkdir(parents=True)
            (gate_dir / "quality_gate.py").write_text(
                "\n".join(
                    f"def check_thing_{i}():\n    pass\n" for i in range(43)
                ),
                encoding="utf-8",
            )
            formal = tmp / "pass_c_formal.jsonl"
            formal.write_text(
                json.dumps({
                    "id": "REQ-PHASE3-001",
                    "section_idx": 1,
                    "source_document": "SKILL.md",
                    "citation_excerpt":
                        "the quality gate runs 45 checks against the manifest",
                }) + "\n",
                encoding="utf-8",
            )
            sections = tmp / "pass_a_sections.json"
            sections.write_text(json.dumps({
                "sections": [{
                    "section_idx": 1, "document": "SKILL.md",
                    "heading": "Quality Gate Overview",
                    "line_start": 1, "line_end": 5,
                }],
            }), encoding="utf-8")
            cfg = ProseToCodeMechanicalConfig(
                formal_path=formal,
                output_path=tmp / "pass_e_p2c.jsonl",
                repo_root=tmp,
                sections_path=sections,
            )
            result = run_divergence_prose_to_code_mechanical(cfg)
            self.assertEqual(result["divergences_emitted"], 1)
            recs = [
                json.loads(line)
                for line in cfg.output_path.read_text().splitlines()
                if line.strip()
            ]
            self.assertEqual(len(recs), 1)
            r = recs[0]
            self.assertEqual(r["claimed_count"], 45)
            self.assertEqual(r["actual_count"], 43)
            self.assertEqual(r["provisional_disposition"], "code-fix")
            self.assertIn("Quality Gate Overview", r["section_heading"])


if __name__ == "__main__":
    unittest.main()
