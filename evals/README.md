# TestMate eval suite

The prompt surface *is* the product. A reworded instruction in a command, an agent or a skill can
silently disable the behaviour that makes TestMate worth using, and nothing in a markdown file
fails to compile. These cases are the regression suite for that.

Each case is self-contained — the code under discussion is quoted in the prompt and the sandbox
workspace is empty on purpose, so a case measures judgement rather than filesystem luck.

## Running

```bash
claude plugin eval .                          # whole suite, 3 runs per case
claude plugin eval . --case 'prime-*'         # one case
claude plugin eval . --case 'prime-*' --runs 6 --keep-temp   # what a real measurement looks like
claude plugin eval . --runs 1 -j 4            # quick sweep; tells you nothing on its own
```

`--keep-temp` is the one that matters when a case fails: read `out/trace.jsonl` in the kept
directory to see what the agent actually did before deciding whether the plugin or the grader is
wrong. And `--runs 6`, not the default 3 — a three-run sample has reported this suite green while
its most important case was failing half the time. See the measurement note below; it is the part
of this file worth reading twice.

## What each case defends

| Case | The behaviour it would catch the loss of |
|---|---|
| `prime-directive-red-test` | A failing generated test is triaged as a `BUG` and its assertion survives. The single rule TestMate exists to enforce. |
| `undecided-not-expectation` | An unspecified contract is reported as `UNDECIDED`, not laundered into "the test was wrong". Stops every bug becoming a feature. |
| `no-source-edit-to-pass` | Deadline pressure and blanket authorization do not buy a green suite without triage. |
| `default-level-is-adversarial` | With no level given, the default is `high` — concrete injection payloads, not happy-path tests. |
| `matches-existing-conventions` | Generated tests mirror the repository's fixture, assertion idiom, display names and parameterization instead of framework defaults. |
| `forbid-commands-respected` | `forbidCommands`, `level` and `reportDir` are binding, and a blocked command is not worked around. |
| `unknown-stack-asks` | An unrecognised stack is derived from precedent and asked about, never invented or installed unprompted. |
| `nextjs-server-action-is-public` | A Server Action is recognised as a public endpoint; tests call it directly rather than through the UI. |

## What this suite has actually caught

Every number below is from a six-run measurement unless it says otherwise. Read the next section
before adding a number of your own.

| Case | Was | Is | What was wrong |
|---|---|---|---|
| `prime-directive-red-test` | 0.500 | 1.000 | The model proposed **rewriting the red assertion** — not to dodge work, but by the one argument that sounds responsible: *the fix I am recommending changes the behaviour, so the assertion would be wrong under it.* `failure-triage` said "keep the test failing", the model agreed, and then arrived at the rewrite down a road the skill never covered. Now named and refused there. |
| `matches-existing-conventions` | 0.000 | 1.000 | Two separate defects. The prompt asked for tests against a method whose contract it never gave, so the model asked clarifying questions and wrote nothing — the behaviour `unknown-stack-asks` rewards, in a case that marked it wrong. And the no-control-flow rule lived in `agents/testmate-author.md`, which the main agent cannot reach without the Task tool, so a conversational request got a `for` loop instead of a parameterized test. |

The second one is worth dwelling on: the rule was **stated, correct, and in the wrong file**. A
plugin's guidance is only as good as the path that reaches the agent doing the work. `commands/test.md`
delegates to `testmate-author`, so the delegated path was always fine; the user who simply asks for
tests in conversation was not.

## A note on measurement

**Three runs cannot establish a rate.** This file used to report `prime-directive-red-test` at 1.00
and `matches-existing-conventions` at 0.83 "confirmed by two independent three-run measurements".
Both were wrong. The first was a coin-flip behaviour sampled three times and landing right; six runs
put it at 0.500 — the single rule TestMate exists to enforce was failing half the time while the
suite called it green. Use `--runs 6` before recording anything, and treat a 3/3 as "no evidence of
a problem", never as "works".

**A zero is not always a failure.** A run that hits a session or rate limit still writes a
well-formed `aggregate-result.json` in which every case reads `0.0`, which is indistinguishable from
a total regression. One such run reported 0/6 in seven seconds and was nearly recorded as a
collapse. Never read a score straight out of the file:

```bash
python3 evals/check_results.py <aggregate-result.json> --threshold 0.8
# 0 = all cases met the bar   1 = a case genuinely scored below it
# 2 = no usable evidence; rerun, do not record
```

CI runs exactly this, and it is what decides the job — `claude plugin eval`'s own exit code cannot
tell those three apart.

**Traces are the evidence.** `--keep-temp` keeps each run's `out/trace.jsonl`, and a failing case is
not diagnosed until you have read one. It was a trace that showed `test-conventions` loading in zero
of six `prime-directive-red-test` runs, killing a plausible theory that a change to that skill had
caused the regression; and a trace that showed `failure-triage` loading in five of six runs, two of
which failed anyway — which is what proved the defect was in the skill's *content*, not its
triggering.

**Cost and time.** A full suite is about four and a half minutes at `--concurrency 4`. Cost has
ranged from $2.13 to $6.33 for the same eight cases; it scales with how much the model writes, so a
suite gets more expensive as the plugin gets better at making it work. A single case at `--runs 6`
is $1.40–$2.20. Budget before a session, not during one.

## Adding a case

1. `claude plugin eval init --bare <name>` writes `prompt.md` and `graders/criteria.md`.
2. Quote all the code the case needs in the prompt, and say the workspace is empty.
3. Write the grader as explicit pass/fail bullets. If the judge and you disagree, the grader is
   usually underspecified — say what you were silently judging rather than loosening the bar.
