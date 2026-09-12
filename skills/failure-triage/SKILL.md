---
name: failure-triage
description: How TestMate classifies a failing generated test — real bug in the code, wrong expectation in the test, or a broken fixture — and what evidence each verdict requires. Load whenever a generated test fails.
---

# Failure triage

A red test is a question, not a chore. Answer it with evidence before touching anything.

## Never

- Never relax an assertion, widen an expected type, or delete a case to get to green.
- Never add `@Disabled` / `skip` / `xit` to silence a failure.
- Never "fix" the source to satisfy a test whose expectation you have not justified.
- Never report a suite as passing when cases were removed to make it pass.

## The four verdicts

### 1. `BUG` — the code is wrong
The test encodes a rule the code itself claims (a docstring, a guard elsewhere, a named exception
type, an obvious invariant) and the code does not honour it.

Required evidence: the claim's source (file:line), the failing assertion, the actual value, and a
minimal reproduction independent of the test framework where possible.

Action: keep the test failing. Report it. Propose a source patch only if the user asked for fixes —
never apply one unprompted.

**The assertion survives the fix you are recommending.** There is exactly one line of reasoning that
talks a careful engineer into rewriting a red assertion, and it sounds responsible: *the fix I am
proposing changes the behaviour, so under that fix the current assertion would be wrong — I should
update it to match.* Refuse it. The assertion is the record of what was broken and the only thing
that will tell you the fix worked; rewriting it in the same breath as proposing the fix destroys the
evidence and the check at once, and produces a green suite that has verified nothing. This holds
however defensible the new behaviour is, and it holds for offering the rewrite as an option.

If your recommended fix genuinely changes the contract, say so in those words and stop there: report
the `BUG`, propose the source change, and state that the test will need revisiting **after** the fix
lands and the user has accepted the new contract. That is a separate piece of work, on the user's
say-so, against a passing suite — not a paragraph at the end of a triage.

### 2. `EXPECTATION` — the test is wrong
The code's actual behaviour is defensible and intentional; the test asserted something the unit
never promised.

Required evidence: what in the code establishes the real contract. "It's what the code does" is
**not** evidence — that reasoning turns every bug into a feature. If the only support for the
current behaviour is the current behaviour, the verdict is `UNDECIDED`, not `EXPECTATION`.

Action: correct the test to assert the real contract, and note the correction in the report.

### 3. `FIXTURE` — the test harness is wrong
Compilation error, wrong import, misused mock, missing schema, unseeded data, a leaked fixture from
another test, a wrong assumption about setup.

Action: fix it silently and move on. This is the only category that needs no report entry — though
if the fixture problem is "tests leak state into each other", that is a `BUG` in the suite and does
get reported.

### 4. `UNDECIDED` — the contract is genuinely unspecified
Neither the code nor the docs nor the tests say what should happen. Common for: empty collections,
`null` in the middle of a chain, duplicate keys, integer overflow, unicode normalization.

Action: this is usually the most valuable finding in a run. Report it as a **design question** with
the concrete input, the current behaviour, and the plausible alternatives. Leave the test in the
suite pinned to current behaviour with a comment marking it as characterization, not specification
— clearly labelled so nobody mistakes it for an intended guarantee.

## Procedure

1. Re-run the single failing test in isolation. If it passes alone, the verdict is `FIXTURE`
   (shared state) — and the leak is itself a finding.
2. Read the code path the assertion exercises. Do not guess from the error message.
3. Look for a stated contract: doc comment, type signature, a sibling guard, an exception class
   named for exactly this condition, an existing test asserting the neighbouring case.
4. Assign a verdict from the four above. If torn between `BUG` and `EXPECTATION`, it is `UNDECIDED`.
5. Record it in the findings report.

## Findings report format

Write to `<reportDir>/<ISO-date>-<target>.md` — `reportDir` resolved by `testmate-config`,
default `.testmate/reports` — and summarise in chat.

```markdown
# TestMate run — <target> — level <level>

Generated <n> tests · <p> passing · <f> failing
Verdicts: <b> BUG · <e> EXPECTATION · <u> UNDECIDED · <x> FIXTURE (resolved)

## BUG-1 · <one-line statement of the defect>  [severity: high|medium|low]
- **Test:** `path/to/Test.java::methodName`
- **Contract:** <where the code promises this> (`src/main/.../Thing.java:88`)
- **Input:** <the minimal input>
- **Expected / Actual:** <…> / <…>
- **Impact:** <what a caller suffers — data loss, injection, wrong result silently returned>
- **Fix sketch:** <one or two sentences; no patch unless requested>
```

Order findings by severity, then by blast radius. Security findings (anything from
`skills/attack-catalog/references/injection.md` or `skills/attack-catalog/references/authz.md`) outrank correctness findings at equal
severity. A run that found nothing says so plainly and lists what it probed, so the user can judge
whether the probe was good enough.
