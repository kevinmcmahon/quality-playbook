"""Phase prompt externalization tests (v1.5.4 F-1).

The phase prompt bodies live as markdown files under ``phase_prompts/``
at the QPB repo root, loaded by
``bin.run_playbook._load_phase_prompt``. Externalization is the single-
source-of-truth lever that lets UI-context skill-direct mode and
CLI-automation runner-driven mode read the same content.

These tests pin two contracts:

1. **Loader contract** — verbatim return for pure-literal prompts,
   ``str.format()`` substitution for parameterized prompts, missing
   files raise FileNotFoundError loudly.

2. **File presence contract** — every phase prompt + the single_pass
   and iteration prompts have a corresponding markdown file. If a
   future edit deletes one, this test fires before downstream gates
   silently regress.

The byte-equality regression — that `phaseN_prompt()` outputs the
exact bytes the legacy in-source f-string templates produced — is
covered implicitly by the existing prompt-content tests in
test_run_playbook.py, test_phase3_iteration_prompt.py,
test_phase3_prompt_worked_example.py, and test_role_tagging.py.
Those tests pin substrings that would shift if externalization
introduced any character drift.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from bin import run_playbook


PHASE_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "phase_prompts"


class PhasePromptsDirectoryTests(unittest.TestCase):
    """File presence contract: every prompt the orchestrator loads
    must have a corresponding markdown file."""

    def test_phase_prompts_dir_exists_at_repo_root(self) -> None:
        self.assertTrue(
            PHASE_PROMPTS_DIR.is_dir(),
            f"phase_prompts/ not found at {PHASE_PROMPTS_DIR}",
        )

    def test_all_six_phase_files_present(self) -> None:
        for n in range(1, 7):
            path = PHASE_PROMPTS_DIR / f"phase{n}.md"
            self.assertTrue(path.is_file(), f"missing {path}")

    def test_single_pass_and_iteration_files_present(self) -> None:
        for name in ("single_pass.md", "iteration.md"):
            self.assertTrue(
                (PHASE_PROMPTS_DIR / name).is_file(),
                f"missing phase_prompts/{name}",
            )

    def test_readme_present(self) -> None:
        self.assertTrue(
            (PHASE_PROMPTS_DIR / "README.md").is_file(),
            "phase_prompts/ should carry a README explaining the layout",
        )


class LoaderContractTests(unittest.TestCase):
    """Loader contract: `_load_phase_prompt(name)` returns file contents
    verbatim; `_load_phase_prompt(name, **subs)` applies str.format()."""

    def test_loader_returns_file_verbatim_when_no_substitutions(self) -> None:
        # phase2 is a pure-literal file; the loader must return its
        # bytes unchanged.
        text = run_playbook._load_phase_prompt("phase2")
        on_disk = (PHASE_PROMPTS_DIR / "phase2.md").read_text(encoding="utf-8")
        self.assertEqual(text, on_disk)

    def test_loader_applies_substitutions_when_provided(self) -> None:
        # iteration.md uses {strategy} substitution.
        text = run_playbook._load_phase_prompt(
            "iteration",
            skill_fallback_guide="GUIDE",
            strategy="parity",
        )
        # The "{strategy}" placeholder should be substituted.
        self.assertIn("using the parity strategy", text)
        self.assertNotIn("{strategy}", text)

    def test_loader_missing_file_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            run_playbook._load_phase_prompt("does_not_exist")

    def test_loader_pure_literal_phase_files_have_no_unescaped_braces(self) -> None:
        """Pure-literal phase files (phase2..phase6) skip .format() so
        their JSON code blocks can use single { without escaping. This
        test pins that they are NOT mistakenly run through .format()
        — if a future loader change introduces unconditional
        formatting, the JSON braces would explode."""
        for n in range(2, 7):
            text = run_playbook._load_phase_prompt(f"phase{n}")
            # The loader returns the file unchanged. We re-check by
            # reading the file directly and confirming equality.
            on_disk = (PHASE_PROMPTS_DIR / f"phase{n}.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(text, on_disk, f"phase{n} loader drift")


class FormatStringEscapingTests(unittest.TestCase):
    """Files that go through .format() must double-escape literal
    braces. Pure-literal files must NOT — otherwise their JSON code
    blocks would render with double braces in the output."""

    def test_phase1_uses_double_braces_for_json(self) -> None:
        """phase1.md goes through .format(); JSON code blocks must use
        {{ / }} so they render as { / } after substitution."""
        raw = (PHASE_PROMPTS_DIR / "phase1.md").read_text(encoding="utf-8")
        # The role-map schema JSON in phase1.md is the load-bearing
        # case. It must contain `{{` (which becomes `{` after format).
        self.assertIn('{{\n  "schema_version"', raw)

    def test_phase3_uses_single_braces_for_json(self) -> None:
        """phase3.md is pure-literal (no substitutions); JSON code
        blocks use single { directly."""
        raw = (PHASE_PROMPTS_DIR / "phase3.md").read_text(encoding="utf-8")
        # The compensation-grid schema JSON in phase3.md uses single
        # braces because we never call .format() on it.
        self.assertIn('{\n  "schema_version": "1.5.2"', raw)


class CursorRunnerStdinPipingTests(unittest.TestCase):
    """v1.5.4 F-1 also ensured the cursor runner pipes the prompt on
    stdin (verified against cursor-cli 3.1.10). Pin the runner-side
    branch so a future refactor can't quietly switch cursor to argv
    passing and hit argv-length limits on long phase prompts."""

    def test_run_prompt_pipes_stdin_for_cursor(self) -> None:
        # The branch under test lives at the run_prompt subprocess
        # call site: runner in ("codex", "cursor") sets
        # run_kwargs["input"] = prompt. We grep for the literal tuple
        # to pin it without booting subprocess.run.
        src = Path(run_playbook.__file__).read_text(encoding="utf-8")
        self.assertIn('runner in ("codex", "cursor")', src)


if __name__ == "__main__":
    unittest.main()
