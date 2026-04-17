# Functional Test Examples — Go

Reference companion to `functional_tests.md` with all Go examples.

Name the test file using Go conventions: `functional_test.go`.

## Structure: Three Test Groups

Organize tests into three logical groups using subtests:

```
Spec Requirements
    — One test per testable spec section
    — Each test's documentation cites the spec requirement

Fitness Scenarios
    — One test per QUALITY.md scenario (1:1 mapping)
    — Named to match: TestScenario1_MemorableName

Boundaries and Edge Cases
    — One test per defensive pattern from Step 5
    — Targets null guards, error returns, normalization, fallbacks
```

## Import Patterns

Go has two distinct test patterns:

- **Same package:** test files in the same directory with `package mypackage` — gives access to unexported identifiers
- **Black-box testing:** `package mypackage_test` with explicit imports — tests only the exported API
- Internal packages may require specific import paths

Whatever pattern the existing tests use, copy it exactly. Do not guess or invent a different pattern.

## Test Setup

Helper functions in the same `_test.go` file with `t.Helper()`. Use `t.TempDir()` for temporary directories. Go convention strongly prefers inline setup — avoid shared test state.

**Rule: Every fixture or test helper referenced must be defined.** If a test depends on shared setup that doesn't exist, the test will error during setup (not fail during assertion) — producing broken tests that look like they pass.

### Inline Setup (Preferred)

```go
// Go
func TestConfigValidation(t *testing.T) {
    tmpDir := t.TempDir()
    config := Config{Pipeline: Pipeline{Name: "Test"}}
}
```

**Library version awareness:** Check the project's dependency manifest to verify what's available. Use `t.Skip()` for optional dependencies.

**After writing all tests, run the test suite and check for setup errors.** Setup errors (fixture not found, import failures) count as broken tests regardless of how the framework categorizes them.

## Spec-Derived Tests

Walk each spec document section by section. For each section, ask: "What testable requirement does this state?" Then write a test.

Each test should:
1. **Set up** — Load a fixture, create test data, configure the system
2. **Execute** — Call the function, run the pipeline, make the request
3. **Assert specific properties** the spec requires

```go
// Go (testing)
func TestSpecRequirement_SectionN_XProducesY(t *testing.T) {
    // [Req: formal — Design Doc §N] X should produce Y
    result := Process(fixture)
    if result.Property != expectedValue {
        t.Errorf("expected %v, got %v", expectedValue, result.Property)
    }
}
```

## Cross-Variant Testing

If the project handles multiple input types, cross-variant coverage is where silent bugs hide. Aim for roughly 30% of tests exercising all variants.

Go idiom: use table-driven tests:

```go
// Go (testing) — table-driven tests
func TestFeatureWorksAcrossVariants(t *testing.T) {
    variants := []Variant{variantA, variantB, variantC}
    for _, v := range variants {
        t.Run(v.Name, func(t *testing.T) {
            output := Process(v.Input)
            if !output.HasExpectedProperty() {
                t.Errorf("variant %s: missing expected property", v.Name)
            }
        })
    }
}
```

If parametrization doesn't fit, loop explicitly within a single test.

**Which tests should be cross-variant?** Any test verifying a property that *should* hold regardless of input type: entity identity, structural properties, required links, temporal fields, domain-specific semantics.

**After writing all tests, do a cross-variant audit.** Count cross-variant tests divided by total. If below 30%, convert more.

## Anti-Patterns — WRONG vs. RIGHT

These patterns look like tests but don't catch real bugs. Always check your Step 5b schema map before choosing mutation values.

```go
// Go — WRONG: tests the error, not the outcome
func TestBadValueRejected(t *testing.T) {
    fixture.Field = "invalid"  // Validator rejects this!
    _, err := Process(fixture)
    if err == nil { t.Fatal("expected error") }
    // Tells you nothing about output
}

// Go — RIGHT: tests the requirement
func TestBadValueNotInOutput(t *testing.T) {
    fixture.Field = ""  // Zero value is valid
    output, err := Process(fixture)
    if err != nil { t.Fatalf("unexpected error: %v", err) }
    if containsBadProperty(output) { t.Error("bad data should be absent") }
    if !containsExpectedType(output) { t.Error("expected data should be present") }
}
```

## Fitness Scenario Tests

For each scenario in QUALITY.md, write a test. This is a 1:1 mapping:

```go
// Go (testing)
func TestScenario1_MemorableName(t *testing.T) {
    // [Req: formal — QUALITY.md Scenario 1] [Name]
    // Requirement: [What the code must do]
    result := Process(fixture)
    if !conditionThatPreventsFailure(result) {
        t.Error("scenario 1 failed: [describe expected behavior]")
    }
}
```

## Boundary and Negative Tests

One test per defensive pattern from Step 5. Use your Step 5b schema map when choosing mutation values. Every mutation must use a value the schema accepts.

```go
// Go (testing)
func TestDefensivePattern_FunctionName_GuardsAgainstX(t *testing.T) {
    // [Req: inferred — from FunctionName() guard] guards against X
    input := defaultFixture()
    input.Field = nil  // Trigger defensive code path
    result, err := Process(input)
    if err != nil {
        t.Fatalf("expected graceful handling, got: %v", err)
    }
    // Assert result is valid despite edge-case input
}
```

Systematic approach:
- **Missing fields** — Optional field absent? Set to nil or zero value.
- **Wrong types** — Field gets different type? Use schema-valid alternative.
- **Empty values** — Empty slice? Empty string? nil map?
- **Boundary values** — Zero, negative, maximum, first, last.
- **Cross-module boundaries** — Module A produces unusual but valid output — does B handle it?

If you found 10+ defensive patterns but wrote only 4 boundary tests, go back and write more. Target a 1:1 ratio.
