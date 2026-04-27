"""Tests for bin/skill_derivation/pass_c.py — formal REQ + UC production."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin.skill_derivation import pass_c, protocol


def _write_project_type(tmp: Path, classification: str) -> Path:
    qd = tmp / "quality"
    qd.mkdir(parents=True, exist_ok=True)
    out = qd / "project_type.json"
    out.write_text(
        json.dumps({
            "schema_version": "1.1",
            "classification": classification,
            "rationale": "fixture",
            "confidence": "high",
            "evidence": {
                "skill_md_present": classification != "Code",
                "skill_md_path": "SKILL.md" if classification != "Code" else None,
                "skill_md_word_count": 1000 if classification != "Code" else None,
                "total_code_loc": 500 if classification != "Skill" else 0,
                "code_languages": [],
                "confidence_reason": "unambiguous",
            },
            "classified_at": "2026-04-27T00:00:00Z",
            "classifier_version": "1.0",
            "override_applied": False,
            "override_rationale": None,
        }),
        encoding="utf-8",
    )
    return out


def _write_pass_b_complete_progress(tmp: Path) -> Path:
    p3 = tmp / "phase3"
    p3.mkdir(parents=True, exist_ok=True)
    progress = p3 / "pass_b_progress.json"
    protocol.write_progress_atomic(
        progress,
        protocol.ProgressState(
            pass_="B", unit="draft", cursor=10, total=10,
            status="complete", last_updated="2026-04-27T00:00:00Z",
        ),
    )
    return progress


def _make_config(tmp: Path) -> pass_c.PassCConfig:
    p3 = tmp / "phase3"
    p3.mkdir(parents=True, exist_ok=True)
    return pass_c.PassCConfig(
        citations_path=p3 / "pass_b_citations.jsonl",
        uc_drafts_path=p3 / "pass_a_use_case_drafts.jsonl",
        formal_path=p3 / "pass_c_formal.jsonl",
        formal_use_cases_path=p3 / "pass_c_formal_use_cases.jsonl",
        progress_path=p3 / "pass_c_progress.json",
        pass_b_progress_path=p3 / "pass_b_progress.json",
        project_type_path=tmp / "quality" / "project_type.json",
    )


def _write_citations(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


class DispositionBranchTests(unittest.TestCase):
    """Each disposition branch from the 6-row table must produce
    output with the right tier / source_type / skill_section /
    disposition. Round 3 process gap: every record MUST populate
    source_type."""

    def _setup(self, tmp: Path, project_type: str = "Hybrid"):
        _write_project_type(tmp, project_type)
        _write_pass_b_complete_progress(tmp)
        return _make_config(tmp)

    def _read_formal(self, config) -> list[dict]:
        if not config.formal_path.is_file():
            return []
        return [
            json.loads(line)
            for line in config.formal_path.read_text().splitlines()
            if line.strip()
        ]

    def test_branch_1_verified_skill_md_to_tier_1(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            _write_citations(config.citations_path, [{
                "draft_idx": 0, "section_idx": 1, "_pass_b_idx": 0,
                "title": "x", "description": "y",
                "acceptance_criteria": "z", "proposed_source_ref": "Phase 1",
                "citation_status": "verified",
                "citation_excerpt": "verbatim text",
                "source_document": "SKILL.md",
                "similarity_score": 0.95,
            }])
            pass_c.run_pass_c(config)
            recs = self._read_formal(config)
            self.assertEqual(len(recs), 1)
            r = recs[0]
            self.assertEqual(r["tier"], 1)
            self.assertEqual(r["source_type"], "skill-section")
            self.assertEqual(r["disposition"], "accepted")
            self.assertIsNotNone(r["skill_section"])
            self.assertEqual(r["citation_excerpt"], "verbatim text")

    def test_branch_2_verified_reference_file_to_tier_2(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            _write_citations(config.citations_path, [{
                "draft_idx": 0, "section_idx": 5, "_pass_b_idx": 0,
                "title": "x", "description": "y",
                "acceptance_criteria": "z",
                "proposed_source_ref": "exploration_patterns.md",
                "citation_status": "verified",
                "citation_excerpt": "patterns text",
                "source_document": "references/exploration_patterns.md",
                "similarity_score": 0.85,
            }])
            pass_c.run_pass_c(config)
            recs = self._read_formal(config)
            r = recs[0]
            self.assertEqual(r["tier"], 2)
            self.assertEqual(r["source_type"], "reference-file")
            self.assertIsNone(r["skill_section"])
            self.assertEqual(r["disposition"], "accepted")

    def test_branch_3_unverified_structural_skill_md_to_council(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            _write_citations(config.citations_path, [{
                "draft_idx": 0, "section_idx": 1, "_pass_b_idx": 0,
                "title": "x", "description": "y",
                "acceptance_criteria": "z",
                "proposed_source_ref": "Phase 1 section",
                "citation_status": "unverified",
                "source_document": None,
            }])
            pass_c.run_pass_c(config)
            recs = self._read_formal(config)
            r = recs[0]
            # Structural near-miss: source_document is None but
            # proposed_source_ref names a section.
            self.assertEqual(r["tier"], 1)
            self.assertEqual(r["source_type"], "skill-section")
            self.assertEqual(r["disposition"], "needs-council-review")

    def test_branch_4_unverified_structural_reference_to_council(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            _write_citations(config.citations_path, [{
                "draft_idx": 0, "section_idx": 5, "_pass_b_idx": 0,
                "title": "x", "description": "y",
                "acceptance_criteria": "z",
                "proposed_source_ref": "exploration_patterns.md",
                "citation_status": "unverified",
                "source_document": "references/exploration_patterns.md",
                "similarity_score": 0.4,  # below threshold but search hit
            }])
            pass_c.run_pass_c(config)
            recs = self._read_formal(config)
            r = recs[0]
            self.assertEqual(r["tier"], 2)
            self.assertEqual(r["source_type"], "reference-file")
            self.assertIsNone(r["skill_section"])
            self.assertEqual(r["disposition"], "needs-council-review")

    def test_branch_5_unverified_behavioral_hybrid_to_tier_5(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp, project_type="Hybrid")
            _write_citations(config.citations_path, [{
                "draft_idx": 0, "section_idx": 1, "_pass_b_idx": 0,
                "title": "x", "description": "y",
                "acceptance_criteria": "behavioral claim no anchor",
                "proposed_source_ref": "",  # empty -> behavioral
                "citation_status": "unverified",
                "source_document": None,
            }])
            pass_c.run_pass_c(config)
            recs = self._read_formal(config)
            r = recs[0]
            self.assertEqual(r["tier"], 5)
            self.assertEqual(r["source_type"], "code-derived")
            self.assertIsNone(r["skill_section"])
            self.assertEqual(r["disposition"], "demoted-tier-5")

    def test_branch_6_unverified_behavioral_skill_to_council(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp, project_type="Skill")
            _write_citations(config.citations_path, [{
                "draft_idx": 0, "section_idx": 1, "_pass_b_idx": 0,
                "title": "x", "description": "y",
                "acceptance_criteria": "behavioral claim",
                "proposed_source_ref": "",
                "citation_status": "unverified",
                "source_document": None,
            }])
            pass_c.run_pass_c(config)
            recs = self._read_formal(config)
            r = recs[0]
            self.assertIsNone(r["tier"])  # provisional; Council assigns
            self.assertEqual(r["source_type"], "skill-section")
            self.assertEqual(r["disposition"], "needs-council-review")


class CriticalInvariantTests(unittest.TestCase):
    """Round 3 process gap + reserved-source-type invariants."""

    def _setup(self, tmp: Path, project_type: str = "Hybrid"):
        _write_project_type(tmp, project_type)
        _write_pass_b_complete_progress(tmp)
        return _make_config(tmp)

    def test_every_record_has_source_type_populated(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            # Mixture of all six branches in one citation file.
            _write_citations(config.citations_path, [
                # Branch 1
                {"draft_idx": 0, "section_idx": 1, "title": "a",
                 "description": "x", "acceptance_criteria": "y",
                 "proposed_source_ref": "Phase 1",
                 "citation_status": "verified",
                 "citation_excerpt": "vt", "source_document": "SKILL.md"},
                # Branch 2
                {"draft_idx": 1, "section_idx": 5, "title": "b",
                 "description": "x", "acceptance_criteria": "y",
                 "proposed_source_ref": "ref",
                 "citation_status": "verified",
                 "citation_excerpt": "rt",
                 "source_document": "references/x.md"},
                # Branch 3
                {"draft_idx": 2, "section_idx": 1, "title": "c",
                 "description": "x", "acceptance_criteria": "y",
                 "proposed_source_ref": "Phase 1",
                 "citation_status": "unverified", "source_document": None},
                # Branch 5 (Hybrid)
                {"draft_idx": 3, "section_idx": 1, "title": "d",
                 "description": "x", "acceptance_criteria": "y",
                 "proposed_source_ref": "",
                 "citation_status": "unverified", "source_document": None},
            ])
            pass_c.run_pass_c(config)
            recs = [
                json.loads(line)
                for line in config.formal_path.read_text().splitlines()
                if line.strip()
            ]
            self.assertEqual(len(recs), 4)
            for r in recs:
                self.assertIn("source_type", r)
                self.assertIsNotNone(r["source_type"])
                self.assertNotEqual(
                    r["source_type"], "execution-observation",
                    f"Pass C MUST NOT produce execution-observation; got {r}",
                )

    def test_skill_section_consistency(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            _write_citations(config.citations_path, [
                # Branch 1: skill-section -> non-empty skill_section
                {"draft_idx": 0, "section_idx": 1, "title": "a",
                 "description": "x", "acceptance_criteria": "y",
                 "proposed_source_ref": "Phase 1 section",
                 "citation_status": "verified",
                 "citation_excerpt": "vt", "source_document": "SKILL.md"},
                # Branch 2: reference-file -> skill_section is None
                {"draft_idx": 1, "section_idx": 5, "title": "b",
                 "description": "x", "acceptance_criteria": "y",
                 "proposed_source_ref": "ref",
                 "citation_status": "verified",
                 "citation_excerpt": "rt",
                 "source_document": "references/x.md"},
            ])
            pass_c.run_pass_c(config)
            recs = [
                json.loads(line)
                for line in config.formal_path.read_text().splitlines()
                if line.strip()
            ]
            for r in recs:
                if r["source_type"] == "skill-section":
                    self.assertIsNotNone(
                        r["skill_section"],
                        "skill-section source_type requires non-empty skill_section",
                    )
                    self.assertNotEqual(r["skill_section"], "")
                else:
                    self.assertIsNone(
                        r["skill_section"],
                        f"non-skill-section source_type {r['source_type']!r} "
                        f"requires skill_section to be None",
                    )


class ReqIdGenerationTests(unittest.TestCase):
    def test_req_ids_are_deterministic_and_zero_padded(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            _write_project_type(tmp, "Hybrid")
            _write_pass_b_complete_progress(tmp)
            config = _make_config(tmp)
            _write_citations(config.citations_path, [
                {"draft_idx": i, "section_idx": 1, "title": f"r{i}",
                 "description": "x", "acceptance_criteria": "y",
                 "proposed_source_ref": "Phase 1",
                 "citation_status": "verified",
                 "citation_excerpt": "vt", "source_document": "SKILL.md"}
                for i in range(3)
            ])
            pass_c.run_pass_c(config)
            recs = [
                json.loads(line)
                for line in config.formal_path.read_text().splitlines()
                if line.strip()
            ]
            ids = [r["id"] for r in recs]
            self.assertEqual(ids, ["REQ-PHASE3-001", "REQ-PHASE3-002", "REQ-PHASE3-003"])


class B4UpstreamGateTests(unittest.TestCase):
    def test_pass_c_refuses_when_pass_b_incomplete(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            _write_project_type(tmp, "Hybrid")
            # Pass B progress with status="running" -> Pass C must refuse.
            p3 = tmp / "phase3"
            p3.mkdir(parents=True, exist_ok=True)
            protocol.write_progress_atomic(
                p3 / "pass_b_progress.json",
                protocol.ProgressState(
                    pass_="B", unit="draft", cursor=2, total=10,
                    status="running", last_updated="2026-04-27T00:00:00Z",
                ),
            )
            config = _make_config(tmp)
            (p3 / "pass_b_citations.jsonl").write_text("", encoding="utf-8")
            with self.assertRaises(protocol.UpstreamIncompleteError) as cm:
                pass_c.run_pass_c(config)
            self.assertIn("Pass C refused to start", str(cm.exception))


class ProjectTypeFileTests(unittest.TestCase):
    def test_missing_project_type_raises(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            _write_pass_b_complete_progress(tmp)
            config = _make_config(tmp)
            (config.citations_path).parent.mkdir(parents=True, exist_ok=True)
            (config.citations_path).write_text("", encoding="utf-8")
            with self.assertRaises(FileNotFoundError) as cm:
                pass_c.run_pass_c(config)
            self.assertIn("classify_project", str(cm.exception))


class UCHandlingTests(unittest.TestCase):
    def test_uc_drafts_become_formal_uc_records(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            _write_project_type(tmp, "Hybrid")
            _write_pass_b_complete_progress(tmp)
            config = _make_config(tmp)
            (config.citations_path).parent.mkdir(parents=True, exist_ok=True)
            (config.citations_path).write_text("", encoding="utf-8")
            with config.uc_drafts_path.open("w", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "uc_draft_idx": 0, "section_idx": 4,
                    "title": "Operator runs Phase 1",
                    "actors": ["operator"],
                    "steps": ["invoke", "review"],
                    "trigger": "operator chooses to begin",
                    "acceptance": "EXPLORATION.md exists",
                    "proposed_source_ref": "Phase 1",
                }) + "\n")
            pass_c.run_pass_c(config)
            ucs = [
                json.loads(line)
                for line in config.formal_use_cases_path.read_text().splitlines()
                if line.strip()
            ]
            self.assertEqual(len(ucs), 1)
            uc = ucs[0]
            self.assertEqual(uc["uc_id"], "UC-PHASE3-01")
            self.assertTrue(uc["needs_council_review"])
            self.assertNotIn("citation", uc)
            self.assertNotIn("citation_excerpt", uc)
            self.assertEqual(uc["title"], "Operator runs Phase 1")


if __name__ == "__main__":
    unittest.main()
