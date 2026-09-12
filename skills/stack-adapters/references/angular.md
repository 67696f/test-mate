# Angular / TypeScript

## Defaults

| | |
|---|---|
| Runner | Jasmine + Karma (Angular default) or Jest / Vitest if the project configured one — detect, do not assume |
| Location | sibling file: `foo.service.spec.ts` next to `foo.service.ts` |
| Naming | `describe('FooService', ...)` → `describe('method', ...)` → `it('rejects an empty id', ...)` |
| Doubles | `jasmine.createSpyObj`, or `jest.fn()` where Jest is in use |

Write `it` sentences as specifications, present tense, no "should".

## Refusal idiom

```ts
expect(() => service.setTable('users; DROP TABLE users--'))
  .toThrowError(InvalidIdentifierError);

await expectAsync(service.load('../../etc/passwd'))
  .toBeRejectedWithError(/path/i);
```

Assert the specific error class or a message pattern — never a bare `toThrow()`.

## Fixture idiom

```ts
describe('UserService', () => {
  let service: UserService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [UserService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(UserService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());   // fails the test on an unexpected or missing request
});
```

On Angular 16 and earlier use `imports: [HttpClientTestingModule]` instead — it is deprecated from
17 onward in favour of the two providers above. Match whichever the repository already uses.

`http.verify()` in `afterEach` is non-negotiable — without it a test can pass while the code issues
requests nobody asserted.

## What to attack in an Angular app

- **Template escaping.** Any use of `[innerHTML]`, `bypassSecurityTrustHtml`,
  `bypassSecurityTrustResourceUrl` or `bypassSecurityTrustUrl` is a finding candidate. Assert a
  payload-bearing string is sanitized, and that no caller-controlled value reaches a bypass.
- **URL construction.** A router navigation or an HTTP URL built by concatenation: assert the id is
  encoded and that a value containing a slash or `..` cannot change the route or the endpoint.
- **HTTP contract.** For each service method assert the method, the exact URL, the body, the
  headers, and — critically — the behaviour on 4xx and 5xx and on a network error. Most Angular
  service suites test only the 200.
- **Interceptors.** Assert the auth token is attached to in-app requests and **not** attached to
  third-party hosts; assert a 401 triggers the intended refresh exactly once under concurrent
  requests, not once per request.
- **Guards and resolvers.** The authz matrix from `skills/attack-catalog/references/authz.md` applies
  directly: anonymous, wrong role, expired token, and the legitimate case.
- **Forms.** Validators are a refusal suite: assert each validator rejects its target input and
  accepts a legitimate one; assert a disabled control's value is not silently submitted.
- **Subscriptions.** Assert `ngOnDestroy` unsubscribes — a leaked subscription is the Angular form
  of `skills/attack-catalog/references/resources.md`.
- **Change detection.** For `OnPush` components assert the view updates when the input reference
  changes and does not when it is mutated in place — that mismatch is classic silent wrongness.

## Async

Prefer `fakeAsync` + `tick()` over real timers, and `flush()` to drain. Never `setTimeout` in a
test. For observables, assert the full emission sequence including completion and error, not just
the first value.

## Property-based and mutation (level max)

- Property-based: **fast-check** — `fc.assert(fc.property(fc.string(), s => ...))`.
- Mutation: **Stryker** (`npx stryker run`).

## Commands

| | |
|---|---|
| All, CI mode | `npx ng test --watch=false --browsers=ChromeHeadless` |
| One file | add `--include='**/foo.service.spec.ts'` |
| Coverage | `npx ng test --watch=false --code-coverage` |
| Lint | `npx ng lint` |

If the project uses Jest or Vitest instead, follow `skills/stack-adapters/references/node.md` for the commands and keep the Angular
guidance above.
