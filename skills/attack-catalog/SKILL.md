---
name: attack-catalog
description: Language-independent catalogue of vulnerability and defect families, each mapped to a concrete test shape. The source of TestMate's adversarial cases at level high and max. Load before writing adversarial tests or running an audit.
---

# Attack catalogue

A catalogue of ways software breaks, expressed as **test shapes** that are independent of language
and framework. A stack adapter translates a shape into idiom; the shape itself never changes.

## How to use it

1. Read the unit under test and identify its **surfaces**: what crosses its boundary — strings that
   become identifiers or code, values that become paths, bytes that become objects, a caller
   identity, shared mutable state, an external handle, an environment-dependent operation.
2. For each surface, load the matching reference below and pick the families that apply.
3. For each family, write the test shape. **Assert the refusal, not the outcome** — a guard that
   throws is proven by a test that demands the throw.
4. If a family does not apply, say why in the report rather than silently skipping it. "No SQL is
   constructed here" is a useful line in a findings report.

## References

| File | Covers | Applies when the unit… |
|---|---|---|
| `references/injection.md` | SQL, command, path, template, header, log, deserialization, XSS | builds a string that is later interpreted by another engine |
| `references/authz.md` | authn/authz bypass, IDOR, privilege escalation, tenant leakage | makes a decision about who may do what |
| `references/boundaries.md` | numeric limits, off-by-one, empty & huge collections, precision, unbounded input | accepts a number, a size, a range or a collection |
| `references/concurrency.md` | races, TOCTOU, deadlock, non-atomic updates, unsafe caching | touches shared mutable state or is documented as thread-safe |
| `references/resources.md` | leaks on error paths, double-close, unbounded growth, missing timeouts | acquires a connection, file, socket, lock or thread |
| `references/environment.md` | locale, timezone/DST, charset, line endings, dialect and platform variance | formats, parses, compares or renders anything |
| `references/silent-wrongness.md` | plausible wrong answers instead of loud failures | is the highest-value family — always consider it |

## The refusal-test principle

The single most valuable thing this catalogue produces is a **safety suite**: one test file per
module in which every test asserts that a bad input is *rejected*.

```
for each guard the code claims:
    give it exactly the input the guard exists to stop
    assert the specific failure type, not a generic one
    assert nothing was mutated / nothing was executed / nothing leaked
```

Suites that only test happy paths pass just as well after someone deletes a validator. A refusal
suite does not. When in doubt about what to write next at level `high`, write another refusal test.

## Severity

Rate each finding for the report:

- **high** — untrusted input reaches an interpreter, an authorization decision can be skipped,
  data can be destroyed or corrupted without a guard, or a secret can leak.
- **medium** — wrong results returned silently, resource exhaustion reachable by a caller, a race
  that corrupts state under realistic load.
- **low** — a loud failure with a poor message, a defensible-but-undocumented edge behaviour,
  an inefficiency.
