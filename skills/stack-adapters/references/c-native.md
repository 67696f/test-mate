# C / C++ (native)

The stack with the fewest guarantees and therefore the most to gain. Sanitizers do more here than
any assertion you can write — treat them as part of the test run, not an extra.

## Defaults

| | |
|---|---|
| Framework | Unity or Criterion for C; GoogleTest or Catch2 for C++ |
| Build/run | CTest via CMake |
| Location | `tests/test_<unit>.c` / `tests/<unit>_test.cpp` |
| Naming | `TEST(Parser, RejectsUnterminatedString)` / `void test_parser_rejects_unterminated(void)` |

## Refusal idiom

C has no exceptions — refusal means a documented error return plus an untouched output.

```c
void test_parse_rejects_oversized_length(void) {
    parser_t p;
    output_t out = {0};
    int rc = parse(&p, "\xff\xff\xff\xff", 4, &out);

    TEST_ASSERT_EQUAL_INT(ERR_INVALID_LENGTH, rc);
    TEST_ASSERT_NULL(out.buf);              /* nothing allocated */
    TEST_ASSERT_EQUAL_size_t(0, out.len);   /* output untouched */
}
```

Always assert **all three**: the return code, that no resource was allocated, and that the output
parameter was not partially written. A function that returns an error after half-filling its output
is the classic C silent-wrongness bug.

For C++, assert the specific exception type with `EXPECT_THROW` and additionally assert the strong
exception guarantee where it is claimed — the object is unchanged after a failed operation.

## What to attack

- **Every buffer boundary.** Input of exactly the buffer size, size minus one, size plus one, and
  an input with no terminating NUL. Assert no write past the end — ASan proves it.
- **The string functions.** `strcpy`, `strcat`, `sprintf`, `gets`, `alloca` with a computed size:
  each is a high-severity finding on sight. `strncpy` does not NUL-terminate on truncation —
  test exactly that case. `snprintf`'s return is the length it *would* have written; using it as
  the length written is a common overflow.
- **Integer issues.** Signed overflow (undefined behaviour), `size_t` underflow from `len - 1` when
  `len == 0`, a signed-to-unsigned conversion turning a negative length into an enormous one,
  and a multiplication in a `malloc` size that overflows. Test each with the boundary value.
- **Allocation failure.** Make `malloc` fail (an interposed allocator or a failure-injection hook)
  and assert the caller checks the result and unwinds cleanly.
- **Free discipline.** Double free, use after free, free of a non-heap pointer, and a missing free
  on the error path. ASan and LSan find all four if the test exercises the path.
- **Uninitialized reads.** MSan finds these; the job of the test is only to reach the code.
- **Format strings.** A caller-controlled format argument to any `printf` family function.
- **NULL parameters.** Every pointer parameter, passed NULL. Assert a documented refusal or a
  documented precondition — not a segfault.
- **Concurrency.** TSan plus the shapes in `skills/attack-catalog/references/concurrency.md`.

## Sanitizers — the core of the run

```bash
cmake -B build-asan -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_C_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build build-asan && ctest --test-dir build-asan --output-on-failure
```

Run the suite at least twice: once under ASan+UBSan, once under TSan (they are incompatible with
each other). Add MSan for uninitialized reads where the toolchain supports it. **A sanitizer report
is a confirmed `BUG`** — it needs no further triage.

Also build with `-Wall -Wextra -Werror` and treat a new warning as a finding.

## Fuzzing (level max, and often at high)

For any function that parses bytes, a fuzz target is worth more than twenty unit tests:

```c
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    parser_state_t p;
    parse(&p, data, size);   /* must not crash, leak, or read out of bounds */
    return 0;
}
```

Build with `-fsanitize=fuzzer,address`, run for a bounded time, and commit every crashing input as
a regression test case in `tests/corpus/`.

Also available: Valgrind (`valgrind --leak-check=full --error-exitcode=1`) where sanitizers are not
an option, and `clang-tidy` / `cppcheck` for static findings.

## Commands

| | |
|---|---|
| Configure | `cmake -B build -DCMAKE_BUILD_TYPE=Debug` |
| Build | `cmake --build build -j` |
| All | `ctest --test-dir build --output-on-failure` |
| One test | `ctest --test-dir build -R 'Parser.*' --output-on-failure` |
| Repeat | `ctest --test-dir build --repeat until-fail:10` |
| Coverage | build with `--coverage`, then `gcovr -r . --html-details` |

For a plain Makefile project without CTest, invoke the test binary directly and report its exit
code; do not restructure the build system without asking.
