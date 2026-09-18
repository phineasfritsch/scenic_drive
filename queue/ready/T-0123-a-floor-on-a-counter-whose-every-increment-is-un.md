---
id: T-0123
title: mutation-test the ops checks; static analysis of bash floors does not work
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/mutate/, ops/check-tests, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/check-tests` (P-TEST-02) catches "an assertion whose expected value comes from the thing it checks" in
Swift. Its own Brief states the limit: it reads Swift, and the ninth instance of that defect found in this
session was in **bash** - `ops/lib/check-review-remedy`, where a reviewer showed that

  * a case-1 assertion `grep -q "blocked" "$out"` is satisfied by the fixture's own path string, always; and
  * the floor `if [[ $cases -ne 4 ]]` guards a counter incremented only by unconditional straight-line code,
    so `$cases` is always exactly 4 and the floor cannot fail.

This task was opened to do for bash what `ops/check-tests` does for Swift. **A static version was written
and it does not work.** That is recorded below rather than shipped, because a check that answers wrongly is
worse than no check, and this one answered wrongly on the exact file that motivated it.

## The measurement that killed it

`ops/lib/check-bash-floors.py` tracked conditional nesting with line regexes: `if/while/until/for/case` and
trailing `then`/`do` open a level, `fi/done/esac` close one. Run against
`origin/task/T-0063~1:ops/lib/check-review-remedy`, the real pre-fix file:

    floors found:  ('cases', 'ne', '4'), ('fail', 'ne', '0'), ... 16 in all
    cases     depths=[0, 1, 5, 8, 12]
    fail      depths=[0]

**Depth 12 in a 245-line script.** `OPENERS` matches more often than `CLOSERS` closes - `if ...; then` on
one line fires both the `^if` branch and the trailing-`then` branch - so the depth ratchets upward and never
comes back. The consequences, both on the same file:

  * **False negative on the real defect.** Because one recorded depth for `cases` is not 0, the
    `all(depth == 0)` test is false and `[[ $cases -ne 4 ]]` - the finding this check exists for - is not
    flagged.
  * **False positive on a sound floor.** Only one assignment to `fail` was matched; the `fail=1` inside the
    `bad()` helper was missed, so `[[ $fail -ne 0 ]]` was reported as unable to fail when it is fine.

A wider regex does not fix this. Bash nesting is not a regular language, `case` arms close with `;;`,
`&&`/`||` make a one-line command conditional, functions and subshells introduce scopes, and an assignment
can appear anywhere on a line. Getting this right needs a real parser, and a check nobody can be confident
in is a check that gets an escape-hatch comment on its first false positive.

## What to do instead, and why it is the better answer

**Mutation-test the checks themselves.** That is the approach that actually worked everywhere else in this
session: `ops/mutate/handoff.py`, `budget.py`, `routescore.py`, `corridorspeeds.py` and `retrace.py` each
break their subject in named ways and require a NAMED assertion to notice, report `trapped` and
`compile-only` separately so a crash is not scored as a catch, carry an `EQUIVALENT` list asserted the other
way round, and prove themselves non-vacuous by running with the tests removed.

The same harness shape applies directly to a bash check: mutate the CHECK, and require its own case suite to
go red. It is dynamic, so it needs no parser; it asks the only question that matters - can this assertion
fail? - and it answers by making it fail.

The reviewer of PR #52 did exactly this by hand and found both defects with it: emptying
`for mode in empty unreadable; do` to `for mode in ; do` produced `REVIEW REMEDY OK (4 cases)` and exit 0
with zero of case 4's assertions run. That is the mutation a harness would carry.

Do:

1. `ops/mutate/opschecks.py`, in the shape of the five existing harnesses, over the bash checks under
   `ops/lib/` that have their own case suites - `check-review-remedy`, `check-lock-lifecycle`,
   `check-queue-roundtrip`, `check-exec-bits`, `check-line-cap`, `check-touches-merge.py`.
2. Each check's suite must go RED for every mutation of the check it covers, and the harness must prove
   itself non-vacuous by emptying the case list.
3. **Carry the two mutations the PR #52 reviewer used**, verbatim, since they are known to have found real
   defects: the emptied `for mode in` loop, and `_paths_after_merge` replaced by the branch's own path.

**Do not resurrect the static check.** `ops/lib/check-bash-floors.py` was written, measured, and deleted;
the measurement is above so nobody has to rediscover it. If someone wants a static pass later, the bar is
that it must flag `[[ $cases -ne 4 ]]` and not flag `[[ $fail -ne 0 ]]` in that exact file, and it must be
demonstrated against both.

## Log

- Wrote `ops/lib/check-bash-floors.py`, ran it against `origin/task/T-0063~1`, measured the depths above,
  and deleted it. `python .artifacts/floors-against-history.py` reproduces the run; the file it tests is
  preserved at `.artifacts/crr-prefix.sh`.
