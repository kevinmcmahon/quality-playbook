"""Tests for bin/skill_derivation/citation_search.py and pass_b.py."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin.skill_derivation import citation_search, pass_b, protocol


# ---------------------------------------------------------------------------
# citation_search.find_best_match
# ---------------------------------------------------------------------------


class CitationSearchTests(unittest.TestCase):
    def _docs(self, body: str) -> list[tuple[str, str]]:
        return [("SKILL.md", body)]

    def test_verbatim_match_above_threshold(self) -> None:
        body = (
            "Phase 1 produces EXPLORATION.md with at least 8 findings.\n"
            "Other prose.\n"
        )
        hit = citation_search.find_best_match(
            "Phase 1 produces EXPLORATION.md with at least 8 findings.",
            self._docs(body),
        )
        self.assertIsNotNone(hit)
        self.assertGreater(hit.score, 0.95)
        self.assertEqual(hit.document, "SKILL.md")
        self.assertEqual(hit.line_start, 1)

    def test_no_support_returns_none(self) -> None:
        body = "Completely unrelated text about widgets and sprockets.\n"
        hit = citation_search.find_best_match(
            "Phase 1 produces EXPLORATION.md with at least 8 findings.",
            self._docs(body),
        )
        self.assertIsNone(hit)

    def test_fuzzy_minor_wording_difference_still_matches(self) -> None:
        body = (
            "Phase 1 produces an EXPLORATION.md file with at least eight "
            "findings before the gate runs.\n"
        )
        hit = citation_search.find_best_match(
            "Phase 1 produces EXPLORATION.md with 8 findings",
            self._docs(body),
            similarity_threshold=0.5,  # accept a slightly looser bar
        )
        self.assertIsNotNone(hit)
        self.assertGreater(hit.score, 0.5)

    def test_threshold_boundary_just_below(self) -> None:
        # Construct a body where the best match scores under 0.6 ratio.
        body = "Sprockets and widgets and gears.\n"
        hit = citation_search.find_best_match(
            "Phase 1 produces EXPLORATION.md with 8 findings",
            self._docs(body),
            similarity_threshold=0.6,
        )
        self.assertIsNone(hit)

    def test_threshold_boundary_just_above(self) -> None:
        body = "Phase 1 produces EXPLORATION.md with 8 findings.\n"
        hit = citation_search.find_best_match(
            "Phase 1 produces EXPLORATION.md with 8 findings",
            self._docs(body),
            similarity_threshold=0.6,
        )
        self.assertIsNotNone(hit)
        self.assertGreaterEqual(hit.score, 0.6)

    def test_picks_best_window_across_documents(self) -> None:
        docs = [
            ("SKILL.md", "Other prose about generic topics.\n"),
            ("references/x.md", "The orchestrator MUST exit non-zero on missing SKILL.md.\n"),
        ]
        hit = citation_search.find_best_match(
            "The orchestrator MUST exit non-zero on missing SKILL.md.",
            docs,
        )
        self.assertIsNotNone(hit)
        self.assertEqual(hit.document, "references/x.md")

    def test_empty_candidate_returns_none(self) -> None:
        self.assertIsNone(
            citation_search.find_best_match("", self._docs("some body"))
        )

    def test_collect_documents_reads_skill_and_references(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            (tmp / "SKILL.md").write_text("skill body\n", encoding="utf-8")
            refs = tmp / "references"
            refs.mkdir()
            (refs / "patterns.md").write_text("patterns body\n", encoding="utf-8")
            (refs / "ignored.txt").write_text("not markdown\n", encoding="utf-8")
            docs = citation_search.collect_documents(
                tmp / "SKILL.md", refs, tmp
            )
            paths = [d[0] for d in docs]
            self.assertIn("SKILL.md", paths)
            self.assertIn("references/patterns.md", paths)
            self.assertNotIn("references/ignored.txt", paths)


# ---------------------------------------------------------------------------
# pass_b.run_pass_b
# ---------------------------------------------------------------------------


class PassBDriverTests(unittest.TestCase):
    def _setup(self, tmp: Path) -> tuple[pass_b.PassBConfig, list[dict]]:
        skill = tmp / "SKILL.md"
        skill.write_text(
            "# Doc\n\n"
            "## Phase 1: Explore\n\n"
            "Phase 1 produces EXPLORATION.md with at least 8 findings.\n"
            "The orchestrator MUST exit non-zero on missing SKILL.md.\n",
            encoding="utf-8",
        )
        drafts_path = tmp / "phase3" / "pass_a_drafts.jsonl"
        drafts_path.parent.mkdir(parents=True, exist_ok=True)
        drafts = [
            {
                "draft_idx": 0,
                "section_idx": 1,
                "title": "Exploration produces ≥8 findings",
                "description": "Phase 1 must hit minimum coverage.",
                "acceptance_criteria": (
                    "Phase 1 produces EXPLORATION.md with at least 8 findings."
                ),
                "proposed_source_ref": "Phase 1 section",
            },
            {
                "draft_idx": 1,
                "section_idx": 1,
                "title": "Non-zero exit on missing SKILL",
                "description": "Hard fail at startup if SKILL.md is missing.",
                "acceptance_criteria": (
                    "The orchestrator MUST exit non-zero on missing SKILL.md."
                ),
                "proposed_source_ref": "Phase 1 section",
            },
            {
                "draft_idx": 2,
                "section_idx": 1,
                "title": "Hallucinated unsupported claim",
                "description": "Behavioral claim not in any document.",
                "acceptance_criteria": (
                    "The system implements quantum entanglement debugging."
                ),
                "proposed_source_ref": "Phase 1 section",
            },
            # Skip marker passes through unchanged.
            {
                "section_idx": 0,
                "skipped": True,
                "skip_reason": "meta-allowlist",
                "_metadata": {"elapsed_ms": 0},
            },
        ]
        with drafts_path.open("w", encoding="utf-8") as fh:
            for d in drafts:
                fh.write(json.dumps(d) + "\n")
        config = pass_b.PassBConfig(
            drafts_path=drafts_path,
            citations_path=tmp / "phase3" / "pass_b_citations.jsonl",
            progress_path=tmp / "phase3" / "pass_b_progress.json",
            skill_md_path=skill,
            references_dir=None,
            document_root=tmp,
        )
        return config, drafts

    def test_full_run_marks_supported_as_verified(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config, _ = self._setup(tmp)
            pass_b.run_pass_b(config)
            recs = [
                json.loads(line)
                for line in config.citations_path.read_text().splitlines()
                if line.strip()
            ]
            verified = [r for r in recs if r.get("citation_status") == "verified"]
            self.assertEqual(len(verified), 2)
            for r in verified:
                self.assertTrue(r.get("citation_excerpt"))
                self.assertEqual(r["source_document"], "SKILL.md")
                self.assertGreater(r["similarity_score"], 0.8)

    def test_unsupported_claim_marked_unverified(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config, _ = self._setup(tmp)
            pass_b.run_pass_b(config)
            recs = [
                json.loads(line)
                for line in config.citations_path.read_text().splitlines()
                if line.strip()
            ]
            unverified = [
                r for r in recs
                if r.get("citation_status") == "unverified"
                and r.get("draft_idx") == 2
            ]
            self.assertEqual(len(unverified), 1)
            self.assertIsNone(unverified[0]["citation_excerpt"])

    def test_skip_marker_passes_through_with_skipped_status(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config, _ = self._setup(tmp)
            pass_b.run_pass_b(config)
            recs = [
                json.loads(line)
                for line in config.citations_path.read_text().splitlines()
                if line.strip()
            ]
            skipped = [r for r in recs if r.get("citation_status") == "skipped"]
            self.assertEqual(len(skipped), 1)
            self.assertEqual(skipped[0]["skip_reason"], "meta-allowlist")

    def test_progress_complete_at_end(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config, drafts = self._setup(tmp)
            pass_b.run_pass_b(config)
            state = protocol.read_progress(config.progress_path)
            self.assertEqual(state.status, "complete")
            self.assertEqual(state.cursor, len(drafts))

    def test_resumability_kill_mid_pass(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config, drafts = self._setup(tmp)

            # Manually simulate a partial run: write the first 2
            # citation records and a stale progress file at cursor=2.
            from bin.skill_derivation.pass_b import (
                _draft_to_citation_record,
            )
            documents = citation_search.collect_documents(
                config.skill_md_path, config.references_dir, config.document_root
            )
            for idx in range(2):
                rec = _draft_to_citation_record(drafts[idx], documents, config)
                rec["_pass_b_idx"] = idx
                protocol.append_jsonl(config.citations_path, rec)
            protocol.write_progress_atomic(
                config.progress_path,
                protocol.ProgressState(
                    pass_="B",
                    unit="draft",
                    cursor=2,
                    total=len(drafts),
                    status="running",
                    last_updated="2026-04-26T12:00:00Z",
                ),
            )
            # Resume: should process only drafts 2 and 3 (the
            # remaining two), giving a final total of 4.
            pass_b.run_pass_b(config)
            recs = [
                json.loads(line)
                for line in config.citations_path.read_text().splitlines()
                if line.strip()
            ]
            self.assertEqual(len(recs), len(drafts))
            # Each draft idx represented exactly once.
            idxs = sorted(r["_pass_b_idx"] for r in recs)
            self.assertEqual(idxs, list(range(len(drafts))))


if __name__ == "__main__":
    unittest.main()
