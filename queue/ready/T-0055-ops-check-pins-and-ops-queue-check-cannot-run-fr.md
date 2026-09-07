---
id: T-0055
title: ops/check-pins and ops/queue-check cannot run from WSL, so no single shell runs all four gates
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/check-pins, ops/queue-check, ops/claim, ops/lock, ops/new-task, ops/queue-next, ops/queue-sweep, ops/agent-preflight]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Found by agent/reviewer-34 while reviewing T-0025 round 4, stated as an aside and worth more than that:

    "ops/check-pins and ops/queue-check still use git rev-parse and cannot run from WSL, so no single shell
     runs all four gates."

On this box the repo is a Windows checkout. WSL's git cannot read a Windows worktree's `.git` file - it holds
a path like `C:/Users/.../worktrees/T-0025` that no Linux `cd` can use - so `git rev-parse --show-toplevel`
either fails or prints something unusable. Meanwhile the pinned `scenic-etl` image is reachable ONLY from
WSL, because docker is not on PATH in git-bash.

The result is that verifying a change takes two shells and nobody can produce one transcript of all four
gates. Every "Verification" block in this repo's task logs is therefore stitched together by hand from two
sessions, which is exactly the kind of seam where a number gets copied from the wrong run - and this task's
own history has three separate instances of a figure being reported from the wrong place.

T-0025 already fixed this shape of bug in two scripts: `ops/etl-curvature-fixture` and `ops/etl-oracle-report`
stopped using `cd "$(git rev-parse --show-toplevel)"` and now derive the root from `${BASH_SOURCE[0]}` and
verify it with a marker file. Before that fix, the failure was SILENT - without `set -e` the `cd` failed and
the script carried on in whatever directory it started in, which happened to be the right one.

- Apply the same treatment to `ops/check-pins` and `ops/queue-check`, and audit every other script under
  `ops/` for the same `cd "$(git rev-parse ...)"` pattern - fix them all in one pass, since they share the
  failure and reviewing five small identical diffs separately is wasted effort.
- Anything that genuinely NEEDS git (queue-check reads task files, check-pins may shell out) still needs to
  work; the point is that locating the repo root must not depend on git being able to read the worktree.
- Demonstrate red properly: run each script from WSL against this Windows worktree BEFORE the change and
  capture what it actually does - which for some will be "fails loudly", for others "succeeds by accident
  from the right directory". Those are different failures and the log should say which is which.
- The acceptance test is one transcript, from one shell, containing `ops/test`, `ops/check-pins`,
  `ops/queue-check` and the ETL pytest run in the pinned image, all passing.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from agent/reviewer-34's T-0025 round-4 review.

### 2026-09-08 - measured before claiming, and it corrects this brief

The brief above speculated that some scripts would "succeed by accident from the right directory". They do
not. Measured from WSL against a Windows worktree:

    bash ops/queue-check  -> exit 2
    bash ops/check-pins   -> exit 2
    bash ops/test         -> exit 1

All FAIL CLOSED, loudly, with git's own "fatal: not a git repository" on stderr. So this is not a correctness
hole and no gate has ever reported success without running - which is the thing that would have made it
urgent. It is an ergonomics defect, and its real cost is the one the brief already names: every Verification
block in this repo is stitched together from two shells, and that seam is where a number gets copied from the
wrong run.

Downgraded accordingly. Still worth fixing, because the fix is three lines per script and the seam is real.

THIRTEEN scripts use the pattern, not two: agent-preflight, check-pins, claim, deploy, lock, merge, new-task,
prod-read, queue-check, queue-next, queue-sweep, sane, test. `ops/merge` and `ops/deploy` are owned by
unmerged branches (T-0021/T-0022/T-0044/T-0049 and the deploy chain), so this task takes the eight that are
free on main and names the rest for whoever merges them.

Also measured and NOT a defect: `ops/queue-check` failed once with
`/c/.../WindowsApps/python3: Permission denied`, which looked like a Windows App Execution Alias problem. It
does not reproduce - three consecutive runs pass, and the resolved path execs fine directly. Recorded as a
transient rather than filed, because a bug nobody can reproduce is not a finding.

