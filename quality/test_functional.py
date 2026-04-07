import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
QUALITY_DIR = REPO_ROOT / "quality"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestSpecRequirements(unittest.TestCase):
    def test_root_and_github_skill_files_are_identical(self):
        """[Req: formal — README.md §Quick start] Root and packaged SKILL.md stay synchronized."""
        self.assertEqual(read(REPO_ROOT / "SKILL.md"), read(REPO_ROOT / ".github/skills/SKILL.md"))

    def test_root_and_github_reference_trees_match(self):
        """[Req: formal — AGENTS.md §Installing the skill] Root and packaged references stay synchronized."""
        root_refs = sorted((REPO_ROOT / "references").glob("*.md"))
        github_refs = sorted((REPO_ROOT / ".github/skills/references").glob("*.md"))
        self.assertEqual([p.name for p in root_refs], [p.name for p in github_refs])
        for root_ref, gh_ref in zip(root_refs, github_refs):
            with self.subTest(reference=root_ref.name):
                self.assertEqual(read(root_ref), read(gh_ref))

    def test_skill_contains_exact_startup_banner(self):
        """[Req: formal — SKILL.md startup block] The mandatory startup banner remains exact."""
        skill = read(REPO_ROOT / ".github/skills/SKILL.md")
        expected = (
            "> Quality Playbook v1.3.8 — by Andrew Stellman\n"
            "> https://github.com/andrewstellman/quality-playbook\n"
            ">\n"
            "> Generating a complete quality system for this project. Here's what I'll do:"
        )
        self.assertIn(expected, skill)

    def test_progress_template_tracks_all_required_phases(self):
        """[Req: formal — SKILL.md §PROGRESS template] The tracked phases stay explicit."""
        skill = read(REPO_ROOT / ".github/skills/SKILL.md")
        for phase in (
            "Phase 1: Exploration",
            "Phase 2: Artifact generation",
            "Phase 2b: Code review + regression tests",
            "Phase 2c: Spec audit + triage",
            "Phase 2d: Post-review reconciliation + closure verification",
            "Phase 3: Verification benchmarks",
            "## Terminal Gate Verification",
        ):
            with self.subTest(phase=phase):
                self.assertIn(phase, skill)

    def test_requirements_pipeline_defines_versioning_and_review_outputs(self):
        """[Req: formal — requirements_pipeline.md §Versioning protocol] Versioned refinement stays documented."""
        pipeline = read(REPO_ROOT / "references/requirements_pipeline.md")
        for needle in (
            "## Versioning protocol",
            "quality/VERSION_HISTORY.md",
            "quality/REVIEW_REQUIREMENTS.md",
            "quality/REFINE_REQUIREMENTS.md",
            "quality/history/vX.Y/",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, pipeline)

    def test_spec_audit_reference_requires_docs_validation_and_council_status(self):
        """[Req: formal — spec_audit.md] The audit baseline and council-size checks remain mandatory."""
        spec_audit = read(REPO_ROOT / "references/spec_audit.md")
        for needle in (
            "## Pre-audit docs validation",
            "## Council Status",
            "verification probe",
            "If `docs_gathered/` does not exist",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, spec_audit)

    def test_review_protocol_reference_requires_executable_regression_closure(self):
        """[Req: formal — review_protocols.md §Closure mandate] Confirmed bugs must have executable closure."""
        review_protocols = read(REPO_ROOT / "references/review_protocols.md")
        for needle in (
            "### Closure mandate",
            "quality/test_regression.*",
            "The only acceptable exemption",
            "### Test-finding alignment check",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, review_protocols)

    def test_integration_protocol_contains_field_reference_table(self):
        """[Req: formal — review_protocols.md §Field Reference Table] Integration gates must be grounded in actual fields."""
        protocol = read(QUALITY_DIR / "RUN_INTEGRATION_TESTS.md")
        for needle in (
            "## Field Reference Table",
            "Started",
            "Phase completion",
            "Terminal Gate Verification",
            "Closure Status",
            "Found By",
            "quality/VERSION_HISTORY.md",
            "quality/REFINEMENT_HINTS.md",
            "## Skill Integration Test Protocol",
            "**Recommendation:** SHIP IT / FIX FIRST / NEEDS INVESTIGATION",
            "quality/results/YYYY-MM-DD-integration.md",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, protocol)

    def test_gathered_docs_inventory_is_available_to_phase_one(self):
        """[Req: formal — SKILL.md Phase 1; docs_gathered/] Supplemental history remains present for exploration."""
        gathered = REPO_ROOT / "docs_gathered"
        self.assertTrue(gathered.is_dir())
        for required in (
            "quality_md_genesis.md",
            "qpb-1.3.6-bootstrap-review-copilot.md",
            "qpb-1.3.6-bootstrap-review-cursor.md",
            "qpb-1.3.6-bootstrap-review-cowork.md",
        ):
            with self.subTest(doc=required):
                self.assertTrue((gathered / required).is_file())


class TestFitnessScenarios(unittest.TestCase):
    def test_scenario_1_canonical_and_packaged_skill_copies_diverge(self):
        """[Req: formal — QUALITY.md Scenario 1] The quality system guards mirror drift."""
        quality = read(QUALITY_DIR / "QUALITY.md")
        self.assertIn("### Scenario 1: Canonical and packaged skill copies diverge", quality)
        self.assertIn("test_root_and_github_skill_files_are_identical", quality)
        self.assertIn("test_root_and_github_reference_trees_match", quality)

    def test_scenario_2_public_docs_advertise_the_wrong_license(self):
        """[Req: formal — QUALITY.md Scenario 2] The quality system records a license-drift guardrail."""
        quality = read(QUALITY_DIR / "QUALITY.md")
        self.assertIn("### Scenario 2: Public docs advertise the wrong license", quality)
        self.assertIn("test_readme_license_text_matches_shipped_license_file", quality)

    def test_scenario_3_readme_still_teaches_the_old_phase_model(self):
        """[Req: formal — QUALITY.md Scenario 3] The quality system records the phase-drift probe."""
        quality = read(QUALITY_DIR / "QUALITY.md")
        self.assertIn("### Scenario 3: README still teaches the old phase model", quality)
        self.assertIn("test_readme_phase_summary_mentions_six_tracked_phases_and_verification", quality)

    def test_scenario_4_install_snippets_omit_required_package_files(self):
        """[Req: formal — QUALITY.md Scenario 4] The quality system records the install-completeness probe."""
        quality = read(QUALITY_DIR / "QUALITY.md")
        self.assertIn("### Scenario 4: Install snippets omit required package files", quality)
        self.assertIn("test_install_instructions_copy_required_license_file", quality)

    def test_scenario_5_spec_audit_bugs_disappear_between_phases(self):
        """[Req: formal — QUALITY.md Scenario 5] The generated playbook guards against BUG-orphaning."""
        progress = read(QUALITY_DIR / "PROGRESS.md")
        self.assertIn("## Cumulative BUG tracker", progress)
        self.assertIn("## Terminal Gate Verification", progress)
        self.assertIn(
            "BUG tracker has 5 entries. 5 have regression tests, 0 have exemptions, 0 are unresolved. "
            "Code review confirmed 4 bugs. Spec audit confirmed 5 code bugs (1 net-new). Expected total: 4 + 1.",
            progress,
        )
        protocol = read(QUALITY_DIR / "RUN_CODE_REVIEW.md")
        self.assertIn("Every confirmed BUG must map to `quality/test_regression.py`", protocol)
        triage = read(QUALITY_DIR / "spec_audits/2026-04-06-triage.md")
        self.assertIn("## Confirmed code bugs", triage)
        self.assertIn("**Net-new bug:** SA-005", triage)

    def test_scenario_6_stale_supplemental_docs_skew_the_audit_baseline(self):
        """[Req: formal — QUALITY.md Scenario 6] The spec audit protocol validates supplemental docs."""
        triage = read(QUALITY_DIR / "spec_audits/2026-04-06-triage.md")
        self.assertIn("## Pre-audit docs validation", triage)
        self.assertIn("## Council Status", triage)
        self.assertIn("Claim source", triage)
        self.assertIn("docs_gathered/qpb-1.3.6-bootstrap-review-cursor.md", triage)

    def test_scenario_7_partial_sessions_masquerade_as_successful_runs(self):
        """[Req: formal — QUALITY.md Scenario 7] The protocols guard against stale or empty artifacts."""
        spec_audit = read(REPO_ROOT / "references/spec_audit.md")
        for needle in (
            "Partial session detection",
            "A partial session is not a \"clean run with no findings\"",
            "PROVENANCE:",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, spec_audit)

    def test_scenario_8_integration_quality_gates_hallucinate_artifact_fields(self):
        """[Req: formal — QUALITY.md Scenario 8] The integration protocol uses artifact-derived field names."""
        protocol = read(QUALITY_DIR / "RUN_INTEGRATION_TESTS.md")
        for needle in ("Started", "With docs", "Closure Status", "Effective council"):
            with self.subTest(needle=needle):
                self.assertIn(needle, protocol)


class TestBoundariesAndEdgeCases(unittest.TestCase):
    def test_requirements_use_canonical_req_heading_format(self):
        """[Req: inferred — from requirements_pipeline.md heading rule] Requirements remain machine-parseable."""
        requirements = read(QUALITY_DIR / "REQUIREMENTS.md")
        headings = re.findall(r"^### REQ-\d{3}: ", requirements, flags=re.MULTILINE)
        self.assertEqual(len(headings), 17)

    def test_review_and_refinement_files_reference_shared_feedback_state(self):
        """[Req: inferred — from review/refinement templates] Review and refinement share REFINEMENT_HINTS state."""
        review = read(QUALITY_DIR / "REVIEW_REQUIREMENTS.md")
        refine = read(QUALITY_DIR / "REFINE_REQUIREMENTS.md")
        self.assertIn("quality/REFINEMENT_HINTS.md", review)
        self.assertIn("quality/REFINEMENT_HINTS.md", refine)
        self.assertIn("quality/VERSION_HISTORY.md", refine)

    def test_progress_metadata_reflects_docs_presence(self):
        """[Req: inferred — from SKILL.md metadata guard] PROGRESS accurately records docs availability."""
        progress = read(QUALITY_DIR / "PROGRESS.md")
        self.assertIn("With docs: yes", progress)
        self.assertIn("BUG tracker has 5 entries.", progress)

    def test_terminal_gate_count_matches_bug_tracker_rows(self):
        """[Req: inferred — from SKILL.md Phase 2d] Terminal-gate arithmetic matches the tracker row count."""
        progress = read(QUALITY_DIR / "PROGRESS.md")
        bug_rows = re.findall(r"^\| \d+ \| ", progress, flags=re.MULTILINE)
        self.assertEqual(len(bug_rows), 5)
        self.assertIn("BUG tracker has 5 entries.", progress)

    def test_spec_audit_reference_downgrades_incomplete_councils(self):
        """[Req: inferred — from spec_audit.md council rules] Reduced councils cannot overclaim confidence."""
        spec_audit = read(REPO_ROOT / "references/spec_audit.md")
        for needle in (
            "Effective council: 2/3",
            "Needs verification",
            "Do not silently substitute stale reports",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, spec_audit)

    def test_review_protocol_forbids_non_executable_closure(self):
        """[Req: inferred — from review_protocols.md closure mandate] Markdown-only bug closure is not allowed."""
        review_protocols = read(REPO_ROOT / "references/review_protocols.md")
        self.assertIn("not a Markdown file, not prose documentation", review_protocols)

    def test_generated_quality_suite_uses_unittest_expected_failure_for_regressions(self):
        """[Req: inferred — from repo test conventions] Regression probes use built-in unittest expected failures."""
        regression = read(QUALITY_DIR / "test_regression.py")
        self.assertIn("@unittest.expectedFailure", regression)


if __name__ == "__main__":
    unittest.main()
