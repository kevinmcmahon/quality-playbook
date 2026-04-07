import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RegressionTests(unittest.TestCase):
    @unittest.expectedFailure
    def test_install_instructions_copy_required_license_file(self):
        """[BUG from quality/code_reviews/2026-04-06-review.md]
        README.md and AGENTS.md install snippets omit LICENSE.txt even though the packaged skill ships it
        and the frontmatter points users to LICENSE.txt for the terms."""
        required_snippets = (
            "cp LICENSE.txt .github/skills/LICENSE.txt",
            "cp LICENSE.txt .claude/skills/quality-playbook/LICENSE.txt",
        )
        docs = (read(REPO_ROOT / "README.md"), read(REPO_ROOT / "AGENTS.md"))
        for snippet in required_snippets:
            self.assertTrue(any(snippet in doc for doc in docs), msg=f"Missing install step: {snippet}")

    @unittest.expectedFailure
    def test_readme_license_text_matches_shipped_license_file(self):
        """[BUG from quality/spec_audits/2026-04-06-triage.md]
        README.md advertises Apache 2.0 while the shipped LICENSE.txt files are MIT."""
        readme = read(REPO_ROOT / "README.md")
        license_text = read(REPO_ROOT / "LICENSE.txt")
        self.assertIn("MIT License", license_text)
        self.assertNotRegex(readme, r"Apache 2\.0")
        self.assertRegex(readme, r"\*\*License:\*\* MIT")

    @unittest.expectedFailure
    def test_readme_phase_summary_mentions_six_tracked_phases_and_verification(self):
        """[BUG from quality/code_reviews/2026-04-06-review.md]
        README.md still teaches a four-phase flow and omits the tracked 2b/2c/2d + verification lifecycle."""
        readme = read(REPO_ROOT / "README.md")
        self.assertNotIn("The playbook runs in four phases", readme)
        self.assertRegex(readme, r"Phase 2b")
        self.assertRegex(readme, r"Phase 2c")
        self.assertRegex(readme, r"Phase 2d")
        self.assertRegex(readme, r"Phase 3: Verification")

    @unittest.expectedFailure
    def test_skill_frontmatter_artifact_count_matches_body(self):
        """[BUG from quality/code_reviews/2026-04-06-review.md]
        SKILL.md frontmatter still advertises six quality artifacts while the body and output table define seven files."""
        skill = read(REPO_ROOT / "SKILL.md")
        self.assertNotIn("generate six quality artifacts", skill)
        self.assertIn("Seven files that together form a repeatable quality system", skill)

    @unittest.expectedFailure
    def test_readme_artifact_table_does_not_place_agents_md_under_quality_directory(self):
        """[BUG from quality/spec_audits/2026-04-06-triage.md]
        README says the listed artifacts are generated in `quality/`, but the same table includes root-level AGENTS.md."""
        readme = read(REPO_ROOT / "README.md")
        self.assertNotIn("The playbook generates these files in a `quality/` directory:", readme)
        self.assertRegex(readme, r"\| `AGENTS\.md` \|")


if __name__ == "__main__":
    unittest.main()
