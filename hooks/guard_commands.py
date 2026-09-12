#!/usr/bin/env python3
"""PreToolUse guard for Bash: enforce forbidCommands from .testmate/config.json.

This is the enforcement half of the `forbidCommands` setting. The skill instructs the
model not to run a forbidden command; this hook makes it so regardless of what the model
decides, which is the difference between a documented intention and a guarantee.

Active only when the project has a .testmate/config.json with a non-empty forbidCommands
list, so installing TestMate does not change the behaviour of a project that never asked.
"""
import fnmatch
import json
import os
import sys


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
    """Walk up from the working directory looking for .testmate/config.json."""
    path = os.path.abspath(start)
    while True:
        candidate = os.path.join(path, ".testmate", "config.json")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        approve_silently()

    command = (payload.get("tool_input") or {}).get("command")
    if not command:
        approve_silently()

    config_path = find_config(payload.get("cwd") or os.getcwd())
    if not config_path:
        approve_silently()

    try:
        with open(config_path) as handle:
            config = json.load(handle)
    except Exception as exc:
        # A malformed safety config must never be treated as an absent one, but it must
        # not brick the session either. Hand the decision to the user.
        emit("ask", f"TestMate: {config_path} could not be parsed ({exc}). "
                    "forbidCommands cannot be enforced until it is valid JSON.")

    forbidden = config.get("forbidCommands")
    if forbidden is None:
        approve_silently()
    if not isinstance(forbidden, list):
        # A typo in a safety key must not silently become an absent safety key.
        emit("ask", f"TestMate: forbidCommands in {config_path} is "
                    f"{type(forbidden).__name__}, expected a list of strings. It cannot be "
                    f"enforced until that is fixed.")
    if not forbidden:
        approve_silently()

    # Normalise whitespace so that a reformatted command cannot slip past a pattern.
    normalised = " ".join(str(command).split())
    lowered = normalised.lower()

    for entry in forbidden:
        if not isinstance(entry, str) or not entry.strip():
            continue
        pattern = " ".join(entry.split())
        matched = pattern.lower() in lowered
        if not matched and any(ch in pattern for ch in "*?["):
            matched = fnmatch.fnmatch(normalised, pattern) or fnmatch.fnmatch(
                normalised, f"*{pattern}*")
        if matched:
            emit("deny",
                 f"TestMate blocked this command: it matches forbidCommands entry "
                 f"{entry!r} in {config_path}. Report the block and continue with work "
                 f"that does not depend on it. Do not substitute an equivalent command "
                 f"that evades the pattern.")

    approve_silently()


if __name__ == "__main__":
    main()
