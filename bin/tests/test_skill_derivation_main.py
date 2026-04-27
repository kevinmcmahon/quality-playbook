"""Tests for bin/skill_derivation/__main__.py — CLI entry point.

Covers:
  - Argument parsing (the moved TestSkillDerivationMainArgs class).
  - End-to-end --pass all orchestration (Round 5 ND-1): runs A -> B
    -> C -> D in sequence with the B4 upstream-status gate enforced
    at each transition. Uses a small synthetic SKILL.md fixture and a
    deterministic MockRunner so the test does not depend on a live
    LLM. Verifies all four progress files reach status="complete"
    and the per-pass artifacts land at the expected paths.
"""

from __future__ import annotations

import json
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, List
from unittest import mock

from bin.skill_derivation import __main__ as main_mod
from bin.skill_derivation import protocol
from bin.skill_derivation.runners import RunnerResult


# ---------------------------------------------------------------------------
# Argument parsing -- moved from .github/skills/quality_gate/tests/
# test_quality_gate.py:2678 per Round 5 ND-1. The bin/skill_derivation
# CLI tests structurally belong in the bin test suite; the gate suite
# tests gate behavior, not CLI plumbing.
# ---------------------------------------------------------------------------


class TestSkillDerivationMainArgs(unittest.TestCase):
    """Phase 3b commit 9: __main__.py argument parsing."""

    def test_imports_cleanly(self) -> None:
        # Smoke test: the module imports without side effects.
        from bin.skill_derivation import __main__ as main_mod_local
        self.assertTrue(callable(main_mod_local._main))

    def test_pass_choice_default_is_all(self) -> None:
        from bin.skill_derivation.__main__ import _parse_args
        args = _parse_args(["/tmp/example"])
        self.assertEqual(args.pass_choice, "all")
        self.assertTrue(args.resume)
        self.assertEqual(args.runner, "claude")
        self.assertEqual(args.pace_seconds, 0)

    def test_no_resume_flag(self) -> None:
        from bin.skill_derivation.__main__ import _parse_args
        args = _parse_args(["/tmp/example", "--no-resume"])
        self.assertFalse(args.resume)

    def test_pass_choice_individual(self) -> None:
        from bin.skill_derivation.__main__ import _parse_args
        for choice in ("A", "B", "C", "D"):
            args = _parse_args(["/tmp/example", "--pass", choice])
            self.assertEqual(args.pass_choice, choice)

    def test_runner_copilot(self) -> None:
        from bin.skill_derivation.__main__ import _parse_args
        args = _parse_args(["/tmp/example", "--runner", "copilot"])
        self.assertEqual(args.runner, "copilot")

    def test_pace_seconds_int(self) -> None:
        from bin.skill_derivation.__main__ import _parse_args
        args = _parse_args(["/tmp/example", "--pace-seconds", "30"])
        self.assertEqual(args.pace_seconds, 30)


# ---------------------------------------------------------------------------
# End-to-end --pass all integration test (Round 5 ND-1).
# ---------------------------------------------------------------------------


@dataclass
class _MockRunner:
    """Deterministic LLM runner for Pass A. Returns one REQ draft per
    call with the section_idx parsed out of the rendered prompt.
    elapsed_ms is set above the Pass A throughput tripwire floor.
    """

    elapsed_ms: int = 30_000
    call_log: List[str] = field(default_factory=list)

    def run(self, prompt: str) -> RunnerResult:
        import re
        self.call_log.append(prompt)
        match = re.search(r"Section index in this run: `(\d+)`", prompt)
        if match is None:
            section_idx = 0
        else:
            section_idx = int(match.group(1))
        # Single REQ per section keeps the fixture predictable.
        record = {
            "draft_idx": 0,
            "section_idx": section_idx,
            "title": f"REQ from section {section_idx}",
            "description": "stub description",
            "acceptance_criteria": "stub acceptance criteria",
            "proposed_source_ref": f"section_idx={section_idx}",
        }
        return RunnerResult(
            stdout=json.dumps(record) + "\n",
            stderr="",
            elapsed_ms=self.elapsed_ms,
            returncode=0,
        )


def _build_synthetic_fixture(root: Path) -> None:
    """Build a small Skill-shaped fixture (SKILL.md + project_type.json)
    suitable for an end-to-end --pass all run. No reference files; the
    integration test focuses on orchestration, not reference-file
    iteration coverage (which has its own targeted tests)."""
    skill_text = """\
# Synthetic Skill

## Why This Exists

Meta prose -- intentionally allowlisted so Pass A skips it.

## Phase 1: Explore

Operational prose. The orchestrator MUST exit non-zero on missing
SKILL.md. Phase 1 produces EXPLORATION.md with at least 8 findings.

## Phase 2: Plan

Operational prose. The plan must enumerate all phases.

## Phase 3: Build

Operational prose. The build must run all unit tests.
"""
    (root / "SKILL.md").write_text(skill_text, encoding="utf-8")

    quality = root / "quality"
    quality.mkdir(parents=True, exist_ok=True)
    (quality / "project_type.json").write_text(
        json.dumps({
            "schema_version": "1.1",
            "classification": "Skill",
            "rationale": "synthetic fixture for integration test",
            "confidence": "high",
            "evidence": {
                "skill_md_present": True,
                "skill_md_path": "SKILL.md",
                "skill_md_word_count": 200,
                "total_code_loc": 0,
                "code_languages": [],
                "confidence_reason": "fixture",
            },
            "classified_at": "2026-04-27T00:00:00Z",
            "classifier_version": "1.0",
            "override_applied": False,
            "override_rationale": None,
        }),
        encoding="utf-8",
    )


class PassAllIntegrationTests(unittest.TestCase):
    """Round 5 ND-1: --pass all orchestration body has end-to-end
    coverage. Verifies A -> B -> C -> D run in sequence with B4 gate
    enforced at each transition, all four progress files reach
    status='complete', and the expected artifact set lands."""

    def test_pass_all_runs_a_b_c_d_in_order_with_b4_gate(self) -> None:
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            _build_synthetic_fixture(tmp)

            mock_runner = _MockRunner()

            # Patch make_runner so --pass all uses MockRunner instead
            # of firing real `claude --print` subprocesses. Pass-spec
            # path defaults to a real file in the brief dir; override
            # with a stub so render_recovery_preamble has something
            # readable on the integration host.
            spec_stub = tmp / "PASS_SPEC_STUB.md"
            spec_stub.write_text("integration test stub", encoding="utf-8")

            with mock.patch.object(
                main_mod, "make_runner", return_value=mock_runner
            ):
                rc = main_mod._main([
                    str(tmp),
                    "--pass", "all",
                    "--runner", "claude",
                    "--pass-spec-path", str(spec_stub),
                ])

            self.assertEqual(rc, 0)

            p3 = tmp / "quality" / "phase3"

            # All four progress files exist and are complete.
            for pass_name in ("a", "b", "c", "d"):
                progress_path = p3 / f"pass_{pass_name}_progress.json"
                self.assertTrue(
                    progress_path.is_file(),
                    f"pass_{pass_name}_progress.json missing",
                )
                state = protocol.read_progress(progress_path)
                self.assertIsNotNone(
                    state, f"pass_{pass_name} progress unreadable"
                )
                self.assertEqual(
                    state.status, "complete",
                    f"pass_{pass_name} did not complete: status={state.status}",
                )

            # Per-pass artifacts at expected paths.
            self.assertTrue((p3 / "pass_a_sections.json").is_file())
            self.assertTrue((p3 / "pass_a_drafts.jsonl").is_file())
            self.assertTrue((p3 / "pass_b_citations.jsonl").is_file())
            self.assertTrue((p3 / "pass_c_formal.jsonl").is_file())
            self.assertTrue((p3 / "pass_d_audit.json").is_file())
            self.assertTrue((p3 / "pass_d_section_coverage.json").is_file())
            self.assertTrue((p3 / "pass_d_council_inbox.json").is_file())

            # Pass A produced records for every non-meta section.
            drafts = [
                json.loads(line)
                for line in (p3 / "pass_a_drafts.jsonl").read_text().splitlines()
                if line.strip()
            ]
            self.assertGreater(len(drafts), 0)
            # The "Why This Exists" meta section is allowlisted; it
            # contributes a skip marker rather than a draft REQ.
            skipped = [d for d in drafts if d.get("skipped")]
            self.assertEqual(
                len(skipped), 1,
                "expected exactly one meta-skip marker for "
                "'Why This Exists'",
            )

            # Pass B emitted one citation record per Pass A draft
            # (including skip markers, which pass through with
            # citation_status='skipped').
            citations = [
                json.loads(line)
                for line in (p3 / "pass_b_citations.jsonl").read_text().splitlines()
                if line.strip()
            ]
            self.assertEqual(len(citations), len(drafts))

            # Pass C emitted formal REQs (verified or council-review).
            formals = [
                json.loads(line)
                for line in (p3 / "pass_c_formal.jsonl").read_text().splitlines()
                if line.strip()
            ]
            self.assertGreater(len(formals), 0)
            # Schemas.md invariant #21: every record populates
            # source_type and never carries the reserved
            # "execution-observation" value.
            for r in formals:
                self.assertIn("source_type", r)
                self.assertNotEqual(r["source_type"], "execution-observation")
                if r["source_type"] == "skill-section":
                    ss = r.get("skill_section")
                    self.assertIsNotNone(ss)
                    self.assertIsInstance(ss, str)
                    self.assertNotEqual(ss.strip(), "")

            # Pass D produced an audit + council inbox.
            audit = json.loads((p3 / "pass_d_audit.json").read_text())
            self.assertIn("promoted", audit)
            self.assertIn("rejected", audit)
            self.assertIn("demoted_to_tier_5", audit)
            inbox = json.loads((p3 / "pass_d_council_inbox.json").read_text())
            self.assertEqual(inbox["schema_version"], "1.0")
            self.assertIsInstance(inbox["items"], list)

    def test_pass_b_refuses_when_pass_a_incomplete(self) -> None:
        """Round 5 ND-1: --pass B run on a fixture whose Pass A never
        completed must fail with UpstreamIncompleteError. This pins
        the B4 gate behavior at the CLI orchestration boundary."""
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            _build_synthetic_fixture(tmp)
            p3 = tmp / "quality" / "phase3"
            p3.mkdir(parents=True, exist_ok=True)
            # Pass A progress with status="running" -> Pass B refuses.
            protocol.write_progress_atomic(
                p3 / "pass_a_progress.json",
                protocol.ProgressState(
                    pass_="A", unit="section", cursor=2, total=10,
                    status="running", last_updated="2026-04-27T00:00:00Z",
                ),
            )
            (p3 / "pass_a_drafts.jsonl").write_text("", encoding="utf-8")

            with self.assertRaises(protocol.UpstreamIncompleteError) as cm:
                main_mod._main([str(tmp), "--pass", "B", "--runner", "claude"])
            self.assertIn("Pass B refused to start", str(cm.exception))

    def test_pass_c_refuses_when_pass_b_incomplete(self) -> None:
        """B4 gate at the C-of-A->B->C->D transition."""
        with TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            _build_synthetic_fixture(tmp)
            p3 = tmp / "quality" / "phase3"
            p3.mkdir(parents=True, exist_ok=True)
            # Pass A complete, Pass B not.
            protocol.write_progress_atomic(
                p3 / "pass_a_progress.json",
                protocol.ProgressState(
                    pass_="A", unit="section", cursor=4, total=4,
                    status="complete", last_updated="2026-04-27T00:00:00Z",
                ),
            )
            protocol.write_progress_atomic(
                p3 / "pass_b_progress.json",
                protocol.ProgressState(
                    pass_="B", unit="draft", cursor=2, total=4,
                    status="running", last_updated="2026-04-27T00:00:00Z",
                ),
            )
            (p3 / "pass_b_citations.jsonl").write_text("", encoding="utf-8")

            with self.assertRaises(protocol.UpstreamIncompleteError) as cm:
                main_mod._main([str(tmp), "--pass", "C", "--runner", "claude"])
            self.assertIn("Pass C refused to start", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
