"""Pipeline-activation tests — v1.5.4 Phase 2.

For each of the five fixture role-map shapes from the v1.5.4 Phase 1
brief, assert which downstream pipelines activate. The contract Phase 2
ships is the activation outcome — that the four-pass skill-derivation
pipeline, the code-review pipeline, and the prose-to-code divergence
check each turn on / off based on the role map alone.

Activation surfaces tested:

  - **Four-pass pipeline** — gated at ``bin.skill_derivation.__main__``
    by ``has_skill_prose(role_map)``.
  - **Code-review pipeline** — Phase 3 in ``bin.run_playbook``; gated
    by ``_code_review_should_skip(repo_dir)`` returning ``None``.
  - **Prose-to-code LLM divergence** — gated by ``has_skill_tools(role_map)``
    flipping ``ProseToCodeLLMConfig.should_run``.

Fixture shapes (from ``bin/tests/test_role_tagging.py``):

  1. **pdf-style** — skill-prose + skill-reference + skill-tool, no code.
     Four-pass: on. Code-review: off. Prose-to-code: on.
  2. **Pure-Markdown skill** — skill-prose only.
     Four-pass: on. Code-review: off. Prose-to-code: off.
  3. **Pure-code project** — code only.
     Four-pass: off. Code-review: on. Prose-to-code: off.
  4. **QPB-style** — skill-prose + skill-reference + code, no skill-tools.
     Four-pass: on. Code-review: on. Prose-to-code: off.
  5. **Pre-played benchmark** — target's intrinsic surface plus a
     ``playbook-output`` carry-over. Activation reflects the target's
     intrinsic surface only; ``playbook-output`` does not turn anything
     on or off.

Tests are deterministic: each writes a hand-built role map to a temp
directory and queries the activation predicates. No LLM is invoked —
the contract under test is "did the right pipelines flip on", not
"what did the pipeline emit when it ran".
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin import role_map as rm
from bin import run_playbook
from bin.skill_derivation import divergence_prose_to_code_llm as p2c_llm


# ---------------------------------------------------------------------------
# Fixture builders.
# ---------------------------------------------------------------------------


def _entry(path: str, role: str, size: int, **extra) -> dict:
    rec = {
        "path": path,
        "role": role,
        "size_bytes": size,
        "rationale": f"fixture entry for {path}",
    }
    rec.update(extra)
    return rec


def _make_role_map(files: list[dict]) -> dict:
    return {
        "schema_version": rm.SCHEMA_VERSION,
        "timestamp_start": "2026-04-29T00:00:00Z",
        "files": files,
        "breakdown": rm.compute_breakdown(files),
    }


def _write_role_map(repo_dir: Path, role_map: dict) -> Path:
    """Write the role map to ``<repo>/quality/exploration_role_map.json``
    so the on-disk consumers (Phase 3 skip predicate, the four-pass
    dispatch helper) can find it."""
    quality = repo_dir / "quality"
    quality.mkdir(parents=True, exist_ok=True)
    out = quality / "exploration_role_map.json"
    out.write_text(json.dumps(role_map), encoding="utf-8")
    return out


# Activation predicate trio captured as a triple so each test asserts a
# single tuple match instead of three separate calls. Order matches
# (four-pass, code-review, prose-to-code).
def _activations(role_map: dict, repo_dir: Path) -> tuple[bool, bool, bool]:
    _write_role_map(repo_dir, role_map)
    four_pass_on = rm.has_skill_prose(role_map)
    # Site 2 helper inverts has_code: returns None when code path
    # should run, returns a skip-reason string when it should no-op.
    code_review_on = run_playbook._code_review_should_skip(repo_dir) is None
    prose_to_code_on = rm.has_skill_tools(role_map)
    return four_pass_on, code_review_on, prose_to_code_on


# ---------------------------------------------------------------------------
# Fixture 1 — pdf-style (skill-prose + skill-reference + skill-tool, no code).
# ---------------------------------------------------------------------------


class PdfStylePipelineActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.role_map = _make_role_map([
            _entry("SKILL.md", "skill-prose", 6000),
            _entry("references/forms.md", "skill-reference", 2000),
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

    def test_activation_outcome(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(
                _activations(self.role_map, Path(tmp)),
                (True, False, True),
                "pdf-style: four-pass + prose-to-code on; code-review off",
            )

    def test_prose_to_code_config_should_run_is_true(self) -> None:
        cfg = p2c_llm.ProseToCodeLLMConfig(
            formal_path=Path("/tmp/unused"),
            output_path=Path("/tmp/unused"),
            progress_path=Path("/tmp/unused"),
            repo_root=Path("/tmp/unused"),
            sections_path=Path("/tmp/unused"),
            pass_spec_path=Path("/tmp/unused"),
            should_run=rm.has_skill_tools(self.role_map),
        )
        self.assertTrue(cfg.should_run)


# ---------------------------------------------------------------------------
# Fixture 2 — pure-Markdown skill (only skill-prose).
# ---------------------------------------------------------------------------


class PureMarkdownPipelineActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.role_map = _make_role_map([
            _entry("SKILL.md", "skill-prose", 4000),
        ])

    def test_activation_outcome(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(
                _activations(self.role_map, Path(tmp)),
                (True, False, False),
                "pure-markdown: four-pass on; code-review + prose-to-code off",
            )


# ---------------------------------------------------------------------------
# Fixture 3 — pure-code project (no skill surface).
# ---------------------------------------------------------------------------


class PureCodePipelineActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.role_map = _make_role_map([
            _entry("router.go", "code", 12000),
            _entry("middleware.go", "code", 6000),
            _entry("router_test.go", "test", 4000),
            _entry("README.md", "docs", 1500),
        ])

    def test_activation_outcome(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(
                _activations(self.role_map, Path(tmp)),
                (False, True, False),
                "pure-code: code-review on; four-pass + prose-to-code off",
            )

    def test_skill_derivation_short_circuits_with_no_skill_prose(self) -> None:
        # The four-pass dispatch loads the role map to decide whether
        # to enter pass A/B/C/D. has_skill_prose=False is the same
        # signal _main uses to no-op early.
        self.assertFalse(rm.has_skill_prose(self.role_map))


# ---------------------------------------------------------------------------
# Fixture 4 — QPB-style (skill-prose + skill-reference + code, no skill-tools).
# ---------------------------------------------------------------------------


class QpbStylePipelineActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.role_map = _make_role_map([
            _entry("SKILL.md", "skill-prose", 8000),
            _entry("agents/code-reviewer.md", "skill-prose", 1200),
            _entry(
                "references/exploration_patterns.md",
                "skill-reference",
                3000,
            ),
            _entry("bin/run_playbook.py", "code", 90000),
            _entry("bin/archive_lib.py", "code", 24000),
            _entry("bin/tests/test_archive_lib.py", "test", 8000),
        ])

    def test_activation_outcome(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(
                _activations(self.role_map, Path(tmp)),
                (True, True, False),
                "QPB-style: four-pass + code-review on; prose-to-code off "
                "(no skill-tools — bin/*.py is code, not skill-tool)",
            )


# ---------------------------------------------------------------------------
# Fixture 5 — pre-played benchmark (intrinsic code + playbook-output carry-over).
# ---------------------------------------------------------------------------


class PrePlayedBenchmarkPipelineActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.role_map = _make_role_map([
            # Target's intrinsic surface — pure code.
            _entry("src/parser.py", "code", 3000),
            _entry("src/serializer.py", "code", 2000),
            # Prior playbook output. Must NOT toggle any pipeline on.
            _entry("quality/EXPLORATION.md", "playbook-output", 4000),
            _entry(".github/skills/quality_gate.py", "playbook-output", 50000),
        ])

    def test_activation_outcome(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(
                _activations(self.role_map, Path(tmp)),
                (False, True, False),
                "pre-played benchmark: code-review on (intrinsic code); "
                "playbook-output does not activate skill or tool paths",
            )

    def test_playbook_output_only_target_activates_nothing(self) -> None:
        playbook_only = _make_role_map([
            _entry("quality/EXPLORATION.md", "playbook-output", 4000),
            _entry(".github/skills/quality_gate.py", "playbook-output", 50000),
        ])
        with TemporaryDirectory() as tmp:
            self.assertEqual(
                _activations(playbook_only, Path(tmp)),
                (False, False, False),
                "playbook-output only: every pipeline no-ops",
            )


# ---------------------------------------------------------------------------
# Site 2 — Phase 3 skip-predicate behavior on edge cases.
# ---------------------------------------------------------------------------


class CodeReviewSkipPredicateTests(unittest.TestCase):
    """v1.5.4 Phase 2 Site 2: ``_code_review_should_skip`` returns
    ``None`` (Phase 3 runs) when the role map is absent or unparseable.
    Pre-Phase-1 invocations and pre-iteration targets keep the v1.5.3
    behaviour — Phase 3 runs as before. A present-and-valid role map
    with zero ``code`` files returns a skip-reason string."""

    def test_no_role_map_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertIsNone(
                run_playbook._code_review_should_skip(Path(tmp))
            )

    def test_unparseable_role_map_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            quality = Path(tmp) / "quality"
            quality.mkdir()
            (quality / "exploration_role_map.json").write_text(
                "{ not json", encoding="utf-8"
            )
            self.assertIsNone(
                run_playbook._code_review_should_skip(Path(tmp))
            )

    def test_role_map_with_code_returns_none(self) -> None:
        rmap = _make_role_map([_entry("src/main.py", "code", 100)])
        with TemporaryDirectory() as tmp:
            _write_role_map(Path(tmp), rmap)
            self.assertIsNone(
                run_playbook._code_review_should_skip(Path(tmp))
            )

    def test_role_map_without_code_returns_skip_reason(self) -> None:
        rmap = _make_role_map([_entry("SKILL.md", "skill-prose", 1000)])
        with TemporaryDirectory() as tmp:
            _write_role_map(Path(tmp), rmap)
            reason = run_playbook._code_review_should_skip(Path(tmp))
            self.assertIsNotNone(reason)
            self.assertIn("Phase 3", reason)
            self.assertIn("zero", reason)


# ---------------------------------------------------------------------------
# Site 3 — prose-to-code LLM no-op contract.
# ---------------------------------------------------------------------------


class ProseToCodeLLMActivationTests(unittest.TestCase):
    """v1.5.4 Phase 2 Site 3: ``run_divergence_prose_to_code_llm``
    no-ops cleanly when ``config.should_run`` is False, irrespective
    of what the LLM runner would return. The skipped_reason must
    explicitly name skill-tool so operators can trace the gate."""

    def _make_config(self, *, should_run: bool) -> p2c_llm.ProseToCodeLLMConfig:
        return p2c_llm.ProseToCodeLLMConfig(
            formal_path=Path("/tmp/unused"),
            output_path=Path("/tmp/unused"),
            progress_path=Path("/tmp/unused"),
            repo_root=Path("/tmp/unused"),
            sections_path=Path("/tmp/unused"),
            pass_spec_path=Path("/tmp/unused"),
            should_run=should_run,
        )

    def test_should_run_false_short_circuits_with_skill_tool_reason(self) -> None:
        cfg = self._make_config(should_run=False)

        class _FailingRunner:
            def run(self, prompt):  # noqa: D401, ANN001
                raise AssertionError(
                    "runner.run must NOT be invoked when should_run is False"
                )

        result = p2c_llm.run_divergence_prose_to_code_llm(
            cfg, _FailingRunner()
        )
        self.assertEqual(result["calls_made"], 0)
        self.assertEqual(result["divergences_emitted"], 0)
        self.assertIn("skill-tool", result["skipped_reason"])


if __name__ == "__main__":
    unittest.main()
