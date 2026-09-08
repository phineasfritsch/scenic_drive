---
id: T-0094
title: queue-check reports OK while a task with an open PR sits in claimed with reviewer null
state: claimed
owner: agent/queue-pr-gate
owner_session: d217767a
claimed_at: 2026-09-08T07:12:17Z
lease_expires_at: 2026-09-08T11:12:17Z
worktree: null
branch: task/T-0094
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**The reviewer-is-not-owner gate cannot fire, because the state it inspects is never reached.**
`ops/queue-check` enforces `reviewer != owner` — CLAUDE.md names it as the mechanism — but only for tasks
that are *in* `queue/review/` with a `reviewer:` set. A task whose PR is open while its file still says
`state: claimed` / `reviewer: null` is not checked against anything, and `queue-check` reports `QUEUE OK`.
Found by the reviewer of PR #54 as a [low] on one task. It is not one task.

Measured on 2026-09-08, on **each PR's own head** (not on main — a task moved to `review/` on its branch
correctly still reads `claimed` on main until it merges, so main is the wrong place to look):

    PR#17..#46   31 PRs   ->  queue/review/ or queue/done/, reviewer set on every one
    PR#47 T-0071 -> CLAIMED reviewer=null        PR#52 T-0063 -> CLAIMED reviewer=null
    PR#48 T-0075 -> CLAIMED reviewer=null        PR#53 T-0083 -> CLAIMED reviewer=null
    PR#49 T-0062 -> CLAIMED reviewer=null        PR#54 T-0060 -> CLAIMED reviewer=null
    PR#50 T-0070 -> CLAIMED reviewer=null        PR#55 T-0065 -> CLAIMED reviewer=null
    PR#51 T-0082 -> CLAIMED reviewer=null        PR#56 T-0081 -> CLAIMED reviewer=null

    10 of 10 consecutive PRs, all opened in one session, all reporting QUEUE OK on their own head.

The process held for 31 PRs and then failed 10 times in a row without a single check going red. That is
the signature this repository was built to catch: **a gate that passes because the work never enters the
state the gate reads.** `queue/README.md` step 6 is the only thing asking for the transition, and step 6
is prose.

**What makes this load-bearing rather than tidiness.** `reviewer != owner` is the one mechanical defence
against an agent reviewing its own work. Ten open PRs currently carry no reviewer at all, so for those ten
the rule is not merely unchecked — there is nothing for it to check. A merge that lands one of them lands
work whose reviewer field was never populated, and `ops/merge` does not ask.

Do:

1. `ops/queue-check` gains a rule: **a task whose branch has an open PR must not be in `claimed/`, and
   must carry a non-null `reviewer:`.** Ask GitHub through the same stub seam the merge tests already use
   (`ops/lib/gh-stub-for-merge-tests`), so this is testable offline and does not make `queue-check` require
   the network — a check nobody can run offline is a check people stop running.
2. When GitHub cannot be reached, the rule must **say it was skipped and why**, and must not silently pass.
   A guard that reads an unavailable fact in silence is the fail-open class T-0063 and T-0082 both hit.
3. Red demo: a fixture task in `claimed/` with `reviewer: null` and a stubbed open PR on its branch → exit
   non-zero, naming the task and the PR. Green: the same task in `review/` with a reviewer set → exit 0.
   Also demonstrate the offline path prints the skip line and does **not** report OK as though it checked.
4. Then transition the ten real tasks above with `git mv` on each branch — a copy left in two directories
   is what makes `queue-check` fail (see [[queue-transition-on-stacked-branches]]); each must get a
   `reviewer:` that is not `agent/claude-opus-5`.

**Do not** make the rule key on "a PR exists" alone: a `device/*` or `tmp/*` branch has no task file and
must not be dragged in. Key on the task id parsed from the head ref, the way `ops/merge` already does.

## Log
- 2026-09-08T07:12:17Z claimed by agent/queue-pr-gate; lease until 2026-09-08T11:12:17Z
- 2026-09-08 **the open-PR gate, in `ops/lib/queue.py` only** (`touches:` unchanged, one file, +80 lines).

  **Re-measured first, and the brief's number has moved.** `.artifacts/measure-open-prs.sh` walks every
  open PR and reads the task file **on that PR's own head** (`git ls-tree`/`git show origin/<head>:<path>`,
  never main). 41 open PRs name a task; the violators are now **four**, not ten and not nine — a sweep
  landed while this task was in flight (#49 T-0062, #50 T-0070, #51 T-0082, #52 T-0063, #53 T-0083,
  #54 T-0060 have all been transitioned since the brief was written):

      PR#47 task/T-0071  dir=claimed  reviewer=null   <== VIOLATION
      PR#48 task/T-0075  dir=claimed  reviewer=null   <== VIOLATION
      PR#55 task/T-0065  dir=claimed  reviewer=null   <== VIOLATION
      PR#56 task/T-0081  dir=claimed  reviewer=null   <== VIOLATION
      ---- open PRs naming a task: 41   violations (claimed/ or reviewer null): 4

  **What the rule is.** After the existing `cmd_check` rules: ask GitHub for the open PR whose head is the
  branch this tree is on; parse `T-\d{4}` out of the **head ref gh returns** (the way `ops/merge` gate 1
  keys, `ops/merge:34`); look that id up in the tree; require its directory to be `review/` or `done/`
  (`PR_OPEN_OK_STATES`) and its `reviewer:` to be non-null. Two `gh` calls, ~1s.

  **Why keyed on the branch this tree is on, not on a repo-wide `gh pr list`.** A repo-wide list compared
  against the local tree is *wrong*, and the brief says why in its own methodology: a task correctly moved
  to `review/` on its branch still reads `claimed` on main until it merges. Every one of the 37 correctly
  transitioned PRs above would be a false positive on main. The fact is only readable on the PR's own head,
  so the check reads it there — which is also where CI and every agent runs `ops/queue-check`. It also
  means the rule never turns the shared tree red for someone else's branch.

  **The seam.** `gh` resolved on `PATH`, the seam `ops/merge` already uses, so the committed
  `ops/lib/gh-stub-for-merge-tests` double drives it offline with `STUB_HEAD_REF`. `_run` resolves argv[0]
  through `shutil.which` — without that the seam is **dead on Windows**: `CreateProcess` only appends
  `.exe`, so an extensionless `gh` shim is silently stepped over and the *real* network answers the
  "offline" test. Caught it doing exactly that on the first run of the demo (transcript below was `no pull
  requests found for branch "task/T-0094"` — the real CLI — while the stub sat unused on `PATH`).

  Demo: `bash .artifacts/demo.sh`. The stub is `git show origin/task/T-0022:ops/lib/gh-stub-for-merge-tests`
  verbatim (sha256 prefix `e836715e40966308` on both sides), plus a `gh.cmd` that runs it, in a dir
  prepended to `PATH`. Fixture `T-9001` is created in the real `queue/` and removed by the trap.

  **0. RED — the defect itself.** Pre-fix `queue.py` (`git show HEAD:ops/lib/queue.py`), same fixture in
  `claimed/` with `reviewer: null`, stub reporting an open PR on `task/T-9001`:

      QUEUE OK (89 tasks)
      EXIT=0

  **1. RED — the gate.** Same fixture, same stub, `ops/queue-check`:

      open-PR gate: checked T-9001 against a PR on task/T-9001
      QUEUE CHECK FAIL
       - queue/claimed/T-9001-open-pr-gate-fixture.md: a PR is open on task/T-9001 but the task is still in claimed/ - a PR is the request for review, so git mv it to queue/review/ before opening one
       - queue/claimed/T-9001-open-pr-gate-fixture.md: a PR is open on task/T-9001 but reviewer: is null - the reviewer-is-not-owner rule has no reviewer to read
      EXIT=1

  **2. GREEN.** Same task in `review/` with `reviewer: agent/fixture-reviewer` (≠ owner), same open PR:

      open-PR gate: checked T-9001 against a PR on task/T-9001
      QUEUE OK (89 tasks) - open-PR gate: checked T-9001 against a PR on task/T-9001
      EXIT=0

  **3. RED — the rule this task exists to un-block.** With the task now forced into `review/`, flipping the
  reviewer to the owner finally has a state to read (this is the assertion that could never fire before):

      QUEUE CHECK FAIL
       - queue/review/T-9001-open-pr-gate-fixture.md: reviewer == owner (agent/fixture-owner) - a worker may not grade its own work
      EXIT=1

  **4. NOT DRAGGED IN.** Fixture back in `claimed/` with `reviewer: null` — a non-task head ref must not
  key onto anything, and must say so rather than passing quietly:

      open-PR gate: nothing to check - head ref tmp/stub-no-task names no task (T-nnnn)
      QUEUE OK (89 tasks) - open-PR gate: nothing to check - head ref tmp/stub-no-task names no task (T-nnnn)
      EXIT=0
      open-PR gate: nothing to check - head ref device/iphone-15 names no task (T-nnnn)
      QUEUE OK (89 tasks) - open-PR gate: nothing to check - head ref device/iphone-15 names no task (T-nnnn)
      EXIT=0

  **5. OFFLINE — skipped, said so, did not report OK as though it checked.** Fixture still in `claimed/`
  with `reviewer: null`, i.e. the violating state; the gate must not swallow it silently. Both a `gh` that
  cannot reach GitHub and no `gh` at all (GitHub CLI stripped from `PATH`):

      open-PR gate SKIPPED, NOT CHECKED: GitHub could not be reached (dial tcp: lookup api.github.com: no such host)
      QUEUE OK (89 tasks) - open-PR gate SKIPPED, NOT CHECKED: GitHub could not be reached (dial tcp: lookup api.github.com: no such host)
      EXIT=0
      open-PR gate SKIPPED, NOT CHECKED: GitHub could not be reached (gh is not installed)
      QUEUE OK (89 tasks) - open-PR gate SKIPPED, NOT CHECKED: GitHub could not be reached (gh is not installed)
      EXIT=0

  The skip line goes to **stderr** as well as onto the `QUEUE OK` line, because P-PROC-01 runs
  `bash ops/queue-check >/dev/null` and a skip that only reached stdout would be invisible exactly there.
  Exit stays 0 on a skip on purpose: `ops/queue-check` must keep working offline (T-0055). Loud, not fatal.

  `gh repo view` runs before `gh pr view` — that split is the whole of requirement 2. Without it a network
  failure and "this branch has no PR" are the same non-zero exit, and the gate passes in silence.

  **Vacuity.** The gate emits exactly one of four outcomes on every run and never nothing: `SKIPPED, NOT
  CHECKED: <reason>` / `nothing to check - <no open PR>` / `nothing to check - head ref names no task` /
  `checked <T-nnnn> against PR #n`. A reader can always tell whether the fact was read.

  Verify: `ops/test` -> `TESTS linux=50/50 ios=skipped failed=0 skipped=0 / OK`;
  `ops/check-pins` -> `PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux`; `ops/sane` -> `SANE OK`.
  `git status --short` after the demo shows only ` M ops/lib/queue.py` — no fixture left behind.

  **Deliberately NOT done here, still to do:** the four real violators (#47 T-0071, #48 T-0075,
  #55 T-0065, #56 T-0081) are untouched. That sweep is `git mv` + `reviewer:` on four *other* branches and
  would put four other tasks' files in this task's `touches:`. Each needs a reviewer that is not its owner
  (see [[queue-transition-on-stacked-branches]]: `git mv`, never a copy that leaves the file in two dirs).

  **Known limitation, worth a follow-up task:** `.github/workflows/linux-core.yml` runs `ops/queue-check`
  inside the pinned swift image, which has no `gh` and no `GH_TOKEN`, so in CI this gate prints
  `SKIPPED, NOT CHECKED: gh is not installed` and CI stays green. It bites where an agent runs
  `ops/queue-check` on its own branch. Making it bite in CI means installing `gh` and passing
  `GH_TOKEN: ${{ github.token }}` on that step — `.github/` is outside this task's `touches:`.
