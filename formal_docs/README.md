# formal_docs/

**Tier 1 and Tier 2 plaintext primary sources** — authoritative documentation
that Quality Playbook v1.5.0 cites when deriving requirements and filing bugs.
Files in this folder feed `bin/formal_docs_ingest.py`, which walks the
directory at the start of Phase 1 and writes
`quality/formal_docs_manifest.json` (one `FORMAL_DOC` record per file, per
`schemas.md` §4).

## What to put here

- **Tier 1** — your project's own formal spec (design doc, protocol
  definition, published API contract). Authoritative intent — wins over
  Tier 2 when the two conflict.
- **Tier 2** — external formal standards you rely on (RFC, W3C/ISO
  standards, third-party published API contracts).

Tier semantics are defined in `schemas.md` §3.1. Tier 3/4/5 sources
(code, AI chats, inferred behavior) do NOT go here — Tier 4 belongs in
`informal_docs/`; Tier 3/5 needs no folder (it lives in source code and
inferred prose).

## Plaintext only

Ingest accepts `.txt` and `.md` files only (`schemas.md` §2). PDFs,
DOCX, HTML, and other formatted documents are rejected with an
actionable conversion hint. Convert **outside** the playbook and commit
the plaintext:

- `pdftotext spec-v1.1.pdf spec-v1.1.txt`
- `pandoc -t plain spec.docx -o spec.txt`
- `lynx -dump https://example.org/spec.html > spec.txt`

The skill is stdlib-only Python — it does not parse binary or marked-up
formats, and it will not try. A clean `pdftotext` output is more
reliable than any library we could ship.

## Sidecar convention

Every `<name>.txt` or `<name>.md` here needs a companion
`<name>.meta.json` sidecar. The sidecar carries the per-document
metadata that the `FORMAL_DOC` schema requires:

```json
{
  "tier": 1,
  "version": "2.0",
  "date": "2024-06-15",
  "url": "https://example.org/spec-v2.0.pdf",
  "retrieved": "2026-04-19"
}
```

Only `tier` is required (integer `1` or `2` — `FORMAL_DOC` records are
Tier 1/2 only). `version`, `date`, `url`, and `retrieved` are optional
but recommended. Ingest computes `source_path`, `document_sha256`, and
`bytes` from the file itself — do not put them in the sidecar.

See `schemas.md` §4 for the full `FORMAL_DOC` field list and §4.1 for
field-by-field constraints.

## Stem collisions

Two plaintext files sharing a stem (e.g., `virtio.txt` and `virtio.md`)
would share one sidecar and fail ingest. Rename one of them before
re-running.

## Citation implications

When Phase 1 derives a requirement at Tier 1 or Tier 2, the REQ record
carries a `citation` block pointing back at one of these documents
(`schemas.md` §5). The `citation_excerpt` is a deterministic text slice
produced at ingest time by `bin/citation_verifier.py` per the algorithm
in `schemas.md` §5.4 (with section resolution per §5.5). The excerpt is
byte-verified by `quality_gate.py` at gate time — hand-authored or
paraphrased excerpts are rejected (schemas.md §10 invariant #11).

The LLM does not write citation excerpts by hand and does not shell out
to `citation_verifier` directly — excerpts are a product of the ingest
pipeline and are consumed from `quality/formal_docs_manifest.json`.

## What does not go here

- AI chat transcripts, retrospectives, design notes, exploratory
  writeups — those are Tier 4 context for `informal_docs/`.
- Original binary/formatted sources — convert first, commit plaintext.
- Scratch documentation, partial thoughts, or anything you would not
  cite in a bug report.
- Code excerpts — Tier 3 authority is the source tree itself; REQs
  reference `file:line` in their `description` rather than citing from
  this folder.

Keep this folder clean. Every file here should be something you could
hand a maintainer as the basis for a `spec-fix` or `upstream-spec-issue`
disposition. If you would not cite it in a bug report, it probably
belongs in `informal_docs/` instead.
