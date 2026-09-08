---
id: T-0082
title: 32 of 48 leases have expired and queue-sweep would clobber every one of them
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T03:28:24Z
lease_expires_at: 2026-09-08T09:28:24Z
worktree: wt/T-0082
branch: task/T-0082
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**32 of the 48 tasks in `queue/claimed/` have an expired lease. None of them is abandoned.** Every one is
finished work sitting on a branch, waiting for a merge that has not been possible since 2026-09-07.

`cmd_sweep` is designed for the opposite situation - an agent that died mid-task - and does the right thing
for it: move the task back to `ready/`, clear the lease, release the locks. Run today it would do that to all
32, and each one is a compounding mistake:

1. **It sets `owner: None`.** That is precisely the state [[T-0068]] was filed to reject, and `cmd_sweep` is
   named in that brief as the tooling that produces it. A task later moved to `review/` by hand then reaches
   `done/` with no owner and, until T-0073's fix merges, no complaint.
2. **It multiplies the task-file divergence.** `main` would say `ready/<id>`; the branch says `review/` or
   `done/`. That is the add/add across two paths this session has repaired on eleven branches by hand, and it
   would be recreated on 32.
3. **It discards a signoff.** Several of these have been reviewed. Sweeping loses the reviewer along with the
   owner, and the task looks unclaimed to the next agent that runs `ops/queue-next`.

**The model is wrong, not the implementation.** A lease answers "is an agent still working on this?" The
queue is using `claimed/` to answer a different question - "has this merged yet?" - and those have completely
different timescales. An agent works for hours; a branch waits for days.

- Distinguish the two. A task whose branch is pushed and whose PR is open is not a lease candidate, whatever
  its timestamp says. `ops/claim` already records `branch:`, and `gh pr list` can say whether it is open.
- Or split the state: `claimed/` for work in progress, and something like `merging/` for work that is finished
  and waiting. The directory is the state, so this is a `git mv` and a name.
- **Whatever is chosen, `cmd_sweep` must refuse to clear an owner on a task whose branch exists on the
  remote.** That single rule makes the current 32 safe without deciding the larger question.
- [[T-0032]] releases exclusive locks on the claim -> review transition, which fixes the LOCK half. It is
  written and unmerged. This task is the OWNER half, and the two together are the whole problem.

**Demonstrate red before fixing:** run `ops/queue-sweep` against a copy of the current tree (never the real
one) and count how many task files it rewrites and how many owners it clears. That number is the finding.
[[T-0064]] is already blocked behind this: it cannot claim `scenic-index` because T-0024 holds the lock for a
task whose work is complete.

## Log
- 2026-09-08 filed by agent/claude-opus-5 after declining to sweep. The 32 figure was measured by parsing
  `lease_expires_at` from every file in `queue/claimed/`.
- 2026-09-08T03:28:24Z claimed by agent/claude-opus-5; lease until 2026-09-08T09:28:24Z

- 2026-09-08 agent/claude-opus-5 — the containment, with the sweeper still working.

  **RED, measured against a COPY of the live tree** (never the real one — `.artifacts/sweep-probe.sh` builds a
  throwaway holding only `ops/lib/` and `queue/`, which is self-contained because `ROOT` comes from `__file__`):

        BEFORE  claimed=46  ready=1  with an owner=46  locks=2
        SWEEP done (29 moved)
        AFTER   claimed=17  ready=30  with an owner=17  locks=1
                task files moved claimed/ -> ready/:  29
                files in ready/ now carrying owner: null: 30
                exclusive locks released: 1

        swept tasks whose branch EXISTS (work in flight):   29
        swept tasks with no branch at all (abandoned):       0

  (An earlier version of this table wrote `1` on the second row, summing to 30 against 29 moved. Reported
  as [medium] by the reviewer of PR #51 and confirmed: the rows had been counted over the whole post-sweep
  `ready/` directory rather than over the swept set, so the extra file was **T-0041**, which was already in
  `ready/` before the sweep, was never claimed and was never swept. The reviewer reproduced the same
  off-by-one at a different scale — 32 moved, 32 with branches, plus the same single pre-existing T-0041.
  The conclusion is unchanged and is now arithmetically consistent: no swept task lacked a branch.)

  **Twenty-nine of twenty-nine.** Not one expired lease belonged to an abandoned task; every one was pushed
  work waiting on a merge. The sweeper would have set `owner: None` on all of them — the state [[T-0068]]
  exists to reject, produced by this very function, which that brief already names — and left `main` saying
  `ready/<id>` while each branch says `review/` or `done/`, recreating on 29 branches the add/add divergence
  eleven branches had already been repaired by hand for.

  **GREEN, identical probe:**

        SWEEP kept 29 expired lease(s) whose branch still exists ...
        SWEEP done (0 moved, 29 kept)
        AFTER   claimed=46  ready=1  with an owner=46  locks=2

  **CONTROL — and this is the one that matters, because a guard that disables the tool is not a fix.** A
  genuinely abandoned task (`T-9990`, expired lease, `branch: task/T-9990-does-not-exist`) added to the
  sandbox:

        SWEEP done (1 moved, 29 kept)
        T-9990 is now in ready/, gone from claimed/, owner: null

  The dead agent is still swept. Only live work is kept.

  **FAIL-CLOSED.** Every guard here is a git query, and a git that cannot read the worktree answers "no such
  branch" to all of them — indistinguishable from "abandoned", and the wrong default by exactly the margin of
  the damage above. That is not hypothetical: from WSL against this Windows checkout, `.git` says
  `gitdir: C:/...` and WSL's git cannot follow it (T-0055). So `_git_usable()` is asked once, before anything
  moves. Demonstrated with a PATH containing python but not git:

        SWEEP REFUSED: git cannot read this repo, so 'has this task got a branch?' cannot be answered.
          Every expired lease would look abandoned and be swept. Run this where git works.
        exit 2
        claimed: 46  ready: 1   (unchanged)

  `_branch_exists` also returns True on an exception rather than False: cannot tell means do not sweep.

  **What this does NOT fix**, and the brief is right that it is the larger question: the queue is still using
  `claimed/` to answer two questions with different timescales — "is an agent working on this" (hours) and
  "has this merged" (days). This makes the current 29 safe without deciding that. [[T-0032]] fixes the LOCK
  half on the claim -> review transition and is written and unmerged.

  No fetch is done. A sweeper that reaches the network is a sweeper nobody runs, and a stale remote-tracking
  ref can only make this MORE conservative.

  `ops/lib/queue.py` is now **711 lines** — 653 before this. That is the third time in one session this file
  has grown while [[T-0059]] waits, and T-0059 is blocked because six unmerged branches hold it.

- 2026-09-08 — **the reviewer of PR #51 was right twice, and the second one had disabled the tool.**

  **(high) The guard asked the wrong question, so nothing real was ever swept again.** `cmd_claim` writes
  `branch: task/<id>` for every task without exception, and `queue/README.md` step 4 creates exactly that
  branch — `git worktree add ../wt/T-XXXX -b task/T-XXXX` — *before* any work happens. So `_branch_exists`
  is true for every task the documented workflow has ever claimed, including the one shape this sweeper
  exists for: claim, open the worktree, die. That task keeps its owner and its `exclusive:` lock forever.
  My CONTROL missed it because I wrote `branch: task/T-9990-does-not-exist`, a name `ops/claim` cannot
  produce; it proved only that the sweeper still sweeps tasks that could not exist.

  The property that actually separates the two populations is **ahead-of-main**, not existence. A
  claim-time branch sits at main's tip, zero commits ahead. The 29 expired leases of 2026-09-08 were
  pushed branches with open PRs — all ahead. `_branch_has_work(name, base)` replaces `_branch_exists`.

  **(high) The docstring's reason for not fetching was backwards.** It claimed a stale ref could only make
  the sweeper more conservative. The opposite: a branch pushed since the last fetch reads as *absent*, so
  the sweeper clears its owner and releases its exclusive lock — and nothing refuses, because git itself is
  fine and `_git_usable()` returns True. `_sweep_fetch()` now fetches and **refuses on failure**;
  `--no-fetch` is the explicit, documented escape for a single-pusher checkout.

  **Corrected control (`.artifacts/demo-t0082-review.sh`)** — two fixtures with names `ops/claim` really
  writes, in a throwaway worktree: `T-9989` = claimed, `task/T-9989` created from `origin/main`, no commits
  (agent died); `T-9988` = `task/T-9988` one commit ahead (work waiting to merge).

        ===== RED: guard as shipped in PR #51 =====
          SWEEP kept 37 expired lease(s) whose branch still exists - finished work waiting to
          SWEEP done (0 moved, 37 kept)
          T-9989 still in claimed/: YES
          T-9989 lock still held:   YES

        ===== GREEN: with the fix =====
          SWEEP kept 36 expired lease(s) whose branch carries commits - finished work waiting to
          SWEEP done (1 moved, 36 kept)
          T-9989 swept to ready/:   YES
          T-9989 lock released:     YES
          T-9988 kept in claimed/:  YES

  RED is the reviewer's finding, not a hypothetical: the abandonment this task was filed to sweep was the
  one case the fix refused to sweep. GREEN sweeps it, releases the lock, and still holds every one of the
  36 branches that carry commits — the regression T-0068 exists to reject is still rejected.

  `ops/queue-check` → `QUEUE OK (76 tasks)`.
