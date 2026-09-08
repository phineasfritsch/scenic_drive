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
touches: [ops/lib/check-lock-lifecycle, ops/lib/check-brief-required, ops/lib/check-failure-naming, ops/lib/tmpdir.sh]
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

