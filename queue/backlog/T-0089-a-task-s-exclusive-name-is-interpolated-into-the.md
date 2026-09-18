---
id: T-0089
title: a task's exclusive: name is interpolated into the lock path, so ../ writes the lock outside the repo
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

Found while attacking T-0087's own fix with the neighbouring evasion. T-0087 stopped `--state` being
interpolated into the path `cmd_new` writes. One option over, `exclusive:` is interpolated into the path
`cmd_claim` writes, with no check at all:

    ops/lib/queue.py:  for res in fm.get("exclusive") or []:
    ops/lib/queue.py:      (LOCKS / f"{res}.lock").write_text(...)

`LOCKS` is `queue/LOCKS`, so a resource named `../../../pwned` resolves to `<repo>/../pwned.lock` - above
the repository root, outside every worktree, where nothing in `ops/` will ever look at it again. The same
interpolation appears in `cmd_lock` (acquire), `cmd_review` (release) and `cmd_check` (orphan scan), so a
fix belongs at the path construction, not at one call site.

Red, executed on task/T-0087 at 0be7589 against a throwaway queue tree (`.artifacts/attack4.sh`), because
running it against the fleet's real queue/ is the defect:

    11:exclusive: [../../../pwned]

    $ queue.py claim T-0500 --owner agent/x
    claimed T-0500 -> queue/claimed/T-0500-fixture.md  (now: git add queue/ && git commit && git push ...)
    EXIT=0

    --- lock files anywhere under .artifacts ---
    .artifacts/pwned.lock
    --- and its resolved path ---
    /c/Users/phineasf/Documents/GitHub/wt/T-0087/.artifacts/pwned.lock

`.artifacts/fix/queue/LOCKS/../../../pwned.lock` == `.artifacts/pwned.lock`: three levels above the fake
queue/LOCKS, which in the real tree is three levels above `<repo>/queue/LOCKS`.

Why this matters beyond tidiness: the lock IS the serialisation protocol for the files CLAUDE.md calls
serial-only. A lock that lands outside `queue/LOCKS` is a lock that `cmd_check`'s orphan scan cannot see,
`cmd_review` cannot release and the next claimer cannot detect - so two agents both believe they hold
`scenic-index` and both edit `services/routing/config.yml`. It is not reached through an option (`--exclusive`
could be validated in `cmd_new`) but through a hand-edited `exclusive:` line, which is the documented
workflow: CLAUDE.md tells every agent to declare `exclusive:` in the task file before touching those paths.

Wanted: one `lock_path(res)` that returns `LOCKS / f"{res}.lock"` only for a bare name and None otherwise,
used by all four sites, with the callers reporting the bad name instead of writing. Anchor the check on the
name (an identifier), not on a comment. `cmd_check` should FAIL on a task whose `exclusive:` list holds a
name that cannot be a lock file, so an already-committed one is reported rather than silently unlockable.

Not fixed under T-0087: that task is "a usage line instead of a traceback" and this is a traversal in the
lock subsystem; also `ops/lib/queue.py`'s lock paths are being rewritten by T-0032, which is in review.
Sequence this after T-0032 merges.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from T-0087's self-attack round. The red run above is verbatim
  and was executed by the same agent that wrote T-0087's fix, so it wants an independent re-run.
