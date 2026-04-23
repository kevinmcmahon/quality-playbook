# Quality Playbook v1.5.0 — Design Document

*Status: design complete, implementation pending*
*Authored: April 2026*
*Owner: Andrew Stellman*

## Purpose of This Document

This file captures the full design rationale for QPB v1.5.0 so that implementation doesn't depend on the context window of any single chat session. It should contain enough context that a fresh agent (or a future Andrew) can pick up the work without backtracking. The companion file `QPB_v1.5.0_Implementation_Plan.md` covers the execution roadmap.

---

## Core Reframing — Why v1.5.0 Exists

### The Old Model (v1.4.x)

Prior versions of QPB treated bug-finding as a qualitative judgment task. The playbook read source code, formed opinions about what the code "should" do based on inferred intent, and flagged behaviors that seemed wrong. This worked, but it had two chronic weaknesses:

1. **LLM people-pleasing.** Asked to find bugs, an LLM will find bugs. Asked to evaluate intent, an LLM will synthesize a plausible-sounding narrative about what the code is "trying" to do. Both failure modes produce output that looks good but can't be mechanically verified.
2. **Upstream defensiveness.** Bug reports framed as "I think this code is wrong" invite the maintainer to defend the code. The conversation becomes adversarial before disposition can be discussed.

### The New Model (v1.5.0)

**Defect redefined:** a defect is a divergence between documented intent and code implementation. Not a judgment about whether code is "good" — a factual comparison between two artifacts.

This reframing changes the LLM's task from "expert code reviewer" to "diff-and-report." Instead of asking "what's wrong with this code?" the playbook asks "where does column A (documented intent) differ from column B (code behavior)?" That's a lookup task, not a performance of expertise.

Downstream consequence: the bug report becomes a bookkeeping observation rather than an accusation. Upstream maintainers engage with disposition ("the spec is wrong" vs. "the code is wrong") rather than defending the code against a critique.

This reframing is the foundation of every other change in v1.5.0.

---

## The Six Structural Changes

### 1. Formal / Informal Document Split

Projects can now provide two kinds of documentation:

- **`formal_docs/`** — authoritative sources of intent. Project specs, RFCs, published standards, API contracts with versioning and publication dates. Tracked in git. Each document requires a plaintext companion (see below).
- **`informal_docs/`** — unofficial context. AI chat logs, design notes, scratch writeups, partial thoughts. NOT tracked in git (contains private material). A `README.md` exception IS tracked so fresh clones know the folder exists and what it's for.

Gitignore pattern:
```
informal_docs/
!informal_docs/README.md
```

### 2. Tier System for Requirements

Every requirement carries a tier that reflects the authority of its source:

- **Tier 1** — project's own formal spec (highest authority; when Tier 1 and Tier 2 conflict, Tier 1 wins)
- **Tier 2** — external formal standard (RFC, W3C, ISO, etc.)
- **Tier 3** — source of truth code (when no formal spec exists; code is the authority)
- **Tier 4** — informal documentation (AI chats, design notes)
- **Tier 5** — inferred from code behavior without any documentation backing

Tier distribution is a reported metric, not a gate. A valid run against a doc-poor project will be 100% Tier 3/4/5. The playbook degrades gracefully into a Spec Gap Analyzer for projects without formal documentation. The meta-finding "this project has 0 Tier 1/2 requirements" is itself a valuable output — it characterizes the project's documentation maturity.

### 3. Formal-Source Citation Schema

Every Tier 1/2 requirement must cite its source with mechanical precision:

```
citation:
  document: virtio-v1.1.pdf
  document_sha256: <hash>
  version: "1.1"
  date: "2019-06-05"
  section: "2.4"
  line: 142
  page: 34
  url: https://docs.oasis-open.org/virtio/virtio/v1.1/...
  retrieved: "2026-04-15"
  citation_excerpt: "<extracted text at the cited location>"
```

The `citation_excerpt` field is not optional — it's populated at ingest by extracting the text at the cited location. If the location doesn't exist in the plaintext companion, the requirement fails validation and can't be promoted to Tier 1/2.

### 4. One-Way Traceability

Traceability goes REQ → UC → formal_doc, not the other way around.

Earlier discussion explored bidirectional traceability (every UC links to REQs, every REQ links to UCs) but rejected it as too brittle for current LLMs to maintain consistently. One-way traceability has the property that each link is locally verifiable: given a REQ, you can check its UC link; given a UC, you can check its formal_doc link. No global consistency requirement.

Completeness check is still possible without bidirectional links: run a pass that asks "are there use cases this requirement doesn't serve?" and "are there requirements that don't appear in any use case?" That's an audit, not a structural constraint.

### 5. Requirements Grouped by Functionality

REQUIREMENTS.md reorganizes from a flat list into functional sections. Each section has:

- A short introduction describing the functional area
- The requirements in that area (with tier, citation, disposition fields)
- Back-references to applicable use cases

Completeness check: after the functional grouping, a final audit pass verifies that requirements and use cases span the application's surface area. This is a Phase 4 (Council) activity, not a hard gate.

### 6. Unified `quality/` Layout with Run Archival

Prior versions scattered skill-generated output across three top-level directories: `quality/` (current run), `control_prompts/` (per-phase prompts), and `previous_runs/` (archived runs). Three locations, one cognitive purpose. v1.5.0 consolidates: **QPB writes to `quality/`, nothing else.**

#### Target layout

```
quality/
  # Current run — overwritten each run (keeps git diff across runs clean)
  BUGS.md
  REQUIREMENTS.md
  CONTRACTS.md
  COVERAGE_MATRIX.md
  EXPLORATION*.md
  ITERATION_PLAN.md
  QUALITY.md
  RUN_*.md
  COMPLETENESS_REPORT.md
  code_reviews/
  mechanical/
  patches/
  spec_audits/
  writeups/
  control_prompts/           ← moved from repo root; per-phase prompt captures
    phase1.output.txt
    ...
  results/                   ← timestamped result files + -latest pointers
    recheck-results-YYYYMMDDTHHMMSSZ.json
    recheck-results-latest.json
    recheck-summary-YYYYMMDDTHHMMSSZ.md
    recheck-summary-latest.md
    gate-report-YYYYMMDDTHHMMSSZ.json
    ...
  RUN_INDEX.md               ← top-level: one row per archived run

  # Historical runs — full snapshots, one folder per run
  runs/                      ← renamed from previous_runs/
    20260418T193542Z/
      BUGS.md
      REQUIREMENTS.md
      ...                    ← same structure as above, frozen snapshot
      control_prompts/
      results/
      INDEX.md               ← per-run metadata
```

#### Why folder-level timestamps, not per-file

An earlier draft of this design proposed per-file timestamp suffixes (`BUGS-20260419T143022Z.md`). That approach was rejected because it breaks relative markdown links between artifacts — `BUGS.md` links to `writeups/BUG-001.md`, and timestamp-suffixed filenames would require either rewriting every link at archive time or maintaining a parallel link-translation table. Folder-level timestamps (`quality/runs/<ts>/BUGS.md` → `quality/runs/<ts>/writeups/BUG-001.md`) preserve relative links automatically.

Per-file timestamps ARE still used inside `quality/results/`, because that folder holds multiple rechecks between archives — each recheck overwrites would lose history. The `-latest` pointer keeps naive consumers happy.

#### Archival policy

**Archive at end of successful run.** When `quality_gate.py` passes, the orchestrator snapshots the entire `quality/` tree (except `runs/` itself, to avoid recursion) into `quality/runs/<start-timestamp>/` and appends a row to `RUN_INDEX.md`. The current-run artifacts stay in place so a subsequent run starts from them or overwrites cleanly.

**Overwrite failed runs by default.** A failed run is not historical evidence and would otherwise accumulate forever. Detection is deterministic: a failed run is one where either (a) `quality/results/gate-report-latest.json` reports a non-pass verdict, or (b) no gate report exists at all (orchestrator crashed before gate ran). If the next run detects this state, it overwrites without prompting.

**Non-interactive safety.** The `run_playbook` runner and benchmark harness are non-interactive. The orchestrator MUST NOT prompt at any step that could block CI execution. If it needs a decision between overwrite and archive-as-failed, the default is overwrite. Operators who want to preserve a failed run invoke the explicit `archive --status=failed` command (see below) before the next run.

**Explicit archive command.** For cases where an operator wants to preserve a failed run, snapshot an in-progress run, or force-archive before overwriting, expose `quality_playbook archive [--status=failed|partial]`. Archive folders for non-successful runs get a suffix: `quality/runs/20260419T143022Z-FAILED/` or `-PARTIAL/`. This is the only way a non-successful run enters history.

#### Per-run `INDEX.md` contents

Generated by the orchestrator (not the gate — the orchestrator knows phase timing and model assignments). Required fields:

- `run_timestamp_start` / `run_timestamp_end` / `duration_seconds`
- `qpb_version` (e.g., "1.5.0")
- `target_repo_path`
- `target_repo_git_sha` (at run start)
- `target_project_type` (Code / Skill / Hybrid — per v1.5.2)
- `phases_executed[]` — each with: `phase_id`, `model`, `start`, `end`, `exit_status`
- `summary`:
  - `requirements`: counts by tier
  - `bugs`: counts by severity and disposition
  - `gate_verdict`: pass / fail / partial
- `artifacts[]` — relative links to files produced in this run folder

The gate validates INDEX.md exists and has all required fields before issuing a pass verdict.

#### Top-level `RUN_INDEX.md`

Scannable history — one row per archived run: timestamp, QPB version, target project type, gate verdict, bug count, link to that run's `INDEX.md`. Append-only; never rewrites prior rows.

#### Phase 0 Seed Discovery update

The current Phase 0 (Prior Run Analysis) globs `previous_runs/*/quality/BUGS.md` to extract seed checks — bugs found in prior runs that should be re-verified. After this layout change, the glob must update to `quality/runs/*/BUGS.md`. This is a one-line fix but easy to miss; call it out explicitly in the implementation plan so Phase 0 doesn't silently stop finding seeds.

#### Migration of existing `previous_runs/`

QPB's own repo already has `previous_runs/20260418T193542Z/`. Migration: rename to `quality/runs/20260418T193542Z/`, backfill `INDEX.md` from git log and surviving artifacts (best-effort — older runs may lack some fields), and generate the initial `RUN_INDEX.md`. One-time migration script delivered as part of v1.5.0.

#### `.gitignore` policy — project-level choice

Archived runs can grow large (hundreds of megabytes of LLM prompts and artifacts over many iterations). Whether to track them is a project-level decision:

- **Skill template default:** `quality/runs/` is ignored. New adopters don't accidentally commit bulk history.
- **QPB's own repo:** `quality/runs/` IS tracked, as it's canonical self-audit / bootstrap evidence for the playbook itself. QPB's `.gitignore` overrides the template default.
- **Documented in `quality/README.md`:** one paragraph explaining the tradeoff so projects can opt in knowingly.

Skill template gitignore pattern:
```
# Archived QPB runs — bulk history; uncomment to track as project evidence.
quality/runs/

# But always track the top-level index (small, useful for reviewers).
!quality/RUN_INDEX.md
```

#### Interaction with timestamped result filenames

This structural change absorbs what an earlier draft treated as a separate "Timestamped Result Filenames" feature. The contract now splits cleanly:

- **Inside `quality/results/`** (current run, between archives): per-file timestamps + `-latest` pointers. Catches multiple rechecks.
- **At archive time:** whole `quality/` tree copied to `quality/runs/<ts>/`. Folder name IS the timestamp; filenames inside stay unchanged so relative markdown links survive.

---

## Disposition Field

Every bug carries a disposition indicating how it should be resolved:

- **`code-fix`** — divergence, code should change
- **`spec-fix`** — divergence, project's own spec (Tier 1) should change
- **`upstream-spec-issue`** — divergence because external spec (Tier 2) is ambiguous or broken; project's implementation is defensible
- **`mis-read`** — playbook misread spec or code; no real divergence
- **`deferred`** — known divergence, explicit decision to accept

Important nuance: when Tier 1 (project's own spec) and Tier 2 (external spec) conflict, Tier 1 wins. If a project documents "we deviate from RFC 7230 on chunked encoding for reason X," that's not a defect. `upstream-spec-issue` only applies when there's no project-level documentation of the deviation.

**Disposition accuracy tracking (future consideration):** a spec-fix disposition is a claim about upstream intent. If upstream patches the code instead of the spec, the disposition was wrong. Over time, the playbook should track disposition accuracy as a calibration signal on its own judgment. This is not a v1.5.0 requirement but should be designed-for in the data schema.

---

## Hallucination Risk Mitigation

LLMs hallucinate citations confidently. If Tier 1/2 citations can be fabricated, the entire authority hierarchy collapses. Mitigation is a hard gate with two layers:

### Layer 1: Mechanical Grep at Ingest

When a REQ cites `document=virtio-v1.1.pdf, section=2.4, line=142`, the ingest pass extracts text at that location from the plaintext companion and stores it in `citation_excerpt`. If the location doesn't exist, the REQ fails validation and cannot be promoted to Tier 1/2. Cheap, catches ~90% of hallucinations.

### Layer 2: Semantic Check in Phase 4 Council

The Council reviews each Tier 1/2 REQ with the excerpt attached. Single question: "Does this excerpt support this requirement, or is the requirement overreaching what the excerpt actually says?" Catches cases where the citation exists but doesn't mean what the REQ claims.

**Both layers must pass.** Either one alone is insufficient. Layer 1 without Layer 2 accepts excerpts that don't support the claim. Layer 2 without Layer 1 can be fooled by fabricated excerpts.

---

## Stdlib-Only Python — Global Design Constraint

All Python code shipped with the playbook must run on a stock Python 3 installation with no `pip install` step and no virtual environment. This is a hard constraint, not a preference.

Reason: agent runners like Claude Code, GitHub Actions self-hosted runners, and locked-down enterprise environments often cannot create virtual environments or install packages at run time. Every external dependency we add is a trip hazard that prevents someone from running QPB in their environment.

Consequences:

- No `PyPDF2`, `pdfplumber`, or similar — we don't parse PDFs at all (see "Document Format Policy" below).
- No `PyYAML` — if we need to parse YAML frontmatter in SKILL.md, we hand-roll a minimal parser for the specific schema we control, or switch to a format the stdlib handles (JSON frontmatter, TOML via `tomllib` on Python 3.11+).
- No `requests` — if we ever need HTTP, use `urllib.request`.
- No `jinja2` — templates use `str.format()` or f-strings.
- No `jsonschema` — validation is hand-rolled against `schemas.md` using stdlib `json` + explicit field checks.

Exception: developer-facing tooling (benchmarks, local smoke tests) MAY use `pip install` IF it lives outside the core skill and is clearly marked. Core skill code stays stdlib-only.

---

## Document Format Policy

Formal and informal docs are plaintext only: `.txt`, `.md`, or equivalent text formats. PDFs are not accepted as input to ingest or the citation gate.

Reason: PDF parsing requires a library (brittle across Unicode, columns, embedded fonts, image-only PDFs) which would violate the stdlib-only constraint. Pushing the extraction step outside the playbook keeps the implementation simple and portable.

**Workflow for PDF sources:** the operator runs `pdftotext` (or their tool of choice) outside QPB and checks in the resulting `.txt` or `.md` file. The original PDF may also live in the repo for human reference, but the playbook only reads the plaintext.

Ingest fails with a clear message if it encounters a non-text file in `formal_docs/`:

```
formal_docs/virtio-v1.1.pdf is not a text file.
QPB does not parse PDFs. Convert outside the playbook (e.g. `pdftotext
virtio-v1.1.pdf virtio-v1.1.txt`) and commit the .txt file.
```

Supported extensions list lives in `schemas.md` (initially `.txt`, `.md`; extensible if a benchmark finds another plaintext format worth supporting).

---

## Formal Document Versioning

Gemini's original review (April 2026) surfaced this as a gap: if QPB files a spec-fix bug against virtio v1.1 and the project publishes v1.2 resolving the ambiguity, how does the next QPB run know the old citation is stale?

Three mechanisms, in increasing cost:

1. **Checksums.** The `FORMAL_DOC` record stores `document_sha256` alongside version/date/section fields. On re-run, if the formal doc's checksum has changed, every REQ citing that doc is marked `citation_stale` and must be re-verified against the new version. Cheap, automatic.

2. **Disposition replay.** A spec-fix bug's disposition record includes the exact text-before and text-after the spec *should* read. On re-run, if the new spec text matches the proposed fix, the bug auto-closes as `resolved-upstream`. If the new spec text is different from both the old and the proposed fix, the bug reopens with a note that upstream took a different path.

3. **Version pinning at run time.** The run config pins the exact version of each formal doc. To re-run against a newer version, the operator explicitly bumps the pin, which forces full re-derivation of REQs. Prevents silent drift mid-iteration.

All three together: checksums catch changes automatically, disposition replay handles intentional spec-fix flow, version pinning prevents accidental mixing.

---

## schemas.md — The Static Contract

`schemas.md` is NOT a per-run artifact. It's a static contract file that ships with the playbook skill, alongside `SKILL.md`. It defines what REQ, UC, BUG, and FORMAL_DOC records look like; what valid tier values are; what the disposition enum contains.

Versioning: `schemas.md` is versioned with the playbook itself. v1.5.0 → v1.5.1 may tweak fields.

Reason for making it static: if `schemas.md` were generated per run, two runs of the same playbook against the same project could produce structurally different artifacts. That would break diff-across-runs and benchmark-across-projects. Invariance across runs is what makes the quality gate mechanical rather than judgment-based.

**Reference file strategy:** One consolidated `schemas.md` with every data structure and examples. Protocols (how to produce/validate) stay inline in SKILL.md where they're used, NOT in separate files. The failure mode Gemini warned about — "reference file hell" with 8 separate protocol files fragmenting LLM context — is avoided by this single-file approach.

**Project-specific extensions:** some projects may need domain fields (e.g., a crypto library wanting `threat_model` on every REQ). If that comes up, the clean answer is a project-level `schemas.local.md` that extends but cannot override the base schema. Deferred for v1.5.0 — start with a single global schema and only add extension support if a benchmark project actually needs it.

---

## Provenance — How This Design Emerged

This section documents the review-and-revision history so future work knows which decisions are load-bearing and why.

### Originating insight (Andrew)

During the v1.4.5 self-audit, Andrew pushed back on a framing I used that treated MST/virtio spec-vs-code disagreement as a "judgment call" about which source was authoritative. His correction was the seed of v1.5.0:

> "If there's a disagreement there, it's a defect. Like MST pointed out, it could need a spec change rather than a code change, but it's a flag that the documented intent and code implementation do not match. That is the definition of a defect."

Every structural change in v1.5.0 descends from this: if defect = divergence, then the playbook's job is mechanical comparison, which requires strict schemas, verifiable citations, and an authority hierarchy.

### Gemini review round 1

Gemini reviewed the initial plan and flagged four functional issues (patent discussion excluded per Andrew's instruction):

1. **"Antidote to LLM people-pleasing"** — agreed with the reframing; noted that binary comparison changes LLM attention allocation from performance-of-expertise to production-of-evidence.
2. **Tier 3 problem** — realistically ~80% of open-source projects have poor documentation and will default to Tier 3/4/5. QPB becomes a Spec Gap Analyzer for most projects. The meta-finding "0 Tier 1/2 requirements" is itself valuable. This shifted tier distribution from a failure metric to a reported metric.
3. **Hallucination risk** — LLMs are notoriously bad at citing specific sections. Must have both mechanical grep AND semantic Council check. Elevated from "nice-to-have" to "hard gate."
4. **Formal doc versioning** — closing question: how does QPB know when an old citation is stale after a spec update? Led to the three-mechanism solution above.

### Gemini review round 2

After the initial v1.5.0 plan was drafted, Gemini reviewed it and added four refinements:

1. **External spec dilemma** — a project faithfully implementing a broken RFC shouldn't be asked to file a spec-fix against their own spec. Led to `upstream-spec-issue` as a distinct disposition for Tier 2 divergences. Andrew's nuance: when Tier 1 and Tier 2 conflict, Tier 1 wins, because a project's own documented deviation is authoritative intent.
2. **PDF grep problem** — don't parse PDFs in the quality gate; require plaintext companions. Accepted as-is.
3. **Context fragmentation** — warned against "reference file hell" of separate protocol files. Adjusted to: one consolidated `schemas.md`, protocols inline in SKILL.md.
4. **Informal docs README** — add tracked `informal_docs/README.md` via gitignore exception so fresh clones know what the folder is for. Accepted as-is.

### Design stability

The design is considered stable at the structural level. Open questions that could surface during implementation:

- Project-specific schema extensions (`schemas.local.md`) — deferred unless a benchmark needs it.
- Disposition accuracy tracking over time — design-for but don't implement in v1.5.0.
- Whether `pdftotext` auto-run on ingest is worth the complexity — decide during Phase 2.

---

## Out of Scope for v1.5.0

- Bidirectional traceability (REQ ↔ UC)
- Hard gate on tier distribution
- Cross-project requirement sharing
- Schema extension mechanism (`schemas.local.md`)
- Disposition accuracy calibration dashboard
- Anything related to patents (explicitly excluded from this chat's scope)

---

## Success Criteria

v1.5.0 is successful if:

1. The benchmark repo with formal docs (virtio) shows a qualitative improvement in bug analysis — bugs now carry dispositions and cite specific spec sections, not just behavioral descriptions.
2. The benchmark repos without formal docs (chi, cobra, express, httpx) produce clean Tier 3/4/5 runs without citation hallucinations in the artifacts.
3. The mechanical citation gate (Layer 1) rejects at least some fabricated citations during test runs. Zero rejections would suggest the test wasn't adversarial enough.
4. The Council-of-Three Phase 4 flags at least one Tier 1/2 REQ per run where the excerpt doesn't support the claim (semantic layer catching what mechanical layer missed), OR reports clean with confidence.
5. A fresh clone of any benchmark repo can run end-to-end with no manual schema copy-paste, because `schemas.md` is part of the skill and ingest infrastructure is self-contained.
