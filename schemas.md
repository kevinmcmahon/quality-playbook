> Quality Playbook v1.5.0 — Data Contract (`schemas.md`)
> Versioned with the playbook skill. Do not edit per-run.

# Quality Playbook Data Schemas

This file defines the **static data contract** for every structured record the
Quality Playbook produces or consumes: `FORMAL_DOC`, `REQ`, `UC`, `BUG`, and the
embedded `citation` block, plus the enums that constrain their fields.

It ships alongside `SKILL.md` and is versioned with the playbook itself. It is
NOT generated per run. Two runs of the same playbook version against the same
project must agree on record shape — that invariance is what lets the quality
gate validate artifacts mechanically instead of asking an LLM whether the output
"looks right." Schema changes are breaking changes and must bump the playbook
minor version.

Protocols — *how* to produce and validate records at each phase — live inline in
`SKILL.md` where they are used. This file defines *what the records look like*,
nothing more. If you find yourself describing a process here, move it to
`SKILL.md`.

---

## 1. Scope and Design Notes

### 1.1 What `schemas.md` covers

- Record shapes for `FORMAL_DOC`, `REQ`, `UC`, `BUG`.
- The embedded `citation` block used by Tier 1/2 requirements.
- Enums: `tier`, `disposition`, `severity`, `fix_type`, `verdict`.
- The list of supported plaintext extensions for `formal_docs/` and
  `informal_docs/`.

### 1.2 What `schemas.md` does NOT cover

- On-disk file layout, directory conventions, run archival policy — see the
  v1.5.0 design doc and `SKILL.md`.
- Phase-by-phase prompts or review protocols — `SKILL.md`.
- Gate check sequencing — `SKILL.md` and `quality_gate.py`.

### 1.3 Serialization format

The playbook maintains two parallel renderings of the same underlying records:

1. **Machine-readable JSON manifests** — canonical source of truth for the
   gate. Examples: `quality/formal_docs_manifest.json`,
   `quality/requirements_manifest.json`, `quality/use_cases_manifest.json`,
   `quality/bugs_manifest.json`. Validated field-by-field by
   `quality_gate.py` using stdlib `json` and explicit checks (no
   `jsonschema`). Each top-level manifest is a JSON object:

   ```json
   {
     "schema_version": "1.5.0",
     "generated_at": "2026-04-19T14:30:22Z",
     "records": [
       { "id": "REQ-001", "title": "...", "tier": 3, "functional_section": "..." }
     ]
   }
   ```

2. **Human-readable markdown artifacts** — `quality/REQUIREMENTS.md`,
   `quality/USE_CASES.md`, `quality/BUGS.md`. Rendered from the manifests by
   the phase scripts so humans can read narrative prose with full context.
   The gate does NOT parse these markdown files structurally — they are
   presentation, the manifests are contract.

Both renderings MUST stay in sync. A phase script that writes to one without
updating the other is a bug.

### 1.4 Stdlib-only constraint

Every validator that consumes these records must run on stock Python 3 with no
`pip install` and no virtualenv — see the "Stdlib-Only Python" section of the
v1.5.0 design doc. Concretely: manifests are JSON (`json` module), hashes are
computed with `hashlib`, dates are ISO 8601 strings parsed with `datetime`. No
`PyYAML`, no `jsonschema`, no external HTTP. That rules out YAML frontmatter in
manifests even where it would read more nicely.

### 1.5 Field conventions

- Field names are `lower_snake_case`.
- Optional fields may be omitted from the JSON object OR present as JSON
  `null` — validators MUST accept both forms.
- Required fields must be present and non-null. Empty strings are not a valid
  substitute for `null`.
- Array fields default to `[]`, not `null`, when empty.
- All timestamps are ISO 8601 with explicit timezone. Prefer `Z` for UTC.
- Record IDs use fixed prefixes with a zero-padded sequence:
  - `REQ-NNN` (three digits, e.g. `REQ-017`)
  - `UC-NN` (two digits)
  - `BUG-NNN` (three digits)
  - `FORMAL_DOC` records have no synthetic ID — they are identified by
    `source_path` (see §4).

---

## 2. Supported Plaintext Extensions

`formal_docs/` and `informal_docs/` accept plaintext files only. This list is
authoritative; ingest rejects anything not listed.

| Extension | Notes                                                       |
|-----------|-------------------------------------------------------------|
| `.txt`    | Plain UTF-8 text. Preferred for spec excerpts from PDF.     |
| `.md`     | CommonMark-ish Markdown. Allowed for spec bodies and notes. |

Common extensions that are **deliberately excluded** and will fail ingest:

- `.pdf` — binary, no stdlib parser. Convert outside the playbook
  (`pdftotext virtio-v1.1.pdf virtio-v1.1.txt`) and commit the `.txt`.
- `.docx`, `.doc`, `.rtf` — office formats. Export to `.txt` or `.md`.
- `.html`, `.htm` — markup noise interferes with line-number citations. If
  HTML is the only source, run a text-mode converter (`pandoc -t plain`,
  `lynx -dump`) and commit the plaintext.
- `.odt`, `.epub`, and other formatted documents — same policy.

Extending the list: a benchmark project that legitimately needs another
plaintext format may propose it in a PR that (a) adds the extension here,
(b) updates `formal_docs_ingest.py` accordingly, and (c) adds a fixture
exercising it. Don't add extensions speculatively.

**Why this matters:** the citation gate reads the raw bytes of the plaintext
file and resolves `section`, `line`, and `page` references directly against
it. A binary or heavily-marked-up file would require a parser, and any
parser we ship pulls in a dependency or breaks the stdlib-only constraint.

---

## 3. Enums

All enum values are case-sensitive string literals. Validators compare with
`==`, not `lower()`.

### 3.1 `tier` — authority of the source behind a requirement

| Value | Meaning                                                               |
|-------|-----------------------------------------------------------------------|
| `1`   | Project's own formal spec. Highest authority.                         |
| `2`   | External formal standard — RFC, W3C, ISO, published API contract, etc.|
| `3`   | Source-of-truth code when no formal spec exists; the code IS the spec.|
| `4`   | Informal documentation — AI chats, design notes, scratch writeups.    |
| `5`   | Inferred from code behavior with no documentation of any kind behind it.|

Stored as a JSON **integer** (`1`), not a string (`"1"`).

**Conflict rule.** When a Tier 1 claim and a Tier 2 claim contradict each other,
Tier 1 wins. A project's own documented deviation from an external standard is
authoritative intent, not a defect.

**Distribution is a metric, not a gate.** A project with 0 Tier 1/2
requirements is valid — the run degrades gracefully into a Spec Gap
Analyzer and the meta-finding "0 Tier 1/2 requirements" is reported.

### 3.2 `disposition` — how a BUG should be resolved

| Value                  | Meaning                                                                                   |
|------------------------|-------------------------------------------------------------------------------------------|
| `code-fix`             | The divergence is real and the code should change.                                        |
| `spec-fix`             | The divergence is real and the project's own spec (Tier 1) should change.                |
| `upstream-spec-issue`  | Divergence from an external spec (Tier 2) that is ambiguous or broken; code is defensible.|
| `mis-read`             | The playbook misread spec or code; no real divergence.                                    |
| `deferred`             | Known divergence, explicit decision to accept for now.                                    |

**`upstream-spec-issue` vs `spec-fix`.** `upstream-spec-issue` applies only
when the external (Tier 2) spec is the source of the problem AND the project
has not documented its own position. If the project's own spec (Tier 1)
already explains the deviation, there is no bug — Tier 1 wins. If the
project's spec is silent and the external spec is broken, that is
`upstream-spec-issue`, not `spec-fix` — the project shouldn't be asked to
fix an upstream body's document.

### 3.3 `severity` — impact rating on a BUG

| Value    | Meaning                                                                        |
|----------|--------------------------------------------------------------------------------|
| `HIGH`   | Correctness or security impact; data loss; visible user-facing failure.         |
| `MEDIUM` | Behavior diverges from spec but impact is contained; workaround exists.         |
| `LOW`    | Cosmetic, documentation-only, or a divergence with negligible observable effect.|

Uppercase literals. Validators reject `high`, `High`, etc.

### 3.4 `fix_type` — what surface the proposed fix touches on a BUG

| Value   | Meaning                                                          |
|---------|------------------------------------------------------------------|
| `code`  | Fix changes code only.                                           |
| `spec`  | Fix changes documentation only (project's own spec or upstream). |
| `both`  | Fix requires coordinated code and spec changes.                  |

`fix_type` is orthogonal to `disposition`. Most combinations are legal; some
pair more naturally than others:

| disposition           | natural fix_type | notes                                               |
|-----------------------|------------------|-----------------------------------------------------|
| `code-fix`            | `code`           | `both` is legitimate when spec also needs a clarifier. |
| `spec-fix`            | `spec`           | `both` when code also needs a small alignment tweak.|
| `upstream-spec-issue` | `spec` or `both` | Project may patch its own spec to pin the deviation.|
| `mis-read`            | `code`/`spec`    | `fix_type` is whichever artifact the mis-read looked at; typically no actual change shipped. |
| `deferred`            | any              | Recorded for bookkeeping; the fix is not shipped now.|

### 3.5 `verdict` — per-REQ output of the Council-of-Three semantic citation check

| Value          | Meaning                                                                |
|----------------|------------------------------------------------------------------------|
| `supports`     | The `citation_excerpt` clearly supports the requirement as stated.     |
| `overreaches`  | The citation exists but the requirement claims more than the excerpt says. |
| `unclear`      | The reviewer cannot tell whether the excerpt supports the requirement. |

Used only in `quality/citation_semantic_check.json` (Phase 6). Gate fails if
a majority (≥2 of 3) Council members record `overreaches` for the same REQ.

---

## 4. `FORMAL_DOC`

One record per plaintext document in `formal_docs/`. Produced by
`formal_docs_ingest.py` (Phase 2). Stored in
`quality/formal_docs_manifest.json`.

### 4.1 Fields

| Field             | Type    | Required | Notes                                                                 |
|-------------------|---------|----------|-----------------------------------------------------------------------|
| `source_path`     | string  | yes      | Repo-relative path, e.g. `formal_docs/virtio-v1.1.txt`. Natural key.  |
| `document_sha256` | string  | yes      | Lowercase hex SHA-256 of the file's raw bytes. Computed at ingest.     |
| `tier`            | integer | yes      | `1` or `2` only. `3/4/5` have no `FORMAL_DOC` record by definition.    |
| `version`         | string  | no       | Human-readable version string, e.g. `"1.1"`, `"RFC 7230 §4"`.          |
| `date`            | string  | no       | Publication date, ISO 8601 `YYYY-MM-DD`.                               |
| `url`             | string  | no       | Canonical URL where the document was retrieved from.                   |
| `retrieved`       | string  | no       | Date the plaintext was captured, ISO 8601 `YYYY-MM-DD`. Important for specs that change under the same version label. |
| `bytes`           | integer | no       | File size in bytes at ingest. Diagnostic only; recomputed on each run. |

There is intentionally no `plaintext_path` field — per the Document Format
Policy, `source_path` IS the plaintext file.

### 4.2 Example

```json
{
  "source_path": "formal_docs/virtio-v1.1.txt",
  "document_sha256": "a3f4c8e2b7d5f1a9c6b0e3d7f8a2c5b9d4e6f1a3c7b5d8e0f2a4c6b8d0e3f5a7",
  "tier": 1,
  "version": "1.1",
  "date": "2019-06-05",
  "url": "https://docs.oasis-open.org/virtio/virtio/v1.1/cs01/virtio-v1.1-cs01.pdf",
  "retrieved": "2026-04-15",
  "bytes": 481293
}
```

### 4.3 Common mistakes

- **Committing the original PDF and expecting ingest to parse it.** Ingest
  rejects non-text files with a message pointing at `pdftotext`. Run the
  conversion outside the playbook and commit the `.txt`.
- **Leaving `document_sha256` stale after re-saving the plaintext.** The
  hash is computed at ingest and compared to the hash embedded in every
  `citation.document_sha256`. A mismatch means every citation into that
  document is marked `citation_stale` on the next run. Re-ingest after any
  edit to a document under `formal_docs/`.
- **Marking a Tier 3/4/5 source as a `FORMAL_DOC`.** Code (Tier 3) and
  informal notes (Tier 4/5) are not formal documents. They do not get
  `FORMAL_DOC` records and cannot be cited in a `citation` block.
- **Omitting `retrieved` for an external spec with a living URL.** When an
  external spec is updated silently under the same version label, the only
  evidence of what you actually cited is the `retrieved` date combined with
  the hash. Record it.

---

## 5. `citation` (embedded)

Embedded inside every Tier 1 and Tier 2 `REQ`. Populated by
`citation_verifier.py` at ingest — the `citation_excerpt` field is a
deterministic text slice from the referenced document, not LLM-generated
prose.

### 5.1 Fields

| Field               | Type   | Required | Notes                                                                  |
|---------------------|--------|----------|------------------------------------------------------------------------|
| `document`          | string | yes      | `FORMAL_DOC.source_path` being cited.                                  |
| `document_sha256`   | string | yes      | Copied from the `FORMAL_DOC` at ingest. Stale hash → `citation_stale`. |
| `section`           | string | conditional | e.g. `"2.4"`. At least one locator (`section`, `line`, `page`) must be present. |
| `line`              | integer| conditional | 1-based line number in the plaintext file.                          |
| `page`              | integer| conditional | Page number from the original source. Diagnostic; plaintext does not have pages. |
| `version`           | string | no       | Redundant with `FORMAL_DOC.version`; present for standalone readability.|
| `date`              | string | no       | Redundant with `FORMAL_DOC.date`.                                      |
| `url`               | string | no       | Redundant with `FORMAL_DOC.url`.                                       |
| `retrieved`         | string | no       | Redundant with `FORMAL_DOC.retrieved`.                                 |
| `citation_excerpt`  | string | yes      | Extracted text at the cited location. Mechanically populated at ingest; never LLM-authored. |

**Locator rule.** At least one of `section`, `line`, `page` must be present
and must resolve in the plaintext document, or ingest fails the REQ's
validation and the REQ cannot be promoted to Tier 1 or Tier 2.

### 5.2 Example

```json
{
  "document": "formal_docs/virtio-v1.1.txt",
  "document_sha256": "a3f4c8e2b7d5f1a9c6b0e3d7f8a2c5b9d4e6f1a3c7b5d8e0f2a4c6b8d0e3f5a7",
  "version": "1.1",
  "date": "2019-06-05",
  "section": "2.4",
  "line": 142,
  "page": 34,
  "url": "https://docs.oasis-open.org/virtio/virtio/v1.1/cs01/virtio-v1.1-cs01.pdf",
  "retrieved": "2026-04-15",
  "citation_excerpt": "A device MUST reset itself when a VIRTIO_F_VERSION_1 feature bit negotiation fails, and MUST NOT accept further driver writes until RESET has completed."
}
```

### 5.3 Common mistakes

- **Allowing the LLM to author `citation_excerpt`.** The excerpt is a
  deterministic slice of the plaintext file, produced by
  `citation_verifier.py`. If the excerpt prose is too clean, too
  paraphrased, or too convenient for the REQ it supports, it was not
  mechanically extracted. Layer 1 of the hallucination gate exists to
  prevent exactly this.
- **Citing a location that does not exist.** `section=2.4` in a document
  that has no §2.4, or `line=142` in a 50-line file, fails ingest. The REQ
  cannot be promoted to Tier 1/2.
- **Omitting all three locators.** A citation with only `document` and
  no `section`/`line`/`page` is not verifiable. Ingest rejects it.
- **Hand-editing `document_sha256` to match after swapping the source file.**
  Defeats the citation-staleness detection that protects against silent spec
  drift. Always re-ingest instead.
- **Using `page` in lieu of `line` for a plaintext-only source.** Plaintext
  has no pages. `page` is a diagnostic pointer back to the original PDF or
  paginated source. The gate verifies location using `section` and `line`
  only; `page` is informational.

---

## 6. `REQ`

A requirement record — one claim about what the system is supposed to do,
anchored at a specific tier. Stored in
`quality/requirements_manifest.json`; rendered to
`quality/REQUIREMENTS.md`.

### 6.1 Fields

| Field                 | Type       | Required | Notes                                                                      |
|-----------------------|------------|----------|----------------------------------------------------------------------------|
| `id`                  | string     | yes      | `REQ-NNN` with zero-padded three-digit sequence.                            |
| `title`               | string     | yes      | Short, imperative, one-line.                                                |
| `description`         | string     | yes      | Prose explanation of the requirement, sufficient to derive tests from.      |
| `tier`                | integer    | yes      | Member of `tier` enum.                                                      |
| `functional_section`  | string     | yes      | LLM-derived grouping (e.g. `"Authentication"`, `"Bus enumeration"`). Reviewed by Council in Phase 4. |
| `citation`            | object     | conditional | Required if `tier in {1,2}`; must be absent or `null` if `tier in {3,4,5}`. Shape: §5. |
| `use_cases`           | array      | no       | List of `UC-NN` IDs this REQ participates in. One-way forward link; `[]` when none. |
| `disposition`         | string     | no       | Set when a BUG is filed against this REQ. Mirrors the resulting BUG's disposition. Null when no bugs cite this REQ. If multiple BUGs cite it and dispositions differ, use `"multiple"`. The authoritative view is still the BUG records themselves. |

### 6.2 Examples

**Tier 1 REQ (project's own spec):**

```json
{
  "id": "REQ-017",
  "title": "Device reset on failed feature negotiation",
  "description": "When VIRTIO_F_VERSION_1 negotiation fails, the device must reset itself and reject subsequent driver writes until the reset completes.",
  "tier": 1,
  "functional_section": "Device initialization",
  "citation": {
    "document": "formal_docs/virtio-v1.1.txt",
    "document_sha256": "a3f4c8e2...5a7",
    "version": "1.1",
    "section": "2.4",
    "line": 142,
    "citation_excerpt": "A device MUST reset itself when a VIRTIO_F_VERSION_1 feature bit negotiation fails..."
  },
  "use_cases": ["UC-03", "UC-05"],
  "disposition": null
}
```

**Tier 3 REQ (code is the authority, no formal doc):**

```json
{
  "id": "REQ-042",
  "title": "Non-zero exit code on missing SKILL.md",
  "description": "run_playbook exits non-zero when the target repo has no SKILL.md at any of the four documented install paths.",
  "tier": 3,
  "functional_section": "CLI entry points",
  "use_cases": ["UC-01"],
  "disposition": "code-fix"
}
```

Note the Tier 3 record has **no** `citation` field. The locator for a Tier 3
requirement is source code and is recorded in the prose `description`, not
in a structured citation. A `citation` on a Tier 3 REQ is a validation
error — citations are only legal when the authority is a FORMAL_DOC.

### 6.3 Common mistakes

- **Tier 1/2 without a citation.** Fails Layer 1 of the hallucination gate.
  If you can't cite it, it's at most Tier 3.
- **Tier 3/4/5 with a citation.** Citation is for `FORMAL_DOC` references
  only. Code snippets and file paths belong in `description`, not
  `citation`. Validators reject citation blocks on non-Tier-1/2 REQs.
- **Promoting a REQ to Tier 1 because it "feels authoritative."** Tier 1 is
  mechanical: a `FORMAL_DOC` record with `tier=1` backs the citation. No
  backing doc, no Tier 1.
- **Letting the LLM write `functional_section` as a near-duplicate of
  `title`.** The section is a grouping across many REQs; if each section has
  one REQ, the grouping does nothing. Phase 4 Council catches this.
- **Back-filling `use_cases` from a UC's REQ list.** Traceability is one-way,
  REQ → UC. Populate this list when the REQ is derived, not retroactively
  from UC records.
- **Writing `"disposition": ""`.** Empty string is not a valid substitute
  for `null`. Unresolved fields are `null` or omitted.

---

## 7. `UC`

A use case record — an end-to-end scenario from an actor's point of view.
Stored in `quality/use_cases_manifest.json`; rendered to
`quality/USE_CASES.md`.

### 7.1 Fields

| Field              | Type           | Required | Notes                                                                |
|--------------------|----------------|----------|----------------------------------------------------------------------|
| `id`               | string         | yes      | `UC-NN` with zero-padded two-digit sequence.                          |
| `title`            | string         | yes      | Short, one-line statement of the scenario.                            |
| `description`      | string         | yes      | Prose describing actor, goal, preconditions, flow, and acceptance.    |
| `actors`           | array of string| yes      | At least one actor name. Human or system roles (e.g. `"Benchmark operator"`, `"AI agent"`). |
| `steps`            | array of string| yes      | Ordered flow steps. At least one.                                     |
| `formal_doc_refs`  | array of string| no       | `FORMAL_DOC.source_path` values that back this UC. `[]` when none.    |

Note: there is no explicit `requirements[]` field on `UC`. Traceability is
**one-way**, REQ → UC. The UC → REQ direction is derived by querying REQ
records by their `use_cases` field, not persisted.

### 7.2 Example

```json
{
  "id": "UC-03",
  "title": "Benchmark operator compares multiple AI agents against the same target",
  "description": "A researcher replicating published benchmark numbers runs the playbook against the same target repo with different AI agents and compares bug yield.",
  "actors": ["Benchmark operator", "AI agent"],
  "steps": [
    "Operator runs bin/run_playbook.py <target> --agent claude",
    "Operator runs bin/run_playbook.py <target> --agent copilot",
    "Harness produces two parallel quality/ trees, one per agent",
    "Operator diffs BUGS.md and quality_gate verdicts across runs"
  ],
  "formal_doc_refs": []
}
```

### 7.3 Common mistakes

- **Steps that describe code internals.** UC steps describe what the actor
  does and what the system visibly does in response, not function call
  chains. If a step reads like a stack trace, it belongs in a REQ or an
  exploration note, not a UC.
- **Single-actor scenarios with no trigger.** Every UC has at least one
  actor and one trigger step. A UC with empty `actors` or `steps` is a
  validation error.
- **Filling `formal_doc_refs` with documents the UC doesn't actually
  depend on.** Only list documents whose content meaningfully shapes the
  scenario. Speculative references inflate the trace graph without adding
  evidence.
- **Using UC as a place to park REQ back-links.** The REQ → UC link lives
  on the REQ. The UC record stays clean.

---

## 8. `BUG`

A defect record — a specific divergence between documented intent (REQ) and
code behavior. Stored in `quality/bugs_manifest.json`; rendered to
`quality/BUGS.md` and `quality/writeups/BUG-NNN.md`.

### 8.1 Fields

| Field                    | Type    | Required | Notes                                                               |
|--------------------------|---------|----------|---------------------------------------------------------------------|
| `id`                     | string  | yes      | `BUG-NNN` zero-padded three-digit sequence.                          |
| `title`                  | string  | yes      | Short divergence statement — not a value judgment.                   |
| `severity`               | string  | yes      | Member of `severity` enum.                                           |
| `divergence_description` | string  | yes      | One-paragraph summary of what diverges from what.                    |
| `documented_intent`      | string  | yes      | Direct quote or close paraphrase of the REQ / spec language.         |
| `code_behavior`          | string  | yes      | What the code actually does, with file:line references.              |
| `disposition`            | string  | yes      | Member of `disposition` enum.                                        |
| `disposition_rationale`  | string  | yes      | One-paragraph explanation of why this disposition, not the others.   |
| `req_id`                 | string  | yes      | The primary REQ that revealed the divergence (`REQ-NNN`). Singular. |
| `proposed_fix`           | string  | yes      | Concrete description of the fix — patch-shaped when `fix_type` includes `code`, textual redline when `spec`. |
| `fix_type`               | string  | yes      | Member of `fix_type` enum.                                           |

The choice of singular `req_id` (not `req_ids[]`) is deliberate: every bug has
one primary REQ that frames the divergence. If a bug appears to touch multiple
REQs, either (a) the REQs are duplicates and should be merged, or (b) there are
several bugs, one per REQ, sharing a common root cause — file them separately
and cross-link in `disposition_rationale`.

### 8.2 Examples

**`code-fix` bug:**

```json
{
  "id": "BUG-017",
  "title": "Device does not reset on failed VERSION_1 negotiation",
  "severity": "HIGH",
  "divergence_description": "The virtio spec requires a device reset when VIRTIO_F_VERSION_1 negotiation fails; the driver silently proceeds with legacy behavior instead.",
  "documented_intent": "virtio 1.1 §2.4: 'A device MUST reset itself when a VIRTIO_F_VERSION_1 feature bit negotiation fails...'",
  "code_behavior": "src/virtio/init.c:312 — feature_negotiate() returns ENOTSUP on VERSION_1 failure, and the caller (init_device() at src/virtio/init.c:96) treats ENOTSUP as 'fall back to legacy' without invoking device_reset().",
  "disposition": "code-fix",
  "disposition_rationale": "Tier 1 spec is unambiguous (MUST). No project-level documentation of a deviation. Code is wrong.",
  "req_id": "REQ-017",
  "proposed_fix": "In init_device() at src/virtio/init.c:96, before the legacy fallback, invoke device_reset() and block on reset completion. See quality/patches/BUG-017-fix.patch.",
  "fix_type": "code"
}
```

**`upstream-spec-issue` bug:**

```json
{
  "id": "BUG-042",
  "title": "Chunked encoding trailer handling ambiguous in RFC 7230",
  "severity": "LOW",
  "divergence_description": "RFC 7230 §4.1.2 does not define behavior when a trailer field name duplicates a header field name. The implementation drops the trailer silently; other implementations merge.",
  "documented_intent": "RFC 7230 §4.1.2: 'A sender MUST NOT generate a trailer that contains a field necessary for...'",
  "code_behavior": "src/http/trailer.c:88 — drops trailers whose name collides with any prior header.",
  "disposition": "upstream-spec-issue",
  "disposition_rationale": "The external spec (Tier 2) does not resolve the collision case. The project's own spec (Tier 1) is silent. The behavior is defensible but should be documented locally rather than treated as a project defect.",
  "req_id": "REQ-089",
  "proposed_fix": "Add a paragraph to docs/http-trailers.md pinning the drop-on-collision behavior as our documented deviation; no code change.",
  "fix_type": "spec"
}
```

### 8.3 Common mistakes

- **Writing `title` as a value judgment.** `"Sloppy trailer handling"` is
  a critique; `"Trailers dropped when name collides with header"` is a
  divergence statement. Bugs are observations, not accusations.
- **Blurring `documented_intent` and `code_behavior`.** The two fields are
  deliberately separate so the reader can read them as a side-by-side diff.
  If `documented_intent` contains speculation about what the spec "seems to
  mean," the bug is not ready to file — go re-read the spec.
- **Setting `disposition=code-fix` without citing a REQ that backs the
  "documented intent."** Divergence requires two sides. If there is no REQ
  for the intent side, you have an exploration finding, not a bug.
- **`disposition=spec-fix` when the project has no formal spec (Tier 0
  documentation posture).** There's nothing to fix. Most of these are
  `code-fix` against a Tier 3/5 REQ or a `mis-read`.
- **`disposition=upstream-spec-issue` when the project's own Tier 1 spec
  explicitly documents the deviation.** Tier 1 wins over Tier 2. If the
  project already says "we deviate from RFC X for reason Y," there is no
  bug at all — close it as `mis-read`.
- **Empty or formulaic `disposition_rationale`.** "Code is wrong because
  spec says so" is not a rationale. The rationale explains why THIS
  disposition and not an adjacent one (code-fix vs spec-fix, or spec-fix
  vs upstream-spec-issue).
- **Multiple `req_id`s smuggled into a single BUG.** Split into one bug
  per REQ, share the underlying diagnosis in the writeup.
- **`fix_type=code` but `proposed_fix` is a paragraph of rationale with no
  patch.** The patch lives in `quality/patches/BUG-NNN-fix.patch`; the
  `proposed_fix` field references it and summarizes the change.

---

## 9. Cross-Record Invariants

These invariants span multiple records. The quality gate enforces them at
Layer 1 (mechanical checks):

1. **Citation tier gating.** A REQ with `tier in {1,2}` MUST have a
   `citation` block. A REQ with `tier in {3,4,5}` MUST NOT have one.

2. **Citation document exists.** `citation.document` MUST match the
   `source_path` of a record in `formal_docs_manifest.json`.

3. **Citation hash match.** `citation.document_sha256` MUST equal the
   `document_sha256` of that `FORMAL_DOC` record. Mismatch marks the
   citation `citation_stale`.

4. **Citation excerpt presence and locatability.** Every Tier 1/2 citation
   MUST have a non-empty `citation_excerpt` AND the locator
   (`section`/`line`/`page`) MUST resolve in the referenced plaintext file.
   Re-verified at gate time, not just at ingest, to catch post-ingest
   tampering.

5. **Bug → REQ resolution.** Every `BUG.req_id` MUST match the `id` of an
   existing REQ record.

6. **Forward-link resolution.** Every `UC-NN` in any `REQ.use_cases` list
   MUST match the `id` of an existing UC record. (The reverse direction
   is not required — UC → REQ is derived, not persisted.)

7. **Disposition completeness.** Every BUG MUST have a non-null
   `disposition` AND a non-empty `disposition_rationale`.

8. **Functional section presence.** Every REQ MUST have a non-empty
   `functional_section` string.

9. **No orphan formal docs.** Every file under `formal_docs/` whose
   extension is in the supported list MUST appear as a `FORMAL_DOC` record
   (ingest ran and was complete). Files with unsupported extensions MUST
   cause ingest to fail with a clear error, not be silently skipped.

10. **Run index presence.** `quality/INDEX.md` (for the current run) MUST
    exist and contain every required field listed in the design doc's
    "Per-run `INDEX.md` contents" section. This gate check lives in
    `quality_gate.py` but references this schema file for the field list.

---

## 10. Versioning

`schemas.md` carries the playbook version in the banner at the top of this
file. The string MUST match `metadata.version` in `SKILL.md`. The
bootstrap self-audit checks both.

Backwards-incompatible schema changes (renaming a field, dropping a field,
changing a required/optional flag, modifying an enum value) require a minor
version bump at minimum. Additive changes (new optional fields, new enum
values consumed only when written by new code) may ship in a patch release
but must be reflected here before any code depends on them.

If a field is being deprecated, leave it in `schemas.md` with a "deprecated
in v1.X.Y" note for at least one minor version before removing it — this is
the only signal a re-running operator has that their manifests need to be
regenerated.

---

## 11. Change Log

| Version | Change                                                                |
|---------|-----------------------------------------------------------------------|
| 1.5.0   | Initial version. `FORMAL_DOC`, `REQ`, `UC`, `BUG`, `citation`, enums. |
