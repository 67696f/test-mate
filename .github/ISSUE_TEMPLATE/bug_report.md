---
name: Bug report
about: TestMate did something wrong, or failed to do something it promises
title: ''
labels: bug
assignees: ''
---

**What happened**
What TestMate did, and what you expected instead.

**Which command**
e.g. `/testmate:test src/main/java/... --level high`

**Stack**
Language, build tool, test runner. Whether the project has existing tests.

**Config**
Your `.testmate/config.json`, if any.

**Did it weaken a test?**
TestMate must never relax, skip or delete a test to reach green, and must never patch source without
being asked. If it did either, say so here — that is the most serious class of bug in this project
and it will be treated as such.

**Report output**
The relevant part of the findings report, if one was produced.
