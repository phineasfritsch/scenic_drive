---
id: T-0137
title: "pre-commit checks nothing when a git command errors: an empty MERGE_HEAD disables the touches gate"
state: claimed
owner: agent/claude-opus-5
owner_session: 012vL7Yk1ov7eNxoFD9U6Pfm
claimed_at: 2026-09-16T02:45:00Z
lease_expires_at: 2026-09-16T06:45:00Z
worktree: .worktrees/T-0137
branch: task/T-0137
exclusive: []
touches: [.githooks/pre-commit, ops/lib/check-touches-merge.py]
pins_affected: [P-GIT-01, P-GIT-02]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "python ops/lib/check-touches-merge.py -> TOUCHES-MERGE OK (10 cases), exit 0"
  - "python ops/lib/check-touches-merge.py --variants -> TOUCHES-MERGE VARIANTS OK (3), each breaking exactly one case: --no-renames->5, error fallback->8, literal .git/MERGE_HEAD->9, exit 0"
  - "RED: git show 43f4f6f:.githooks/pre-commit > .artifacts/prefix-hook (hash ffc8d05d7f7f7f986a1f3b763a302c6d94caf730 == git rev-parse 43f4f6f:.githooks/pre-commit); python ops/lib/check-touches-merge.py --hook .artifacts/prefix-hook -> FAIL 8/empty-MERGE_HEAD must REFUSE (exit 0), TOUCHES-MERGE FAIL (10 cases), exit 1"
  - "bash ops/check-pins -> PINS ok=14 skipped=0 pending=3 expired=0 failed=0 tier=linux, exit 0"
  - "bash ops/check-pins --source-only -> PINS ok=6 skipped=10 pending=1 expired=0 failed=0 tier=linux source-only, exit 0"
  - "bash ops/lib/check-line-cap -> P-SRC-02: 25 Swift files tracked, none over 300 lines, exit 0"
---
## Brief

Found by `agent/rv-keystone` while reviewing PR #78, which it passed. This is a **new fail-open introduced by
that PR's merge case**, reported as non-blocking with the reasoning recorded, and it was right that it should
not block the keystone - but it should not sit unfiled either, and the reviewer said so ("worth a follow-up
task; I did not file one", because a sign-off commits the task file alone).

`.githooks/pre-commit:76-78`. The merge case intersects two `git diff --cached` outputs to find the author's
own changes. If **both git calls fail**, their outputs are empty, the intersection is empty, and the `while`
loop iterates over nothing - so the gate checks nothing and the commit is allowed. An empty
`.git/MERGE_HEAD` is enough to produce that, and the commit that results is an **ordinary single-parent
commit**, not a merge:

```
printf 'x\n' >> other/b.txt && git add other/b.txt
: > "$(git rev-parse --git-dir)/MERGE_HEAD"
git commit -m whatever          # exit 0
git log -1 --pretty=%P          # ONE sha - not a merge
```

CONTROL, from the same reviewer: `main`'s pre-fix hook refuses the identical sequence with
`other/b.txt is outside T-9999 touches`, exit 1.

### Why it is worth fixing even though it needs a deliberate write into `.git/`

The shape is the one this repository keeps finding: **a check that silently passes when its own machinery
fails.** Everything else here has been hardened against exactly this - `ops/lib/check-exec-bits` refuses on an
empty file set, the mutation harnesses refuse on an empty population, `--prove-vacuity` requires MISSED to be
complete. The gate that runs on *every commit by every agent* should not be the one place where "the command
errored" reads as "nothing to check".

It is also invisible when it happens. There is no output, no warning, and the commit looks normal afterwards.

### Do

1. Make the merge case fail CLOSED: if either `git diff --cached` exits non-zero, fall back to checking the
   full staged set (`"$staged"`) rather than the intersection. A gate that cannot compute the narrower set
   must check the wider one.
2. **Demonstrate red then green**, with the reproduction above as the red case and a normal merge as the
   green one, so the fix does not re-break what PR #78 just unblocked.
3. Add the case to `ops/lib/check-touches-merge.py`, whose seven cases all build plain `git init` checkouts.

### Two related findings from the same review, recorded so they are not rediscovered

* **F-B, permissive by design.** The merge case trusts *any* merge parent, not `main`. A forbidden file
  committed on a branch whose name does not match `^task/(T-[0-9]+)` - where the gate does not apply at all,
  which is pre-existing - and then merged in, is byte-identical to `MERGE_HEAD`, drops out of the
  intersection, and is never checked. The reviewer weighed this non-blocking after measuring that
  `git cherry-pick` and `git rebase` **never run `pre-commit` at all**, so a forbidden file reaches a task
  branch today in fewer steps with the hook never firing. Tightening the exemption to a `MERGE_HEAD` that is
  an ancestor of `origin/main` would close the merge route. Worth doing *with* item 1, not instead of it.
* **F-E, coverage.** The fixture only builds plain `git init` checkouts, where `--git-dir` is `.git`. The hook
  is correct today inside a **linked worktree** - which is where every task in this fleet actually runs, and
  the reviewer verified it - but nothing pins that. A later "simplification" to a literal `.git/MERGE_HEAD`
  would leave all seven cases green and break every real merge. An eighth case using `git worktree add`
  anchors it.

## Log
- 2026-09-15T23:30:00Z filed by agent/claude-opus-5 from agent/rv-keystone's review of PR #78. That PR is
  merged: the merge case is on `main`, and task branches can take an update from `main` for the first time.
  This is the debt that came with it.
- 2026-09-16T03:10:00Z claimed by agent/claude-opus-5; lease until 2026-09-16T06:45:00Z. Worktree
  `.worktrees/T-0137`, branch `task/T-0137`, off `43f4f6f`.
- 2026-09-16T03:40:00Z **Item 1 fixed, and one thing this task asked for turned out to be the defect it
  warns about.** Both git calls now run into variables so their exit codes can be read - process
  substitution throws the status away, which is the whole reason the fail-open existed - and if either is
  non-zero the gate checks `$staged`, the FULL staged set, and says so on stdout.

  **RED, reproducible from git rather than from a scratch directory:**

      $ git show 43f4f6f:.githooks/pre-commit > .artifacts/prefix-hook
      $ git hash-object .artifacts/prefix-hook          -> ffc8d05d7f7f7f986a1f3b763a302c6d94caf730
      $ git rev-parse 43f4f6f:.githooks/pre-commit      -> ffc8d05d7f7f7f986a1f3b763a302c6d94caf730
      $ python ops/lib/check-touches-merge.py --hook .artifacts/prefix-hook
        FAIL    8/empty-MERGE_HEAD          must REFUSE  (exit 0)
                    [task/T-9999 3054c54] commit with an empty MERGE_HEAD
                    fatal: ambiguous argument 'MERGE_HEAD': unknown revision or path not in the working tree.
        TOUCHES-MERGE FAIL (10 cases)                                                            exit 1

  The `fatal:` line is the point: git said it could not do the thing, and the gate read that as nothing to
  check. GREEN after the fix: `TOUCHES-MERGE OK (10 cases)`, exit 0.

  **F-E (the worktree coverage gap) was going to ship as exactly the defect this repository keeps finding.**
  My first version of case 9 was *"the same merge inside a linked worktree, resolution OUTSIDE touches:,
  must REFUSE"*. It passed - against the pre-fix hook, against the fixed hook, and against a hook with the
  `--git-dir` lookup replaced by the literal `.git/MERGE_HEAD`. It could not fail. In a linked worktree
  `.git` is a FILE, so a literal `.git/MERGE_HEAD` finds no merge, the narrowing never applies, the hook
  checks the full staged set - and a REFUSE case passes for a reason that has nothing to do with what it
  claims to pin. Only the direction that DEPENDS on the narrowing can see it. So case 9 is now
  *"resolution INSIDE touches:, must COMMIT"* - the merge every task in this fleet actually makes, the one
  PR #36 needed - and case 10 keeps the REFUSE direction so the narrowing cannot become a blanket skip in
  the one environment cases 1-8 never enter. `_linked_worktree` returns 99 (setup-failed) if `.git` is a
  directory or `--git-dir` ends in `.git`, so the pair cannot silently degrade into two more plain-repo
  cases.

  **Each variant breaks exactly one case**, which is what makes ten cases discriminating rather than
  decorative. Generated from the real hook at run time:

      $ python ops/lib/check-touches-merge.py --variants
      ok      variant without --no-renames       breaks exactly 5/rename-into-touches
      ok      variant without the error fallback breaks exactly 8/empty-MERGE_HEAD
      ok      variant literal ".git/MERGE_HEAD"  breaks exactly 9/linked-worktree-resolve
      TOUCHES-MERGE VARIANTS OK (3)                                                               exit 0

  The second variant is the fail-open exactly as it shipped: the error path computing an empty set instead
  of the wide one. The third is the "simplification" F-E predicted, and case 9 is the only case that sees
  it.

  **VERIFICATION.** `bash ops/check-pins` -> `PINS ok=14 skipped=0 pending=3 expired=0 failed=0 tier=linux`,
  exit 0 (P-GIT-02 is this fixture). `bash ops/check-pins --source-only` -> `PINS ok=6 skipped=10 pending=1
  expired=0 failed=0 tier=linux source-only`, exit 0. `bash ops/lib/check-line-cap` -> `P-SRC-02: 25 Swift
  files tracked, none over 300 lines`, exit 0 - the 300-line cap is Swift-only and this fixture is 440
  lines, which is stated here rather than discovered by a reviewer.

  **F-B is NOT fixed, and the reason is a measurement, not an opinion.** Tightening the merge exemption to a
  `MERGE_HEAD` that is an ancestor of `origin/main` closes the route where a forbidden file committed on a
  non-`task/` branch is merged in and drops out of the intersection. But every case in this fixture builds
  a repo with no remote, so the rule would have to answer "what if `origin/main` does not resolve" - and
  both answers are bad in the shape this task is about: trusting the merge is the same fail-open one level
  up, and refusing it breaks cases 1, 2 and 9. Doing it properly means giving `build()` a real bare origin
  and adding a case for a merge parent that is NOT an ancestor of it. That is a second task, not a rider on
  this one, and the reviewer who found F-B already weighed it non-blocking after measuring that
  `git cherry-pick` and `git rebase` never run `pre-commit` at all - a forbidden file reaches a task branch
  today in fewer steps with the hook never firing. Filed as a follow-up rather than half-done here.
