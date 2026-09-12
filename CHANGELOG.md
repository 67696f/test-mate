# Changelog

All notable changes to TestMate are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Because the product is a prompt surface, "behaviour" here means what the commands, agents and skills
instruct — a reworded instruction is a behavioural change even though no code moved, and is recorded
as one.

## [Unreleased]

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
