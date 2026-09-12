# Resource lifecycle

Almost every resource leak lives on an error path, because the happy path is the one that got
tested. Write the failure first.

## The core shape

```
arrange a dependency that fails midway
invoke the unit
assert the failure propagated
assert the resource was still released
```

Prove release by instrumentation, not inspection: a mock whose `close`/`dispose`/`release` you
verify, a counting factory, a pool whose available-count you read afterwards, or a fake filesystem
that reports open handles.

## Shapes

| Shape | Assert |
|---|---|
| Failure during use | the connection, file, socket, stream or lock is released |
| Failure during acquisition | nothing partially acquired is left dangling |
| Failure during release | the original exception is not swallowed by the cleanup failure — it is preserved, with the cleanup failure attached as suppressed/cause |
| Early return path | every `return` between acquire and release still releases |
| Double release | releasing twice is safe, or refused with a clear error — never corrupts a pool |
| Iterator/stream not fully consumed | abandoning a lazy result set does not hold a connection open; assert the pool recovers |
| Nested acquisition | inner failure releases both levels, in reverse order |
| Pool exhaustion loop | N acquire-and-fail cycles leave the pool at full capacity |

## Streams and lazy results

A lazily evaluated query result is the classic leak: the caller gets a stream, the test asserts the
first element, and the connection is never returned. Assert explicitly that:

- consuming fully releases the resource;
- closing early releases the resource;
- an exception thrown by the consumer releases the resource;
- the stream cannot be consumed twice, or is documented to support it.

## Timeouts and unbounded work

- Every outbound call has a connect timeout **and** a read timeout. Assert by pointing the unit at
  a fake that never responds and requiring the call to fail inside a bound.
- Every retry loop has a maximum attempt count and a backoff. Assert the count and that the total
  elapsed work is bounded.
- Every queue, buffer and cache has a maximum size or an eviction policy. Assert that feeding it
  beyond the limit evicts rather than grows.

## Memory growth

At level `max`, run the operation many thousands of times and assert a bounded growth in a
countable proxy — the size of a registry, the number of listeners, the number of live entries in a
cache. Do not assert on heap bytes; it is not reproducible.

- Listener/observer registration has a matching deregistration, and a deregistration that runs on
  the error path too.
- A `ThreadLocal`, request-scoped context or similar is cleared when the request ends, including
  when it ends in failure — otherwise the value leaks into whichever request reuses the thread.
