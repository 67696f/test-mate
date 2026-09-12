# Node / React / TypeScript

## Defaults

| | |
|---|---|
| Runner | Vitest for new work; Jest if the project already uses it; `node:test` for dependency-free packages |
| Location | `foo.test.ts` beside the source, or under `__tests__/` — follow the repo |
| Naming | `describe('createUser', ...)` → `it('rejects a body carrying a role field', ...)` |
| Component tests | Testing Library (`@testing-library/react`) — query by role and accessible name, never by class or test id where a role exists |
| HTTP doubles | MSW (`msw`) at the network layer; `supertest` for driving a server |

## Refusal idiom

```ts
expect(() => parseRange('10..1')).toThrow(InvalidRangeError);
await expect(svc.load('../../etc/passwd')).rejects.toThrow(/outside root/);
```

Always assert the class or a message pattern. A bare `.toThrow()` passes on a `TypeError` from a
typo in your own test.

For "nothing happened": `expect(db.query).not.toHaveBeenCalled()`.

## Fixture idiom

```ts
let server: ReturnType<typeof setupServer>;
beforeAll(() => { server = setupServer(...handlers); server.listen({ onUnhandledRequest: 'error' }); });
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

`onUnhandledRequest: 'error'` is the Node equivalent of `HttpTestingController.verify()` — it turns
an unasserted network call into a failure instead of a silent pass.

For databases, start a container or an in-process instance **per test file** with a unique schema
name; never share a database between files running in parallel.

## What to attack in a Node service

- **Prototype pollution.** A body or query containing `__proto__`, `constructor`, `prototype` in a
  key. Assert a merge/assign helper does not write to `Object.prototype` — check a fresh object
  afterwards for the injected key.
- **Mass assignment.** Assert the handler ignores `role`, `id`, `isAdmin` in the body.
- **Path handling.** `path.join` does not prevent traversal — assert the resolved path is checked
  against a root with `path.resolve` and a separator-aware prefix test.
- **Child processes.** Assert `execFile`/`spawn` with an argument array, never `exec` with an
  interpolated string.
- **Type coercion at the edge.** Query parameters arrive as strings or arrays: assert
  `?id=1&id=2` (an array where a string was expected) and `?n=1e999` are refused, not coerced.
  `==`, `parseInt` without a radix, and truthiness checks on `0` / `''` are all finding candidates.
- **JSON limits.** Assert a body size limit exists and that exceeding it returns 413 rather than
  consuming memory.
- **Unhandled rejections.** Assert an async handler's rejection produces a 5xx response, not a
  process-level unhandled rejection. Register a listener in the test and fail if it fires.
- **Timeouts.** Every outbound `fetch`/client call has an `AbortSignal.timeout` — prove it with a
  handler that never responds.

## What to attack in a React component

- Renders the error state, the empty state and the loading state — most suites test only the
  populated state.
- User input containing markup is rendered as text; any `dangerouslySetInnerHTML` is a finding.
- An `href` built from data cannot become `javascript:`.
- Keyboard and screen-reader access: the interactive element is reachable by role and operable by
  keyboard. Use `userEvent`, not `fireEvent`, so real event sequences are exercised.
- Effects clean up: unmount and assert no state update, no pending timer, no open subscription.

## Property-based and mutation (level max)

- Property-based: **fast-check**.
- Mutation: **Stryker** (`npx stryker run`).
- Fuzzing a parser: `fast-check` with `fc.string()` / `fc.uint8Array()` and an invariant.

## Commands

| | Vitest | Jest |
|---|---|---|
| All | `npx vitest run` | `npx jest` |
| One file | `npx vitest run src/foo.test.ts` | `npx jest src/foo.test.ts` |
| One test | `npx vitest run -t 'rejects a body'` | `npx jest -t 'rejects a body'` |
| Coverage | `npx vitest run --coverage` | `npx jest --coverage` |

Always use the non-watch form. Check the package manager from the lockfile (`pnpm-lock.yaml`,
`yarn.lock`, `bun.lockb`) and use its runner rather than `npx` where one is in use.
