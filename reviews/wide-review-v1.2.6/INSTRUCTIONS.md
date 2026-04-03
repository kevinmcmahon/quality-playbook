# Wide Review v1.2.6 — Web UI Instructions

Run all 4 simultaneously. Each takes ~5-15 minutes.

## What to attach

Attach all 8 files from `runs/improvement_001/playbook_versions/v1.2.6/`:
1. `SKILL.md` — the main playbook (576 lines)
2. `references/constitution.md` — reference: quality constitution template
3. `references/defensive_patterns.md` — reference: grep patterns and skeleton detection
4. `references/functional_tests.md` — reference: test generation guide
5. `references/review_protocols.md` — reference: code review and integration test templates
6. `references/schema_mapping.md` — reference: schema-to-test mapping
7. `references/spec_audit.md` — reference: Council of Three audit protocol
8. `references/verification.md` — reference: self-check benchmarks

## What to type as the message

Paste the contents of `REVIEW_PROMPT.md` as the chat message.

## Targets

### Target 3: Claude.ai — Opus 4.6
1. Go to claude.ai, new conversation, select **Opus 4.6**, enable **extended thinking**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response → `claude-opus.md`

### Target 4: Claude.ai — Haiku 4.6
1. Go to claude.ai, new conversation, select **Haiku 4.6**, enable **extended thinking**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response → `claude-haiku.md`

### Target 7: ChatGPT — with Thinking
1. Go to chatgpt.com, new conversation, enable **Thinking**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response → `chatgpt.md`

### Target 8: Copilot — with Think Deeper
1. Go to copilot.microsoft.com, new conversation, enable **Think Deeper**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response → `copilot.md`

## After All 4 Complete

Save responses into `reviews/wide-review-v1.2.6/` and bring them back to the Cowork session for cross-model triage.
