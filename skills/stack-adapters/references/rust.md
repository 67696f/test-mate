# Rust

## Defaults

| | |
|---|---|
| Runner | `cargo test` |
| Unit tests | `#[cfg(test)] mod tests` at the bottom of the source file — access to private items |
| Integration tests | `tests/<area>.rs` — exercises only the public API, which is where contract bugs live |
| Naming | `fn rejects_empty_filter_list()`, with `#[test]` |
| Assertions | `assert_eq!`, `assert!`; `pretty_assertions` if the project uses it |

Write both kinds: the unit module for internal invariants, an integration file per public area so
an accidental visibility or signature change fails a test.

## Refusal idiom

```rust
#[test]
fn table_rejects_injection() {
    let err = Db::table("users; DROP TABLE users--").unwrap_err();
    assert!(matches!(err, Error::InvalidIdentifier { .. }), "got {err:?}");
}
```

Match the error **variant**. For a panicking API use `#[should_panic(expected = "...")]` with a
substring — never a bare `#[should_panic]`, which passes on any panic including one from the test's
own setup.

## Fixture idiom

Rust has no fixture framework in the standard runner; write a constructor function and rely on
`Drop` for teardown.

```rust
struct TestDb { _dir: tempfile::TempDir, conn: Connection }

fn test_db() -> TestDb {
    let dir = tempfile::tempdir().unwrap();
    let conn = Connection::open(dir.path().join("t.db")).unwrap();
    conn.execute_batch(SCHEMA).unwrap();
    TestDb { _dir: dir, conn }
}
```

`TempDir` cleans up on drop even when the test panics. Never write to a shared path.

## What to attack in Rust specifically

The compiler removes whole families of bugs; aim at what it does not remove.

- **`unsafe` blocks.** Every one is a finding candidate. Assert the documented invariant is
  actually enforced at the boundary, and run the suite under Miri.
- **Panics in library code.** `unwrap`, `expect`, indexing, slicing and integer division on
  caller-controlled data. Feed the input that panics and assert a `Result` is returned instead.
  A library that panics on bad input has an incomplete error type.
- **Arithmetic overflow.** Debug builds panic, release builds wrap — a behaviour difference between
  profiles is silent wrongness. Assert `checked_*` / `saturating_*` where it matters, and test in
  release if the project ships release.
- **Slicing on a non-char-boundary** of a UTF-8 string panics. Test with multi-byte input.
- **`Ord` / `PartialEq` / `Hash` consistency**, especially with a manual implementation or floats
  (`NaN` breaks `Ord`). A `HashMap` key type with an inconsistent `Hash`/`Eq` pair is a real bug.
- **Interior mutability and `Send`/`Sync`.** Anything with `RefCell`, `Cell`, `Rc` crossing a
  thread boundary, or a manual `unsafe impl Send`.
- **Blocking inside async.** A `std` blocking call inside a `tokio` task starves the runtime; assert
  a bounded completion time under concurrent load.
- **`Drop` order and leaks.** `std::mem::forget`, reference cycles through `Rc`. Assert a counter in
  a `Drop` impl reaches zero.
- **Error conversion.** A `From` impl that collapses distinct causes into one variant loses the
  ability to react — assert the variant carries the distinguishing information.

## Property-based, fuzzing and mutation (level max)

- Property-based: **proptest** or **quickcheck**. Ideal for parsers, encoders and comparators.
- Fuzzing: **cargo-fuzz** (libFuzzer) or **afl.rs** for anything parsing untrusted bytes.
- **Miri**: `cargo +nightly miri test` — detects undefined behaviour in `unsafe` code. Run it
  whenever the crate contains `unsafe`.
- Sanitizers: `RUSTFLAGS="-Zsanitizer=address" cargo +nightly test`.
- Mutation: **cargo-mutants**.

## Commands

| | |
|---|---|
| All | `cargo test` |
| One test | `cargo test tests::rejects_empty_filter_list -- --exact --nocapture` — `--exact` matches the full path, so include the module |
| One target | `cargo test --test integration_db` |
| Release profile | `cargo test --release` (different overflow behaviour — run both) |
| All features | `cargo test --all-features` and `--no-default-features` |
| Lints | `cargo clippy --all-targets -- -D warnings` |
| Miri | `cargo +nightly miri test` |
| Doc tests | included in `cargo test`; treat a failing doc example as a `BUG` |
