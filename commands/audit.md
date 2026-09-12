---
description: Read-only vulnerability and weak-spot hunt across the target. Produces a ranked findings report. Writes no tests and no code.
argument-hint: "[path | file] [--families injection,authz,concurrency,...]"
---

# TestMate — audit

Find the holes, write nothing. Use this when the user wants to know what is wrong before deciding
whether to invest in tests, or when the codebase is not yet in a state where tests can run.

Target: `$ARGUMENTS` (default: the whole project).

**Read-only.** Create no files except the report itself. Modify nothing. Run no build commands
other than read-only static analysis the project already has configured.

## Steps

1. Load `attack-catalog` and its references, plus `stack-adapters` for language-specific hazards.
2. Run `testmate-recon` for the stack profile and the risk ranking.
3. Run `testmate-adversary` across the ranked targets — in parallel across modules. Ask for the
   full case list including `confidence` ratings.
4. **Verify before reporting.** For each case rated `likely-bug`, read the code path yourself and
   confirm the defect is real. An audit that reports plausible-sounding non-issues is worse than no
   audit, because the next one gets ignored. Downgrade anything you cannot confirm to
   "unverified — needs a test to settle it".
5. If the project has linters, type checkers or sanitizer configurations already set up, run them
   and fold confirmed results in. Do not install anything.

## Report

Write to `.testmate/reports/<ISO-date>-audit.md` and summarise in chat.

Order by severity (`attack-catalog` defines the three levels), security ahead of correctness at
equal severity. For each finding:

```markdown
## <severity> · <family> · <one-line statement of the defect>
- **Where:** `src/.../Thing.java:88`
- **Reachable by:** <who can trigger it, and through which entry point>
- **Input:** <the concrete input that triggers it>
- **What happens:** <the actual consequence — data loss, injection, a wrong answer returned silently>
- **Why it is a defect:** <the contract it violates, quoted or cited>
- **Confirmed:** yes (read the path) | unverified (needs a test)
- **Proving test:** <the one-line description of the test that would demonstrate it>
```

Close with:

- **What was probed and found clean** — per family, so the reader knows the shape of the audit.
- **What was not probed** and why: out of scope, no access, needs a running system.
- An offer: `/testmate:harden` turns every finding above into a failing test that proves it.

Never speculate. A finding you cannot tie to a code path is a note in a "worth checking" list, not
a finding.
