from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
import re
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

    def test_find_repo_dir_prefers_exact_version(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            exact = temp_path / "chi-1.4.2"
            exact.mkdir()
            (temp_path / "chi-1.4.1").mkdir()
            self.assertEqual(lib.find_repo_dir("chi", "1.4.2", repos_dir=temp_path), exact)

    def test_find_repo_dir_falls_back_to_highest_version(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "cobra-1.4.0").mkdir()
            latest = temp_path / "cobra-1.4.9"
            latest.mkdir()
            (temp_path / "cobra-1.4.9-claude").mkdir()
            self.assertEqual(lib.find_repo_dir("cobra", "1.5.0", repos_dir=temp_path), latest)

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

    def test_repo_short_name_strips_version_suffix(self) -> None:
        self.assertEqual(lib.repo_short_name(Path("virtio-1.4.2")), "virtio")
        self.assertEqual(lib.repo_short_name(Path("virtio")), "virtio")

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


if __name__ == "__main__":
    unittest.main()