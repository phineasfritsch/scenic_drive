---
id: T-0137
title: "pre-commit checks nothing when a git command errors: an empty MERGE_HEAD disables the touches gate"
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.githooks/pre-commit, ops/lib/check-touches-merge.py]
pins_affected: [P-GIT-01, P-GIT-02]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
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
