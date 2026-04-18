from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from bin import run_playbook


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class RunPlaybookTests(unittest.TestCase):
    def test_parse_args_defaults_to_current_directory(self) -> None:
        args = run_playbook.parse_args([])
        self.assertEqual(args.targets, ["."])
        self.assertTrue(args.parallel)
        self.assertEqual(args.runner, "copilot")

    def test_parse_args_accepts_explicit_paths(self) -> None:
        args = run_playbook.parse_args(["./project-a", "/abs/project-b"])
        self.assertEqual(args.targets, ["./project-a", "/abs/project-b"])

    def test_parse_args_validates_iteration_vs_phase(self) -> None:
        with self.assertRaises(SystemExit):
            run_playbook.parse_args(["--next-iteration", "--phase", "3", "./somedir"])

    def test_phase1_prompt_mentions_seed_skip(self) -> None:
        prompt = run_playbook.phase1_prompt(no_seeds=True)
        self.assertIn("Skip Phase 0 and Phase 0b entirely", prompt)
        self.assertIn("quality/EXPLORATION.md", prompt)

    def test_single_pass_prompt_changes_with_seed_mode(self) -> None:
        self.assertIn("Skip Phase 0 and Phase 0b", run_playbook.single_pass_prompt(no_seeds=True))
        self.assertNotIn("Skip Phase 0 and Phase 0b", run_playbook.single_pass_prompt(no_seeds=False))

    def test_phase2_gate_requires_exploration_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            gate = run_playbook.check_phase_gate(Path(temp_dir), "2")
            self.assertFalse(gate.ok)
            self.assertIn("EXPLORATION.md missing", gate.messages[0])

    def test_phase3_gate_requires_phase2_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            quality_dir = temp_path / "quality"
            write(quality_dir / "REQUIREMENTS.md", "ok")
            gate = run_playbook.check_phase_gate(temp_path, "3")
            self.assertFalse(gate.ok)
            self.assertIn("QUALITY.md", gate.messages[0])
            self.assertIn("CONTRACTS.md", gate.messages[0])

    def test_phase4_gate_warns_when_code_reviews_missing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            quality_dir = temp_path / "quality"
            write(quality_dir / "REQUIREMENTS.md", "ok")
            write(quality_dir / "RUN_SPEC_AUDIT.md", "ok")
            gate = run_playbook.check_phase_gate(temp_path, "4")
            self.assertTrue(gate.ok)
            self.assertEqual(gate.messages, ["GATE WARN Phase 4: no code_reviews/ - Phase 3 may not have run"])

    def test_phase_list_from_mode_expands_all(self) -> None:
        self.assertEqual(run_playbook.phase_list_from_mode("all"), ["1", "2", "3", "4", "5", "6"])
        self.assertEqual(run_playbook.phase_list_from_mode("3,4,5"), ["3", "4", "5"])

    def test_iteration_prompt_contains_strategy(self) -> None:
        self.assertTrue(run_playbook.iteration_prompt("parity").endswith("using the parity strategy."))

    def test_archive_previous_run_archives_and_removes_live_dirs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            write(repo_dir / "quality" / "BUGS.md", "bug")
            write(repo_dir / "control_prompts" / "phase1.output.txt", "prompt")

            run_playbook.archive_previous_run(repo_dir, "20260418-120000")

            self.assertFalse((repo_dir / "quality").exists())
            self.assertFalse((repo_dir / "control_prompts").exists())
            self.assertEqual(
                (repo_dir / "previous_runs" / "20260418-120000" / "quality" / "BUGS.md").read_text(encoding="utf-8"),
                "bug",
            )

    def test_final_artifact_gaps_reports_missing_and_empty_when_complete(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            missing = run_playbook.final_artifact_gaps(repo_dir)
            self.assertIn("quality/REQUIREMENTS.md", missing)
            self.assertIn("functional test", missing)

            for artifact in [
                "quality/REQUIREMENTS.md",
                "quality/CONTRACTS.md",
                "quality/COVERAGE_MATRIX.md",
                "quality/COMPLETENESS_REPORT.md",
                "quality/PROGRESS.md",
                "quality/QUALITY.md",
                "quality/RUN_CODE_REVIEW.md",
                "quality/RUN_INTEGRATION_TESTS.md",
                "quality/RUN_SPEC_AUDIT.md",
                "quality/RUN_TDD_TESTS.md",
            ]:
                write(repo_dir / artifact, "ok")
            write(repo_dir / "quality" / "test_functional.py", "ok")

            self.assertEqual(run_playbook.final_artifact_gaps(repo_dir), [])

    def test_command_for_runner_builds_claude_and_copilot_variants(self) -> None:
        claude_default = run_playbook.command_for_runner("claude", "prompt text", None)
        self.assertEqual(claude_default, ["claude", "-p", "prompt text", "--dangerously-skip-permissions"])

        claude_model = run_playbook.command_for_runner("claude", "prompt text", "sonnet")
        self.assertEqual(claude_model, ["claude", "--model", "sonnet", "-p", "prompt text", "--dangerously-skip-permissions"])

        copilot_default = run_playbook.command_for_runner("copilot", "prompt text", None)
        self.assertEqual(copilot_default, ["gh", "copilot", "-p", "prompt text", "--model", run_playbook.lib.DEFAULT_MODEL, "--yolo"])

        copilot_model = run_playbook.command_for_runner("copilot", "prompt text", "gpt-5.5")
        self.assertEqual(copilot_model, ["gh", "copilot", "-p", "prompt text", "--model", "gpt-5.5", "--yolo"])

    def test_command_preview_quotes_shell_arguments(self) -> None:
        preview = run_playbook.command_preview(["gh", "copilot", "-p", "contains spaces", "weird'quote"])
        self.assertEqual(preview, "gh copilot -p 'contains spaces' 'weird'\"'\"'quote'")

    def test_build_worker_command_passes_target_path(self) -> None:
        phased_args = run_playbook.argparse.Namespace(
            parallel=False,
            runner="claude",
            no_seeds=False,
            phase="3,4,5",
            next_iteration=False,
            strategy="parity",
            model="sonnet",
            kill=False,
            targets=["./project-a"],
            worker=False,
        )

        command = run_playbook.build_worker_command(phased_args, "/abs/path/to/target")

        self.assertEqual(command[0], run_playbook.sys.executable)
        self.assertEqual(Path(command[1]).resolve(), Path(run_playbook.__file__).resolve())
        self.assertEqual(
            command[2:],
            [
                "--worker",
                "--sequential",
                "--claude",
                "--with-seeds",
                "--phase",
                "3,4,5",
                "--strategy",
                "parity",
                "--model",
                "sonnet",
                "/abs/path/to/target",
            ],
        )

        iteration_args = run_playbook.argparse.Namespace(
            parallel=False,
            runner="copilot",
            no_seeds=True,
            phase=None,
            next_iteration=True,
            strategy="parity",
            model="gpt-5.4",
            kill=False,
            targets=["./project-a"],
            worker=False,
        )
        iteration_command = run_playbook.build_worker_command(iteration_args, "/home/user/project")
        self.assertEqual(
            iteration_command[2:],
            [
                "--worker",
                "--sequential",
                "--copilot",
                "--no-seeds",
                "--next-iteration",
                "--strategy",
                "parity",
                "--model",
                "gpt-5.4",
                "/home/user/project",
            ],
        )

    def test_next_strategy_chain(self) -> None:
        self.assertEqual(run_playbook.next_strategy("gap"), "unfiltered")
        self.assertEqual(run_playbook.next_strategy("unfiltered"), "parity")
        self.assertEqual(run_playbook.next_strategy("parity"), "adversarial")
        self.assertEqual(run_playbook.next_strategy("adversarial"), "")

    def test_count_lines_handles_missing_and_existing_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self.assertEqual(run_playbook.count_lines(temp_path / "missing.txt"), 0)
            write(temp_path / "present.txt", "one\ntwo\nthree\n")
            self.assertEqual(run_playbook.count_lines(temp_path / "present.txt"), 3)

    def test_check_phase_gate_covers_all_phases(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            quality_dir = temp_path / "quality"

            phase1 = run_playbook.check_phase_gate(temp_path, "1")
            self.assertTrue(phase1.ok)
            self.assertEqual(phase1.messages, [])

            write(quality_dir / "EXPLORATION.md", "x\n" * 10)
            phase2_warn = run_playbook.check_phase_gate(temp_path, "2")
            self.assertTrue(phase2_warn.ok)
            self.assertEqual(len(phase2_warn.messages), 1)
            self.assertIn("expected 80+", phase2_warn.messages[0])

            write(quality_dir / "QUALITY.md", "ok")
            write(quality_dir / "CONTRACTS.md", "ok")
            write(quality_dir / "RUN_CODE_REVIEW.md", "ok")
            write(quality_dir / "REQUIREMENTS.md", "ok")
            phase3_ok = run_playbook.check_phase_gate(temp_path, "3")
            self.assertTrue(phase3_ok.ok)
            self.assertEqual(phase3_ok.messages, [])

            phase4_fail = run_playbook.check_phase_gate(Path(temp_dir) / "other", "4")
            self.assertFalse(phase4_fail.ok)
            self.assertIn("REQUIREMENTS.md missing", phase4_fail.messages[0])

            write(quality_dir / "RUN_SPEC_AUDIT.md", "ok")
            code_reviews = quality_dir / "code_reviews"
            code_reviews.mkdir(parents=True, exist_ok=True)
            write(code_reviews / "review.md", "ok")
            phase4_ok = run_playbook.check_phase_gate(temp_path, "4")
            self.assertTrue(phase4_ok.ok)
            self.assertEqual(phase4_ok.messages, [])

            write(quality_dir / "PROGRESS.md", "ok")
            phase5_warn = run_playbook.check_phase_gate(temp_path, "5")
            self.assertTrue(phase5_warn.ok)
            self.assertEqual(phase5_warn.messages, ["GATE WARN Phase 5: no BUGS.md and no spec_audits/ - Phases 3-4 may not have run"])

            write(quality_dir / "BUGS.md", "ok")
            phase5_ok = run_playbook.check_phase_gate(temp_path, "5")
            self.assertTrue(phase5_ok.ok)
            self.assertEqual(phase5_ok.messages, [])

            phase6_ok = run_playbook.check_phase_gate(temp_path, "6")
            self.assertTrue(phase6_ok.ok)
            self.assertEqual(phase6_ok.messages, [])

            phase6_fail = run_playbook.check_phase_gate(Path(temp_dir) / "missing-progress", "6")
            self.assertFalse(phase6_fail.ok)
            self.assertIn("PROGRESS.md missing", phase6_fail.messages[0])

    # --- Path-based target resolution (replaces the old version-matching tests) ---

    def test_resolve_target_dirs_absolute_path_passes_through(self) -> None:
        with TemporaryDirectory() as temp_dir:
            resolved, warnings, errors = run_playbook.resolve_target_dirs([temp_dir])
            self.assertEqual(resolved, [Path(temp_dir).resolve()])
            self.assertEqual(errors, [])
            # No skill installed -> warning about missing SKILL.md
            self.assertEqual(len(warnings), 1)
            self.assertIn("No SKILL.md found", warnings[0])

    def test_resolve_target_dirs_relative_path_anchors_to_cwd(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()
            sub = temp_path / "project"
            sub.mkdir()
            prior_cwd = Path.cwd()
            try:
                os.chdir(temp_path)
                resolved, _, errors = run_playbook.resolve_target_dirs(["./project"])
            finally:
                os.chdir(prior_cwd)
            self.assertEqual(resolved, [sub])
            self.assertEqual(errors, [])

    def test_resolve_target_dirs_dot_resolves_to_cwd(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()
            prior_cwd = Path.cwd()
            try:
                os.chdir(temp_path)
                resolved, _, errors = run_playbook.resolve_target_dirs(["."])
            finally:
                os.chdir(prior_cwd)
            self.assertEqual(resolved, [temp_path])
            self.assertEqual(errors, [])

    def test_resolve_target_dirs_non_directory_is_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "does-not-exist"
            resolved, warnings, errors = run_playbook.resolve_target_dirs([str(missing)])
            self.assertEqual(resolved, [])
            self.assertEqual(warnings, [])
            self.assertEqual(len(errors), 1)
            self.assertIn("is not a directory", errors[0])

    def test_resolve_target_dirs_suppresses_skill_warning_when_installed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()
            write(temp_path / ".github" / "skills" / "SKILL.md", "version: 1.4.4\n")
            resolved, warnings, errors = run_playbook.resolve_target_dirs([str(temp_path)])
            self.assertEqual(resolved, [temp_path])
            self.assertEqual(warnings, [])
            self.assertEqual(errors, [])

    def test_log_file_for_places_log_beside_target(self) -> None:
        target = Path("/tmp/my-project").resolve()
        log_path = run_playbook.log_file_for(target, "20260418-130000")
        self.assertEqual(log_path.parent, target.parent)
        self.assertEqual(log_path.name, f"{target.name}-playbook-20260418-130000.log")


if __name__ == "__main__":
    unittest.main()
