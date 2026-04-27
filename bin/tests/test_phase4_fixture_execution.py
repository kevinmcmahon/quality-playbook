"""Phase 4 Part F.3 integration fixture: execution-divergence on
synthetic previous_runs/.

A tmpdir with a synthetic previous_runs/ directory containing 5
archived runs (3 fail, 2 pass on the same gate check) plus a
pass_c_formal.jsonl with gate_check_ids POPULATED on the relevant
REQ — proving the machinery works when REQs carry the field. (QPB
itself has zero REQs with gate_check_ids per DQ-4-3.)"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin.skill_derivation.divergence_execution import (
    ExecutionDivergenceConfig,
    run_divergence_execution,
)


def _seed_run(prev_runs: Path, run_id: str, status: str) -> None:
    log_dir = prev_runs / run_id / "quality" / "results"
    log_dir.mkdir(parents=True, exist_ok=True)
    if status == "fail":
        (log_dir / "quality-gate.log").write_text(
            "  FAIL: `phase1_finding_count` failed (count=4 < 8)\n",
            encoding="utf-8",
        )
    else:
        (log_dir / "quality-gate.log").write_text(
            "  PASS: `phase1_finding_count` count >= 8\n",
            encoding="utf-8",
        )


class Phase4F3IntegrationTests(unittest.TestCase):
    def test_5_runs_3_fails_emits_high_confidence_execution_divergence(self):
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            prev = tmp / "previous_runs"
            for run_id, status in [
                ("run-2026-03-01", "fail"),
                ("run-2026-03-15", "fail"),
                ("run-2026-04-01", "fail"),
                ("run-2026-04-15", "pass"),
                ("run-2026-04-22", "pass"),
            ]:
                _seed_run(prev, run_id, status)
            formal = tmp / "pass_c_formal.jsonl"
            formal.write_text(
                json.dumps({
                    "id": "REQ-PHASE3-001",
                    "section_idx": 7,
                    "source_document": "SKILL.md",
                    "gate_check_ids": ["phase1_finding_count"],
                    "citation_excerpt": "Phase 1 must produce ≥8 findings",
                }) + "\n",
                encoding="utf-8",
            )
            sections = tmp / "pass_a_sections.json"
            sections.write_text(json.dumps({
                "sections": [{
                    "section_idx": 7, "document": "SKILL.md",
                    "heading": "Phase 1 Output",
                    "line_start": 1, "line_end": 5,
                }],
            }), encoding="utf-8")
            cfg = ExecutionDivergenceConfig(
                formal_path=formal,
                previous_runs_dir=prev,
                output_path=tmp / "pass_e_exec.jsonl",
                sections_path=sections,
            )
            result = run_divergence_execution(cfg)
            self.assertEqual(result["divergences_emitted"], 1)
            recs = [
                json.loads(line)
                for line in cfg.output_path.read_text().splitlines()
                if line.strip()
            ]
            self.assertEqual(len(recs), 1)
            r = recs[0]
            self.assertEqual(r["confidence"], "high")
            self.assertEqual(r["fail_count"], 3)
            self.assertEqual(r["total_runs_considered"], 5)
            self.assertEqual(r["provisional_disposition"], "code-fix")
            self.assertEqual(r["req_id"], "REQ-PHASE3-001")
            self.assertEqual(
                set(r["failed_run_ids"]),
                {"run-2026-03-01", "run-2026-03-15", "run-2026-04-01"},
            )


if __name__ == "__main__":
    unittest.main()
