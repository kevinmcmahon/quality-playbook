"""Tests for repos/stage_formal_docs.py (v1.5.1 Item 1.1)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


def _load_stager():
    """Load the stager module without a package path (it lives under repos/)."""
    here = Path(__file__).resolve().parent.parent.parent / "repos" / "stage_formal_docs.py"
    spec = importlib.util.spec_from_file_location("stage_formal_docs", here)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["stage_formal_docs"] = module
    spec.loader.exec_module(module)
    return module


stager = _load_stager()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


RST_SAMPLE = """\
.. SPDX-License-Identifier: GPL-2.0

.. _virtio:

===============
Virtio on Linux
===============

Introduction
============

Virtio is an open standard that defines a protocol for communication
between drivers and devices. See Chapter 5 (:ref:`Device Types <virtio>`)
of the ``virtio`` spec.

Example code::

	#include <linux/virtio.h>

References
==========

_`[1]` Virtio Spec v1.2:
https://docs.oasis-open.org/virtio/virtio/v1.2/virtio-v1.2.html

.. rubric:: Footnotes

.. [#f1] trailing footnote that should be stripped.
"""

HTML_SAMPLE = """\
<html>
  <head><title>Spec</title><style>body{}</style></head>
  <body>
    <h1>Virtio Specification</h1>
    <p>A device <strong>MUST</strong> reset itself when negotiation fails.</p>
    <script>noise()</script>
    <p>See <a href="/appendix">Appendix A</a>.</p>
  </body>
</html>
"""


class RstConverterTests(unittest.TestCase):
    def test_strips_directives_and_underlines(self) -> None:
        out = stager.convert_rst_to_plaintext(RST_SAMPLE)
        # Directives gone.
        self.assertNotIn("SPDX-License-Identifier", out)
        self.assertNotIn(".. _virtio", out)
        self.assertNotIn(".. rubric::", out)
        self.assertNotIn("[#f1]", out)
        # Section underlines gone but headings preserved.
        self.assertNotIn("====", out)
        self.assertIn("Virtio on Linux", out)
        self.assertIn("Introduction", out)
        # Double colon literal-block opener normalized.
        self.assertIn("Example code:", out)
        self.assertNotIn("Example code::", out)

    def test_inline_markup_stripped(self) -> None:
        out = stager.convert_rst_to_plaintext(
            "Use the ``foo`` helper. See :ref:`bar <bar>` for details.\n"
        )
        self.assertIn("Use the foo helper.", out)
        self.assertIn("See bar for details.", out)
        self.assertNotIn("``", out)
        self.assertNotIn(":ref:", out)

    def test_collapses_blank_runs(self) -> None:
        # 5 consecutive blanks in the source should collapse to at most 2 in
        # the output (the implementation caps blank runs at 2 — 3 newlines).
        out = stager.convert_rst_to_plaintext("para1\n\n\n\n\npara2\n")
        self.assertNotIn("\n\n\n\n", out)
        self.assertIn("para1", out)
        self.assertIn("para2", out)


class HtmlConverterTests(unittest.TestCase):
    def test_strips_tags_and_scripts(self) -> None:
        out = stager.convert_html_to_plaintext(HTML_SAMPLE)
        self.assertIn("Virtio Specification", out)
        self.assertIn("MUST reset itself", out)
        self.assertIn("Appendix A", out)
        self.assertNotIn("<p>", out)
        self.assertNotIn("noise()", out)
        self.assertNotIn("body{}", out)


class StageDirectoryTests(unittest.TestCase):
    def test_converts_rst_and_html_passes_through_md_txt(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "docs_gathered"
            dest = Path(tmp) / "formal_docs"
            _write(source / "virtio.rst", RST_SAMPLE)
            _write(source / "appendix.html", HTML_SAMPLE)
            _write(source / "virtio-spec.md", "# Behavioral contracts\nbody\n")
            _write(source / "plain.txt", "already plaintext\n")

            warn: list = []
            converted, skipped = stager.stage_directory(source, dest, warn=warn)
            self.assertEqual(converted, 4)
            self.assertEqual(skipped, 0)
            self.assertEqual(warn, [])

            self.assertTrue((dest / "virtio.txt").is_file())
            self.assertTrue((dest / "appendix.txt").is_file())
            self.assertTrue((dest / "virtio-spec.md").is_file())
            self.assertTrue((dest / "plain.txt").is_file())

            # RST output no longer has RST directives.
            rst_out = (dest / "virtio.txt").read_text(encoding="utf-8")
            self.assertIn("Virtio on Linux", rst_out)
            self.assertNotIn("SPDX", rst_out)

    def test_skips_pdf_and_other_binary_with_warning(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "docs_gathered"
            dest = Path(tmp) / "formal_docs"
            _write(source / "spec.pdf", "%PDF placeholder\n")
            _write(source / "weird.xyz", "???\n")

            warn: list = []
            converted, skipped = stager.stage_directory(source, dest, warn=warn)
            self.assertEqual(converted, 0)
            self.assertEqual(skipped, 2)
            self.assertFalse((dest / "spec.pdf").exists())
            self.assertTrue(any("spec.pdf" in w for w in warn))
            self.assertTrue(any("weird.xyz" in w for w in warn))

    def test_empty_rst_conversion_warns_and_skips(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "docs_gathered"
            dest = Path(tmp) / "formal_docs"
            # All-directive RST collapses to nothing.
            _write(
                source / "only-toctree.rst",
                ".. toctree::\n   :maxdepth: 1\n\n   foo\n",
            )

            warn: list = []
            converted, skipped = stager.stage_directory(source, dest, warn=warn)
            self.assertEqual(converted, 0)
            self.assertEqual(skipped, 1)
            self.assertFalse((dest / "only-toctree.txt").exists())


class VirtioEndToEndTests(unittest.TestCase):
    """Stage the real virtio docs_gathered/ tree and verify the staging is
    operable with the v1.5.1 sidecar manifest."""

    def test_virtio_staging_produces_expected_tier_assignments(self) -> None:
        from bin import setup_formal_docs as sfd
        from bin import formal_docs_ingest as fdi

        qpb_root = Path(__file__).resolve().parent.parent.parent
        source = qpb_root / "repos" / "docs_gathered" / "virtio"
        if not source.is_dir():
            self.skipTest(f"virtio docs_gathered not available at {source}")

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target = tmp_path / "virtio-test"
            formal = target / "formal_docs"
            # Stage the plaintext.
            converted, _ = stager.stage_directory(source, formal)
            self.assertGreaterEqual(converted, 3)

            # Apply the per-repo manifest via the setup helper.
            manifest = stager._repo_manifest(
                qpb_root / "repos" / "formal_docs_tiers.json", "virtio"
            )
            sfd.setup_sidecars(formal, manifest=manifest)

            # Briefing minimum: these three files must have specific tiers.
            required = {
                "virtio.txt": 1,
                "virtio-spec-behavioral-contracts.md": 1,
                "writing_virtio_drivers.txt": 2,
            }
            for filename, expected_tier in required.items():
                sidecar = formal / (Path(filename).stem + ".meta.json")
                self.assertTrue(sidecar.is_file(), f"missing sidecar for {filename}")
                import json as _json
                payload = _json.loads(sidecar.read_text(encoding="utf-8"))
                self.assertEqual(
                    payload["tier"], expected_tier,
                    f"{filename}: expected tier {expected_tier}, got {payload['tier']}",
                )

            # Ingest must accept the staged tree without modification.
            fake_skill = target / ".github" / "skills"
            fake_skill.mkdir(parents=True)
            (fake_skill.parent.parent / "SKILL.md").write_text(
                "version: 1.4.6\n", encoding="utf-8"
            )
            manifest_path, records = fdi.ingest(target, qpb_root=target)
            self.assertTrue(manifest_path.is_file())
            self.assertGreaterEqual(len(records), 3)


if __name__ == "__main__":
    unittest.main()
