---
name: test-strategy
description: TestMate's rigor levels (low / standard / high / max), the test taxonomy each level unlocks, hermeticity rules, and how to pick targets. Load before generating or planning any test work with TestMate.
---

# TestMate Test Strategy

## The prime directive

**A generated test that fails is a finding until proven otherwise.**

Never weaken, delete, `@Disabled`/`skip`, or loosen the assertion of a test in order to make a
suite green. If a test fails, hand it to `failure-triage`. The only thing that may be silently
corrected is a test that does not *compile/parse* or that mis-uses the test framework — a
mechanical defect, not a disagreement about behaviour.

## Levels

Levels are cumulative: `high` includes everything in `standard`, which includes `low`.
**`high` is the default** when the user does not say otherwise.

### low — smoke
Cheap proof the unit is wired up at all.
- Happy path for each public entry point.
- Null / empty / absent / zero arguments.
- Constructor & factory sanity; object is usable after construction.

Use when: a spike, a throwaway script, or the user explicitly wants speed.

### standard — correctness
What a careful engineer writes before merging.
- Boundary values: 0, 1, n-1, n, n+1, min/max of the type, empty and single-element collections.
- Every declared error path: each thrown exception / returned error / rejected promise is
  provoked deliberately and asserted by **type and message**, not just "it threw".
- Collaborator interaction: mock or stub dependencies, assert the calls made to them
  (arguments captured, not just invocation counts).
- State invariants: the object is left in a valid state after a failed operation.
- Round-trip / idempotence: `parse(render(x)) == x`, applying twice == applying once.

### high — adversarial *(default)*
Everything above, plus an attempt to *break* the code. Drive this from `attack-catalog`.
- **Refusal tests.** For every guard the code claims to have, assert it actually refuses.
  This is the highest-value category and the one most suites omit. Model it on a
  dedicated `…SafetyTest` / `…_safety` file per module.
- Injection families relevant to the code under test (SQL, command, path, template, header,
  deserialization, log). See `skills/attack-catalog/references/injection.md`.
- Authorization bypass: same operation as a different principal, missing principal, and a
  principal whose scope was checked on one field but applied to another.
- Concurrency: two callers racing the same mutable state; check-then-act (TOCTOU) windows.
- Resource lifecycle: connections/handles/streams released on the *error* path, not just success.
- Environment variance: locale (`Locale.TR` for `toUpperCase`), timezone/DST, charset, line
  endings, and — for anything that renders a dialect/target language — every supported dialect.
- **"Silently wrong" hunting.** The most valuable regression tests are cases that return a
  plausible-looking wrong answer instead of failing loudly. Actively look for them: a filter
  that silently drops when its argument list is empty, a quote function applied to a whole
  qualified name instead of per segment, a numeric conversion that truncates.

Also at this level: **run the suite, triage every failure, produce a findings report.**

### max — proof
Everything above, plus evidence that the suite is itself any good.
- Property-based / generative tests for pure functions and parsers (jqwik, Hypothesis,
  fast-check, proptest, gopter). Encode invariants, not examples.
- Fuzzing for anything that consumes untrusted bytes or text.
- **Mutation testing** (PIT, Stryker, mutmut, cargo-mutants). Surviving mutants are reported as
  suite gaps and each one gets a test written for it. This is the only honest answer to
  "are my tests good?" — coverage is not.
- Integration against real dependencies in containers (Testcontainers or equivalent), not
  in-memory fakes, for at least the persistence and HTTP boundaries.
- Resource exhaustion: very large inputs, deep nesting, many concurrent callers.
- Public API contract snapshot, so an accidental signature/serialization change fails a test.

## Hermeticity rules — non-negotiable

Every test TestMate writes must be:
1. **Isolated.** Fresh fixture per test. Never share mutable state between tests; never depend on
   execution order. (Reference pattern: an in-memory DB whose name contains a fresh UUID per test.)
2. **Offline.** No real network, no real cloud, no real SMTP. Use a local fake, an interceptor,
   or a container started by the test itself.
3. **Credential-free.** Never read a real secret, never point at a URL from a production config.
   If a test needs a dependency, it starts its own.
4. **Deterministic.** Inject the clock, the RNG seed, the locale and the timezone. A test that
   passes in Tbilisi and fails in UTC is a bug in the test.
5. **Non-destructive.** A destructive scenario is exercised against a throwaway fixture the test
   created. Never against anything named in the project's runtime configuration.

## Choosing targets

| User says | Target set |
|---|---|
| nothing / "the project" | Public API surface first, then risk hot-spots from recon, ordered by blast radius. |
| a directory | Every source file under it that has behaviour worth asserting. |
| a file | That file's public surface, plus the private paths reachable only through it. |
| `Class#method` / `module.func` | That symbol, exhaustively, at the requested level. |

Skip: generated code, vendored dependencies, pure DTOs with no logic, and anything already
covered by an existing test asserting the same thing — extend the existing test file instead of
creating a parallel one.

## Budget

Tests are read more than written. Prefer 20 sharp tests with one concern each and a
sentence-style name over 100 shallow ones. If a test does not distinguish a working
implementation from a broken one, delete it.
