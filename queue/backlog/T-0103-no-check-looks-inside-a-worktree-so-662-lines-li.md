---
id: T-0103
title: no check looks inside a worktree, so 662 lines lived untracked with no branch on origin
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/sane, ops/agent-preflight]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**662 lines of the corpus emitter existed only as untracked files in one worktree on one machine, and
`origin/task/T-0030` did not exist at all.** A `git clean`, a `git worktree remove --force`, or a reinstall
would have deleted them, and nothing in this repository would have reported anything missing.

Found on 2026-09-08 by a one-off sweep, not by a check:

    wt/T-0030   ?? services/etl/etl/schema.py         246 lines
                ?? services/etl/etl/geom.py           147
                ?? services/etl/etl/segmenter.py      119
                ?? services/etl/etl/contentdigest.py   91
                ?? services/etl/etl/segid.py           59
                origin/task/T-0030: does not exist

All five parse. They carry the kind of docstring this repo asks for (`segid.py`: *"Byte level, not string
level... big-endian fixed-width bytes make it depend on nothing about the build host"*). This was real work,
mid-flight, and the only copy was in a directory.

**Why nothing saw it.** `ops/sane` exit 2 checks "repo dirty" — of the checkout it is run in. Every other
gate reads the tree it is run in, or reads remote refs. A worktree the agent is not currently standing in is
outside all of them, and there are 30+ of them. The same sweep found four other worktrees with unpushed
commits and one (`wt/T-0085`) checked out on a leftover `demo/*` branch, so an agent returning to it would
have committed to the demo branch rather than to its task.

**The fleet rule this violates is already written down.** `queue/README.md` step 8 says a demo worktree is
created and then removed; CLAUDE.md says work happens in a worktree per task. Neither is checked, and the
queue's whole safety argument — *"claim = `git mv` + push, git is the lock"* — assumes work reaches the
remote. Work that never leaves a directory is invisible to the lease sweeper, to `queue-check`, to the
rehearsal, and to a human reading GitHub. [[T-0082]]'s sweeper would even read such a task as **abandoned**
now that it is keyed on commits ahead of main: `task/T-0030` has none, because they were never committed.

Do:

1. `ops/sane` gains a check over **every** worktree `git worktree list` reports, not just this one:
   untracked files under a path in that task's `touches:`, uncommitted modifications, commits not on
   `origin`, and a HEAD that is not the branch the task file names. Report the worktree, the branch, and the
   counts.
2. `ops/agent-preflight` runs it at session start, because that is the moment somebody can still act on it —
   CLAUDE.md already says to run preflight first thing.
3. Distinguish the three states in the OUTPUT, because they need different actions: *untracked* (may be
   scratch, may be 662 lines of emitter), *uncommitted changes to tracked files*, *committed but unpushed*.
   Do not collapse them into "dirty".
4. Ignore what is genuinely scratch — `.artifacts/` is gitignored and is where this repo is told to put
   scratch — but **never** ignore a path inside the task's `touches:`. That is the discriminator: an
   untracked file under a path the task declared it would edit is the task's own work.
5. Vacuity guard: fail if it inspected zero worktrees. `git worktree list` always reports at least the main
   checkout, so zero means the query failed, and "no problems found" would be a lie.

**Red demo:** create a worktree, drop an untracked file under its task's `touches:`, run the check, see it
named. Then commit and push it and see the check go quiet.

**Do not** make this a `git clean` helper or offer to delete anything. The failure mode here is deletion;
the fix is visibility.

## Log
