---
type: llm
weight: 1
---

This case checks the single most important Next.js-specific insight: a Server Action is a public
endpoint, and the UI around it is not a security boundary.

Passes if ALL of:

- It states that the Server Action compiles to a publicly addressable POST endpoint that can be
  invoked directly, and that being behind a login page or an owner-only button does not protect it.
- It identifies the missing authentication check AND the missing ownership/authorization check as
  the defects — the action never looks at who is calling.
- It proposes tests that CALL THE ACTION FUNCTION DIRECTLY — with no session, and with a session
  belonging to a user who does not own the project — rather than testing through the form or the
  rendered UI.
- It asserts refusal, and that no deletion occurred, not merely that an error was returned.

Strong signal (not required): it notes the unused `project` lookup result, or recommends the same
audit for every other exported Server Action in the codebase, or includes a positive test proving
the legitimate owner can still delete.

Fails if it treats the login page or the conditionally rendered button as adequate protection, or
if its proposed tests only drive the UI.
