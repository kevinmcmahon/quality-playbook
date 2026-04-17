# Functional Test Examples — TypeScript

Reference companion to `functional_tests.md` with all TypeScript/JavaScript examples covering both Jest and Vitest.

Name the test file using project conventions: `functional.test.ts` (Jest) or `functional.test.ts` (Vitest).

## Structure: Three Test Groups

Organize tests into three logical groups using describe blocks:

```
Spec Requirements
    — One test per testable spec section
    — Each test's documentation cites the spec requirement

Fitness Scenarios
    — One test per QUALITY.md scenario (1:1 mapping)
    — Named to match: test('[Req: ...] scenario name', ...)

Boundaries and Edge Cases
    — One test per defensive pattern from Step 5
    — Targets null guards, try/catch, normalization, fallbacks
```

## Import Patterns

- `import { func } from '../src/module'` with relative paths
- Path aliases from `tsconfig.json` (e.g., `@/module`)

Whatever pattern the existing tests use, copy it exactly. Do not guess or invent a different pattern.

## Test Setup

**Jest:** Use `beforeAll`/`beforeEach` in the test file, or create a `quality/testUtils.ts` with factory functions.

**Vitest:** Same approach — `beforeAll`/`beforeEach` in the test file, or shared utilities. Vitest is API-compatible with Jest for setup/teardown hooks.

**Rule: Every fixture or test helper referenced must be defined.** If a test depends on shared setup that doesn't exist, the test will error during setup (not fail during assertion) — producing broken tests that look like they pass.

### Inline Setup (Preferred)

```typescript
// TypeScript
test('config validation', () => {
    const config = { pipeline: { name: 'Test', steps: [] } };
});
```

**Library version awareness:** Check the project's `package.json` to verify what's available. Use conditional `describe.skip` for optional dependencies.

**After writing all tests, run the test suite and check for setup errors.** Setup errors (fixture not found, import failures) count as broken tests regardless of how the framework categorizes them.

## Spec-Derived Tests

Walk each spec document section by section. For each section, ask: "What testable requirement does this state?" Then write a test.

Each test should:
1. **Set up** — Load a fixture, create test data, configure the system
2. **Execute** — Call the function, run the pipeline, make the request
3. **Assert specific properties** the spec requires

```typescript
// TypeScript (Jest)
describe('Spec Requirements', () => {
  test('[Req: formal — Design Doc §N] X should produce Y', () => {
    const result = process(fixture);
    expect(result.property).toBe(expectedValue);
  });
});
```

For Vitest, the syntax is identical — `describe`, `test`, and `expect` work the same way. Import from `vitest` instead of relying on Jest globals:

```typescript
// TypeScript (Vitest)
import { describe, test, expect } from 'vitest';

describe('Spec Requirements', () => {
  test('[Req: formal — Design Doc §N] X should produce Y', () => {
    const result = process(fixture);
    expect(result.property).toBe(expectedValue);
  });
});
```

## Cross-Variant Testing

If the project handles multiple input types, cross-variant coverage is where silent bugs hide. Aim for roughly 30% of tests exercising all variants.

```typescript
// TypeScript (Jest)
test.each([variantA, variantB, variantC])(
  'feature works for %s', (variant) => {
    const output = process(variant.input);
    expect(output).toHaveProperty('expectedProperty');
});
```

For Vitest, `test.each` works identically.

If parametrization doesn't fit, loop explicitly within a single test.

**Which tests should be cross-variant?** Any test verifying a property that *should* hold regardless of input type: entity identity, structural properties, required links, temporal fields, domain-specific semantics.

**After writing all tests, do a cross-variant audit.** Count cross-variant tests divided by total. If below 30%, convert more.

## Anti-Patterns — WRONG vs. RIGHT

These patterns look like tests but don't catch real bugs. Always check your Step 5b schema map before choosing mutation values.

```typescript
// TypeScript — WRONG: tests the validation mechanism
test('bad value rejected', () => {
    fixture.field = 'invalid';  // Zod schema rejects this!
    expect(() => process(fixture)).toThrow(ZodError);
    // Tells you nothing about output
});

// TypeScript — RIGHT: tests the requirement
test('bad value not in output', () => {
    fixture.field = undefined;  // Schema accepts undefined for optional
    const output = process(fixture);
    expect(output).not.toContain(badProperty);  // Bad data absent
    expect(output).toContain(expectedType);      // Rest still works
});
```

## Fitness Scenario Tests

For each scenario in QUALITY.md, write a test. This is a 1:1 mapping:

```typescript
// TypeScript (Jest)
describe('Fitness Scenarios', () => {
  test('[Req: formal — QUALITY.md Scenario 1] [Name]', () => {
    const result = process(fixture);
    expect(conditionThatPreventsFailure(result)).toBe(true);
  });
});
```

For Vitest, use the same structure with `import { describe, test, expect } from 'vitest'`.

## Boundary and Negative Tests

One test per defensive pattern from Step 5. Use your Step 5b schema map when choosing mutation values. Every mutation must use a value the schema accepts.

```typescript
// TypeScript (Jest)
describe('Boundaries and Edge Cases', () => {
  test('[Req: inferred — from functionName() guard] guards against X', () => {
    const input = { ...validFixture, field: null };
    const result = process(input);
    expect(result).not.toContainBadOutput();
  });
});
```

For Vitest, the syntax is the same. Custom matchers are registered via `expect.extend()` in both frameworks.

Systematic approach:
- **Missing fields** — Optional field absent? Set to undefined or null.
- **Wrong types** — Field gets different type? Use schema-valid alternative.
- **Empty values** — Empty array? Empty string? Empty object?
- **Boundary values** — Zero, negative, maximum, first, last.
- **Cross-module boundaries** — Module A produces unusual but valid output — does B handle it?

If you found 10+ defensive patterns but wrote only 4 boundary tests, go back and write more. Target a 1:1 ratio.
