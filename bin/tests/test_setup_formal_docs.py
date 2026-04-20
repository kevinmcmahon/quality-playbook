"""Tests for bin/setup_formal_docs.py (v1.5.1 Item 1.2)."""

from __future__ import annotations

import io
import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable

from bin import setup_formal_docs as sfd


def _touch(path: Path, content: str = "content\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _read_sidecar(doc: Path) -> dict:
    return json.loads(
        doc.with_name(doc.stem + sfd.SIDECAR_SUFFIX).read_text(encoding="utf-8")
    )


def _run(
    formal_docs_dir: Path,
    *,
    interactive: bool = False,
    overwrite: bool = False,
    manifest: dict | None = None,
    unknown_keys: Iterable[str] = (),
    stdin_text: str = "",
    run_timestamp: str | None = None,
) -> tuple[sfd.SetupResult, str]:
    stream_in = io.StringIO(stdin_text)
    stream_out = io.StringIO()
    result = sfd.setup_sidecars(
        formal_docs_dir,
        interactive=interactive,
        overwrite=overwrite,
        manifest=manifest or {},
        unknown_manifest_keys=tuple(unknown_keys),
        stream_in=stream_in,
        stream_out=stream_out,
        run_timestamp=run_timestamp,
    )
    return result, stream_out.getvalue()


class HeuristicTests(unittest.TestCase):
    def test_tier1_tokens(self) -> None:
        for name in (
            "virtio-spec.md",
            "rfc7230.txt",
            "behavioral-contracts.md",
            "http-standard.md",
        ):
            tier, flagged = sfd._heuristic_tier(name)
            self.assertEqual(tier, 1, name)
            self.assertFalse(flagged, name)

    def test_tier2_tokens(self) -> None:
        for name in (
            "programmer-guide.md",
            "howto-quickstart.md",
            "tutorial_basics.txt",
            "example-client.txt",
        ):
            tier, flagged = sfd._heuristic_tier(name)
            self.assertEqual(tier, 2, name)
            self.assertFalse(flagged, name)

    def test_filenames_outside_pattern_list_are_flagged(self) -> None:
        # Per briefing: writing_virtio_drivers.txt is the canonical example of
        # a file that the heuristic can't classify — the per-repo manifest is
        # what pins it to Tier 2. Fall-through must surface as flagged so the
        # operator reviews it.
        tier, flagged = sfd._heuristic_tier("writing_virtio_drivers.txt")
        self.assertEqual(tier, 2)
        self.assertTrue(flagged)

    def test_case_insensitive(self) -> None:
        tier, flagged = sfd._heuristic_tier("VIRTIO-SPEC.MD")
        self.assertEqual(tier, 1)
        self.assertFalse(flagged)
        tier, flagged = sfd._heuristic_tier("Writing_HOWTO_Guide.TXT")
        self.assertEqual(tier, 2)
        self.assertFalse(flagged)

    def test_flagged_default(self) -> None:
        tier, flagged = sfd._heuristic_tier("random-notes.md")
        self.assertEqual(tier, 2)
        self.assertTrue(flagged)


class BackupBehaviorTests(unittest.TestCase):
    def test_existing_sidecar_is_backed_up(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "virtio-spec.md"
            _touch(doc, "# spec\n")
            sidecar = doc.with_name("virtio-spec.meta.json")
            _touch(sidecar, json.dumps({"tier": 2, "note": "hand-authored"}))

            ts = "20260420T140000Z"
            result, _ = _run(root, run_timestamp=ts)

            # Original sidecar has been moved aside.
            backup = root / sfd.BACKUP_DIRNAME / ts / "virtio-spec.meta.json"
            self.assertTrue(backup.is_file(), "backup should exist at timestamped path")
            backed_up_payload = json.loads(backup.read_text(encoding="utf-8"))
            self.assertEqual(backed_up_payload["note"], "hand-authored")

            # Newly written sidecar is present and has only the canonical fields.
            new_payload = _read_sidecar(doc)
            self.assertEqual(new_payload, {"tier": 1})
            self.assertEqual(result.backed_up, 1)

    def test_overwrite_suppresses_backup(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "virtio-spec.md"
            _touch(doc)
            sidecar = doc.with_name("virtio-spec.meta.json")
            _touch(sidecar, json.dumps({"tier": 2}))

            result, _ = _run(root, overwrite=True, run_timestamp="20260420T140000Z")

            # No backup directory was created.
            self.assertFalse((root / sfd.BACKUP_DIRNAME).exists())
            self.assertEqual(result.backed_up, 0)
            self.assertEqual(_read_sidecar(doc)["tier"], 1)

    def test_timestamp_uses_iso8601_basic(self) -> None:
        ts = sfd._backup_timestamp()
        self.assertRegex(ts, r"^\d{8}T\d{6}Z$")


class SummaryTests(unittest.TestCase):
    def test_summary_counts_and_flag_listing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "virtio-spec.md")
            _touch(root / "programmer-guide.md")
            _touch(root / "ambiguous-notes.md")

            result = sfd.setup_sidecars(root, run_timestamp="20260420T140000Z")
            stream_out = io.StringIO()
            sfd._print_summary(result, root, stream_out)
            summary = stream_out.getvalue()

            self.assertEqual(result.generated, 3)
            self.assertEqual(result.flagged, 1)
            self.assertEqual(result.backed_up, 0)
            self.assertIn("3 sidecars generated", summary)
            self.assertIn("0 skipped", summary)
            self.assertIn("1 flagged for review", summary)
            self.assertIn("FLAGGED  ambiguous-notes.md", summary)
            self.assertNotIn("FLAGGED  virtio-spec.md", summary)


class ReadmeAndSidecarSkipTests(unittest.TestCase):
    def test_readme_is_skipped(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "README.md", "# docs readme\n")
            _touch(root / "virtio-spec.md")
            sfd.setup_sidecars(root)
            self.assertFalse((root / "README.meta.json").exists())
            self.assertTrue((root / "virtio-spec.meta.json").is_file())

    def test_sidecar_files_are_not_treated_as_plaintext(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "foo.txt")
            # Pre-existing sidecar looks like `.meta.json`; must not trigger a
            # double-sidecar (foo.meta.meta.json).
            _touch(root / "foo.meta.json", json.dumps({"tier": 1}))
            sfd.setup_sidecars(root, overwrite=True)
            self.assertFalse((root / "foo.meta.meta.json").exists())

    def test_backup_dir_contents_not_rescanned(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "virtio-spec.md")
            _touch(root / ".sidecar_backups" / "20260101T000000Z" / "older.md")
            result = sfd.setup_sidecars(root)
            self.assertEqual(len(result.outcomes), 1)
            self.assertEqual(result.outcomes[0].path.name, "virtio-spec.md")


class InteractiveTests(unittest.TestCase):
    def test_interactive_accepts_default(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "virtio-spec.md")
            # Empty line = accept default.
            result, _ = _run(root, interactive=True, stdin_text="\n")
            self.assertEqual(_read_sidecar(root / "virtio-spec.md")["tier"], 1)
            self.assertEqual(result.skipped, 0)

    def test_interactive_override(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "virtio-spec.md")
            # Override heuristic Tier 1 → Tier 2.
            result, _ = _run(root, interactive=True, stdin_text="2\n")
            self.assertEqual(_read_sidecar(root / "virtio-spec.md")["tier"], 2)

    def test_interactive_skip(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "virtio-spec.md")
            result, _ = _run(root, interactive=True, stdin_text="s\n")
            self.assertFalse((root / "virtio-spec.meta.json").exists())
            self.assertEqual(result.skipped, 1)
            self.assertEqual(result.generated, 0)

    def test_interactive_eof_is_skip_not_crash(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "virtio-spec.md")
            # Empty stdin: StringIO readline returns "" immediately.
            result, _ = _run(root, interactive=True, stdin_text="")
            self.assertEqual(result.skipped, 1)
            self.assertFalse((root / "virtio-spec.meta.json").exists())


class ManifestTests(unittest.TestCase):
    def test_manifest_overrides_heuristic(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Heuristic would label this Tier 2 (guide). Manifest forces Tier 1.
            _touch(root / "writing_virtio_drivers.txt")
            manifest = {"writing_virtio_drivers.txt": {"tier": 1, "version": "kernel-6.0"}}
            result, _ = _run(root, manifest=manifest)
            payload = _read_sidecar(root / "writing_virtio_drivers.txt")
            self.assertEqual(payload["tier"], 1)
            self.assertEqual(payload["version"], "kernel-6.0")
            # Manifest-sourced sidecars are never flagged.
            self.assertEqual(result.flagged, 0)

    def test_manifest_accepts_bare_int_shape(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "random-notes.md")
            # `_load_manifest` is what validates the two accepted shapes.
            manifest_path = root / "manifest.json"
            _touch(manifest_path, json.dumps({"random-notes.md": 1}))
            loaded = sfd._load_manifest(manifest_path)
            self.assertEqual(loaded, {"random-notes.md": {"tier": 1}})

    def test_manifest_unknown_filename_warns(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "virtio-spec.md")
            manifest = {"not-present.txt": {"tier": 1}}
            # Simulate the CLI's unknown-key detection.
            unknown = sfd._resolve_unknown_manifest_keys(manifest, root)
            self.assertEqual(unknown, ["not-present.txt"])
            result, output = _run(root, manifest=manifest, unknown_keys=unknown)
            # Warning was printed; run still succeeded.
            self.assertIn("WARN: manifest entry 'not-present.txt'", output)
            self.assertEqual(result.generated, 1)

    def test_manifest_invalid_tier_raises(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "bad.json"
            _touch(manifest_path, json.dumps({"foo.md": {"tier": 3}}))
            with self.assertRaises(ValueError):
                sfd._load_manifest(manifest_path)

    def test_manifest_non_object_raises(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / "bad.json"
            _touch(bad, json.dumps([1, 2, 3]))
            with self.assertRaises(ValueError):
                sfd._load_manifest(bad)


class IntegrationWithIngestTests(unittest.TestCase):
    """The sidecars this helper writes must ingest through
    bin/formal_docs_ingest.py unmodified."""

    def test_generated_sidecars_accepted_by_ingest(self) -> None:
        from bin import formal_docs_ingest as fdi

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            qpb_root = tmp_path / "qpb"
            qpb_root.mkdir()
            _touch(qpb_root / "SKILL.md", "version: 1.5.0\n")

            target = tmp_path / "target"
            formal = target / "formal_docs"
            formal.mkdir(parents=True)
            _touch(formal / "virtio-spec.md", "# behavioral contract\n")
            _touch(formal / "writing_virtio_drivers.txt", "guide body\n")

            manifest = {"writing_virtio_drivers.txt": {"tier": 2}}
            sfd.setup_sidecars(formal, manifest=manifest)

            manifest_path, records = fdi.ingest(target, qpb_root=qpb_root)
            by_path = {r["source_path"]: r for r in records}
            self.assertEqual(
                by_path["formal_docs/virtio-spec.md"]["tier"], 1
            )
            self.assertEqual(
                by_path["formal_docs/writing_virtio_drivers.txt"]["tier"], 2
            )


class CliExitCodeTests(unittest.TestCase):
    def test_exit_zero_when_no_flags(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "virtio-spec.md")
            exit_code = sfd.main([str(root)])
            self.assertEqual(exit_code, 0)

    def test_exit_one_when_flagged(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "random-notes.md")
            exit_code = sfd.main([str(root)])
            self.assertEqual(exit_code, 1)

    def test_exit_two_on_missing_directory(self) -> None:
        with TemporaryDirectory() as tmp:
            missing = Path(tmp) / "no-such-dir"
            exit_code = sfd.main([str(missing)])
            self.assertEqual(exit_code, 2)

    def test_exit_two_on_bad_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "virtio-spec.md")
            bad = root / "bad.json"
            _touch(bad, "not json {")
            exit_code = sfd.main([str(root), "--manifest", str(bad)])
            self.assertEqual(exit_code, 2)


class SidecarContentTests(unittest.TestCase):
    def test_sidecar_uses_two_space_indent_and_trailing_newline(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "virtio-spec.md")
            sfd.setup_sidecars(root)
            raw = (root / "virtio-spec.meta.json").read_text(encoding="utf-8")
            self.assertTrue(raw.endswith("\n"))
            self.assertIn('  "tier": 1', raw)


if __name__ == "__main__":
    unittest.main()
