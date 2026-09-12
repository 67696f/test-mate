---
name: testmate-config
description: Reads and enforces .testmate/config.json — levels per root, excluded paths, forbidden commands, report location, dependency-change policy and mutation thresholds. Load at the start of every TestMate command, before running anything.
---

# TestMate configuration

Every TestMate command loads this skill **first**, before recon, before any target selection, and
before running any command. A setting that is read but not enforced is worse than one that does not
exist, because the user stops watching for the thing it claimed to prevent.

## Locating the file

Look for `.testmate/config.json` at the root of the working directory. In a monorepo also check the
root of the target path. If both exist, the nearer one wins key by key.

If there is no config file, use the defaults below and do not mention it further.

If the file exists but does not parse, **stop and say so**. Do not fall back to defaults silently —
a malformed safety config must never be treated as an absent one.

## Schema and defaults

| Key | Type | Default | Meaning |
|---|---|---|---|
| `level` | `"low" \| "standard" \| "high" \| "max"` | `"high"` | Default rigor level for every command. |
| `roots` | `[{ "path": string, "level"?: string }]` | `[]` | Per-directory overrides. The longest matching `path` wins. |
| `exclude` | `string[]` (globs) | `[]` | Paths never targeted, never written to, never reported on. |
| `forbidCommands` | `string[]` | `[]` | Commands that must never be run. See enforcement below. |
| `reportDir` | `string` | `".testmate/reports"` | Where findings reports are written. |
| `mutation.enabled` | `boolean` | `true` | Whether `/testmate:mutate` may run at all. |
| `mutation.threshold` | `number` (0-100) | none | Mutation score below which the run is reported as failing. |
| `allowDependencyChanges` | `boolean` | `false` | Whether a build/manifest file may be edited to add a test dependency. |

Unknown keys are reported once as a warning — a typo in a safety key is a silent failure otherwise —
and then ignored.

## Precedence

An explicit command-line flag always wins over the config file, which always wins over the default.

```
/testmate:test src/db --level max   >   roots[].level for src/db   >   level   >   "high"
```

State the resolved level in the run's output whenever it did not come from an explicit flag, so the
user can see which rule applied.

## Enforcement

These are obligations, not suggestions. Each one corresponds to a promise made in the README.

### `forbidCommands` — check before every execution

Before running **any** shell command, compare it against every entry in `forbidCommands`. An entry
matches if the command being run contains it as a substring after normalising whitespace, or if the
entry is a glob and matches the command line. Matching is deliberately broad: a near-miss that runs
anyway defeats the purpose.

On a match: **do not run it.** Report the command, the entry that matched, and what you were trying
to accomplish, then continue with the rest of the work if it can proceed without that command. Do
not look for an equivalent command that evades the pattern — that is circumvention, not a workaround.

This obligation extends to every agent TestMate spawns. Pass the `forbidCommands` list to each
agent that has `Bash`, in its prompt, as a list it must check against.

### `exclude` — filter targets before work begins

Apply the globs when selecting targets, when ranking risk, and when choosing where to write tests.
An excluded path is not audited, not tested, not reported on. If the user names an excluded path
explicitly as the target, say that it is excluded and ask whether to override rather than silently
obeying or silently refusing.

### `reportDir` — the one place reports go

Every findings report path is `<reportDir>/<ISO-date>-<target>.md`, where `<reportDir>` is the
resolved value, not a hardcoded literal. Create the directory if it does not exist.

### `allowDependencyChanges` — gate on build-file edits

When `false` (the default), no agent may edit `pom.xml`, `build.gradle*`, `package.json`,
`pyproject.toml`, `Cargo.toml`, `go.mod`, `CMakeLists.txt` or any other manifest. Report the
dependency that a case would need, show the exact snippet that would add it, and ask. When `true`,
the edit is permitted but still announced.

### `mutation` — gate on `/testmate:mutate`

If `mutation.enabled` is `false`, `/testmate:mutate` reports that it is disabled by config and
stops. If `mutation.threshold` is set, the run reports pass or fail against it explicitly.

## Reporting what applied

At the end of a run that used a config file, add one line naming the settings that actually changed
behaviour — the resolved level and where it came from, how many paths `exclude` removed, whether any
command was blocked by `forbidCommands`. A setting that silently did nothing is indistinguishable
from a setting that was ignored, which is the defect this skill exists to prevent.
