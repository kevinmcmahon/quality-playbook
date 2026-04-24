"""Tests for bin.reference_docs_ingest (v1.5.2)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bin import reference_docs_ingest as rdi


def _scaffold(tmp: Path, *, skill_version: str = "1.5.2") -> Path:
    """Write a minimal SKILL.md at tmp so benchmark_lib.detect_skill_version resolves."""
    skill = tmp / "SKILL.md"
    skill.write_text(
        f"---\nname: quality-playbook\nmetadata:\n  version: {skill_version}\n---\n",
        encoding="utf-8",
    )
    return tmp


class ReferenceDocsIngestTests(unittest.TestCase):
    def test_empty_reference_docs_yields_empty_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root = _scaffold(Path(d))
            (root / "reference_docs" / "cite").mkdir(parents=True)
            manifest = rdi.ingest(root)
            self.assertEqual(manifest["records"], [])
            self.assertIn("schema_version", manifest)

    def test_cite_file_produces_record_with_tier_1_default(self):
        with tempfile.TemporaryDirectory() as d:
            root = _scaffold(Path(d))
            cite = root / "reference_docs" / "cite"
            cite.mkdir(parents=True)
            (cite / "spec.md").write_text("# Project Spec\n\nFoo bar.\n", encoding="utf-8")
            manifest = rdi.ingest(root)
            self.assertEqual(len(manifest["records"]), 1)
            rec = manifest["records"][0]
            self.assertEqual(rec["source_path"], "reference_docs/cite/spec.md")
            self.assertEqual(rec["tier"], 1)
            self.assertTrue(rec["citation_excerpt"])

    def test_html_tier_marker_upgrades_to_tier_2(self):
        with tempfile.TemporaryDirectory() as d:
            root = _scaffold(Path(d))
            cite = root / "reference_docs" / "cite"
            cite.mkdir(parents=True)
            (cite / "rfc.md").write_text(
                "<!-- qpb-tier: 2 -->\n# External RFC\n\nBody.\n", encoding="utf-8"
            )
            manifest = rdi.ingest(root)
            self.assertEqual(manifest["records"][0]["tier"], 2)

    def test_hash_tier_marker_upgrades_to_tier_2(self):
        with tempfile.TemporaryDirectory() as d:
            root = _scaffold(Path(d))
            cite = root / "reference_docs" / "cite"
            cite.mkdir(parents=True)
            (cite / "rfc.txt").write_text(
                "# qpb-tier: 2\nContent line.\n", encoding="utf-8"
            )
            manifest = rdi.ingest(root)
            self.assertEqual(manifest["records"][0]["tier"], 2)

    def test_top_level_file_is_not_cited(self):
        with tempfile.TemporaryDirectory() as d:
            root = _scaffold(Path(d))
            ref = root / "reference_docs"
            ref.mkdir()
            (ref / "design-notes.md").write_text("Freeform notes.\n", encoding="utf-8")
            manifest = rdi.ingest(root)
            self.assertEqual(manifest["records"], [])
            tier4 = rdi.load_tier4_context(root)
            self.assertEqual(len(tier4), 1)
            self.assertEqual(tier4[0][0], "reference_docs/design-notes.md")

    def test_readme_files_are_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            root = _scaffold(Path(d))
            ref = root / "reference_docs"
            ref.mkdir()
            (ref / "README.md").write_text("adopter-local notes\n", encoding="utf-8")
            (ref / "cite").mkdir()
            (ref / "cite" / "README.md").write_text("cite readme\n", encoding="utf-8")
            manifest = rdi.ingest(root)
            self.assertEqual(manifest["records"], [])
            self.assertEqual(rdi.load_tier4_context(root), [])

    def test_unsupported_extension_rejected_with_hint(self):
        with tempfile.TemporaryDirectory() as d:
            root = _scaffold(Path(d))
            cite = root / "reference_docs" / "cite"
            cite.mkdir(parents=True)
            (cite / "spec.pdf").write_bytes(b"%PDF-1.4\n")
            with self.assertRaises(rdi.IngestError) as ctx:
                rdi.ingest(root)
            self.assertIn("pdftotext", str(ctx.exception))

    def test_tier4_context_sorted_and_returns_all_top_level(self):
        with tempfile.TemporaryDirectory() as d:
            root = _scaffold(Path(d))
            ref = root / "reference_docs"
            (ref / "cite").mkdir(parents=True)
            (ref / "b.md").write_text("b\n", encoding="utf-8")
            (ref / "a.md").write_text("a\n", encoding="utf-8")
            (ref / "cite" / "spec.md").write_text("spec\n", encoding="utf-8")
            paths = [p for p, _ in rdi.load_tier4_context(root)]
            self.assertEqual(paths, [
                "reference_docs/a.md",
                "reference_docs/b.md",
            ])

    def test_manifest_written_to_quality_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root = _scaffold(Path(d))
            cite = root / "reference_docs" / "cite"
            cite.mkdir(parents=True)
            (cite / "spec.md").write_text("spec body\n", encoding="utf-8")
            rdi.ingest(root)
            out = root / "quality" / "formal_docs_manifest.json"
            self.assertTrue(out.is_file())
            manifest = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["records"]), 1)


if __name__ == "__main__":
    unittest.main()
