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


# Commands whose arguments are data, not instructions. A forbidden string appearing only
# as an argument to one of these is being printed or searched for, not run.
INERT_COMMANDS = frozenset({
    "echo", "printf", "cat", "grep", "egrep", "fgrep", "rg", "ag", "ack",
    "head", "tail", "less", "more", "wc", "comm", "diff",
})

# Anything that can turn data back into a running command. If a segment contains one of
# these, the inert-command exemption does not apply: `echo $(git push)` runs git push, and
# a guard fooled by that is worse than no guard.
SUBSTITUTION = ("$(", "`", "${", "<(", ">(")

# Shell operators that separate one command from the next.
SEPARATORS = ("&&", "||", ";", "|", "&", "\n")


def split_segments(command):
    """Split a command line into the individual commands it runs.

    Deliberately crude. It does not parse quoting, so a separator inside a quoted string
    splits too -- which errs toward MORE segments and therefore more chances to match, the
    safe direction for a guard.
    """
    # A backslash before the newline is a line continuation: one command written over
    # two lines, not two commands. Join those first, so `mvn \` + newline + `deploy`
    # is still `mvn deploy`. A bare newline, by contrast, IS a separator and stays one.
    command = command.replace("\\\r\n", " ").replace("\\\n", " ")
    segments = [command]
    for sep in SEPARATORS:
        nxt = []
        for part in segments:
            nxt.extend(part.split(sep))
        segments = nxt
    return [" ".join(s.split()) for s in segments if s.strip()]


def leading_command(segment):
    """The command a segment actually runs, past any VAR=value prefixes."""
    for token in segment.split():
        if "=" in token and not token.startswith("="):
            name = token.split("=", 1)[0]
            if name and all(c.isalnum() or c == "_" for c in name):
                continue    # an environment assignment, not the command
        return os.path.basename(token).lower()
    return ""


def segment_matches(segment, pattern):
    if any(mark in segment for mark in SUBSTITUTION):
        # Data can become a command here; fall back to the broad check.
        return pattern.lower() in segment.lower()
    if leading_command(segment) in INERT_COMMANDS:
        # The pattern is an argument being printed or searched for, not executed.
        return False
    return pattern.lower() in segment.lower()


def matches(command, pattern):
    """True if any command the line runs matches the forbidden entry.

    Takes the RAW command. Whitespace is normalised per segment, after splitting --
    never before. Normalising first turns a newline into a space, which merges
    `echo "starting"` and `git push` on the next line into one segment led by an
    inert command, and the exemption then lets the push through.

    Matching stays substring-based within each segment: an entry of `git push` still
    blocks `git push --force origin main`, and still blocks it inside `bash -c '...'`,
    because bash is not an inert command. What it no longer blocks is the pattern
    appearing purely as data -- `echo "git push"`, `grep -r "npm publish" docs/`.
    """
    if any(ch in pattern for ch in "*?["):
        flat = " ".join(command.split())
        if fnmatch.fnmatch(flat, pattern) or fnmatch.fnmatch(flat, f"*{pattern}*"):
            return True
    return any(segment_matches(seg, pattern) for seg in split_segments(command))


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

    # The raw command goes to the matcher; it normalises whitespace per segment AFTER
    # splitting, so a newline still separates commands (see matches()).
    for entry in forbidden:
        if not isinstance(entry, str) or not entry.strip():
            continue
        pattern = " ".join(entry.split())
        matched = matches(str(command), pattern)
        if matched:
            emit("deny",
                 f"TestMate blocked this command: it matches forbidCommands entry "
                 f"{entry!r} in {config_path}. Report the block and continue with work "
                 f"that does not depend on it. Do not substitute an equivalent command "
                 f"that evades the pattern.")

    approve_silently()


if __name__ == "__main__":
    main()
