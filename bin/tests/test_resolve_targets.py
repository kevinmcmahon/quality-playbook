"""Tests for resolve_target_dirs() and the version-append fallback.

The fallback converts a bare target name (``chi``) into ``chi-<VERSION>`` when
the bare name doesn't exist on disk, where VERSION comes from SKILL.md at the
QPB root. This replaces the short-name lookup the retired
``repos/run_playbook.sh`` provided. It only triggers for bare names — anything
path-like (absolute, containing ``/``, starting with ``.`` / ``..`` / ``~``,
or with a Windows drive letter) is taken literally.

Every test monkeypatches ``benchmark_lib.QPB_DIR`` onto a synthetic root that
either contains a fake SKILL.md with a known ``version:`` line or doesn't.
Tests use ``tempfile.TemporaryDirectory``, no external fixtures.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from bin import benchmark_lib as lib
from bin import run_playbook


class FakeQPBRoot:
    """Context manager that swaps lib.QPB_DIR and chdir's into a synthetic cwd."""

    def __init__(self, *, version: str | None = "1.4.5",
                 cwd_has: tuple = (), qpb_skill: bool = True) -> None:
        self.version = version
        self.cwd_subdirs = cwd_has
        self.qpb_skill = qpb_skill

    def __enter__(self):
        self._qpb_dir_tmp = tempfile.TemporaryDirectory()
        self._cwd_tmp = tempfile.TemporaryDirectory()
        self.qpb_dir = Path(self._qpb_dir_tmp.name).resolve()
        self.cwd = Path(self._cwd_tmp.name).resolve()

        if self.qpb_skill:
            skill = self.qpb_dir / "SKILL.md"
            if self.version is not None:
                skill.write_text(
                    f"---\nname: quality-playbook\nversion: {self.version}\n---\n",
                    encoding="utf-8",
                )
            else:
                # SKILL.md exists but has no parseable version line.
                skill.write_text("---\nname: quality-playbook\n---\n", encoding="utf-8")
        # else: no SKILL.md at all

        for name in self.cwd_subdirs:
            (self.cwd / name).mkdir(parents=True, exist_ok=True)

        # Swap QPB_DIR and cwd for the duration.
        self._orig_qpb_dir = lib.QPB_DIR
        lib.QPB_DIR = self.qpb_dir
        self._orig_cwd = Path.cwd()
        os.chdir(self.cwd)
        return self

    def __exit__(self, exc_type, exc, tb):
        os.chdir(self._orig_cwd)
        lib.QPB_DIR = self._orig_qpb_dir
        self._cwd_tmp.cleanup()
        self._qpb_dir_tmp.cleanup()
        return False


class SkillVersionTests(unittest.TestCase):
    def test_returns_version_when_skill_md_present(self) -> None:
        with FakeQPBRoot(version="1.4.5") as ctx:
            self.assertEqual(lib.skill_version(), "1.4.5")

    def test_returns_none_when_skill_md_missing(self) -> None:
        with FakeQPBRoot(qpb_skill=False) as ctx:
            self.assertIsNone(lib.skill_version())

    def test_returns_none_when_no_version_line(self) -> None:
        with FakeQPBRoot(version=None) as ctx:
            self.assertIsNone(lib.skill_version())

    def test_handles_whitespace_and_extra_tokens(self) -> None:
        with FakeQPBRoot(version="1.4.5") as ctx:
            # Rewrite SKILL.md with indented version line + trailing comment
            (ctx.qpb_dir / "SKILL.md").write_text(
                "---\n  version:   9.9.9   # comment\n---\n", encoding="utf-8",
            )
            self.assertEqual(lib.skill_version(), "9.9.9")


class IsBareNameTests(unittest.TestCase):
    def test_plain_name_is_bare(self) -> None:
        self.assertTrue(run_playbook._is_bare_name("chi"))
        self.assertTrue(run_playbook._is_bare_name("virtio"))
        self.assertTrue(run_playbook._is_bare_name("some-project"))

    def test_absolute_is_not_bare(self) -> None:
        self.assertFalse(run_playbook._is_bare_name("/tmp/foo"))

    def test_slash_is_not_bare(self) -> None:
        self.assertFalse(run_playbook._is_bare_name("foo/bar"))
        self.assertFalse(run_playbook._is_bare_name("./chi"))
        self.assertFalse(run_playbook._is_bare_name("../foo"))

    def test_leading_dot_is_not_bare(self) -> None:
        self.assertFalse(run_playbook._is_bare_name("."))
        self.assertFalse(run_playbook._is_bare_name(".git"))
        self.assertFalse(run_playbook._is_bare_name(".."))

    def test_leading_tilde_is_not_bare(self) -> None:
        self.assertFalse(run_playbook._is_bare_name("~"))
        self.assertFalse(run_playbook._is_bare_name("~/project"))

    def test_windows_drive_letter_is_not_bare(self) -> None:
        self.assertFalse(run_playbook._is_bare_name("C:"))
        self.assertFalse(run_playbook._is_bare_name("C:\\Users"))

    def test_empty_is_not_bare(self) -> None:
        self.assertFalse(run_playbook._is_bare_name(""))


class ResolveTargetDirsFallbackTests(unittest.TestCase):
    def test_bare_name_exists_as_is_no_fallback(self) -> None:
        with FakeQPBRoot(version="1.4.5", cwd_has=("chi",)) as ctx:
            resolved, warnings, errors = run_playbook.resolve_target_dirs(["chi"])
            self.assertEqual(resolved, [ctx.cwd / "chi"])
            self.assertEqual(errors, [])

    def test_bare_name_exists_only_versioned_fallback_hits(self) -> None:
        with FakeQPBRoot(version="1.4.5", cwd_has=("chi-1.4.5",)) as ctx:
            resolved, warnings, errors = run_playbook.resolve_target_dirs(["chi"])
            self.assertEqual(resolved, [ctx.cwd / "chi-1.4.5"])
            self.assertEqual(errors, [])

    def test_bare_name_missing_both_error_mentions_both(self) -> None:
        with FakeQPBRoot(version="1.4.5") as ctx:
            resolved, warnings, errors = run_playbook.resolve_target_dirs(["chi"])
            self.assertEqual(resolved, [])
            self.assertEqual(len(errors), 1)
            self.assertIn("'chi' is not a directory", errors[0])
            self.assertIn("also tried 'chi-1.4.5'", errors[0])

    def test_absolute_path_missing_no_also_tried_clause(self) -> None:
        with FakeQPBRoot(version="1.4.5") as ctx:
            resolved, warnings, errors = run_playbook.resolve_target_dirs(["/nonexistent/target"])
            self.assertEqual(resolved, [])
            self.assertEqual(len(errors), 1)
            self.assertNotIn("also tried", errors[0])

    def test_relative_path_with_slash_no_fallback(self) -> None:
        with FakeQPBRoot(version="1.4.5") as ctx:
            # ./foo/bar doesn't exist; fallback must NOT be attempted
            resolved, warnings, errors = run_playbook.resolve_target_dirs(["./foo/bar"])
            self.assertEqual(resolved, [])
            self.assertEqual(len(errors), 1)
            self.assertNotIn("also tried", errors[0])

    def test_leading_dot_resolves_to_cwd_no_fallback(self) -> None:
        with FakeQPBRoot(version="1.4.5") as ctx:
            # "." is cwd, which exists → no error, no fallback attempt
            resolved, warnings, errors = run_playbook.resolve_target_dirs(["."])
            self.assertEqual(resolved, [ctx.cwd])
            self.assertEqual(errors, [])

    def test_home_prefix_missing_no_fallback(self) -> None:
        with FakeQPBRoot(version="1.4.5") as ctx:
            # Pick a path under ~ that definitely doesn't exist.
            missing = "~/qpb-testsuite-placeholder-that-does-not-exist"
            resolved, warnings, errors = run_playbook.resolve_target_dirs([missing])
            self.assertEqual(resolved, [])
            self.assertEqual(len(errors), 1)
            self.assertNotIn("also tried", errors[0])

    def test_skill_md_missing_bare_name_error_has_no_also_tried(self) -> None:
        with FakeQPBRoot(qpb_skill=False) as ctx:
            resolved, warnings, errors = run_playbook.resolve_target_dirs(["chi"])
            self.assertEqual(resolved, [])
            self.assertEqual(len(errors), 1)
            self.assertNotIn("also tried", errors[0])

    def test_skill_md_without_version_line_no_also_tried(self) -> None:
        with FakeQPBRoot(version=None) as ctx:
            resolved, warnings, errors = run_playbook.resolve_target_dirs(["chi"])
            self.assertEqual(resolved, [])
            self.assertEqual(len(errors), 1)
            self.assertNotIn("also tried", errors[0])

    def test_mixed_path_and_bare_name_both_resolve(self) -> None:
        with FakeQPBRoot(version="1.4.5") as ctx:
            explicit = ctx.cwd / "explicit-target"
            explicit.mkdir()
            (ctx.cwd / "cobra-1.4.5").mkdir()
            resolved, warnings, errors = run_playbook.resolve_target_dirs(
                [str(explicit), "cobra"]
            )
            self.assertEqual(
                resolved,
                [explicit, ctx.cwd / "cobra-1.4.5"],
            )
            self.assertEqual(errors, [])

    def test_fallback_prints_info_line_to_stderr(self) -> None:
        import io
        from contextlib import redirect_stderr

        with FakeQPBRoot(version="1.4.5", cwd_has=("chi-1.4.5",)) as ctx:
            buf = io.StringIO()
            with redirect_stderr(buf):
                resolved, _, errors = run_playbook.resolve_target_dirs(["chi"])
            self.assertEqual(errors, [])
            stderr_out = buf.getvalue()
            self.assertIn("INFO: resolved 'chi' to 'chi-1.4.5'", stderr_out)
            self.assertIn("via SKILL.md version", stderr_out)


if __name__ == "__main__":
    unittest.main()
