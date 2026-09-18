---
id: T-0155
title: replay the acceptance block - re-run every quoted command in a task file's acceptance lines at HEAD and refuse on a mismatch, from ops/review, not pre-commit
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/, ops/review, queue/README.md]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Filed from the 2026-09-18 11:13 panel (PROCESS lens, grounded). PR #87's round 3 FAILED on exactly one
blocking finding: three acceptance lines quoted numbers that were TRUE when written and went stale under a
merge of main (41/42 scanned -> 46/47, 10 cases -> 11, ok=16 -> ok=19), while the same push updated the Log
and the PR body. T-0150's prose regex cannot see that: the numbers were printed by a command, just not at
this head. PR #88 went FAIL -> fix -> PASS in two hours largely because its fixer re-ran all nine acceptance
lines in the fix commit (T-0141 Log :288) and caught `ok=6/132 -> ok=8/140` moved by the same kind of merge.
Make that mechanical.

**Do:** `ops/lib/replay-acceptance <task-id>` - parse the task file's `acceptance:` lines of the form
`"<command> -> <quoted output>[, exit N]"`, run each command at HEAD in the task's worktree with a timeout,
and compare: the quoted output must appear verbatim in what the command printed, and the exit code must
match when one is quoted. Print one line per acceptance line (`ok`, `STALE: quoted ... printed ...`,
`SKIP: <reason>`) and exit non-zero on any STALE. Lines beginning `RED` and lines naming a procedure rather
than a command (a script under `.artifacts/`, a mutation by hand) are SKIPPED BY NAME and counted - never
silently; a block that is all skips is refused as an empty population. Commands that need the network
(`gh api`, `swift package resolve`) run only with `--network`.

Wire it into `ops/review <id> --reviewer` as the first thing a reviewer sees, and document it in
`queue/README.md`. NOT a pre-commit hook: T-0141's nine lines include `swift package` and `gh api`, and a
full `bash ops/check-pins` takes minutes.

**Demonstrated red** on PR #87's round-3 head (`git worktree add --detach ... 4aa8995`): lines 5, 10 and 11
reported STALE with the quoted and the printed values; then green at the round-4 head.

Not folded into T-0150: different touches (T-0150 edits `.githooks/pre-commit` and depends_on T-0143), and
different defect (a count nobody printed vs a count that went stale).

## Log
- 2026-09-18T18:00:00Z filed by agent/claude-fable-5-1 from the 11:13 panel (PROCESS F2, grounded; the clause folding it into T-0150 was ruled WRONG by the grounding pass). Not started.
