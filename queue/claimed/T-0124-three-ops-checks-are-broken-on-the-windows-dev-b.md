---
id: T-0124
title: three ops checks are broken on the Windows dev box because mktemp gives a path Windows python cannot open
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T17:25:15Z
lease_expires_at: 2026-09-08T19:25:15Z
worktree: .worktrees/T-0124
branch: task/T-0124
exclusive: []
touches: [ops/lib/check-lock-lifecycle, ops/lib/check-brief-required, ops/lib/check-failure-naming, ops/lib/tmpdir.sh, ops/lib/check-exec-bits, ops/lib/check-worktrees-demo, ops/lib/check-tmpdir-guard, ops/mutate/lock_lifecycle.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "bash ops/lib/check-lock-lifecycle, check-brief-required, check-failure-naming -> exit 0 on the Windows checkout"
  - "bash ops/check-pins -> P-OPS-02 no longer failed"
  - "RED: all three exit 1 today with a path error naming C:\\tmp\\tmp.XXXX"
---
## Brief

**Three verification checks do not run on the machine this project is driven from.** They are green in Linux
CI and broken in git-bash on the Windows checkout, which is where every agent actually invokes them.

    $ bash ops/lib/check-lock-lifecycle
    FAIL: review accepted a task that was not claimed (rc=2): python.exe: can't open file
    'C:\\tmp\\tmp.ASM3sx3tVQ\\ops\\lib\\queue.py': [Errno 2] No such file or directory
    LOCK LIFECYCLE FAIL                                                                    exit 1

    $ bash ops/lib/check-brief-required
    python.exe: can't open file 'C:\\tmp\\tmp.LBnyMFYgea\\ops\\lib\\queue.py'
    BRIEF CHECK FAIL                                                                       exit 1

    $ bash ops/lib/check-failure-naming
    P-OPS-02: a <failure> testcase was not named: junit_count: cannot read
    /tmp/tmp.fH9vq5U3Uo/per-case.xml: [Errno 2] No such file or directory                  exit 1

One cause, three files. `TMP="$(mktemp -d)"` in git-bash yields an MSYS path - `/tmp/tmp.XXXX` - and the
interpreter on PATH is a **Windows** python, which reads a leading `/` as a relative path and looks for
`C:\tmp\tmp.XXXX`. The same class as `ops/check-tests`, which died with
`can't open file 'C:\c\Users\...'` because `pwd` yields `/c/Users/...`; that one is fixed with `cygpath`.

**P-OPS-02 is red in `ops/check-pins` on this box for exactly this reason**, and identically red on a clean
`main`, so it has been read as "environmental" and stepped over. It is not environmental. It is a check that
cannot run where it is most needed.

## Why this matters more than a red line in a summary

The three affected checks are `check-lock-lifecycle` (P-PROC-02), `check-brief-required`, and
`check-failure-naming` (P-OPS-02). An agent working locally sees them fail for a reason that has nothing to
do with its change, learns that those lines are noise, and stops reading them. That is how a real failure
gets stepped over - and two of these three guard the queue protocol that the whole fleet depends on.

It also means **nobody has ever seen these three go red for a real reason on this box**, which by CLAUDE.md's
own standard makes them untested here.

Do:

1. A shared helper - `ops/lib/tmpdir.sh`, sourced - that makes a temp directory and returns a path the
   interpreter can open: `mktemp -d`, then `cygpath -w` when `cygpath` exists. On Linux and WSL there is no
   `cygpath` and the POSIX path is already right, so the helper is a no-op there.
2. Use it in all three. Do not inline `cygpath` three times: the next check to be written will copy whichever
   neighbour it happens to look at, and a helper is the only version of this that stays fixed.
3. **RED FIRST, and on the real thing.** The three transcripts above are the red run. After the fix each must
   exit 0 on this box, and `ops/check-pins` must stop reporting P-OPS-02 as failed. Record both.
4. Check whether the same pattern exists elsewhere: `git grep -n 'mktemp' -- ops .githooks` and confirm every
   hit either goes through the helper or never reaches a Windows interpreter.

**Do not fix this by exporting `PYTHON=` to a POSIX python.** That works on one machine and hides the defect
from everyone else; the checks must work with the interpreter that is actually on PATH. And do not delete
the temp-directory use in favour of writing into the worktree - these checks build throwaway repositories on
purpose, and a check that mutates the tree it is checking is a worse problem than this one.

## Log
- 2026-09-08T17:25:15Z claimed by agent/claude-opus-5; lease until 2026-09-08T19:25:15Z

    bash ops/lib/check-brief-required     exit 1 -> exit 0
    bash ops/lib/check-failure-naming     exit 1 -> exit 0
    bash ops/lib/check-lock-lifecycle     exit 1 -> exit 1, but for a different and already-filed reason
    bash ops/check-pins                   P-OPS-02 failed -> PINS ok=12 failed=0

### The fix

`ops/lib/tmpdir.sh`, sourced by all three. `portable_mktemp_d` runs `mktemp -d` and translates with
`cygpath -w` when `cygpath` exists; on Linux and WSL there is no `cygpath` and the POSIX path is already
right, so it is a no-op there. `portable_posix_path` gives the shell-side form back for the `rm -rf` trap,
because a backslash path inside a single-quoted trap is an escaping hazard and a trap that fails to fire
leaves a temp tree behind on every run.

A helper rather than three inline copies: the next check written will copy whichever neighbour its author
happens to open.

`ops/lib/check-worktrees` and `check-worktrees-demo` also call `mktemp -d`, and were left alone - their temp
paths never reach a Windows interpreter. Checked, not assumed.

### Making one check run for the first time found two more things

`check-lock-lifecycle` had never executed on this box. Once it could, it reported two failures that read like
defects in `cmd_review`:

    FAIL: review did not release the lock
    FAIL: review refused a task that holds no locks

**Neither was a defect in `cmd_review`.** `.artifacts/probe-review.py` runs the command in a throwaway tree
and shows what actually happens:

    review rc=1  T-9201: cannot read main, so whether merging this branch would duplicate the task file

`cmd_review` gained a merge rehearsal - it reads `main` to decide whether merging this branch would leave
two copies of the task file. The check's fixture is a bare directory with no git at all, so the rehearsal
cannot run and the command refuses. Fail-closed, and correct.

So **the check had gone stale against its own subject, and nothing could see it because the check could not
run.** Both halves are the point of this task. Fixed by giving `reset_repo` a real git repo with a `main`
branch; both failures are gone and the case now reads `ok: a task declaring no exclusive resources still
moves`.

### What remains red, and why it is not mine to fix here

    FAIL: queue-check not clean after review: QUEUE CHECK FAIL
     - only 1 task(s) visible, floor is 40

`cmd_check`'s `MIN_TASKS` floor against a one-task fixture. **Already filed as T-0091**, and independently
confirmed as pre-existing by the T-0063 fixer in the same session.

I did pad the fixture to 45 filler tasks and it did go green - and then reverted it. The padding is a
workaround for a filed task, it duplicates T-0091's decision about which population the floor should count,
and choosing that here would settle a question that belongs to that task. It is also how a fixture grows
until it is a second implementation of the thing under test.

Worth recording from the attempt: the 45 identical fillers were caught by the duplicate-brief guard
(`45 tasks share one brief`), which is T-0070's work doing exactly its job on a fixture built carelessly.

### Six of seven cases now pass

    ok: claim takes the lock and names the task
    ok: a hand git mv leaves the lock and queue-check FAILS - the red run this command exists for
    FAIL: queue-check not clean after review          <- T-0091
    ok: a task declaring no exclusive resources still moves
    ok: reviewer == owner refused, and the task did not move
    ok: a lock held by another task is left alone and the transition refuses
    ok: a task already in done/ cannot be handed to review

Before this task it produced no `ok` lines at all, because it could not open its own temp directory.


- 2026-09-08T19:05:00Z P-OPS-01 went red on this branch: `ops/lib/tmpdir.sh (script, should be 100755, is
  100644)`. Did NOT chmod +x. `tmpdir.sh` is a SOURCED library and the exec bit is not what makes it work.

### Why chmod +x would have been the wrong fix

Every call site is a `source`, and there are exactly three:

    ops/lib/check-brief-required:25    source "$(dirname "${BASH_SOURCE[0]}")/tmpdir.sh"
    ops/lib/check-failure-naming:26    source "$(dirname "${BASH_SOURCE[0]}")/tmpdir.sh"
    ops/lib/check-lock-lifecycle:27    source "$(dirname "${BASH_SOURCE[0]}")/tmpdir.sh"

`git grep -nE '(\./|bash |sh |exec )[^ ]*tmpdir\.sh'` over the tree returns nothing - no direct-execution
form exists. Nothing globs `ops/lib/*` and runs the matches; the checks are named one at a time, and CI
(`.github/workflows/linux-core.yml`) invokes everything as `bash ops/x`. `source` needs the READ bit and
never the exec bit, so 100755 would have asserted a mode the repo does not depend on.

This is the identical category to `ops/lib/*.py`, which T-0036 moved into the 100644 data bucket for exactly
this reason ("they are all invoked as `"$PY" ops/lib/x.py`"). `tmpdir.sh` is the stronger case of the two:
the `.py` helpers still carry a vestigial `#!/usr/bin/env python3`, and `tmpdir.sh` has NO shebang at all.
Shebang-iff-executable therefore already holds for it, and needed no change.

Fix: extended the documented exemption in `ops/lib/check-exec-bits` to `*.sh`, with the reasoning written
into the file the way the `.py` reasoning is. Also added `ops/lib/tmpdir.sh` to `REQUIRED` - three checks
source it, so it is load-bearing, and purpose #2 of that file is that load-bearing files are actually
tracked.

### The exemption is bounded so it cannot become a hole

A new `.sh` here inherits the data classification automatically, so an executable one could slip in
unnoticed. `check-exec-bits` now also fails when a `*.sh` under `ops/`/`.githooks/` HAS a shebang - that is
a file somebody means to execute, and it must not sit in the data bucket. Anchored on the committed blob's
first two bytes (an artifact), not on a comment.

### RED then GREEN - mutation demo in a throwaway repo, real index never touched

    M0 baseline                              rc=0  P-OPS-01: 34 files, 24 required present, all modes correct
    M1 ops/sane -> 100644                    rc=1  ops/sane (script, should be 100755, is 100644)
    M2 ro_cases.json -> 100755               rc=1  ops/lib/ro_cases.json (data, should be 100644, is 100755)
    M3 tmpdir.sh -> 100755                   rc=1  ops/lib/tmpdir.sh (data, should be 100644, is 100755)
    M4 tmpdir.sh untracked                   rc=1  load-bearing script(s) not tracked: ops/lib/tmpdir.sh
    M5 tmpdir.sh gains a shebang             rc=1  *.sh ... is the sourced-library extension, but has a shebang
    M6 restored                              rc=0  P-OPS-01: 34 files, 24 required present, all modes correct

M1 is the "does it still catch a genuinely wrong mode" case; M3 is the new rule proving it still fails in
the inverse direction rather than just ignoring `.sh`. Verified on the real tree:

    bash ops/lib/check-exec-bits   P-OPS-01: 34 files, 24 required present, all modes correct   exit 0
    bash ops/check-pins            PINS ok=12 skipped=0 pending=2 expired=0 failed=0 tier=linux exit 0

`ops/lib/tmpdir.sh` is byte-for-byte and mode-for-mode unchanged (still blob 58c9728, still 100644).
`ops/lib/check-exec-bits` was added to `touches:` before being edited.


- 2026-09-08 reviewer-pr79 returned FAIL with seven findings, five blocking. F1 was already closed by
  7c44cc2 before the review landed. F2-F6 are worked below. Every finding was re-reproduced first; none was
  taken on the reviewer's word, and none was closed by deleting a mutation or loosening an assertion.

### F5 first, because it was the dangerous one

CONFIRMED, against a non-destructive replica (`.artifacts/f5probe/ops/lib/probe-old`, verbatim preamble with
the destructive lines replaced by `echo`):

    $ cd .artifacts/f5probe/ops && bash lib/probe-old
    lib/probe-old: line 9: lib/tmpdir.sh: No such file or directory
    lib/probe-old: line 10: portable_mktemp_d: command not found
    TMP            = []
    WOULD RUN      : rm -rf "/queue" "/ops" "/.git"          exit=0

`source "$(dirname "${BASH_SOURCE[0]}")/tmpdir.sh"` sits AFTER the `cd` to the repo root, so a relative
`BASH_SOURCE[0]` no longer resolves; no `set -e`, status unchecked, `TMP=""`. On main the same invocation is
harmless (main has a plain `TMP="$(mktemp -d)"` and no source line at all), so this was new in this PR. `/`
is `C:\Program Files\Git` here and not writable, which is the only reason nothing was destroyed while the
reviewer was measuring it; on Linux CI it is writable.

Fix, in all three: source `ops/lib/tmpdir.sh` by its repo-root-relative path with the status checked, and
refuse on an empty `TMP` before any `rm`. `portable_mktemp_d` also now refuses to emit an empty or
non-existent path, so a caller that forgets the `|| exit` still cannot be handed `""`.

    $ cd .artifacts/f5probe/ops && bash lib/probe-new
    TMP            = [C:\Users\phineasf\AppData\Local\Temp\tmp.XD68z5ve2o]     exit=0

**Named test: `ops/lib/check-tmpdir-guard`.** Shadows `rm` with a logging shim that deletes nothing, runs
each of the three checks FROM `ops/` - the cwd that triggers the bug - and asserts that every path they hand
`rm` lives under a temp directory, and that the log is non-empty so the assertion cannot pass vacuously.

    RED  (subjects from 8978957, .artifacts/guard-red.sh):
      FAIL: check-brief-required asked rm for a path outside any temp directory, run from ops/:  []
      FAIL: check-failure-naming asked rm for a path outside any temp directory, run from ops/:  []
      FAIL: check-lock-lifecycle asked rm for a path outside any temp directory, run from ops/:
          [/queue] [/ops] [/.git]  (x6)
      TMPDIR GUARD FAIL                                                                          exit 1

    GREEN (this branch):
      ok: check-brief-required only ever deletes under a temp dir (1 path(s)), run from ops/
      ok: check-failure-naming only ever deletes under a temp dir (1 path(s)), run from ops/
      ok: check-lock-lifecycle only ever deletes under a temp dir (26 path(s)), run from ops/
      TMPDIR GUARD OK                                                                            exit 0

Writing that guard immediately caught a hole in the guard itself: the first version used `grep -v 'tmp\.'`,
and `rm -rf ""` - which is what the pre-fix trap degrades to when `portable_posix_path` is undefined - is an
empty line that command substitution strips, so two of the three pre-fix subjects passed. Now `awk` prints
each path in brackets and the empty path is offending. Both bracketed `[]` lines above are that fix working.

### F4 - the fixture never exercised the thing it was added for

CONFIRMED (`.artifacts/f4probe.sh`), building exactly what `reset_repo` built:

    --- what main tracks in the fixture ---            ops/lib/queue.py
    --- ls-tree -r --name-only main queue/ ---         0 path(s)

`git add -A` ran before `make_task`, so `_would_duplicate_on_merge` looped over an empty range and returned
`[]` unconditionally. The commit message spent five lines justifying a fixture that proved only that
`cmd_review` can get PAST the rehearsal.

Fixed on both sides. `reset_repo` now writes `.gitkeep` into every state dir and commits one task
(`T-9200`) that is not the subject of any case, so the loop body runs and the `/{tid}-` filter is exercised
in the negative direction. Two new named cases exercise it in the positive direction:

    ok: review refuses when merging would leave two copies of the task file, and nothing moves
    ok: review refuses when git cannot read main, instead of reading silence as 'no duplicate'

Case 8 puts the task file on `main` at a commit the branch does not contain - the real T-0063 shape - and
asserts the refusal names the path and that nothing moved. Case 9 removes `.git` and asserts fail-closed;
that behaviour is what the OLD fixture accidentally depended on, and nothing asserted it.

`make_task` now varies `title:` and the brief body by id: with more than one task in the fixture, identical
ones trip T-0070's duplicate-brief and duplicate-title guards, and a fixture that trips an unrelated guard
hides its own subject.

**The reviewer's own M2, re-run against both versions** (`.artifacts/m2-before-after.sh`; M2 =
`_would_duplicate_on_merge` -> `return []`):

    BEFORE (8978957)   baseline exit=1   M2 exit=1   M2 MISSED - output byte-identical to baseline
    AFTER  (this tree) baseline exit=0   M2 exit=1   M2 caught:
        - ok: review refuses when merging would leave two copies of the task file, and nothing moves
        + FAIL: the merge rehearsal did not refuse a duplicate main holds (rc=0): T-9107 -> queue/review/...

### F3 / F2 - the exit code was a constant 1, so no gate could read it

Case 3 asserted a bare `QUEUE OK`, which also demanded the fixture clear `cmd_check`'s `MIN_TASKS` floor of
40. A fixture of a handful of tasks cannot, so the case failed for a reason owned by **T-0091 - which is
claimed by agent/lock-lifecycle right now**, so `MIN_TASKS` was not mine to touch.

The property this check owns is the lock, not the whole queue's health. Case 3 now requires every problem
`cmd_check` reports to be gone EXCEPT the floor line, whose text is written out by hand as the single
exemption; any other problem line, including a new one, still fails the case. The verdict line
(`QUEUE OK`/`QUEUE CHECK FAIL`) is required first, so a crashed `cmd_check` cannot pass by printing no
problems at all. That is narrower than the old assertion in one axis and strictly wider in another: a new
queue-check problem introduced by `review` now fails this case, where before it was lost in a run that was
already red.

Acceptance criterion 1 is therefore met for real rather than amended:

    bash ops/lib/check-brief-required     exit 0
    bash ops/lib/check-failure-naming     exit 0
    bash ops/lib/check-lock-lifecycle     exit 0     <- was a constant 1, healthy or broken
    9 cases, all ok

**NOT fixed, and deliberately: F3's second half.** Nothing runs `check-lock-lifecycle` - no caller in `ops/`,
`.github/workflows/linux-core.yml` or `pins/PINS.yaml`. That is exactly **T-0090**, whose `touches:` is
`ops/test`. Wiring it into a gate here would take that task's decision and its file. `check-tmpdir-guard`
is unrun for the same reason and by the same argument; both are in `check-exec-bits`' `REQUIRED` list so
they cannot silently vanish in the meantime.

### F6 - "checked, not assumed" was checked wrongly

CONFIRMED (`.artifacts/f6probe.sh`), without running the demo - running it is what reparented the live repo
during review:

    A. ROOT=$(mktemp -d)              = /tmp/tmp.tC4xf2DNy9
       MSYS_NO_PATHCONV=1 git init -q -b main "$ROOT/repo"
       cd $ROOT/repo : FAILED - bash cannot reach where git built it
       git actually built it at: /c/tmp/tmp.tC4xf2DNy9/repo
    B. through portable_mktemp_d      = C:\Users\...\Temp\tmp.u23l0zGRwn
       cd $ROOT/repo : OK
    C. (cd /definitely/not/here && bash CHECK) -> rc=1, and run() wants 1 for every RED case

Git IS a Windows interpreter here; the PR body's claim was wrong. Three fixes in
`ops/lib/check-worktrees-demo`: `ROOT` comes from `portable_mktemp_d` (verified that the Windows form works
for bash `cd`/`mv`/redirection AND for `git -C` under `MSYS_NO_PATHCONV=1`); the fixture's top-level
`cd "$ROOT/repo"` is guarded, which is what let `remote add`/`commit`/`push`/`worktree add` run against the
live repository; and `run()` refuses to compare exit codes at all unless `$ROOT/repo/.git` exists, because
a crashed `cd` returns 1 and 1 is exactly the code every RED case wants.

    before:  MSYS_NO_PATHCONV=1 bash ops/lib/check-worktrees-demo   DEMO: 5 ok, 14 failed   exit 1
    after:   bash ops/lib/check-worktrees-demo                      DEMO: 19 ok, 0 failed   exit 0
             MSYS_NO_PATHCONV=1 bash ops/lib/check-worktrees-demo   DEMO: 19 ok, 0 failed   exit 0

`git status --porcelain` and `git rev-parse HEAD` captured either side of the `MSYS_NO_PATHCONV=1` run:
identical. Nothing was reparented.

### The gap cannot silently reopen: ops/mutate/lock_lifecycle.py

New, and written against the CORRECTED harness contract (`ops/mutate/guidance.py` on task/T-0129), not the
one every other harness in this repo shipped. `caught == len(MUTATIONS)`, full stop: trapped, compile-only
and skipped each FAIL the run; `--prove-vacuity` requires `caught == 0` AND `missed == len(MUTATIONS)`; the
EQUIVALENT arm requires MISSED specifically; SKIP is its own bucket. Subject is `ops/lib/queue.py`; a catch
requires a named case in `check-lock-lifecycle` to print `FAIL:`.

    caught      claim does not write the lock file
    caught      review moves the task but never releases the lock
    caught      a lock held by another task is released along with our own
    caught      reviewer == owner is accepted
    caught      review accepts a task that is not in claimed/
    caught      the merge rehearsal is deleted outright (return [])          <- reviewer-pr79's M2
    caught      the rehearsal asks whether the path exists instead of whether this branch can delete it
    caught      'git cannot answer' is read as 'no duplicate' instead of being refused
    caught      review writes the task to review/ without removing the claimed/ copy
    MISSED      rename the comprehension variable in the rehearsal's loop    <- EQUIVALENT, must be MISSED
    MISSED      split a tuple assignment into two statements                 <- EQUIVALENT, must be MISSED
    caught by a named case: 9 of 9   (trapped 0, compile-only 0, MISSED 0, skipped 0)          exit 0

    --prove-vacuity (check replaced by a stub that asserts nothing):
    caught by a named case: 0 of 9   (trapped 0, compile-only 0, MISSED 9, skipped 0)
    VACUITY PROOF OK                                                                           exit 0

Subject md5 identical before and after both runs; the tree is left pristine.

The last mutation exists to keep me honest about the change to case 3. Rewriting that assertion is the one
place here where a weaker-looking form replaced a stronger-looking one, so it needs a mutation that ONLY it
catches. `.artifacts/which-case.sh` shows which case fires:

    FAIL: queue-check reported a problem other than the MIN_TASKS floor after review:
         - queue/claimed/T-9102-demo.md: declares exclusive [scenic-index] but ... lock is not held
     - duplicate id T-9102: queue/review/T-9102-demo.md and queue/claimed/T-9102-demo.md
     - 2 tasks share one title: queue/claimed/T-9102-demo.md, queue/review/T-9102-demo.md

The old `grep -q "^QUEUE OK"` form could not have distinguished this from its own baseline, because its
baseline was already failing. Case 3 catches strictly more than it did before, not less.

### Verification

    bash ops/lib/check-brief-required                      BRIEF CHECK OK                       exit 0
    bash ops/lib/check-failure-naming                      P-OPS-02: every counted failure ...  exit 0
    bash ops/lib/check-lock-lifecycle                      LOCK LIFECYCLE OK (9 cases)          exit 0
    bash ops/lib/check-tmpdir-guard                        TMPDIR GUARD OK                      exit 0
    bash ops/lib/check-exec-bits                           P-OPS-01: 36 files, 26 required      exit 0
    bash ops/lib/check-worktrees-demo                      DEMO: 19 ok, 0 failed                exit 0
    bash ops/check-pins        PINS ok=12 skipped=0 pending=2 expired=0 failed=0 tier=linux     exit 0
    bash ops/queue-check                                   QUEUE OK (117 tasks)                 exit 0
    "$PY" ops/mutate/lock_lifecycle.py                     8 of 8                               exit 0
    "$PY" ops/mutate/lock_lifecycle.py --prove-vacuity     VACUITY PROOF OK                     exit 0

    bash ops/test              swift tier: 16 tests in 3 suites passed
                               FAIL: services/api exists but vitest produced no report          exit 1

**`ops/test` is red and I did not make it green.** `services/api/node_modules` does not exist in this
worktree or in the main checkout, so `npx vitest` produces no report; nothing under `services/` is touched by
this branch. This is **T-0040** ("ops/test fails with a misleading message when se..."), already filed. I am
not claiming a green `ops/test`.

### Reviewer's CLEANUP OWED

Cleared the local half, which was garbage pointing into a temp directory: `git worktree remove --force
C:/tmp/tmp.QfGKU5bgVv/wt/T-9901`, `git worktree prune`, `git branch -D task/T-9901`, and the temp tree
itself. Left alone: the origin branches `task/T-9901` and `demo/T-9901-mrg`. Deleting refs on the shared
remote was not asked of me and is not reversible from here; they are named in the review for whoever wants
them gone.
