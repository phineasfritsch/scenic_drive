---
id: T-0131
title: Every claimed lease is expired (67/67) and the sweeper cannot see that the work is already pushed
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/queue.py, ops/queue-sweep, queue/README.md]
pins_affected: [P-PROC-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
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
