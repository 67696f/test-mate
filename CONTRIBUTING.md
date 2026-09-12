# Contributing to TestMate

TestMate's product is a prompt surface. Markdown fails to compile in no way at all, so the only
protection against a reworded instruction quietly removing a behaviour is the test and eval suites.
Please treat them as the gate, not as paperwork.

## Before you open a PR

```bash
python3 -m unittest discover -s tests -v    # ~1s, no credentials needed
claude plugin eval .                        # ~4 min, ~$1.80, needs your Claude credential
```

The unit tests must be green. The eval suite must not regress: seven cases at 1.00 and
`matches-existing-conventions` at its documented range. If a case drops, find out **why** before
touching the grader.

## The rule that governs changes

The same one TestMate enforces on the code it tests:

> **A failing test is a finding until proven otherwise.**

If an eval case fails, run it with `--keep-temp` and read `out/trace.jsonl` before concluding
anything. In this repository's history, the first three eval failures were *all* defects in the eval
suite, and the fourth and fifth were real defects in the plugin. Both outcomes are normal; guessing
which without reading the trace is not.

Never loosen a grader to reach green. A grader that is honestly soft and documented is worth more
than one relaxed until it passes — see `matches-existing-conventions`, which is left failing on
purpose.

## Adding a stack adapter

1. Write `skills/stack-adapters/references/<stack>.md` with the six sections the parent skill lists:
   where test files go, the refusal idiom, the fixture idiom, parameterization, doubles, and the
   commands to run.
2. Add a detection row to the table in `skills/stack-adapters/SKILL.md`.
3. **Verify the commands actually run** in that ecosystem. Adapter commands are a correctness
   surface with no automated coverage; a wrong flag is invisible until it fails in someone's repo.
   Say in the PR which commands you executed and against what.

No change to the attack catalogue should be needed — test shapes are language-independent, and an
adapter only translates them into idiom. If you find yourself wanting to add a *family*, that
belongs in `skills/attack-catalog/` and applies to every language.

## Adding an eval case

```bash
claude plugin eval init --bare <name>
```

Quote all the code the case needs in the prompt and state that the workspace is empty — the sandbox
has no repository, and a case that assumes one measures filesystem luck rather than judgement.

Write the grader as explicit pass/fail bullets. If you and the judge disagree, the grader is usually
underspecified: say what you were silently judging rather than lowering the bar.

## Changing the hooks

`hooks/*.py` are security controls that run on every `Bash`, `Write` and `Edit` call in a user's
session. Changes there need:

- a test in `tests/test_hooks.py` for the new behaviour, **and** one for the bypass you would try
  first if you wanted to evade it;
- fail-safe behaviour preserved: a malformed config must `ask`, never silently `allow` and never
  brick the session;
- no new dependency — the hooks are stdlib-only Python 3 so they run wherever Claude Code does.

## Style

Match the surrounding prose. The skills are written as instructions to an agent that will follow
them literally: prefer a concrete input over a description of one, state the obligation rather than
suggesting it, and give the reason when the reason is what makes the rule stick.

## Commits

Explain the defect and its consequence, not the diff. "forbidCommands was inert, so a user could
believe deploys were blocked when they were not" tells a future reader why the change exists;
"update config handling" does not.
