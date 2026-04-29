"""Tests for bin/skill_derivation/pass_c.py — formal REQ + UC production."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin.skill_derivation import pass_c, protocol


def _write_project_type(tmp: Path, classification: str) -> Path:
    """Write a v1.5.4 role map shaped to derive the requested legacy
    project type via bin.role_map.derive_legacy_project_type. Skill
    => skill-prose only; Hybrid => skill-prose + code; Code => code
    only."""
    qd = tmp / "quality"
    qd.mkdir(parents=True, exist_ok=True)
    out = qd / "exploration_role_map.json"
    files: list[dict] = []
    if classification in ("Skill", "Hybrid"):
        files.append({
            "path": "SKILL.md",
            "role": "skill-prose",
            "size_bytes": 1000,
            "rationale": "fixture skill prose",
        })
    if classification in ("Code", "Hybrid"):
        files.append({
            "path": "lib/main.py",
            "role": "code",
            "size_bytes": 500,
            "rationale": "fixture code surface",
        })
    total = sum(int(f["size_bytes"]) for f in files) or 1
    skill_size = sum(
        int(f["size_bytes"]) for f in files
        if f["role"] in ("skill-prose", "skill-reference")
    )
    code_size = sum(
        int(f["size_bytes"]) for f in files if f["role"] == "code"
    )
    payload = {
        "schema_version": "1.0",
        "timestamp_start": "2026-04-27T00:00:00Z",
        # v1.5.4 Phase 3.6.1: provenance + summary are required
        # top-level fields. Pass C itself doesn't validate, but
        # downstream gate paths do; populate so the fixture matches
        # the production shape.
        "provenance": "git-ls-files",
        "files": files,
        "breakdown": {
            "files_by_role": {
                f["role"]: sum(1 for x in files if x["role"] == f["role"])
                for f in files
            },
            "size_by_role": {
                f["role"]: sum(
                    int(x["size_bytes"]) for x in files
                    if x["role"] == f["role"]
                )
                for f in files
            },
            "percentages": {
                "skill_share": skill_size / total,
                "code_share": code_size / total,
                "tool_share": 0.0,
                "other_share": max(
                    0.0, 1.0 - (skill_size / total) - (code_size / total)
                ),
            },
        },
    }
    payload["summary"] = {
        "file_count": len(files),
        "role_breakdown": dict(payload["breakdown"]["files_by_role"]),
        "percentages": dict(payload["breakdown"]["percentages"]),
        "provenance": payload["provenance"],
    }
    out.write_text(json.dumps(payload), encoding="utf-8")
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
        role_map_path=tmp / "quality" / "exploration_role_map.json",
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
            # v1.5.4: pass_c reads the Phase-1 role map; the error names
            # the missing artifact so the operator knows what to run.
            self.assertIn("exploration_role_map.json", str(cm.exception))


class SkillSectionGuardTests(unittest.TestCase):
    """Round 5 ND-2: Pass C must NOT emit a record with
    source_type=='skill-section' AND empty skill_section. Such a
    record would FAIL schemas.md invariant #21 in the v1.5.3 manifest
    validator. The guard re-routes the record to council-review with
    a provisional skill_section placeholder."""

    def _setup(self, tmp: Path, project_type: str = "Skill"):
        _write_project_type(tmp, project_type)
        _write_pass_b_complete_progress(tmp)
        return _make_config(tmp)

    def test_empty_source_ref_skill_project_routes_to_council(self) -> None:
        """Behavioral branch on a pure-Skill project would set
        source_type=skill-section with skill_section from
        proposed_source_ref. When proposed_source_ref is empty AND
        section_heading is missing, the guard rewrites disposition
        to needs-council-review with a provisional placeholder
        instead of emitting an invariant-violating record."""
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp, project_type="Skill")
            _write_citations(config.citations_path, [{
                "draft_idx": 0,
                "section_idx": 1,
                "_pass_b_idx": 0,
                "title": "behavioral claim",
                "description": "x",
                "acceptance_criteria": "y",
                "proposed_source_ref": "",  # empty -> behavioral path
                # No section_heading field on the draft.
                "citation_status": "unverified",
                "source_document": None,
            }])
            pass_c.run_pass_c(config)
            recs = [
                json.loads(line)
                for line in config.formal_path.read_text().splitlines()
                if line.strip()
            ]
            self.assertEqual(len(recs), 1)
            r = recs[0]
            # Invariant-preserving: source_type=skill-section AND
            # skill_section is a non-empty string.
            self.assertEqual(r["source_type"], "skill-section")
            self.assertIsNotNone(r["skill_section"])
            self.assertIsInstance(r["skill_section"], str)
            self.assertNotEqual(r["skill_section"].strip(), "")
            # Disposition was rewritten to council-review.
            self.assertEqual(r["disposition"], "needs-council-review")
            self.assertIn("ND-2", r.get("council_review_rationale", ""))


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


class HandAuthoredUcSynthesizedTagTests(unittest.TestCase):
    """Round 7 Council finding: hand-authored / retroactively-
    synthesized UC drafts (those carrying
    `_metadata.phase_3d_synthesized=true` in
    pass_a_use_case_drafts.jsonl) must propagate the tag through
    Pass C to the formal UC record. Phase 4's Council triage relies
    on the tag to differentiate organic UCs (surfaced via section
    enumeration) from hand-authored ones that need anchor verification
    before BUGs are generated against them.

    The discipline these tests enforce: a future Phase 3e / 4 / 5
    hand-authored UC cannot ship un-tagged. If Pass C's
    `_build_formal_uc` regresses and drops the tag, these tests fail
    loudly.
    """

    def _setup(self, tmp: Path):
        _write_project_type(tmp, "Hybrid")
        _write_pass_b_complete_progress(tmp)
        config = _make_config(tmp)
        (config.citations_path).parent.mkdir(parents=True, exist_ok=True)
        (config.citations_path).write_text("", encoding="utf-8")
        return config

    def test_synthesized_uc_draft_propagates_tag_to_formal(self) -> None:
        """A Pass A UC draft with `_metadata.phase_3d_synthesized=true`
        must produce a formal Pass C UC record carrying the same tag
        on `_metadata.phase_3d_synthesized=true`."""
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            with config.uc_drafts_path.open("w", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "uc_draft_idx": 0, "section_idx": 4,
                    "title": "Bootstrap self-audit (hand-authored)",
                    "actors": ["maintainer"],
                    "steps": ["invoke playbook on QPB itself"],
                    "trigger": "maintainer runs self-audit",
                    "acceptance": "all four passes complete",
                    "proposed_source_ref": "SKILL.md §Phase 0",
                    "_metadata": {"phase_3d_synthesized": True},
                }) + "\n")
            pass_c.run_pass_c(config)
            ucs = [
                json.loads(line)
                for line in config.formal_use_cases_path.read_text().splitlines()
                if line.strip()
            ]
            self.assertEqual(len(ucs), 1)
            uc = ucs[0]
            self.assertIn(
                "_metadata", uc,
                "hand-authored UC draft tagged `_metadata.phase_3d_synthesized=true` "
                "in Pass A must carry an `_metadata` dict on the formal Pass C UC; "
                "missing `_metadata` means Pass C's `_build_formal_uc` is dropping "
                "the tag and the discipline cannot be enforced downstream.",
            )
            self.assertIsInstance(uc["_metadata"], dict)
            self.assertTrue(
                uc["_metadata"].get("phase_3d_synthesized"),
                "formal UC built from a synthesized Pass A draft must carry "
                "`_metadata.phase_3d_synthesized=true` (got "
                f"{uc['_metadata']!r})",
            )

    def test_organic_uc_draft_does_not_carry_synthesized_tag(self) -> None:
        """Symmetric guard: a Pass A UC draft WITHOUT the synthesized
        tag must NOT carry the tag on the formal record. Otherwise the
        tag becomes meaningless (every UC has it). Organic UCs surfaced
        by section enumeration ship without the tag."""
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config = self._setup(tmp)
            with config.uc_drafts_path.open("w", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "uc_draft_idx": 0, "section_idx": 3,
                    "title": "Operator runs Phase 1 (organic)",
                    "actors": ["operator"],
                    "steps": ["invoke"],
                    "trigger": "operator action",
                    "acceptance": "Phase 1 completes",
                    "proposed_source_ref": "SKILL.md §How to Use",
                    "_metadata": {"elapsed_ms": 30000},
                }) + "\n")
            pass_c.run_pass_c(config)
            ucs = [
                json.loads(line)
                for line in config.formal_use_cases_path.read_text().splitlines()
                if line.strip()
            ]
            self.assertEqual(len(ucs), 1)
            uc = ucs[0]
            md = uc.get("_metadata") or {}
            self.assertFalse(
                md.get("phase_3d_synthesized"),
                "organic UC draft (no `_metadata.phase_3d_synthesized` in "
                "Pass A input) must NOT carry the synthesized tag on the "
                "formal Pass C UC record",
            )

    def test_live_run_uc_phase3_17_carries_tag(self) -> None:
        """Regression guard for the Round 7 finding itself: the
        committed live-run artifact at
        quality/phase3/pass_c_formal_use_cases.jsonl must contain
        UC-PHASE3-17 with the `_metadata.phase_3d_synthesized=true`
        tag. If a future re-run of Pass C drops the tag, this test
        fails loudly."""
        repo_root = Path(__file__).resolve().parents[2]
        artifact = repo_root / "quality" / "phase3" / "pass_c_formal_use_cases.jsonl"
        if not artifact.is_file():
            self.skipTest(
                f"live-run artifact at {artifact} not present; this guard only "
                "fires when the Phase 3d artifacts are committed."
            )
        ucs = [
            json.loads(line)
            for line in artifact.read_text().splitlines()
            if line.strip()
        ]
        uc17 = next((u for u in ucs if u.get("uc_id") == "UC-PHASE3-17"), None)
        self.assertIsNotNone(
            uc17,
            "UC-PHASE3-17 (Bootstrap Self-Audit) must be present in the "
            "live-run artifact",
        )
        md = uc17.get("_metadata") or {}
        self.assertTrue(
            md.get("phase_3d_synthesized"),
            "UC-PHASE3-17 is the Phase 3d hand-authored UC (Round 6 Finding 4); "
            "it must carry `_metadata.phase_3d_synthesized=true` so Phase 4's "
            "Council triage knows to anchor-verify before generating BUGs. "
            f"Got _metadata={md!r}",
        )


if __name__ == "__main__":
    unittest.main()
