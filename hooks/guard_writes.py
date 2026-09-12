#!/usr/bin/env python3
"""PreToolUse guard for Write/Edit: keep writes inside test paths.

TestMate's core promise is that it writes tests and does not touch your source. The agent
definitions say so; this hook can make it true.

OPT-IN, and deliberately so. A plugin hook fires for every Write and Edit in the session,
including the user's own ordinary work, so enforcing by default would be worse than the
problem it solves. Enable it per project:

    { "enforce": { "sourceWrites": true } }

in .testmate/config.json. With it off (the default), this hook does nothing at all.
"""
import json
import os
import re
import sys

# Paths that are recognised as test surface across the supported ecosystems.
TEST_DIR_PATTERN = re.compile(
    r"(^|/)(tests?|__tests__|spec|specs|e2e|testdata|fixtures|src/test|"
    r"integration-tests?|\.testmate)(/|$)",
    re.IGNORECASE,
)
TEST_FILE_PATTERN = re.compile(
    r"(^|[._-])(tests?|specs?)([._-]|$)|"      # foo_test.go, test_foo.py, foo.test.ts
    r"(Test|Tests|Spec|IT)\.(java|kt|scala|cs)$|"
    r"^conftest\.py$|^(jest|vitest|karma|playwright|stryker)\.config\.",
    re.IGNORECASE,
)


def emit(decision, message):
    # hookSpecificOutput is a discriminated union keyed on hookEventName: without it the
    # whole object fails validation and the decision is silently dropped. The reason must
    # be in permissionDecisionReason -- that is the field the model reads; systemMessage
    # only reaches the user.
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": message,
        },
        "systemMessage": message,
    }, sys.stdout)
    sys.exit(0)


def approve_silently():
    sys.exit(0)


def find_config(start):
    path = os.path.abspath(start)
    while True:
        candidate = os.path.join(path, ".testmate", "config.json")
        if os.path.isfile(candidate):
            return candidate, os.path.realpath(path)
        parent = os.path.dirname(path)
        if parent == path:
            return None, None
        path = parent


def is_test_path(path, root):
    # realpath, not abspath: abspath normalises ".." but follows no symlinks, so a link
    # under tests/ pointing into src/ would otherwise pass as test surface.
    try:
        relative = os.path.relpath(os.path.realpath(path), root)
    except ValueError:
        # Different drive on Windows: not under the root, so not this project's surface.
        return False
    relative = relative.replace(os.sep, "/")
    # Outside the project entirely. The patterns below describe THIS project's test
    # surface, and they match on shape alone -- so without this check a write to
    # /anywhere/tests/x.py reads as test surface and is allowed, which turns a guard
    # scoped to one repository into permission to write test-shaped paths across the
    # whole filesystem.
    if relative == ".." or relative.startswith("../"):
        return False
    if TEST_DIR_PATTERN.search(relative):
        return True
    return bool(TEST_FILE_PATTERN.search(os.path.basename(relative)))


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        approve_silently()

    file_path = (payload.get("tool_input") or {}).get("file_path")
    if not file_path:
        approve_silently()

    config_path, root = find_config(payload.get("cwd") or os.getcwd())
    if not config_path:
        approve_silently()

    try:
        with open(config_path) as handle:
            config = json.load(handle)
    except Exception:
        # guard_commands.py already surfaces a malformed config; stay quiet here rather
        # than asking twice for the same defect.
        approve_silently()

    enforce = config.get("enforce") or {}
    if not enforce.get("sourceWrites"):
        approve_silently()

    if is_test_path(file_path, root):
        approve_silently()

    emit("deny",
         f"TestMate blocked a write to {file_path}: enforce.sourceWrites is on in "
         f"{config_path}, so writes are restricted to test paths. If this file genuinely "
         f"is test surface the pattern did not recognise, say so — do not work around the "
         f"guard, and do not edit source to make a test pass.")


if __name__ == "__main__":
    main()
