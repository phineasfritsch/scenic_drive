---
id: T-0106
title: core.hooksPath is machine-local and unverified, so a worktree may run another branch's hooks
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/sane, ops/agent-preflight, pins/PINS.yaml]
pins_affected: [P-OPS-01]
reviewer: null
depends_on: []
verify: [ops/sane, ops/check-pins]
acceptance:
  - "ops/sane (or preflight) reports a distinct non-zero exit when core.hooksPath resolves outside the current worktree"
  - "the red run: set core.hooksPath to an absolute path into another checkout, see the check fail; set it back to .githooks, see it pass"
  - "a written re-audit verdict for every task log that records a hook red/green, saying which of them tested the branch's hook and which tested main's"
---
## Brief

Split out of the review of PR #47 (T-0071), where it invalidated a recorded red/green. It is bigger than
that PR: **every hook demonstration ever performed in a worktree may have exercised `main`'s hook rather
than the branch's**, and nothing in the repo can tell you which.

`core.hooksPath` lives in `.git/config`, which is **shared by every worktree** and is **not tracked**. When
its value is an absolute path, all worktrees run the hooks of whatever checkout that path names — normally
`main` — so a branch that *changes a hook* cannot test its own change by committing, and a branch that
*adds* a hook rule gets no enforcement at all until it merges. `extensions.worktreeConfig` is not enabled
here (`git config --get extensions.worktreeConfig` → rc=1), so there is no per-worktree override in play.

**Measured, 2026-09-08, from `wt/T-0071` (branch `task/T-0071`):**

    $ git config --show-origin --get core.hooksPath
    file:C:/.../scenic_drive/.git/config    C:\Users\phineasf\Documents\GitHub\scenic_drive\.githooks

    md5 .githooks/commit-msg on task/T-0071   8f9d42bfcad3a70d0fd7c8b43befc035
    md5 .githooks/commit-msg on main          1817aafa89e79654da96bd0b8d25135e
    main's hook, line 6:  for f in pins/floor_linux.txt pins/floor_ios.txt; do

`main`'s hook iterates two literal filenames that **no longer exist** on `task/T-0071` (T-0071 split the
combined Linux floor into three per-tier files). So a commit lowering `pins/floor_linux_swift.txt` 16 -> 10
is accepted in the worktree with no output at all, while the branch's own hook refuses it. Both halves
re-measured, using `main`'s committed hook content copied into a scratch dir so nothing executes out of the
main checkout:

    $ git -c core.hooksPath=.artifacts/oldhooks commit -m "lower a floor with no reason"
    [task/T-0071 d2fadaa] lower a floor with no reason
    GIT_COMMIT_EXIT=0        HEAD 704e0f7 -> d2fadaa, committed floor = 10

    $ git -c core.hooksPath=.githooks   commit -m "lower a floor with no reason"     # same staged change
    commit-msg: pins/floor_linux_swift.txt lowered 16 -> 10 without a 'floor-lower: <reason>' line
    GIT_COMMIT_EXIT=1        HEAD unchanged at 704e0f7

**A second fact, and the reason this needs a check rather than a one-line fix.** The value changed *during*
that session, with no record of who changed it. Read at the start of the T-0071 review-fix session it was
the absolute path above; read roughly an hour later in the same session, from the same worktree, it was:

    $ git config --show-origin --get core.hooksPath
    file:C:/.../scenic_drive/.git/config    .githooks

Relative `.githooks` is the correct value — git resolves it against the worktree root, so each worktree runs
its own hooks. But it is shared mutable state that any agent can flip, it is not in the tree, no gate reads
it, and a wrong value fails **open**: hooks silently do the wrong job and every commit looks fine.

**Do:**
- Add a check (in `ops/sane`, with its own exit code, and mirrored in `ops/agent-preflight` so it is seen
  first thing) that `core.hooksPath` resolves to the current worktree's `.githooks`. Fail when it is unset
  (git then uses `.git/hooks`, which is empty here — hooks silently do nothing), and fail when it resolves
  anywhere else. Vacuity guard: a check that could not read the config must FAIL, not pass.
- Consider a pin next to `P-OPS-01`, which already guards the exec bits on `.githooks/*`. Exec bits and
  which-file-runs are the same class of defect: the hook exists, looks right, and is not the thing running.
- **Re-audit.** Grep the task logs for recorded hook red/green transcripts and say, per task, whether it
  tested the branch's hook. Anything demonstrated by direct invocation (`bash .githooks/pre-commit`) is
  fine — that names the file. Anything demonstrated through `git commit` before this is fixed is suspect,
  and a demonstration that *passed* when it should have failed is the dangerous direction.
- Do **not** "fix" it by committing a `core.hooksPath` into any tracked config: git deliberately ignores
  repo-tracked `.gitconfig`. It has to be a checked precondition plus a documented setup step.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the PR #47 review round. All numbers above were measured in
  `wt/T-0071`, not inferred; the two `git config` readings are an hour apart in one session.

- 2026-09-08 — **filed as `T-0076` and renumbered to `T-0106`: that id already meant something else.**
  `T-0076` on `main` and on 24 other refs is *"ops/test picks whichever python3 is first on PATH"*.

  **Third id collision of the day, and the first one a tool caught.** `ops/queue-ids` ([[T-0105]]) reported
  it, having been written that morning because the first two were found by a human reading two agents'
  output side by side:

        IDS FAIL: 1 id(s) name different work on different refs
          T-0076
            core-hookspath-is-machine-local-and-unverified-s   task/T-0071
            ops-test-picks-whichever-python3-is-first-on-pat   main, task/T-0045, task/T-0060 (+22 more)

  **How this one was issued is worth more than the renumber.** It was not the read/push race [[T-0101]] was
  filed for. `task/T-0071`'s own tree tops out at `T-0075` and `main` is at `T-0104`, so `next_id()` returned
  `max + 1` from the worktree alone — 28 ids below the real maximum. That is `_ids_in_refs()` taking its own
  documented degraded path, warning to stderr where nobody reads it, and continuing. T-0101 now refuses
  instead of warning, for exactly this reason.
