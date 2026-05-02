"""Tests for the Quality Playbook installer scripts."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "install-quality-playbook.sh"
CLAUDE_WRAPPER = ROOT / "install-claude-code.sh"


def _run_installer(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(INSTALLER), *args, str(target)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _run_wrapper(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(CLAUDE_WRAPPER), *args, str(target)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _read_manifest(target: Path) -> dict:
    return json.loads((target / ".quality-playbook-install.json").read_text(encoding="utf-8"))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class InstallQualityPlaybookTests(unittest.TestCase):
    def test_auto_fresh_target_installs_claude_layout_and_shared_files(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp)

            _run_installer(target)

            self.assertTrue((target / ".claude/skills/quality-playbook/SKILL.md").is_file())
            self.assertTrue((target / ".claude/skills/quality-playbook/LICENSE.txt").is_file())
            self.assertTrue((target / ".claude/skills/quality-playbook/quality_gate.py").is_file())
            self.assertTrue((target / ".claude/skills/quality-playbook/references/iteration.md").is_file())
            self.assertTrue((target / ".claude/skills/quality-playbook/phase_prompts/phase1.md").is_file())
            self.assertTrue((target / "agents/quality-playbook.agent.md").is_file())
            self.assertTrue((target / "agents/quality-playbook-claude.agent.md").is_file())
            self.assertTrue((target / "reference_docs/cite").is_dir())
            self.assertFalse((target / ".github/skills/SKILL.md").exists())
            self.assertFalse((target / ".gitignore").exists())

            manifest = _read_manifest(target)
            self.assertEqual(manifest["selected_layouts"], ["claude"])
            paths = {entry["path"] for entry in manifest["installed_files"]}
            self.assertIn(".claude/skills/quality-playbook/SKILL.md", paths)
            self.assertIn(".claude/skills/quality-playbook/LICENSE.txt", paths)
            self.assertIn(".claude/skills/quality-playbook/phase_prompts/phase1.md", paths)
            self.assertIn("agents/quality-playbook.agent.md", paths)

    def test_existing_claude_install_is_idempotent(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp)
            _run_installer(target)

            result = _run_installer(target)

            self.assertIn("No file changes needed.", result.stdout)
            self.assertFalse((target / ".quality-playbook-backups").exists())
            self.assertTrue((target / ".quality-playbook-install.json").is_file())

    def test_auto_updates_detected_copilot_flat_and_nested_layouts(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp)
            _write(target / ".github/skills/SKILL.md", "old flat\n")
            _write(target / ".github/skills/quality-playbook/SKILL.md", "old nested\n")

            _run_installer(target)

            source_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
            self.assertEqual((target / ".github/skills/SKILL.md").read_text(encoding="utf-8"), source_skill)
            self.assertEqual(
                (target / ".github/skills/quality-playbook/SKILL.md").read_text(encoding="utf-8"),
                source_skill,
            )
            self.assertTrue((target / ".github/skills/LICENSE.txt").is_file())
            self.assertTrue((target / ".github/skills/quality-playbook/LICENSE.txt").is_file())
            self.assertTrue((target / ".github/skills/quality_gate.py").is_file())
            self.assertTrue((target / ".github/skills/quality-playbook/quality_gate.py").is_file())
            self.assertTrue((target / ".github/skills/phase_prompts/phase1.md").is_file())
            self.assertTrue((target / ".github/skills/quality-playbook/phase_prompts/phase1.md").is_file())
            self.assertFalse((target / ".claude/skills/quality-playbook/SKILL.md").exists())
            self.assertEqual(_read_manifest(target)["selected_layouts"], ["copilot-flat", "copilot-nested"])

    def test_layout_all_creates_every_supported_layout(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp)

            _run_installer(target, "--layout", "all")

            self.assertTrue((target / ".claude/skills/quality-playbook/SKILL.md").is_file())
            self.assertTrue((target / ".github/skills/SKILL.md").is_file())
            self.assertTrue((target / ".github/skills/quality-playbook/SKILL.md").is_file())
            self.assertEqual(
                _read_manifest(target)["selected_layouts"],
                ["claude", "copilot-flat", "copilot-nested"],
            )

    def test_dry_run_changes_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp)

            result = _run_installer(target, "--layout", "all", "--dry-run")

            self.assertIn("Would create file: .claude/skills/quality-playbook/SKILL.md", result.stdout)
            self.assertEqual(list(target.iterdir()), [])

    def test_modified_installed_file_is_backed_up_before_replacement(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp)
            _run_installer(target)
            skill_path = target / ".claude/skills/quality-playbook/SKILL.md"
            skill_path.write_text(skill_path.read_text(encoding="utf-8") + "\nlocal edit\n", encoding="utf-8")

            _run_installer(target)

            backups = list((target / ".quality-playbook-backups").rglob("SKILL.md"))
            self.assertEqual(len(backups), 1)
            self.assertIn("local edit", backups[0].read_text(encoding="utf-8"))
            self.assertNotIn("local edit", skill_path.read_text(encoding="utf-8"))

    def test_stale_files_are_removed_and_user_owned_paths_survive(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp)
            _run_installer(target)
            _write(target / ".claude/skills/quality-playbook/quality_gate.sh", "legacy gate\n")
            _write(target / ".claude/skills/quality-playbook/references/stale.md", "stale reference\n")
            _write(target / ".claude/skills/quality-playbook/phase_prompts/stale.md", "stale prompt\n")
            _write(target / "agents/quality-playbook-old.agent.md", "stale agent\n")
            _write(target / "reference_docs/cite/spec.md", "spec text\n")
            _write(target / "quality/BUGS.md", "bug text\n")
            _write(target / "AGENTS.md", "user agent guide\n")

            _run_installer(target)

            self.assertFalse((target / ".claude/skills/quality-playbook/quality_gate.sh").exists())
            self.assertFalse((target / ".claude/skills/quality-playbook/references/stale.md").exists())
            self.assertFalse((target / ".claude/skills/quality-playbook/phase_prompts/stale.md").exists())
            self.assertFalse((target / "agents/quality-playbook-old.agent.md").exists())
            self.assertEqual((target / "reference_docs/cite/spec.md").read_text(encoding="utf-8"), "spec text\n")
            self.assertEqual((target / "quality/BUGS.md").read_text(encoding="utf-8"), "bug text\n")
            self.assertEqual((target / "AGENTS.md").read_text(encoding="utf-8"), "user agent guide\n")

    def test_claude_wrapper_installs_only_claude_layout(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp)

            _run_wrapper(target)

            self.assertTrue((target / ".claude/skills/quality-playbook/SKILL.md").is_file())
            self.assertFalse((target / ".github/skills/SKILL.md").exists())
            self.assertEqual(_read_manifest(target)["selected_layouts"], ["claude"])


if __name__ == "__main__":
    unittest.main()
