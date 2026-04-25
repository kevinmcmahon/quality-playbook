"""Tests for bin.run_playbook._mark_iterations_explicit (v1.5.2 Phase 6)."""

import unittest

from bin.run_playbook import _mark_iterations_explicit


class IterationsExplicitTests(unittest.TestCase):
    def test_explicit_iterations_list(self):
        argv = ["--iterations", "gap,unfiltered,parity,adversarial", "repo1"]
        self.assertTrue(_mark_iterations_explicit(argv))

    def test_full_run_expansion_not_explicit(self):
        argv = ["--full-run", "repo1"]
        self.assertFalse(_mark_iterations_explicit(argv))

    def test_single_strategy_is_explicit(self):
        argv = ["--strategy", "parity", "repo1"]
        self.assertTrue(_mark_iterations_explicit(argv))

    def test_full_run_with_iterations_flag_is_not_explicit(self):
        # --full-run always wins for the marker purpose.
        argv = ["--full-run", "--iterations", "gap", "repo1"]
        self.assertFalse(_mark_iterations_explicit(argv))

    def test_no_iteration_flag(self):
        argv = ["--phase", "all", "repo1"]
        self.assertFalse(_mark_iterations_explicit(argv))

    def test_mark_iterations_explicit_accepts_split_token_form(self):
        self.assertTrue(_mark_iterations_explicit(["--strategy", "adversarial"]))
        self.assertTrue(_mark_iterations_explicit(["--iterations", "3"]))

    def test_mark_iterations_explicit_accepts_combined_token_form(self):
        # argparse accepts --strategy=adversarial as a single combined token.
        # Round 7 Finding F: the legacy set-intersection check missed this.
        self.assertTrue(_mark_iterations_explicit(["--strategy=adversarial"]))
        self.assertTrue(_mark_iterations_explicit(["--iterations=3"]))
        self.assertTrue(_mark_iterations_explicit(["--strategy=parity,adversarial"]))

    def test_mark_iterations_explicit_full_run_overrides(self):
        self.assertFalse(_mark_iterations_explicit(["--strategy=adversarial", "--full-run"]))
        self.assertFalse(_mark_iterations_explicit(["--full-run"]))

    def test_mark_iterations_explicit_implicit_default(self):
        self.assertFalse(_mark_iterations_explicit([]))
        self.assertFalse(_mark_iterations_explicit(["--target", "/tmp/foo"]))


if __name__ == "__main__":
    unittest.main()
