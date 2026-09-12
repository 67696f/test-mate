# Go

## Defaults

| | |
|---|---|
| Runner | `go test` (standard library) |
| Location | `foo_test.go` beside `foo.go`, same package; `package foo_test` when testing only the exported surface |
| Naming | `func TestTable_RejectsInjection(t *testing.T)`, subtests named as sentences |
| Assertions | standard library by default; `testify` only if the project already uses it |

Table-driven subtests are the house style — use them for everything, including refusal suites.

## Refusal idiom

```go
func TestTable_RejectsBadIdentifiers(t *testing.T) {
	cases := map[string]struct {
		in      string
		wantErr error
	}{
		"stacked statement": {"users; DROP TABLE users--", ErrInvalidIdentifier},
		"uppercase":         {"Users", ErrInvalidIdentifier},
		"empty":             {"", ErrInvalidIdentifier},
	}
	for name, tc := range cases {
		t.Run(name, func(t *testing.T) {
			_, err := Table(tc.in)
			if !errors.Is(err, tc.wantErr) {
				t.Fatalf("Table(%q) error = %v, want %v", tc.in, err, tc.wantErr)
			}
		})
	}
}
```

Use `errors.Is` / `errors.As` against a sentinel or typed error. Comparing error **strings** is a
finding in itself — report it when you see it in existing tests.

## Fixture idiom

```go
func newTestDB(t *testing.T) *sql.DB {
	t.Helper()
	db, err := sql.Open("sqlite", "file:"+t.Name()+"?mode=memory&cache=shared")
	if err != nil { t.Fatal(err) }
	t.Cleanup(func() { db.Close() })
	// schema + seed...
	return db
}
```

`t.Helper()` so failures point at the caller, `t.Cleanup` so teardown survives a `t.Fatal`,
`t.TempDir()` for files. Call `t.Parallel()` in every test that can run in parallel — and note that
adding it will surface shared-state bugs, which is the point.

## What to attack in Go specifically

- **Ignored errors.** `_ = f()` or a missing error check is the most common Go defect. Make the
  dependency fail and assert the caller propagates rather than continuing with a zero value.
- **Nil maps and nil slices.** Writing to a nil map panics; a nil slice appends fine. Assert the
  zero value of an exported struct is usable, or that a constructor is mandatory.
- **Slice aliasing.** `append` may share the backing array: mutate a returned slice and assert the
  source is unchanged. Same for a struct containing a slice or map returned by value.
- **Loop variable capture** in goroutines and closures (pre-Go 1.22 semantics) — assert the
  collected results are the expected set, not N copies of the last element.
- **Goroutine leaks.** Use `go.uber.org/goleak` in `TestMain`, or count goroutines before and
  after. Assert a cancelled `context` actually stops the work.
- **Context.** Every exported blocking function takes a `ctx` and honours cancellation and
  deadline. Prove it: cancel immediately and assert `context.Canceled` inside a short bound.
- **`defer` in a loop** accumulating open handles until the function returns.
- **Interface nil trap.** A nil pointer stored in an interface is non-nil — assert `err != nil`
  behaviour when a typed nil is returned.
- **`time.Now()` called directly** rather than through an injected clock: a finding, because it
  makes the environment cases in the catalogue untestable.

## Property-based and mutation (level max)

- Fuzzing is built in: `func FuzzParse(f *testing.F)` with `f.Add(seed)` and `f.Fuzz(...)`.
  Run with `go test -fuzz=FuzzParse -fuzztime=60s`. Commit any crash corpus it produces.
- Property-based: `pgregory.net/rapid` or `gopter`.
- Mutation: `go-mutesting` (less mature — treat its output as advisory).

## Commands

| | |
|---|---|
| All | `go test ./...` |
| One package | `go test ./internal/db/` |
| One test | `go test ./internal/db/ -run 'TestTable_RejectsInjection/empty' -v` |
| Race detector | `go test -race ./...` — run this at level `high` or above, always |
| Coverage | `go test -coverprofile=cover.out ./... && go tool cover -func=cover.out` |
| Repeat (flake hunt) | `go test -count=10 -race ./...` |
| Vet | `go vet ./...` |

`-race` is the highest-value single flag in this document. Any race it reports is a confirmed
`BUG`, not a candidate.
