---
id: T-0039
title: pre-commit touches enforcement is dead for tasks in queue/done/ - a signed-off task can commit anywhere
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.githooks/pre-commit, ops/lib/queue.py]
pins_affected: []
reviewer: null
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
