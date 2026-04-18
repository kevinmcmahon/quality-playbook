from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
import subprocess

from bin import benchmark_lib as lib


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class BenchmarkLibTests(unittest.TestCase):
    def test_detect_skill_version_reads_root_skill(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            write(temp_path / "SKILL.md", "version: 9.8.7\n")
            self.assertEqual(lib.detect_skill_version(temp_path), "9.8.7")

    def test_detect_repo_skill_version_reads_installed_copy(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            write(temp_path / ".github" / "skills" / "SKILL.md", "version: 1.4.2\n")
            self.assertEqual(lib.detect_repo_skill_version(temp_path), "1.4.2")

    def test_detect_repo_skill_version_falls_back_to_claude_and_root(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            write(temp_path / ".claude" / "skills" / "quality-playbook" / "SKILL.md", "version: 2.0.0\n")
            self.assertEqual(lib.detect_repo_skill_version(temp_path), "2.0.0")

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            write(temp_path / "SKILL.md", "version: 3.0.0\n")
            self.assertEqual(lib.detect_repo_skill_version(temp_path), "3.0.0")

        with TemporaryDirectory() as temp_dir:
            self.assertEqual(lib.detect_repo_skill_version(Path(temp_dir)), "")

    def test_find_installed_skill_returns_first_hit(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            gh_skill = temp_path / ".github" / "skills" / "SKILL.md"
            write(gh_skill, "version: 1.0.0\n")
            write(temp_path / "SKILL.md", "version: 2.0.0\n")
            # .github/skills/SKILL.md is searched first.
            self.assertEqual(lib.find_installed_skill(temp_path), gh_skill)

    def test_find_installed_skill_returns_none_when_absent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            self.assertIsNone(lib.find_installed_skill(Path(temp_dir)))

    def test_find_functional_and_regression_tests_skip_generated_dirs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir) / "virtio-1.4.2"
            write(repo_dir / "quality" / "node_modules" / "test_functional.py", "ignored")
            write(repo_dir / "quality" / "target" / "RegressionTest.java", "ignored")
            functional = repo_dir / "quality" / "test_functional.py"
            regression = repo_dir / "quality" / "RegressionTest.java"
            write(functional, "ok")
            write(regression, "ok")

            self.assertEqual(lib.find_functional_test(repo_dir), functional)
            self.assertEqual(lib.find_regression_test(repo_dir), regression)

    def test_cleanup_repo_reverts_tracked_changes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            subprocess.run(["git", "init"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
            tracked = repo_dir / "tracked.txt"
            write(tracked, "original\n")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repo_dir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            write(tracked, "changed\n")
            self.assertTrue(lib.cleanup_repo(repo_dir))
            self.assertEqual(tracked.read_text(encoding="utf-8"), "original\n")

    def test_count_matching_lines_uses_regex(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "requirements.md"
            write(path, "### REQ-001\n### REQ-002\nno match\nREQ-xyz\n")
            self.assertEqual(lib.count_matching_lines(path, r"### REQ-"), 2)
            self.assertEqual(lib.count_matching_lines(path, r"REQ-[0-9]{3}"), 2)

    def test_count_bug_writeups_counts_matching_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            write(repo_dir / "quality" / "writeups" / "BUG-001.md", "a")
            write(repo_dir / "quality" / "writeups" / "BUG-002.md", "b")
            write(repo_dir / "quality" / "writeups" / "NOTE.md", "c")
            self.assertEqual(lib.count_bug_writeups(repo_dir), 2)

    def test_print_summary_produces_expected_columns(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir) / "chi-1.4.2"
            for artifact in [
                "quality/REQUIREMENTS.md",
                "quality/BUGS.md",
                "quality/TDD_TRACEABILITY.md",
                "quality/RUN_INTEGRATION_TESTS.md",
            ]:
                write(repo_dir / artifact, "[Tier 1]\n[Tier 2]\n[Tier 3]\n### REQ-001\n### UC-01\nTDD verified\n")
            write(repo_dir / "quality" / "test_functional.py", "ok")
            write(repo_dir / "quality" / "test_regression.py", "ok")

            output = lib.print_summary([repo_dir])

            self.assertIn("=== Artifact Summary ===", output)
            self.assertIn("Repo", output)
            self.assertIn("REQS", output)
            self.assertIn("BUGS", output)
            self.assertIn("chi-1.4.2", output)
            self.assertIn("=== Quality Checks ===", output)

    def test_log_and_logboth_format_and_write(self) -> None:
        message = lib.log("hello")
        self.assertRegex(message, r"^\d{2}:\d{2}:\d{2} hello$")

        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "runner.log"
            with mock.patch("sys.stdout.isatty", return_value=False):
                lib.logboth(log_file, "stored line")
            self.assertEqual(log_file.read_text(encoding="utf-8"), "stored line\n")

    def test_version_resolution_helpers_are_gone(self) -> None:
        """Version-based repo resolution has been removed; positional args are now paths."""
        for name in ("REPOS_DIR", "SHORT_VERSIONED_DIR_PATTERN",
                     "find_repo_dir", "resolve_repos", "repo_short_name",
                     "version_key"):
            self.assertFalse(hasattr(lib, name), f"lib.{name} should have been removed")


if __name__ == "__main__":
    unittest.main()
