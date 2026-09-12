# Next.js

Read `skills/stack-adapters/references/node.md` first — runner, assertions, Testing Library, MSW and the Node service hazards all
apply. This file covers what is specific to Next.js, which is where most of the real findings are.

## Detection

`next` in `package.json` dependencies, plus `next.config.{js,mjs,ts}`. Then determine the router,
because it changes almost everything:

- **App Router** — an `app/` directory. Server Components by default, Server Actions, route
  handlers, `middleware.ts`.
- **Pages Router** — a `pages/` directory. `getServerSideProps` / `getStaticProps`, API routes.
- Both can coexist. Profile per directory.

## Test layers

| Layer | What | How |
|---|---|---|
| Pure logic, `lib/`, utils | unit | Vitest or Jest, per `skills/stack-adapters/references/node.md` |
| Client Components (`'use client'`) | unit | Testing Library + `userEvent` |
| Route handlers (`app/**/route.ts`) | unit | import the exported `GET`/`POST` and call it with a `Request` |
| Server Actions | unit | **import the action and call it directly** — see below |
| Server Components (async) | E2E | Playwright. Testing Library cannot render an async Server Component; do not fight it |
| Middleware | unit + E2E | import and call with a `NextRequest`, then prove the real route is also guarded |

Set up Playwright if the project has any Server Component worth asserting on — but propose it and
ask before adding the dependency.

## The highest-value target: Server Actions

**A Server Action is a public HTTP endpoint.** It compiles to a POST route addressable by anyone
who knows its action id. The `<form>` wrapping it, the `disabled` button, the client-side role
check and the fact that the page is behind a login are all irrelevant to an attacker.

So the test is: **call the action function directly**, with no session, with the wrong user's
session, and with a body the UI could never produce. That is exactly what an attacker does, and it
is a clean unit test.

```ts
import { deleteProject } from '@/app/projects/actions';

it('refuses an unauthenticated caller', async () => {
  mockSession(null);
  await expect(deleteProject('proj_1')).rejects.toThrow(UnauthorizedError);
  expect(db.project.delete).not.toHaveBeenCalled();
});

it("refuses a caller who does not own the project", async () => {
  mockSession({ userId: 'u_2' });                    // project belongs to u_1
  await expect(deleteProject('proj_1')).rejects.toThrow(ForbiddenError);
  expect(db.project.delete).not.toHaveBeenCalled();
});
```

Write this pair for **every** exported Server Action. Then apply the rest of
`skills/attack-catalog/references/authz.md`: mass assignment through the `FormData`, an id in the payload
that differs from the one authorized, and a legitimate caller proving the action still works.

Also assert every action validates its input — `FormData` values are `string | File`, never the
typed object the call site pretends they are. A missing field arrives as `null`, not as an error.

## Middleware is routing, not authorization

Treat `middleware.ts` as a convenience, never as the security boundary:

- **Matcher bypass.** Attack the `config.matcher` pattern — a trailing slash, a different case, a
  path-traversal-normalized form, a prefixed locale segment, `/api/../admin`. Assert the protected
  handler refuses on its own when middleware is skipped.
- **Known bypass class.** Next.js has shipped a middleware authorization bypass driven by a
  request header (`x-middleware-subrequest`, CVE-2025-29927). Whatever the patch status, the
  lesson is structural: re-check authorization in the route handler, the Server Action and the data
  layer. Assert that a request carrying that header still gets refused by the handler itself.
- Middleware runs on the Edge runtime — Node APIs are unavailable. Assert nothing in the middleware
  path imports a Node-only module.

## Data leaking into the RSC payload

A Server Component that passes an object to a Client Component **serializes that whole object into
the HTML**. Passing a full user row leaks the password hash, the email, the internal flags — all of
it readable in view-source, with the UI showing only the display name.

```ts
it('does not serialize secret fields into the page', async () => {
  const html = await renderPage('/profile/u_1');
  expect(html).not.toContain(user.passwordHash);
  expect(html).not.toContain(user.internalNotes);
});
```

Write this for every page that renders user or tenant data. Also assert server-only modules are
marked `import 'server-only'`, so an accidental client import fails the build rather than shipping.

## Environment variables

- Any `NEXT_PUBLIC_*` value is in the browser bundle. Assert no secret carries that prefix — a
  simple test over `process.env` keys catches a whole class of incident.
- Assert a server-only secret is not reachable from a client component, and does not appear in the
  built output (`grep` the `.next/static` bundle for the known value at level `max`).

## Caching — the silent-wrongness engine

The highest-severity Next.js bugs are cache bugs, because they return a plausible page belonging to
someone else.

- **User data in a static or shared cache.** A route that reads per-user data but is statically
  rendered, or wrapped in `unstable_cache` / `cache()` without the user id in the key, serves one
  user's data to everyone. Test: render for user A, then for user B, assert B does not see A's data.
- **Dynamic opt-in.** `cookies()`, `headers()` and `searchParams` opt a route into dynamic
  rendering. Assert that a route which must be per-request actually is — a refactor that removes the
  last `cookies()` call silently makes it static.
- **`fetch` cache defaults and `revalidate`.** Assert the cache option is explicit on every fetch of
  user-scoped or mutable data.
- **Revalidation after mutation.** Assert a Server Action calls `revalidatePath`/`revalidateTag` for
  what it changed; a mutation that succeeds but leaves a stale page is silent wrongness the user
  will report as "it didn't save".

## Control flow that throws

`redirect()` and `notFound()` work by **throwing**. A `try { ... } catch { ... }` around them
swallows the redirect and falls through to the code below — a very common real bug, and a clean
test:

```ts
it('redirects an anonymous visitor instead of rendering', async () => {
  mockSession(null);
  await expect(loadDashboard()).rejects.toMatchObject({ digest: expect.stringContaining('NEXT_REDIRECT') });
});
```

Assert the redirect actually escapes any surrounding `try/catch`, and that no work happens after it.

## Routing and input

- **Open redirect.** Any `callbackUrl`, `next`, `returnTo` or `from` parameter fed to `redirect()`.
  Attack it with an absolute URL, a protocol-relative `//evil.com`, `https:evil.com`, and
  `/\evil.com`. Assert an allowlist, not a "starts with /" check.
- **`searchParams` is `string | string[] | undefined`.** `?id=1&id=2` yields an array. Assert the
  array and absent cases are handled, not coerced.
- **Dynamic segments** are caller-controlled strings. `/[slug]` with `../` or an encoded separator
  must not reach a filesystem or a database identifier unvalidated.
- **`next/image`.** A remote loader with permissive `remotePatterns` is an SSRF and bandwidth
  vector. Assert the patterns are specific hosts, not a wildcard.

## Client component tests

Mock the App Router hooks — they throw outside a router context:

```ts
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }),
  useSearchParams: () => new URLSearchParams('?q=test'),
  usePathname: () => '/projects',
}));
```

Assert the component renders its loading, empty and error states, and that `useSearchParams`
consumers are wrapped in `<Suspense>` — the missing boundary only fails at build time.

## Commands

| | |
|---|---|
| Unit | `npx vitest run` / `npx jest` (see `skills/stack-adapters/references/node.md` for the package-manager form) |
| One file | `npx vitest run app/projects/actions.test.ts` |
| E2E | `npx playwright test` |
| One E2E | `npx playwright test e2e/auth.spec.ts --project=chromium` |
| Type + build check | `npx next build` — catches type errors, missing Suspense boundaries, and client/server import violations that no unit test will |
| Lint | `npx next lint` |

`next build` is part of the run, not an extra: several whole classes of Next.js defect are
build-time only. Run it at level `standard` and above.
