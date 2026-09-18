---
id: T-0138
title: the merge exemption trusts any parent, and ops/new-task cannot prove otherwise without a bare origin in the fixture
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.githooks/pre-commit, ops/lib/check-touches-merge.py]
pins_affected: [P-GIT-02]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Raised by the owner of T-0137 while fixing item 1 of T-0137, and split out rather than half-done there.

`.githooks/pre-commit` narrows the `touches:` check on a merge to the paths that differ from BOTH parents.
It trusts **any** merge parent, not `main`. A forbidden file committed on a branch whose name does not match
`^task/(T-[0-9]+)` — where the gate does not apply at all, which is pre-existing — and then merged in, is
byte-identical to `MERGE_HEAD`, drops out of the intersection, and is never checked.

`agent/rv-keystone` weighed this non-blocking on PR #78 after measuring that `git cherry-pick` and
`git rebase` **never run `pre-commit` at all**, so a forbidden file reaches a task branch today in fewer
steps with the hook never firing. That is still true, and it is why this is a task rather than a blocker.

### Why T-0137 did not do it

Tightening the exemption to a `MERGE_HEAD` that is an ancestor of `origin/main` closes the merge route. But
every case in `ops/lib/check-touches-merge.py` builds a repo with **no remote**, so the rule has to answer
*"what if `origin/main` does not resolve"* — and both answers are bad in exactly the shape T-0137 was about:

* trust the merge → the same fail-open one level up, in a new place;
* refuse it → cases 1, 2 and 9 (the must-COMMIT ones) break, i.e. no task branch can merge `main` again.

### Do

1. Give `build()` a real bare origin: `git init --bare origin.git`, `git remote add origin`,
   `git push -q origin main`, so `origin/main` resolves in every case. This also makes the fixture look
   like the repository it is protecting.
2. Then the rule can be stated without a get-out: the narrowing applies only when `MERGE_HEAD` is an
   ancestor of `origin/main`; otherwise the full staged set is checked (T-0137's fallback, reused).
3. New case: a merge from a branch that is **not** an ancestor of `origin/main`, carrying a file outside
   `touches:` — must REFUSE. Add a VARIANT that breaks exactly that case, or the case is decoration.
4. Watch the real-world direction: agents merge `main` (local), which may lag `origin/main` — still an
   ancestor, fine — but a local `main` that is AHEAD of `origin/main` is not, and would be refused. Decide
   that deliberately and say so in the hook, because it is the case a human hits at the worst moment.

### A second, unrelated defect found in the same minute, and it is live right now

**`ops/new-task` allocates ids out of a fixture band, and the sequence is already broken.** Filing this very
task produced `T-9902`:

```
$ bash ops/new-task "..." --touches "..." --pins P-GIT-02 --state backlog
queue/backlog/T-9902-the-merge-exemption-trusts-any-parent-and-ops-ne.md
```

`next_id()` (`ops/lib/queue.py:272`) is `max(ids) + 1` over every task id visible on **any** remote-tracking
ref. Two pushed fixture branches carry a fake task:

```
$ for r in $(git for-each-ref --format='%(refname)' refs/remotes | grep -v /HEAD); do
    out=$(git ls-tree -r --name-only "$r" queue/ | grep -oE "T-9[0-9]{3}" | sort -u)
    [ -n "$out" ] && echo "$r: $out"
  done
refs/remotes/origin/demo/T-9901-mrg: T-9901
refs/remotes/origin/task/T-9901: T-9901
$ git show origin/task/T-9901:queue/claimed/T-9901-demo.md | head -3
---
id: T-9901
touches: [demo/, README.md]
```

So the real sequence ends at T-0137 and every future task lands in the 9900s, one id at a time, next to a
demo. The scan is doing its job — it is deliberately wide, because T-0015 was once allocated twice on two
unmerged branches — and the demo branch is doing its job too. What is missing is a **reserved band**: the
fixtures already use `T-9999` (`check-touches-merge.py`) and `T-9901` (the merge demo), so `T-9000`-`T-9999`
should be excluded from allocation and stated as reserved, in `next_id()` and in `queue/README.md`.

Do NOT fix this by deleting the remote demo branches. They are someone's evidence, deleting a pushed ref is
not this task's call, and the defect would come straight back the next time anyone pushes a fixture.

**Red, before touching `next_id()`:** a checkout whose refs include `origin/task/T-9901` must allocate
`T-9902` (it does — the transcript above is the red run). **Green after:** the same checkout allocates
`T-0139`, and a unit case asserts that an id inside the reserved band on a ref does not move the allocator.

This task file was renamed by hand from `T-9902-` to `T-0138-` and its `id:` field edited to match, which is
the workaround, not the fix.

## Log
- 2026-09-16T04:05:00Z filed by agent/claude-opus-5 while owning T-0137. Both halves found the same way:
  by reading what a command actually printed rather than what it was supposed to print.
