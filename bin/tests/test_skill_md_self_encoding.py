"""SKILL.md self-encoding prose-contract tests (v1.5.4 Phase 3.9, B-18b).

After the Phase 3.9 rewrite, SKILL.md self-encodes the canonical
invocation, bootstrap mode, v1.5.4 mechanics pointers, the
operational guardrails, and the output artifact contract — so that a
single-line operator prompt ("Run the Quality Playbook") pointed at
any AI agent against any QPB-installed target produces a v1.5.4-shape
bootstrap run without further hand-holding.

These tests are coarse string-presence assertions. They protect
against accidental regressions during future SKILL.md edits — if a
maintainer trims the prose and drops the canonical-invocation
reference, the no-delegation guardrail, etc., the matching test
fires.

The tests do NOT pin exact wording. The brief explicitly framed
these as "string-presence" assertions; they catch the load-bearing
content disappearing, not phrasing changes. If a future edit
substantively reshapes the section AND the corresponding test fails,
update the test alongside the prose — the test pins the contract,
not a literal copy.
"""

from __future__ import annotations

import unittest
from pathlib import Path


SKILL_MD = Path(__file__).resolve().parents[2] / "SKILL.md"


def _read_skill_md() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


class SkillMdSelfEncodingTests(unittest.TestCase):
    """v1.5.4 Phase 3.9 (B-18b): pin the load-bearing prose
    contract. Each test corresponds to one of the 6 brief-mandated
    string-presence assertions."""

    def test_skill_md_documents_canonical_invocation(self) -> None:
        text = _read_skill_md()
        # The canonical invocation pattern. Operators / AI agents
        # reading this section should infer `python3 -m bin.run_playbook
        # <target>` from the prose without ambiguity.
        self.assertIn("python3 -m bin.run_playbook", text)

    def test_skill_md_documents_bootstrap_mode(self) -> None:
        text = _read_skill_md()
        # "Bootstrap" framing: target == QPB repo, archive of existing
        # quality/ to previous_runs/ is automatic, the operator
        # doesn't need to clean anything manually.
        self.assertIn("Bootstrap mode", text)
        self.assertIn("python3 -m bin.run_playbook .", text)
        self.assertIn("previous_runs", text)

    def test_skill_md_names_role_map_artifact(self) -> None:
        text = _read_skill_md()
        # v1.5.4 architecture anchor: the role map is the canonical
        # routing input for downstream pipelines. Naming it in
        # SKILL.md makes the architecture operator-visible.
        self.assertIn("exploration_role_map.json", text)
        self.assertIn("schema_version", text)
        self.assertIn("target_role_breakdown", text)

    def test_skill_md_forbids_sub_agent_delegation(self) -> None:
        text = _read_skill_md()
        # The B-15 failure mode (Phase 1 completes, phases 2-6 die in
        # a delegated agent) is the most consequential v1.5.4
        # guardrail. SKILL.md must explicitly forbid sub-agent
        # delegation in operator-facing prose.
        self.assertIn("Task tool", text)
        # The "Synchronous execution" framing surfaces the
        # discipline as a hard constraint, not a suggestion.
        self.assertIn("Synchronous execution", text)
        self.assertIn("sub-agent", text)

    def test_skill_md_forbids_source_patching(self) -> None:
        text = _read_skill_md()
        # If you encounter a bug in QPB source mid-run, STOP +
        # report; do not patch. Codex's 2026-04-29 self-audit
        # attempt patched bin/archive_lib.py mid-run; the structural
        # backstop catches it but the prose discipline names it.
        self.assertIn("STOP and report", text)
        self.assertIn("Don't patch QPB source", text)

    def test_skill_md_forbids_sentinel_deletion(self) -> None:
        text = _read_skill_md()
        # `.gitignore !`-rule sentinels (.gitkeep files etc.) keep
        # tracked directories present. Codex deleted them; SKILL.md
        # must explicitly tell the agent not to.
        self.assertIn("sentinel", text.lower())
        self.assertIn(".gitkeep", text)
        self.assertIn("Don't delete sentinel files", text)


class SkillMdGuardrailsExtraTests(unittest.TestCase):
    """Additional contract pins for v1.5.4 mechanics not specifically
    enumerated in the 6-test brief but flagged by the brief's
    'Guardrails' subsection. These are auxiliary; failures here are
    real but lower-priority than the 6 above."""

    def test_skill_md_documents_git_ls_files_for_phase_1(self) -> None:
        text = _read_skill_md()
        # Phase 1 enumeration must use git ls-files (not os.walk /
        # find / listdir). Codex walked .git/ + .venv/ via os.walk
        # producing a 5287-entry role map.
        self.assertIn("git ls-files", text)

    def test_skill_md_lists_disallowed_path_prefixes(self) -> None:
        text = _read_skill_md()
        # The role-map validator rejects these prefixes; SKILL.md
        # documents them so the agent avoids producing them.
        for prefix in (".git/", ".venv/", "node_modules/"):
            self.assertIn(prefix, text)

    def test_skill_md_documents_full_run_default(self) -> None:
        text = _read_skill_md()
        # B-18a: bare invocation defaults to full-run. The prose
        # encodes this so the operator/AI doesn't add unnecessary
        # flags.
        self.assertIn("full run", text.lower())
        self.assertIn("6 phases", text)
        self.assertIn("4 iteration", text)


if __name__ == "__main__":
    unittest.main()
