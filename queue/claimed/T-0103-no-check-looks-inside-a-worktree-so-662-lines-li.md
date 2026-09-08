---
id: T-0103
title: no check looks inside a worktree, so 662 lines lived untracked with no branch on origin
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T09:21:19Z
lease_expires_at: 2026-09-08T12:21:19Z
worktree: null
branch: task/T-0103
exclusive: []
touches: [ops/sane, ops/agent-preflight, ops/lib/check-worktrees]
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
- 2026-09-08T09:21:19Z claimed by agent/claude-opus-5; lease until 2026-09-08T12:21:19Z

- 2026-09-08 — **`ops/lib/check-worktrees`, wired into `ops/sane` (exit 10) and `ops/agent-preflight`.**

  **It found the motivating shape on its first run**, which is the only evidence that matters here:

        T-0103   unpushed:[no origin/task/T-0103 at all]
        _dupprobe   unpushed:[no origin/tmp/dupprobe at all]

  That is exactly `wt/T-0030`'s state — a branch whose work exists on one disk only — reported by a check
  rather than by a hand sweep.

  **The design decision, and it was forced by measurement rather than taste.** At 67 worktrees, under four
  concurrent agents:

        three git calls per worktree   real 11m55s   user 0m22s   sys 2m14s
        one   git call  per worktree   real  6m55s   user 0m14s   sys 1m19s
        ZERO  git calls per worktree   real  1m57s   user 0m01s   sys 0m11s   <- the default

  Almost none of it was ever computation. **A check that takes minutes is a check nobody runs, and a check
  nobody runs is precisely the hole this task was filed to close** — so the first two versions were not
  slow implementations of the right check, they were the wrong check. The default had to leave the
  per-worktree business entirely.

  It could, because the catastrophic case needs no per-worktree call: `origin/task/T-0030` simply did not
  exist, and that fact is already in `git worktree list --porcelain` (which prints each HEAD sha) plus one
  `for-each-ref`. `--deep` buys untracked-in-`touches:` and modified files at one `git status` each, and
  says so in its own output rather than letting a fast run be mistaken for a thorough one.

  Three states are reported separately and never collapsed into "dirty", because they need different
  actions: *untracked inside touches:*, *modified*, *committed but not on origin*. Untracked files are
  judged only against the task's declared `touches:` — `.artifacts/` is gitignored and is where this repo
  tells agents to put scratch, so a file under a path the task said it would edit is the task's own work.

  **Vacuity floor:** `git worktree list` always reports at least this checkout, so parsing zero means the
  parser is wrong, and it exits 2 rather than reporting no problems.

- 2026-09-08 — **`ops/agent-preflight` was reporting the repository as misconfigured in every session, and
  it was wrong.**

        $ git config --get core.hooksPath
        C:\Users\phineasf\Documents\GitHub\scenic_drive\.githooks
        $ bash ops/agent-preflight | grep hooks
        hooksPath    NOT SET - run: git config core.hooksPath .githooks

  It *was* set. The check compared the value to the literal string `.githooks`, so an ABSOLUTE value failed
  the string test — and preflight, the command `CLAUDE.md` says to run **first thing in every session**, had
  been exiting non-zero on every worktree with a message that is simply false. A check that always fails is
  a check nobody reads, and that is why the hazard underneath it went unseen for so long.

  The hazard, found by the reviewer of PR #47: git resolves a **relative** `core.hooksPath` against the top
  of the working tree, so `.githooks` is per-worktree while an absolute path is not. With the absolute value
  pointing at the main checkout, **every worktree ran main's hooks** — a branch could not exercise its own
  `.githooks` change by committing, and a hook red/green demonstration done in a worktree tested main's copy.
  The reviewer proved it the only way that counts: the commit PR #47's log records as REFUSED is accepted,
  with HEAD advancing.

  The check now resolves both paths and reports the three states apart:

        hooksPath    .githooks (relative - resolves to THIS worktree, which is what you want)

  **And the config itself was corrected mid-session, by another agent, while four were committing.**
  `.git/config` changed at 03:02 local. It is the right change and preflight is what verifies it, but it is
  repo-wide, out of band, and outside every `touches:` — the pre-commit hook cannot police git config, so
  nothing would have reported it. Verified after the fact rather than trusted:

        $ git rev-parse --git-path hooks     # in three different worktrees
        .githooks        .githooks        .githooks       (and the file exists in each)

        $ bash ops/lib/check-exec-bits
        P-OPS-01: 24 files, 15 required present, all modes correct
