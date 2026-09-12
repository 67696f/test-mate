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
claude plugin eval . --runs 1 -j 4            # quick sweep, less reliable
claude plugin eval . --keep-temp              # keep each run's trace for debugging
```

`--keep-temp` is the one that matters when a case fails: read `out/trace.jsonl` in the kept
directory to see what the agent actually did before deciding whether the plugin or the grader is
wrong. Scoring at `--runs 1` makes ordinary variance look like failure — use 3 before concluding
anything.

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

## Known-unstable case

`matches-existing-conventions` is the one case that does not score 1.00, and its results disagree
between runs — 0.83 in one clean measurement (`criteria` 3/3, `skill-fired` 2/3), 0.33 in another.
Treat it as unsettled until a clean full-suite run confirms it.

Its second grader, `skill-fired`, asks whether TestMate actually engaged rather than whether the
base model happened to guess the right style unaided. That distinction matters: traces from an
earlier failing run showed the agent using **no tools at all**, which meant the case was measuring
base-model luck rather than anything the plugin did. Sharpening `test-conventions`'s description
fixed the engagement problem in isolation; whether it holds under load is what the outstanding run
will show.

The case is left failing rather than loosened. A grader that is honestly soft and documented is
worth more than one relaxed until it is green — the exact move this plugin refuses to make in the
code it tests.

## A note on measurement

Runs abort if the account hits a session or rate limit, and an aborted case reports `0.00` with an
`exit 1` note rather than a real score. Check the NOTES column before believing a zero. A full suite
is roughly four minutes and about $1.80 at `--concurrency 4`.

## Adding a case

1. `claude plugin eval init --bare <name>` writes `prompt.md` and `graders/criteria.md`.
2. Quote all the code the case needs in the prompt, and say the workspace is empty.
3. Write the grader as explicit pass/fail bullets. If the judge and you disagree, the grader is
   usually underspecified — say what you were silently judging rather than loosening the bar.
