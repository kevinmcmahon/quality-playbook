"""Phase 2 integration test — end-to-end ingest + extraction on a small fixture.

Runs formal_docs_ingest.py against `bin/tests/fixtures/phase2_virtio_mini/`
and asserts that the resulting manifest matches the expected FORMAL_DOC
shape, and that citation_verifier.extract_excerpt returns a byte-equal
excerpt for the known (section="2.4") anchor.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bin import citation_verifier as cv
from bin import formal_docs_ingest as fdi


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "phase2_virtio_mini"

EXPECTED_SECTION_24_EXCERPT = (
    "2.4 Device initialization\n"
    "The driver MUST perform the following steps, in order, before the\n"
    "device is considered operational. Each step has specific precondition\n"
    "and failure-recovery semantics which the driver MUST honor.\n"
    "On failure of VIRTIO_F_VERSION_1 feature negotiation, the device\n"
    "MUST reset itself and MUST NOT accept further driver writes until\n"
    "RESET has completed."
)


class Phase2IntegrationTests(unittest.TestCase):
    def _copy_fixture_to_tmp(self, tmp: Path) -> Path:
        """Clone the on-disk fixture into a tempdir so tests don't mutate it."""
        target = tmp / "target"
        shutil.copytree(FIXTURE_DIR, target)
        return target

    def _write_skill_md(self, tmp: Path, version: str) -> Path:
        qpb_root = tmp / "qpb"
        qpb_root.mkdir()
        (qpb_root / "SKILL.md").write_text(f"version: {version}\n", encoding="utf-8")
        return qpb_root

    def test_ingest_then_extract_matches_expected_excerpt(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target = self._copy_fixture_to_tmp(tmp_path)
            qpb_root = self._write_skill_md(tmp_path, "1.5.1")

            manifest_path, records = fdi.ingest(target, qpb_root=qpb_root)

            # Exactly one FORMAL_DOC record.
            self.assertEqual(len(records), 1)
            rec = records[0]

            # Schema-compliant field set.
            self.assertEqual(rec["source_path"], "formal_docs/virtio-excerpt.txt")
            self.assertEqual(rec["tier"], 2)
            self.assertEqual(rec["version"], "1.1-phase2-fixture")
            self.assertEqual(rec["date"], "2026-04-19")
            self.assertEqual(rec["url"], "https://example.test/phase2-fixture")
            self.assertEqual(rec["retrieved"], "2026-04-19")

            # SHA is the raw-bytes SHA-256 of the file.
            doc_path = target / "formal_docs" / "virtio-excerpt.txt"
            expected_sha = hashlib.sha256(doc_path.read_bytes()).hexdigest()
            self.assertEqual(rec["document_sha256"], expected_sha)
            # 64 lowercase hex chars.
            self.assertEqual(len(rec["document_sha256"]), 64)
            self.assertTrue(
                all(c in "0123456789abcdef" for c in rec["document_sha256"]),
                "SHA must be lowercase hex only",
            )

            # Bytes count matches file size.
            self.assertEqual(rec["bytes"], doc_path.stat().st_size)

            # Manifest file parses and wrapper matches §1.6.
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(set(manifest.keys()), {"schema_version", "generated_at", "records"})
            self.assertEqual(manifest["schema_version"], "1.5.1")
            self.assertEqual(manifest["records"], records)

            # §5.4 extraction: section="2.4" returns the locked-down excerpt.
            extracted = cv.extract_excerpt(
                doc_path.read_bytes(),
                ".txt",
                "2.4",
                None,
            )
            self.assertEqual(extracted, EXPECTED_SECTION_24_EXCERPT)

            # verify_citation against the real record yields ok=True and the
            # same excerpt.
            result = cv.verify_citation(
                {
                    "document": "formal_docs/virtio-excerpt.txt",
                    "document_sha256": expected_sha,
                    "section": "2.4",
                },
                rec,
                target,
            )
            self.assertTrue(result.ok, result.error_message)
            self.assertEqual(result.excerpt, EXPECTED_SECTION_24_EXCERPT)
            self.assertEqual(result.warnings, ())

    def test_second_ingest_is_idempotent(self) -> None:
        """Re-running ingest against the same fixture produces identical records."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target = self._copy_fixture_to_tmp(tmp_path)
            qpb_root = self._write_skill_md(tmp_path, "1.5.1")

            _, first = fdi.ingest(target, qpb_root=qpb_root)
            _, second = fdi.ingest(target, qpb_root=qpb_root)
            # records list is identical across runs (contents-wise).
            self.assertEqual(first, second)

    def test_extract_works_against_checked_in_fixture_directly(self) -> None:
        """Runs extraction on the fixture in place — no tempdir, no ingest.

        This guards against bit-rot on the fixture file (e.g., someone hand-edits
        the fixture and breaks the expected excerpt without updating the test).
        """
        doc_bytes = (FIXTURE_DIR / "formal_docs" / "virtio-excerpt.txt").read_bytes()
        self.assertEqual(
            cv.extract_excerpt(doc_bytes, ".txt", "2.4", None),
            EXPECTED_SECTION_24_EXCERPT,
        )


if __name__ == "__main__":
    unittest.main()
