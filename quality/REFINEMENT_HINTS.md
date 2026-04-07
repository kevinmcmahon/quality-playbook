# Refinement Hints

## Review Progress
- [ ] Use Case 1: Install the skill into a target repository
- [ ] Use Case 2: Execute the full quality playbook with supplemental docs
- [ ] Use Case 3: Review and close BUG findings
- [ ] Use Case 4: Run the skill integration test protocol
- [ ] Use Case 5: Perform a Council-of-Three spec audit
- [ ] Use Case 6: Refine the generated requirements over time

## Cross-Cutting Concerns
- [ ] Mirror synchronization between root docs and `.github/skills/`
- [ ] BUG tracker integrity and terminal-gate arithmetic
- [ ] Docs baseline validation and effective council handling
- [ ] Installation completeness and license consistency
- [ ] Metadata drift after late-stage requirement edits

## Feedback

### Seed observations from Phase 1
- Public docs drift is already visible in README: the shipped license file is MIT while README says Apache 2.0, and the README still teaches a four-phase model instead of the six tracked phases in `SKILL.md`.
- Install snippets currently copy `SKILL.md` and `references/` but do not copy `LICENSE.txt`, even though the packaged skill includes it and the frontmatter references it.
- `docs_gathered/` is high-value evidence and should remain part of future refinement passes.

## Additional hints
- If later refinement removes or changes any packaging contract, re-run the mirror-sync and install-snippet checks first.
