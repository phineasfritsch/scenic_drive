---
id: T-0047
title: pre-commit should refuse a commit whose staged content is stale relative to the working tree
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.githooks/pre-commit]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Six agents in one session have shipped a commit whose staged content was stale relative to the working tree,
every one of them the same shape:

    git mv queue/review/T-XXXX-....md queue/done/T-XXXX-....md   # stages the rename against the PRE-edit blob
    # ... edit the file: state: done, append findings ...
    git add <one path>                                            # a second path in the same command was wrong,
                                                                  # or the edit came after the mv and was never staged
    git commit                                                    # lands a pure rename, 0 insertions

`git status` shows a clean rename and says nothing is wrong. The reviewer's verdict, their `state: done`, and
their entire findings log are simply absent from the commit. Two agents caught it only because the task
instructions told them to run `git show HEAD:<path>` afterwards; the rest caught it by luck or not at all
(agent/reviewer-18's first PASS commit `43565bb` had to be repaired by `b2b79f3`; agent/reviewer-22's
`290a99a` by `54268e8`; agent/reviewer-20's by `7ece47a`).

An instruction that has to be repeated in every prompt is not a guard. This is mechanical and belongs in the
hook.

- In `.githooks/pre-commit`, for every path that is staged, compare the staged blob to the working-tree file.
  If they differ, the commit is about to record something other than what the author is looking at: refuse,
  name the paths, and say `git add <path>` fixes it.
- Consider whether this should be a refusal or a warning. Argue it in the log. A refusal is right if the
  legitimate cases are rare; the obvious legitimate case is a deliberate partial stage (`git add -p`), so say
  how someone does that on purpose - an env var like `ALLOW_PARTIAL_STAGE=1`, or exempting a path the author
  names.
- Demonstrate red: reproduce the exact `git mv` + edit + commit sequence and show the hook accepts it today,
  then refuses after the fix. Then show a deliberate partial stage still works by whatever route you chose.
- Check the interaction with the existing `touches:` and CRLF checks - both read `git show ":$f"`, i.e. the
  staged blob, which is correct and should stay that way.

Related: T-0039 fixes a different hole in the same hook (the `touches:` block being skipped for tasks in
`queue/done/`). Land that first if both are open; they touch the same file.

## Log
