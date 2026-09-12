# Concurrency

Only write these when the unit actually touches shared mutable state, is documented as thread-safe,
is a singleton, or mediates access to an external resource. Concurrency tests that do not need to
be concurrent are flaky noise.

## Make them deterministic

A test that fires threads and hopes is a coin flip. Prefer, in order:

1. **Inject the interleaving.** Give the unit a seam (a hook, a latch, a test-only callback) and
   drive the exact sequence you want to prove is broken. Deterministic, fast, never flaky.
2. **Barrier/latch coordination.** Release N threads simultaneously from a barrier and assert on
   the aggregate invariant, not on a specific interleaving.
3. **Repetition with an invariant.** Run the operation many times from many threads and assert an
   invariant that must hold under every interleaving (a total, a count, a set of ids). Report the
   failure rate rather than a single pass/fail.

Never assert on timing, sleep as a synchronization mechanism, or depend on scheduler order.

## Shapes

| Shape | Setup | Assert |
|---|---|---|
| **Lost update** | two callers read-modify-write the same record | final value reflects both, or one fails loudly with an optimistic-lock error |
| **Check-then-act (TOCTOU)** | two callers both see "does not exist" and both create | exactly one succeeds; the other gets a well-typed conflict, not a constraint-violation stack trace |
| **Non-atomic compound** | an operation that reads, computes and writes across two calls | either wrapped in a transaction/lock, or the intermediate state is observably valid |
| **Shared builder or state leak** | reuse a "fluent" or builder object across two callers | the second caller does not inherit the first one's accumulated state |
| **Cache coherence** | write through one path, read through a cached path | the read reflects the write, or staleness is bounded and documented |
| **Idempotence under retry** | invoke the same operation twice with the same idempotency key | one effect, not two |
| **Lock ordering** | two operations that take the same two locks | acquired in a consistent order; assert no deadlock inside a timeout |
| **Resource pool exhaustion** | more concurrent callers than the pool size | callers queue and complete, or fail with a clear timeout — never hang forever |

## Statics and singletons

Any mutable static, class-level cache, or process-global configuration is a finding candidate on
its own. Test that two instances or two threads do not interfere, and that a value set by one test
cannot leak into another — a leak between tests is proof of a leak between requests.

## Async and reactive code

- An error thrown inside a callback, a promise chain or a stream operator propagates to the caller
  rather than becoming an unhandled rejection. Assert the unhandled-rejection handler is not hit.
- Cancellation actually cancels: assert the downstream work stops and resources are released.
- Backpressure: a fast producer against a slow consumer does not grow memory without bound.
- Ordering guarantees are asserted explicitly, since the natural test passes by luck.
