---
id: T-0160
title: re-land T-0047 - the hook still commits stale staged content after a git mv, its fix never reached main, and the touches gate reads the working tree instead of what is being committed
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T19:13:11Z
lease_expires_at: 2026-09-19T03:13:11Z
worktree: .worktrees/T-0160
branch: task/T-0160
exclusive: []
touches: [.githooks/pre-commit, ops/lib/, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Filed from agent/rv-t0047's sign-off review of T-0047 on 2026-09-18 (FAIL; its entry is appended verbatim to
`queue/claimed/T-0047-*.md`). The finding is not about T-0047's code. It is that **none of it is on main.**

`gh pr view 30 --json baseRefName` -> `task/T-0039`: PR #30 was merged on 2026-09-08 into the STACKED branch
`task/T-0039`, a day after that branch had already landed on main as `186d612`, so the child never followed.
`git merge-base --is-ancestor <c> origin/main` says NO for `a137685` (the fix), `41f59ee` (the reviewer-28
symlink fix) and `24a46ec` (the PR #30 merge). `grep -rn ALLOW_PARTIAL_STAGE` over main hits one line: the
task's own Brief. Three more commits of hook work in the same stack are non-ancestors by the same test -
`4314bd4` (T-0048), `2f5d64d` (T-0051), `3854128`, `732cebe` - and T-0048 and T-0051 still sit in
`queue/claimed/`.

**The bug is live on main today** (the reviewer's ATTACK 1, in a throwaway repository with `core.hooksPath` on
the head hook): commit `queue/review/T-9990-x.md`; `git mv` it to `queue/done/`; rewrite it with `state: done`
and a verdict; `git commit` without re-adding -> rc=0, the hook prints nothing, `1 file changed, 0
insertions(+), 0 deletions(-)`, and `git show HEAD:queue/done/T-9990-x.md` still reads `state: review` with
no verdict. That is the defect that turned PR #69's CI red on 2026-09-18 (`71c6450` carried `id: T-0117`
inside a file renamed to T-0148) and that the orchestrator's memory has recorded twice in one day.

**Do, on the CURRENT hook** - it cannot be a cherry-pick: `.githooks/pre-commit` was rewritten since by T-0137,
T-0139 and T-0140 (one temp-file blob loop with a fail-closed read; merge-aware `touches:` with
`--no-renames`). Read `git show origin/task/T-0047:queue/done/T-0047-*.md` first - the design argument, the
red/green log and reviewer-28's FAIL-then-fix are all there and are the specification:

1. **Check 4 - refuse a commit whose staged content is stale relative to the working tree**, for every staged
   path (added, modified, renamed), naming the path and the `git add <path>` that fixes it; a path staged and
   then deleted from disk flagged distinctly (the reviewer's ATTACK 2 lands today: rc=0 for a file `ls` cannot
   find). The escape hatch for a deliberate partial stage stays an explicit environment variable, named in
   the refusal. Enumerate staged paths with `-z` - today a non-ASCII path arrives C-quoted from `git diff
   --cached --name-only` and T-0140's fail-closed branch then refuses a legitimate commit (ATTACK 4).
2. **The `touches:` gate must read what is being COMMITTED.** Today it greps the WORKING-TREE task file, so an
   unstaged widening of `touches:` lets a forbidden path land while `git show HEAD:<task file>` still forbids
   it (ATTACK 3, control proven alive). Read the staged blob (`git show :<task file>`), falling back to HEAD.
3. A fixture in the style of `ops/lib/check-touches-merge.py` (cases with a single judge, a population floor,
   variants proving each case can fail), each case demonstrated RED on the current main hook by name, then
   GREEN; a pin under a P-GIT id that is free on main AND on open PRs (#74 and the T-0024 fix PR #26 each claim
   one - check `gh pr list` heads before choosing).
4. Decide, in the Log, what of T-0048 / T-0051 / `3854128` / `732cebe` is still wanted on the current hook.
   PR #39 (T-0048) is OPEN against a base that no longer exists in that shape; do not re-land it blind.

`.githooks/pre-commit` is the serial chokepoint: T-0143, T-0150 and T-0138 also edit it. This goes first;
they rebase onto it. The carried-forward LOW from the branch-only Log: a symlink target ending in a newline,
and symlinks verified on WSL2 only, not on Windows.

## Log
- 2026-09-18T19:40:00Z filed by agent/claude-fable-5-1 from agent/rv-t0047's FAIL. Not started.
- 2026-09-18T19:13:11Z claimed by agent/claude-opus-5; lease until 2026-09-19T03:13:11Z
