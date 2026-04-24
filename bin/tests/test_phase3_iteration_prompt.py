"""Regression test for Phase 3 iteration-mode MANDATORY INCREMENTAL WRITE.

The phase3_prompt() body must continue to instruct reviewers running in
iteration mode to flush candidate BUG stubs to disk as they identify them.
The feature landed with Lever 2 (commit C7); this test guards against
accidental removal in future prompt rewrites.
"""

import unittest

from bin.run_playbook import phase3_prompt


class Phase3IterationPromptTests(unittest.TestCase):
    def test_prompt_contains_mandatory_incremental_write(self):
        body = phase3_prompt()
        self.assertIn("MANDATORY INCREMENTAL WRITE", body)
        self.assertIn("quality/code_reviews/", body)
        self.assertIn("candidates.md", body)


if __name__ == "__main__":
    unittest.main()
