---
id: T-0101
title: task ids are allocated by a read, not a compare-and-swap, and T-0099 was issued twice
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T08:23:05Z
lease_expires_at: 2026-09-08T11:23:05Z
worktree: null
branch: task/T-0101
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**`T-0099` was allocated twice on 2026-09-08, minutes apart, on two different branches, and nothing caught
it.** `main` got *"every merge-readiness tool enumerates open PRs, so eleven branches of work are
invisible"*; `task/T-0080` got *"P-SRC-01 greps Sources/ only, so a banned import in Tests/ is invisible"*.
Two unrelated findings, one id. Reconciled by hand and the second renumbered to `T-0100`.

**It happened TWICE in one day, and the second one was worse.** `T-0088` was also allocated twice: `main`
has *"the 69 mutation survivors are five gaps"* (from `task/T-0081`) and `task/T-0087` has *"ops/check-pins
tier with no value prints an index"*. Renumbered to `T-0102`.

That second instance is the one that should decide the priority, because **no gate could see it**.
`ops/queue-check` passes on `main`. It passes on `task/T-0087`. The duplicate exists only in the MERGE of
the two — the merge-time-only class [[T-0063]] was filed for and [[T-0065]]'s rehearsal exists to catch —
and the rehearsal could not see it either, because `task/T-0087` has no open PR and the rehearsal
enumerated pull requests ([[T-0099]]). It surfaced only because an unrelated task happened to branch from
`task/T-0087` and merge `main` into it. That is luck, not a mechanism.

**This is not a hole in [[T-0017]]'s fix; it is the limit of its shape.** `next_id()` consults
`_ids_in_refs()`, which scans every remote ref precisely to stop this, and the comment there is right about
what it buys. But the sequence is:

    read the refs  ->  pick max+1  ->  write the file  ->  ...work...  ->  commit  ->  push

Two allocators that both READ before either PUSHED get the same number, and the window is not milliseconds —
it is however long the first agent takes to reach its first push. Here it was several minutes, because
`ops/new-task` is typically run at the *start* of a piece of work.

**The queue already solves this exact problem one step over, and the contrast is the whole brief.** Claiming
is safe because it is a compare-and-swap: `git mv` + push, and *a rejected push means someone else claimed
it* — `queue/README.md` step 3 says so in as many words. Allocation has the read and no second step. So the
repository's own safety mechanism exists, is documented, and is not applied to the one operation that
invents a unique name.

**What it costs when it is not caught.** `ops/queue-check` fails on `duplicate id` — but only once both
files are in one tree, i.e. after the merge, on a branch neither author is looking at. That is the same
merge-time-only class as the stale `claimed/` copy [[T-0063]] was filed for, and the reason
[[T-0065]]'s rehearsal exists. Here it was caught by a human reading two agents' reports side by side,
which is not a mechanism.

Do:

1. Make allocation a compare-and-swap. The cheapest form that fits this repo: `ops/new-task` writes the
   file, commits **just that file**, and pushes immediately — a rejected push means the id was taken, so it
   re-reads and retries with the next free id. The task file at that point is `ops/new-task`'s placeholder,
   which `brief_is_unwritten()` already recognises ([[T-0056]], [[T-0070]]), so an unwritten brief on `main`
   for a few minutes is a state the rest of the system already understands.
2. If pushing at allocation is judged too eager, the alternative is to stop pretending ids are dense:
   allocate `T-` plus a short hash of (title, owner, timestamp) and let `queue-check` enforce uniqueness.
   That trades readable ordering for correctness by construction. **Pick one and say why in the log** —
   the failure mode of choosing neither is the one already measured.
3. Either way, `ops/new-task` must print the id it actually got, and must refuse silently reusing one.

**Red demo:** two allocations from two worktrees with no push between them currently produce the same id.
That is a two-line reproduction and it should be in the log before the fix.

**Do not** make this depend on the network at read time only — a scan that is more thorough is still a
read, and this task exists because a read is not enough.

## Log
- 2026-09-08T08:23:05Z claimed by agent/claude-opus-5; lease until 2026-09-08T11:23:05Z

- 2026-09-08 — **the id is now reserved by pushing a ref whose NAME is the id, which is the missing second
  step.**

  `git push origin HEAD:refs/tags/id/T-0103` is rejected when the ref already exists — no `--force`, no
  lease — so the push either wins the id or says who has it. It commits nothing, touches no branch, and
  reserves globally rather than per-branch, so it works from any worktree.

  **The sentence this task was filed against is corrected in place**, because it was the load-bearing part
  of the mistake. `_ids_in_refs()` said *"the push is the compare-and-swap that settles that, exactly as for
  claims."* For a CLAIM that is true — the moved file goes to `main` and a rejected push means somebody else
  moved it first. For an ALLOCATION nothing is pushed at allocation time and the task file's eventual push
  goes to a task BRANCH, where it can never conflict with another branch's push. There was no second step,
  only a longer read, and the comment asserting otherwise is why nobody looked.

  **RED** (`.artifacts/demo-reserve.py`, two module instances, nothing pushed between them):

        allocator A -> T-0103
        allocator B -> T-0103     (nothing was pushed in between)
        SAME ID: True

  **GREEN:**

        reservations on origin before: ['T-0103', 'T-0104']
        allocator C -> T-0105
        allocator D -> T-0106     (again nothing was committed or pushed by the caller)
        SAME ID: False
        reservations on origin after: ['T-0103', 'T-0104', 'T-0105', 'T-0106']

        $ ops/queue-check   QUEUE OK (95 tasks)   exit 0
        $ ops/check-pins --source-only   ok=3 failed=0   exit 0

  **Two defects of my own, both found by the demo rather than by reading:**

  1. The first RED printed `T-0001`. The before-copy had been written to `.artifacts/`, so its
     `ROOT = Path(__file__).parents[2]` resolved outside the repository — it saw no tasks and no git, and
     the "red" was an artifact of the harness. Moved to `ops/lib/queue_before.py` and re-run. A red that
     comes from the harness proves nothing, and this one would have read as proof.
  2. `--reserve no` skipped *reading* the reservations as well as writing them, and handed out `T-0103`
     while `T-0103` was already reserved. The escape hatch exists because a box may not be able to PUSH;
     that does not make reading free-er to skip. It now always reads and only the push is conditional.

  **Failure modes, deliberately:** if the reservations cannot be READ, it warns loudly and continues, because
  that is exactly the old behaviour and refusing would make an offline box unable to file a task at all. If
  the reservation cannot be WRITTEN, it **refuses** — allocating unreserved is what issued two ids twice, so
  it is not something to do by accident. `--reserve no` is the deliberate version and prints what it costs.

  **Left as it is, on purpose:** `T-0103`–`T-0106` are now reserved with no task behind them, burned by this
  demo. Deleting a reservation is the one operation that reintroduces the collision, so it should be a
  deliberate act and not a cleanup step in a demo script. A future `queue-check` rule could report
  reservations with no task file; that is not this task.
