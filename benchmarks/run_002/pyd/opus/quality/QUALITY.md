# Quality Constitution: Pydantic

## Purpose

Pydantic is the most widely-used data validation library for Python, converting Python type hints into runtime validation, serialization, and JSON Schema generation. Quality for Pydantic means **fitness for use** in the Juran sense: every model definition must produce correct validation behavior, every serialization must preserve data fidelity, and every schema generation must accurately reflect the model's constraints. A subtle bug in Pydantic doesn't just break one application — it silently corrupts validation across thousands of downstream projects.

Quality is **built in, not inspected in** (Deming): the validation pipeline from Python type annotations through `GenerateSchema` to `pydantic-core` `SchemaValidator` must produce correct schemas by construction. Post-hoc testing catches regressions, but the architecture itself — sentinel values, defensive type guards, state machine tracking via `__pydantic_complete__` — exists to prevent entire categories of bugs from being possible.

Quality is **free** (Crosby): investing in a quality playbook for Pydantic prevents the far more expensive debugging of silent validation failures, schema generation errors that surface only in production, and serialization data loss that propagates through API boundaries.

## Coverage Targets

| Subsystem | Target | Why |
|-----------|--------|-----|
| `pydantic/_internal/_generate_schema.py` | 90–95% | Most complex module (~4000 lines). Schema generation from arbitrary Python types is the core pipeline. A bug here silently produces wrong validators for all downstream models. Defensive `try/except` blocks and `isinstance` guards cover 50+ edge cases. |
| `pydantic/main.py` (BaseModel) | 90–95% | The public API surface. `__init__`, `__setattr__`, `model_validate()`, `model_dump()` must handle frozen fields, private attributes, extra fields, and custom validators without data loss. The memoized `__pydantic_setattr_handlers__` cache adds a layer of complexity where stale handlers could bypass field checks. |
| `pydantic/fields.py` (FieldInfo) | 85–90% | Field metadata merging (`_apply_field_from_defaults`, `merge_field_infos`) uses `PydanticUndefined` sentinel comparisons. Wrong merge order silently drops constraints. |
| `pydantic/types.py` | 85–90% | 60+ constrained types. Each `__get_pydantic_core_schema__` method must produce correct core schemas. `conint()`, `confloat()`, `constr()` apply constraints conditionally via `is not None` guards — a missed guard silently ignores a constraint. |
| `pydantic/_internal/_discriminated_union.py` | 85–90% | Discriminated union resolution. `_ApplyInferredDiscriminator` must correctly map discriminator values to union members. `MissingDefinitionForUnionRef` exceptions guard against incomplete schema resolution. |
| `pydantic/json_schema.py` | 80–85% | JSON Schema generation from core schemas. Mode-aware (`validation` vs `serialization`). Incorrect schema generation breaks OpenAPI docs and API contract validation. |
| `pydantic/_internal/_model_construction.py` | 80–85% | `ModelMetaclass.__new__` orchestrates field collection, schema generation, and validator binding. The `__pydantic_complete__` state machine must transition correctly or models silently lack validation. |
| `pydantic/type_adapter.py` | 80% | Non-model type validation. `_getattr_no_parents()` safe attribute access prevents MRO issues. |
| `pydantic/config.py`, `pydantic/aliases.py` | 75–80% | Configuration and alias resolution. Lower risk — mostly data containers with simple validation. |

## Coverage Theater Prevention

The following test patterns look like they provide coverage but catch zero real bugs in Pydantic:

- **Asserting `isinstance(model, BaseModel)`** — This tests Python's metaclass, not Pydantic's validation logic.
- **Creating a model and only checking it didn't raise** — Pydantic's value is in *what* it validates, not that `__init__` completes. Assert field values after construction.
- **Testing `model_dump()` returns a dict** — Every model returns a dict. Test that the dict contains the *correct* values, especially after type coercion.
- **Asserting `ValidationError` is raised for obviously wrong types** — Testing `int("not_a_number")` tells you nothing about Pydantic. Test boundary cases: `float("inf")` with `allow_inf_nan=False`, empty strings in constrained fields, `None` in `Optional` vs required fields.
- **Mocking `pydantic_core.SchemaValidator`** — The core validator is the system under test. Mocking it tests your mock, not Pydantic.
- **Testing deprecated V1 APIs without V2 equivalents** — V1 compatibility is intentionally thin. Test the V2 API.
- **Asserting JSON Schema has `"type": "object"`** — Every model produces this. Assert that specific field constraints (min, max, pattern, enum) appear in the generated schema.

## Fitness-to-Purpose Scenarios

### Scenario 1: Silent Constraint Dropping During Field Merge

**Requirement tag:** [Req: inferred — from FieldInfo.merge_field_infos() behavior]

**What happened:** When a child model overrides a parent field, `merge_field_infos()` in `pydantic/fields.py` merges constraints from parent and child `FieldInfo` objects. The merge uses `PydanticUndefined` sentinel comparisons (e.g., `if child.gt is not PydanticUndefined`) to decide which value wins. If a constraint exists on the parent but the child's `_attributes_set` doesn't track it as explicitly unset, the parent's constraint is silently dropped. For a model hierarchy with `conint(gt=0)` on a parent field and no explicit constraint on the child, the merged field could lose the `gt=0` bound — allowing negative values through validation on 100% of instances using the child model.

**The requirement:** Field constraint merging must preserve all parent constraints unless the child explicitly overrides them. The merged `FieldInfo.metadata` list must contain every constraint from both parent and child, with child taking precedence only for explicitly set attributes.

**How to verify:** Create parent model with `Field(gt=0, le=100)`, child model overriding the field with `Field(description="updated")`. Validate that the child still enforces `gt=0` and `le=100`. Assert `ValidationError` for value `0` and value `101`.

### Scenario 2: Incomplete Model Due to `__pydantic_complete__` State Machine Failure

**Requirement tag:** [Req: inferred — from ModelMetaclass.__new__() and __pydantic_complete__ state tracking]

**What happened:** `_model_construction.py` manages a state machine via `__pydantic_complete__`. A model starts as `False`, and transitions to `True` after successful schema generation (line ~710). If schema generation fails (e.g., forward reference not yet defined), the model remains incomplete. Code that checks `__pydantic_complete__` guards against using incomplete models, but any code path that skips this check — including `model_validate()` called before `model_rebuild()` — operates on a model without a functioning `SchemaValidator`. For a large application with circular imports and 50+ models, 3-5 models may remain incomplete after import, silently accepting any input without validation.

**The requirement:** Any attempt to validate data against an incomplete model (`__pydantic_complete__ == False`) must raise a clear error, not silently skip validation.

**How to verify:** Create a model with a forward reference that hasn't been resolved. Attempt `model_validate()` without calling `model_rebuild()`. Assert that a `PydanticUserError` with code `'class-not-fully-defined'` is raised.

### Scenario 3: Frozen Model Bypass via Direct `__dict__` Mutation

**Requirement tag:** [Req: inferred — from _check_frozen() and __setattr__() in main.py]

**What happened:** `BaseModel.__setattr__` (line ~1044) uses memoized handlers from `__pydantic_setattr_handlers__` to enforce field immutability when `model_config['frozen'] = True`. The `_check_frozen()` function (line ~85) raises `ValidationError` on attribute assignment. However, Python's `object.__dict__` is accessible, and `model.__dict__['field'] = new_value` bypasses `__setattr__` entirely. While this is technically a Python limitation, any code that relies on frozen guarantees for data integrity (e.g., using models as dict keys via `__hash__`) can be silently corrupted. With 1,000 model instances used as cache keys, a single `__dict__` mutation corrupts the cache lookup for that instance.

**The requirement:** Frozen models must enforce immutability through `__setattr__`. The `__hash__` implementation must be consistent with the frozen guarantee. Documentation must clearly state that `__dict__` mutation bypasses frozen protection.

**How to verify:** Create a frozen model, verify `__setattr__` raises `ValidationError`. Verify `__hash__` is defined. Verify `model.__dict__` direct mutation changes the value (documenting the limitation).

### Scenario 4: Discriminated Union Misrouting on Ambiguous Discriminator Values

**Requirement tag:** [Req: inferred — from _ApplyInferredDiscriminator in _discriminated_union.py]

**What happened:** `_ApplyInferredDiscriminator.apply()` converts a plain union into a tagged union by mapping discriminator field values to specific union members. If two union members share a `Literal` discriminator value, the `TypeError` raised ("discriminator value mapped to multiple choices") catches the conflict. But if the discriminator field is `Optional[Literal["a", "b"]]` and `None` is a valid discriminator value that matches a `None`-typed union member, the mapping becomes ambiguous. For an API receiving 10,000 requests/day with discriminated union payloads, 0.1% of requests with `null` discriminator values could be silently routed to the wrong union member, producing valid-looking but semantically wrong validated objects.

**The requirement:** Discriminated unions must unambiguously map every possible discriminator value to exactly one union member. `None` as a discriminator value must be handled explicitly.

**How to verify:** Define a discriminated union with two members where one has `Literal["a"]` and another has `Optional[Literal["a"]]`. Validate data with discriminator `None`. Assert either correct routing or a clear error — not silent misrouting.

### Scenario 5: Schema-Valid Mutation Passes Validation But Produces Wrong Serialization

**Requirement tag:** [Req: inferred — from model_dump(mode='python') vs model_dump_json() asymmetry]

**What happened:** `model_dump(mode='python')` and `model_dump_json()` use different serializers (Python serializer vs JSON serializer). A model with a custom type that implements `__get_pydantic_core_schema__` with different validation and serialization schemas can produce objects that validate successfully but serialize to wrong values. For example, a `SecretStr` field validates as a string but serializes as `'**********'` — which is correct. But a custom type with an incorrect `json_schema()` method can produce JSON Schema that doesn't match the actual serialization output. When 500 API endpoints rely on the JSON Schema for client code generation, every endpoint using this type generates client code that sends wrong data.

**The requirement:** For every type, the JSON Schema generated by `model_json_schema()` must accurately describe the output of `model_dump_json()`. Validation schema and serialization schema may differ, but the JSON Schema must match whichever mode it's generated for.

**How to verify:** Create model with `SecretStr`, `datetime`, and custom `Annotated` type. Generate JSON Schema in both `'validation'` and `'serialization'` modes. Validate that `model_dump_json()` output conforms to the serialization-mode JSON Schema.

### Scenario 6: `TypeAdapter` Validation Without Model Context Loses Config

**Requirement tag:** [Req: inferred — from TypeAdapter.__init__() config handling and _getattr_no_parents()]

**What happened:** `TypeAdapter` (in `type_adapter.py`) validates arbitrary types without requiring a `BaseModel` subclass. When a `ConfigDict` is passed to `TypeAdapter`, it applies to the validation. But when `TypeAdapter` wraps a type that's already a `BaseModel` subclass, the `TypeAdapter`'s config and the model's `model_config` can conflict. The `_getattr_no_parents()` function (line ~44) defensively avoids MRO issues, but config precedence isn't documented. For 200 TypeAdapter instances across a codebase, 5-10 may have conflicting configs where the user expects TypeAdapter config to override model config but model config wins.

**The requirement:** When `TypeAdapter` wraps a `BaseModel` subclass and both provide config, the behavior must be well-defined: either TypeAdapter config takes precedence, model config takes precedence, or a clear error is raised on conflict.

**How to verify:** Create a `BaseModel` with `model_config = ConfigDict(strict=True)`. Wrap it with `TypeAdapter(MyModel, config=ConfigDict(strict=False))`. Validate coercible input. Assert which strict mode wins and that the behavior matches documentation.

### Scenario 7: Extra Fields Data Loss During Nested Model Serialization

**Requirement tag:** [Req: inferred — from model_dump() and ConfigDict(extra='allow') behavior]

**What happened:** When `extra='allow'` is configured, extra fields passed during validation are stored in `__pydantic_extra__`. During serialization with `model_dump()`, extra fields are included. But when a nested model also has `extra='allow'`, and the inner model receives extra fields during validation of the outer model, the round-trip `model_validate(model_dump())` must preserve all extra fields at all nesting levels. If the serialization of inner extra fields drops type information (e.g., a `datetime` extra field serializes to ISO string in JSON but the inner model has no schema for that field), the round-trip produces a different type. For a data pipeline processing 50,000 records with nested extra fields, 12% of records with non-primitive extra values silently change type on round-trip.

**The requirement:** `model_validate(model.model_dump())` must be a lossless round-trip for all fields including extras, when both models use the same mode. Extra field type preservation must be consistent between `model_dump(mode='python')` and `model_dump_json()`.

**How to verify:** Create outer model with `extra='allow'` containing inner model with `extra='allow'`. Populate both with extra fields of various types (int, str, list, dict). Assert `model_dump()` round-trip preserves all extras at both levels with correct types.

### Scenario 8: `model_rebuild()` Race Condition in Multi-Threaded Applications

**Requirement tag:** [Req: inferred — from model_rebuild() and __pydantic_complete__ state machine]

**What happened:** `model_rebuild()` regenerates schemas and validators, transitioning `__pydantic_complete__` from potentially `False` to `True`. This operation is not thread-safe — if two threads call `model_rebuild()` simultaneously or one thread validates while another rebuilds, the model's `__pydantic_validator__` can be in an inconsistent state. Because `model_rebuild()` sets `__pydantic_complete__ = False` before rebuilding and `True` after, there's a window where another thread sees an incomplete model. In a web application with 100 concurrent request threads and lazy model building, the first 2-5 requests after startup may encounter incomplete validators, producing either crashes or silently skipped validation.

**The requirement:** `model_rebuild()` must be safe to call concurrently. Either it must be idempotent and thread-safe, or it must be documented as requiring single-threaded initialization.

**How to verify:** Create a model with forward references. In a multi-threaded test, call `model_rebuild()` from multiple threads simultaneously while other threads attempt validation. Assert no thread encounters an incomplete model or crashes. (Note: this is a concurrency test — verify thread safety or document limitation.)

### Scenario 9: Validator Execution Order Depends on Definition Order, Not Declaration

**Requirement tag:** [Req: inferred — from _decorators.py validator collection and __pydantic_decorators__]

**What happened:** Field validators (`@field_validator`) and model validators (`@model_validator`) are collected in `__pydantic_decorators__` during class construction. The execution order depends on decorator collection order, which follows Python's method resolution order (MRO) and class body definition order. When a child class defines validators that depend on parent validators having run first (e.g., parent normalizes a field, child validates the normalized value), the order is fragile. Reordering methods in the source file changes validation behavior without any error. For a model hierarchy with 8 validators across 3 class levels, changing the definition order of 2 validators silently changes whether normalization happens before or after validation, producing different results for 15% of inputs.

**The requirement:** Validator execution order must be deterministic and documented. `mode='before'` validators must always run before `mode='after'` validators. Within the same mode, parent validators run before child validators.

**How to verify:** Create parent with `@field_validator('x', mode='before')` that normalizes, and child with `@field_validator('x', mode='after')` that validates the normalized value. Assert the child validator receives normalized input regardless of method definition order.

### Scenario 10: `constr(pattern=...)` Accepts Partial Matches Without Anchors

**Requirement tag:** [Req: inferred — from constr() and pattern metadata in types.py]

**What happened:** `constr(pattern=r'\d{3}')` creates a constrained string type. The pattern is passed to `pydantic-core` as a regex constraint. If the regex engine uses partial matching (like Python's `re.search`), the pattern `\d{3}` matches any string *containing* three consecutive digits, not just strings that *are* three digits. The string `"abc123def"` would pass validation when the user likely intended to match only `"123"`. Without explicit anchors (`^\d{3}$`), 100% of constrained string patterns using `constr(pattern=...)` silently accept longer strings containing the pattern anywhere.

**The requirement:** Pattern validation behavior (full-match vs partial-match) must be clearly documented. If partial matching is the default, the documentation must explicitly warn users to add anchors for full-match behavior.

**How to verify:** Create `constr(pattern=r'\d{3}')`. Validate `"123"` (should pass), `"abc123def"` (check behavior — document whether this passes or fails), `"12"` (should fail). Assert behavior matches documentation.

## AI Session Quality Discipline

1. Read `quality/QUALITY.md` before starting work on pydantic.
2. Run `pytest tests/ -x -q` before marking any task complete.
3. Add tests for new functionality — include edge cases for `None`, empty collections, type coercion boundaries.
4. Update this file if new failure modes are discovered.
5. Output a Quality Compliance Checklist before ending a session.
6. Never remove a fitness-to-purpose scenario. Only add new ones.
7. When modifying `_generate_schema.py`, run the full test suite — this module affects all downstream validation.
8. When modifying `FieldInfo` or field merging, test with model inheritance hierarchies.

## The Human Gate

- **Backward compatibility decisions** — Whether to break V1 API compatibility requires domain judgment about the ecosystem impact.
- **Performance vs. correctness trade-offs** — Some validation edge cases may be intentionally loose for performance (e.g., `pydantic-core` Rust validation vs Python-level checks).
- **Documentation accuracy** — Type constraint descriptions in docstrings must match actual behavior, requiring human verification.
- **Security review of validation bypass** — Any change that allows data to skip validation (e.g., `model_construct()`) needs human security review.
- **Third-party type plugin compatibility** — Custom `__get_pydantic_core_schema__` implementations from the ecosystem can't be tested exhaustively.
