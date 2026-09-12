---
description: Turn audit findings into a refusal test suite that proves each hole. Tests that fail are your confirmed bugs.
argument-hint: "[report path | path | file]"
---

# TestMate — harden

Take findings and make them executable. Every finding becomes a test that asserts the code
*refuses* the bad input. The tests that fail are the findings that were real.

Argument: `$ARGUMENTS` — a report path under `.testmate/reports/`, or a code path to audit first.

## Steps

1. If given a report, read it. If given a code path with no report, run `/testmate:audit` on it
   first and use those findings. If the user ran an audit earlier in this conversation, reuse it.
2. Load `attack-catalog`, `test-conventions`, `stack-adapters`, `failure-triage`.
3. Run `testmate-recon` for the convention and stack profile if you do not already have it.
4. Run `testmate-author` with a case list built **one case per finding**, plus the positive
   counterpart for each — legitimate input on the same path must still succeed.

   Collect them in a dedicated safety file per module (`<Area>SafetyTest` or the stack's
   equivalent), so a reviewer reads the module's guarantees as one list. Each test's display name
   states the rule being enforced, and carries the finding id from the report in a comment.

5. Run `testmate-runner`. **Expect failures — that is the deliverable.** Every failing test here is
   a finding that just graduated from "suspected" to "demonstrated". Triage them anyway per
   `failure-triage`: a finding that turns out to be already guarded becomes `EXPECTATION`, and the
   test stays as a regression guard proving the guard exists.

## Report

Summarise as a scoreboard, because that is what the user wants from this command:

| Finding | Test | Result | Verdict |
|---|---|---|---|
| BUG-1 empty filter list silently dropped | `DBSafetyTest#whereInRejectsEmpty` | **FAILED** | confirmed bug |
| BUG-2 identifier allowlist not anchored | `DBSafetyTest#tableRejectsInjection` | passed | already guarded — kept as a regression test |

Then:

- **Confirmed** — the failing tests, ordered by severity, each with the concrete impact.
- **Already guarded** — findings that turned out to be covered. Say it plainly; a false alarm
  reported honestly is what makes the confirmed list credible.
- **Could not be tested** — findings with no testability seam, or needing a dependency the project
  does not have. These stay findings; they just have no proof yet.

Leave every failing test in the suite, red. Do not propose fixes unless asked — and if asked, take
them one at a time, each with its failing test as the acceptance criterion, and re-run after each.
