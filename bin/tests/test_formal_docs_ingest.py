"""Tests for bin/formal_docs_ingest.py."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from bin import formal_docs_ingest as fdi


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


class _IngestScaffold:
    """Helper for tests: sets up a fake QPB root + target repo in a tempdir."""

    def __init__(self, tmp: Path, qpb_version: str = "9.8.7") -> None:
        self.qpb_root = tmp / "qpb"
        self.target = tmp / "target"
        self.qpb_root.mkdir(parents=True)
        self.target.mkdir(parents=True)
        _write(self.qpb_root / "SKILL.md", f"version: {qpb_version}\n")
        self.qpb_version = qpb_version

    def run(self):
        return fdi.ingest(self.target, qpb_root=self.qpb_root)


class FormalDocsIngestTests(unittest.TestCase):
    def test_happy_path_two_documents(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp), qpb_version="1.5.1")
            doc_a = s.target / "formal_docs" / "alpha.txt"
            doc_b = s.target / "formal_docs" / "beta.md"
            _write(doc_a, "alpha content\nanother line\n")
            _write(doc_b, "# Beta\n\nSome markdown.\n")
            _write(
                doc_a.with_name("alpha.meta.json"),
                json.dumps({"tier": 1, "version": "0.1", "date": "2026-01-01"}),
            )
            _write(
                doc_b.with_name("beta.meta.json"),
                json.dumps({"tier": 2, "url": "https://example.com/beta"}),
            )
            manifest_path, records = s.run()

            # Manifest exists and parses.
            raw = manifest_path.read_text(encoding="utf-8")
            manifest = json.loads(raw)

            # Wrapper per §1.6.
            self.assertEqual(manifest["schema_version"], "1.5.1")
            self.assertIn("generated_at", manifest)
            # ISO 8601 with Z suffix.
            self.assertTrue(
                re.fullmatch(
                    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
                    manifest["generated_at"],
                ),
                f"bad generated_at: {manifest['generated_at']}",
            )
            # Parses through datetime.
            ts = manifest["generated_at"].replace("Z", "+00:00")
            datetime.fromisoformat(ts)

            self.assertEqual(len(manifest["records"]), 2)

            # Records sorted by path walk order (alphabetical).
            by_path = {r["source_path"]: r for r in manifest["records"]}

            alpha = by_path["formal_docs/alpha.txt"]
            self.assertEqual(alpha["tier"], 1)
            self.assertEqual(alpha["version"], "0.1")
            self.assertEqual(alpha["date"], "2026-01-01")
            self.assertNotIn("url", alpha)  # optional, not provided
            # Hash is recomputable.
            expected_sha = hashlib.sha256(doc_a.read_bytes()).hexdigest()
            self.assertEqual(alpha["document_sha256"], expected_sha)
            self.assertEqual(len(alpha["document_sha256"]), 64)
            self.assertEqual(alpha["document_sha256"], alpha["document_sha256"].lower())
            self.assertEqual(alpha["bytes"], doc_a.stat().st_size)

            beta = by_path["formal_docs/beta.md"]
            self.assertEqual(beta["tier"], 2)
            self.assertEqual(beta["url"], "https://example.com/beta")
            self.assertNotIn("version", beta)

            # Records matches function return value.
            self.assertEqual(records, manifest["records"])

    def test_rejects_pdf_with_pdftotext_guidance(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            _write_bytes(s.target / "formal_docs" / "foo.pdf", b"%PDF-1.4")
            with self.assertRaises(fdi.IngestError) as ctx:
                s.run()
            msg = str(ctx.exception)
            self.assertIn("foo.pdf", msg)
            self.assertIn("unsupported extension", msg)
            self.assertIn("pdftotext", msg)

    def test_rejects_docx_with_pandoc_guidance(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            _write_bytes(s.target / "formal_docs" / "foo.docx", b"PK")
            with self.assertRaises(fdi.IngestError) as ctx:
                s.run()
            msg = str(ctx.exception)
            self.assertIn("foo.docx", msg)
            self.assertIn("pandoc -t plain", msg)

    def test_rejects_html_with_pandoc_or_lynx_guidance(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            _write_bytes(s.target / "formal_docs" / "foo.html", b"<html>")
            with self.assertRaises(fdi.IngestError) as ctx:
                s.run()
            msg = str(ctx.exception)
            self.assertIn("foo.html", msg)
            self.assertIn("pandoc -t plain", msg)
            self.assertIn("lynx -dump", msg)

    def test_rejects_unknown_extension_with_default_guidance(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            _write_bytes(s.target / "formal_docs" / "foo.xyz", b"junk")
            with self.assertRaises(fdi.IngestError) as ctx:
                s.run()
            self.assertIn("foo.xyz", str(ctx.exception))
            self.assertIn("pandoc", str(ctx.exception))

    def test_missing_sidecar_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            _write(s.target / "formal_docs" / "alpha.txt", "body\n")
            with self.assertRaises(fdi.IngestError) as ctx:
                s.run()
            msg = str(ctx.exception)
            self.assertIn("missing sidecar", msg)
            self.assertIn("alpha.meta.json", msg)
            self.assertIn("schemas.md", msg)

    def test_sidecar_missing_tier_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            doc = s.target / "formal_docs" / "alpha.txt"
            _write(doc, "body\n")
            _write(doc.with_name("alpha.meta.json"), json.dumps({"version": "1.0"}))
            with self.assertRaises(fdi.IngestError) as ctx:
                s.run()
            self.assertIn("'tier'", str(ctx.exception))

    def test_sidecar_tier_out_of_range_fails(self) -> None:
        for bad_tier in (0, 3, 4, 5, 6):
            with self.subTest(tier=bad_tier):
                with TemporaryDirectory() as tmp:
                    s = _IngestScaffold(Path(tmp))
                    doc = s.target / "formal_docs" / "alpha.txt"
                    _write(doc, "body\n")
                    _write(
                        doc.with_name("alpha.meta.json"),
                        json.dumps({"tier": bad_tier}),
                    )
                    with self.assertRaises(fdi.IngestError) as ctx:
                        s.run()
                    self.assertIn("Tier 1/2 only", str(ctx.exception))

    def test_sidecar_tier_non_integer_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            doc = s.target / "formal_docs" / "alpha.txt"
            _write(doc, "body\n")
            _write(doc.with_name("alpha.meta.json"), json.dumps({"tier": "1"}))
            with self.assertRaises(fdi.IngestError) as ctx:
                s.run()
            self.assertIn("integer 1 or 2", str(ctx.exception))

    def test_sidecar_bool_rejected_as_tier(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            doc = s.target / "formal_docs" / "alpha.txt"
            _write(doc, "body\n")
            _write(doc.with_name("alpha.meta.json"), json.dumps({"tier": True}))
            with self.assertRaises(fdi.IngestError) as ctx:
                s.run()
            self.assertIn("integer", str(ctx.exception))

    def test_sidecar_invalid_json_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            doc = s.target / "formal_docs" / "alpha.txt"
            _write(doc, "body\n")
            _write(doc.with_name("alpha.meta.json"), "{not json}")
            with self.assertRaises(fdi.IngestError) as ctx:
                s.run()
            self.assertIn("invalid JSON", str(ctx.exception))

    def test_sidecar_non_object_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            doc = s.target / "formal_docs" / "alpha.txt"
            _write(doc, "body\n")
            _write(doc.with_name("alpha.meta.json"), "[1, 2, 3]")
            with self.assertRaises(fdi.IngestError) as ctx:
                s.run()
            self.assertIn("JSON object", str(ctx.exception))

    def test_sidecar_wrong_optional_type_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            doc = s.target / "formal_docs" / "alpha.txt"
            _write(doc, "body\n")
            _write(
                doc.with_name("alpha.meta.json"),
                json.dumps({"tier": 1, "version": 42}),
            )
            with self.assertRaises(fdi.IngestError) as ctx:
                s.run()
            self.assertIn("'version' must be a string", str(ctx.exception))

    def test_case_fold_collision_rejected(self) -> None:
        """Two files differing only in case are flagged as a uniqueness violation."""
        # Simulate by passing two records through the uniqueness check via a
        # custom walk. On a case-sensitive filesystem we can have both files;
        # on case-insensitive, only one will exist. We test by calling the
        # module function with both names present on disk when possible; if
        # the OS refuses, we assert the check path directly.
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            doc_a = s.target / "formal_docs" / "Alpha.txt"
            _write(doc_a, "one\n")
            _write(doc_a.with_name("Alpha.meta.json"), json.dumps({"tier": 1}))
            try:
                doc_b = s.target / "formal_docs" / "alpha.txt"
                _write(doc_b, "two\n")
                _write(doc_b.with_name("alpha.meta.json"), json.dumps({"tier": 1}))
            except OSError:
                self.skipTest("filesystem does not allow distinct-case siblings")
            # Re-read after writing — on case-insensitive FS the two writes
            # collapsed to one file, and we can't exercise the uniqueness path.
            same_dir = sorted(p.name for p in (s.target / "formal_docs").iterdir())
            has_distinct = (
                "Alpha.txt" in same_dir
                and "alpha.txt" in same_dir
            )
            if not has_distinct:
                self.skipTest("case-insensitive filesystem collapsed siblings")
            with self.assertRaises(fdi.IngestError) as ctx:
                s.run()
            self.assertIn("uniqueness violation", str(ctx.exception))

    def test_manifest_wrapper_round_trip(self) -> None:
        """Wrapper keys match §1.6 and JSON round-trips cleanly."""
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp), qpb_version="1.5.1")
            doc = s.target / "formal_docs" / "alpha.txt"
            _write(doc, "body\n")
            _write(doc.with_name("alpha.meta.json"), json.dumps({"tier": 2}))
            manifest_path, _ = s.run()
            parsed = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(set(parsed.keys()), {"schema_version", "generated_at", "records"})
            self.assertIsInstance(parsed["records"], list)

    def test_skips_readme_md(self) -> None:
        """README.md under formal_docs/ is skipped (no sidecar needed, no record produced)."""
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            _write(s.target / "formal_docs" / "README.md", "# informational")
            doc = s.target / "formal_docs" / "alpha.txt"
            _write(doc, "body\n")
            _write(doc.with_name("alpha.meta.json"), json.dumps({"tier": 2}))
            _, records = s.run()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["source_path"], "formal_docs/alpha.txt")

    def test_absent_formal_docs_directory_produces_empty_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            manifest_path, records = s.run()
            self.assertEqual(records, [])
            parsed = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["records"], [])

    def test_stem_collision_between_txt_and_md_fails(self) -> None:
        """foo.txt and foo.md in the same directory would share foo.meta.json."""
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            _write(s.target / "formal_docs" / "foo.txt", "txt body\n")
            _write(s.target / "formal_docs" / "foo.md", "md body\n")
            _write(
                s.target / "formal_docs" / "foo.meta.json",
                json.dumps({"tier": 1}),
            )
            with self.assertRaises(fdi.IngestError) as ctx:
                s.run()
            self.assertIn("share sidecar", str(ctx.exception))

    def test_cli_happy_path(self) -> None:
        """`python -m bin.formal_docs_ingest` prints the expected summary on success."""
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp), qpb_version="1.5.1")
            doc = s.target / "formal_docs" / "alpha.txt"
            _write(doc, "body\n")
            _write(doc.with_name("alpha.meta.json"), json.dumps({"tier": 2}))
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                exit_code = fdi.main([
                    str(s.target),
                    "--qpb-root", str(s.qpb_root),
                ])
            self.assertEqual(exit_code, 0)
            self.assertIn("Ingested 1 FORMAL_DOC records", buf.getvalue())
            self.assertIn("formal_docs_manifest.json", buf.getvalue())

    def test_cli_missing_target_dir_exits_2(self) -> None:
        exit_code = fdi.main(["/nonexistent/path/that/should/not/exist/ever"])
        self.assertEqual(exit_code, 2)

    def test_cli_reports_ingest_error_with_exit_1(self) -> None:
        with TemporaryDirectory() as tmp:
            s = _IngestScaffold(Path(tmp))
            _write_bytes(s.target / "formal_docs" / "foo.pdf", b"junk")
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                exit_code = fdi.main([str(s.target), "--qpb-root", str(s.qpb_root)])
            self.assertEqual(exit_code, 1)
            self.assertIn("pdftotext", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
