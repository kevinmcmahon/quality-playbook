# Code Review: nsqadmin/static/js/views/channel.hbs

## channel.hbs

- **Line 132:** BUG — `{{#if ../graph_active}}` uses incorrect Handlebars scope prefix `../`. This line is in the **Total row**, which is outside the `{{#each nodes}}` block (that block ends at line 122). At this point the context is the root template context, so `graph_active` is directly accessible without `../`. The `../` causes Handlebars to look above the root frame, resolving to `undefined`/falsy. As a result, when graphs are enabled, the Total row **never renders the Rate `<td>`**, producing 9 columns instead of 10. This misaligns the Total row against the header and per-node data rows. Compare with `topic.hbs:114` which correctly uses `{{#if graph_active}}` (no `../`) in the equivalent total row. **Severity: Medium** — table layout breaks when graphing is active.

## Summary

| Severity | Count |
|----------|-------|
| Medium   | 1     |

- **Files with no additional findings:** channel.hbs (remainder of template is correct)
- The per-node rows (inside `{{#each nodes}}`) correctly use `../graph_active` (lines 91, 103).
- The Total graph row at line 144 correctly uses `{{#if graph_active}}` (no `../`), confirming the inconsistency at line 132 is unintentional.
- Column counts are otherwise consistent across header, data, and graph rows.
- No XSS concerns — all interpolations use double-brace (`{{...}}`) which auto-escapes in Handlebars.

**Overall assessment: FIX FIRST** — The table misalignment when graphs are active is a user-visible rendering bug.
