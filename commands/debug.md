---
description: Root-cause a failing test or a described bug — minimal reproduction, bisect, one hypothesis at a time, causal chain.
argument-hint: "<test name | file:line | description of the bug> [--fix]"
---

# TestMate — debug

Find the cause, not a workaround.

Argument: `$ARGUMENTS` — a failing test's name, a file and line, a stack trace, or a description of
wrong behaviour. `--fix` permits proposing and applying a source patch after the cause is proven.

## Rules

- **Never** make a test pass by changing the test, unless triage concludes the expectation was
  genuinely wrong — and then say so explicitly.
- **Never** patch source without `--fix` and without having proven the cause first. A change that
  makes the symptom go away is not a fix until you can say why it was happening.
- One hypothesis at a time, stated before it is tested.

## Steps

1. **Load** `testmate-config` and resolve `forbidCommands` and `reportDir` before running anything.

2. **Reproduce.** Run the exact failing case in isolation and read the real output — report files,
   full trace, sanitizer output. If it passes in isolation but fails in the suite, the cause is
   shared state; that is the bug, and it is a finding in its own right.

   If the failure is intermittent, run with repetition (`-count=10`, `--repeat until-fail:10`,
   `-race`, a loop) and report the failure rate. That number is diagnostic.

3. **Minimize.** Strip the reproduction until removing one more element makes it pass. What remains
   is the defect's shape, and it is usually recognisable at that point.

4. **Hypothesize, then test.** State the hypothesis. Add temporary instrumentation — a captured
   argument, a log line, a counter, a breakpoint-equivalent assertion — run it, read the result,
   then remove the instrumentation. Repeat. Do not shotgun changes.

5. **Bisect** if git history is available and the code used to work: find the commit that
   introduced it and read its diff.

6. **Widen.** Once you have the cause, look for its siblings — the same mistake on another path, in
   another method, in another module. The second instance of a bug is nearly always cheaper to find
   now than later. Report each one.

7. **Write the regression test** before any fix: a test that fails for exactly this reason and
   would have caught it. Follow `test-conventions` so it belongs in the suite.

## Report

State the **causal chain** with a `file:line` at every step:

> input `""` → `whereIn` at `DB.java:212` receives an empty list → the branch at `:215` returns
> without appending a predicate → the builder renders `DELETE FROM users` with no `WHERE` →
> every row is deleted.

Then: the fix in prose, the regression test you wrote, the sibling instances you found, and — only
with `--fix` — the applied patch, with the suite re-run afterwards and the result stated.

If you cannot find the cause, say so, and list what you ruled out and what you would try next.
A clear dead end is more useful than a confident guess.
