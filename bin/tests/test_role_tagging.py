"""Tests for bin/role_map.py — QPB v1.5.4 Phase 1 file-role-tagging.

The role tagging itself is produced by an LLM agent during Phase 1
exploration; the unit-test surface here is the schema + breakdown
helpers that every consumer (INDEX rendering, pass_c, quality_gate)
shares. Each fixture test handcrafts the role map an LLM SHOULD
produce for a given target shape and asserts the helper functions
process it correctly. The "did the LLM tag the right files" assertion
lives in the wide-test harness, not here.

Fixtures cover the five shapes called out in the v1.5.4 Phase 1 brief:

  1. pdf-style          SKILL.md + reference docs + helper scripts
                        explicitly invoked from SKILL.md (skill-tool).
  2. pure-Markdown      single SKILL.md, no scripts.
  3. pure-code          no SKILL.md, only library/orchestrator code.
  4. QPB-style          SKILL.md + agents/* (skill-prose) + bin/*.py
                        (code, NOT skill-tool — independent contracts).
  5. pre-played         target carrying a quality/ subtree from a
                        prior playbook run; tagged playbook-output so
                        the LOC-pollution failure mode of v1.5.3
                        cannot reoccur.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin import role_map as rm


def _make_role_map(files: list[dict]) -> dict:
    """Helper: assemble a complete role map from a list of file entries
    with the breakdown computed by the production helper. This is what
    Phase 1 should ultimately emit; the helper makes the fixtures
    declarative."""
    return {
        "schema_version": rm.SCHEMA_VERSION,
        "timestamp_start": "2026-04-28T00:00:00Z",
        "files": files,
        "breakdown": rm.compute_breakdown(files),
    }


def _entry(path: str, role: str, size: int, **extra) -> dict:
    rec = {
        "path": path,
        "role": role,
        "size_bytes": size,
        "rationale": f"fixture entry for {path}",
    }
    rec.update(extra)
    return rec


# ---------------------------------------------------------------------------
# Fixture 1 — pdf-style: SKILL.md + reference + skill-tool scripts
# ---------------------------------------------------------------------------


class PdfStyleFixtureTests(unittest.TestCase):
    """The pdf skill ships SKILL.md + a reference doc + two scripts
    that SKILL.md explicitly tells the agent to invoke. The role map
    must distinguish skill-tool (scripts subordinate to SKILL.md prose)
    from code (independent libraries)."""

    def setUp(self) -> None:
        self.role_map = _make_role_map([
            _entry("SKILL.md", "skill-prose", 6000),
            _entry("references/forms.md", "skill-reference", 2000),
            _entry("references/extraction.md", "skill-reference", 1000),
            _entry(
                "scripts/extract_form_field_info.py",
                "skill-tool",
                500,
                skill_prose_reference="SKILL.md:47",
            ),
            _entry(
                "scripts/render_pdf.py",
                "skill-tool",
                500,
                skill_prose_reference="references/forms.md:20",
            ),
        ])

    def test_validates_clean(self) -> None:
        self.assertEqual(rm.validate_role_map(self.role_map), [])

    def test_breakdown_distinguishes_skill_tool_from_code(self) -> None:
        files_by_role = self.role_map["breakdown"]["files_by_role"]
        self.assertEqual(files_by_role.get("skill-prose"), 1)
        self.assertEqual(files_by_role.get("skill-reference"), 2)
        self.assertEqual(files_by_role.get("skill-tool"), 2)
        # No 'code' bucket should appear at all (not even with count 0).
        self.assertNotIn("code", files_by_role)

    def test_percentages_match_pdf_style_shape(self) -> None:
        pcts = self.role_map["breakdown"]["percentages"]
        # 6000 + 2000 + 1000 = 9000 skill prose; 1000 tool; 0 code; 0 other.
        # Total = 10000.
        self.assertAlmostEqual(pcts["skill_share"], 0.9, places=3)
        self.assertAlmostEqual(pcts["tool_share"], 0.1, places=3)
        self.assertAlmostEqual(pcts["code_share"], 0.0, places=3)
        self.assertAlmostEqual(pcts["other_share"], 0.0, places=3)

    def test_activation_predicates(self) -> None:
        self.assertTrue(rm.has_skill_prose(self.role_map))
        self.assertTrue(rm.has_skill_tools(self.role_map))
        self.assertFalse(rm.has_code(self.role_map))

    def test_legacy_project_type_is_skill(self) -> None:
        # No code surface; pass_c's behavioral-claim branch should
        # route to council-review (Branch 6), not Tier-5 demotion.
        self.assertEqual(rm.derive_legacy_project_type(self.role_map), "Skill")

    def test_skill_tool_carries_prose_reference(self) -> None:
        skill_tool_entries = [
            f for f in self.role_map["files"] if f["role"] == "skill-tool"
        ]
        self.assertEqual(len(skill_tool_entries), 2)
        for entry in skill_tool_entries:
            self.assertIn("skill_prose_reference", entry)
            self.assertRegex(
                entry["skill_prose_reference"], r"^[\w./-]+:\d+$"
            )


# ---------------------------------------------------------------------------
# Fixture 2 — pure-Markdown skill: single SKILL.md
# ---------------------------------------------------------------------------


class PureMarkdownSkillFixtureTests(unittest.TestCase):
    """schedule / consolidate-memory / setup-cowork from the v1.5.4
    Design Part 1 validation set. Pure prose, no scripts."""

    def setUp(self) -> None:
        self.role_map = _make_role_map([
            _entry("SKILL.md", "skill-prose", 4000),
        ])

    def test_validates_clean(self) -> None:
        self.assertEqual(rm.validate_role_map(self.role_map), [])

    def test_breakdown_is_100_percent_skill_prose(self) -> None:
        pcts = self.role_map["breakdown"]["percentages"]
        self.assertAlmostEqual(pcts["skill_share"], 1.0, places=3)
        self.assertAlmostEqual(pcts["code_share"], 0.0, places=3)
        self.assertAlmostEqual(pcts["tool_share"], 0.0, places=3)
        self.assertAlmostEqual(pcts["other_share"], 0.0, places=3)

    def test_has_skill_prose_only(self) -> None:
        self.assertTrue(rm.has_skill_prose(self.role_map))
        self.assertFalse(rm.has_skill_tools(self.role_map))
        self.assertFalse(rm.has_code(self.role_map))

    def test_legacy_project_type_is_skill(self) -> None:
        self.assertEqual(rm.derive_legacy_project_type(self.role_map), "Skill")


# ---------------------------------------------------------------------------
# Fixture 3 — pure-code: chi/virtio/express-style
# ---------------------------------------------------------------------------


class PureCodeProjectFixtureTests(unittest.TestCase):
    """A v1.5.1-pinned code benchmark: no SKILL.md at root, only code
    plus README/test files. Must role-tag as ~100% code with the
    four-pass pipeline gate evaluating to inactive."""

    def setUp(self) -> None:
        self.role_map = _make_role_map([
            _entry("router.go", "code", 12000),
            _entry("middleware.go", "code", 6000),
            _entry("handler.go", "code", 2000),
            _entry("router_test.go", "test", 4000),
            _entry("README.md", "docs", 1500),
            _entry("go.mod", "config", 500),
        ])

    def test_validates_clean(self) -> None:
        self.assertEqual(rm.validate_role_map(self.role_map), [])

    def test_breakdown_dominated_by_code(self) -> None:
        # 20000 code / 26000 total ≈ 0.769
        pcts = self.role_map["breakdown"]["percentages"]
        self.assertGreater(pcts["code_share"], 0.7)
        self.assertEqual(pcts["skill_share"], 0.0)
        self.assertEqual(pcts["tool_share"], 0.0)
        # Test/docs/config bucket into other.
        self.assertGreater(pcts["other_share"], 0.0)

    def test_no_skill_prose(self) -> None:
        self.assertFalse(rm.has_skill_prose(self.role_map))
        self.assertTrue(rm.has_code(self.role_map))

    def test_legacy_project_type_is_code(self) -> None:
        # Four-pass pipeline should NOT activate; existing code-review
        # path runs unchanged.
        self.assertEqual(rm.derive_legacy_project_type(self.role_map), "Code")


# ---------------------------------------------------------------------------
# Fixture 4 — QPB-style: SKILL.md + agents/* + bin/*.py
# ---------------------------------------------------------------------------


class QpbStyleFixtureTests(unittest.TestCase):
    """QPB itself is the sentinel case for "skill-tool vs code." Its
    SKILL.md is large skill-prose; its agents/*.md are also skill-prose;
    its bin/*.py modules carry their own behavior contracts (they're
    NOT subordinate to SKILL.md prose) and must role-tag as code, not
    skill-tool. Misclassifying bin/*.py as skill-tool would explode
    the skill-tool surface area and make the prose-to-code divergence
    check meaningless."""

    def setUp(self) -> None:
        self.role_map = _make_role_map([
            _entry("SKILL.md", "skill-prose", 8000),
            _entry("agents/code-reviewer.md", "skill-prose", 1200),
            _entry("agents/explore.md", "skill-prose", 800),
            _entry("references/exploration_patterns.md", "skill-reference", 3000),
            # bin/*.py must be 'code', NOT 'skill-tool'.
            _entry("bin/run_playbook.py", "code", 90000),
            _entry("bin/archive_lib.py", "code", 24000),
            _entry("bin/citation_verifier.py", "code", 12000),
            _entry("bin/tests/test_archive_lib.py", "test", 8000),
            _entry("docs/design/v1.5.4.md", "docs", 6000),
            _entry(".gitignore", "config", 200),
        ])

    def test_validates_clean(self) -> None:
        self.assertEqual(rm.validate_role_map(self.role_map), [])

    def test_bin_pyfiles_tagged_code_not_skill_tool(self) -> None:
        """The defining QPB invariant: bin/*.py is NEVER skill-tool."""
        for entry in self.role_map["files"]:
            if entry["path"].startswith("bin/") and entry["path"].endswith(".py"):
                if "test" not in entry["path"]:
                    self.assertEqual(
                        entry["role"],
                        "code",
                        msg=(
                            f"{entry['path']} is misclassified as "
                            f"{entry['role']!r} — bin/*.py modules carry "
                            "independent behavior contracts and must "
                            "tag as 'code'"
                        ),
                    )

    def test_no_skill_tool_files(self) -> None:
        # QPB has no skill-tools at all (it has independent code only).
        self.assertFalse(rm.has_skill_tools(self.role_map))

    def test_both_skill_and_code_surfaces_present(self) -> None:
        self.assertTrue(rm.has_skill_prose(self.role_map))
        self.assertTrue(rm.has_code(self.role_map))

    def test_legacy_project_type_is_hybrid(self) -> None:
        # has skill-prose AND has code -> Hybrid (pass_c can demote
        # behavioral claims to Tier 5).
        self.assertEqual(rm.derive_legacy_project_type(self.role_map), "Hybrid")

    def test_breakdown_surfaces_both_sides(self) -> None:
        pcts = self.role_map["breakdown"]["percentages"]
        self.assertGreater(pcts["skill_share"], 0.0)
        self.assertGreater(pcts["code_share"], 0.0)


# ---------------------------------------------------------------------------
# Fixture 5 — pre-played benchmark: target carrying a prior quality/ tree
# ---------------------------------------------------------------------------


class PrePlayedBenchmarkFixtureTests(unittest.TestCase):
    """The v1.5.3 LOC-pollution failure mode: QPB ships its own
    quality_gate.py into a benchmark target's .github/skills/, and
    a prior playbook run leaves a quality/ subtree behind. The v1.5.3
    mechanical classifier counted these as part of the target's code
    LOC and silently flipped the classification.

    In v1.5.4 the role map either omits these paths (Phase 1's ignore
    rules already skip quality/) OR tags them explicitly as
    playbook-output. Either way, the breakdown for the target's
    intrinsic surface is what it is — there's no LOC-denominator math
    that can be polluted. This fixture pins the contract: when
    playbook-output entries appear in the role map, they bucket into
    other_share, never into code_share or skill_share."""

    def setUp(self) -> None:
        self.role_map = _make_role_map([
            # Target's own surface — pure code.
            _entry("src/parser.py", "code", 3000),
            _entry("src/serializer.py", "code", 2000),
            # Prior playbook output that stuck around in the target.
            _entry("quality/EXPLORATION.md", "playbook-output", 4000),
            _entry("quality/REQUIREMENTS.md", "playbook-output", 3000),
            _entry("quality/runs/20260101T000000Z/INDEX.md", "playbook-output", 1000),
            _entry(".github/skills/quality_gate.py", "playbook-output", 50000),
        ])

    def test_validates_clean(self) -> None:
        self.assertEqual(rm.validate_role_map(self.role_map), [])

    def test_playbook_output_does_not_inflate_code_share(self) -> None:
        # If the v1.5.3 bug had reoccurred, the 50000-byte quality_gate.py
        # would be lumped into code_share and dominate. v1.5.4 bucketing
        # routes playbook-output into other_share.
        pcts = self.role_map["breakdown"]["percentages"]
        # 5000 code / 63000 total ≈ 0.079
        self.assertLess(pcts["code_share"], 0.10)
        self.assertEqual(pcts["skill_share"], 0.0)
        self.assertEqual(pcts["tool_share"], 0.0)
        # Playbook output dominates other.
        self.assertGreater(pcts["other_share"], 0.85)

    def test_legacy_project_type_is_code_not_skill(self) -> None:
        # The target itself is pure-code; the playbook artifacts must
        # not flip the legacy-project-type derivation to Skill/Hybrid.
        self.assertEqual(rm.derive_legacy_project_type(self.role_map), "Code")

    def test_no_skill_activation_from_playbook_output(self) -> None:
        # quality_gate.py is technically a Python file but it's NOT the
        # target's code surface; the role map's playbook-output tag
        # ensures has_code() reflects only the target's intrinsic code.
        # In this fixture the target also has src/*.py so has_code is
        # True — but tagging IS what protects: if the target had no
        # intrinsic code, playbook-output would not flip the predicate.
        self.assertTrue(rm.has_code(self.role_map))  # src/*.py
        self.assertFalse(rm.has_skill_prose(self.role_map))
        self.assertFalse(rm.has_skill_tools(self.role_map))

    def test_pure_target_with_only_playbook_output_is_not_skill(self) -> None:
        """Sentinel: a hypothetical target with NO intrinsic surface
        and only playbook leftovers must not classify as anything
        skill-side. playbook-output never activates skill predicates."""
        playbook_only = _make_role_map([
            _entry("quality/EXPLORATION.md", "playbook-output", 4000),
            _entry(".github/skills/quality_gate.py", "playbook-output", 50000),
        ])
        self.assertFalse(rm.has_skill_prose(playbook_only))
        self.assertFalse(rm.has_code(playbook_only))
        self.assertFalse(rm.has_skill_tools(playbook_only))
        self.assertEqual(rm.derive_legacy_project_type(playbook_only), "Code")


# ---------------------------------------------------------------------------
# Schema + helper unit tests
# ---------------------------------------------------------------------------


class ValidateRoleMapTests(unittest.TestCase):
    def test_rejects_non_dict(self) -> None:
        self.assertTrue(rm.validate_role_map([]))

    def test_rejects_missing_top_keys(self) -> None:
        errs = rm.validate_role_map({"schema_version": rm.SCHEMA_VERSION})
        self.assertTrue(any("files" in e for e in errs))
        self.assertTrue(any("breakdown" in e for e in errs))

    def test_rejects_invalid_role(self) -> None:
        bad = _make_role_map([_entry("foo.py", "code", 100)])
        bad["files"][0]["role"] = "not-a-real-role"
        errs = rm.validate_role_map(bad)
        self.assertTrue(any("not-a-real-role" in e for e in errs))

    def test_rejects_duplicate_paths(self) -> None:
        bad = _make_role_map([
            _entry("foo.py", "code", 100),
            _entry("foo.py", "code", 200),
        ])
        errs = rm.validate_role_map(bad)
        self.assertTrue(any("duplicate" in e for e in errs))

    def test_rejects_negative_size(self) -> None:
        bad = _make_role_map([_entry("foo.py", "code", 100)])
        bad["files"][0]["size_bytes"] = -1
        errs = rm.validate_role_map(bad)
        self.assertTrue(any("size_bytes" in e for e in errs))

    def test_rejects_schema_version_mismatch(self) -> None:
        bad = _make_role_map([_entry("foo.py", "code", 100)])
        bad["schema_version"] = "9.9"
        errs = rm.validate_role_map(bad)
        self.assertTrue(any("schema_version" in e for e in errs))

    def test_rejects_percentage_sum_drift(self) -> None:
        bad = _make_role_map([_entry("foo.py", "code", 100)])
        bad["breakdown"]["percentages"]["code_share"] = 0.5  # was 1.0
        errs = rm.validate_role_map(bad)
        self.assertTrue(any("sum to 1.0" in e for e in errs))

    def test_skill_tool_with_empty_prose_reference_rejected(self) -> None:
        bad = _make_role_map([
            _entry(
                "scripts/x.py",
                "skill-tool",
                500,
                skill_prose_reference="",
            ),
        ])
        errs = rm.validate_role_map(bad)
        self.assertTrue(any("skill_prose_reference" in e for e in errs))


class ComputeBreakdownTests(unittest.TestCase):
    def test_empty_files_yields_zero_shares(self) -> None:
        bd = rm.compute_breakdown([])
        self.assertEqual(bd["files_by_role"], {})
        for v in bd["percentages"].values():
            self.assertEqual(v, 0.0)

    def test_unknown_role_skipped(self) -> None:
        bd = rm.compute_breakdown([
            _entry("a", "code", 100),
            {"path": "b", "role": "garbage", "size_bytes": 100, "rationale": "x"},
        ])
        # Only the legitimate code entry counts; garbage role is dropped.
        self.assertEqual(bd["files_by_role"], {"code": 1})
        self.assertEqual(bd["percentages"]["code_share"], 1.0)

    def test_playbook_output_buckets_into_other(self) -> None:
        bd = rm.compute_breakdown([
            _entry("a", "playbook-output", 100),
            _entry("b", "code", 100),
        ])
        self.assertAlmostEqual(bd["percentages"]["code_share"], 0.5, places=3)
        self.assertAlmostEqual(bd["percentages"]["other_share"], 0.5, places=3)
        self.assertAlmostEqual(bd["percentages"]["skill_share"], 0.0, places=3)


class LoadRoleMapTests(unittest.TestCase):
    def test_load_returns_none_when_absent(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertIsNone(rm.load_role_map(Path(tmp) / "missing.json"))

    def test_load_returns_none_on_garbage(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "rm.json"
            p.write_text("not json", encoding="utf-8")
            self.assertIsNone(rm.load_role_map(p))

    def test_load_returns_dict_on_valid(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "rm.json"
            payload = _make_role_map([_entry("x.py", "code", 100)])
            p.write_text(json.dumps(payload), encoding="utf-8")
            loaded = rm.load_role_map(p)
            self.assertIsInstance(loaded, dict)
            self.assertEqual(rm.validate_role_map(loaded), [])

    def test_default_path_under_quality(self) -> None:
        path = rm.default_path(Path("/tmp/repo"))
        self.assertEqual(
            path, Path("/tmp/repo/quality/exploration_role_map.json")
        )


class IndexBreakdownProjectionTests(unittest.TestCase):
    def test_role_breakdown_for_index_includes_three_subkeys(self) -> None:
        m = _make_role_map([_entry("a.py", "code", 100)])
        out = rm.role_breakdown_for_index(m)
        self.assertIsNotNone(out)
        self.assertIn("files_by_role", out)
        self.assertIn("size_by_role", out)
        self.assertIn("percentages", out)

    def test_role_breakdown_for_index_returns_none_when_absent(self) -> None:
        self.assertIsNone(rm.role_breakdown_for_index(None))
        self.assertIsNone(rm.role_breakdown_for_index({}))


if __name__ == "__main__":
    unittest.main()
