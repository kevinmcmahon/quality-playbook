"""Tests for bin/skill_derivation/pass_a.py — Pass A driver."""

from __future__ import annotations

import json
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, List

from bin.skill_derivation import pass_a, protocol, sections
from bin.skill_derivation.runners import RunnerResult


# ---------------------------------------------------------------------------
# Mock runner -- deterministic per-prompt response with configurable elapsed
# time, used to test cursor advancement, tripwire, and parsing without
# firing real LLM calls.
# ---------------------------------------------------------------------------


@dataclass
class MockRunner:
    """Deterministic LLM runner for tests.

    response_for(prompt) is a callable mapping prompt text to a JSONL
    string; elapsed_ms is the per-call simulated wall-clock time.
    """

    response_for: Callable[[str], str]
    elapsed_ms: int = 30_000  # 30s default; well above the tripwire floor
    call_log: List[str] = field(default_factory=list)

    def run(self, prompt: str) -> RunnerResult:
        self.call_log.append(prompt)
        return RunnerResult(
            stdout=self.response_for(prompt),
            stderr="",
            elapsed_ms=self.elapsed_ms,
            returncode=0,
        )


def _setup_fixture(tmp: Path) -> dict:
    """Write a minimal SKILL.md fixture and produce its sections JSON.

    Returns a dict of paths used by the Pass A driver.
    """
    skill_text = """\
# Doc

## Why This Exists

Meta prose; allowlisted.

## Phase 1: Explore

Operational prose. The orchestrator MUST exit non-zero when SKILL.md
is missing. Phase 1 produces EXPLORATION.md with at least 8 findings.

## Phase 2: Plan

Operational prose. The plan must enumerate all phases.

## Phase 3: Build

Operational prose. The build must run all unit tests.
"""
    skill_path = tmp / "SKILL.md"
    skill_path.write_text(skill_text, encoding="utf-8")
    enumerated = sections.enumerate_sections(skill_path, repo_root=tmp)
    sections_path = tmp / "phase3" / "pass_a_sections.json"
    sections.write_sections_json(enumerated, sections_path)
    return {
        "skill_path": skill_path,
        "sections_path": sections_path,
        "drafts_path": tmp / "phase3" / "pass_a_drafts.jsonl",
        "progress_path": tmp / "phase3" / "pass_a_progress.json",
        "pass_spec_path": tmp / "PHASE3_BRIEF.md",
        "document_root": tmp,
        "section_count": len(enumerated),
    }


class CursorAdvancementTests(unittest.TestCase):
    def _response(self, prompt: str) -> str:
        # Extract section_idx from the rendered prompt to keep responses unique.
        # The template includes "Section index in this run: `<idx>`".
        import re
        m = re.search(r"Section index in this run: `(\d+)`", prompt)
        if m is None:
            raise AssertionError(
                "Prompt did not include the expected `Section index in this "
                "run: `<idx>`` marker; mock response cannot route by section."
            )
        section_idx = int(m.group(1))
        return json.dumps({
            "draft_idx": 0,
            "section_idx": section_idx,
            "title": f"REQ from section {section_idx}",
            "description": "x",
            "acceptance_criteria": "y",
            "proposed_source_ref": "z",
        })

    def test_full_run_processes_all_non_skipped_sections(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            paths = _setup_fixture(tmp)
            # Write a stub spec doc so render_recovery_preamble has something.
            paths["pass_spec_path"].write_text("stub spec", encoding="utf-8")
            template = (
                Path(__file__).resolve().parents[1]
                / "skill_derivation"
                / "prompts"
                / "pass_a_section.md"
            )
            config = pass_a.PassAConfig(
                drafts_path=paths["drafts_path"],
                progress_path=paths["progress_path"],
                sections_path=paths["sections_path"],
                pass_spec_path=paths["pass_spec_path"],
                document_root=paths["document_root"],
            )
            runner = MockRunner(response_for=self._response)
            pass_a.run_pass_a(config, runner, template)
            # Skipped sections (Why This Exists) emit a record without
            # firing the runner; operational sections fire it once.
            non_skipped = paths["section_count"] - 1  # Why This Exists is meta
            self.assertEqual(len(runner.call_log), non_skipped)
            # All sections are represented in the JSONL.
            recs = [
                json.loads(line)
                for line in paths["drafts_path"].read_text().splitlines()
                if line.strip()
            ]
            represented_idxs = {r["section_idx"] for r in recs}
            self.assertEqual(represented_idxs, set(range(paths["section_count"])))
            # Progress is complete.
            state = protocol.read_progress(paths["progress_path"])
            self.assertEqual(state.status, "complete")
            self.assertEqual(state.cursor, paths["section_count"])

    def test_kill_mid_pass_resume_continues_from_cursor(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            paths = _setup_fixture(tmp)
            paths["pass_spec_path"].write_text("stub spec", encoding="utf-8")
            template = (
                Path(__file__).resolve().parents[1]
                / "skill_derivation"
                / "prompts"
                / "pass_a_section.md"
            )
            config = pass_a.PassAConfig(
                drafts_path=paths["drafts_path"],
                progress_path=paths["progress_path"],
                sections_path=paths["sections_path"],
                pass_spec_path=paths["pass_spec_path"],
                document_root=paths["document_root"],
            )

            # First runner halts after the second non-skipped section.
            call_count = [0]

            def halting_response(prompt: str) -> str:
                call_count[0] += 1
                if call_count[0] >= 3:
                    raise RuntimeError("simulated kill")
                return self._response(prompt)

            runner_a = MockRunner(response_for=halting_response)
            with self.assertRaises(RuntimeError):
                pass_a.run_pass_a(config, runner_a, template)

            # Progress should now show partial completion -- some
            # sections processed, cursor advanced.
            state = protocol.read_progress(paths["progress_path"])
            self.assertEqual(state.status, "running")
            partial_cursor = state.cursor
            self.assertGreater(partial_cursor, 0)
            self.assertLess(partial_cursor, paths["section_count"])

            # Second runner completes successfully -- resumes from cursor.
            runner_b = MockRunner(response_for=self._response)
            pass_a.run_pass_a(config, runner_b, template)

            # Sections processed by runner_b == total - partial_cursor.
            non_skipped_total = paths["section_count"] - 1
            non_skipped_already = sum(
                1
                for line in paths["drafts_path"].read_text().splitlines()
                if line.strip() and "draft_idx" in line and "skipped" not in line
            )
            # All non-skipped sections covered exactly once.
            self.assertEqual(non_skipped_already, non_skipped_total)
            # Final progress complete.
            state = protocol.read_progress(paths["progress_path"])
            self.assertEqual(state.status, "complete")
            self.assertEqual(state.cursor, paths["section_count"])


class SkippedSectionTests(unittest.TestCase):
    def test_meta_section_emits_skip_marker_without_runner(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            paths = _setup_fixture(tmp)
            paths["pass_spec_path"].write_text("stub spec", encoding="utf-8")
            template = (
                Path(__file__).resolve().parents[1]
                / "skill_derivation"
                / "prompts"
                / "pass_a_section.md"
            )
            config = pass_a.PassAConfig(
                drafts_path=paths["drafts_path"],
                progress_path=paths["progress_path"],
                sections_path=paths["sections_path"],
                pass_spec_path=paths["pass_spec_path"],
                document_root=paths["document_root"],
            )

            def response(prompt: str) -> str:
                return json.dumps({
                    "draft_idx": 0,
                    "section_idx": 0,
                    "title": "x",
                    "description": "y",
                    "acceptance_criteria": "z",
                    "proposed_source_ref": "w",
                })

            runner = MockRunner(response_for=response)
            pass_a.run_pass_a(config, runner, template)
            recs = [
                json.loads(line)
                for line in paths["drafts_path"].read_text().splitlines()
                if line.strip()
            ]
            skipped = [r for r in recs if r.get("skipped")]
            self.assertEqual(len(skipped), 1)
            self.assertEqual(skipped[0]["skip_reason"], "meta-allowlist")


class TripwireTests(unittest.TestCase):
    def test_sub_12s_response_fires_tripwire(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            paths = _setup_fixture(tmp)
            paths["pass_spec_path"].write_text("stub spec", encoding="utf-8")
            template = (
                Path(__file__).resolve().parents[1]
                / "skill_derivation"
                / "prompts"
                / "pass_a_section.md"
            )
            config = pass_a.PassAConfig(
                drafts_path=paths["drafts_path"],
                progress_path=paths["progress_path"],
                sections_path=paths["sections_path"],
                pass_spec_path=paths["pass_spec_path"],
                document_root=paths["document_root"],
            )
            runner = MockRunner(
                response_for=lambda p: json.dumps({
                    "draft_idx": 0,
                    "section_idx": 0,
                    "title": "x",
                    "description": "y",
                    "acceptance_criteria": "z",
                    "proposed_source_ref": "w",
                }),
                elapsed_ms=4000,  # 4s -- well below 12s floor
            )
            with self.assertRaises(pass_a.TripwireFired) as cm:
                pass_a.run_pass_a(config, runner, template)
            self.assertIn("plausibility floor", str(cm.exception))


class JsonlParserTests(unittest.TestCase):
    def test_parses_jsonl_lines_and_skips_garbage(self) -> None:
        stdout = (
            'Some preamble line that is not JSON\n'
            '{"draft_idx": 0, "section_idx": 5, "title": "a"}\n'
            '\n'
            '```\n'
            '{"draft_idx": 1, "section_idx": 5, "title": "b"}\n'
            'trailing prose\n'
        )
        records = pass_a._parse_jsonl_response(stdout, expected_section_idx=5)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["title"], "a")
        self.assertEqual(records[1]["title"], "b")

    def test_no_reqs_marker_passes_through(self) -> None:
        stdout = (
            '{"section_idx": 5, "no_reqs": true, "rationale": "purely descriptive"}\n'
        )
        records = pass_a._parse_jsonl_response(stdout, expected_section_idx=5)
        self.assertEqual(len(records), 1)
        self.assertTrue(records[0]["no_reqs"])

    def test_missing_section_idx_filled_from_expected(self) -> None:
        stdout = '{"draft_idx": 0, "title": "x"}\n'
        records = pass_a._parse_jsonl_response(stdout, expected_section_idx=7)
        self.assertEqual(records[0]["section_idx"], 7)


class EmptyResponseTests(unittest.TestCase):
    def test_empty_stdout_emits_no_reqs_record(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            paths = _setup_fixture(tmp)
            paths["pass_spec_path"].write_text("stub spec", encoding="utf-8")
            template = (
                Path(__file__).resolve().parents[1]
                / "skill_derivation"
                / "prompts"
                / "pass_a_section.md"
            )
            config = pass_a.PassAConfig(
                drafts_path=paths["drafts_path"],
                progress_path=paths["progress_path"],
                sections_path=paths["sections_path"],
                pass_spec_path=paths["pass_spec_path"],
                document_root=paths["document_root"],
            )
            runner = MockRunner(
                response_for=lambda p: "", elapsed_ms=30_000
            )
            pass_a.run_pass_a(config, runner, template)
            recs = [
                json.loads(line)
                for line in paths["drafts_path"].read_text().splitlines()
                if line.strip()
            ]
            no_reqs = [
                r for r in recs
                if r.get("no_reqs")
                and "LLM produced no parseable" in r.get("rationale", "")
            ]
            # 3 operational sections (Phase 1, Phase 2, Phase 3)
            # produced no parseable output.
            self.assertEqual(len(no_reqs), 3)


class RecoveryPreambleInPromptTests(unittest.TestCase):
    def test_rendered_prompt_contains_recovery_preamble(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            paths = _setup_fixture(tmp)
            paths["pass_spec_path"].write_text("stub spec", encoding="utf-8")
            template = (
                Path(__file__).resolve().parents[1]
                / "skill_derivation"
                / "prompts"
                / "pass_a_section.md"
            )
            config = pass_a.PassAConfig(
                drafts_path=paths["drafts_path"],
                progress_path=paths["progress_path"],
                sections_path=paths["sections_path"],
                pass_spec_path=paths["pass_spec_path"],
                document_root=paths["document_root"],
            )
            captured = []

            def capture_response(prompt: str) -> str:
                captured.append(prompt)
                return json.dumps({
                    "draft_idx": 0,
                    "section_idx": 0,
                    "title": "x",
                    "description": "y",
                    "acceptance_criteria": "z",
                    "proposed_source_ref": "w",
                })

            runner = MockRunner(response_for=capture_response)
            pass_a.run_pass_a(config, runner, template)
            self.assertGreater(len(captured), 0)
            for prompt in captured:
                self.assertIn("auto-compaction", prompt)
                self.assertIn("Re-read the pass specification", prompt)
                self.assertIn("Disk is the source of truth", prompt)


if __name__ == "__main__":
    unittest.main()
