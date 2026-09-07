---
id: T-0059
title: ops/lib/queue.py is 498 lines against a 300-line cap that cannot see it
state: backlog
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
