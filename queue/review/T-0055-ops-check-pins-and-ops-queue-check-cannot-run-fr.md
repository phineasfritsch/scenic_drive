---
id: T-0055
title: ops/check-pins and ops/queue-check cannot run from WSL, so no single shell runs all four gates
state: review
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T23:06:34Z
lease_expires_at: 2026-09-08T01:06:34Z
worktree: null
branch: task/T-0055
exclusive: []
touches: [ops/check-pins, ops/queue-check, ops/claim, ops/lock, ops/new-task, ops/queue-next, ops/queue-sweep, ops/agent-preflight]
pins_affected: []
reviewer: agent/reviewer-45
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
- 2026-09-07T23:06:34Z claimed by agent/unknown; lease until 2026-09-08T01:06:34Z

- 2026-09-08T07:40Z implemented by agent/claude-opus-5. EIGHT wrappers converted, and the work turned up the
  actual root cause, which is not in any script.

  **THE ROOT CAUSE IS THE CHECKOUT LOCATION, and it is a plan decision that was not followed.** The plan's Dev
  box row says: *"Repo in WSL2 ext4 home, never `/mnt/c`"*, with the rationale *"CRLF and NTFS break every
  `ops/*` script"*. The repo is at `C:/Users/phineasf/Documents/GitHub/scenic_drive` - NTFS, reached from WSL
  as `/mnt/c/...`. Every symptom in this task follows from that one fact: a Windows worktree's `.git` file
  says `gitdir: C:/...`, which WSL's git cannot follow, so `git rev-parse` and every `git ls-files` inside a
  pin assertion fails there. T-0051's CRLF work is the same rationale's other half.
  Filed separately as T-0060 - it is an environment decision for the owner, not something a script can fix.

  **What this task does fix:** `ops/agent-preflight`, `check-pins`, `claim`, `lock`, `new-task`, `queue-check`,
  `queue-next`, `queue-sweep` now derive the repo root from `${BASH_SOURCE[0]}` and verify it with a marker
  file, instead of asking git. Same treatment T-0025 applied to the two etl scripts.

      before, from WSL:  fatal: not a git repository: .../wt/T-0055/C:/Users/.../worktrees/T-0055   exit 2
      after,  from WSL:  QUEUE OK (56 tasks)
      after,  git-bash:  QUEUE OK (56 tasks) / PINS ok=9 skipped=0 pending=3 expired=0 failed=0

  **THE INTERESTING RESULT.** With the wrapper fixed, `ops/check-pins` RUNS from WSL and then FAILS - because
  the pin ASSERTIONS shell out to `git ls-files` themselves, which still cannot read the worktree:

      P-OPS-01 output: only 0 files tracked under ops/ and .githooks/ (expected >= 17).
        An empty or truncated set must never read as 'all modes correct'.
      P-SRC-02 output: An empty or truncated set must never read as 'no file exceeds 300 lines'.

  Those two lines are T-0019's and T-0037's vacuity guards firing, and they are the reason this is a failure
  and not a FALSE PASS. Without them, running check-pins from WSL would have reported that no file exceeds 300
  lines and every mode is correct - over an empty set, on a machine where nothing had been checked at all.
  Two guards written for a hypothetical caught a real one the first time the door was opened. Filed as T-0061:
  the assertion layer needs the same treatment as the wrappers.

  **The acceptance criterion in the brief IS NOT MET, and I am not claiming it.** It asks for one transcript,
  from one shell, with `ops/test`, `ops/check-pins`, `ops/queue-check` and the ETL pytest all passing. That
  needs `ops/test` and `ops/sane` converted too, and both are owned by unmerged branches - `ops/test` by
  T-0023 (done) and T-0040 (review), `ops/sane` by T-0024 - so touching them here would be the
  two-agents-one-file collision CLAUDE.md forbids. Five of the thirteen scripts using this pattern are left:
  `deploy`, `merge`, `prod-read`, `sane`, `test`. Whoever merges their owning branches should convert them,
  and T-0061 covers the assertions.

  **Verification:** git-bash `ops/queue-check` -> `QUEUE OK (56 tasks)`, `ops/check-pins` -> `PINS ok=9
  skipped=0 pending=3 expired=0 failed=0 tier=linux`. WSL `ops/queue-check` -> `QUEUE OK (56 tasks)`,
  `ops/queue-next` -> `(no unblocked ready task)`. GitHub Actions is DISABLED repo-wide (T-0053), so there is
  no CI signal.

  **What to attack.** The marker file is `ops/lib/queue.py`, so `ops/check-pins` now refuses to run if that
  unrelated file is missing - a coupling I introduced for uniformity and cannot defend well. Second: the
  brief's own acceptance is unmet and I moved the task to review anyway; if you think that should have stayed
  in claimed until T-0061 lands, say so. Third: `ops/claim` with no arguments still raises IndexError and
  prints a traceback here - fixed on task/T-0032, not on main, so this branch shows the old behaviour.

