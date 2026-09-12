---
description: Generate adversarial tests for the project, a path, a file or a symbol; run them; triage every failure. Levels low/standard/high/max, default high.
argument-hint: "[path | file | Class#method] [--level low|standard|high|max] [--dry-run]"
---

# TestMate — test

The main command. Generate tests that try to break the target, run them, and triage what fails.

Arguments: `$ARGUMENTS`

- **Target** — a path, a file, a `Class#method` / `module.function`, or nothing for the whole project.
- **`--level`** — `low`, `standard`, `high` (default), `max`. Never assume a level other than `high`
  unless it is given here or set in `.testmate/config.json`.
- **`--dry-run`** — design the cases and show them, write no files.

## The rule that governs this command

**A generated test that fails is a finding until proven otherwise.** Nothing in this run may
weaken, skip or delete a test to reach green, and nothing may patch source code. If the suite ends
red with every failure correctly explained, the run succeeded.

## Steps

1. **Load** `testmate-config` first and resolve the configuration — the level (an explicit
   `--level` wins over `roots[].level`, which wins over `level`, which defaults to `high`),
   `exclude`, `forbidCommands`, `reportDir`, `allowDependencyChanges`. Then load `test-strategy`,
   `test-conventions`, `stack-adapters`, `attack-catalog`, `failure-triage`.

   Pass `forbidCommands` to every agent you spawn that holds `Bash`.

2. **Recon** — run `testmate-recon` on the target unless a profile from a `/testmate:scan` earlier
   in this conversation is still accurate. Note any pre-existing test failures now, so they are
   never attributed to this run.

3. **Design** — run `testmate-adversary` on the target to get the ranked case list. For a
   multi-file target, run one adversary per module in parallel. Filter the list to the families the
   level allows (`test-strategy`).

   If `--dry-run`, present the case list here and stop.

4. **Write** — run `testmate-author`, one per module, in parallel for independent modules. Pass it
   the stack profile, the convention profile and that module's case list. Authors write tests only;
   they never touch source or build files.

5. **Run and triage** — run `testmate-runner`. It establishes the baseline, runs narrow then wide,
   isolates each failure, assigns a verdict per `failure-triage`, fixes only fixture defects, and
   runs the full suite twice at the end.

6. **At level `max` only** — after the suite is green-or-explained, run mutation testing on the
   target and add tests for surviving mutants, then re-run. If no mutation tool is configured, say
   so and recommend the one from the adapter rather than adding it yourself.

## Report

Write the findings report to `<reportDir>/<ISO-date>-<target>.md` — `reportDir` resolved from
config, default `.testmate/reports` — in the format from `failure-triage`, and summarise in chat:

- Files created or extended, and the case count in each.
- Counts: generated / passing / failing, and the verdict breakdown.
- **Findings, most severe first.** Each with the test that proves it, the contract it violates
  (`file:line`), the concrete input, expected vs. actual, and the impact in plain terms —
  *"returns every row when the caller passed an empty filter list"*, not *"incorrect behaviour"*.
- **Design questions** — the `UNDECIDED` cases. Often the most useful section.
- **Testability findings** — where the design made a correct test impossible.
- **Not covered** — cases skipped, families deliberately not probed and why, dependencies that
  would be needed. Never let a gap go unstated.

Then offer next steps: `/testmate:debug <test>` to root-cause a specific failure, a level bump, or
the next target down the risk list. Propose source fixes only if the user asks — and then one at a
time, each with the failing test as its proof.
