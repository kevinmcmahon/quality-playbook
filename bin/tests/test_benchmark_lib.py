from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

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


if __name__ == "__main__":
    unittest.main()