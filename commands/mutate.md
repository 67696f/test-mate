---
description: Measure whether the existing suite actually detects bugs, by mutation testing. Surviving mutants become new tests.
argument-hint: "[path | package] [--write] [--threshold N]"
---

# TestMate — mutate

Coverage says which lines ran. Mutation testing says which bugs your suite would **catch**. It is
the only honest answer to "are these tests any good?", and it is the level-`max` centrepiece.

Arguments: `$ARGUMENTS` — a path or package to mutate, `--write` to add tests for survivors,
`--threshold N` to fail below N% mutation score.

## Steps

1. **Check the suite is green first.** Mutation results are meaningless over a failing suite. If it
   is red, stop and say so — run `/testmate:test` or `/testmate:debug` first.

2. **Find the tool** from `stack-adapters`:

   | Stack | Tool | Invocation |
   |---|---|---|
   | JVM | PIT | `mvn org.pitest:pitest-maven:mutationCoverage -DtargetClasses=<pkg>.*` |
   | Node / TS / Angular | Stryker | `npx stryker run` |
   | Python | mutmut | `mutmut run --paths-to-mutate <pkg>` |
   | Rust | cargo-mutants | `cargo mutants --package <crate>` |
   | Go | go-mutesting | advisory only — the tool is immature; prefer `-race` and fuzzing |
   | C / C++ | mull | `mull-runner` over an instrumented build |

   If it is not configured, **do not add it to the build file yourself** — show the exact
   configuration snippet and ask. These tools are slow and invasive; the user should opt in.

3. **Scope it.** Mutation testing is expensive — often 10-100× a normal suite run. Mutate one
   package or one file at a time, starting with the highest-risk target from recon. Say how long
   you expect it to take before starting, and never launch an unbounded whole-repo run without
   warning the user.

4. **Read the survivors.** A surviving mutant is a change to the source that no test noticed.
   Classify each:

   - **Real gap** — the mutation changes behaviour a caller would care about and nothing caught it.
     This is a missing test.
   - **Equivalent mutant** — the mutation does not actually change observable behaviour (a
     redundant bound, an unreachable branch, a logging change). Not a gap; note it and move on.
   - **Dead code** — the mutated code cannot be reached at all. That is a finding of its own:
     report it as removable.

5. **With `--write`** — run `testmate-author` to add a test per real gap, then re-run mutation on
   that target and report the new score. Each new test must be a genuine behavioural assertion; a
   test written only to kill a mutant, with no meaning to a reader, is worse than the gap.

## Report

- **Score**: mutants generated, killed, survived, timed out; the percentage; and whether it meets
  `--threshold`.
- **Survivors that matter**, ranked — each with the mutation applied (`file:line`, what changed),
  why no test caught it, and the test that should exist.
- **Equivalent mutants** — counted, listed briefly, excluded from the judgement.
- **Dead code** found.
- The honest headline: a high line-coverage number alongside a low mutation score is the most
  useful thing this command can tell a team. Say it directly when you see it.
