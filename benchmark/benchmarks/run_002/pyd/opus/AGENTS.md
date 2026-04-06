# AGENTS.md — Pydantic

## Project Description

Pydantic is the most widely-used data validation library for Python. It uses Python type hints to define data models that validate, serialize, and generate JSON Schemas at runtime. Pydantic V2 is a ground-up rewrite with a Rust-based core (`pydantic-core`) for performance.

**One sentence:** Pydantic converts Python type annotations into runtime data validation, serialization, and JSON Schema generation.

## Setup

```bash
# Clone and install in development mode
git clone https://github.com/pydantic/pydantic.git
cd pydantic

# Install with dev dependencies (prefer uv)
uv pip install -e ".[dev]"
# OR with pip
pip install -e ".[dev]"
```

**Requirements:**
- Python 3.9+
- `pydantic-core==2.44.0` (pinned exact version)
- `typing-extensions>=4.14.1`
- `annotated-types>=0.6.0`
- `typing-inspection>=0.4.2`

## Build & Test

```bash
# Run full test suite
pytest tests/ -x -q

# Run specific test file
pytest tests/test_main.py -v

# Run quality playbook tests
pytest quality/test_functional.py -v

# Linting
ruff check pydantic/
ruff format --check pydantic/

# Type checking (selected files)
pyright tests/test_pipeline.py
```

## Architecture Overview

### Core Pipeline

```
Python Type Hints → GenerateSchema → CoreSchema → pydantic-core (Rust)
                                                    ├── SchemaValidator
                                                    └── SchemaSerializer
```

### Key Subsystems (5 core modules)

1. **`pydantic/main.py`** — `BaseModel` class. Public API surface: `__init__`, `model_validate()`, `model_dump()`, `model_dump_json()`, `model_json_schema()`, `model_rebuild()`, `model_copy()`, `model_construct()`.

2. **`pydantic/_internal/_generate_schema.py`** — `GenerateSchema` class (~4000 lines). Converts Python types to `pydantic-core` `CoreSchema` objects. Handles unions, optionals, literals, annotated types, recursive types, generics, dataclasses, and custom types via `__get_pydantic_core_schema__`.

3. **`pydantic/fields.py`** — `FieldInfo` class and `Field()` function. Stores field metadata (constraints, aliases, defaults, deprecation). `merge_field_infos()` handles inheritance.

4. **`pydantic/_internal/_model_construction.py`** — `ModelMetaclass`. Orchestrates field collection, schema generation, and validator/serializer binding during class creation. Manages `__pydantic_complete__` state machine.

5. **`pydantic/types.py`** — 60+ constrained types (`conint`, `confloat`, `constr`, `SecretStr`, network types, etc.). Each type implements `__get_pydantic_core_schema__` to produce correct validation schemas.

### Additional Important Modules

- **`pydantic/_internal/_discriminated_union.py`** — Tagged union resolution
- **`pydantic/_internal/_decorators.py`** — Validator/serializer decorator processing
- **`pydantic/json_schema.py`** — JSON Schema generation from CoreSchema
- **`pydantic/type_adapter.py`** — TypeAdapter for non-model type validation
- **`pydantic/config.py`** — ConfigDict configuration system
- **`pydantic/errors.py`** — Error hierarchy with ~40 specific error codes
- **`pydantic/root_model.py`** — RootModel for single-value models
- **`pydantic/generics.py`** — Generic model support

### Data Flow

1. User defines `class MyModel(BaseModel)` with type-annotated fields
2. `ModelMetaclass.__new__()` collects fields, processes decorators
3. `GenerateSchema` converts each field's type to a `CoreSchema`
4. `pydantic-core` (Rust) compiles `CoreSchema` into `SchemaValidator` and `SchemaSerializer`
5. `MyModel(data=...)` calls `SchemaValidator.validate_python(data)`
6. `model_dump()` calls `SchemaSerializer.to_python()`
7. `model_json_schema()` generates JSON Schema from `CoreSchema`

## Key Design Decisions

- **Rust core (`pydantic-core`):** Validation and serialization are in Rust for performance. Python code handles schema generation and metaprogramming. This means validation bugs may be in Rust code, not Python.
- **Lazy schema generation:** Models with forward references start with `__pydantic_complete__ = False` and build schemas lazily via `model_rebuild()`.
- **Sentinel values:** `PydanticUndefined` and `MISSING` sentinels distinguish "not provided" from `None`. Getting sentinel comparisons wrong silently changes behavior.
- **Memoized setattr handlers:** `__pydantic_setattr_handlers__` caches attribute setter functions for performance. Stale cache entries could bypass frozen checks.
- **V1 compatibility:** Full V1 implementation available as `pydantic.v1`. Deprecated V1 APIs emit warnings.

## Known Quirks

- `model_construct()` creates instances without any validation — use only when you trust the data completely.
- `ConfigDict(extra='allow')` stores extra fields in `__pydantic_extra__`, not `__dict__`.
- `constr(pattern=...)` uses the `pydantic-core` regex engine, which may differ from Python's `re` module for some patterns.
- Frozen models prevent `__setattr__` but Python's `object.__dict__` mutation still works (Python limitation).
- `model_rebuild()` is not thread-safe — call it during single-threaded initialization.

## Quality Docs

- **Quality constitution:** `quality/QUALITY.md` — Read this first. Defines fitness-to-purpose scenarios and coverage targets.
- **Functional tests:** `quality/test_functional.py` — 50 automated tests covering specs, scenarios, and boundary conditions.
- **Code review protocol:** `quality/RUN_CODE_REVIEW.md` — 8 focus areas with guardrails.
- **Integration test protocol:** `quality/RUN_INTEGRATION_TESTS.md` — 8-test matrix with quality gates.
- **Spec audit protocol:** `quality/RUN_SPEC_AUDIT.md` — Council of Three audit with 10 scrutiny areas.

### Running Quality Tests

```bash
# Run all quality tests
pytest quality/test_functional.py -v

# Run specific test group
pytest quality/test_functional.py::TestSpecRequirements -v
pytest quality/test_functional.py::TestFitnessScenarios -v
pytest quality/test_functional.py::TestBoundariesAndEdgeCases -v
```
