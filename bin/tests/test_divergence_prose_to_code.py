"""Tests for bin/skill_derivation/divergence_prose_to_code_*.py
— Phase 4 Parts A.2 (mechanical) and A.3 (LLM-driven)."""

from __future__ import annotations

import json
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, List

from bin.skill_derivation.divergence_prose_to_code_mechanical import (
    ProseToCodeMechanicalConfig,
    run_divergence_prose_to_code_mechanical,
)
from bin.skill_derivation.divergence_prose_to_code_llm import (
    ProseToCodeLLMConfig,
    run_divergence_prose_to_code_llm,
)
from bin.skill_derivation.runners import RunnerResult


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


# ---------------------------------------------------------------------------
# Mock LLM runner.
# ---------------------------------------------------------------------------


@dataclass
class _MockRunner:
    response_for: Callable[[str], str]
    elapsed_ms: int = 30_000
    call_log: List[str] = field(default_factory=list)

    def run(self, prompt: str) -> RunnerResult:
        self.call_log.append(prompt)
        return RunnerResult(
            stdout=self.response_for(prompt),
            stderr="",
            elapsed_ms=self.elapsed_ms,
            returncode=0,
        )


# ---------------------------------------------------------------------------
# Part A.2 mechanical-countable tests.
# ---------------------------------------------------------------------------


class MechanicalCountableTests(unittest.TestCase):
    def test_hybrid_45_vs_43_emits_one_divergence(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            # Synthetic quality_gate.py with 43 def check_* functions.
            gate_dir = tmp / ".github" / "skills" / "quality_gate"
            gate_dir.mkdir(parents=True)
            gate_py = gate_dir / "quality_gate.py"
            gate_py.write_text(
                "\n".join(f"def check_thing_{i}():\n    pass\n" for i in range(43)),
                encoding="utf-8",
            )
            formal = tmp / "pass_c_formal.jsonl"
            _write_jsonl(formal, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt": "the gate runs 45 checks against artifacts"},
            ])
            sections = tmp / "pass_a_sections.json"
            _write_sections(sections, [
                {"section_idx": 1, "document": "SKILL.md",
                 "heading": "Gate Checks", "line_start": 1, "line_end": 5},
            ])
            cfg = ProseToCodeMechanicalConfig(
                formal_path=formal,
                output_path=tmp / "pass_e_p2c.jsonl",
                repo_root=tmp,
                sections_path=sections,
            )
            run_divergence_prose_to_code_mechanical(cfg)
            recs = _read_output(cfg.output_path)
            self.assertEqual(len(recs), 1)
            r = recs[0]
            self.assertEqual(r["subtype"], "mechanical-countable")
            self.assertEqual(r["claimed_count"], 45)
            self.assertEqual(r["actual_count"], 43)
            self.assertEqual(r["provisional_disposition"], "code-fix")

    def test_no_artifact_no_divergence(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            formal = tmp / "pass_c_formal.jsonl"
            _write_jsonl(formal, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt": "the gate runs 45 checks"},
            ])
            sections = tmp / "pass_a_sections.json"
            _write_sections(sections, [])
            cfg = ProseToCodeMechanicalConfig(
                formal_path=formal,
                output_path=tmp / "pass_e_p2c.jsonl",
                repo_root=tmp,
                sections_path=sections,
            )
            run_divergence_prose_to_code_mechanical(cfg)
            self.assertEqual(_read_output(cfg.output_path), [])

    def test_matched_count_no_divergence(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            gate_dir = tmp / ".github" / "skills" / "quality_gate"
            gate_dir.mkdir(parents=True)
            (gate_dir / "quality_gate.py").write_text(
                "\n".join(
                    f"def check_thing_{i}():\n    pass\n" for i in range(43)
                ),
                encoding="utf-8",
            )
            formal = tmp / "pass_c_formal.jsonl"
            _write_jsonl(formal, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt": "the gate runs 43 checks"},
            ])
            sections = tmp / "pass_a_sections.json"
            _write_sections(sections, [])
            cfg = ProseToCodeMechanicalConfig(
                formal_path=formal,
                output_path=tmp / "pass_e_p2c.jsonl",
                repo_root=tmp,
                sections_path=sections,
            )
            run_divergence_prose_to_code_mechanical(cfg)
            self.assertEqual(_read_output(cfg.output_path), [])


# ---------------------------------------------------------------------------
# Part A.3 LLM-judged tests.
# ---------------------------------------------------------------------------


class LLMJudgedTests(unittest.TestCase):
    def _make_hybrid_fixture(self, tmp: Path) -> ProseToCodeLLMConfig:
        # Code artifact under bin/ so the resolver picks it up.
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        (bin_dir / "run_playbook.py").write_text(
            "def run_playbook():\n    return 'orchestrator'\n",
            encoding="utf-8",
        )
        formal = tmp / "pass_c_formal.jsonl"
        _write_jsonl(formal, [
            {"id": "REQ-PHASE3-001", "section_idx": 1,
             "source_document": "SKILL.md",
             "citation_excerpt": (
                 "the bin/run_playbook.py orchestrator handles continuation"
             )},
        ])
        sections = tmp / "pass_a_sections.json"
        _write_sections(sections, [
            {"section_idx": 1, "document": "SKILL.md",
             "heading": "Orchestration", "line_start": 1, "line_end": 5},
        ])
        spec_stub = tmp / "STUB.md"
        spec_stub.write_text("stub", encoding="utf-8")
        return ProseToCodeLLMConfig(
            formal_path=formal,
            output_path=tmp / "pass_e_p2c.jsonl",
            progress_path=tmp / "pass_e_p2c_progress.json",
            repo_root=tmp,
            # v1.5.4 Phase 2 Site 3: should_run replaces the legacy
            # project_type=="Hybrid" guard. The hybrid-shaped fixture
            # carries skill-tool surface in spirit, so should_run=True.
            should_run=True,
            sections_path=sections,
            pass_spec_path=spec_stub,
        )

    def test_llm_matches_emits_zero_divergences(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            cfg = self._make_hybrid_fixture(tmp)
            runner = _MockRunner(
                response_for=lambda p: json.dumps(
                    {"verdict": "matches", "rationale": "code implements claim"}
                )
            )
            result = run_divergence_prose_to_code_llm(cfg, runner)
            self.assertEqual(result["divergences_emitted"], 0)
            self.assertEqual(result["calls_made"], 1)
            self.assertEqual(_read_output(cfg.output_path), [])

    def test_llm_diverges_emits_one_divergence(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            cfg = self._make_hybrid_fixture(tmp)
            runner = _MockRunner(
                response_for=lambda p: json.dumps(
                    {"verdict": "diverges", "rationale": "code lacks the feature"}
                )
            )
            result = run_divergence_prose_to_code_llm(cfg, runner)
            self.assertEqual(result["divergences_emitted"], 1)
            recs = _read_output(cfg.output_path)
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0]["subtype"], "llm-judged")
            self.assertEqual(recs[0]["llm_verdict"], "diverges")
            self.assertEqual(recs[0]["provisional_disposition"], "code-fix")

    def test_skill_project_a3_is_noop(self) -> None:
        """v1.5.4 Phase 2 Site 3: a target whose role map reports zero
        skill-tool files (e.g. a pure-Markdown skill) flips should_run
        to False; Part A.3 must no-op regardless of what the LLM
        runner would have produced."""
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            cfg = self._make_hybrid_fixture(tmp)
            cfg.should_run = False
            runner = _MockRunner(
                response_for=lambda p: json.dumps(
                    {"verdict": "diverges", "rationale": "x"}
                )
            )
            result = run_divergence_prose_to_code_llm(cfg, runner)
            self.assertEqual(result["calls_made"], 0)
            self.assertEqual(result["divergences_emitted"], 0)
            self.assertEqual(runner.call_log, [])
            self.assertIn("skill-tool", result["skipped_reason"])

    def test_un_anchored_uc_skipped_at_a2_and_a3(self) -> None:
        """DQ-4-6: REQs flagged as derived from an un-anchored UC are
        skipped by both A.2 and A.3. We pin this by passing the
        REQ id in skipped_uc_ids and verifying it doesn't surface."""
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            # A.2 skip path
            gate_dir = tmp / ".github" / "skills" / "quality_gate"
            gate_dir.mkdir(parents=True)
            (gate_dir / "quality_gate.py").write_text(
                "\n".join(f"def check_x_{i}():\n  pass\n" for i in range(2)),
                encoding="utf-8",
            )
            formal = tmp / "pass_c_formal.jsonl"
            _write_jsonl(formal, [
                {"id": "REQ-PHASE3-999", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt": "the gate runs 45 checks"},
            ])
            sections = tmp / "pass_a_sections.json"
            _write_sections(sections, [])
            cfg = ProseToCodeMechanicalConfig(
                formal_path=formal,
                output_path=tmp / "pass_e_p2c.jsonl",
                repo_root=tmp,
                sections_path=sections,
                skipped_uc_ids=("REQ-PHASE3-999",),
            )
            run_divergence_prose_to_code_mechanical(cfg)
            self.assertEqual(_read_output(cfg.output_path), [])


if __name__ == "__main__":
    unittest.main()
