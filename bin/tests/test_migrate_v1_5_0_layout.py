"""Tests for bin/migrate_v1_5_0_layout.py."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin import migrate_v1_5_0_layout as mig


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _init_git(repo: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)


def _commit(repo: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", message, "--allow-empty"],
        cwd=repo,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class PlanAndMoveTests(unittest.TestCase):
    def test_full_legacy_layout_migrates_both(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo / "previous_runs" / "20260418-120000" / "quality" / "BUGS.md", "legacy")
            _write(repo / "control_prompts" / "phase1.output.txt", "prompt body")

            mig.migrate(repo)

            self.assertFalse((repo / "previous_runs").exists())
            self.assertFalse((repo / "control_prompts").exists())
            self.assertTrue(
                (repo / "quality" / "runs" / "20260418-120000" / "quality" / "BUGS.md").is_file()
            )
            self.assertTrue(
                (repo / "quality" / "control_prompts" / "phase1.output.txt").is_file()
            )

    def test_idempotent_second_invocation_is_noop(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo / "previous_runs" / "20260418-120000" / "quality" / "BUGS.md", "legacy")
            _write(repo / "control_prompts" / "phase1.output.txt", "prompt")
            mig.migrate(repo)
            before = sorted(p.relative_to(repo).as_posix() for p in (repo / "quality").rglob("*"))

            mig.migrate(repo)
            after = sorted(p.relative_to(repo).as_posix() for p in (repo / "quality").rglob("*"))
            self.assertEqual(before, after)

    def test_half_migrated_completes_remaining_half(self) -> None:
        """previous_runs present, control_prompts already moved — migration still runs for prev."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo / "previous_runs" / "20260418-120000" / "quality" / "BUGS.md", "legacy")
            # Assume a prior invocation already moved control_prompts
            _write(repo / "quality" / "control_prompts" / "phase1.output.txt", "prompt")

            mig.migrate(repo)

            self.assertFalse((repo / "previous_runs").exists())
            self.assertTrue(
                (repo / "quality" / "runs" / "20260418-120000" / "quality" / "BUGS.md").is_file()
            )
            # control_prompts already under quality/ — left as-is.
            self.assertTrue((repo / "quality" / "control_prompts" / "phase1.output.txt").is_file())

    def test_half_migrated_completes_control_prompts_half(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo / "control_prompts" / "phase1.output.txt", "prompt")
            # quality/runs/ already exists from a prior invocation
            _write(repo / "quality" / "runs" / "20260418-120000" / "quality" / "BUGS.md", "legacy")

            mig.migrate(repo)

            self.assertFalse((repo / "control_prompts").exists())
            self.assertTrue((repo / "quality" / "control_prompts" / "phase1.output.txt").is_file())

    def test_dry_run_does_not_write(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo / "previous_runs" / "20260418-120000" / "quality" / "BUGS.md", "legacy")
            _write(repo / "control_prompts" / "phase1.output.txt", "prompt")

            mig.migrate(repo, dry_run=True)

            # Dry-run leaves legacy dirs in place.
            self.assertTrue((repo / "previous_runs").is_dir())
            self.assertTrue((repo / "control_prompts").is_dir())
            self.assertFalse((repo / "quality" / "runs").exists())
            self.assertFalse((repo / "quality" / "control_prompts").exists())

    def test_empty_previous_runs_moves_cleanly(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "previous_runs").mkdir()
            mig.migrate(repo)
            self.assertFalse((repo / "previous_runs").exists())
            self.assertTrue((repo / "quality" / "runs").is_dir())
            self.assertEqual(list((repo / "quality" / "runs").iterdir()), [])

    def test_refuses_when_destination_exists_for_previous_runs(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo / "previous_runs" / "20260418-120000" / "quality" / "BUGS.md", "legacy")
            # A pre-existing quality/runs/ with non-empty contents blocks the move.
            _write(repo / "quality" / "runs" / "something" / "INDEX.md", "existing")
            with self.assertRaises(mig.MigrationError):
                mig.migrate(repo)


class IndexBackfillTests(unittest.TestCase):
    def _make_legacy_run(self, repo: Path, run_id: str) -> Path:
        run_folder = repo / "previous_runs" / run_id
        _write(
            run_folder / "quality" / "BUGS.md",
            """# Bug Report: test

<!-- Quality Playbook v1.4.3 — Phase 3 -->

### BUG-001

**Severity**: HIGH

Body of bug 001.

### BUG-002

**Severity**: MEDIUM

Body of bug 002.

### BUG-003

**Severity**: LOW

Body of bug 003.
""",
        )
        _write(
            run_folder / "quality" / "REQUIREMENTS.md",
            """# Requirements

### REQ-001: First
body

### REQ-002: Second
body
""",
        )
        _write(
            run_folder / "quality" / "PROGRESS.md",
            """## Phase completion

- [x] Phase 1: Exploration
- [x] Phase 2: Generation
- [ ] Phase 3: Code review
""",
        )
        return run_folder

    def test_backfill_writes_index_md_with_fields(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_git(repo)
            self._make_legacy_run(repo, "20260418-120000")
            _commit(repo, "initial import")

            mig.migrate(repo)

            index_path = repo / "quality" / "runs" / "20260418-120000" / "INDEX.md"
            self.assertTrue(index_path.is_file())
            text = index_path.read_text(encoding="utf-8")
            self.assertIn("# Run Index — 20260418-120000", text)
            # JSON block parses.
            payload = mig._load_existing_index_payload(index_path)
            self.assertIsNotNone(payload)
            self.assertEqual(payload["qpb_version"], "1.4.3")
            self.assertEqual(payload["summary"]["bugs"]["HIGH"], 1)
            self.assertEqual(payload["summary"]["bugs"]["MEDIUM"], 1)
            self.assertEqual(payload["summary"]["bugs"]["LOW"], 1)
            # Legacy REQs (no **Tier** field) count as "unknown".
            self.assertEqual(payload["summary"]["requirements"]["unknown"], 2)
            self.assertEqual(
                sorted(p["phase_id"] for p in payload["phases_executed"]),
                ["1", "2"],
            )

    def test_run_index_md_has_row_per_run(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_git(repo)
            self._make_legacy_run(repo, "20260418-120000")
            self._make_legacy_run(repo, "20260419-120000")
            _commit(repo, "init")

            mig.migrate(repo)

            run_index = repo / "quality" / "RUN_INDEX.md"
            self.assertTrue(run_index.is_file())
            text = run_index.read_text(encoding="utf-8")
            self.assertIn("| Run | QPB version |", text)
            self.assertIn("20260418-120000", text)
            self.assertIn("20260419-120000", text)
            self.assertIn("[INDEX.md](quality/runs/20260418-120000/INDEX.md)", text)

    def test_existing_index_md_is_preserved(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_git(repo)
            run = self._make_legacy_run(repo, "20260418-120000")
            # Pre-write INDEX.md to simulate a run that already has one.
            existing_index = run / "INDEX.md"
            preserved_content = "# Existing\n\n```json\n{\"qpb_version\": \"custom\"}\n```\n"
            _write(existing_index, preserved_content)
            _commit(repo, "init")

            mig.migrate(repo)

            final_path = repo / "quality" / "runs" / "20260418-120000" / "INDEX.md"
            self.assertEqual(final_path.read_text(encoding="utf-8"), preserved_content)

    def test_gate_verdict_pass_detected_from_run_json(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_git(repo)
            run = self._make_legacy_run(repo, "20260418-120000")
            _write(
                run / "quality" / "results" / "run-2026-04-18T19-35-42.json",
                json.dumps({"gate_result": "PASS", "skill_version": "1.4.3"}),
            )
            _commit(repo, "init")

            mig.migrate(repo)

            index = repo / "quality" / "runs" / "20260418-120000" / "INDEX.md"
            payload = mig._load_existing_index_payload(index)
            self.assertEqual(payload["summary"]["gate_verdict"], "pass")


class CLITests(unittest.TestCase):
    def test_cli_dry_run_exits_zero(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo / "control_prompts" / "phase1.output.txt", "prompt")
            self.assertEqual(mig.main([str(repo), "--dry-run"]), 0)

    def test_cli_real_invocation_exits_zero(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo / "control_prompts" / "phase1.output.txt", "prompt")
            self.assertEqual(mig.main([str(repo)]), 0)
            self.assertTrue((repo / "quality" / "control_prompts" / "phase1.output.txt").is_file())

    def test_cli_nonexistent_repo_errors(self) -> None:
        self.assertEqual(mig.main(["/no/such/path/should/exist/ever/xyz"]), 1)


if __name__ == "__main__":
    unittest.main()
