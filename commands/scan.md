---
description: Profile this project for testing — stack, existing conventions, risk hot-spots — and propose a plan. Writes nothing.
argument-hint: "[path] (default: whole project)"
---

# TestMate — scan

Read-only reconnaissance. **Create no files, modify no files, add no dependencies.** The output is
a plan the user approves before anything is written.

Target: `$ARGUMENTS` (default: the whole project).

## Steps

1. Load `testmate-config` first and resolve the configuration — level, `exclude`, `forbidCommands`,
   `reportDir`. Then load the `stack-adapters`, `test-conventions` and `test-strategy` skills.
2. Run the `testmate-recon` agent on the target. If the project has clearly separate source roots
   (a backend and a frontend, several services in a monorepo), run one recon agent per root, in
   parallel, and keep the profiles separate.
3. Fold the resolved configuration into the plan: the level that would apply and where it came
   from, and which paths `exclude` removes from the target set.

## Report

Present, in this order and no longer than it needs to be:

**Stack** — one block per source root: language, build tool, runner, assertion and mocking
libraries, what is already available for coverage / property-based / mutation / containers, and the
exact command that runs the suite here.

**Current posture** — how many tests exist, what they cover, and — the question that matters — how
many of them assert a *refusal*. A suite of pure happy-path tests passes unchanged after someone
deletes a validator; say so if that is what you found.

**Conventions** — the house style you would match, with one concrete example lifted from the repo.
Where there is no precedent, the adapter defaults you would adopt.

**Risk hot-spots** — the ranked list from recon, top 10-15, one line each: what it is, why it
scores, and which attack families apply to it.

**Hazards** — pre-existing failing tests, a suite that needs a live service, anything destructive,
anything that cannot run in this environment. Be explicit that pre-existing failures are not
TestMate's.

**Proposed plan** — what `/testmate:test` would do at the default level `high`: which files, roughly
how many cases, which families, and what it would cost in wall-clock time. Then offer the choices:

- run `/testmate:test <top hot-spot>` to start narrow on the highest-risk file
- run `/testmate:audit` to get the findings report without writing any tests
- run `/testmate:test` on everything at level `high`
- pick a different level — `low`, `standard`, `high` (default), `max`

End by asking which, rather than starting work.
