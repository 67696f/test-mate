# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities privately via
[GitHub Security Advisories](https://github.com/67696f/test-mate/security/advisories/new) rather
than opening a public issue.

Include the affected component, what an attacker can achieve, and the minimal steps to reproduce.
You will get an acknowledgement within a week.

## Threat model

TestMate ships two kinds of executable surface, and they carry different risk.

**The hooks** (`hooks/*.py`) are the sharp end. They run as `PreToolUse` handlers on **every**
`Bash`, `Write` and `Edit` call in any session where the plugin is installed — including the user's
own work, not just TestMate's. They are stdlib-only Python 3, read only `.testmate/config.json` from
the project, and never execute anything themselves. Failure modes that matter:

- **Failing open.** A guard that approves when it cannot evaluate turns a safety control into
  decoration. Malformed configuration returns `ask`, never a silent `allow`.
- **Failing closed too hard.** A guard that denies everything on an unexpected input would make the
  session unusable. Unrelated inputs are approved silently.
- **Bypass.** `forbidCommands` matching normalises whitespace and case and matches substrings
  precisely so that reformatting, chaining and wrapping do not evade it. `enforce.sourceWrites`
  resolves symlinks and `..` before classifying a path.

`tests/test_hooks.py` covers each of these, including the bypasses.

**The prompt surface** (commands, agents, skills) instructs a model. It cannot be *enforced* in the
way the hooks can — the author agent must hold `Write` to produce test files at all, and no tool
grants write access to a single subtree. The README states plainly which guarantees are instructed
and which are enforced; please do not weaken that distinction.

## What TestMate will not do

- It does not transmit your code anywhere. Everything runs in your Claude Code session.
- It does not read credentials. Generated tests are required to be credential-free and offline, and
  the hooks read nothing but the project's own config file.
- It does not add dependencies or edit build files unless `allowDependencyChanges` is `true`.

## Using it on untrusted code

Auditing hostile code is a normal use. Be aware that TestMate reads that code and quotes it into
reports and test files, so treat the output with the same care as the input. Set `forbidCommands`
and `exclude` before pointing it at anything you do not control.

## Supported versions

Pre-1.0: only the latest release receives fixes.
