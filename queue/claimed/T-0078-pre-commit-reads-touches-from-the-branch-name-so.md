---
id: T-0078
title: pre-commit reads touches from the branch name, so a follow-up task's touches field is decorative
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:59:05Z
lease_expires_at: 2026-09-08T08:59:05Z
worktree: wt/T-0078
branch: task/T-0078
exclusive: []
touches: [.githooks/pre-commit]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`.githooks/pre-commit` builds its `touches:` allowlist from the **branch name**: `task/T-XXXX` ->
`queue/claimed/T-XXXX*.md`. So on a branch carrying a follow-up task - [[T-0072]] worked on `task/T-0066`,
[[T-0073]] on `task/T-0068`, [[T-0074]] on `task/T-0069` - the hook enforces the **parent's** list and ignores
the follow-up's entirely.

**A follow-up task's `touches:` field is therefore decorative.** It is written, committed, reviewed, and never
consulted. Both files had to be widened by hand during T-0072 to get the commit through, which is the symptom:
the field that was consulted was not the field that described the work.

Found by the T-0072 fixer while trying to commit, and stated in its report rather than worked around silently.

This is the same class as [[T-0039]] - `touches:` enforcement being dead for a category of task - and the
third time the queue's identity has been inferred from something other than the task being worked. Deciding
which task a commit belongs to by parsing a branch name works exactly until two tasks share a branch, which is
a thing this repo now does deliberately, because a follow-up belongs on the branch that carries the fix it
follows.

- The commit must say which task it is for, or the hook must consider EVERY claimed task whose `branch:` field
  names this branch. The second is mechanical and needs no new convention: `ops/claim` already writes
  `branch:` into the task file, and T-0072/T-0073/T-0074 set it explicitly to the parent's branch.
- Union the `touches:` of every task claimed onto this branch, or refuse when more than one is claimed and the
  commit does not name one. Either is defensible; pick one and say why in the file.
- Do not simply widen the parent's `touches:` to cover the child. That is what was done under duress here, and
  it makes the parent's declared scope a lie.
- Demonstrate red: on a branch with two claimed tasks, commit a path that is in the follow-up's `touches:` and
  not the parent's, and show the hook allowing it today. Then show it refusing a path in neither.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the T-0072 fix agent's report. It hit this while committing and
  widened both task files' `touches:` to proceed, which is recorded there.
- 2026-09-08T02:59:05Z claimed by agent/claude-opus-5; lease until 2026-09-08T08:59:05Z
