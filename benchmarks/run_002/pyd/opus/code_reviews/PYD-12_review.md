# PYD-12: Code Review — enum_.rs & test_enums.py

## Summary

Reviewed `pydantic-core/src/validators/enum_.rs` (247 lines) and `pydantic-core/tests/validators/test_enums.py` (507 lines) for bugs and correctness issues.

---

## Findings

### Finding 1

| Field       | Value |
|-------------|-------|
| Type        | BUG |
| File        | `tests/validators/test_enums.py` |
| Line        | 465 |
| Severity    | Medium |
| Description | Function `support_custom_new_method` is missing the `test_` prefix. Pytest discovers test functions by the `test_` naming convention, so this function is **never executed** by the test suite. The function contains meaningful assertions (lines 486–489) validating enum behavior with custom `__new__` methods and multi-value enums. It should be `test_support_custom_new_method`. This means the behavior it intends to validate (enum members resolved via `_value2member_map_` side-channel) has zero test coverage. |

### Finding 2

| Field       | Value |
|-------------|-------|
| Type        | QUESTION |
| File        | `src/validators/enum_.rs` |
| Line        | 125 |
| Severity    | Medium |
| Description | When `T::validate_value` returns `None`, the fallback calls `class.as_unbound().call1(py, (input.as_python(),))`. For JSON input, `as_python()` returns `None` (the Rust `Option::None`, which PyO3 converts to Python `None`). This means the enum constructor is called with `None` as the value — i.e., `MyEnum(None)`. For most enums this harmlessly raises `ValueError` (caught by the `if let Ok`). However, if an enum has `None` as a valid member value (e.g., `class MyEnum(Enum): a = None`), a **non-matching** JSON input would incorrectly resolve to that member. The fix would be to gate this call on `input.as_python().is_some()`, or use `input.to_object(py)?` (as is done on line 128) instead. |

### Finding 3

| Field       | Value |
|-------------|-------|
| Type        | QUESTION |
| File        | `src/validators/enum_.rs` |
| Lines       | 125–136 |
| Severity    | Low |
| Description | When a `missing` handler is configured and the input doesn't match any member, the `_missing_` logic can be invoked **twice**: first implicitly via the Python enum constructor on line 125 (`class.call1(...)` triggers Python's `Enum.__new__` → `_missing_`), and then explicitly via the `missing` callable on line 128. For typical `_missing_` implementations this is harmless (the first call fails, the second is the canonical path). But if `_missing_` has **side effects** (logging, counters, database writes), those side effects fire twice per validation of a non-matching value. A guard like `if self.missing.is_none()` around the line-125 constructor call would avoid the redundant invocation. |

### Finding 4

| Field       | Value |
|-------------|-------|
| Type        | QUESTION |
| File        | `src/validators/enum_.rs` |
| Lines       | 189–191 |
| Severity    | Low |
| Description | In `PlainEnumValidator::validate_value`, when the input is a `PyFloat` (and not strict), the code calls `lookup.validate_int()` (line 191). The comment on line 189 says this is "necessary for compatibility with 2.6, where float values are allowed for int enums in lax mode." This correctly handles the case where a plain enum has **integer** member values and receives a float like `1.0` (coerced to `1`). However, for a plain enum with **float** member values (e.g., `a = 1.5`), a float subclass input like `MyFloatSubclass(1.5)` would fail the initial `lookup.validate()` (line 180), then `validate_int` would fail to find `1.5` (not a valid int), and the method returns `None`. The value is then recovered by the enum-constructor fallback on line 125, so no incorrect behavior occurs, but the path is indirect and the comment is misleading about the actual scope. |

---

## Files Reviewed

- `pydantic-core/src/validators/enum_.rs` — 247 lines, fully read
- `pydantic-core/tests/validators/test_enums.py` — 507 lines, fully read

## Methodology

- Read both files in full, including all function bodies
- Verified `as_python()` default implementation returns `None` for non-Python input (`input_abstract.rs:73–75`)
- Verified `to_object()` properly converts any input to a Python object (`input_abstract.rs:63–65`)
- Confirmed `support_custom_new_method` has no `test_` prefix via grep
- Cross-referenced `LiteralLookup::validate` signature and behavior in `literal.rs`
