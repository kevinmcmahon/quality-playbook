"""Tests for bin/archive_lib.py (Phase 5c archival + INDEX rendering)."""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from bin import archive_lib as al


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _init_git(repo: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)


def _commit(repo: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", message, "--allow-empty"],
        cwd=repo,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _fixed_now() -> datetime:
    return datetime(2026, 4, 19, 14, 30, 22, tzinfo=timezone.utc)


class TimestampTests(unittest.TestCase):
    def test_utc_compact_format(self) -> None:
        self.assertEqual(al.utc_compact_timestamp(_fixed_now()), "20260419T143022Z")

    def test_utc_extended_format(self) -> None:
        self.assertEqual(al.utc_extended_timestamp(_fixed_now()), "2026-04-19T14:30:22Z")


class WriteTimestampedResultTests(unittest.TestCase):
    def test_writes_timestamped_and_latest_with_extension(self) -> None:
        with TemporaryDirectory() as tmp:
            quality = Path(tmp) / "quality"
            ts_path, latest_path = al.write_timestamped_result(
                quality,
                "recheck-results.json",
                "{\"ok\": true}",
                now=_fixed_now(),
            )
            self.assertEqual(ts_path.name, "recheck-results-20260419T143022Z.json")
            self.assertEqual(latest_path.name, "recheck-results-latest.json")
            self.assertTrue(ts_path.is_file())
            self.assertTrue(latest_path.exists())
            # Latest resolves to the timestamped file (symlink or copy).
            if latest_path.is_symlink():
                target = os.readlink(latest_path)
                self.assertEqual(target, ts_path.name)
            else:
                self.assertEqual(latest_path.read_text(encoding="utf-8"), "{\"ok\": true}")

    def test_writes_extensionless(self) -> None:
        with TemporaryDirectory() as tmp:
            quality = Path(tmp) / "quality"
            ts_path, latest_path = al.write_timestamped_result(
                quality,
                "gate-report",
                "pass",
                now=_fixed_now(),
            )
            self.assertEqual(ts_path.name, "gate-report-20260419T143022Z")
            self.assertEqual(latest_path.name, "gate-report-latest")

    def test_overwrites_latest_on_second_call(self) -> None:
        with TemporaryDirectory() as tmp:
            quality = Path(tmp) / "quality"
            first_now = datetime(2026, 4, 19, 10, 0, 0, tzinfo=timezone.utc)
            second_now = datetime(2026, 4, 19, 11, 0, 0, tzinfo=timezone.utc)
            al.write_timestamped_result(quality, "gate.json", "{\"v\": 1}", now=first_now)
            al.write_timestamped_result(quality, "gate.json", "{\"v\": 2}", now=second_now)
            latest = quality / "results" / "gate-latest.json"
            # latest should now point at the second write.
            if latest.is_symlink():
                target = os.readlink(latest)
                self.assertIn("11", target)  # second timestamp
            else:
                self.assertEqual(latest.read_text(encoding="utf-8"), "{\"v\": 2}")


class RunIndexRenderingTests(unittest.TestCase):
    def test_run_index_row_counts_bugs(self) -> None:
        payload = {
            "qpb_version": "1.5.0",
            "target_project_type": "Code",
            "summary": {
                "bugs": {"HIGH": 2, "MEDIUM": 3, "LOW": 1, "code-fix": 0, "spec-fix": 0},
                "gate_verdict": "pass",
            },
        }
        row = al.render_run_index_row("20260419T143022Z", payload)
        self.assertIn("| 20260419T143022Z ", row)
        self.assertIn("| 1.5.0 ", row)
        self.assertIn("| Code ", row)
        self.assertIn("| pass ", row)
        self.assertIn("| 6 ", row)  # 2+3+1
        self.assertIn("[INDEX.md](quality/runs/20260419T143022Z/INDEX.md)", row)

    def test_run_index_header_has_columns(self) -> None:
        h = al.render_run_index_header()
        self.assertIn("| Run | QPB version |", h)

    def test_index_markdown_contains_provenance(self) -> None:
        rendered = al.render_index_markdown(
            "20260419T143022Z",
            {"qpb_version": "1.5.0", "summary": {"bugs": {}, "gate_verdict": "pass"}},
            provenance="written by test",
        )
        self.assertIn("written by test", rendered)
        self.assertIn("# Run Index — 20260419T143022Z", rendered)
        self.assertIn("```json", rendered)


class AppendRunIndexRowTests(unittest.TestCase):
    def _payload(self, verdict: str = "pass") -> dict:
        return {
            "qpb_version": "1.5.0",
            "target_project_type": "Code",
            "summary": {"bugs": {"HIGH": 1}, "gate_verdict": verdict},
        }

    def test_creates_file_with_header_when_absent(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            al.append_run_index_row(repo, "20260419T100000Z", self._payload())
            text = (repo / "quality" / "RUN_INDEX.md").read_text(encoding="utf-8")
            self.assertIn("| Run | QPB version |", text)
            self.assertIn("| 20260419T100000Z ", text)

    def test_appends_to_existing_file_without_rewriting_prior_rows(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            al.append_run_index_row(repo, "20260419T100000Z", self._payload("pass"))
            al.append_run_index_row(repo, "20260420T100000Z", self._payload("partial"))
            text = (repo / "quality" / "RUN_INDEX.md").read_text(encoding="utf-8")
            self.assertIn("| 20260419T100000Z ", text)
            self.assertIn("| 20260420T100000Z ", text)
            # First row still says pass.
            first_row_line = next(
                line for line in text.splitlines() if "20260419T100000Z" in line
            )
            self.assertIn(" pass ", first_row_line)

    def test_is_idempotent_for_duplicate_run_id(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            al.append_run_index_row(repo, "20260419T100000Z", self._payload())
            before = (repo / "quality" / "RUN_INDEX.md").read_text(encoding="utf-8")
            al.append_run_index_row(repo, "20260419T100000Z", self._payload())
            after = (repo / "quality" / "RUN_INDEX.md").read_text(encoding="utf-8")
            self.assertEqual(before, after)


class ArchiveRunTests(unittest.TestCase):
    def _seed_live_run(self, repo: Path) -> None:
        _init_git(repo)
        _write(repo / "quality" / "BUGS.md", "# Bugs\n\n<!-- Quality Playbook v1.5.0 -->\n\n### BUG-001\n\n**Severity**: HIGH\n")
        _write(repo / "quality" / "REQUIREMENTS.md", "# Requirements\n\n### REQ-001\n\n**Tier**: 3\nBody.\n")
        _write(repo / "quality" / "PROGRESS.md", "## Phase completion\n\n- [x] Phase 1: Exploration\n- [x] Phase 2: Generation\n")
        _commit(repo, "seed run content")

    def test_success_archive_has_no_suffix(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._seed_live_run(repo)
            archive = al.archive_run(repo, "20260419T143022Z", status="success")
            self.assertEqual(archive.name, "20260419T143022Z")
            self.assertTrue((archive / "quality" / "BUGS.md").is_file())
            self.assertTrue((archive / "INDEX.md").is_file())
            self.assertTrue((repo / "quality" / "RUN_INDEX.md").is_file())
            # Live quality/ remains in place.
            self.assertTrue((repo / "quality" / "BUGS.md").is_file())

    def test_failed_archive_has_failed_suffix(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._seed_live_run(repo)
            archive = al.archive_run(repo, "20260419T143022Z", status="failed")
            self.assertEqual(archive.name, "20260419T143022Z-FAILED")
            payload = al.load_index_payload(archive / "INDEX.md")
            self.assertEqual(payload["summary"]["gate_verdict"], "fail")

    def test_partial_archive_has_partial_suffix(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._seed_live_run(repo)
            archive = al.archive_run(repo, "20260419T143022Z", status="partial")
            self.assertEqual(archive.name, "20260419T143022Z-PARTIAL")
            payload = al.load_index_payload(archive / "INDEX.md")
            self.assertEqual(payload["summary"]["gate_verdict"], "partial")

    def test_archive_refuses_when_target_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._seed_live_run(repo)
            al.archive_run(repo, "20260419T143022Z", status="success")
            with self.assertRaises(al.ArchiveError):
                al.archive_run(repo, "20260419T143022Z", status="success")

    def test_archive_excludes_runs_subtree(self) -> None:
        """archive_run must not recurse into quality/runs/ itself."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._seed_live_run(repo)
            # Pre-existing archived run should not be copied into the new archive.
            _write(repo / "quality" / "runs" / "priorrun" / "INDEX.md", "prior")
            archive = al.archive_run(repo, "20260419T143022Z", status="success")
            self.assertFalse((archive / "quality" / "runs").exists())

    def test_archive_run_appends_run_index_row(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._seed_live_run(repo)
            al.archive_run(repo, "20260419T143022Z", status="success")
            text = (repo / "quality" / "RUN_INDEX.md").read_text(encoding="utf-8")
            self.assertIn("20260419T143022Z", text)
            self.assertIn("[INDEX.md](quality/runs/20260419T143022Z/INDEX.md)", text)

    def test_archive_rejects_when_quality_missing(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with self.assertRaises(al.ArchiveError):
                al.archive_run(repo, "20260419T143022Z", status="success")

    def test_archive_rejects_invalid_status(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._seed_live_run(repo)
            with self.assertRaises(al.ArchiveError):
                al.archive_run(repo, "20260419T143022Z", status="cancelled")


class CLITests(unittest.TestCase):
    def test_cli_exits_zero_on_success(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_git(repo)
            _write(repo / "quality" / "BUGS.md", "# bugs\n")
            _commit(repo, "init")
            self.assertEqual(
                al.main([str(repo), "--status", "partial", "--timestamp", "20260419T143022Z"]),
                0,
            )
            self.assertTrue(
                (repo / "quality" / "runs" / "20260419T143022Z-PARTIAL" / "INDEX.md").is_file()
            )

    def test_cli_exits_one_on_missing_quality(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertEqual(
                al.main([str(repo), "--timestamp", "20260419T143022Z"]),
                1,
            )


if __name__ == "__main__":
    unittest.main()
