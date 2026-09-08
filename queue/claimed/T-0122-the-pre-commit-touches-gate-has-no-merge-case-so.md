---
id: T-0122
title: the pre-commit touches gate has no merge case, so no task branch can merge main
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T16:55:41Z
lease_expires_at: 2026-09-08T18:55:41Z
worktree: .worktrees/T-0122
branch: task/T-0122
exclusive: []
touches: [.githooks/pre-commit, ops/lib/check-touches-merge.py, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "python ops/lib/check-touches-merge.py -> TOUCHES-MERGE OK (4 cases), exit 0"
  - "RED: --hook <pre-fix> fails cases 1 and 2; --hook <naive> fails case 3"
---
## Brief

**No task branch can merge `main`.** The pre-commit `touches:` gate has no case for a merge commit, so it
refuses every file the merge brings in.

Reproduced on `task/T-0097`, which needed `main` to resolve a real conflict:

    $ git merge origin/main          # one conflict, in ops/merge; resolved by hand
    $ git commit
    pre-commit: .githooks/pre-commit is outside T-0097 touches: [ops/merge ops/merge-selftest ]
    pre-commit: .github/workflows/linux-core.yml is outside T-0097 touches: [...]
    pre-commit: ops/agent-preflight is outside T-0097 touches: [...]
    ... 41 paths ...
    pre-commit: refusing commit

Every one of those is a file `main` changed and this branch did not touch. The author changed exactly one
file, `ops/merge`, which IS in `touches:`.

`.githooks/pre-commit:32-46` reads the staged path list and compares each entry against the task's
`touches:`. `git grep -n 'MERGE_HEAD' .githooks/` returns nothing: the hook cannot tell a merge from an
ordinary commit.

## Why this is worth a task rather than a `--no-verify`

**It is very likely the cause of the branch tower.** [[T-0113]] measured 31 open PRs, ten of them based on a
branch whose own PR had already merged, and a chain of task branches stacked on merged parents with no route
back to `main`. If merging `main` into a task branch is blocked by the hook, then the only way to get
current with `main` is to branch off another task branch - which is exactly the shape [[T-0113]] found and
could not explain.

It also blocks the honest resolution of a merge conflict. A conflict is where two branches disagree, and
resolving it is the moment the most careful work happens; a gate that refuses that commit pushes people to
`--no-verify`, which turns off the secret scan and the CRLF check as well.

## What the fix must and must not do

**Must not** simply skip the check when `MERGE_HEAD` exists. A merge commit legitimately carries the
author's own conflict resolutions - `ops/merge` in the case above - and those are exactly the changes
`touches:` should still govern. Skipping the whole check would make "merge main" a way to smuggle any file
into any branch.

**Must** check the paths the author actually changed. On a merge, that is the set of files differing from
BOTH parents: a file taken unmodified from either side is not the author's edit, and a file that differs
from both is a resolution the author wrote. `git diff-tree` against each parent, intersected.

Do:

1. Teach `.githooks/pre-commit` the merge case: when `MERGE_HEAD` exists, apply `touches:` to
   `staged ∩ (differs from HEAD) ∩ (differs from MERGE_HEAD)` rather than to every staged path.
2. **RED FIRST.** The reproduction above is the red run and it is already recorded: a resolved merge of
   `origin/main` into `task/T-0097` refused with 41 paths. After the fix the same merge must commit, and a
   merge that also modifies a file outside `touches:` must still be refused - both directions, because a
   gate that only ever passes is the defect this repository is built around.
3. A check under `ops/lib/` that exercises both directions on a constructed repository, so the property has
   a witness that is not a story in this Log.

**Note the ordering problem, and do not work around it.** Fixing the hook requires committing
`.githooks/pre-commit`, which this task declares in `touches:`, so this branch can be committed normally.
But `task/T-0097`'s merge stays blocked until this reaches `main`. Its resolved files are preserved at
`.worktrees/T-0097/.artifacts/resolution/` and the merge was aborted rather than forced, so nothing is lost
and nothing was smuggled past the gate.

## Log
- 2026-09-08T16:55:41Z claimed by agent/claude-opus-5; lease until 2026-09-08T18:55:41Z

## Log

    python ops/lib/check-touches-merge.py            TOUCHES-MERGE OK (4 cases)      exit 0
    bash -n .githooks/pre-commit                     syntax OK                       exit 0

### The fix

`.githooks/pre-commit` gains a merge case. On a merge it applies `touches:` to
`staged INTERSECT (differs from HEAD) INTERSECT (differs from MERGE_HEAD)` - the files that differ from BOTH
parents. A file identical to either side arrived from that side and is not an edit; a file differing from
both is a resolution the author wrote, and those are exactly what `touches:` should still govern.

The CRLF check and the secret scan above it keep reading the raw staged list on purpose: a secret arriving
from the other side of a merge is still a secret in this branch's history.

`git rev-parse --git-dir`, not `--show-toplevel` - the latter is banned in `ops/` and the hooks because from
WSL this checkout's `.git` file reads `gitdir: C:/...` which WSL's git cannot follow (T-0060, T-0093).

### RED, against two different wrong hooks, each failing a DIFFERENT case

`ops/lib/check-touches-merge.py --hook <path>` runs the four cases against a variant.

    hook                              1 merge   2 resolve-inside   3 resolve-outside   4 plain-outside
    origin/main (no merge case)       FAIL      FAIL               ok                  ok
    naive: skip on MERGE_HEAD         ok        ok                 FAIL                ok
    this branch                       ok        ok                 ok                  ok

**Case 3 is why the naive fix is not the fix.** Skipping the check whenever `MERGE_HEAD` exists passes three
of four cases and turns "merge main" into a way to stage any file into any branch - and nothing else in the
repository would notice. It is the obvious one-line change and it is wrong.

**Case 4 is the control.** A hook that had lost the touches check entirely passes 1, 2 and 3.

Each variant fails a different case, which is what makes the four discriminating rather than decorative.

### The variant builder had a defect of its own, and it is the kind that fakes a red

The first version sliced the hook on `src.index("fi\n", ...)` and cut at the INNER
`if [[ -n "$to_check" ]]` terminator, leaving a stray `fi`. The variant did not parse, so every case failed
with a bash syntax error - **which looks exactly like a successful red run** if you only read the verdict.
Rebuilt line-based, walking the block by nesting depth. Worth recording: a red for the wrong reason is
worse than a green, because it is evidence that will be cited later.

### What this unblocks

`task/T-0097` needs `main` to resolve a genuine semantic conflict in `ops/merge` (two fixes that compose;
taking either side drops the other). That merge was aborted rather than forced past the gate, and its
resolved files are preserved at `.worktrees/T-0097/.artifacts/resolution/`. It can be redone once this
reaches `main`.

More broadly, [[T-0113]] found ten open PRs based on a branch whose own PR had already merged, and could not
explain how the tower formed. This is a mechanism that would produce exactly that shape.
