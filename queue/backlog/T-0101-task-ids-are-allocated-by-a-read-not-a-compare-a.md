---
id: T-0101
title: task ids are allocated by a read, not a compare-and-swap, and T-0099 was issued twice
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
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
