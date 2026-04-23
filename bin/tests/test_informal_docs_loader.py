"""Tests for bin/informal_docs_loader.py."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin import informal_docs_loader as idl


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


class InformalDocsLoaderTests(unittest.TestCase):
    def test_missing_directory_returns_empty_list(self) -> None:
        with TemporaryDirectory() as tmp:
            result = idl.load_informal_docs(Path(tmp))
            self.assertEqual(result, [])

    def test_loads_txt_and_md_sorted(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "informal_docs" / "zebra.md", "# Z")
            _write(root / "informal_docs" / "alpha.txt", "alpha body")
            _write(root / "informal_docs" / "mid" / "nested.md", "nested")
            result = idl.load_informal_docs(root)
            paths = [r for r, _ in result]
            # Sorted by relative path, directory traversal included.
            self.assertEqual(
                paths,
                [
                    "informal_docs/alpha.txt",
                    "informal_docs/mid/nested.md",
                    "informal_docs/zebra.md",
                ],
            )
            contents = dict(result)
            self.assertEqual(contents["informal_docs/alpha.txt"], "alpha body")
            self.assertEqual(contents["informal_docs/zebra.md"], "# Z")
            self.assertEqual(contents["informal_docs/mid/nested.md"], "nested")

    def test_rejects_pdf(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_bytes(root / "informal_docs" / "note.pdf", b"%PDF")
            with self.assertRaises(idl.InformalDocsError) as ctx:
                idl.load_informal_docs(root)
            self.assertIn("note.pdf", str(ctx.exception))
            self.assertIn("pdftotext", str(ctx.exception))

    def test_rejects_docx(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_bytes(root / "informal_docs" / "note.docx", b"PK")
            with self.assertRaises(idl.InformalDocsError) as ctx:
                idl.load_informal_docs(root)
            self.assertIn("pandoc", str(ctx.exception))

    def test_skips_readme_md(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "informal_docs" / "README.md", "folder-level doc")
            _write(root / "informal_docs" / "chat.txt", "content")
            result = idl.load_informal_docs(root)
            paths = [r for r, _ in result]
            self.assertEqual(paths, ["informal_docs/chat.txt"])

    def test_read_only_no_writes(self) -> None:
        """Loader must not mutate informal_docs or write any files under it."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "informal_docs" / "chat.txt", "content")
            before = sorted((root / "informal_docs").iterdir())
            before_mtimes = {p: p.stat().st_mtime_ns for p in before}
            idl.load_informal_docs(root)
            after = sorted((root / "informal_docs").iterdir())
            self.assertEqual(before, after)
            for p in after:
                self.assertEqual(p.stat().st_mtime_ns, before_mtimes[p], f"{p} mtime changed")

    def test_invalid_utf8_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_bytes(root / "informal_docs" / "broken.txt", b"valid\n\xff\xfeinvalid\n")
            with self.assertRaises(idl.InformalDocsError) as ctx:
                idl.load_informal_docs(root)
            self.assertIn("UTF-8", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
