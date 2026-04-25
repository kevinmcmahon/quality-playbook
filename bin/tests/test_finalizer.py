"""Tests for bin/run_playbook.py::_finalize_iteration (C13.9).

The finalizer subprocesses quality_gate.py against a target repo, captures
its real output to quality/results/quality-gate.log (preserving the existing
artifact contract), and appends a structured ## Run finalization block to
quality/PROGRESS.md. Mocks subprocess.run so tests don't depend on the live
gate script being installed.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bin.run_playbook import _finalize_iteration


class _FakeCompleted:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _make_repo(tmp: Path, *, with_gate: bool = True, with_progress: str = None,
               bug_writeup_count: int = 0) -> Path:
    """Build a minimal repo at ``tmp`` with quality/ dir and optional fixtures."""
    repo = tmp / "repo"
    repo.mkdir()
    (repo / "quality").mkdir()
    if with_gate:
        gate = repo / ".github" / "skills"
        gate.mkdir(parents=True)
        (gate / "quality_gate.py").write_text("# stub\n", encoding="utf-8")
    if with_progress is not None:
        (repo / "quality" / "PROGRESS.md").write_text(with_progress, encoding="utf-8")
    if bug_writeup_count > 0:
        writeups = repo / "quality" / "writeups"
        writeups.mkdir()
        for i in range(1, bug_writeup_count + 1):
            (writeups / f"BUG-{i:03d}.md").write_text(f"# BUG-{i:03d}\n", encoding="utf-8")
    return repo


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


class FinalizerUnitTests(unittest.TestCase):

    # ---- Test 1 ----
    def test_finalizer_writes_log_on_clean_gate_run(self):
        with tempfile.TemporaryDirectory() as d:
            repo = _make_repo(Path(d))
            log_file = repo / "run.log"
            with mock.patch("bin.run_playbook.subprocess.run",
                            return_value=_FakeCompleted(0, stdout="GATE PASSED\n")):
                status = _finalize_iteration(repo, "post-test", log_file)
            self.assertEqual(status, "pass")
            log = _read(repo / "quality" / "results" / "quality-gate.log")
            self.assertIn("GATE PASSED", log)

    # ---- Test 2 ----
    def test_finalizer_writes_log_on_failing_gate(self):
        with tempfile.TemporaryDirectory() as d:
            repo = _make_repo(Path(d))
            log_file = repo / "run.log"
            with mock.patch("bin.run_playbook.subprocess.run",
                            return_value=_FakeCompleted(1, stdout="GATE FAILED: uncovered cells\n")):
                status = _finalize_iteration(repo, "post-test", log_file)
            self.assertEqual(status, "fail")
            log = _read(repo / "quality" / "results" / "quality-gate.log")
            self.assertIn("GATE FAILED: uncovered cells", log)

    # ---- Test 3 ----
    def test_finalizer_returns_aborted_regardless_of_gate_exit(self):
        with tempfile.TemporaryDirectory() as d:
            repo = _make_repo(Path(d))
            log_file = repo / "run.log"
            with mock.patch("bin.run_playbook.subprocess.run",
                            return_value=_FakeCompleted(0, stdout="GATE PASSED\n")):
                status = _finalize_iteration(
                    repo, "abort-during-adversarial", log_file,
                    aborted=True, abort_reason="runner exited 2",
                )
            self.assertEqual(status, "aborted")
            progress = _read(repo / "quality" / "PROGRESS.md")
            self.assertIn("Gate status: ABORTED", progress)
            self.assertIn("Abort reason: runner exited 2", progress)
            # The gate ran; its output is captured but not authoritative.
            log = _read(repo / "quality" / "results" / "quality-gate.log")
            self.assertIn("GATE PASSED", log)

    # ---- Test 4 ----
    def test_finalizer_appends_to_progress_md(self):
        original = "# Progress\n\n## Phase 1 complete\n\n2026-04-25T12:00:00Z\n"
        with tempfile.TemporaryDirectory() as d:
            repo = _make_repo(Path(d), with_progress=original)
            log_file = repo / "run.log"
            with mock.patch("bin.run_playbook.subprocess.run",
                            return_value=_FakeCompleted(0, stdout="GATE PASSED\n")):
                _finalize_iteration(repo, "post-phase-6", log_file)
            progress = _read(repo / "quality" / "PROGRESS.md")
            self.assertTrue(progress.startswith(original),
                            "Original PROGRESS.md content must be preserved verbatim.")
            self.assertIn("## Run finalization (post-phase-6)", progress)

    # ---- Test 5 ----
    def test_finalizer_creates_progress_md_when_absent(self):
        with tempfile.TemporaryDirectory() as d:
            repo = _make_repo(Path(d))  # no PROGRESS.md
            log_file = repo / "run.log"
            self.assertFalse((repo / "quality" / "PROGRESS.md").exists())
            with mock.patch("bin.run_playbook.subprocess.run",
                            return_value=_FakeCompleted(0, stdout="GATE PASSED\n")):
                _finalize_iteration(repo, "post-singlepass", log_file)
            progress = _read(repo / "quality" / "PROGRESS.md")
            self.assertIn("## Run finalization (post-singlepass)", progress)

    # ---- Test 6 ----
    def test_finalizer_idempotent_call_appends_second_block(self):
        with tempfile.TemporaryDirectory() as d:
            repo = _make_repo(Path(d))
            log_file = repo / "run.log"
            with mock.patch("bin.run_playbook.subprocess.run",
                            return_value=_FakeCompleted(0, stdout="GATE PASSED\n")):
                _finalize_iteration(repo, "post-test", log_file)
                _finalize_iteration(repo, "post-test", log_file)
            progress = _read(repo / "quality" / "PROGRESS.md")
            # Two blocks, both with the same label.
            self.assertEqual(progress.count("## Run finalization (post-test)"), 2)
            # Log got overwritten — only one copy of the gate output.
            log = _read(repo / "quality" / "results" / "quality-gate.log")
            self.assertEqual(log.count("GATE PASSED"), 1)

    # ---- Test 7 ----
    def test_finalizer_handles_missing_gate_script(self):
        with tempfile.TemporaryDirectory() as d:
            repo = _make_repo(Path(d), with_gate=False)
            log_file = repo / "run.log"
            with mock.patch("bin.run_playbook.subprocess.run") as mock_run:
                status = _finalize_iteration(repo, "post-test", log_file)
            self.assertEqual(status, "fail")
            mock_run.assert_not_called()
            progress = _read(repo / "quality" / "PROGRESS.md")
            self.assertIn("Gate status: FAIL", progress)
            self.assertIn("not produced — gate script not found", progress)

    # ---- Test 8 ----
    def test_finalizer_handles_subprocess_timeout(self):
        with tempfile.TemporaryDirectory() as d:
            repo = _make_repo(Path(d))
            log_file = repo / "run.log"
            timeout_exc = subprocess.TimeoutExpired(cmd=["python3"], timeout=120)
            with mock.patch("bin.run_playbook.subprocess.run", side_effect=timeout_exc):
                status = _finalize_iteration(repo, "post-test", log_file)
            self.assertEqual(status, "fail")
            log = _read(repo / "quality" / "results" / "quality-gate.log")
            self.assertIn("gate timed out after 120s", log)

    # ---- Test 9 ----
    def test_finalizer_skips_when_quality_missing(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d) / "repo"
            repo.mkdir()
            # Deliberately no quality/ directory.
            log_file = repo / "run.log"
            with mock.patch("bin.run_playbook.subprocess.run") as mock_run:
                status = _finalize_iteration(repo, "post-test", log_file)
            self.assertEqual(status, "pass")
            mock_run.assert_not_called()
            self.assertFalse((repo / "quality").exists(),
                             "Finalizer must not create quality/ when it doesn't exist.")

    # ---- Test 10 ----
    def test_finalizer_bug_count_matches_count_bug_writeups(self):
        with tempfile.TemporaryDirectory() as d:
            repo = _make_repo(Path(d), bug_writeup_count=5)
            log_file = repo / "run.log"
            with mock.patch("bin.run_playbook.subprocess.run",
                            return_value=_FakeCompleted(0, stdout="GATE PASSED\n")):
                _finalize_iteration(repo, "post-test", log_file)
            progress = _read(repo / "quality" / "PROGRESS.md")
            self.assertIn("Bug count: 5", progress)

    # ---- Test 11 ----
    def test_finalizer_does_not_overwrite_progress_with_synthetic_receipt(self):
        """The receipt is the gate's real output, written to quality-gate.log
        only. PROGRESS.md must NOT mirror that output (regression guard
        against the rev-1 design that wrote synthetic schema there)."""
        gate_output = "GATE PASSED\nDistinctive marker line for assertion\n"
        with tempfile.TemporaryDirectory() as d:
            repo = _make_repo(Path(d))
            # Pre-seed log with a fixture string we expect to be overwritten.
            (repo / "quality" / "results").mkdir(parents=True, exist_ok=True)
            (repo / "quality" / "results" / "quality-gate.log").write_text(
                "OLD STALE CONTENT", encoding="utf-8",
            )
            log_file = repo / "run.log"
            with mock.patch("bin.run_playbook.subprocess.run",
                            return_value=_FakeCompleted(0, stdout=gate_output)):
                _finalize_iteration(repo, "post-test", log_file)
            log = _read(repo / "quality" / "results" / "quality-gate.log")
            self.assertNotIn("OLD STALE CONTENT", log)
            self.assertIn("Distinctive marker line for assertion", log)
            progress = _read(repo / "quality" / "PROGRESS.md")
            self.assertNotIn("Distinctive marker line for assertion", progress,
                             "PROGRESS.md must not mirror gate output (rev-1 regression guard).")


if __name__ == "__main__":
    unittest.main()
