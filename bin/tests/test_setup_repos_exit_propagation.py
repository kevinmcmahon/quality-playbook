"""v1.5.1 Phase 1 rev (Council — gpt-5.4 blocker 1):
repos/setup_repos.sh must propagate stage_formal_docs.py failures
instead of swallowing them with `|| true`. These tests drive the real
setup_repos.sh against a hermetic fixture tree and verify both the
loud-failure path and the happy path.

Stdlib-only. The fixture fakes QPB_SKILL_DIR + a clean/<repo> + a
docs_gathered/<repo>, then substitutes stage_formal_docs.py either
with the real one (happy path) or a one-liner that exits 1
(failure fixture).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REAL_SETUP = REPO_ROOT / "repos" / "setup_repos.sh"
REAL_LIB = REPO_ROOT / "repos" / "_benchmark_lib.sh"
REAL_STAGER = REPO_ROOT / "repos" / "stage_formal_docs.py"
REAL_TIERS = REPO_ROOT / "repos" / "formal_docs_tiers.json"
REAL_HELPER = REPO_ROOT / "bin" / "setup_formal_docs.py"


def _materialize_fixture(tmp: Path, *, failing_stager: bool) -> Path:
    """Build a minimal, self-contained QPB-like tree under tmp and return
    the path to the fake repos/ directory (where setup_repos.sh lives)."""

    qpb_root = tmp / "qpb"
    qpb_root.mkdir()
    (qpb_root / "SKILL.md").write_text(
        "---\nname: fixture\nmetadata:\n  version: 1.4.6\n---\n",
        encoding="utf-8",
    )
    # setup_repos.sh cp's references/*, LICENSE.txt, and quality_gate.py
    # from QPB_DIR with "|| true" — their absence is tolerated.

    repos_dir = qpb_root / "repos"
    repos_dir.mkdir()
    shutil.copy2(REAL_SETUP, repos_dir / "setup_repos.sh")
    shutil.copy2(REAL_LIB, repos_dir / "_benchmark_lib.sh")
    shutil.copy2(REAL_TIERS, repos_dir / "formal_docs_tiers.json")

    if failing_stager:
        # Stager that prints a marker line and exits non-zero.
        (repos_dir / "stage_formal_docs.py").write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "print('FIXTURE: stager crashed intentionally', file=sys.stderr)\n"
            "sys.exit(1)\n",
            encoding="utf-8",
        )
    else:
        # Happy path: use the real stager, but it needs bin/setup_formal_docs.py
        # to exist somewhere it can find. The real stager defaults to
        # `<script_dir>/../bin/setup_formal_docs.py` — so place it at
        # <qpb_root>/bin/setup_formal_docs.py.
        shutil.copy2(REAL_STAGER, repos_dir / "stage_formal_docs.py")
        (qpb_root / "bin").mkdir()
        shutil.copy2(REAL_HELPER, qpb_root / "bin" / "setup_formal_docs.py")

    # clean/<repo> needs at least one tracked file so `cp -a` has something.
    clean_repo = repos_dir / "clean" / "fixture-repo"
    clean_repo.mkdir(parents=True)
    (clean_repo / "README").write_text("fixture\n", encoding="utf-8")

    # docs_gathered/<repo> triggers the staging block in setup_repos.sh.
    docs = repos_dir / "docs_gathered" / "fixture-repo"
    docs.mkdir(parents=True)
    (docs / "behavioral-spec.md").write_text(
        "# Behavioral contract\n\nMUST do X.\n", encoding="utf-8"
    )

    return repos_dir


def _run_setup(fake_repos_dir: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["QPB_SKILL_DIR"] = str(fake_repos_dir.parent)
    return subprocess.run(
        ["bash", str(fake_repos_dir / "setup_repos.sh"), "fixture-repo"],
        cwd=str(fake_repos_dir),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class SetupReposExitPropagationTests(unittest.TestCase):
    def test_staging_failure_aborts_and_does_not_print_ready(self) -> None:
        with TemporaryDirectory() as tmp:
            repos_dir = _materialize_fixture(Path(tmp), failing_stager=True)
            result = _run_setup(repos_dir)
            combined = (result.stdout or "") + (result.stderr or "")
            self.assertNotEqual(
                result.returncode, 0,
                f"expected non-zero exit, got 0. Output:\n{combined}",
            )
            self.assertIn(
                "Staging formal_docs failed for fixture-repo", combined,
                f"expected loud failure message. Output:\n{combined}",
            )
            self.assertNotIn(
                "✓ fixture-repo-1.4.6 ready", combined,
                f"happy-path marker leaked into failure run. Output:\n{combined}",
            )

    def test_staging_happy_path_exits_clean_and_stages_sidecars(self) -> None:
        with TemporaryDirectory() as tmp:
            repos_dir = _materialize_fixture(Path(tmp), failing_stager=False)
            result = _run_setup(repos_dir)
            combined = (result.stdout or "") + (result.stderr or "")
            self.assertEqual(
                result.returncode, 0,
                f"expected clean exit, got {result.returncode}. Output:\n{combined}",
            )
            self.assertIn(
                "✓ fixture-repo-1.4.6 ready", combined,
                f"happy-path marker missing. Output:\n{combined}",
            )
            staged = repos_dir / "fixture-repo-1.4.6" / "formal_docs"
            self.assertTrue(staged.is_dir(), f"formal_docs/ not created at {staged}")
            self.assertTrue(
                (staged / "behavioral-spec.md").is_file(),
                "plaintext file did not pass through",
            )
            self.assertTrue(
                (staged / "behavioral-spec.meta.json").is_file(),
                "sidecar was not generated",
            )


if __name__ == "__main__":
    unittest.main()
