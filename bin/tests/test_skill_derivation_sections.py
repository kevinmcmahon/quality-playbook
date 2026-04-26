"""Tests for bin/skill_derivation/sections.py — heading enumeration."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin.skill_derivation import sections


SKILL_FIXTURE = """\
# Document title

## Why This Exists

Meta prose; should be skipped via the allowlist.

## Phase 1: Explore the Codebase

Some operational prose.

### Sub-step

Sub-step prose.

## Phase 2: Plan

More prose.

```
## Run metadata

This heading is inside a fenced block; it must NOT be enumerated.
```

## Phase 3: Build

Closing prose.
"""


class FencedBlockAwarenessTests(unittest.TestCase):
    def test_fenced_block_heading_not_enumerated(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(SKILL_FIXTURE, encoding="utf-8")
            secs = sections.enumerate_sections(path, repo_root=Path(tmp))
            headings = [s.heading for s in secs]
            self.assertNotIn("Run metadata", headings)


class MetaAllowlistTests(unittest.TestCase):
    def test_why_this_exists_skipped(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(SKILL_FIXTURE, encoding="utf-8")
            secs = sections.enumerate_sections(path, repo_root=Path(tmp))
            why = [s for s in secs if s.heading == "Why This Exists"]
            self.assertEqual(len(why), 1)
            self.assertEqual(why[0].skip_reason, "meta-allowlist")

    def test_operational_section_not_skipped(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(SKILL_FIXTURE, encoding="utf-8")
            secs = sections.enumerate_sections(path, repo_root=Path(tmp))
            phase1 = [s for s in secs if s.heading.startswith("Phase 1")]
            self.assertEqual(len(phase1), 1)
            self.assertIsNone(phase1[0].skip_reason)


class IndexingTests(unittest.TestCase):
    def test_section_idx_monotonic(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(SKILL_FIXTURE, encoding="utf-8")
            secs = sections.enumerate_sections(path, repo_root=Path(tmp))
            idxs = [s.section_idx for s in secs]
            self.assertEqual(idxs, sorted(idxs))
            self.assertEqual(idxs, list(range(len(idxs))))

    def test_starting_idx_offsets_indexes(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(SKILL_FIXTURE, encoding="utf-8")
            secs = sections.enumerate_sections(
                path, repo_root=Path(tmp), starting_idx=100
            )
            self.assertEqual(secs[0].section_idx, 100)


SPLIT_FIXTURE_TEMPLATE = """\
# Doc

## Big Section

""" + ("filler line\n" * 350) + """\

### Subsection A

Sub A prose.

### Subsection B

Sub B prose.

## Small Section

Small prose.
"""


class SplitRuleTests(unittest.TestCase):
    def test_oversized_section_splits_into_subsections(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(SPLIT_FIXTURE_TEMPLATE, encoding="utf-8")
            secs = sections.enumerate_sections(path, repo_root=Path(tmp))
            headings = [s.heading for s in secs]
            # `Big Section` is over the threshold and has child ###s,
            # so its contained Subsection A and Subsection B are
            # emitted as their own iteration units; `Big Section`
            # itself is NOT emitted (the level-2 header alone would
            # double-count its child content).
            self.assertNotIn("Big Section", headings)
            self.assertIn("Subsection A", headings)
            self.assertIn("Subsection B", headings)
            # Small Section stays as a single level-2 unit.
            self.assertIn("Small Section", headings)


SMALL_SECTIONS_FIXTURE = """\
# Doc

## Small Section A

Brief prose.

### Sub of A

Sub prose; level-3 heading inside an under-threshold parent should
NOT be emitted as its own section.

## Small Section B

More brief prose.
"""


class SubSectionInferenceTests(unittest.TestCase):
    def test_small_parent_subsection_not_emitted(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(SMALL_SECTIONS_FIXTURE, encoding="utf-8")
            secs = sections.enumerate_sections(path, repo_root=Path(tmp))
            headings = [s.heading for s in secs]
            self.assertIn("Small Section A", headings)
            self.assertIn("Small Section B", headings)
            self.assertNotIn("Sub of A", headings)


DUPLICATE_HEADING_FIXTURE = """\
# Doc

## Pattern Deep Dive — [Pattern Name]

First instance.

## Pattern Deep Dive — [Pattern Name]

Second instance (template duplicate).
"""


class DuplicateHeadingTests(unittest.TestCase):
    def test_duplicates_get_distinct_indexes(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(DUPLICATE_HEADING_FIXTURE, encoding="utf-8")
            secs = sections.enumerate_sections(path, repo_root=Path(tmp))
            self.assertEqual(len(secs), 2)
            self.assertNotEqual(secs[0].section_idx, secs[1].section_idx)
            self.assertEqual(secs[0].heading, secs[1].heading)


class ScreamingHeadingTests(unittest.TestCase):
    def test_all_caps_heading_marked_screaming(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text(
                "# Doc\n\n## RUN_METADATA\n\nstub\n\n## Phase 1\n\nstub\n",
                encoding="utf-8",
            )
            secs = sections.enumerate_sections(path, repo_root=Path(tmp))
            run = [s for s in secs if s.heading == "RUN_METADATA"]
            self.assertEqual(run[0].skip_reason, "screaming")


class WriteSectionsJsonTests(unittest.TestCase):
    def test_write_emits_schema_versioned_payload(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(SKILL_FIXTURE, encoding="utf-8")
            secs = sections.enumerate_sections(path, repo_root=Path(tmp))
            out_path = Path(tmp) / "pass_a_sections.json"
            sections.write_sections_json(secs, out_path)
            import json
            payload = json.loads(out_path.read_text())
            self.assertEqual(payload["schema_version"], "1.0")
            self.assertEqual(len(payload["sections"]), len(secs))


class QPBSkillFixtureTests(unittest.TestCase):
    """Tests against QPB's actual SKILL.md as fixture.

    These tests guard against regression on the real-world target
    Phase 3 will run against. They avoid asserting exact section
    counts (those drift as SKILL.md is edited) and instead pin the
    invariants that matter: at least one Phase 1 section, no fenced-
    block headings, meta sections marked.
    """

    def setUp(self):
        self.skill_path = Path(__file__).resolve().parents[2] / "SKILL.md"
        self.repo_root = Path(__file__).resolve().parents[2]
        if not self.skill_path.is_file():
            self.skipTest("QPB SKILL.md not at expected location")

    def test_qpb_skill_md_at_least_phase_sections(self) -> None:
        secs = sections.enumerate_sections(self.skill_path, repo_root=self.repo_root)
        phase_headings = [s.heading for s in secs if s.heading.startswith("Phase ")]
        self.assertGreaterEqual(
            len(phase_headings), 4,
            "Expected at least four phase-prefixed sections in QPB SKILL.md "
            "(Phase 1, 2, 3, 4 minimum); got: " + repr(phase_headings),
        )

    def test_qpb_skill_md_no_run_metadata_outside_fenced_block(self) -> None:
        # The SKILL.md template-output blocks (lines ~824-963 in the
        # current revision) include `## Run metadata` headings inside
        # fenced code blocks. The enumerator must skip them.
        secs = sections.enumerate_sections(self.skill_path, repo_root=self.repo_root)
        run_metadata_headings = [s for s in secs if s.heading == "Run metadata"]
        self.assertEqual(
            len(run_metadata_headings), 0,
            "Run metadata heading is inside a fenced code block in SKILL.md "
            "and must not be enumerated as a top-level section",
        )

    def test_qpb_skill_md_meta_sections_skipped(self) -> None:
        secs = sections.enumerate_sections(self.skill_path, repo_root=self.repo_root)
        # Why This Exists is in the META_SECTION_ALLOWLIST.
        wte = [s for s in secs if s.heading == "Why This Exists"]
        if wte:
            self.assertEqual(wte[0].skip_reason, "meta-allowlist")


if __name__ == "__main__":
    unittest.main()
