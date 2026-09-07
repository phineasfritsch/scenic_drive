---
id: T-0039
title: pre-commit touches enforcement is dead for tasks in queue/done/ - a signed-off task can commit anywhere
state: review
owner: agent/builder-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:38:26Z
lease_expires_at: 2026-09-07T19:38:26Z
worktree: ../wt/T-0039
branch: task/T-0039
exclusive: []
touches: [.githooks/pre-commit, ops/lib/queue.py]
pins_affected: []
reviewer: agent/reviewer-24
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`.githooks/pre-commit` only looks for the task file in `queue/claimed/` and `queue/review/`:

    taskfile="$(ls queue/claimed/"$task"*.md queue/review/"$task"*.md 2>/dev/null | head -1 || true)"

Once a reviewer moves the task to `queue/done/`, `$taskfile` is empty, the `touches:` block is skipped
entirely, and the branch can commit ANY path with the hook still exiting 0. The branch is usually still open at
that point - `ops/merge` requires the task to be in `done/` on the PR head, so every PR spends its whole
merge window in exactly this ungoverned state.

Found while fixing T-0023: commits touching `.gitignore` and `ops/lib/junit_count.py`, neither in that task's
`touches:`, were accepted without complaint.

- Include `queue/done/` in the lookup.
- Decide and document what a `done` task may still commit. Recommendation: `touches:` still applies; nothing
  about review makes a path safe that was not before.
- Demonstrate red: on a branch whose task is in `done/`, stage a path outside `touches:` and show the hook
  accepts it today; apply the fix; show it refuse.

## Log
- 2026-09-07T16:38:26Z claimed by agent/builder-21; lease until 2026-09-07T19:38:26Z
- 2026-09-07T16:43:49Z agent/builder-5: decision + red/green demonstration.

  **Decision: what may a `done` task still commit?** Going with the brief's recommendation - `touches:`
  still applies, unchanged, in `done/` exactly as in `claimed/` and `review/`. Reasoning, from the cases
  that actually arise on this fleet (per CLAUDE.md: don't make the hook refuse what the fleet legitimately
  does many times a day, and don't leave the gate open either):

    - A reviewer moving a task queue/review -> queue/done and committing only the task file: already
      exempt today, unconditionally, via the `[[ "$f" == queue/* ]] && ok=1` line - this never touched
      `touches:` and still doesn't. No change in behavior for this, the single most common `done`-state
      commit on the fleet.
    - An owner fixing a review finding after the task is already in `done/` (e.g. a fixup pushed to the
      same PR branch before `ops/merge` runs): must stay inside the same `touches:` it had in `claimed/`.
      Nothing about a reviewer's sign-off makes a path outside the declared scope newly safe - the premise
      in CLAUDE.md ("agents report success on broken work") applies exactly as much post-review as
      pre-review. If the fix needs a path outside `touches:`, the correct move is to widen `touches:` in
      the task file (which is itself inside `queue/*` and always committable) and say so in the log, same
      as any other task - never to have the hook wave it through because a reviewer already looked once.
    - A merge commit: out of scope for this hook by construction. `ops/merge` merges via `gh pr merge`
      (GitHub-side, API merge) - no local `git commit` happens on the task branch for it, so `pre-commit`
      never runs. A local `git merge` of a task branch onto `main` would run on branch `main`, which does
      not match `^task/(T-[0-9]+)`, so the touches block is skipped for that commit too (as it already is
      for any commit made directly on `main`) - unaffected by this fix either way.

  So the only code change needed: add `queue/done/` to the `ls` lookup. No change to the exemption logic,
  no change to what counts as "allowed" - only to *finding* the task file that was always supposed to
  govern the branch.

  **RED** - `.githooks/pre-commit` before the fix, on scratch branch `task/T-9101-red-demo` (deleted after
  this run), with a scratch task file at `queue/done/T-9101-scratch-red-demo.md`
  (`state: done`, `touches: [ops/scratch-red-demo-touch.txt]`), staging `services/scratch-red-probe.txt`
  (new file, not in that `touches:` list) and running the hook directly:

      $ bash .githooks/pre-commit; echo "EXIT=$?"
      EXIT=0

  No output, exit 0 - the hook accepted a staged path completely outside the task's `touches:` because
  `taskfile` came back empty (lookup only checked `claimed/` and `review/`), exactly the bug reported.

  **Fix applied** - `.githooks/pre-commit`, `taskfile=` line:

      -  taskfile="$(ls queue/claimed/"$task"*.md queue/review/"$task"*.md 2>/dev/null | head -1 || true)"
      +  taskfile="$(ls queue/claimed/"$task"*.md queue/review/"$task"*.md queue/done/"$task"*.md 2>/dev/null | head -1 || true)"

  plus a comment update at the top of the file documenting the `done/` case and the "review doesn't widen
  scope" rule. No other line changed.

  **GREEN 1 (refused)** - identical staged state as the RED run (same scratch branch/task file/probe file,
  only the hook script edited in between):

      $ bash .githooks/pre-commit; echo "EXIT=$?"
      pre-commit: services/scratch-red-probe.txt is outside T-9101 touches: [ops/scratch-red-demo-touch.txt ]
      pre-commit: refusing commit
      EXIT=1

  **GREEN 2 (legitimate cases all still pass)**, each on its own scratch branch/task file, deleted after:

    - `task/T-9102-claimed-demo`, task file in `queue/claimed/` (`state: claimed`,
      `touches: [ops/scratch-claimed-demo-touch.txt]`), staging `ops/scratch-claimed-demo-touch.txt`
      (inside `touches:`): `EXIT=0`, no output.
    - `task/T-9101-red-demo`, task file in `queue/done/` (`state: done`), staging only
      `queue/done/T-9101-scratch-red-demo.md` itself (the "reviewer commits only the task file" case):
      `EXIT=0`, no output.
    - Same branch/task, staging `ops/scratch-red-demo-touch.txt` (a path inside that `done` task's
      `touches:`): `EXIT=0`, no output.
    - `scratch/no-task-branch` (branch names no task at all), staging an arbitrary new file: `EXIT=0`, no
      output - unchanged, the `^task/(T-[0-9]+)` branch match still fails first, exactly as before this fix.
    - `task/T-9999-missing-file-demo` (branch names a task, but no `T-9999*.md` exists anywhere under
      `queue/claimed|review|done/`), staging an arbitrary new file: `EXIT=0`, no output - unchanged,
      `taskfile` is still empty (now checked across three directories instead of two, but still not found),
      so enforcement is still skipped exactly as it was pre-fix for this case.

  All scratch branches (`task/T-9101-red-demo`, `task/T-9102-claimed-demo`, `scratch/no-task-branch`,
  `task/T-9999-missing-file-demo`) and every scratch file created for these runs were deleted; `git status`
  confirmed clean before returning to `task/T-0039`.

  Did not touch `ops/lib/queue.py` - nothing in `queue.py` participates in `pre-commit`'s enforcement (it's
  a separate Python CLI for queue transitions; the hook is pure bash reading the filesystem directly), so no
  change was needed there for this fix. Leaving it out of this commit; `touches:` already allows it if a
  future finding needs it.
