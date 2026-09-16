---
id: T-0131
title: Every claimed lease is expired (67/67) and the sweeper cannot see that the work is already pushed
state: claimed
owner: agent/claude-opus-5
owner_session: 012vL7Yk1ov7eNxoFD9U6Pfm
claimed_at: 2026-09-16T04:30:00Z
lease_expires_at: 2026-09-16T10:30:00Z
worktree: .worktrees/T-0131
branch: task/T-0131
exclusive: []
touches: [ops/lib/, ops/queue-sweep, queue/README.md, pins/PINS.yaml]
pins_affected: [P-PROC-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "python ops/lib/check-sweep.py -> SWEEP-CHECK OK (6 cases), exit 0"
  - "python ops/lib/check-sweep.py --variants -> SWEEP VARIANTS OK (3): git-usable guard->5, declared-branch fallback->2, no branch check->1,2,6, exit 0"
  - "RED: git show 01a3128:ops/lib/queue.py > .artifacts/prefix-queue.py (hash 7d0bcbad9e16d2fd0e419c4fb1bfb7d04559f820 == git rev-parse 01a3128:ops/lib/queue.py); python ops/lib/check-sweep.py --queue .artifacts/prefix-queue.py -> FAIL 2/declared-not-fetched must KEEP, ended in ready/, SWEEP-CHECK FAIL (6 cases), exit 1"
  - "bash ops/check-pins -> PINS ok=15 skipped=0 pending=3 expired=0 failed=0 tier=linux, exit 0"
  - "bash ops/queue-check -> QUEUE OK, exit 0"
---
## Brief

`ops/queue-sweep` exists to release leases whose owner has gone away. Right now, on `main`:

* **67 of 67** tasks in `queue/claimed/` have an expired `lease_expires_at`.
* **39 of those 67** have a branch with an **open PR** - work that is finished and pushed, several of them
  with green CI.

So the sweeper, run today, would release 39 tasks whose work exists, is on a branch, and is waiting for a
review. It cannot tell them apart from a task an agent picked up and abandoned, because the only thing it
looks at is a timestamp.

The measurement, reproducible:

```
$ ls queue/claimed | wc -l                    # 67
$ # every one has lease_expires_at in the past
$ # cross-referenced against `gh pr list --state open`:
claimed tasks whose branch has an OPEN PR: 39
  task/T-0024, T-0027, T-0028, T-0033, T-0034, T-0040, T-0043, T-0045, T-0046, T-0048, T-0049, T-0050,
  T-0051, T-0052, T-0055, T-0058, T-0060, T-0062, T-0065, T-0071, T-0075, T-0080, T-0081, T-0088, T-0094,
  T-0097, T-0101, T-0107, T-0108, T-0114, T-0116, T-0117, T-0118, T-0119, T-0120, T-0122, T-0124, T-0126,
  T-0129
```

### The two halves of the problem, which need different answers

**1. The lease is too short for the work.** Leases are 2-4 hours; a task in this repository routinely takes
longer, because it must be demonstrated red, then green, then have a mutation harness written. 67/67 expiry is
not 67 abandoned tasks, it is a lease duration that does not match the job. Whatever the fix, note that simply
lengthening it trades one wrong number for another - a heartbeat (the owner re-stamping while it is actually
working) would express the real thing, which is "is anyone still on this".

**2. A finished-but-unreviewed task has no home.** This is the load-bearing half. The owner does the work,
pushes, opens a PR, and their session ends. The task is now permanently in `claimed/` with `reviewer: null`,
and:

* the sweeper's answer is to send it back to `ready/`, discarding the fact that the work is done;
* `ops/merge` will not take it, because it never reached `review/`;
* nobody else can move it forward, because `claimed -> review` is the owner's transition and the owner is gone.

**T-0080 is the worked example, and it is blocking a chain.** PR #59 is green and MERGEABLE. The task sits in
`queue/claimed/` with `reviewer: null` and `owner: agent/pins-mutation`, a session that has ended. PR #63
(`task/T-0100`) is based on `task/T-0080` and cannot move until it lands - see the correction appended to
[[T-0113]], which establishes that the 18 stacked PRs are a real dependency chain and cannot be unblocked by
retargeting.

### Do

1. Make the sweeper **PR-aware**, or more precisely, evidence-aware: an expired lease on a task whose branch
   exists and has commits ahead of `main` is not an abandoned task. Releasing it to `ready/` throws away work.
   Decide what it should do instead and say so in `queue/README.md`.
2. Give `claimed -> review` a path that does not require the original owner. This is the actual unblock. It
   probably belongs next to [[T-0032]] (*"give claimed → review a home, so the lock is released"*), and it must
   not weaken the gate that matters: `reviewer != owner` stays mechanical.
3. Be careful about **who counts as the owner**. `T-0080`'s frontmatter records `owner: agent/pins-mutation`
   and `owner_session: d217767a`. The mechanical check compares `reviewer` to `owner`, so a differently-named
   agent from **the same session** would pass it while defeating its purpose. If `owner_session` is going to
   be trusted for anything, that should be deliberate and asserted, not incidental.
4. Demonstrate red then green, and demonstrate the specific thing: a task with an expired lease AND a pushed
   branch must not be swept to `ready/`.

### Do not

Do not fix this by running `ops/queue-sweep` and calling the queue tidy. With 39 tasks in this state that is a
mass release of finished work, and the queue would read as "39 things to do again".

## Log
- 2026-09-08T20:55:00Z filed by agent/claude-opus-5 after finding all 67 claimed leases expired while looking
  for a way to unblock T-0080. Both counts above are real command output taken at filing time.
- 2026-09-16T04:30:00Z claimed by agent/claude-opus-5; worktree `.worktrees/T-0131`, branch `task/T-0131`,
  off `01a3128`. `touches:` widened from `[ops/lib/queue.py, ops/queue-sweep, queue/README.md]` to
  `[ops/lib/, ops/queue-sweep, queue/README.md, pins/PINS.yaml]`: the check this task needed is a new file
  (`ops/lib/check-sweep.py`) and a check nothing runs is not a check, so it needs a pin.
- 2026-09-16T05:20:00Z **Items 1 and 2 of the Brief had already landed. Item 4 had not, and that was the
  hole.** Read before writing: `cmd_sweep` already refuses outright when git cannot read the repo, and
  already keeps an expired lease whose branch exists (`ops/lib/queue.py`, `_git_usable` / `_branch_exists`).
  `cmd_review` already makes `claimed -> review` from any session - it is not the owner's private door - so
  a finished task whose owner is gone is not stuck. Neither of those is what this task's item 4 asked for:
  **nothing asserted any of it.** Deleting the guard that protects 39 pushed branches left `ops/queue-check`,
  `ops/check-pins --source-only` and the whole `linux-core` job green, because no check ran the sweeper at
  all - and it cannot be run against the real queue, because it is the one command here that mutates.

  **The defect the new check found on its first run, which is exactly this task's title.**
  `_branch_exists` does no fetch - deliberately; a sweeper that reaches the network is a sweeper nobody runs
  - so a branch another agent pushed since this checkout last fetched reads as **absent**, and the old code
  swept it. The docstring called that direction safe. It is the unsafe one: absent means swept, and swept
  means `owner: null` (the state T-0068 exists to reject), `main` saying `ready/<id>` while the branch says
  `review/`, and the add/add divergence eleven branches were repaired for by hand.

  **RED, from the committed bytes rather than from a scratch edit:**

      $ git show HEAD:ops/lib/queue.py > .artifacts/prefix-queue.py
      $ git hash-object .artifacts/prefix-queue.py   -> 7d0bcbad9e16d2fd0e419c4fb1bfb7d04559f820
      $ git rev-parse HEAD:ops/lib/queue.py          -> 7d0bcbad9e16d2fd0e419c4fb1bfb7d04559f820
      $ python ops/lib/check-sweep.py --queue .artifacts/prefix-queue.py
        FAIL    2/declared-not-fetched   must KEEP  ended in ready/, expected claimed/
                    swept T-9002 -> ready/
                    SWEEP done (1 moved, 0 kept)
        SWEEP-CHECK FAIL (6 cases)                                                               exit 1

  **FIX.** `_declares_branch` is split out from `_branch_exists` because the two answer different questions
  and only one can be answered offline. A DECLARED branch is now kept even when no ref for it is here, with
  the reason printed (`declares branch task/X; no ref here - fetch to see it`). What is left to sweep is a
  task that never named a branch at all - the abandonment this command is for. GREEN:
  `SWEEP-CHECK OK (6 cases)`, exit 0.

  **The check asserts what the sweeper SAID, not only where the file ended up.** Four of the six cases are
  must-KEEP, and a sweeper that crashed before its loop - or one whose loop never ran - would pass all four
  by moving nothing. Case 5 (not a git repository) is the control: without it, a sweeper that refused
  everything would also pass 1, 2, 4 and 6.

  **Each variant breaks exactly the cases named against it**, generated from the real `queue.py` at run time:

      $ python ops/lib/check-sweep.py --variants
      ok      variant without the git-usable guard   breaks exactly 5
      ok      variant declared-branch falls through  breaks exactly 2
      ok      variant without any branch check       breaks exactly 1,2,6
      SWEEP VARIANTS OK (3)                                                                      exit 0

  Two things this file got wrong first, both recorded because both are the shape this repository keeps
  finding. (a) The first draft's variant markers described code that was never written; the marker check
  RAISED rather than skipping, which is why it was caught - a variant sweep that quietly drops a stale
  variant reports OK while proving nothing. (b) The third variant's first replacement was a bare
  `if False:` with no body, an IndentationError, which broke all six cases: a variant that dies on import
  proves only that a broken file is broken, not that any case is watching the guard. The replacement now
  carries `continue`.

  **VERIFICATION.** `bash ops/check-pins` -> `PINS ok=15 skipped=0 pending=3 expired=0 failed=0 tier=linux`,
  exit 0 (14 before this pin). `bash ops/queue-check` -> `QUEUE OK`, exit 0.

  **STILL OPEN - item 3 of the Brief, deliberately not attempted here.** `owner_session:` is recorded and
  compared by nothing, so a differently-named agent from the SAME session passes `reviewer != owner` while
  defeating its purpose - which is how every review in this fleet currently runs, including the ones that
  passed four PRs. Closing it means making `--session` mandatory on `ops/review` and refusing
  `reviewer_session == owner_session`, which changes the signature of a command every agent calls and needs
  its own red/green and its own round of the queue fixture. It is a task, not a rider on this one. What
  changed here is that `queue/README.md` now says the hole exists instead of leaving it implied.
