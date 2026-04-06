# PYD-07 Code Review: _typing_extra.py and test_forward_ref.py

## pydantic/_internal/_typing_extra.py

- **Line 413:** [BUG] Docstring for `try_eval_type` has swapped parameter descriptions. The `localns` arg is documented as "The global namespace to use during annotation evaluation" and the `globalns` arg is documented as "The local namespace to use during annotation evaluation." These descriptions are reversed — `globalns` should describe the global namespace and `localns` should describe the local namespace. While the function implementation correctly passes `globalns` and `localns` to `eval_type_backport` (line 423), this incorrect documentation could mislead developers into passing arguments in the wrong order when calling this public function.

- **Line 438:** [BUG] Same swapped docstring issue in `eval_type`. The `localns` arg is documented as "The global namespace" and `globalns` as "The local namespace." Same risk as above — callers relying on the docstring would swap their namespace arguments.

- **Line 493:** [BUG] Missing closing backtick in RecursionError message string. The message reads `` `MyType = list['MyType'] `` but the closing backtick after `]` is missing. The actual string is `"e.g. \`MyType = list['MyType']), "` — it should be `"e.g. \`MyType = list['MyType']\`), "`. This produces a malformed markdown-style backtick in the error note shown to users.

## tests/test_forward_ref.py

- **Line 1364-1371:** [BUG] In `test_validate_call_does_not_override_the_global_ns_with_the_local_ns_where_it_is_used`, the `inner()` function is defined (lines 1364-1371) but never called. The function contains the entire test logic: importing `func` from `module_1`, wrapping it with `validate_call`, and asserting `func_val(a=1)` works. Since `inner()` is never invoked, the test only creates the module and then exits — it passes vacuously without testing its stated purpose. Compare with the other `inner()` at line 1471 which IS called at line 1479.

- **Lines 1004, 1008, 1013, 1017:** [QUESTION] In `test_rebuild_recursive_schema`, four model classes use `model_config = dict(undefined_types_warning=False)`. However, `undefined_types_warning` does not exist as a recognized config key in `pydantic/config.py` (searched the entire `pydantic/` source — zero matches). Because the config is set via a plain `dict` rather than `ConfigDict`, no validation rejects the unknown key — it is silently ignored. The test still passes because its assertions don't depend on this config. Is this dead config from a previous pydantic version, or is there an unimplemented config feature?

## Summary

| Severity | Count |
|----------|-------|
| BUG | 4 |
| QUESTION | 1 |

- **Files with no findings:** None (both files have findings)

**Overall assessment:** FIX FIRST — The uncalled `inner()` in `test_validate_call_does_not_override_the_global_ns_with_the_local_ns_where_it_is_used` means a stated test scenario is not being exercised, which could mask regressions. The swapped docstrings in two public-facing functions (`try_eval_type`, `eval_type`) risk incorrect usage by downstream callers.
