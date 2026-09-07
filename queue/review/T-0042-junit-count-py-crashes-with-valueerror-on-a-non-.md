---
id: T-0042
title: junit_count.py crashes with ValueError on a non-numeric failures= or errors= attribute
state: review
owner: agent/builder-6
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:38:26Z
lease_expires_at: 2026-09-07T19:38:26Z
worktree: ../wt/T-0042
branch: task/T-0042
exclusive: []
touches: [ops/lib/junit_count.py, ops/lib/check-failure-naming]
pins_affected: []
reviewer: agent/reviewer-25
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/lib/junit_count.py` reads `failures=` and `errors=` off summary-only `<testsuite>` elements with a bare
`int(...)`. A non-numeric attribute - `failures="abc"`, or an empty string from a half-written report - raises
an uncaught `ValueError` traceback out of both `count()` (`junit_count.py:24`, pre-existing) and
`list_failures()` (`junit_count.py:56`, introduced with the summary-only branch) instead of the documented
clean exit 2.

Found by agent/reviewer-18 while re-reviewing T-0023 and filed there as MAJOR, non-blocking, because the
failure is symmetric (both paths break the same way, so the count and the naming cannot disagree) and loud
(a traceback, not a silent zero) - and `ops/test`'s parse guard still catches it via `read`'s empty stream.
So there is no false green today. It is still the wrong failure: the module's docstring promises exit 2 for an
unreadable report, and a traceback is what a reader mistakes for a broken runner rather than a broken report.

- Treat a non-numeric or missing count attribute the way a parse error is treated: `junit_count: cannot read
  <path>: ...` on stderr, exit 2, on BOTH paths.
- Demonstrate red first with a hand-built `<testsuite tests="1" failures="abc">`: show the traceback, then
  show the clean exit 2.
- `ops/lib/check-failure-naming` (P-OPS-02) already generates malformed-report fixtures; add this shape to it
  so the property is guarded rather than just fixed.

## Log
- 2026-09-07T16:38:26Z claimed by agent/builder-61; lease until 2026-09-07T19:38:26Z
- 2026-09-07T17:20:00Z builder-6: widened `touches:` to add `ops/lib/check-failure-naming` (the brief asks
  the P-OPS-02 guard in that file to be extended, and `ops/lib/junit_count.py` alone does not cover it).
  Note: the pre-commit hook exempts `queue/*` paths unconditionally (`.githooks/pre-commit`: `[[ "$f" ==
  queue/* ]] && ok=1`), so the queue-file move at the end of this task needed no `touches:` entry.

### RED — hand-built `<testsuite tests="1" failures="abc">`, pre-fix code

  ```
  $ python ops/lib/junit_count.py bad-failures.xml
  Traceback (most recent call last):
    ...
    File "...\ops\lib\junit_count.py", line 24, in count
      failed += int(s.get("failures", 0)) + int(s.get("errors", 0))
  ValueError: invalid literal for int() with base 10: 'abc'
  exit=1

  $ python ops/lib/junit_count.py --list-failures bad-failures.xml
  Traceback (most recent call last):
    ...
    File "...\ops\lib\junit_count.py", line 56, in list_failures
      n = int(s.get("failures", 0) or 0) + int(s.get("errors", 0) or 0)
  ValueError: invalid literal for int() with base 10: 'abc'
  exit=1
  ```
  Both paths crash with an uncaught traceback and exit 1, not the documented exit 2.

### Fix applied

  `ops/lib/junit_count.py`: added `_count_attr(el, name)`, used by both `count()` and `list_failures()` for
  every summary-only-suite attribute (`tests`, `failures`, `errors`, `skipped`). An absent attribute still
  defaults to 0. A present attribute that is not a valid non-negative int now raises `UnreadableReport`
  (`failures='abc' is not an integer`), caught in `main()` alongside `OSError`/`ET.ParseError` on BOTH the
  counting and `--list-failures` paths, producing the documented `junit_count: cannot read <path>: ...` /
  exit 2. This also removed `list_failures()`'s `int(x or 0)` fallback, which silently coerced an
  attribute-present-but-empty string to 0 instead of raising - that fallback was the source of an
  undocumented asymmetry with `count()` (see the check-failure-naming RED run below, `attr-empty.xml`).

### GREEN — same fixture, fixed code

  ```
  $ python ops/lib/junit_count.py bad-failures.xml
  junit_count: cannot read .../bad-failures.xml: failures='abc' is not an integer
  exit=2

  $ python ops/lib/junit_count.py --list-failures bad-failures.xml
  junit_count: cannot read .../bad-failures.xml: failures='abc' is not an integer
  exit=2
  ```

### Adjacent shapes (step 4) - decision per shape, all exercised via hand-built fixtures and then folded
  into `ops/lib/check-failure-naming` as permanent fixtures:

  - `errors="1.5"` -> **unreadable**, exit 2 on both paths (`errors='1.5' is not an integer`). A float
    string is not an integer count; `int("1.5")` already raised, same as `"abc"`.
  - `failures=""` -> **unreadable**, exit 2 on both paths (`failures='' is not an integer`). Chosen
    deliberately over the pre-fix behavior, where `list_failures()`'s `int(x or 0)` silently turned an empty
    string into 0 while `count()` raised - an asymmetry that itself violates P-OPS-02's "unreadable reports
    fail closed on both paths" invariant. An attribute that is *present* but empty is not "no attribute"; it
    is exactly as untrustworthy as `"abc"`.
  - `failures="-1"` (valid int, negative) -> **unreadable**, exit 2 on both paths
    (`failures='-1' is negative`). Pre-fix, this did not crash at all: `count()` silently returned
    `total=1 failed=-1 skipped=0` and `--list-failures` printed "`broken: -1 failure(s) in a summary-only
    suite`" with exit 0 - the worst outcome of the three, a clean-looking answer that is simply wrong (and
    would corrupt `check-failure-naming`'s own `[[ "$n" -gt 0 ]]` arithmetic downstream). A negative failure
    count can never be legitimate, so it is now rejected exactly like a non-numeric one.
  - missing `tests=` attribute -> **NOT unreadable**, counted normally (`total=0 failed=1 skipped=0`,
    exit 0). `_count_attr` only treats a *present* value as a claim that must parse; an absent attribute is a
    terse-but-valid summary suite (this is the pre-existing, correct behavior for e.g. `errors-only.xml`,
    which already omits `failures=`), and elevating "absent" to "unreadable" would reject reports that were
    never broken.

### RED - `bash ops/lib/check-failure-naming` against the pre-fix `junit_count.py`, extended fixtures

  Extended the script (new fixtures `attr-non-numeric.xml`, `attr-float.xml`, `attr-empty.xml`,
  `attr-negative.xml`, `attr-missing-tests.xml`; the unreadable-report loop now asserts exit code is
  *exactly* 2 and stderr matches `^junit_count: cannot read `, not just "non-zero", so a traceback-and-exit-1
  is caught instead of slipping past a bare `&&` non-zero check). Ran it with `ops/lib/junit_count.py`
  temporarily replaced by `git show HEAD:ops/lib/junit_count.py` (the pre-fix blob, since this task's fix was
  still uncommitted) - the tracked file was restored immediately after, nothing pre-fix was ever committed:

  ```
  P-OPS-02: counting path exited 1 (want 2) on unreadable attr-non-numeric.xml: Traceback (most recent call last): ...
    ValueError: invalid literal for int() with base 10: 'abc'
  P-OPS-02: counting path did not print the clean cannot-read message on attr-non-numeric.xml: Traceback ...
  P-OPS-02: --list-failures exited 1 (want 2) on unreadable attr-non-numeric.xml: Traceback ...
  P-OPS-02: --list-failures did not print the clean cannot-read message on attr-non-numeric.xml: Traceback ...
  P-OPS-02: counting path exited 1 (want 2) on unreadable attr-float.xml: Traceback ... ValueError: invalid literal for int() with base 10: '1.5'
  P-OPS-02: counting path did not print the clean cannot-read message on attr-float.xml: Traceback ...
  P-OPS-02: --list-failures exited 1 (want 2) on unreadable attr-float.xml: Traceback ...
  P-OPS-02: --list-failures did not print the clean cannot-read message on attr-float.xml: Traceback ...
  P-OPS-02: counting path exited 1 (want 2) on unreadable attr-empty.xml: Traceback ... ValueError: invalid literal for int() with base 10: ''
  P-OPS-02: counting path did not print the clean cannot-read message on attr-empty.xml: Traceback ...
  P-OPS-02: --list-failures exited 0 (want 2) on unreadable attr-empty.xml:
  P-OPS-02: --list-failures did not print the clean cannot-read message on attr-empty.xml:
  P-OPS-02: counting path exited 0 (want 2) on unreadable attr-negative.xml: total=1 failed=-1 skipped=0
  P-OPS-02: counting path did not print the clean cannot-read message on attr-negative.xml: total=1 failed=-1 skipped=0
  P-OPS-02: --list-failures exited 0 (want 2) on unreadable attr-negative.xml: broken: -1 failure(s) in a summary-only suite - the report carries no per-test detail, look in the tier's own log
  P-OPS-02: --list-failures did not print the clean cannot-read message on attr-negative.xml: broken: -1 failure(s) in a summary-only suite - the report carries no per-test detail, look in the tier's own log
  exit=1
  ```
  Notably `attr-empty.xml` and `attr-negative.xml` did not even traceback on `--list-failures` /
  `count()` respectively pre-fix - they returned wrong, silently-green-looking answers (exit 0), which the
  strengthened "exit exactly 2 + clean message" assertion catches where a bare "exit non-zero" check would
  not have.

### GREEN - same run, fixed `junit_count.py` restored

  ```
  P-OPS-02: every counted failure is named; unreadable reports fail closed
  exit=0
  ```

### Final verification (fresh worktree; `cd services/api && npm ci --no-audit --no-fund` run first per T-0040)

  ```
  $ bash ops/test
  ... (linux suite output) ...
  TESTS linux=86/76 ios=skipped failed=0 skipped=0
  OK
  exit=0
  ```
  Note: task brief text said to expect `linux=93/76`; this worktree (stacked on task/T-0023, main merged in)
  actually reports `linux=86/76 failed=0`, above the floor (76) with no failures - reporting the number
  actually observed rather than the expectation, per CLAUDE.md ("a smaller honest result beats a larger
  claimed one"). Not investigated further as it is outside this task's scope (no test count changed by this
  fix - `_count_attr`/`UnreadableReport` add no new test files).

  ```
  $ bash ops/check-pins
  PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux
  exit=0
  ```
  `python ops/lib/pins.py --verbose` confirms `ok P-OPS-02` individually (ran against the fixed
  `junit_count.py` and the extended `check-failure-naming`).

  ```
  $ bash ops/queue-check
  QUEUE OK (44 tasks)
  exit=0
  ```
