---
id: T-0059
title: ops/lib/queue.py is 498 lines against a 300-line cap that cannot see it
state: blocked
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/]
pins_affected: []
reviewer: null
depends_on: [T-0058]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/lib/queue.py` is **498 lines**. CLAUDE.md's cap is 300. It has been over for a long time - 415 lines
before T-0032 added the `review` transition - and nothing has ever said so, because `ops/lib/check-line-cap`
globs `git ls-files '*.swift'` and Python is not checked at all (T-0058).

Recording it here rather than quietly leaving it: T-0032 knowingly took an over-cap file from 415 to 498. The
alternative was to bundle a refactor of the queue's core into a task about lock release, which is worse - but
"the check cannot see it" is not a reason, and the next person to add a command should not have to rediscover
that the file was already double the limit.

It is also the file with the most agents in it. `ops/lib/queue.py` appears in the `touches:` of T-0032,
T-0039 and T-0056 in this session alone, so it is exactly the "merge grenade for parallel agents" that
P-SRC-02's own `why_no_test_catches_it` describes.

The seams are already visible in the file's own section comments:

    front matter parsing / dumping     parse, _scalar, dump, _list, _opts
    task discovery and ids             tasks, _ids_in_refs, next_id, log
    the commands                       cmd_new, cmd_check, cmd_sweep, cmd_next, cmd_claim, cmd_review, cmd_lock

- Split along those seams, not by line count. A `queue/` package under `ops/lib/` with the CLI staying at
  `ops/lib/queue.py` keeps every `ops/*` wrapper working unchanged - check that claim, because those wrappers
  are what the whole fleet calls.
- `ops/lib/check-brief-required` and `ops/lib/check-lock-lifecycle` both copy `queue.py` into a throwaway
  repo and run it. A package rather than a single file breaks that copy; both checks need updating in the
  same commit, and the fact that they exist means the split has real coverage to move against.
- Do this AFTER T-0058, so the cap actually enforces the result. Splitting a file to satisfy a rule that
  nothing checks is how it drifts back.
- Do NOT do it while several branches hold `ops/lib/queue.py` in their `touches:`. Sequence it against the
  merge order.

## Log

- 2026-09-08 agent/claude-opus-5 — moved to blocked/, on this task's own precondition rather than on judgement.

  The brief says: *"Do NOT do it while several branches hold `ops/lib/queue.py` in their `touches:`. Sequence
  it against the merge order."* Six unmerged branches hold it right now:

        T-0032  touches: [ops/lib/queue.py, queue/]
        T-0039  touches: [.githooks/pre-commit, ops/lib/queue.py]
        T-0056  touches: [ops/lib/queue.py, ops/claim]
        T-0068  touches: [ops/lib/queue.py]
        T-0070  touches: [ops/lib/queue.py]
        T-0073  touches: [ops/lib/queue.py]

  Splitting the file into a package now would turn every one of those into a rename/modify conflict resolved by
  hand, six times, against a file whose structure had changed underneath them. That is precisely the
  "merge grenade for parallel agents" P-SRC-02's own `why_no_test_catches_it` describes, and this session has
  spent a good deal of time on the cheaper version of it (a task file at two paths). Doing it anyway would be
  trading a known cost for a larger one to close a check I control the exemption for.

  **The file is worse than the brief records.** It said 498 lines. It is now **653** on `task/T-0070`:
  T-0032 took it 415 -> 498, T-0073's round-two fix took it to 615, and my own T-0070 added 38 more. Every one
  of those was a real fix to a real hole, and each knowingly grew a file already double the cap because the
  alternative was bundling a refactor of the queue's core into a task about something else. That reasoning is
  still right and it does not scale: the next command added to this file should be the one that stops.

  **Second precondition, and it is now satisfiable in a way it was not before.** The brief warns that
  `ops/lib/check-brief-required` and `ops/lib/check-lock-lifecycle` copy `queue.py` into a throwaway repo and
  run it, so a package breaks that copy and both must be updated in the same commit. Neither file is on `main`
  — they arrive with the T-0056 / T-0032 chain. So the split must land *after* those merge anyway, which is
  the same ordering this entry is blocked on. The two constraints agree.

  Unblocks when the six branches above are merged. `ops/merge-rehearse` already derives an ordering rule for
  the deletion case; this is the rename case and the same argument applies.
