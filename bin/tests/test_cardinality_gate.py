"""Merge-gate anchor tests for the v1.5.2 cardinality reconciliation gate.

The adversarial test (test_adversarial_three_cells_one_cover_fails) is the
release-blocking merge gate. Until it passes against the current pipeline,
v1.5.2 is not load-bearing.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Resolve the gate module path — it lives inside .github/skills/quality_gate/.
QPB_ROOT = Path(__file__).resolve().parent.parent.parent
GATE_DIR = QPB_ROOT / ".github" / "skills" / "quality_gate"
sys.path.insert(0, str(GATE_DIR))

import quality_gate  # type: ignore


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture_grid(req_id: str, cells_present: dict) -> dict:
    """Build a minimal compensation_grid.json dict.

    cells_present: dict mapping cell_id → bool (True = present, False = absent).
    """
    return {
        "schema_version": "1.5.2",
        "reqs": {
            req_id: {
                "pattern": "whitelist",
                "items": ["ITEM_A", "ITEM_B", "ITEM_C"],
                "sites": ["SITE"],
                "cells": [
                    {"cell_id": cid, "item": cid.split("-")[-2], "site": cid.split("-")[-1], "present": present}
                    for cid, present in cells_present.items()
                ],
            }
        },
    }


def _requirements_md(req_id: str, pattern: str = "whitelist") -> str:
    return (
        f"# Requirements\n\n"
        f"### {req_id}: test requirement\n"
        f"- Summary: test\n"
        f"- Pattern: {pattern}\n"
    )


def _bugs_md(bug_entries: list) -> str:
    out = ["# Bug Report\n\n"]
    for bug in bug_entries:
        out.append(f"### BUG-{bug['id']}: {bug.get('title', 'test bug')}\n")
        out.append(f"- Primary requirement: {bug['req']}\n")
        if bug.get("covers"):
            out.append(f"- Covers: [{', '.join(bug['covers'])}]\n")
        if bug.get("rationale"):
            out.append(f"- Consolidation rationale: {bug['rationale']}\n")
        out.append("\n")
    return "".join(out)


class CardinalityGateTests(unittest.TestCase):

    # ---- MERGE-GATE ANCHOR ----------------------------------------------
    def test_adversarial_three_cells_one_cover_fails(self):
        """Adversarial fixture: grid has 3 absent cells, reviewer covers 1.

        This is the release-blocking merge gate for v1.5.2. A correctly
        implemented gate MUST fail and name the two uncovered cells.
        """
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            q = repo / "quality"
            cells = {
                "REQ-010/cell-RING_RESET-MMIO": False,
                "REQ-010/cell-RING_RESET-vDPA": False,
                "REQ-010/cell-SR_IOV-MMIO": False,
            }
            _write(q / "compensation_grid.json", json.dumps(_fixture_grid("REQ-010", cells)))
            _write(q / "REQUIREMENTS.md", _requirements_md("REQ-010"))
            _write(q / "BUGS.md", _bugs_md([
                {
                    "id": "001",
                    "req": "REQ-010",
                    "covers": ["REQ-010/cell-RING_RESET-MMIO"],
                },
            ]))

            failures = quality_gate.validate_cardinality_gate(repo)

            self.assertTrue(
                failures,
                "MERGE GATE FAILURE: cardinality gate let a 3-cell/1-cover "
                "adversarial fixture pass. v1.5.2 is not load-bearing.",
            )
            combined = " ".join(failures)
            self.assertIn("REQ-010/cell-RING_RESET-vDPA", combined)
            self.assertIn("REQ-010/cell-SR_IOV-MMIO", combined)
            uncovered_line = next((f for f in failures if "uncovered" in f), "")
            self.assertNotIn("REQ-010/cell-RING_RESET-MMIO", uncovered_line,
                             "covered cell should not appear as uncovered")
    # ---------------------------------------------------------------------

    def test_all_cells_covered_by_bugs_passes(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            q = repo / "quality"
            cells = {
                "REQ-010/cell-A-SITE": False,
                "REQ-010/cell-B-SITE": False,
            }
            _write(q / "compensation_grid.json", json.dumps(_fixture_grid("REQ-010", cells)))
            _write(q / "REQUIREMENTS.md", _requirements_md("REQ-010"))
            _write(q / "BUGS.md", _bugs_md([
                {"id": "001", "req": "REQ-010", "covers": ["REQ-010/cell-A-SITE"]},
                {"id": "002", "req": "REQ-010", "covers": ["REQ-010/cell-B-SITE"]},
            ]))
            self.assertEqual(quality_gate.validate_cardinality_gate(repo), [])

    def test_mix_of_bugs_and_downgrades_passes(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            q = repo / "quality"
            cells = {
                "REQ-010/cell-A-SITE": False,
                "REQ-010/cell-B-SITE": False,
            }
            _write(q / "compensation_grid.json", json.dumps(_fixture_grid("REQ-010", cells)))
            _write(q / "REQUIREMENTS.md", _requirements_md("REQ-010"))
            _write(q / "BUGS.md", _bugs_md([
                {"id": "001", "req": "REQ-010", "covers": ["REQ-010/cell-A-SITE"]},
            ]))
            _write(q / "compensation_grid_downgrades.json", json.dumps({
                "schema_version": "1.5.2",
                "downgrades": [{
                    "cell_id": "REQ-010/cell-B-SITE",
                    "authority_ref": "docs/spec.md:1",
                    "site_citation": "src/thing.py:10-20",
                    "reason_class": "out-of-scope",
                    "falsifiable_claim": "B is not required here because spec scopes it to A-only; falsifiable by showing spec text requiring B.",
                }],
            }))
            self.assertEqual(quality_gate.validate_cardinality_gate(repo), [])

    def test_no_pattern_reqs_skips_gate(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            q = repo / "quality"
            _write(q / "REQUIREMENTS.md", "# Requirements\n\n### REQ-001: plain req\n- Summary: x\n")
            # No grid file, no pattern REQs → gate passes silently.
            self.assertEqual(quality_gate.validate_cardinality_gate(repo), [])

    def test_pattern_req_without_grid_fails(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            q = repo / "quality"
            _write(q / "REQUIREMENTS.md", _requirements_md("REQ-010"))
            # No compensation_grid.json — this should fail.
            failures = quality_gate.validate_cardinality_gate(repo)
            self.assertTrue(any("compensation_grid.json is missing" in f for f in failures))

    def test_downgrade_missing_falsifiable_claim_fails(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            q = repo / "quality"
            cells = {"REQ-010/cell-A-SITE": False}
            _write(q / "compensation_grid.json", json.dumps(_fixture_grid("REQ-010", cells)))
            _write(q / "REQUIREMENTS.md", _requirements_md("REQ-010"))
            _write(q / "BUGS.md", "")
            _write(q / "compensation_grid_downgrades.json", json.dumps({
                "schema_version": "1.5.2",
                "downgrades": [{
                    "cell_id": "REQ-010/cell-A-SITE",
                    "authority_ref": "docs/spec.md:1",
                    "site_citation": "src/x.py:1",
                    "reason_class": "out-of-scope",
                    "falsifiable_claim": "",
                }],
            }))
            failures = quality_gate.validate_cardinality_gate(repo)
            self.assertTrue(any("falsifiable_claim" in f for f in failures))

    def test_downgrade_invalid_reason_class_fails(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            q = repo / "quality"
            cells = {"REQ-010/cell-A-SITE": False}
            _write(q / "compensation_grid.json", json.dumps(_fixture_grid("REQ-010", cells)))
            _write(q / "REQUIREMENTS.md", _requirements_md("REQ-010"))
            _write(q / "BUGS.md", "")
            _write(q / "compensation_grid_downgrades.json", json.dumps({
                "schema_version": "1.5.2",
                "downgrades": [{
                    "cell_id": "REQ-010/cell-A-SITE",
                    "authority_ref": "docs/spec.md:1",
                    "site_citation": "src/x.py:1",
                    "reason_class": "made-up-reason",
                    "falsifiable_claim": "Claim text.",
                }],
            }))
            failures = quality_gate.validate_cardinality_gate(repo)
            self.assertTrue(any("reason_class" in f for f in failures))

    def test_multi_cell_covers_without_consolidation_rationale_fails(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            q = repo / "quality"
            cells = {
                "REQ-010/cell-A-SITE": False,
                "REQ-010/cell-B-SITE": False,
            }
            _write(q / "compensation_grid.json", json.dumps(_fixture_grid("REQ-010", cells)))
            _write(q / "REQUIREMENTS.md", _requirements_md("REQ-010"))
            _write(q / "BUGS.md", _bugs_md([
                {
                    "id": "001",
                    "req": "REQ-010",
                    "covers": ["REQ-010/cell-A-SITE", "REQ-010/cell-B-SITE"],
                },
            ]))
            failures = quality_gate.validate_cardinality_gate(repo)
            self.assertTrue(any("Consolidation rationale" in f for f in failures))

    # ---- Grid-omission cross-check (Round 4 Council convergent finding) ----
    def _two_req_requirements_md(self, reqs):
        """reqs: list of (req_id, pattern_or_None) tuples."""
        out = ["# Requirements\n\n"]
        for req_id, pattern in reqs:
            out.append("### {}: test requirement\n".format(req_id))
            out.append("- Summary: test\n")
            if pattern is not None:
                out.append("- Pattern: {}\n".format(pattern))
            out.append("\n")
        return "".join(out)

    def test_grid_contains_all_pattern_tagged_reqs_passes(self):
        """Positive case: every pattern-tagged REQ appears in the grid."""
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            q = repo / "quality"
            grid = {
                "schema_version": "1.5.2",
                "reqs": {
                    "REQ-001": {
                        "pattern": "whitelist",
                        "items": ["A"], "sites": ["S"],
                        "cells": [{"cell_id": "REQ-001/cell-A-S", "item": "A", "site": "S", "present": True}],
                    },
                    "REQ-002": {
                        "pattern": "parity",
                        "items": ["B"], "sites": ["S"],
                        "cells": [{"cell_id": "REQ-002/cell-B-S", "item": "B", "site": "S", "present": True}],
                    },
                },
            }
            _write(q / "compensation_grid.json", json.dumps(grid))
            _write(
                q / "REQUIREMENTS.md",
                self._two_req_requirements_md([("REQ-001", "whitelist"), ("REQ-002", "parity")]),
            )
            _write(q / "BUGS.md", "")
            self.assertEqual(quality_gate.validate_cardinality_gate(repo), [])

    def test_pattern_tagged_req_missing_from_grid_fails(self):
        """Grid-omission case: REQ-002 is pattern-tagged in REQUIREMENTS.md
        but missing from compensation_grid.json. Gate must surface exactly one
        failure naming REQ-002 and its pattern."""
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            q = repo / "quality"
            grid = {
                "schema_version": "1.5.2",
                "reqs": {
                    "REQ-001": {
                        "pattern": "whitelist",
                        "items": ["A"], "sites": ["S"],
                        "cells": [{"cell_id": "REQ-001/cell-A-S", "item": "A", "site": "S", "present": True}],
                    },
                },
            }
            _write(q / "compensation_grid.json", json.dumps(grid))
            _write(
                q / "REQUIREMENTS.md",
                self._two_req_requirements_md([("REQ-001", "whitelist"), ("REQ-002", "parity")]),
            )
            _write(q / "BUGS.md", "")
            failures = quality_gate.validate_cardinality_gate(repo)
            matches = [f for f in failures if "REQ-002" in f and "compensation_grid.json" in f]
            self.assertEqual(
                len(matches), 1,
                "Expected exactly one failure naming REQ-002; got failures: {!r}".format(failures),
            )
            self.assertIn("parity", matches[0])

    def test_req_without_pattern_not_in_grid_passes(self):
        """Not-tagged-not-in-grid case: REQ-001 has no Pattern field; no grid
        entry is required. Gate passes with no failure from the cross-check."""
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            q = repo / "quality"
            _write(
                q / "REQUIREMENTS.md",
                self._two_req_requirements_md([("REQ-001", None)]),
            )
            # No grid file at all — legitimate when no REQ is pattern-tagged.
            self.assertEqual(quality_gate.validate_cardinality_gate(repo), [])

    def test_invalid_req_pattern_value_fails(self):
        """Invalid pattern case: REQUIREMENTS.md carries ``- Pattern: bogus``.
        ValueError from extract_req_pattern() must be surfaced as a
        REQUIREMENTS.md failure rather than crash the gate."""
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            q = repo / "quality"
            _write(q / "compensation_grid.json", json.dumps({"schema_version": "1.5.2", "reqs": {}}))
            _write(
                q / "REQUIREMENTS.md",
                self._two_req_requirements_md([("REQ-001", "bogus")]),
            )
            _write(q / "BUGS.md", "")
            failures = quality_gate.validate_cardinality_gate(repo)
            self.assertTrue(
                any("REQUIREMENTS.md:" in f and "bogus" in f for f in failures),
                "Expected a REQUIREMENTS.md failure naming 'bogus'; got: {!r}".format(failures),
            )
    # -----------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
