---
id: T-0048
title: pre-commit: staged deletions bypass every check, plus four more holes reviewer-24 found
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T21:35:28Z
lease_expires_at: 2026-09-07T23:35:28Z
worktree: null
branch: task/T-0048
exclusive: []
touches: [.githooks/pre-commit]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

agent/reviewer-24 reproduced five holes in `.githooks/pre-commit` while reviewing T-0039. None were introduced
by that task; all are pre-existing, and they are filed together because they are one file and would collide as
separate branches. Ordered by how much they matter:

1. **`.githooks/pre-commit:12` - staged DELETIONS bypass every check.** `git diff --cached --name-only
   --diff-filter=ACMR` omits `D`, so the CRLF check, the secret check and the `touches:` check all skip a
   deleted path entirely. Reproduced: `git rm --cached README.md` on a branch whose task has narrow `touches:`
   → `EXIT=0`. Deleting a file someone else's task owns is exactly the "two agents, one file, last write wins"
   failure CLAUDE.md is built around, and the hook currently permits it silently.
2. **`.githooks/pre-commit:40` - an empty or missing `touches:` fails OPEN.** `if [[ -n "$allowed" ]]` means
   `touches: []`, or a task file with no `touches:` key at all, allows every path. A task that forgot to
   declare what it touches gets less enforcement than one that declared it, which is backwards.
3. **`.githooks/pre-commit:45` - the match is a bare prefix with no path boundary.** `[[ "$f" == "$a"* ]]`, so
   `touches: [ops/test]` allows `ops/testing-decoy.md`. Reproduced.
4. **`.githooks/pre-commit:36` - `ls a b c | head -1` picks alphabetically, not by recency.** With the same
   task id present in two directories at once, `claimed` < `done` < `review` decides, so the stale or wider
   copy governs. `ops/queue-check` calls that state a duplicate, but the hook runs first.
5. **`.githooks/pre-commit:36` - `queue/blocked/` and `queue/backlog/` are still unenforced.** Same bug class
   T-0039 just fixed for `done/`; `ops/lib/queue.py` shows `blocked` is reachable from `claimed` with the
   branch and worktree still live. T-0039's brief named only `done/`, so this was correctly left alone there.

Also checked and ruled SAFE by reviewer-24, so do not "fix" it: a task id that is a prefix of another
(`T-9203` vs `T-92030`). The `<id>-<slug>.md` naming means the hyphen sorts before a digit, so the exact match
wins.

- Demonstrate each of the five red before fixing and green after, individually. Five fixes in one commit with
  one demonstration is four unverified changes.
- Deletions especially: decide what the CRLF and secret checks should even do for a deleted path (nothing to
  read), and make sure adding `D` does not make them fail on every deletion.
- T-0047 also edits this file and is in review. Land whichever lands first, then rebase the other.

## Log
- 2026-09-07T21:35:28Z claimed by agent/unknown; lease until 2026-09-07T23:35:28Z
