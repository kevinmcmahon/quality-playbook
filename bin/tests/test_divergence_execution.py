"""Tests for bin/skill_derivation/divergence_execution.py and
execution_gate_loader.py — Phase 4 Part B (execution divergence)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin.skill_derivation.execution_gate_loader import (
    GateResult,
    load_archived_runs,
)
from bin.skill_derivation.divergence_execution import (
    ExecutionDivergenceConfig,
    run_divergence_execution,
)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def _write_sections(path: Path, sections: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"sections": sections}), encoding="utf-8")


def _read_output(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _seed_run(prev_runs: Path, run_id: str, check_lines: list[str]) -> None:
    """Write a synthetic gate log under previous_runs/<run_id>/quality/results/."""
    log_dir = prev_runs / run_id / "quality" / "results"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "quality-gate.log").write_text(
        "\n".join(check_lines) + "\n", encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Loader tests.
# ---------------------------------------------------------------------------


class GateLoaderTests(unittest.TestCase):
    def test_missing_dir_returns_empty(self) -> None:
        self.assertEqual(load_archived_runs(None), {})
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str) / "nope"
            self.assertEqual(load_archived_runs(tmp), {})

    def test_loads_pass_and_fail_markers(self) -> None:
        with TemporaryDirectory() as tmp_str:
            prev = Path(tmp_str) / "previous_runs"
            _seed_run(prev, "run-2026-04-01", [
                "  PASS: `phase1_finding_count` count >= 8",
                "  FAIL: `phase1_finding_count` failed",
            ])
            archived = load_archived_runs(prev)
            self.assertIn("run-2026-04-01", archived)
            results = archived["run-2026-04-01"]
            self.assertIn("phase1_finding_count", results)
            # Last marker wins -- this run's final state is FAIL.
            self.assertEqual(
                results["phase1_finding_count"].status, "fail"
            )

    def test_json_gate_output(self) -> None:
        with TemporaryDirectory() as tmp_str:
            prev = Path(tmp_str) / "previous_runs"
            run_dir = prev / "run-2026-03-22" / "quality" / "results"
            run_dir.mkdir(parents=True)
            (run_dir / "quality_gate.json").write_text(
                json.dumps({"checks": [
                    {"check_id": "phase1_finding_count",
                     "status": "fail", "rationale": "5 < 8"},
                    {"check_id": "phase4_council",
                     "status": "pass", "rationale": "ok"},
                ]}),
                encoding="utf-8",
            )
            archived = load_archived_runs(prev)
            results = archived["run-2026-03-22"]
            self.assertEqual(results["phase1_finding_count"].status, "fail")
            self.assertEqual(results["phase4_council"].status, "pass")


# ---------------------------------------------------------------------------
# Aggregator tests.
# ---------------------------------------------------------------------------


class ExecutionAggregatorTests(unittest.TestCase):
    def test_5_runs_3_fails_emits_high_confidence(self) -> None:
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
                _seed_run(prev, run_id, [
                    f"  {'FAIL' if status == 'fail' else 'PASS'}: `phase1_finding_count` ok",
                ])
            formal = tmp / "pass_c_formal.jsonl"
            _write_jsonl(formal, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "gate_check_ids": ["phase1_finding_count"]},
            ])
            sections = tmp / "pass_a_sections.json"
            _write_sections(sections, [
                {"section_idx": 1, "document": "SKILL.md",
                 "heading": "Phase 1", "line_start": 1, "line_end": 5},
            ])
            cfg = ExecutionDivergenceConfig(
                formal_path=formal,
                previous_runs_dir=prev,
                output_path=tmp / "pass_e_exec.jsonl",
                sections_path=sections,
            )
            result = run_divergence_execution(cfg)
            recs = _read_output(cfg.output_path)
            self.assertEqual(len(recs), 1)
            r = recs[0]
            self.assertEqual(r["confidence"], "high")
            self.assertEqual(r["fail_count"], 3)
            self.assertEqual(r["provisional_disposition"], "code-fix")
            self.assertEqual(result["archived_runs_considered"], 5)

    def test_1_run_emits_low_confidence(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            prev = tmp / "previous_runs"
            _seed_run(prev, "run-2026-04-01", [
                "  FAIL: `phase1_finding_count` failed",
            ])
            formal = tmp / "pass_c_formal.jsonl"
            _write_jsonl(formal, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "gate_check_ids": ["phase1_finding_count"]},
            ])
            sections = tmp / "pass_a_sections.json"
            _write_sections(sections, [])
            cfg = ExecutionDivergenceConfig(
                formal_path=formal,
                previous_runs_dir=prev,
                output_path=tmp / "pass_e_exec.jsonl",
                sections_path=sections,
            )
            run_divergence_execution(cfg)
            recs = _read_output(cfg.output_path)
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0]["confidence"], "low")
            self.assertEqual(recs[0]["provisional_disposition"], "mis-read")

    def test_zero_runs_zero_output_no_error(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            formal = tmp / "pass_c_formal.jsonl"
            _write_jsonl(formal, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "gate_check_ids": ["phase1_finding_count"]},
            ])
            sections = tmp / "pass_a_sections.json"
            _write_sections(sections, [])
            cfg = ExecutionDivergenceConfig(
                formal_path=formal,
                previous_runs_dir=tmp / "previous_runs",
                output_path=tmp / "pass_e_exec.jsonl",
                sections_path=sections,
            )
            result = run_divergence_execution(cfg)
            self.assertEqual(result["divergences_emitted"], 0)
            self.assertEqual(_read_output(cfg.output_path), [])

    def test_reqs_without_gate_check_ids_skipped(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            prev = tmp / "previous_runs"
            _seed_run(prev, "run-2026-04-01", [
                "  FAIL: `phase1_finding_count` failed",
            ])
            formal = tmp / "pass_c_formal.jsonl"
            _write_jsonl(formal, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": "SKILL.md"},  # no gate_check_ids
                {"id": "REQ-PHASE3-002", "section_idx": 1,
                 "source_document": "SKILL.md", "gate_check_ids": []},
            ])
            sections = tmp / "pass_a_sections.json"
            _write_sections(sections, [])
            cfg = ExecutionDivergenceConfig(
                formal_path=formal,
                previous_runs_dir=prev,
                output_path=tmp / "pass_e_exec.jsonl",
                sections_path=sections,
            )
            result = run_divergence_execution(cfg)
            self.assertEqual(result["divergences_emitted"], 0)
            self.assertEqual(result["reqs_skipped_no_gate_check_ids"], 2)


if __name__ == "__main__":
    unittest.main()
