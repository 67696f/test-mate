# Unrecognised stack

No adapter matched. Do not guess an idiom — derive one, then say what you derived.

## Procedure

1. **Find the precedent.** Search the repository for anything test-shaped: a `test`/`spec`
   directory, files whose names contain `test` or `spec`, a CI workflow, a `Makefile` target named
   `test`, a `justfile`, a `Taskfile`, a `scripts` block. The CI workflow is usually the most
   reliable statement of how this project is actually tested.
2. **Identify the runner and the command** from that precedent. If a CI job runs it, that command
   is the command.
3. **Derive the conventions** from the existing tests using `test-conventions`. Location, naming,
   assertion style, fixture style.
4. **If there is no precedent at all**, stop and report rather than inventing infrastructure:
   name the language, name the two or three plausible frameworks for it, recommend one with a
   sentence of justification, and ask before adding a dependency or creating a test directory.

## What still applies without an adapter

The whole attack catalogue. Test shapes are language-independent — a refusal test, a boundary
sweep, a locale matrix and a resource-leak test exist in every language. Write them in whatever
idiom step 3 produced.

The hermeticity rules in `test-strategy` also apply unconditionally: isolated, offline,
credential-free, deterministic, non-destructive.

## Reporting

Say explicitly in the report that the stack was unrecognised, state the conventions you adopted and
the command you ran, and invite correction. A wrong-but-stated convention is cheap to fix once; a
wrong-and-silent one gets copied into every file afterwards.

If the stack turns out to be common, the fix is to add a reference file here — an adapter is one
markdown file with the six sections listed in the parent skill, and needs no code change.
