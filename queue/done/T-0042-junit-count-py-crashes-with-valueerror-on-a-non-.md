---
id: T-0042
title: junit_count.py crashes with ValueError on a non-numeric failures= or errors= attribute
state: done
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

## Review — agent/reviewer-25 — VERDICT: FAIL

Re-derived independently rather than trusted, all against the actual worktree / git blobs (not the task
file's prose): the RED tracebacks (step 1), the GREEN clean-exit-2 (step 1), the pre-fix `attr-empty.xml` /
`attr-negative.xml` asymmetry claims (step re: "worth checking hard") by running `git show HEAD~1:...` code
directly, the `check-failure-naming` RED-against-pre-fix / GREEN-against-fix run (step 2), and that the
"exits non-zero" -> "exits exactly 2 + clean message" tightening is a real code change (diffed `HEAD~1` vs
`HEAD` of `ops/lib/check-failure-naming` myself; old assertion was `cmd >/dev/null 2>&1 && note "exited 0"`,
which only fires on exit 0 and would NOT have caught a traceback-with-exit-1 - so the strengthening is
load-bearing, not cosmetic). All matched the task file's transcripts byte-for-byte where compared. Took on
trust: nothing load-bearing: the prose reasoning for each judgement call in step 4 was independently
evaluated, not just read.

**Verified true, both pre-fix claims (step "worth checking hard"):**
- `attr-empty.xml` (`failures=""`) pre-fix: `count()` raises `ValueError: invalid literal for int() with
  base 10: ''` (exit 1, traceback), `list_failures()` returns cleanly with exit 0 and **no output** -
  confirmed by direct execution against `git show HEAD~1:ops/lib/junit_count.py`. The asymmetry claim is
  correct: `list_failures()`'s old `int(x or 0)` silently coerced the empty string to 0 while `count()`'s
  bare `int(x)` raised on the identical input.
- `attr-negative.xml` (`failures="-1"`) pre-fix: `count()` returns `total=1 failed=-1 skipped=0` (exit 0,
  no crash - `int("-1")` succeeds, it's just negative), `list_failures()` prints `broken: -1 failure(s) in a
  summary-only suite - ...` (exit 0). Confirmed: this was the "worst outcome," a clean-looking wrong answer
  on both paths, and P-OPS-02's own pre-existing fixture set never generated a negative-attribute report, so
  the pin was green while its stated invariant was already broken. Both claims stand.

**MAJOR — `ops/lib/junit_count.py:89` (`list_failures`) vs `:53`/`:55` (`count`) — the fix reintroduces the
exact asymmetry it was written to close, on two of the four attributes.**

`count()`'s summary-only branch validates all four attributes through `_count_attr` (`tests` at line 53,
`failures`+`errors` at line 54, `skipped` at line 55). `list_failures()`'s summary-only branch (line 89) only
calls `_count_attr(s, "failures")` and `_count_attr(s, "errors")` - it never touches `tests` or `skipped` at
all. The comment directly above it (lines 86-88) claims "Same `_count_attr()` as `count()`: a
missing/malformed/negative attribute must fail identically on both paths" - that claim is false for `tests=`
and `skipped=`.

Reproduced against the shipped fix (`HEAD`, not pre-fix):

  ```
  $ cat testsbad.xml
  <?xml version="1.0"?><testsuite tests="abc" failures="0"></testsuite>

  $ python ops/lib/junit_count.py testsbad.xml
  junit_count: cannot read testsbad.xml: tests='abc' is not an integer
  exit=2

  $ python ops/lib/junit_count.py --list-failures testsbad.xml
  (no output)
  exit=0
  ```

  Same result for a bad `skipped=` with valid `failures=`/`errors=` (`<testsuite tests="1" failures="0"
  skipped="abc">`): `count()` -> exit 2 `skipped='abc' is not an integer`; `--list-failures` -> exit 0, no
  output.

This is precisely the failure class P-OPS-02 exists to forbid (pin statement: "...and an unreadable report
fails closed on both paths") and precisely what the owner called "the worst outcome... a clean-looking answer
that is simply wrong" when describing the pre-fix `failures="-1"` case - here reproduced via a different
attribute, post-fix. None of the five new fixtures (`attr-non-numeric`, `attr-float`, `attr-empty`,
`attr-negative`, `attr-missing-tests`) isolate a bad `tests=`/`skipped=` from valid `failures=`/`errors=`, so
`ops/lib/check-failure-naming` does not catch it - confirmed by running the extended pin against the shipped
`junit_count.py`: still prints `P-OPS-02: every counted failure is named; unreadable reports fail closed` /
exit 0.

Concrete failure scenario: any caller that invokes `--list-failures` on a report without first (or ever)
calling the counting path on it - e.g. a human or agent debugging a red run by re-running
`ops/lib/junit_count.py --list-failures` directly against one saved report, exactly the manual workaround
this tool's own docstring says it exists to avoid ("cost a debugging round of re-running every tier by hand
in containers") - sees a clean "nothing failed" (exit 0, empty output) for a report that is, by the tool's
own counting path, unreadable. Today's one caller, `ops/test`, happens not to hit this: it calls `count()`
per tier first (`ops/test:30`, `:60`) and aborts via `read`'s failure (`|| { echo "FAIL: could not parse...";
exit 1; }`) before ever reaching the later `--list-failures` call (`ops/test:93`), so there is no false green
in `ops/test` today - same mitigant reviewer-18 originally cited for the parent bug. But that safety is
incidental sequencing in one caller, not a property either function documents or enforces, and it is exactly
the kind of asymmetry this task's own fix, pin extension, and inline comments claim to have eliminated.
Failing this review because the invariant under test - the one this task exists to restore and guard - does
not hold end-to-end, and the extended pin does not catch the gap despite covering the adjacent attributes.

**Minor / informational, not blocking:**
- `ops/lib/junit_count.py:34` (`int(raw)`): whitespace-padded (`failures=" 3 "`) and explicit-plus
  (`failures="+3"`) values are silently accepted (Python's `int()` strips whitespace and allows a leading
  `+`), looser than the "not a valid non-negative integer (non-numeric, empty, or negative)" framing implies.
  Functionally harmless (parses to the correct count); unlikely to occur from a real xunit writer.
- `ops/lib/junit_count.py:34`/`:37`: no upper bound. `failures="99999999999999999999999999"` is accepted and
  printed as-is. Not a regression (pre-fix `int()` was equally unbounded) but worth noting: feeding a count
  that large into `ops/test`'s bash `$(( ))` arithmetic silently wraps to a large *negative* number (verified:
  `f=99999999999999999999999999; echo $((0+f))` -> `-2537764290115403777`) - the same "clean-looking wrong
  answer" class this task fixed for the literal-negative case, reachable here via overflow instead. Requires
  an adversarial/corrupted report; not blocking, flagging for a follow-up task.
- `hex ("0x10")`, `float ("3.0")`, `tests=` non-numeric with everything else valid: all correctly rejected
  (exit 2) on the counting path - `int(..., base=10)` does not accept `0x` prefixes or decimal points.
- A suite with BOTH `<testcase>` children and a `failures=` attribute takes the per-testcase branch
  exclusively; `_count_attr` never runs and the attribute is never validated or compared against the
  per-testcase count. Confirmed via `<testsuite tests="2" failures="5"><testcase>...` -> counted from
  testcases only (`failed=1`), `failures="5"` silently ignored. Pre-existing branching (identical pre- and
  post-fix, not part of this diff's scope) - per-testcase evidence is the correct ground truth to prefer, so
  not treating this as a defect, just documenting it was checked.
- A `<testsuites>` root's own `failures=` attribute is never read (only descendant `<testsuite>` elements
  are, via `root.iter("testsuite")`); a root-only `<testsuites failures="99"></testsuites>` with no nested
  `<testsuite>` silently counts as `total=0 failed=0`. Also pre-existing / unrelated to the int-parsing fix,
  not introduced here.
- Duplicate XML attributes (e.g. `failures="1" failures="2"` on one element) are already rejected by the XML
  parser itself (`xml.etree.ElementTree` raises `ET.ParseError: duplicate attribute`) before `_count_attr` is
  ever reached - not a gap.

**File modes (step 6):** `git ls-files -s` shows `ops/lib/check-failure-naming` 100755 (as expected) and
`ops/lib/junit_count.py` **100755, not 100644** as this review's brief assumed. Checked history
(`git log --follow -p -- ops/lib/junit_count.py`): the file was created 100644 and flipped to 100755 in
commit `b3218b6` (2026-09-06), before this task existed; this task's commit (`b4a6e1a`) changed neither
file's mode (`git diff HEAD~1 HEAD` shows no mode lines). So "modes unchanged by this task" holds, but the
brief's expected value for `junit_count.py` was stale - 100755 is actually correct per P-OPS-01 ("every
script in ops/... is committed with the executable bit"), confirmed via `bash ops/lib/check-exec-bits` ->
`P-OPS-01: 25 files, 15 required present, all modes correct`.

**Verification commands, exact output (fresh run, this worktree, after `cd services/api && npm ci --no-audit
--no-fund`):**

  ```
  $ bash ops/test
  ...
  TESTS linux=86/76 ios=skipped failed=0 skipped=0
  OK
  exit=0
  ```
  86/76 confirmed correct for this branch (stacked on `task/T-0023`, no T-0038 Dockerfile tests) - matches
  the owner's observed number exactly, re-derived independently rather than trusted.

  ```
  $ bash ops/check-pins
  PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux
  exit=0
  ```

  ```
  $ bash ops/queue-check
  QUEUE OK (44 tasks)
  exit=0
  ```

All three green in isolation, consistent with the task file's claims. Failing this review regardless, because
the property under review - P-OPS-02's "unreadable reports fail closed on both paths," which this task's own
diff and pin extension claim to restore - does not hold for the `tests=`/`skipped=` attributes in
`list_failures()`, and the extended pin fixtures do not catch it. Leaving in `queue/review/` for
agent/builder-6 to fix `list_failures()` to validate `tests=`/`skipped=` via `_count_attr` (or explain why it
should not) and add a fixture that isolates a bad `tests=`/`skipped=` from valid `failures=`/`errors=`.

- 2026-09-07T18:10:00Z builder-6: fixed reviewer-25's finding. Correction to my own log: `ops/lib/junit_count.py`
  is 100755, not 100644 - my earlier log entry repeated a wrong assumption from the brief; the mode was
  already correct (P-OPS-01) and this task's commits never touched it.

### The bug, confirmed

  `list_failures()` (the old line 89) ran `_count_attr` on `failures=`/`errors=` only; `count()` (lines 53-55)
  ran it on all four (`tests`, `failures`, `errors`, `skipped`). The inline comment directly above line 89
  claimed the two "fail identically" - false for `tests=`/`skipped=`. Reproduced exactly as reviewer-25
  described, against the code as shipped in commit b4a6e1a:

  ```
  $ python ops/lib/junit_count.py testsbad.xml          # <testsuite tests="abc" failures="0" errors="0">
  junit_count: cannot read testsbad.xml: tests='abc' is not an integer
  exit=2
  $ python ops/lib/junit_count.py --list-failures testsbad.xml
  (no output)
  exit=0
  ```

### Fix: one shared validation path, not two that can drift

  Added `_suite_counts(s)` - the single place a summary-only `<testsuite>`'s `tests=`/`failures=`/`errors=`/
  `skipped=` are read and validated via `_count_attr`. `count()` now calls it for `(total, failed, skipped)`;
  `list_failures()` now calls it too and discards `tests`/`skipped`, keeping only the failed count - it still
  needs the validation side-effect even though it has no use for those two values. This makes "validate a
  different subset" structurally impossible rather than a discipline to remember next time. Rewrote the false
  comment above the `list_failures()` call site to state what the shared path actually guarantees.

  ```
  $ python ops/lib/junit_count.py testsbad.xml
  junit_count: cannot read .../testsbad.xml: tests='abc' is not an integer
  exit=2
  $ python ops/lib/junit_count.py --list-failures testsbad.xml
  junit_count: cannot read .../testsbad.xml: tests='abc' is not an integer
  exit=2
  ```
  Same check with a bad `skipped=` (`tests="1" failures="0" errors="0" skipped="xyz"`) - identical result on
  both paths, both times `skipped='xyz' is not an integer`, exit 2.

### `ops/lib/check-failure-naming`: fixtures 8 and 9 isolate the gap

  Added `attr-bad-tests.xml` (`tests="abc" failures="0" errors="0"` - bad `tests=`, perfectly valid
  `failures=`/`errors=`, reviewer-25's exact shape) and `attr-bad-skipped.xml` (same idea via `skipped=`),
  folded into the existing "exit exactly 2, clean message" loop.

  RED, run against the previously-shipped (pre-this-fix) `ops/lib/junit_count.py` - `git show
  HEAD:ops/lib/junit_count.py` (commit b4a6e1a, the gapped version) copied in temporarily, the tracked file
  restored immediately after, nothing gapped ever re-committed:

  ```
  P-OPS-02: --list-failures exited 0 (want 2) on unreadable attr-bad-tests.xml:
  P-OPS-02: --list-failures did not print the clean cannot-read message on attr-bad-tests.xml:
  P-OPS-02: --list-failures exited 0 (want 2) on unreadable attr-bad-skipped.xml:
  P-OPS-02: --list-failures did not print the clean cannot-read message on attr-bad-skipped.xml:
  exit=1
  ```
  This is the pin passing over the gap the first time, reproduced on demand: `count()`'s half of the loop
  never complained (it already validated all four attributes), only `--list-failures`'s half did, exactly
  the asymmetry under review.

  GREEN, same run, fixed `junit_count.py` restored:

  ```
  P-OPS-02: every counted failure is named; unreadable reports fail closed
  exit=0
  ```

### The two non-blocking notes - decided, not shrugged

  - **Whitespace- and `+`-padded numerics** (`" 3 "`, `"+3"`): left accepted, unchanged from before this
    fix. `int("  3  ")` and `int("+3")` are unambiguously the value 3 under Python's own integer grammar -
    there is no corruption story for them the way there is for `"abc"` (not a number at all), `""` (present
    but empty), or a negative value (a count that cannot exist). Rejecting them would invent a stricter
    format than JUnit's schema requires or any real writer has been observed to violate, purely to reject
    inputs that are not actually wrong. Verified: `<testsuite tests=" 3 " failures="+1" errors="0"
    skipped="0">` -> `total=3 failed=1 skipped=0`, exit 0.
  - **No upper bound / bash arithmetic overflow**: fixed, not left as a note. Added `_MAX_COUNT =
    1_000_000_000` in `_count_attr` - comfortably below both 32- and 64-bit signed integer ranges (so it can
    never overflow `ops/test`'s `linux_total=$((linux_total + t))` accumulation) and far beyond any real
    report's test count. A count attribute above it now raises `UnreadableReport` ("implausibly large"),
    exit 2, same as negative. Verified: `<testsuite tests="1" failures="123456789012345678901234567"
    errors="0" skipped="0">` (27 digits) -> `junit_count: cannot read ...: failures='123456789012345678901234567'
    is implausibly large (> 1000000000)`, exit 2, both paths. This was the one of the two worth more than a
    shrug: it turned a garbage report into a silently negative failure count reaching `ops/test`'s shell
    arithmetic, not merely a differently-formatted valid one.

### Final verification, fixed code (fresh worktree; `services/api && npm ci --no-audit --no-fund` already run)

  ```
  $ bash ops/test
  ...
  TESTS linux=86/76 ios=skipped failed=0 skipped=0
  OK
  exit=0

  $ bash ops/check-pins
  PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux
  exit=0
  (python ops/lib/pins.py --verbose | grep OPS-02  ->  "ok      P-OPS-02")

  $ bash ops/queue-check
  QUEUE OK (44 tasks)
  exit=0
  ```

## Re-review — agent/reviewer-25 — commit 4bd5bbb — VERDICT: PASS

Re-derived rather than trusted: swapped `ops/lib/junit_count.py` for `git show b4a6e1a:ops/lib/junit_count.py`
(the exact code I originally FAILed) into this worktree, ran `bash ops/lib/check-failure-naming` myself, then
restored and re-ran. Also independently re-ran `bash ops/test`, `bash ops/check-pins`, `bash ops/queue-check`,
`git ls-files -s`, and wrote fresh attack fixtures of my own (not reused from the owner's) to probe the new
shared path, the `_MAX_COUNT` boundaries, and the multi-suite case. Took on trust: none of the load-bearing
claims - everything below was executed, not read.

**RED, re-derived (`ops/lib/junit_count.py` = `b4a6e1a`, `ops/lib/check-failure-naming` = current):**
  ```
  P-OPS-02: --list-failures exited 0 (want 2) on unreadable attr-bad-tests.xml:
  P-OPS-02: --list-failures did not print the clean cannot-read message on attr-bad-tests.xml:
  P-OPS-02: --list-failures exited 0 (want 2) on unreadable attr-bad-skipped.xml:
  P-OPS-02: --list-failures did not print the clean cannot-read message on attr-bad-skipped.xml:
  exit=1
  ```
  Matches the owner's transcript exactly: `count()`'s half of the loop raises no complaint (it already
  validated all four attributes pre-fixup) - only the `--list-failures` half fails, isolating exactly the gap
  I reported. File restored immediately after (`diff` against the pre-swap copy came back empty,
  `git status --porcelain` clean).

**GREEN, re-derived (file restored to `HEAD`):**
  ```
  P-OPS-02: every counted failure is named; unreadable reports fail closed
  exit=0
  ```

**Attacking the shared path (`_suite_counts`, `ops/lib/junit_count.py:56-69`):**
- *When is it called?* Identically gated in both functions: `count()` line 82-86 and `list_failures()` line
  116-120 both call it only inside `else:` (i.e. `cases = list(s.iter("testcase"))` is empty - summary-only
  suites). Built `<testsuite tests="abc" failures="1"><testcase name="a"><failure .../></testcase></testsuite>`
  (bad `tests=` AND a real `<testcase>` child): neither `count()` nor `--list-failures` validates `tests=`
  here - both silently take the per-testcase branch (`total=1 failed=1`, `a - x` / exit 0 on both). Symmetric:
  the drift did not move, this shape was already out of scope pre-fixup too (per-testcase evidence takes
  priority over the summary attribute in both paths, unchanged by this diff).
- *End-to-end invariant with a bad attribute AND genuine per-testcase failures in the same report:* built a
  two-`<testsuite>` file - one with a real `<failure>` on a `<testcase>`, the other summary-only with
  `skipped="xyz"`. Both `count()` and `--list-failures` exit 2 with `skipped='xyz' is not an integer` on the
  whole file - no partial credit, the one bad suite makes the entire report unreadable on both paths, exactly
  as the invariant requires (counted>0-implies-named>0 doesn't even get a chance to disagree, because both
  paths refuse to answer at all).
- *Do valid-report numbers still match?* `bash ops/test` -> `TESTS linux=86/76 ios=skipped failed=0
  skipped=0` / `OK` - identical to the pre-fixup run, no regression in the counting arithmetic itself.

**`_MAX_COUNT` boundaries (`ops/lib/junit_count.py:28,51-52`), re-derived with my own fixtures:**
  ```
  tests="1000000000"  -> total=1000000000 failed=0 skipped=0 / exit=0   (at the ceiling: accepted)
  tests="1000000001"  -> cannot read ...: tests='1000000001' is implausibly large (> 1000000000) / exit=2
  tests="50000"        -> total=50000 failed=1 skipped=0 / exit=0        (plausible large suite)
  tests="1000000"      -> total=1000000 failed=1 skipped=0 / exit=0      (very large but real-shaped)
  ```
  Stating explicitly, as asked: 1e9 will not reject any real report. The largest known real-world single
  JUnit-style test suites run to the low hundreds of thousands / low millions of cases at the outside
  (verified 1,000,000 passes clean above); 1,000,000,000 is at least three orders of magnitude beyond that,
  with no realistic report shape anywhere near the ceiling. It is also comfortably inside bash's signed
  64-bit range even summed across many suites/files, so `ops/test`'s `$(( ))` accumulation cannot wrap from
  any combination of reports this cap allows through. No plausible-report-rejection risk.
- Also re-verified the owner's whitespace/`+`-sign claim directly: `tests=" 3 " failures="+1" errors="0"
  skipped="0"` -> `total=3 failed=1 skipped=0`, exit 0 - unchanged, still an unambiguous non-negative integer
  under Python's own grammar, no corruption story. Agree with leaving this accepted.
- Re-verified the owner's 27-digit overflow-fix claim directly: `failures="123456789012345678901234567"` ->
  `cannot read ...: failures='123456789012345678901234567' is implausibly large (> 1000000000)`, exit 2 on
  both paths. This closes the minor/informational bash-arithmetic-overflow note from my first review; no
  follow-up task needed.

**File modes (unchanged by this fixup too):** `git ls-files -s` -> `ops/lib/check-failure-naming` 100755,
`ops/lib/junit_count.py` 100755. Confirmed correct per P-OPS-01, `bash ops/lib/check-exec-bits` -> `P-OPS-01:
25 files, 15 required present, all modes correct`.

**Verification, exact output, this run:**
  ```
  $ bash ops/test
  ...
  TESTS linux=86/76 ios=skipped failed=0 skipped=0
  OK
  exit=0

  $ bash ops/check-pins
  PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux
  exit=0

  $ bash ops/queue-check
  QUEUE OK (44 tasks)
  exit=0
  ```
  `python ops/lib/pins.py --verbose` confirms `ok P-OPS-01` and `ok P-OPS-02` individually. `python -m
  py_compile ops/lib/junit_count.py` compiles clean.

The MAJOR finding from my first review (`list_failures()` not validating `tests=`/`skipped=`) is fixed via a
single shared `_suite_counts()` validation path that both functions call under identical gating, closing the
class of bug rather than just the two attributes I happened to demonstrate. The pin now isolates it with
dedicated fixtures (`attr-bad-tests.xml`, `attr-bad-skipped.xml`) that I independently reproduced red-then-
green. The two non-blocking notes from my first review were each explicitly decided: the overflow risk was
fixed with a well-justified, non-rejecting-any-real-report ceiling; the whitespace/`+` permissiveness was
kept with a documented rationale I agree with. No new asymmetry found in the consolidated path. PASS.
