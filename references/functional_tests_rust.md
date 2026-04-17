# Functional Test Examples — Rust

Reference companion to `functional_tests.md` with all Rust/cargo test examples.

Name the test file using Rust conventions: place unit tests in a `#[cfg(test)] mod tests` block within the source file, or create integration tests in `tests/functional_test.rs`.

## Structure: Three Test Groups

Organize tests into three logical groups using modules:

```
Spec Requirements
    — One test per testable spec section
    — Each test's documentation cites the spec requirement

Fitness Scenarios
    — One test per QUALITY.md scenario (1:1 mapping)
    — Named to match: test_scenario_1_memorable_name

Boundaries and Edge Cases
    — One test per defensive pattern from Step 5
    — Targets Option/Result handling, normalization, fallbacks
```

## Import Patterns

- `use crate::module::function;` for unit tests in the same crate
- `use myproject::module::function;` for integration tests in `tests/`

Whatever pattern the existing tests use, copy it exactly. Do not guess or invent a different pattern.

## Test Setup

Helper functions in a `#[cfg(test)] mod tests` block or a `test_utils.rs` module. Use builder patterns for constructing test data. For integration tests, place files in `tests/`.

**Rule: Every fixture or test helper referenced must be defined.** If a test depends on shared setup that doesn't exist, the test will error during setup (not fail during assertion) — producing broken tests that look like they pass.

### Inline Setup (Preferred)

```rust
// Rust
#[test]
fn test_config_validation() {
    let config = Config { pipeline: Pipeline { name: "Test".into() } };
}
```

**Library version awareness:** Check the project's `Cargo.toml` to verify what's available. Use `#[ignore]` with a comment explaining the prerequisite for optional dependencies.

**After writing all tests, run the test suite and check for setup errors.** Setup errors (fixture not found, import failures) count as broken tests regardless of how the framework categorizes them.

## Spec-Derived Tests

Walk each spec document section by section. For each section, ask: "What testable requirement does this state?" Then write a test.

Each test should:
1. **Set up** — Load a fixture, create test data, configure the system
2. **Execute** — Call the function, run the pipeline, make the request
3. **Assert specific properties** the spec requires

```rust
// Rust (cargo test)
#[test]
fn test_spec_requirement_section_n_x_produces_y() {
    // [Req: formal — Design Doc §N] X should produce Y
    let result = process(&fixture);
    assert_eq!(result.property, expected_value);
}
```

## Cross-Variant Testing

If the project handles multiple input types, cross-variant coverage is where silent bugs hide. Aim for roughly 30% of tests exercising all variants.

Iterate over cases within a single test:

```rust
// Rust (cargo test) — iterate over cases
#[test]
fn test_feature_works_across_variants() {
    let variants = [variant_a(), variant_b(), variant_c()];
    for v in &variants {
        let output = process(&v.input);
        assert!(output.has_expected_property(),
            "variant {}: missing expected property", v.name);
    }
}
```

If iteration doesn't fit, write separate test functions per variant.

**Which tests should be cross-variant?** Any test verifying a property that *should* hold regardless of input type: entity identity, structural properties, required links, temporal fields, domain-specific semantics.

**After writing all tests, do a cross-variant audit.** Count cross-variant tests divided by total. If below 30%, convert more.

## Anti-Patterns — WRONG vs. RIGHT

These patterns look like tests but don't catch real bugs. Always check your Step 5b schema map before choosing mutation values.

```rust
// Rust — WRONG: tests the error, not the outcome
#[test]
fn test_bad_value_rejected() {
    let input = Fixture { field: "invalid".into(), ..default() };
    assert!(process(&input).is_err());  // Tells you nothing about output
}

// Rust — RIGHT: tests the requirement
#[test]
fn test_bad_value_not_in_output() {
    let input = Fixture { field: None, ..default() };  // Option accepts None
    let output = process(&input).expect("should succeed");
    assert!(!output.contains(bad_property));  // Bad data absent
    assert!(output.contains(expected_type));   // Rest still works
}
```

## Fitness Scenario Tests

For each scenario in QUALITY.md, write a test. This is a 1:1 mapping:

```rust
// Rust (cargo test)
#[test]
fn test_scenario_1_memorable_name() {
    // [Req: formal — QUALITY.md Scenario 1] [Name]
    // Requirement: [What the code must do]
    let result = process(&fixture);
    assert!(condition_that_prevents_the_failure(&result));
}
```

## Boundary and Negative Tests

One test per defensive pattern from Step 5. Use your Step 5b schema map when choosing mutation values. Every mutation must use a value the schema accepts.

```rust
// Rust (cargo test)
#[test]
fn test_defensive_pattern_function_name_guards_against_x() {
    // [Req: inferred — from function_name() guard] guards against X
    let input = Fixture { field: None, ..default_fixture() };
    let result = process(&input).expect("expected graceful handling");
    // Assert result is valid despite edge-case input
}
```

Systematic approach:
- **Missing fields** — Optional field absent? Set to `None`.
- **Wrong types** — Field gets different type? Use schema-valid alternative.
- **Empty values** — Empty `Vec`? Empty `String`? Empty `HashMap`?
- **Boundary values** — Zero, negative, maximum, first, last.
- **Cross-module boundaries** — Module A produces unusual but valid output — does B handle it?

If you found 10+ defensive patterns but wrote only 4 boundary tests, go back and write more. Target a 1:1 ratio.
