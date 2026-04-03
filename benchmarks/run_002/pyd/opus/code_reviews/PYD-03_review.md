# PYD-03 Code Review: Serialization Pipeline (pydantic-core)

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Scope:** Serializer files in `pydantic-core/src/serializers/` and `pydantic-core/tests/serializers/test_union.py`

---

## Files Reviewed

- `pydantic-core/src/serializers/computed_fields.rs`
- `pydantic-core/src/serializers/extra.rs`
- `pydantic-core/src/serializers/fields.rs`
- `pydantic-core/src/serializers/filter.rs`
- `pydantic-core/src/serializers/infer.rs`
- `pydantic-core/src/serializers/type_serializers/dataclass.rs`
- `pydantic-core/src/serializers/type_serializers/dict.rs`
- `pydantic-core/src/serializers/type_serializers/function.rs`
- `pydantic-core/src/serializers/type_serializers/generator.rs`
- `pydantic-core/src/serializers/type_serializers/list.rs`
- `pydantic-core/src/serializers/type_serializers/tuple.rs`
- `pydantic-core/src/serializers/type_serializers/union.rs`
- `pydantic-core/tests/serializers/test_union.py`

---

## Findings

### pydantic-core/src/serializers/type_serializers/function.rs

- **Line 559:** [BUG] `exclude_computed_fields` is set to `extra.exclude_none` instead of `extra.exclude_computed_fields` in the `is_field_serializer` branch of `SerializationInfo::new()`. This is a copy-paste error. When a field serializer receives `SerializationInfo` with `info_arg=True`, the `exclude_computed_fields` property will incorrectly reflect the `exclude_none` setting instead. This means: (1) if `exclude_none=True` but `exclude_computed_fields=False`, computed fields will be incorrectly reported as excluded in the info object; (2) if `exclude_none=False` but `exclude_computed_fields=True`, computed fields will be incorrectly reported as included. The non-field-serializer branch at line 579 correctly uses `extra.exclude_computed_fields`. Expected: `exclude_computed_fields: extra.exclude_computed_fields`. Actual: `exclude_computed_fields: extra.exclude_none`.

### pydantic-core/src/serializers/computed_fields.rs

- No bugs found.

### pydantic-core/src/serializers/extra.rs

- No bugs found.

### pydantic-core/src/serializers/fields.rs

- No bugs found.

### pydantic-core/src/serializers/filter.rs

- No bugs found.

### pydantic-core/src/serializers/infer.rs

- No bugs found.

### pydantic-core/src/serializers/type_serializers/dataclass.rs

- No bugs found.

### pydantic-core/src/serializers/type_serializers/dict.rs

- No bugs found.

### pydantic-core/src/serializers/type_serializers/generator.rs

- No bugs found.

### pydantic-core/src/serializers/type_serializers/list.rs

- No bugs found.

### pydantic-core/src/serializers/type_serializers/tuple.rs

- No bugs found.

### pydantic-core/src/serializers/type_serializers/union.rs

- No bugs found.

### pydantic-core/tests/serializers/test_union.py

- No bugs found.

---

## Summary

| Severity | Count |
|----------|-------|
| BUG | 1 |
| QUESTION | 0 |
| INCOMPLETE | 0 |

**Files with no findings:** `computed_fields.rs`, `extra.rs`, `fields.rs`, `filter.rs`, `infer.rs`, `dataclass.rs`, `dict.rs`, `generator.rs`, `list.rs`, `tuple.rs`, `union.rs`, `test_union.py`

**Overall assessment:** FIX FIRST

The single bug found is a clear copy-paste error in `function.rs` line 559 where `exclude_computed_fields` is assigned from `extra.exclude_none` instead of `extra.exclude_computed_fields`. This affects any field serializer that uses `info_arg=True` and queries `SerializationInfo.exclude_computed_fields`. The fix is a one-character change (replacing `exclude_none` with `exclude_computed_fields`). The bug is confined to the `is_field_serializer=True` code path and only surfaces when both `info_arg=True` and `exclude_computed_fields` or `exclude_none` are set to non-default values.
