# Changelog

All notable changes to TestMate are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Because the product is a prompt surface, "behaviour" here means what the commands, agents and skills
instruct — a reworded instruction is a behavioural change even though no code moved, and is recorded
as one.

## [Unreleased]

### Fixed
- **Three stale or wrong details in the stack adapters**, found by reading all 1,333 lines of
  reference content rather than only checking that the files resolve. `angular.md` built its
  fixture on `HttpClientTestingModule`, deprecated since Angular 17 in favour of
  `provideHttpClientTesting()`; `jvm.md` used the `Locale(String, String)` constructor, deprecated
  since Java 19 in favour of `Locale.of`; and `rust.md`'s single-test command passed a bare name to
  `cargo test --exact`, which matches the full path and so would not have run a test inside
  `mod tests`. The rest of the content held up: the injection, authz, concurrency, boundary,
  resource, environment and silent-wrongness families are accurate, and the Next.js adapter's
  middleware-bypass guidance correctly cites CVE-2025-29927.
- **`test_every_case_has_a_prompt_and_a_grader` treated any directory under `evals/` as a case.**
  Latent until `evals/` first contained a `.py` file — adding `check_results.py` meant a
  `__pycache__` could appear there, and the test then failed asserting it had no `prompt.md`.
- **Every agent was told to load skills without being given the tool to load them.** All four
  agents open by instructing themselves to load `testmate-config`, `failure-triage`,
  `attack-catalog` and friends, and none declared `Skill` in `tools:`. Whether the runtime grants
  it implicitly could not be established from the CLI — one line says a worker has Skill access,
  while the zero-tool spawn refusal treats `tools:` as authoritative — so the tool is now declared
  explicitly. Harmless if it was redundant; a closed hole if it was not. A test enforces the
  invariant: an agent whose prompt says "load X" must declare `Skill`.
- **Six cross-skill citations pointed at nothing.** Paths like
  `attack-catalog/references/authz.md` resolve from the plugin root, not from
  `skills/stack-adapters/references/` where they were written, so an agent following one opened no
  file and silently lost the guidance. The existing integrity test compared basenames only, which
  is why they passed. Citations are now root-relative, and a new test resolves every cited path
  from the file that carries it — it fails on five of the six against the old tree.
- **`enforce.sourceWrites` allowed writes to test paths outside the project.** The guard matched on
  path shape, and `os.path.relpath` turns any outside path into `../…`, so `/anywhere/tests/x.py`
  read as test surface and was approved. A guard switched on for one repository was permission to
  write test-shaped paths across the filesystem. Paths resolving outside the root holding
  `.testmate/config.json` are now refused whatever they are named.
- **The eval workflow had never run, once.** It was `pull_request`-only and this repository's
  history is direct pushes to main, so the suite guarding the prompt surface guarded nothing.
  Pushes to main now trigger it, behind the same path filter so a docs edit does not pay for a run.
  It also skips with a warning rather than failing when `ANTHROPIC_API_KEY` is not configured —
  which it is not, on this repository, and a workflow red on every push is how one gets ignored
  into dormancy in the first place. **Set the secret for the suite to actually run.**
- **`skill-fired` could turn the suite red for a non-defect.** It fires about five runs in six, and
  at equal weight two misses in CI's three-run default dropped the case to 0.67. It is now
  `weight: 0.05` — a miss reads 0.952, visible in the report and nowhere near the gate. It also
  carries `arm: with-only`, which is the proper mechanism but inert under `--ablation none`: the
  runner sets `with_only` only for runs belonging to a named arm, and CI passes `--ablation none`
  to avoid paying for a second no-plugin arm.
- CI actions bumped past the Node 20 deprecation (`checkout@v7`, `setup-python@v7`,
  `upload-artifact@v7`).

- **`forbidCommands` blocked commands that were never run.** An entry of `git push` also blocked
  `echo "git push"` and `grep -r "git push" docs/`, because matching was substring-only across the
  whole line. The line is now split on `&&`, `||`, `;`, `|` and newlines and each command checked
  in turn, and a segment whose command merely prints or searches its arguments is exempt. The
  exemption is narrow and yields wherever data can become a command again — `echo $(git push)`,
  backticks, process substitution, and any interpreter (`bash -c '…'`) stay blocked. Nineteen
  cases covering both directions are in the tests; four of them fail against the old matcher.
- **`prime-directive-red-test` was failing half the time and the suite called it green.** The case
  defends the one rule the plugin exists to enforce. Six runs scored it 0.500; the 1.00 on record
  came from three samples that happened to land right. Traces showed `failure-triage` loading in
  five of six runs and two of those failing anyway, so the defect was in the skill's content, not
  its triggering: it covered "do not patch source to reach green" but not the argument the model
  actually used — *my recommended fix changes the contract, so the assertion must change with it*.
  Named and refused now, with the legitimate version routed to after the fix lands. Back to 1.000
  at six runs, on both Opus 5 and Fable 5.1.
- **Stale eval claims in `README.md` and `evals/README.md`.** Both reported
  `matches-existing-conventions` at 0.83 "across two independent measurements" and the other seven
  cases at 1.00. Every one of those numbers came from three-run samples, and two were wrong. Both
  files now carry six-run numbers and say plainly that three runs cannot establish a rate.
- **The two `PreToolUse` guards never actually blocked anything.** Both emitted
  `hookSpecificOutput` without `hookEventName`, and that object is a discriminated union keyed on
  exactly that field — so Claude Code failed it on validation and dropped the decision. Every
  `forbidCommands` deny and every `enforce.sourceWrites` deny was silently discarded, which made
  the "enforced, and hold regardless" row in the README untrue for the whole of 0.2.0. The guards
  now also carry their reason in `permissionDecisionReason`; it had been in `systemMessage`, which
  only the user sees, so text addressed to the model ("do not substitute an equivalent command
  that evades the pattern") never reached it.
- **The hook tests asserted the guards' own output shape, not the harness contract**, which is why
  41 green tests said nothing about the above. `run_guard` now rejects a payload without
  `hookEventName` or without a reason, so every deny and ask case checks the contract.
- **The stdlib-only CI gate was a no-op.** It passed `-E` and `-P` to one `grep`; GNU grep rejects
  that with exit 2, and `if grep ...` reads a nonzero exit as "nothing found", so the step was
  green whatever the hooks imported. Its negative lookahead was unanchored besides, exempting any
  module whose name starts with an allowed one — `requests` passed as `re`. Replaced with an `ast`
  parse that compares top-level package names.
- **`evals/no-source-edit-to-pass` pointed at code it never quoted.** It carried the suite's
  "answer from the code quoted above" footer with no code block and no detail on the three
  failures. It now quotes the run and the three failures, one per verdict — `BUG`, `EXPECTATION`,
  `FIXTURE` — and the grader checks the verdicts.

## [0.2.0] — 2026-09-12

Everything the self-audit found (`docs/self-audit-2026-09-12.md`), plus the defects that running the
eval suite and testing the hooks then turned up.

### Added
- **Eval suite** (`evals/`): eight cases defending the behaviours whose loss would otherwise be
  invisible — the `BUG` verdict with the assertion intact, `UNDECIDED` not laundered into "the test
  was wrong", deadline pressure not buying a green suite, the default level actually being
  adversarial, conventions mirrored, `forbidCommands` not worked around, an unknown stack asked
  about rather than invented, and a Next.js Server Action recognised as a public endpoint.
- **Enforcement hooks** (`hooks/`): `guard_commands.py` blocks any `Bash` call matching
  `forbidCommands`; `guard_writes.py` restricts `Write`/`Edit` to test paths when
  `enforce.sourceWrites` is on. Both no-op without a project config.
- **`testmate-config` skill**: schema, defaults, precedence and the enforcement obligation for every
  configuration key.
- **Next.js stack adapter**: Server Actions as public endpoints, middleware bypass, RSC payload
  leakage, cache-driven cross-user leaks, `redirect()` throwing through `try/catch`.
- **Test suite for the plugin itself** (`tests/`): 25 hook tests, 16 structural integrity tests.
- **CI**: integrity and hook tests on every push; evals gated on prompt-surface changes.
- Governance: `CONTRIBUTING.md`, `SECURITY.md`, `CODEOWNERS`, issue and PR templates.

### Fixed
- `forbidCommands`, `reportDir` and `exclude` were documented but read by nothing. `forbidCommands`
  in particular was presented as a safety control while being wholly inert, which is worse than
  absent because it suppresses the user's own caution.
- Four of six commands never read `.testmate/config.json`, so a project's `level` and `exclude` were
  honoured by two commands and silently ignored by four.
- Report paths were hardcoded in four places while `reportDir` was advertised as configurable.
- `harden` instructed one slash command to invoke another, which cannot work; the audit procedure is
  now inlined.
- `test-conventions` was not discoverable from a plain "add tests matching this style" request —
  traces showed failing runs using no tools at all, so the plugin contributed nothing. Found by the
  eval suite.
- The author agent forbade conditionals in tests but said nothing about loops, so generated tests
  wrapped assertions in `for` loops over an enum. A loop hides which input failed and stops at the
  first. Found by the eval suite.
- `guard_commands.py` silently approved when `forbidCommands` held a string instead of a list — a
  typo in a safety key became no safety key. Found by the hook tests.
- `guard_writes.py` used `abspath`, which normalises `..` but follows no symlinks, so a symlink
  under `tests/` pointing into source passed as test surface. Found by the hook tests.

### Changed
- README now distinguishes **instructed** from **enforced** guarantees rather than claiming
  TestMate "never edits your source code", which was a rule the model follows, not a wall it cannot
  cross.
- "Adding a language is one markdown file" corrected to the two steps it actually takes.
- `--dry-run`, `--families` and `--threshold` documented.

### Known issues
- `matches-existing-conventions` sits at 0.83. Engagement (`skill-fired`) is now reliable;
  the residual is `criteria` failing about one run in three, cause not isolated.
- No adapter's commands have been executed in their own ecosystem; they are written from knowledge.
- TestMate has not yet been run end-to-end against a real codebase.

## [0.1.0] — 2026-09-12

Initial release. Six commands, four agents, five skills, adapters for the JVM, Angular, Node/React,
Python, Go, Rust and native C/C++ with a convention-inference fallback, and rigor levels
low/standard/high/max with `high` as the default.

[Unreleased]: https://github.com/67696f/test-mate/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/67696f/test-mate/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/67696f/test-mate/releases/tag/v0.1.0
