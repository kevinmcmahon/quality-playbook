# informal_docs/

**Tier 4 informal context** — AI chat logs, design notes, exploratory
analysis, retrospectives, and other non-canonical documentation that
carries intent signal. Loaded by `bin/informal_docs_loader.py` during
Phase 1 exploration so the LLM can read this context alongside the
codebase when deriving requirements.

Tier 4 is defined in `schemas.md` §3.1: informal documentation — AI
chats, design notes, scratch writeups. Tier 4 requirements are valid
but carry less authority than Tier 1/2 (formal specs) — citations point
back at the originating document but do NOT get a mechanical
`citation_excerpt` (no FORMAL_DOC backing).

## What counts as Tier 4

- **AI chat logs** — Claude/ChatGPT/Gemini exports, Claude Code
  transcripts, Copilot chat captures. Design conversations, incident
  post-mortems, explanations of why a particular approach was chosen.
- **Design notes** — architecture sketches, ADR-adjacent writeups,
  meeting minutes, Slack/Teams thread summaries.
- **Retrospectives** — incident reports, bug investigations, lessons
  learned, migration summaries.
- **Exploratory analysis** — the kind of README-adjacent writeup that
  explains "what I found when I read this code," as opposed to a
  formal spec.

Signal quality matters more than volume. A 20-line incident note
explaining why a retry was added is more useful than 500 lines of
chat history with no through-line.

## Format — plaintext only

Same policy as `formal_docs/`: `.txt` and `.md` only (`schemas.md`
§2). The loader rejects any other extension with the same actionable
conversion hints (`pdftotext`, `pandoc -t plain`, `lynx -dump`).

No sidecar is required — tier is implied by the folder. `README.md`
at any depth under this folder is skipped (it is folder-level
documentation, not Tier 4 content).

## Tracking

In the skill's own repo, `informal_docs/` is `.gitignore`d because
its contents are run-specific and may contain private material (chat
exports, internal incident writeups). The README is tracked via a
`.gitignore` exception so operators know what the folder is for on a
fresh clone.

In a target repo, whether to track `informal_docs/` is a project
choice. Track it if the content is non-sensitive and valuable as
project history; gitignore it (matching the skill's pattern) if the
content is private. Either way, track the README so fresh clones
self-explain.

## Missing-folder behavior

`informal_docs/` is **optional**. If the folder does not exist in the
target repo, `bin/informal_docs_loader.load_informal_docs()` returns
`[]` and Phase 1 proceeds with zero Tier 4 context. The run is valid;
REQs that would have been Tier 4 fall through to Tier 5 (inferred
from code) or simply are not derived. The Spec Gap reporting in the
completeness report notes the absence.

## What does not go here

- **Canonical specs** — those are Tier 1/2 for `formal_docs/`.
- **Source code** — the code itself is Tier 3 authority; it lives in
  the target repo proper, not under this folder.
- **Test fixtures or sample data** — those are project artifacts, not
  documentation.
- **Binary content** — images, PDFs, archives. Convert to plaintext
  first, or leave them out.
- **Anything private you would not want a run's exploration context
  to carry forward** — Tier 4 content is read into LLM context
  during Phase 1. Assume everything here gets seen.

Keep the signal-to-noise ratio high. The loader sorts by path and
reads every file — noisy content crowds out useful context.
