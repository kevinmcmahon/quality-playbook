# Bootstrap source documentation

These files are the gathered chat history the playbook uses as input during the bootstrap run (playbook auditing QPB itself). They feed Phase 0/1 so REQUIREMENTS.md is grounded in the actual design conversations, not reconstructed from SKILL.md alone.

Last refreshed: 2026-04-18

## Files

- `Cowork-2026-04-03-Convert playbook to open-source skill-1.md` — Cowork chat, the conversion of the internal Octobatch quality system into the open-source Quality Playbook skill.
- `Cowork-2026-04-06-Review Quality Playbook v1.3.7 results.md` — Cowork chat, review of the v1.3.7 benchmark run that drove the next several iteration passes.
- `Claude-web-Quality-Playbook-Opus-4.6.json` — Claude.ai chat, 186 messages, Opus 4.6 model. Extracted as a single conversation object from the 2026-04-18 full export's `conversations.json`.

## Gemini

There is no standalone Gemini conversation file. The relevant content is 11 scattered prompts in the Google Takeout MyActivity export (see `AI Chat History/Google Gemini takeout-20260404T142659Z-3-001/My Activity/Gemini Apps/MyActivity.html`). They are not included here because Takeout doesn't preserve chat-level grouping; if the bootstrap needs that material, grep MyActivity.html for "quality playbook" keywords.

## Refreshing

When any of these chats see significant new activity, recopy the source files from `AI Chat History/` over the versions here. The two Cowork files are single markdown docs indexed by chat name. The Claude.ai JSON is extracted from the bulk export's `conversations.json` by matching `name == "Quality Playbook (Opus 4.6)"`.
