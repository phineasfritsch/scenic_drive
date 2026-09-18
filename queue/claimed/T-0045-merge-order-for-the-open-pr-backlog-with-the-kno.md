---
id: T-0045
title: merge order for the open PR backlog, with the known ADD/ADD conflict on the gh stub
state: claimed
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:52:33Z
lease_expires_at: 2026-09-07T18:52:33Z
worktree: .
branch: task/T-0045
exclusive: []
touches: [queue/]
pins_affected: []
reviewer: agent/reviewer-27
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

(what, why, and the exact demonstration that proves it — including the red run)

## Log
- 2026-09-07T16:52:33Z claimed by agent/claude-opus-5; lease until 2026-09-07T18:52:33Z
- 2026-09-18T23:04:01Z NOTE by agent/claude-fable-5-1 (16:13 panel, grounded by the verification pass against `gh pr list`): the
  stacked-base trap this task is nearest to is larger than any earlier count - 35 open PRs, of which 15 have
  `baseRefName` on a task branch (#63 #62 #56 #49 #44 #43 #42 #41 #40 #39 #38 #37 #35 #34 #29), and 13 MERGED
  PRs were based on task branches (#67 #66 #64 #52 #51 #50 #32 #31 #30 #27 #25 #23 #20), each to be proven on
  main with `git merge-base --is-ancestor <sha> origin/main` or re-landed. This task's lease expired on
  2026-09-07 and it names no branch; T-0172 (the sweep rule) will surface it.
