"""Tests for bin/skill_derivation/pass_d.py — coverage audit + council inbox."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin.skill_derivation import pass_d, protocol, sections


def _setup_phase3_dir(tmp: Path) -> Path:
    p3 = tmp / "phase3"
    p3.mkdir(parents=True, exist_ok=True)
    return p3


def _write_pass_c_complete_progress(tmp: Path) -> Path:
    p3 = _setup_phase3_dir(tmp)
    progress = p3 / "pass_c_progress.json"
    protocol.write_progress_atomic(
        progress,
        protocol.ProgressState(
            pass_="C", unit="citation", cursor=10, total=10,
            status="complete", last_updated="2026-04-27T00:00:00Z",
        ),
    )
    return progress


def _make_config(tmp: Path) -> pass_d.PassDConfig:
    p3 = _setup_phase3_dir(tmp)
    return pass_d.PassDConfig(
        drafts_path=p3 / "pass_a_drafts.jsonl",
        uc_drafts_path=p3 / "pass_a_use_case_drafts.jsonl",
        formal_path=p3 / "pass_c_formal.jsonl",
        formal_use_cases_path=p3 / "pass_c_formal_use_cases.jsonl",
        sections_path=p3 / "pass_a_sections.json",
        audit_path=p3 / "pass_d_audit.json",
        section_coverage_path=p3 / "pass_d_section_coverage.json",
        council_inbox_path=p3 / "pass_d_council_inbox.json",
        progress_path=p3 / "pass_d_progress.json",
        pass_c_progress_path=p3 / "pass_c_progress.json",
    )


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def _write_sections_fixture(path: Path, sections_list: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({
            "schema_version": "1.1",
            "sections": sections_list,
        }),
        encoding="utf-8",
    )


def _basic_sections() -> list[dict]:
    return [
        {
            "section_idx": 0, "document": "SKILL.md",
            "heading": "Why This Exists", "heading_level": 2,
            "line_start": 1, "line_end": 5,
            "skip_reason": "meta-allowlist",
            "section_kind": "meta",
        },
        {
            "section_idx": 1, "document": "SKILL.md",
            "heading": "Phase 1: Explore", "heading_level": 2,
            "line_start": 6, "line_end": 30,
            "skip_reason": None,
            "section_kind": "execution-mode",
        },
        {
            "section_idx": 2, "document": "SKILL.md",
            "heading": "Cross-Cutting Invariants", "heading_level": 2,
            "line_start": 31, "line_end": 50,
            "skip_reason": None,
            "section_kind": "operational",
        },
        {
            "section_idx": 3, "document": "SKILL.md",
            "heading": "Forgotten Section", "heading_level": 2,
            "line_start": 51, "line_end": 60,
            "skip_reason": None,
            "section_kind": "operational",
        },
    ]


class DispositionClassificationTests(unittest.TestCase):
    def _setup(self, tmp: Path):
        _write_pass_c_complete_progress(tmp)
        config = _make_config(tmp)
        _write_sections_fixture(config.sections_path, _basic_sections())
        return config

    def test_promoted_rejected_demoted_classification(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            _write_jsonl(config.drafts_path, [
                {"draft_idx": 0, "section_idx": 1, "title": "p"},
                {"draft_idx": 1, "section_idx": 2, "title": "r"},
                {"draft_idx": 2, "section_idx": 2, "title": "d"},
            ])
            _write_jsonl(config.formal_path, [
                {"id": "REQ-PHASE3-001", "draft_idx": 0,
                 "tier": 1, "source_type": "skill-section",
                 "skill_section": "Phase 1: Explore",
                 "disposition": "accepted"},
                {"id": "REQ-PHASE3-002", "draft_idx": 1,
                 "tier": 1, "source_type": "skill-section",
                 "skill_section": "Cross-Cutting Invariants",
                 "disposition": "needs-council-review",
                 "council_review_rationale": "structural near miss"},
                {"id": "REQ-PHASE3-003", "draft_idx": 2,
                 "tier": 5, "source_type": "code-derived",
                 "skill_section": None,
                 "disposition": "demoted-tier-5",
                 "council_review_rationale": "no anchor"},
            ])
            summary = pass_d.run_pass_d(config)
            self.assertEqual(summary["promoted_count"], 1)
            self.assertEqual(summary["rejected_count"], 1)
            self.assertEqual(summary["demoted_count"], 1)
            audit = json.loads(config.audit_path.read_text())
            self.assertEqual(len(audit["promoted"]), 1)
            self.assertEqual(audit["promoted"][0]["req_id"], "REQ-PHASE3-001")
            self.assertEqual(len(audit["rejected"]), 1)
            self.assertEqual(audit["rejected"][0]["req_id"], "REQ-PHASE3-002")
            self.assertEqual(len(audit["demoted_to_tier_5"]), 1)


class SectionCoverageTests(unittest.TestCase):
    def _setup(self, tmp: Path):
        _write_pass_c_complete_progress(tmp)
        config = _make_config(tmp)
        _write_sections_fixture(config.sections_path, _basic_sections())
        return config

    def test_meta_section_appears_in_report_with_skip_reason(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            _write_jsonl(config.drafts_path, [
                {"section_idx": 0, "skipped": True, "skip_reason": "meta-allowlist"},
                {"draft_idx": 0, "section_idx": 1, "title": "p"},
                {"draft_idx": 1, "section_idx": 2, "title": "p2"},
            ])
            _write_jsonl(config.formal_path, [
                {"id": "REQ-PHASE3-001", "draft_idx": 0,
                 "tier": 1, "source_type": "skill-section",
                 "skill_section": "Phase 1: Explore",
                 "disposition": "accepted"},
                {"id": "REQ-PHASE3-002", "draft_idx": 1,
                 "tier": 1, "source_type": "skill-section",
                 "skill_section": "Cross-Cutting Invariants",
                 "disposition": "accepted"},
            ])
            pass_d.run_pass_d(config)
            cov = json.loads(config.section_coverage_path.read_text())
            meta_section = next(
                s for s in cov["sections"]
                if s["heading"] == "Why This Exists"
            )
            self.assertEqual(meta_section["section_kind"], "meta")
            self.assertEqual(meta_section["skip_reason"], "meta-allowlist")

    def test_completeness_gap_flagged_for_unflagged_zero_req(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            # Forgotten Section (section_idx=3) is operational, gets
            # zero drafts, has no skip rationale -> completeness gap.
            _write_jsonl(config.drafts_path, [
                {"draft_idx": 0, "section_idx": 1, "title": "p"},
                {"draft_idx": 1, "section_idx": 2, "title": "p2"},
            ])
            _write_jsonl(config.formal_path, [
                {"id": "REQ-PHASE3-001", "draft_idx": 0,
                 "tier": 1, "source_type": "skill-section",
                 "skill_section": "Phase 1",
                 "disposition": "accepted"},
                {"id": "REQ-PHASE3-002", "draft_idx": 1,
                 "tier": 1, "source_type": "skill-section",
                 "skill_section": "Cross-Cutting",
                 "disposition": "accepted"},
            ])
            pass_d.run_pass_d(config)
            cov = json.loads(config.section_coverage_path.read_text())
            gaps = cov["completeness_gaps"]
            self.assertEqual(len(gaps), 1)
            self.assertEqual(gaps[0]["heading"], "Forgotten Section")


class CouncilInboxTests(unittest.TestCase):
    def _setup(self, tmp: Path):
        _write_pass_c_complete_progress(tmp)
        config = _make_config(tmp)
        _write_sections_fixture(config.sections_path, _basic_sections())
        return config

    def test_inbox_includes_rejected_demoted_gap_and_uc(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            # 1 rejected, 1 demoted, 1 zero-req-section (auto-flagged
            # for "Forgotten Section"), 1 UC.
            _write_jsonl(config.drafts_path, [
                {"draft_idx": 0, "section_idx": 1,
                 "title": "rejected", "acceptance_criteria": "x"},
                {"draft_idx": 1, "section_idx": 2,
                 "title": "demoted", "acceptance_criteria": "y"},
            ])
            _write_jsonl(config.formal_path, [
                {"id": "REQ-PHASE3-001", "draft_idx": 0,
                 "tier": 1, "source_type": "skill-section",
                 "skill_section": "Phase 1",
                 "disposition": "needs-council-review",
                 "council_review_rationale": "structural"},
                {"id": "REQ-PHASE3-002", "draft_idx": 1,
                 "tier": 5, "source_type": "code-derived",
                 "skill_section": None,
                 "disposition": "demoted-tier-5",
                 "council_review_rationale": "behavioral"},
            ])
            _write_jsonl(config.formal_use_cases_path, [
                {"uc_id": "UC-PHASE3-01", "section_idx": 1,
                 "title": "Operator runs Phase 1",
                 "actors": ["operator"], "steps": ["x"],
                 "trigger": "t", "acceptance": "a",
                 "needs_council_review": True,
                 "uc_draft_idx": 0},
            ])
            pass_d.run_pass_d(config)
            inbox = json.loads(config.council_inbox_path.read_text())
            self.assertEqual(inbox["schema_version"], "1.0")
            self.assertIn("generated_at", inbox)
            item_types = sorted(item["item_type"] for item in inbox["items"])
            # Expect 1 rejected-draft + 1 tier-5-demotion + 1
            # zero-req-section + 1 weak-rationale (UC).
            self.assertEqual(
                item_types,
                sorted([
                    "rejected-draft",
                    "tier-5-demotion",
                    "weak-rationale",
                    "zero-req-section",
                ]),
            )
            for item in inbox["items"]:
                self.assertIn(
                    item["item_type"],
                    pass_d.VALID_COUNCIL_INBOX_ITEM_TYPES,
                )
                self.assertIn("section_idx", item)
                self.assertIn("rationale", item)
                self.assertIn("provisional_disposition", item)


class RejectionRateFlagTests(unittest.TestCase):
    def _setup(self, tmp: Path):
        _write_pass_c_complete_progress(tmp)
        config = _make_config(tmp)
        _write_sections_fixture(config.sections_path, _basic_sections())
        return config

    def test_high_rejection_rate_sets_phase4_flag(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            # 10 drafts, 7 rejected = 70% > 30% threshold.
            drafts = [
                {"draft_idx": i, "section_idx": 2, "title": f"d{i}"}
                for i in range(10)
            ]
            formal = [
                {"id": f"REQ-PHASE3-{i+1:03d}", "draft_idx": i,
                 "tier": 1, "source_type": "skill-section",
                 "skill_section": "Phase 1",
                 "disposition": "accepted" if i < 3 else "needs-council-review",
                 "council_review_rationale": "x"}
                for i in range(10)
            ]
            _write_jsonl(config.drafts_path, drafts)
            _write_jsonl(config.formal_path, formal)
            summary = pass_d.run_pass_d(config)
            self.assertGreater(summary["rejection_rate"], 0.3)
            self.assertTrue(summary["phase4_council_flag"])

    def test_low_rejection_rate_clears_phase4_flag(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            drafts = [
                {"draft_idx": i, "section_idx": 2, "title": f"d{i}"}
                for i in range(10)
            ]
            formal = [
                {"id": f"REQ-PHASE3-{i+1:03d}", "draft_idx": i,
                 "tier": 1, "source_type": "skill-section",
                 "skill_section": "X",
                 "disposition": "accepted"}
                for i in range(10)
            ]
            _write_jsonl(config.drafts_path, drafts)
            _write_jsonl(config.formal_path, formal)
            summary = pass_d.run_pass_d(config)
            self.assertEqual(summary["rejection_rate"], 0.0)
            self.assertFalse(summary["phase4_council_flag"])


class B4UpstreamGateTests(unittest.TestCase):
    def test_pass_d_refuses_when_pass_c_incomplete(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            p3 = _setup_phase3_dir(tmp)
            protocol.write_progress_atomic(
                p3 / "pass_c_progress.json",
                protocol.ProgressState(
                    pass_="C", unit="citation", cursor=2, total=10,
                    status="running", last_updated="2026-04-27T00:00:00Z",
                ),
            )
            config = _make_config(tmp)
            _write_sections_fixture(config.sections_path, _basic_sections())
            (config.drafts_path).write_text("", encoding="utf-8")
            (config.formal_path).write_text("", encoding="utf-8")
            with self.assertRaises(protocol.UpstreamIncompleteError) as cm:
                pass_d.run_pass_d(config)
            self.assertIn("Pass D refused to start", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
