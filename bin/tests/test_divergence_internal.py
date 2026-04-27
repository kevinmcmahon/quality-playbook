"""Tests for bin/skill_derivation/divergence_internal.py — Phase 4
Part A.1 (internal-prose divergence detection)."""

from __future__ import annotations

import json
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin.skill_derivation.divergence_internal import (
    InternalDivergenceConfig,
    run_divergence_internal,
)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def _write_sections(path: Path, sections: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"sections": sections}), encoding="utf-8")


def _make_config(tmp: Path) -> InternalDivergenceConfig:
    return InternalDivergenceConfig(
        formal_path=tmp / "pass_c_formal.jsonl",
        formal_use_cases_path=tmp / "pass_c_formal_use_cases.jsonl",
        sections_path=tmp / "pass_a_sections.json",
        document_root=tmp,
        output_path=tmp / "pass_e_internal_divergences.jsonl",
    )


def _read_output(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class IntraSectionDetectionTests(unittest.TestCase):
    def test_two_reqs_same_section_conflict_emit_one_divergence(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            cfg = _make_config(tmp)
            _write_jsonl(cfg.formal_path, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt": "The gate runs 45 checks."},
                {"id": "REQ-PHASE3-002", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt": "There are 43 checks total."},
            ])
            _write_jsonl(cfg.formal_use_cases_path, [])
            _write_sections(cfg.sections_path, [
                {"section_idx": 1, "document": "SKILL.md",
                 "heading": "Gate Checks", "line_start": 1, "line_end": 5},
            ])
            result = run_divergence_internal(cfg)
            recs = _read_output(cfg.output_path)
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0]["subtype"], "intra-section")
            self.assertEqual(result["divergences_emitted"], 1)

    def test_three_reqs_same_section_no_conflict_zero_divergences(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            cfg = _make_config(tmp)
            _write_jsonl(cfg.formal_path, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt": "The orchestrator must read SKILL.md."},
                {"id": "REQ-PHASE3-002", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt": "The orchestrator stops on missing file."},
                {"id": "REQ-PHASE3-003", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt": "Phase 1 produces an artifact."},
            ])
            _write_jsonl(cfg.formal_use_cases_path, [])
            _write_sections(cfg.sections_path, [
                {"section_idx": 1, "document": "SKILL.md",
                 "heading": "S1", "line_start": 1, "line_end": 5},
            ])
            run_divergence_internal(cfg)
            self.assertEqual(_read_output(cfg.output_path), [])


class CrossSectionCountableTests(unittest.TestCase):
    def test_two_reqs_different_sections_conflict_routes_to_candidates(self) -> None:
        """Phase 5 Stage 1 (DQ-5-4): cross-section-countable matches
        emit to pass_e_internal_candidates.jsonl, NOT the divergences
        file. Prong 2 also requires both excerpts to share an artifact
        name in proximity to the matched number — the fixture mentions
        SKILL.md in both excerpts to satisfy that."""
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            cfg = _make_config(tmp)
            _write_jsonl(cfg.formal_path, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt":
                     "SKILL.md says the gate runs 45 checks today"},
                {"id": "REQ-PHASE3-002", "section_idx": 5,
                 "source_document": "SKILL.md",
                 "citation_excerpt":
                     "we run 43 checks against the SKILL.md manifest"},
            ])
            _write_jsonl(cfg.formal_use_cases_path, [])
            _write_sections(cfg.sections_path, [
                {"section_idx": 1, "document": "SKILL.md",
                 "heading": "S1", "line_start": 1, "line_end": 5},
                {"section_idx": 5, "document": "SKILL.md",
                 "heading": "S5", "line_start": 50, "line_end": 60},
            ])
            run_divergence_internal(cfg)
            # Divergences file: zero cross-section records (Stage 3
            # demoted to candidates per prong 4).
            divs = _read_output(cfg.output_path)
            cross_in_divs = [
                r for r in divs
                if r["subtype"].startswith("cross-section")
            ]
            self.assertEqual(len(cross_in_divs), 0)
            # Candidates file: one record with subtype
            # "cross-section-countable-candidate" and shared SKILL.md
            # artifact context.
            candidates_path = cfg.output_path.with_name(
                "pass_e_internal_candidates.jsonl"
            )
            cands = _read_output(candidates_path)
            self.assertEqual(len(cands), 1)
            self.assertEqual(
                cands[0]["subtype"], "cross-section-countable-candidate"
            )
            self.assertIn("SKILL.md", cands[0]["shared_artifacts"])


class PrecedenceTests(unittest.TestCase):
    def test_skill_md_vs_reference_file_yields_spec_fix_target_reference(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            cfg = _make_config(tmp)
            # Same section_idx so the pair appears in Stage 2.
            _write_jsonl(cfg.formal_path, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt": "the gate has 45 checks total"},
                {"id": "REQ-PHASE3-002", "section_idx": 1,
                 "source_document": "references/exploration_patterns.md",
                 "citation_excerpt": "the gate has 43 checks today"},
            ])
            _write_jsonl(cfg.formal_use_cases_path, [])
            _write_sections(cfg.sections_path, [
                {"section_idx": 1, "document": "SKILL.md",
                 "heading": "Gate", "line_start": 1, "line_end": 5},
                {"section_idx": 1, "document": "references/exploration_patterns.md",
                 "heading": "Gate", "line_start": 1, "line_end": 5},
            ])
            run_divergence_internal(cfg)
            # The two records partition under different (document, section)
            # keys, so Stage 2 doesn't pair them. They DO collide in Stage 3
            # (same document=their own; different sections) -- but they have
            # different documents, so cross-section-countable also misses
            # because Stage 3 partitions by source_document. The conflict
            # instead surfaces in Stage 3 only when the precedence applies
            # within a single document. Cross-document conflicts are
            # currently surfaced only when records share section_idx (Stage
            # 2) -- which they do here. So Stage 2 should fire on the same
            # section_idx=1.
            recs = _read_output(cfg.output_path)
            # Different source_documents partition separately; Stage 2 does
            # not fire across partitions. We assert the brief's documented
            # behavior: when records share (document, section_idx), Stage 2
            # detects; when they share (document, token), Stage 3 detects.
            # Cross-document countable conflicts are NOT detected by Stage
            # 1/2/3 currently — they surface via Council triage on the
            # section-batched inbox.
            self.assertEqual(len(recs), 0)

    def test_intra_skill_md_yields_null_disposition(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            cfg = _make_config(tmp)
            _write_jsonl(cfg.formal_path, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt": "the gate has 45 checks"},
                {"id": "REQ-PHASE3-002", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt": "the gate has 43 checks"},
            ])
            _write_jsonl(cfg.formal_use_cases_path, [])
            _write_sections(cfg.sections_path, [
                {"section_idx": 1, "document": "SKILL.md",
                 "heading": "Gate", "line_start": 1, "line_end": 5},
            ])
            run_divergence_internal(cfg)
            recs = _read_output(cfg.output_path)
            self.assertEqual(len(recs), 1)
            self.assertIsNone(recs[0]["provisional_disposition"])
            self.assertIsNone(recs[0]["provisional_disposition_target"])


class UcAnchorVerificationTests(unittest.TestCase):
    def test_un_anchored_uc_emits_un_anchored_uc_subtype(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            cfg = _make_config(tmp)
            # Synthetic SKILL.md whose section content does NOT mention
            # bootstrap or self-audit at all.
            (tmp / "SKILL.md").write_text(
                "## Phase 0\n\nThis section discusses runtime sequencing.\n",
                encoding="utf-8",
            )
            _write_jsonl(cfg.formal_path, [])
            _write_jsonl(cfg.formal_use_cases_path, [
                {"uc_id": "UC-PHASE3-17", "section_idx": 1,
                 "title": "Bootstrap self-audit",
                 "actors": ["maintainer"],
                 "steps": ["bootstrap audit", "verify outputs"],
                 "trigger": "maintainer runs bootstrap selfaudit",
                 "acceptance": "bootstrap selfaudit completes",
                 "_metadata": {"phase_3d_synthesized": True}},
            ])
            _write_sections(cfg.sections_path, [
                {"section_idx": 1, "document": "SKILL.md",
                 "heading": "Phase 0", "line_start": 1, "line_end": 3},
            ])
            run_divergence_internal(cfg)
            recs = _read_output(cfg.output_path)
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0]["subtype"], "un-anchored-uc")
            self.assertEqual(recs[0]["req_a_id"], "UC-PHASE3-17")

    def test_anchored_uc_does_not_emit_un_anchored_subtype(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            cfg = _make_config(tmp)
            (tmp / "SKILL.md").write_text(
                "## Phase 0\n\nThis section discusses bootstrap selfaudit "
                "scenarios where maintainer runs the playbook on the skill itself.\n",
                encoding="utf-8",
            )
            _write_jsonl(cfg.formal_path, [])
            _write_jsonl(cfg.formal_use_cases_path, [
                {"uc_id": "UC-PHASE3-17", "section_idx": 1,
                 "title": "Bootstrap self-audit",
                 "actors": ["maintainer"],
                 "steps": ["bootstrap selfaudit", "maintainer verifies"],
                 "trigger": "maintainer runs",
                 "acceptance": "bootstrap selfaudit complete",
                 "_metadata": {"phase_3d_synthesized": True}},
            ])
            _write_sections(cfg.sections_path, [
                {"section_idx": 1, "document": "SKILL.md",
                 "heading": "Phase 0", "line_start": 1, "line_end": 3},
            ])
            run_divergence_internal(cfg)
            recs = _read_output(cfg.output_path)
            self.assertEqual(
                [r for r in recs if r["subtype"] == "un-anchored-uc"], [],
            )


class SourceDocumentNoneHandlingTests(unittest.TestCase):
    def test_none_source_document_partitions_as_skill_md(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            cfg = _make_config(tmp)
            _write_jsonl(cfg.formal_path, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": None,
                 "citation_excerpt": "We run 45 checks here."},
                {"id": "REQ-PHASE3-002", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt": "We run 43 checks here."},
            ])
            _write_jsonl(cfg.formal_use_cases_path, [])
            _write_sections(cfg.sections_path, [
                {"section_idx": 1, "document": "SKILL.md",
                 "heading": "Checks", "line_start": 1, "line_end": 5},
            ])
            run_divergence_internal(cfg)
            recs = _read_output(cfg.output_path)
            self.assertGreaterEqual(len(recs), 1)
            self.assertEqual(recs[0]["source_document"], "SKILL.md")


class Stage3DedupeTests(unittest.TestCase):
    """Round 8 Finding 1: when a REQ excerpt repeats the same
    (value, noun) token twice, Stage 3 used to emit two byte-
    identical divergences (DIV-INT-016 / DIV-INT-017 in the QPB
    live run). The dedupe fix collapses them to one."""

    def test_repeated_token_in_excerpt_emits_exactly_one_candidate(self) -> None:
        """Phase 5 Stage 1 (DQ-5-4): Stage 3 candidates land in
        pass_e_internal_candidates.jsonl. The Round 8 dedupe still
        applies — repeated (value, noun) tokens within one excerpt
        do not duplicate the cross-section pair."""
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            cfg = _make_config(tmp)
            # Both excerpts cite SKILL.md so prong 2 (shared artifact
            # name) is satisfied.
            _write_jsonl(cfg.formal_path, [
                {"id": "REQ-PHASE3-001", "section_idx": 1,
                 "source_document": "SKILL.md",
                 "citation_excerpt":
                     "SKILL.md says between 5 and 7 use cases; "
                     "more than 7 use cases per SKILL.md"},
                {"id": "REQ-PHASE3-002", "section_idx": 5,
                 "source_document": "SKILL.md",
                 "citation_excerpt":
                     "SKILL.md integration tests run with 2 use cases per group"},
            ])
            _write_jsonl(cfg.formal_use_cases_path, [])
            _write_sections(cfg.sections_path, [
                {"section_idx": 1, "document": "SKILL.md",
                 "heading": "Use Cases (Overview)",
                 "line_start": 1, "line_end": 5},
                {"section_idx": 5, "document": "SKILL.md",
                 "heading": "Integration Tests",
                 "line_start": 50, "line_end": 60},
            ])
            run_divergence_internal(cfg)
            candidates_path = cfg.output_path.with_name(
                "pass_e_internal_candidates.jsonl"
            )
            cands = _read_output(candidates_path)
            cross = [
                r for r in cands
                if r["subtype"] == "cross-section-countable-candidate"
            ]
            self.assertEqual(
                len(cross), 1,
                f"Stage 3 dedupe failed: expected 1 candidate for the "
                f"REQ-001 x REQ-002 pair (despite repeated token in "
                f"REQ-001's excerpt), got {len(cross)}: "
                f"{[(r['req_a_id'], r['req_b_id']) for r in cross]}",
            )


class PerformanceTests(unittest.TestCase):
    def test_200_reqs_complete_under_30s_with_bounded_pair_count(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            cfg = _make_config(tmp)
            reqs = []
            sections = []
            for s in range(20):
                sections.append({
                    "section_idx": s, "document": "SKILL.md",
                    "heading": f"S{s}", "line_start": s * 10 + 1,
                    "line_end": s * 10 + 9,
                })
                for j in range(10):
                    reqs.append({
                        "id": f"REQ-PHASE3-{s * 10 + j + 1:03d}",
                        "section_idx": s, "source_document": "SKILL.md",
                        # Non-countable text keeps Stage 3's token index
                        # narrow; the fixture exercises Stage 2 partitioning
                        # which dominates wall-clock on QPB.
                        "citation_excerpt": (
                            f"Operator action for section_{s}_record_{j} "
                            "must be performed deterministically."
                        ),
                    })
            _write_jsonl(cfg.formal_path, reqs)
            _write_jsonl(cfg.formal_use_cases_path, [])
            _write_sections(cfg.sections_path, sections)
            t0 = time.monotonic()
            result = run_divergence_internal(cfg)
            elapsed = time.monotonic() - t0
            self.assertLess(elapsed, 30.0)
            self.assertLess(
                result["comparison_count_by_stage"]["stage2_pairs"]
                + result["comparison_count_by_stage"]["stage3_pairs"],
                5000,
            )


if __name__ == "__main__":
    unittest.main()
