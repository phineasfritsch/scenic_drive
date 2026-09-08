---
id: T-0124
title: three ops checks are broken on the Windows dev box because mktemp gives a path Windows python cannot open
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
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
