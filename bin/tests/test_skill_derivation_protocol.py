"""Tests for bin/skill_derivation/protocol.py — Per-Pass Execution Protocol."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin.skill_derivation import protocol


class ProgressFileTests(unittest.TestCase):
    def test_atomic_write_and_read_roundtrip(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "pass_a_progress.json"
            state = protocol.ProgressState(
                pass_="A",
                unit="section",
                cursor=3,
                total=10,
                status="running",
                last_updated="2026-04-26T12:00:00Z",
            )
            protocol.write_progress_atomic(path, state)
            roundtrip = protocol.read_progress(path)
            self.assertEqual(roundtrip, state)

    def test_progress_json_uses_pass_key_not_pass_underscore(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "pass_a_progress.json"
            state = protocol.ProgressState(
                pass_="A",
                unit="section",
                cursor=0,
                total=None,
                status="running",
                last_updated="2026-04-26T12:00:00Z",
            )
            protocol.write_progress_atomic(path, state)
            raw = json.loads(path.read_text())
            self.assertIn("pass", raw)
            self.assertNotIn("pass_", raw)
            self.assertEqual(raw["pass"], "A")

    def test_atomic_write_no_tmp_left_behind(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.json"
            state = protocol.ProgressState(
                pass_="A", unit="section", cursor=0, total=None,
                status="running", last_updated="2026-04-26T12:00:00Z",
            )
            protocol.write_progress_atomic(path, state)
            entries = sorted(p.name for p in Path(tmp).iterdir())
            self.assertEqual(entries, ["p.json"])

    def test_read_progress_absent_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertIsNone(protocol.read_progress(Path(tmp) / "missing.json"))

    def test_read_progress_empty_file_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.json"
            path.write_text("", encoding="utf-8")
            self.assertIsNone(protocol.read_progress(path))


class JsonlAppendTests(unittest.TestCase):
    def test_append_and_count(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "drafts.jsonl"
            protocol.append_jsonl(path, {"section_idx": 0, "title": "x"})
            protocol.append_jsonl(path, {"section_idx": 1, "title": "y"})
            self.assertEqual(protocol.count_jsonl_records(path), 2)

    def test_each_record_one_line(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "drafts.jsonl"
            protocol.append_jsonl(path, {"a": 1, "nested": {"b": 2}})
            protocol.append_jsonl(path, {"c": 3})
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0]), {"a": 1, "nested": {"b": 2}})
            self.assertEqual(json.loads(lines[1]), {"c": 3})


class LastRecordRecoveryTests(unittest.TestCase):
    def test_last_record_complete_file(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "drafts.jsonl"
            protocol.append_jsonl(path, {"section_idx": 0})
            protocol.append_jsonl(path, {"section_idx": 1})
            self.assertEqual(
                protocol.read_last_jsonl_record(path), {"section_idx": 1}
            )

    def test_partial_last_line_is_truncated_and_ignored(self) -> None:
        # Simulate a crash mid-write: the file has two complete
        # records and a partial third.
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "drafts.jsonl"
            path.write_text(
                '{"section_idx": 0}\n'
                '{"section_idx": 1}\n'
                '{"section_idx": 2, "tit',  # crash mid-record
                encoding="utf-8",
            )
            last = protocol.read_last_jsonl_record(path)
            self.assertEqual(last, {"section_idx": 1})
            # File should now end with a newline (partial line trimmed).
            content = path.read_text(encoding="utf-8")
            self.assertTrue(content.endswith("\n"))
            self.assertEqual(protocol.count_jsonl_records(path), 2)

    def test_only_partial_line_truncates_to_empty(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "drafts.jsonl"
            path.write_text('{"section_idx": 0, "tit', encoding="utf-8")
            last = protocol.read_last_jsonl_record(path)
            self.assertIsNone(last)
            self.assertEqual(path.read_text(), "")

    def test_absent_file_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertIsNone(
                protocol.read_last_jsonl_record(Path(tmp) / "missing.jsonl")
            )


class VerifyAndResumeTests(unittest.TestCase):
    def _setup_pass(self, tmp: str, *, drafts: list, cursor: int):
        jsonl = Path(tmp) / "drafts.jsonl"
        progress = Path(tmp) / "progress.json"
        for d in drafts:
            protocol.append_jsonl(jsonl, d)
        if cursor is not None:
            protocol.write_progress_atomic(
                progress,
                protocol.ProgressState(
                    pass_="A",
                    unit="section",
                    cursor=cursor,
                    total=None,
                    status="running",
                    last_updated="2026-04-26T12:00:00Z",
                ),
            )
        return jsonl, progress

    def test_agreement_returns_cursor_unchanged(self) -> None:
        with TemporaryDirectory() as tmp:
            jsonl, progress = self._setup_pass(
                tmp,
                drafts=[{"section_idx": 0}, {"section_idx": 1}, {"section_idx": 2}],
                cursor=3,
            )
            cursor = protocol.verify_and_resume(
                jsonl, progress, idx_field="section_idx"
            )
            self.assertEqual(cursor, 3)
            # Progress not rewritten -- notes remain empty.
            state = protocol.read_progress(progress)
            self.assertIsNotNone(state)
            self.assertEqual(state.notes, "")

    def test_progress_ahead_of_disk_rolls_back(self) -> None:
        with TemporaryDirectory() as tmp:
            # Disk has 2 records (idx 0, 1) but progress says cursor 5.
            jsonl, progress = self._setup_pass(
                tmp,
                drafts=[{"section_idx": 0}, {"section_idx": 1}],
                cursor=5,
            )
            cursor = protocol.verify_and_resume(
                jsonl, progress, idx_field="section_idx"
            )
            self.assertEqual(cursor, 2)
            state = protocol.read_progress(progress)
            self.assertEqual(state.cursor, 2)
            self.assertIn("verify-and-roll-back", state.notes)

    def test_progress_behind_disk_advances(self) -> None:
        with TemporaryDirectory() as tmp:
            # Disk has 5 records but progress says cursor 2.
            jsonl, progress = self._setup_pass(
                tmp,
                drafts=[
                    {"section_idx": 0},
                    {"section_idx": 1},
                    {"section_idx": 2},
                    {"section_idx": 3},
                    {"section_idx": 4},
                ],
                cursor=2,
            )
            cursor = protocol.verify_and_resume(
                jsonl, progress, idx_field="section_idx"
            )
            self.assertEqual(cursor, 5)

    def test_empty_disk_returns_zero(self) -> None:
        with TemporaryDirectory() as tmp:
            jsonl = Path(tmp) / "drafts.jsonl"
            progress = Path(tmp) / "progress.json"
            self.assertEqual(
                protocol.verify_and_resume(jsonl, progress, idx_field="section_idx"),
                0,
            )

    def test_disk_with_no_progress_file_initializes_to_disk_state(self) -> None:
        with TemporaryDirectory() as tmp:
            jsonl, progress = self._setup_pass(
                tmp,
                drafts=[{"section_idx": 0}, {"section_idx": 1}],
                cursor=None,  # no progress file
            )
            self.assertFalse(progress.exists())
            cursor = protocol.verify_and_resume(
                jsonl, progress, idx_field="section_idx"
            )
            self.assertEqual(cursor, 2)


class RecoveryPreambleTests(unittest.TestCase):
    def test_preamble_contains_required_anchors(self) -> None:
        rendered = protocol.render_recovery_preamble(
            pass_spec_path=Path("/path/to/spec.md"),
            progress_file_path=Path("/path/to/progress.json"),
        )
        # The Plan's required block names a few literal phrases that
        # must appear so a compacted-context LLM finds them by string
        # match.
        self.assertIn("auto-compaction", rendered)
        self.assertIn("Re-read the pass specification", rendered)
        self.assertIn("/path/to/spec.md", rendered)
        self.assertIn("/path/to/progress.json", rendered)
        self.assertIn("cursor", rendered.lower())
        self.assertIn("Disk is the source of truth", rendered)


if __name__ == "__main__":
    unittest.main()
