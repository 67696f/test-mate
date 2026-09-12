## What this changes

<!-- The defect and its consequence, not the diff. -->

## Checks

- [ ] `python3 -m unittest discover -s tests` is green
- [ ] `claude plugin eval .` does not regress (7 cases at 1.00; `matches-existing-conventions` within its documented range)

## If an eval case changed score

- [ ] I ran it with `--keep-temp` and read `out/trace.jsonl` before concluding anything
- [ ] I did not loosen a grader to reach green

## If this touches `hooks/`

- [ ] There is a test for the new behaviour
- [ ] There is a test for the bypass I would try first
- [ ] A malformed config still returns `ask`, never a silent `allow`
- [ ] Still stdlib-only

## If this adds a stack adapter

- [ ] Reference file has all six sections
- [ ] Detection row added to `skills/stack-adapters/SKILL.md`
- [ ] I executed the commands in that ecosystem — which ones, and against what:
