# Python

## Defaults

| | |
|---|---|
| Runner | pytest |
| Location | `tests/test_<module>.py`, mirroring the package tree |
| Naming | `def test_rejects_empty_filter_list():` — the name is the specification |
| Doubles | `unittest.mock` (`patch`, `MagicMock`) or `pytest-mock`'s `mocker` fixture |
| Fixtures | pytest fixtures with the narrowest scope that works; default to `function` |

## Refusal idiom

```python
with pytest.raises(InvalidIdentifierError, match="identifier"):
    db.table("users; DROP TABLE users--")
```

Always pass `match=` or assert on the exception instance. A bare `pytest.raises(Exception)` will
happily pass on a `NameError` from a typo in the test itself.

For "nothing happened": `cursor.execute.assert_not_called()`.

## Fixture idiom

```python
@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()
```

Use `tmp_path` rather than a hardcoded path, `monkeypatch` rather than mutating `os.environ`
directly, and `yield` fixtures so teardown runs even when the test fails.

## Parameterization

```python
@pytest.mark.parametrize("payload", [
    "users; DROP TABLE users--",
    "Users",
    "",
    "users\x00",
])
def test_table_rejects_bad_identifiers(db, payload):
    with pytest.raises(InvalidIdentifierError):
        db.table(payload)
```

Give each case an `id` when the value does not read well in the report.

## What to attack in Python specifically

- **Mutable default arguments** (`def f(items=[])`) — call twice and assert the second call does
  not see the first call's data. A near-guaranteed finding wherever it appears.
- **Dynamic execution**: `eval`, `exec`, `pickle.loads`, `yaml.load` without `SafeLoader`,
  `subprocess` with `shell=True`, `os.system`. Each is a high-severity finding; assert the safe
  variant is used and that untrusted input cannot reach the unsafe one.
- **String formatting into SQL.** Assert parameters are passed to `execute` as a separate argument,
  never interpolated. Identifiers still need an allowlist — see the injection reference.
- **Path handling**: `os.path.join` with an absolute second argument discards the first. Assert
  traversal is checked with `Path.resolve()` and `is_relative_to(root)`.
- **Integer/float**: Python integers do not overflow, but `float` for money does lose precision —
  assert `Decimal` and an explicit rounding mode.
- **Equality and hashing**: a dataclass with `eq=True, frozen=False` is unhashable; a custom
  `__eq__` without `__hash__` breaks set membership. Assert both.
- **Iterator exhaustion**: a generator consumed twice yields nothing the second time — assert the
  API returns a sequence where the caller will iterate more than once.
- **Encoding**: `open()` without `encoding=` uses the platform default. Assert an explicit UTF-8.
- **Datetime**: a naive `datetime` in storage or comparison is a finding; assert timezone-aware
  values and an injected clock.

## Async

Use `pytest-asyncio` (`@pytest.mark.asyncio`). Assert cancellation propagates
(`asyncio.CancelledError` is re-raised, not swallowed by a bare `except Exception`) and that every
awaited external call has a timeout.

## Property-based and mutation (level max)

- Property-based: **Hypothesis** — `@given(st.text())`, with `@example(...)` pinning known edge
  cases. Hypothesis' shrinking makes it the best tool in this list for finding silent wrongness.
- Mutation: **mutmut** (`mutmut run`) or **cosmic-ray**.
- Fuzzing: **atheris** for C-extension boundaries.

## Commands

| | |
|---|---|
| All | `python -m pytest -q` |
| One file | `python -m pytest -q tests/test_db.py` |
| One test | `python -m pytest -q tests/test_db.py::test_rejects_empty_filter_list` |
| By name | `python -m pytest -q -k "rejects and not slow"` |
| Coverage | `python -m pytest --cov=<pkg> --cov-report=term-missing` |
| Stop at first failure, full trace | `python -m pytest -x -vv --tb=long` |

Respect the project's environment manager — `uv run`, `poetry run`, `pdm run`, or an activated
virtualenv — rather than calling a global interpreter.
