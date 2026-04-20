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

    def test_parse_args_full_run_default_false(self) -> None:
        args = run_playbook.parse_args(["./somedir"])
        self.assertFalse(args.full_run)

    def test_parse_args_accepts_full_run(self) -> None:
        args = run_playbook.parse_args(["--full-run", "./somedir"])
        self.assertTrue(args.full_run)

    def test_parse_args_rejects_full_run_with_next_iteration(self) -> None:
        with self.assertRaises(SystemExit):
            run_playbook.parse_args(["--full-run", "--next-iteration", "./somedir"])

    def test_parse_args_rejects_full_run_with_phase(self) -> None:
        with self.assertRaises(SystemExit):
            run_playbook.parse_args(["--full-run", "--phase", "3", "./somedir"])

    def test_phase1_prompt_mentions_seed_skip(self) -> None:
        prompt = run_playbook.phase1_prompt(no_seeds=True)
        self.assertIn("Skip Phase 0 and Phase 0b entirely", prompt)
        self.assertIn("quality/EXPLORATION.md", prompt)

    def test_single_pass_prompt_changes_with_seed_mode(self) -> None:
        self.assertIn("Skip Phase 0 and Phase 0b", run_playbook.single_pass_prompt(no_seeds=True))
        self.assertNotIn("Skip Phase 0 and Phase 0b", run_playbook.single_pass_prompt(no_seeds=False))

    def test_phase4_prompt_includes_layer2_semantic_check_steps(self) -> None:
        """Phase 7 r1: phase 4 must instruct the agent to run the Layer-2
        semantic citation check between the spec audit triage and Phase 5."""
        prompt = run_playbook.phase4_prompt()
        # The plan and assemble subcommands must both be referenced.
        self.assertIn("semantic-check plan", prompt)
        self.assertIn("semantic-check assemble", prompt)
        # Output path must be mentioned so the agent verifies it.
        self.assertIn("quality/citation_semantic_check.json", prompt)
        # Council member identifiers come from the config module.
        self.assertIn("claude-opus-4.7", prompt)
        self.assertIn("gpt-5.4", prompt)
        self.assertIn("gemini-2.5-pro", prompt)
        # Spec Gap path must be called out so the agent knows to skip
        # dispatch when there are no Tier 1/2 REQs.
        self.assertIn("Spec Gap", prompt)
        # Invariant #17 framing so the agent understands why the check runs.
        self.assertIn("invariant #17", prompt)

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
        """Phase 5 revision r1: archive_previous_run now delegates to
        archive_lib.archive_run with status='partial', so the archive folder
        carries the -PARTIAL suffix and INDEX.md is produced inside it."""
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            write(repo_dir / "quality" / "BUGS.md", "bug")
            write(repo_dir / "quality" / "control_prompts" / "phase1.output.txt", "prompt")

            run_playbook.archive_previous_run(repo_dir, "20260418T120000Z")

            # Live artifacts cleared; the archive subtree survives under quality/runs/.
            self.assertFalse((repo_dir / "quality" / "BUGS.md").exists())
            self.assertFalse((repo_dir / "quality" / "control_prompts").exists())
            archive_root = repo_dir / "quality" / "runs" / "20260418T120000Z-PARTIAL" / "quality"
            self.assertEqual(
                (archive_root / "BUGS.md").read_text(encoding="utf-8"),
                "bug",
            )
            self.assertEqual(
                (archive_root / "control_prompts" / "phase1.output.txt").read_text(encoding="utf-8"),
                "prompt",
            )
            # Unified pipeline guarantees per-run INDEX.md and a RUN_INDEX row.
            self.assertTrue(
                (repo_dir / "quality" / "runs" / "20260418T120000Z-PARTIAL" / "INDEX.md").is_file()
            )
            run_index = (repo_dir / "quality" / "RUN_INDEX.md").read_text(encoding="utf-8")
            self.assertIn("20260418T120000Z-PARTIAL", run_index)

    def test_archive_previous_run_skips_already_archived_prior(self) -> None:
        """When quality/INDEX.md names a prior run whose archive folder
        already exists, archive_previous_run just clears the live tree
        without producing a duplicate archive."""
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            write(repo_dir / "quality" / "BUGS.md", "bug")
            # Pre-existing archive from the prior run's own end-of-Phase-6 success.
            existing_archive = repo_dir / "quality" / "runs" / "20260419T100000Z"
            write(existing_archive / "quality" / "BUGS.md", "archived")
            # Live INDEX referencing that run.
            write(
                repo_dir / "quality" / "INDEX.md",
                '# Run Index\n\n```json\n'
                '{"run_timestamp_start": "2026-04-19T10:00:00Z"}\n'
                '```\n',
            )

            run_playbook.archive_previous_run(repo_dir, "20260420T100000Z")

            self.assertFalse((repo_dir / "quality" / "BUGS.md").exists())
            # Existing archive preserved; no -PARTIAL duplicate created.
            self.assertTrue(existing_archive.is_dir())
            self.assertFalse(
                (repo_dir / "quality" / "runs" / "20260419T100000Z-PARTIAL").exists()
            )

    def test_write_live_index_stub_passes_gate_invariant_10(self) -> None:
        """Invariant #10: quality/INDEX.md must exist with §11 fields even
        mid-run. The stub at Phase 1 entry satisfies this."""
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            run_playbook.write_live_index_stub(repo_dir, "20260419T143022Z")
            index = repo_dir / "quality" / "INDEX.md"
            self.assertTrue(index.is_file())
            text = index.read_text(encoding="utf-8")
            self.assertIn("```json", text)
            self.assertIn("run_timestamp_start", text)
            self.assertIn("2026-04-19T14:30:22Z", text)

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
            strategy=["parity"],
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
            strategy=["parity"],
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

    def test_build_worker_command_includes_full_run(self) -> None:
        full_run_args = run_playbook.argparse.Namespace(
            parallel=True,
            runner="copilot",
            no_seeds=True,
            phase=None,
            next_iteration=False,
            full_run=True,
            strategy=["gap"],
            model=None,
            kill=False,
            targets=["./project-a"],
            worker=False,
        )
        command = run_playbook.build_worker_command(full_run_args, "/abs/path/to/target")
        self.assertIn("--full-run", command)
        self.assertNotIn("--next-iteration", command)

    def test_next_strategy_chain(self) -> None:
        self.assertEqual(run_playbook.next_strategy("gap"), "unfiltered")
        self.assertEqual(run_playbook.next_strategy("unfiltered"), "parity")
        self.assertEqual(run_playbook.next_strategy("parity"), "adversarial")
        self.assertEqual(run_playbook.next_strategy("adversarial"), "")

    def test_print_suggested_next_command_includes_model_and_runtime(self) -> None:
        import io
        from contextlib import redirect_stdout

        args = run_playbook.argparse.Namespace(
            runner="claude",
            next_iteration=False,
            strategy=["gap"],
            model="sonnet",
            targets=["express-1.4.5"],
        )

        original_argv = run_playbook.sys.argv
        original_executable = run_playbook.sys.executable
        try:
            run_playbook.sys.argv = ["../bin/run_playbook.py"]
            run_playbook.sys.executable = "/usr/bin/python3"
            buf = io.StringIO()
            with redirect_stdout(buf):
                run_playbook.print_suggested_next_command(args)
        finally:
            run_playbook.sys.argv = original_argv
            run_playbook.sys.executable = original_executable

        output = buf.getvalue()
        self.assertIn("python3 ../bin/run_playbook.py", output)
        self.assertIn("--claude", output)
        self.assertIn("--model sonnet", output)
        self.assertIn("--next-iteration --strategy gap", output)
        self.assertIn("express-1.4.5", output)

    def test_print_suggested_next_command_omits_model_when_unset(self) -> None:
        import io
        from contextlib import redirect_stdout

        args = run_playbook.argparse.Namespace(
            runner="copilot",
            next_iteration=True,
            strategy=["unfiltered"],
            model=None,
            targets=["chi-1.4.5"],
        )

        original_argv = run_playbook.sys.argv
        try:
            run_playbook.sys.argv = ["bin/run_playbook.py"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                run_playbook.print_suggested_next_command(args)
        finally:
            run_playbook.sys.argv = original_argv

        output = buf.getvalue()
        self.assertNotIn("--model", output)
        self.assertNotIn("--claude", output)
        self.assertIn("--next-iteration --strategy parity", output)

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
            phase2_fail = run_playbook.check_phase_gate(temp_path, "2")
            self.assertFalse(phase2_fail.ok)
            self.assertEqual(len(phase2_fail.messages), 1)
            self.assertIn("expected 120+", phase2_fail.messages[0])

            write(quality_dir / "EXPLORATION.md", "x\n" * 200)
            phase2_ok = run_playbook.check_phase_gate(temp_path, "2")
            self.assertTrue(phase2_ok.ok)
            self.assertEqual(phase2_ok.messages, [])

            for name in [
                "QUALITY.md", "CONTRACTS.md", "RUN_CODE_REVIEW.md", "REQUIREMENTS.md",
                "COVERAGE_MATRIX.md", "COMPLETENESS_REPORT.md",
                "RUN_INTEGRATION_TESTS.md", "RUN_SPEC_AUDIT.md", "RUN_TDD_TESTS.md",
            ]:
                write(quality_dir / name, "ok")
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

            write(quality_dir / "PROGRESS.md", "- [x] Phase 4\n")
            spec_audits = quality_dir / "spec_audits"
            spec_audits.mkdir(parents=True, exist_ok=True)
            write(spec_audits / "2026-04-19-triage.md", "ok")
            write(spec_audits / "2026-04-19-auditor-1.md", "ok")
            phase5_warn = run_playbook.check_phase_gate(temp_path, "5")
            self.assertTrue(phase5_warn.ok)
            self.assertEqual(phase5_warn.messages, ["GATE WARN Phase 5: no BUGS.md - Phase 3 may not have run"])

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

    # --- Strategy list parsing and dispatch (Issue 2) ---

    def test_parse_strategy_list_single(self) -> None:
        self.assertEqual(run_playbook.parse_strategy_list("gap"), ["gap"])
        self.assertEqual(run_playbook.parse_strategy_list("parity"), ["parity"])

    def test_parse_strategy_list_multi(self) -> None:
        self.assertEqual(
            run_playbook.parse_strategy_list("unfiltered,parity,adversarial"),
            ["unfiltered", "parity", "adversarial"],
        )

    def test_parse_strategy_list_all_expands_to_full_chain(self) -> None:
        self.assertEqual(
            run_playbook.parse_strategy_list("all"),
            ["gap", "unfiltered", "parity", "adversarial"],
        )

    def test_parse_strategy_list_rejects_all_in_list(self) -> None:
        import argparse as _argparse
        with self.assertRaises(_argparse.ArgumentTypeError):
            run_playbook.parse_strategy_list("all,gap")
        with self.assertRaises(_argparse.ArgumentTypeError):
            run_playbook.parse_strategy_list("gap,all")

    def test_parse_strategy_list_rejects_duplicate(self) -> None:
        import argparse as _argparse
        with self.assertRaises(_argparse.ArgumentTypeError):
            run_playbook.parse_strategy_list("gap,gap")
        with self.assertRaises(_argparse.ArgumentTypeError):
            run_playbook.parse_strategy_list("unfiltered,parity,unfiltered")

    def test_parse_strategy_list_rejects_unknown(self) -> None:
        import argparse as _argparse
        with self.assertRaises(_argparse.ArgumentTypeError):
            run_playbook.parse_strategy_list("bogus")
        with self.assertRaises(_argparse.ArgumentTypeError):
            run_playbook.parse_strategy_list("gap,bogus,parity")

    def test_parse_strategy_list_rejects_empty(self) -> None:
        import argparse as _argparse
        with self.assertRaises(_argparse.ArgumentTypeError):
            run_playbook.parse_strategy_list("")
        with self.assertRaises(_argparse.ArgumentTypeError):
            run_playbook.parse_strategy_list("gap,,parity")

    def test_parse_args_accepts_strategy_list(self) -> None:
        args = run_playbook.parse_args([
            "--next-iteration",
            "--strategy", "unfiltered,parity,adversarial",
            "./somedir",
        ])
        self.assertEqual(args.strategy, ["unfiltered", "parity", "adversarial"])

    def test_parse_args_default_strategy_is_list(self) -> None:
        args = run_playbook.parse_args(["./somedir"])
        self.assertEqual(args.strategy, ["gap"])

    def test_parse_args_strategy_all_expands(self) -> None:
        args = run_playbook.parse_args([
            "--next-iteration", "--strategy", "all", "./somedir",
        ])
        self.assertEqual(args.strategy, ["gap", "unfiltered", "parity", "adversarial"])

    def test_parse_args_rejects_invalid_strategy(self) -> None:
        with self.assertRaises(SystemExit):
            run_playbook.parse_args(["--strategy", "bogus", "./somedir"])

    def test_build_worker_command_serializes_strategy_list(self) -> None:
        args = run_playbook.argparse.Namespace(
            parallel=True,
            runner="copilot",
            no_seeds=True,
            phase=None,
            next_iteration=True,
            full_run=False,
            strategy=["unfiltered", "parity", "adversarial"],
            model=None,
            kill=False,
            targets=["./project-a"],
            worker=False,
        )
        command = run_playbook.build_worker_command(args, "/abs/path/to/target")
        # The list is serialized as a single comma-separated token so the worker's
        # parse_strategy_list reconstructs the same list.
        strategy_idx = command.index("--strategy")
        self.assertEqual(command[strategy_idx + 1], "unfiltered,parity,adversarial")

    def test_print_suggested_next_command_partial_phase_suggests_remaining(self) -> None:
        """After --phase 1,2, next step is --phase 3,4,5,6 — not an iteration."""
        import io
        from contextlib import redirect_stdout

        args = run_playbook.argparse.Namespace(
            runner="claude",
            next_iteration=False,
            strategy=["gap"],
            model="claude-opus-4-7",
            targets=["quality-playbook"],
            phase="1,2",
        )
        original_argv = run_playbook.sys.argv
        try:
            run_playbook.sys.argv = ["bin/run_playbook.py"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                run_playbook.print_suggested_next_command(args)
        finally:
            run_playbook.sys.argv = original_argv
        output = buf.getvalue()

        self.assertIn("--phase 3,4,5,6", output)
        self.assertIn("Next phase suggestion:", output)
        # Model override hint appears
        self.assertIn("swap --model", output)
        # Iteration suggestion must NOT appear after a partial phase run.
        self.assertNotIn("--next-iteration", output)

    def test_print_suggested_next_command_partial_phase_preserves_runner_and_target(self) -> None:
        import io
        from contextlib import redirect_stdout

        args = run_playbook.argparse.Namespace(
            runner="claude",
            next_iteration=False,
            strategy=["gap"],
            model="claude-opus-4-7",
            targets=["quality-playbook"],
            phase="3,5",
        )
        original_argv = run_playbook.sys.argv
        try:
            run_playbook.sys.argv = ["bin/run_playbook.py"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                run_playbook.print_suggested_next_command(args)
        finally:
            run_playbook.sys.argv = original_argv
        output = buf.getvalue()
        # Remaining phases are in numeric order, not source-list order.
        self.assertIn("--phase 1,2,4,6", output)
        self.assertIn("--claude", output)
        self.assertIn("--model claude-opus-4-7", output)
        self.assertIn("quality-playbook", output)

    def test_print_suggested_next_command_phase_all_keeps_iteration_suggestion(self) -> None:
        """--phase all means every phase ran; iteration suggestion stays."""
        import io
        from contextlib import redirect_stdout

        args = run_playbook.argparse.Namespace(
            runner="copilot",
            next_iteration=False,
            strategy=["gap"],
            model=None,
            targets=["chi-1.4.5"],
            phase="all",
        )
        original_argv = run_playbook.sys.argv
        try:
            run_playbook.sys.argv = ["bin/run_playbook.py"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                run_playbook.print_suggested_next_command(args)
        finally:
            run_playbook.sys.argv = original_argv
        output = buf.getvalue()
        self.assertNotIn("Next phase suggestion:", output)
        self.assertIn("--next-iteration --strategy gap", output)

    def test_print_suggested_next_command_phase_none_keeps_iteration_suggestion(self) -> None:
        """Single-prompt mode (no --phase) always suggests an iteration next."""
        import io
        from contextlib import redirect_stdout

        args = run_playbook.argparse.Namespace(
            runner="copilot",
            next_iteration=False,
            strategy=["gap"],
            model=None,
            targets=["chi-1.4.5"],
            phase=None,
        )
        original_argv = run_playbook.sys.argv
        try:
            run_playbook.sys.argv = ["bin/run_playbook.py"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                run_playbook.print_suggested_next_command(args)
        finally:
            run_playbook.sys.argv = original_argv
        output = buf.getvalue()
        self.assertNotIn("Next phase suggestion:", output)
        self.assertIn("--next-iteration --strategy gap", output)

    def test_print_suggested_next_command_explicit_full_phase_list_is_complete(self) -> None:
        """--phase 1,2,3,4,5,6 is equivalent to --phase all — iteration suggestion."""
        import io
        from contextlib import redirect_stdout

        args = run_playbook.argparse.Namespace(
            runner="copilot",
            next_iteration=False,
            strategy=["gap"],
            model=None,
            targets=["chi-1.4.5"],
            phase="1,2,3,4,5,6",
        )
        original_argv = run_playbook.sys.argv
        try:
            run_playbook.sys.argv = ["bin/run_playbook.py"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                run_playbook.print_suggested_next_command(args)
        finally:
            run_playbook.sys.argv = original_argv
        output = buf.getvalue()
        self.assertNotIn("Next phase suggestion:", output)
        self.assertIn("--next-iteration --strategy gap", output)

    def test_print_suggested_next_command_list_midchain(self) -> None:
        import io
        from contextlib import redirect_stdout

        args = run_playbook.argparse.Namespace(
            runner="copilot",
            next_iteration=True,
            strategy=["unfiltered", "parity"],  # ends at parity; successor is adversarial
            model=None,
            targets=["chi-1.4.5"],
        )
        original_argv = run_playbook.sys.argv
        try:
            run_playbook.sys.argv = ["bin/run_playbook.py"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                run_playbook.print_suggested_next_command(args)
        finally:
            run_playbook.sys.argv = original_argv
        output = buf.getvalue()
        self.assertIn("--next-iteration --strategy adversarial", output)
        self.assertNotIn("Iteration cycle complete", output)

    def test_print_suggested_next_command_list_ending_at_adversarial(self) -> None:
        import io
        from contextlib import redirect_stdout

        args = run_playbook.argparse.Namespace(
            runner="copilot",
            next_iteration=True,
            strategy=["parity", "adversarial"],
            model=None,
            targets=["chi-1.4.5"],
        )
        original_argv = run_playbook.sys.argv
        try:
            run_playbook.sys.argv = ["bin/run_playbook.py"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                run_playbook.print_suggested_next_command(args)
        finally:
            run_playbook.sys.argv = original_argv
        output = buf.getvalue()
        self.assertIn("Iteration cycle complete", output)
        self.assertIn("To start fresh", output)
        # Should NOT suggest --next-iteration anywhere (cycle is done).
        self.assertNotIn("--next-iteration", output)

    # --- PID file (per-parent) cleanup (Issue 3) ---

    def test_pid_file_for_parent_is_unique_per_process(self) -> None:
        import os as _os
        expected = run_playbook.PID_FILE.parent / f"{run_playbook.PID_FILE.name}.{_os.getpid()}"
        self.assertEqual(run_playbook.pid_file_for_parent(), expected)

    def test_discover_pid_files_returns_all_per_parent_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            base = temp_path / ".run_pids"
            # Create three per-parent files
            (temp_path / f"{base.name}.111").write_text("111 repoA\n")
            (temp_path / f"{base.name}.222").write_text("222 repoB\n")
            (temp_path / f"{base.name}.333").write_text("333 repoC\n")
            # And an unrelated file that shouldn't match
            (temp_path / "unrelated.txt").write_text("skip")

            original_pid_file = run_playbook.PID_FILE
            try:
                run_playbook.PID_FILE = base
                found = run_playbook.discover_pid_files()
            finally:
                run_playbook.PID_FILE = original_pid_file

            self.assertEqual(len(found), 3)
            self.assertEqual(
                {p.name for p in found},
                {f"{base.name}.111", f"{base.name}.222", f"{base.name}.333"},
            )

    def test_write_pid_file_writes_to_per_parent_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            original_pid_file = run_playbook.PID_FILE
            try:
                run_playbook.PID_FILE = Path(temp_dir) / ".run_pids"
                path = run_playbook.write_pid_file([(4242, "chi-1.4.5"), (4243, "cobra-1.4.5")])
                self.assertTrue(path.exists())
                self.assertTrue(path.name.startswith(".run_pids."))
                content = path.read_text(encoding="utf-8")
                self.assertIn("4242 chi-1.4.5", content)
                self.assertIn("4243 cobra-1.4.5", content)
            finally:
                run_playbook.PID_FILE = original_pid_file


class FormalDocsGuardTests(unittest.TestCase):
    """v1.5.1 Item 1.3: pre-run formal_docs/ guard + --no-formal-docs."""

    def test_missing_directory_triggers_warning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            banner = run_playbook.formal_docs_guard_banner(Path(temp_dir))
            self.assertIsNotNone(banner)
            self.assertIn("formal_docs/ is missing", banner)
            # v1.5.1 Phase 1 rev (Council — gpt-5.4 blocker 3): the
            # remediation command must be cwd-robust. Assert the absolute
            # helper path and sys.executable appear; no literal "python3".
            import sys as _sys
            self.assertIn("setup_formal_docs.py", banner)
            self.assertIn(_sys.executable, banner)
            self.assertIn("setup_repos.sh", banner)
            self.assertIn("--no-formal-docs", banner)

    def test_empty_directory_triggers_warning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "formal_docs").mkdir()
            banner = run_playbook.formal_docs_guard_banner(repo)
            self.assertIsNotNone(banner)
            self.assertIn("formal_docs/ is empty", banner)
            # v1.5.1 Phase 1 rev (Council — gpt-5.4 blocker 3): absolute
            # helper path, not cwd-relative.
            self.assertIn("setup_formal_docs.py", banner)
            self.assertNotIn(" python3 bin/setup_formal_docs.py", banner)

    def test_orphan_plaintext_triggers_warning_with_names(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            formal = repo / "formal_docs"
            formal.mkdir()
            write(formal / "virtio.txt", "body\n")
            # Sidecar-less.
            banner = run_playbook.formal_docs_guard_banner(repo)
            self.assertIsNotNone(banner)
            self.assertIn("without .meta.json sidecars", banner)
            self.assertIn("virtio.txt", banner)

    def test_orphan_list_truncates_at_ten(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            formal = repo / "formal_docs"
            formal.mkdir()
            for i in range(15):
                write(formal / f"doc{i:02d}.txt", "x")
            banner = run_playbook.formal_docs_guard_banner(repo)
            self.assertIsNotNone(banner)
            self.assertIn("... and 5 more", banner)

    def test_clean_state_returns_none(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            formal = repo / "formal_docs"
            formal.mkdir()
            write(formal / "virtio.txt", "body\n")
            write(formal / "virtio.meta.json", '{"tier": 1}\n')
            self.assertIsNone(run_playbook.formal_docs_guard_banner(repo))

    def test_readme_and_backups_do_not_trigger_orphan_warning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            formal = repo / "formal_docs"
            formal.mkdir()
            # README.md is allowed without a sidecar (matches ingest policy).
            write(formal / "README.md", "docs readme\n")
            # Files under .sidecar_backups/ are ignored.
            write(formal / ".sidecar_backups" / "20260101T000000Z" / "old.md", "x")
            write(formal / "virtio.txt", "body\n")
            write(formal / "virtio.meta.json", '{"tier": 1}\n')
            self.assertIsNone(run_playbook.formal_docs_guard_banner(repo))

    def test_parse_args_accepts_no_formal_docs(self) -> None:
        args = run_playbook.parse_args(["--no-formal-docs", "./somedir"])
        self.assertTrue(args.no_formal_docs)
        # Default off.
        args_default = run_playbook.parse_args(["./somedir"])
        self.assertFalse(args_default.no_formal_docs)

    def test_build_worker_command_propagates_no_formal_docs(self) -> None:
        args = run_playbook.argparse.Namespace(
            parallel=False,
            runner="claude",
            no_seeds=False,
            phase=None,
            next_iteration=False,
            full_run=False,
            strategy=["gap"],
            model=None,
            no_formal_docs=True,
            kill=False,
            targets=["./project-a"],
            worker=False,
        )
        command = run_playbook.build_worker_command(args, "/abs/target")
        self.assertIn("--no-formal-docs", command)
        # Flag appears before the positional target.
        self.assertLess(
            command.index("--no-formal-docs"), command.index("/abs/target")
        )

    def test_build_worker_command_omits_flag_when_unset(self) -> None:
        args = run_playbook.argparse.Namespace(
            parallel=False,
            runner="claude",
            no_seeds=False,
            phase=None,
            next_iteration=False,
            full_run=False,
            strategy=["gap"],
            model=None,
            no_formal_docs=False,
            kill=False,
            targets=["./project-a"],
            worker=False,
        )
        command = run_playbook.build_worker_command(args, "/abs/target")
        self.assertNotIn("--no-formal-docs", command)


class GuardRemediationCwdRobustnessTests(unittest.TestCase):
    """v1.5.1 Phase 1 rev (Council — gpt-5.4 blocker 3): the guard's
    remediation command must use sys.executable (not the literal
    "python3") and an absolute path to setup_formal_docs.py so it
    works from any working directory."""

    def _banner_for_missing_formal_docs(self) -> str:
        with TemporaryDirectory() as temp_dir:
            banner = run_playbook.formal_docs_guard_banner(Path(temp_dir))
            assert banner is not None
            return banner

    def test_banner_uses_sys_executable_not_literal_python3(self) -> None:
        import sys as _sys
        banner = self._banner_for_missing_formal_docs()
        self.assertIn(_sys.executable, banner)
        # sys.executable is always absolute.
        self.assertTrue(Path(_sys.executable).is_absolute())
        # Reject bare `python3 bin/setup_formal_docs.py` — the prior form
        # that wasn't cwd-robust.
        self.assertNotIn(" python3 bin/setup_formal_docs.py", banner)
        self.assertFalse(
            banner.startswith("python3 bin/setup_formal_docs.py"),
            "banner must not open with the cwd-relative form",
        )

    def test_banner_contains_absolute_path_to_setup_helper(self) -> None:
        banner = self._banner_for_missing_formal_docs()
        # Extract every token that ends in setup_formal_docs.py; at least
        # one must be an absolute filesystem path.
        tokens = [t for t in banner.split() if t.endswith("bin/setup_formal_docs.py")]
        self.assertTrue(tokens, f"banner has no setup_formal_docs.py reference:\n{banner}")
        absolute_tokens = [t for t in tokens if Path(t).is_absolute()]
        self.assertTrue(
            absolute_tokens,
            f"banner has no absolute path to setup_formal_docs.py. Tokens: {tokens}\nBanner:\n{banner}",
        )
        # The resolved path must actually point at the repo's helper.
        real_helper = (
            Path(run_playbook.__file__).resolve().parent / "setup_formal_docs.py"
        )
        self.assertIn(str(real_helper), banner)


class InvocationFlagsPersistenceTests(unittest.TestCase):
    """v1.5.1 Phase 1 rev (Council — gpt-5.4 blocker 2): the --no-formal-docs
    flag must land in quality/INDEX.md under invocation_flags so a later
    auditor can tell intent from accident."""

    @staticmethod
    def _load_index(repo_dir: Path) -> dict:
        import json as _json
        text = (repo_dir / "quality" / "INDEX.md").read_text(encoding="utf-8")
        start = text.index("```json")
        end = text.index("```", start + len("```json"))
        return _json.loads(text[start + len("```json"): end])

    def test_stub_defaults_no_formal_docs_false(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            run_playbook.write_live_index_stub(repo_dir, "20260420T140000Z")
            payload = self._load_index(repo_dir)
            self.assertIn("invocation_flags", payload)
            self.assertEqual(payload["invocation_flags"]["no_formal_docs"], False)

    def test_stub_records_no_formal_docs_true(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            run_playbook.write_live_index_stub(
                repo_dir, "20260420T140000Z", no_formal_docs=True
            )
            payload = self._load_index(repo_dir)
            self.assertEqual(payload["invocation_flags"]["no_formal_docs"], True)

    def test_final_preserves_no_formal_docs_true(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            # Phase 1 entry writes the stub with the flag.
            run_playbook.write_live_index_stub(
                repo_dir, "20260420T140000Z", no_formal_docs=True
            )
            # Phase 6 re-render must keep the flag.
            run_playbook.write_live_index_final(
                repo_dir,
                "20260420T140000Z",
                gate_verdict="pass",
                no_formal_docs=True,
            )
            payload = self._load_index(repo_dir)
            self.assertEqual(payload["invocation_flags"]["no_formal_docs"], True)
            # Sanity: existing §11 keys survive unchanged.
            for required in (
                "run_timestamp_start",
                "run_timestamp_end",
                "qpb_version",
                "phases_executed",
                "summary",
                "artifacts",
            ):
                self.assertIn(required, payload)

    def test_final_default_keeps_no_formal_docs_false(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            run_playbook.write_live_index_stub(repo_dir, "20260420T140000Z")
            run_playbook.write_live_index_final(
                repo_dir, "20260420T140000Z", gate_verdict="partial"
            )
            payload = self._load_index(repo_dir)
            self.assertEqual(payload["invocation_flags"]["no_formal_docs"], False)


class ConfigureLoggingTests(unittest.TestCase):
    """v1.5.1 Item 2.1: configure_logging() is the single call site that
    produces the canonical log path, announces it, and installs line-
    buffered stdout. Tests use an explicit `stream=` kwarg so stdout
    capture is deterministic without monkey-patching sys.stdout."""

    def _restore_default_echo(self, original: bool) -> None:
        run_playbook.lib.set_default_echo(original)

    def test_returns_same_path_as_log_file_for(self) -> None:
        import io as _io
        original = run_playbook.lib.get_default_echo()
        try:
            with TemporaryDirectory() as temp_dir:
                repo = Path(temp_dir) / "subject"
                repo.mkdir()
                buf = _io.StringIO()
                path = run_playbook.configure_logging(
                    repo, "20260420T140000Z", stream=buf
                )
                expected = run_playbook.log_file_for(repo, "20260420T140000Z").resolve()
                self.assertEqual(path, expected)
                self.assertTrue(path.parent.is_dir())
        finally:
            self._restore_default_echo(original)

    def test_prints_stable_prefix_line(self) -> None:
        import io as _io
        original = run_playbook.lib.get_default_echo()
        try:
            with TemporaryDirectory() as temp_dir:
                repo = Path(temp_dir) / "subject"
                repo.mkdir()
                buf = _io.StringIO()
                run_playbook.configure_logging(
                    repo, "20260420T140000Z", stream=buf
                )
                output = buf.getvalue()
                self.assertTrue(output.startswith(run_playbook._CONFIGURE_LOGGING_PREFIX))
                # Path printed is absolute so operators can copy-paste it.
                path_text = output[len(run_playbook._CONFIGURE_LOGGING_PREFIX):].strip()
                self.assertTrue(Path(path_text).is_absolute())
        finally:
            self._restore_default_echo(original)

    def test_no_stdout_echo_flips_logboth_default(self) -> None:
        import io as _io
        original = run_playbook.lib.get_default_echo()
        try:
            with TemporaryDirectory() as temp_dir:
                repo = Path(temp_dir) / "subject"
                repo.mkdir()
                buf = _io.StringIO()
                run_playbook.configure_logging(
                    repo, "20260420T140000Z",
                    no_stdout_echo=True, stream=buf,
                )
                self.assertFalse(run_playbook.lib.get_default_echo())

                # logboth with default echo must now suppress stdout.
                from contextlib import redirect_stdout
                log_file = run_playbook.log_file_for(repo, "20260420T140000Z")
                captured = _io.StringIO()
                with redirect_stdout(captured):
                    run_playbook.lib.logboth(log_file, "silent in sandbox")
                self.assertEqual(captured.getvalue(), "")
                # Log file still written in full.
                self.assertIn(
                    "silent in sandbox",
                    log_file.read_text(encoding="utf-8"),
                )
        finally:
            self._restore_default_echo(original)

    def test_default_no_stdout_echo_keeps_echo_on(self) -> None:
        import io as _io
        original = run_playbook.lib.get_default_echo()
        try:
            with TemporaryDirectory() as temp_dir:
                repo = Path(temp_dir) / "subject"
                repo.mkdir()
                buf = _io.StringIO()
                run_playbook.configure_logging(
                    repo, "20260420T140000Z", stream=buf
                )
                self.assertTrue(run_playbook.lib.get_default_echo())
        finally:
            self._restore_default_echo(original)


class NoStdoutEchoFlagTests(unittest.TestCase):
    """v1.5.1 Item 2.1: --no-stdout-echo parses, propagates to workers,
    and persists in invocation_flags."""

    def test_parse_args_accepts_no_stdout_echo(self) -> None:
        args = run_playbook.parse_args(["--no-stdout-echo", "./somedir"])
        self.assertTrue(args.no_stdout_echo)
        default_args = run_playbook.parse_args(["./somedir"])
        self.assertFalse(default_args.no_stdout_echo)

    def test_build_worker_command_propagates_no_stdout_echo(self) -> None:
        args = run_playbook.argparse.Namespace(
            parallel=False,
            runner="claude",
            no_seeds=False,
            phase=None,
            next_iteration=False,
            full_run=False,
            strategy=["gap"],
            model=None,
            no_formal_docs=False,
            no_stdout_echo=True,
            kill=False,
            targets=["./project-a"],
            worker=False,
        )
        command = run_playbook.build_worker_command(args, "/abs/target")
        self.assertIn("--no-stdout-echo", command)

    def test_invocation_flags_include_no_stdout_echo(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            run_playbook.write_live_index_stub(
                repo_dir, "20260420T140000Z", no_stdout_echo=True
            )
            # Read back the payload from INDEX.md.
            text = (repo_dir / "quality" / "INDEX.md").read_text(encoding="utf-8")
            import json as _json
            start = text.index("```json") + len("```json")
            end = text.index("```", start)
            payload = _json.loads(text[start:end])
            self.assertTrue(payload["invocation_flags"]["no_stdout_echo"])

    def test_invocation_flags_default_no_stdout_echo_false(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            run_playbook.write_live_index_stub(repo_dir, "20260420T140000Z")
            text = (repo_dir / "quality" / "INDEX.md").read_text(encoding="utf-8")
            import json as _json
            start = text.index("```json") + len("```json")
            end = text.index("```", start)
            payload = _json.loads(text[start:end])
            self.assertFalse(payload["invocation_flags"]["no_stdout_echo"])


if __name__ == "__main__":
    unittest.main()
