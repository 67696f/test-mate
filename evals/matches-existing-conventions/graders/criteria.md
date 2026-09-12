---
type: llm
weight: 1
---

Generated tests that do not look like the surrounding tests get deleted by reviewers. This case
checks the house style is mirrored rather than replaced with framework defaults.

Passes if ALL of:

- The new tests extend or reuse `DBTestBase` and the `db` field — they do NOT construct a second
  fixture, a new in-memory database, or a fresh `@BeforeEach` setup of their own.
- They use `assertThatThrownBy(...).isInstanceOf(...)` — AssertJ — for the refusal, not
  `assertThrows`, not `try/fail`, not a bare JUnit assertion.
- Each test carries a `@DisplayName` written as a sentence stating the rule being enforced.
- Method names are terse camelCase phrases consistent with `tableRejectsInjection`.
- It asserts a specific exception type rather than a generic `Exception` or `RuntimeException`.
- **No control flow inside a test body.** If the same assertion is run over several inputs (each
  `LikeMode`, several wildcard strings), it uses `@ParameterizedTest` with a source — NOT a `for`
  loop, a `switch`, or an `if` inside the test method. A loop hides which input failed and stops at
  the first failure.

Strong signal (not required): it also includes a positive counterpart proving a legitimate value
without wildcards is still accepted.

Fails if it invents a parallel fixture, switches assertion library, omits the display names, or puts
a loop or conditional inside a test body instead of parameterizing.

Inventing a plausible exception class name that the prompt did not supply is acceptable, provided the
assumption is stated.
