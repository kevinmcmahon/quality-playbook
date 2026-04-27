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
        # Round 3 Council B4: Pass B requires an upstream-complete
        # Pass A progress file. The setup synthesizes one alongside
        # the drafts so the existing tests exercise normal Pass B
        # behavior; the dedicated B4 test below removes / corrupts
        # this file to verify the refusal path.
        pass_a_progress_path = drafts_path.with_name("pass_a_progress.json")
        protocol.write_progress_atomic(
            pass_a_progress_path,
            protocol.ProgressState(
                pass_="A",
                unit="section",
                cursor=4,
                total=4,
                status="complete",
                last_updated="2026-04-26T12:00:00Z",
            ),
        )
        config = pass_b.PassBConfig(
            drafts_path=drafts_path,
            citations_path=tmp / "phase3" / "pass_b_citations.jsonl",
            progress_path=tmp / "phase3" / "pass_b_progress.json",
            skill_md_path=skill,
            references_dir=None,
            document_root=tmp,
            pass_a_progress_path=pass_a_progress_path,
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


class UpstreamCompletionGateTests(unittest.TestCase):
    """Round 3 Council B4 regression tests.

    Pass B MUST refuse to start unless its upstream Pass A progress
    file reports status="complete" (Implementation Plan line 202).
    Without this gate, a Pass A crash leaving status="running" would
    silently allow Pass B to consume an incomplete drafts file and
    propagate coverage gaps into the formal REQ pipeline.

    Tests cover the three failure cases require_upstream_complete()
    must reject, plus the success path.
    """

    def _bare_config(self, tmp: Path) -> tuple[pass_b.PassBConfig, Path]:
        skill = tmp / "SKILL.md"
        skill.write_text("# Doc\n\n## Phase 1\n\nstub\n", encoding="utf-8")
        drafts_path = tmp / "phase3" / "pass_a_drafts.jsonl"
        drafts_path.parent.mkdir(parents=True, exist_ok=True)
        drafts_path.write_text(
            json.dumps({
                "draft_idx": 0, "section_idx": 1,
                "title": "x", "description": "y",
                "acceptance_criteria": "z", "proposed_source_ref": "w",
            }) + "\n",
            encoding="utf-8",
        )
        upstream = drafts_path.with_name("pass_a_progress.json")
        config = pass_b.PassBConfig(
            drafts_path=drafts_path,
            citations_path=tmp / "phase3" / "pass_b_citations.jsonl",
            progress_path=tmp / "phase3" / "pass_b_progress.json",
            skill_md_path=skill,
            references_dir=None,
            document_root=tmp,
            pass_a_progress_path=upstream,
        )
        return config, upstream

    def test_refuses_when_upstream_progress_file_missing(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config, upstream = self._bare_config(tmp)
            self.assertFalse(upstream.exists())
            with self.assertRaises(protocol.UpstreamIncompleteError) as cm:
                pass_b.run_pass_b(config)
            self.assertIn("Pass B refused to start", str(cm.exception))
            self.assertIn("does not exist or is empty", str(cm.exception))

    def test_refuses_when_upstream_status_running(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config, upstream = self._bare_config(tmp)
            protocol.write_progress_atomic(
                upstream,
                protocol.ProgressState(
                    pass_="A",
                    unit="section",
                    cursor=2,
                    total=4,
                    status="running",
                    last_updated="2026-04-26T12:00:00Z",
                ),
            )
            with self.assertRaises(protocol.UpstreamIncompleteError) as cm:
                pass_b.run_pass_b(config)
            msg = str(cm.exception)
            self.assertIn("Pass B refused to start", msg)
            self.assertIn("'running'", msg)
            self.assertIn("cursor=2", msg)
            self.assertIn("total=4", msg)

    def test_refuses_when_upstream_status_blocked(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config, upstream = self._bare_config(tmp)
            protocol.write_progress_atomic(
                upstream,
                protocol.ProgressState(
                    pass_="A",
                    unit="section",
                    cursor=0,
                    total=None,
                    status="blocked",
                    last_updated="2026-04-26T12:00:00Z",
                    notes="LLM timeout on section 0",
                ),
            )
            with self.assertRaises(protocol.UpstreamIncompleteError):
                pass_b.run_pass_b(config)

    def test_proceeds_when_upstream_complete(self) -> None:
        # Smoke test: with a valid upstream-complete progress file,
        # Pass B does NOT raise UpstreamIncompleteError. We don't
        # care about the body of the run here (the existing
        # PassBDriverTests cover that); just that the gate doesn't
        # block.
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config, upstream = self._bare_config(tmp)
            protocol.write_progress_atomic(
                upstream,
                protocol.ProgressState(
                    pass_="A",
                    unit="section",
                    cursor=4,
                    total=4,
                    status="complete",
                    last_updated="2026-04-26T12:00:00Z",
                ),
            )
            # Should not raise.
            pass_b.run_pass_b(config)

    def test_default_upstream_path_resolves_next_to_drafts(self) -> None:
        # When pass_a_progress_path is None, the default is to look
        # for "pass_a_progress.json" in the same directory as the
        # drafts JSONL. Confirm by NOT setting the field and checking
        # the gate still fires.
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            config, upstream = self._bare_config(tmp)
            # Wipe the explicit field; the default should still find
            # the upstream file at the same canonical location.
            config_default = pass_b.PassBConfig(
                drafts_path=config.drafts_path,
                citations_path=config.citations_path,
                progress_path=config.progress_path,
                skill_md_path=config.skill_md_path,
                references_dir=config.references_dir,
                document_root=config.document_root,
                pass_a_progress_path=None,
            )
            # Without the upstream file written, the default resolution
            # finds nothing -> raises.
            with self.assertRaises(protocol.UpstreamIncompleteError):
                pass_b.run_pass_b(config_default)


if __name__ == "__main__":
    unittest.main()
