---
id: T-0082
title: 32 of 48 leases have expired and queue-sweep would clobber every one of them
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T03:28:24Z
lease_expires_at: 2026-09-08T09:28:24Z
worktree: wt/T-0082
branch: task/T-0082
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: agent/reviewer-pr51
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**32 of the 48 tasks in `queue/claimed/` have an expired lease. None of them is abandoned.** Every one is
finished work sitting on a branch, waiting for a merge that has not been possible since 2026-09-07.

`cmd_sweep` is designed for the opposite situation - an agent that died mid-task - and does the right thing
for it: move the task back to `ready/`, clear the lease, release the locks. Run today it would do that to all
32, and each one is a compounding mistake:

1. **It sets `owner: None`.** That is precisely the state [[T-0068]] was filed to reject, and `cmd_sweep` is
   named in that brief as the tooling that produces it. A task later moved to `review/` by hand then reaches
   `done/` with no owner and, until T-0073's fix merges, no complaint.
2. **It multiplies the task-file divergence.** `main` would say `ready/<id>`; the branch says `review/` or
   `done/`. That is the add/add across two paths this session has repaired on eleven branches by hand, and it
   would be recreated on 32.
3. **It discards a signoff.** Several of these have been reviewed. Sweeping loses the reviewer along with the
   owner, and the task looks unclaimed to the next agent that runs `ops/queue-next`.

**The model is wrong, not the implementation.** A lease answers "is an agent still working on this?" The
queue is using `claimed/` to answer a different question - "has this merged yet?" - and those have completely
different timescales. An agent works for hours; a branch waits for days.

- Distinguish the two. A task whose branch is pushed and whose PR is open is not a lease candidate, whatever
  its timestamp says. `ops/claim` already records `branch:`, and `gh pr list` can say whether it is open.
- Or split the state: `claimed/` for work in progress, and something like `merging/` for work that is finished
  and waiting. The directory is the state, so this is a `git mv` and a name.
- **Whatever is chosen, `cmd_sweep` must refuse to clear an owner on a task whose branch exists on the
  remote.** That single rule makes the current 32 safe without deciding the larger question.
- [[T-0032]] releases exclusive locks on the claim -> review transition, which fixes the LOCK half. It is
  written and unmerged. This task is the OWNER half, and the two together are the whole problem.

**Demonstrate red before fixing:** run `ops/queue-sweep` against a copy of the current tree (never the real
one) and count how many task files it rewrites and how many owners it clears. That number is the finding.
[[T-0064]] is already blocked behind this: it cannot claim `scenic-index` because T-0024 holds the lock for a
task whose work is complete.

## Log
- 2026-09-08 filed by agent/claude-opus-5 after declining to sweep. The 32 figure was measured by parsing
  `lease_expires_at` from every file in `queue/claimed/`.
- 2026-09-08T03:28:24Z claimed by agent/claude-opus-5; lease until 2026-09-08T09:28:24Z

- 2026-09-08 agent/claude-opus-5 — the containment, with the sweeper still working.

  **RED, measured against a COPY of the live tree** (never the real one — `.artifacts/sweep-probe.sh` builds a
  throwaway holding only `ops/lib/` and `queue/`, which is self-contained because `ROOT` comes from `__file__`):

        BEFORE  claimed=46  ready=1  with an owner=46  locks=2
        SWEEP done (29 moved)
        AFTER   claimed=17  ready=30  with an owner=17  locks=1
                task files moved claimed/ -> ready/:  29
                files in ready/ now carrying owner: null: 30
                exclusive locks released: 1

        swept tasks whose branch EXISTS (work in flight):   29
        swept tasks with no branch at all (abandoned):       0

  (An earlier version of this table wrote `1` on the second row, summing to 30 against 29 moved. Reported
  as [medium] by the reviewer of PR #51 and confirmed: the rows had been counted over the whole post-sweep
  `ready/` directory rather than over the swept set, so the extra file was **T-0041**, which was already in
  `ready/` before the sweep, was never claimed and was never swept. The reviewer reproduced the same
  off-by-one at a different scale — 32 moved, 32 with branches, plus the same single pre-existing T-0041.
  The conclusion is unchanged and is now arithmetically consistent: no swept task lacked a branch.)

  **Twenty-nine of twenty-nine.** Not one expired lease belonged to an abandoned task; every one was pushed
  work waiting on a merge. The sweeper would have set `owner: None` on all of them — the state [[T-0068]]
  exists to reject, produced by this very function, which that brief already names — and left `main` saying
  `ready/<id>` while each branch says `review/` or `done/`, recreating on 29 branches the add/add divergence
  eleven branches had already been repaired by hand for.

  **GREEN, identical probe:**

        SWEEP kept 29 expired lease(s) whose branch still exists ...
        SWEEP done (0 moved, 29 kept)
        AFTER   claimed=46  ready=1  with an owner=46  locks=2

  **CONTROL — and this is the one that matters, because a guard that disables the tool is not a fix.** A
  genuinely abandoned task (`T-9990`, expired lease, `branch: task/T-9990-does-not-exist`) added to the
  sandbox:

        SWEEP done (1 moved, 29 kept)
        T-9990 is now in ready/, gone from claimed/, owner: null

  The dead agent is still swept. Only live work is kept.

  **FAIL-CLOSED.** Every guard here is a git query, and a git that cannot read the worktree answers "no such
  branch" to all of them — indistinguishable from "abandoned", and the wrong default by exactly the margin of
  the damage above. That is not hypothetical: from WSL against this Windows checkout, `.git` says
  `gitdir: C:/...` and WSL's git cannot follow it (T-0055). So `_git_usable()` is asked once, before anything
  moves. Demonstrated with a PATH containing python but not git:

        SWEEP REFUSED: git cannot read this repo, so 'has this task got a branch?' cannot be answered.
          Every expired lease would look abandoned and be swept. Run this where git works.
        exit 2
        claimed: 46  ready: 1   (unchanged)

  `_branch_exists` also returns True on an exception rather than False: cannot tell means do not sweep.

  **What this does NOT fix**, and the brief is right that it is the larger question: the queue is still using
  `claimed/` to answer two questions with different timescales — "is an agent working on this" (hours) and
  "has this merged" (days). This makes the current 29 safe without deciding that. [[T-0032]] fixes the LOCK
  half on the claim -> review transition and is written and unmerged.

  No fetch is done. A sweeper that reaches the network is a sweeper nobody runs, and a stale remote-tracking
  ref can only make this MORE conservative.

  `ops/lib/queue.py` is now **711 lines** — 653 before this. That is the third time in one session this file
  has grown while [[T-0059]] waits, and T-0059 is blocked because six unmerged branches hold it.

- 2026-09-08 — **the reviewer of PR #51 was right twice, and the second one had disabled the tool.**

  **(high) The guard asked the wrong question, so nothing real was ever swept again.** `cmd_claim` writes
  `branch: task/<id>` for every task without exception, and `queue/README.md` step 4 creates exactly that
  branch — `git worktree add ../wt/T-XXXX -b task/T-XXXX` — *before* any work happens. So `_branch_exists`
  is true for every task the documented workflow has ever claimed, including the one shape this sweeper
  exists for: claim, open the worktree, die. That task keeps its owner and its `exclusive:` lock forever.
  My CONTROL missed it because I wrote `branch: task/T-9990-does-not-exist`, a name `ops/claim` cannot
  produce; it proved only that the sweeper still sweeps tasks that could not exist.

  The property that actually separates the two populations is **ahead-of-main**, not existence. A
  claim-time branch sits at main's tip, zero commits ahead. The 29 expired leases of 2026-09-08 were
  pushed branches with open PRs — all ahead. `_branch_has_work(name, base)` replaces `_branch_exists`.

  **(high) The docstring's reason for not fetching was backwards.** It claimed a stale ref could only make
  the sweeper more conservative. The opposite: a branch pushed since the last fetch reads as *absent*, so
  the sweeper clears its owner and releases its exclusive lock — and nothing refuses, because git itself is
  fine and `_git_usable()` returns True. `_sweep_fetch()` now fetches and **refuses on failure**;
  `--no-fetch` is the explicit, documented escape for a single-pusher checkout.

  **Corrected control (`.artifacts/demo-t0082-review.sh`)** — two fixtures with names `ops/claim` really
  writes, in a throwaway worktree: `T-9989` = claimed, `task/T-9989` created from `origin/main`, no commits
  (agent died); `T-9988` = `task/T-9988` one commit ahead (work waiting to merge).

        ===== RED: guard as shipped in PR #51 =====
          SWEEP kept 37 expired lease(s) whose branch still exists - finished work waiting to
          SWEEP done (0 moved, 37 kept)
          T-9989 still in claimed/: YES
          T-9989 lock still held:   YES

        ===== GREEN: with the fix =====
          SWEEP kept 36 expired lease(s) whose branch carries commits - finished work waiting to
          SWEEP done (1 moved, 36 kept)
          T-9989 swept to ready/:   YES
          T-9989 lock released:     YES
          T-9988 kept in claimed/:  YES

  RED is the reviewer's finding, not a hypothetical: the abandonment this task was filed to sweep was the
  one case the fix refused to sweep. GREEN sweeps it, releases the lock, and still holds every one of the
  36 branches that carry commits — the regression T-0068 exists to reject is still rejected.

  `ops/queue-check` → `QUEUE OK (76 tasks)`.

- 2026-09-08 — **the declared `verify:` commands, run and pasted**, which `queue/README.md` step 5 requires
  and this log did not have. Raised as [low] by the reviewer of PR #51.

        $ (cd services/api && npm ci)
        $ PYTHON=$(command -v python) bash ops/test
        TESTS linux=50/50 ios=skipped failed=0 skipped=0
        OK

        $ bash ops/check-pins
        PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux

  Worth stating what the first run showed before `npm ci`, because it is the tier rule working:

        FAIL: services/api exists but vitest produced no report
        test exit=1

  `ops/test` refuses a tier that exists and did not run, rather than reporting a smaller green number. That
  is [[T-0071]]'s property, and it fired here on a real omission of mine.

  **And the part the same reviewer was right about that these two commands do not fix:** neither of them
  executes `ops/lib/queue.py`. `ops/test`'s pytest tier is `cd services/etl && pytest`, so it cannot reach
  `ops/lib/` at all — the guard this task adds, and every other guard in that file, is protected by prose in
  a task log and nothing else. Both regressions this file shipped this session (PR #50's duplicate-brief
  guard, PR #51's sweep guard) would have been caught by one test each. Filed as **T-0096**, with the
  measurements, rather than left as a note here.

- 2026-09-08 — **a borrowed branch is evidence about someone else's task.** Reviewer of PR #51, [low]: four
  claimed task files record a branch that is not their own, so the guard keeps them alive on commits that
  belong to a different task.

        T-0072  branch: task/T-0066      T-0074  branch: task/T-0069
        T-0073  branch: task/T-0068      T-0076  branch: task/T-0077

  `cmd_claim` writes `task/<id>` and nothing else, so every one of these was written by hand — and stacking
  work on another task's branch is a real workflow here, not an error. So the rule does not refuse a
  borrowed branch; it asks it for evidence about **this** task: at least one commit ahead of main touching
  `queue/*/<id>-*`. The pathspec is a glob on the id, not the file's current path, so a task that has since
  moved between queue states is still found.

  **On the four real ones the rule changes nothing**, which is the honest result and matches what the
  reviewer said (*"latent rather than active"*) — every borrowed branch here does carry a commit touching
  its task's file, so all four are held either way. Only the printed reason changes:

        RED    T-0072: refs/remotes/origin/task/T-0066 is 5 commit(s) ahead of refs/remotes/origin/main
        GREEN  T-0072: refs/remotes/origin/task/T-0066 (borrowed from another task) carries a commit
                       touching queue/*/T-0072-*

  **So the red had to be synthetic, and it is** (`.artifacts/demo-borrowed2.sh`). `T-9987`, expired lease,
  `branch: task/T-0086` — a real branch, 14 commits ahead of main, with **0** commits touching
  `queue/*/T-9987-*`:

        ===== RED: ahead-of-main only =====
          T-9987: refs/remotes/origin/task/T-0086 is 14 commit(s) ahead of refs/remotes/origin/main
          SWEEP done (0 moved, 36 kept)
          T-9987 stays in claimed/
          exclusive lock STILL HELD

        ===== GREEN: borrowed branch must touch this task's file =====
          swept T-9987 -> ready/
          SWEEP done (1 moved, 35 kept)
          exclusive lock released

  Two throwaway worktrees rather than one with `git checkout --` between runs: that idiom silently lost a
  fix earlier in this session and two "green" runs were measured against the unpatched module.

- 2026-09-08 — **reviewed by `agent/reviewer-pr51` (PR #51): pass with findings.** Recorded here because the review
  itself lived only in a gitignored scratch directory, and because this task had an open PR while its own
  file still said `state: claimed` / `reviewer: null` — the exact blindness [[T-0094]] was filed for.

  The reviewer's own summary, verbatim:

  > The change is real and I reproduced its core: with the base queue.py the sweep moves every expired lease (32 today, 29 when the author ran it) and with the new queue.py it moves none of them and leaves the tree byte-identical. `ops/test` (linux=50/50), `ops/check-pins` (ok=9 failed=0), `ops/queue-check` and `ops/sane` all pass on the branch. The 653→711 line count is exact. Three claims do not survive execution. (1) The code comment and the PR body both assert that not fetching "can only make the sweeper more conservative" — the opposite is true: in a clone that has not fetched the task branch (single-branch clone, fresh clone, the cron README step 9 asks for), the branch demonstrably exists on the remote, `_branch_exists` says no, and the sweep clears the owner and releases the exclusive lock. (2) The CONTROL uses `branch: task/T-9990-does-not-exist`, a value `ops/claim` cannot produce — it always writes `branch: task/<id>` (queue.py:523) and README step 4 creates that local branch before any work. A realistic claim-then-die agent, local branch with zero commits, is KEPT with its lock held; the crash recovery README step 9 promises is now dead for anything past step 4. (3) The RED table's two classification rows sum to 30 against 29 moved: they were computed over the whole post-sweep ready/ directory, and the "1 abandoned" is T-0041, which was in ready/ before the sweep and was never claimed or swept. Nothing here is a regression against the base for the live-work case — when `_branch_exists` returns False the new code just does what the old code did — so this is mergeable with the comment corrected, but finding 2 is a real functional regression against the base for the abandoned-agent case.

  **7 findings (2 high, 1 medium, 4 low), and 5 overclaims quoted back:**

  - `[high]` ops/lib/queue.py:409-430 (_branch_exists docstring, lines 414-417)
  - `[high]` ops/lib/queue.py:449 (_branch_exists(fm.get("branch")) in cmd_sweep) with queue.py:523 (cmd_claim writes branch=f"task/{tid}")
  - `[medium]` PR #51 body, RED block; queue/claimed/T-0082-32-of-48-leases-have-expired-and-queue-sweep-wou.md ## Log
  - `[low]` ops/queue-sweep:2 vs ops/lib/queue.py:439-443
  - `[low]` queue/claimed/T-0082-32-of-48-leases-have-expired-and-queue-sweep-wou.md (verify: [ops/test, ops/check-pins]); ops/test
  - `[low]` ops/lib/queue.py (whole file, 711 lines)
  - `[low]` queue/claimed/*.md (T-0072, T-0073, T-0074, T-0076) as consumed by ops/lib/queue.py:449

  Every `critical`, `high` and `medium` above is fixed on this branch, each with its own red-then-green
  transcript in the entries above this one. The `low` items are recorded rather than silently dropped;
  where one was substantive it was fixed and says so.

- 2026-09-08 — **second review pass by `agent/reviewer-pr51`, against the head that actually merged
  (`7750ecc`), not the one the first pass saw (`09a3836`). PASS, review -> done, with two findings.**

  `acceptance:` is `[]`, so there was nothing to run there and nothing to check it against — see finding
  (5). What was run, in the worktree at `7750ecc`, exit code taken with `<cmd> >/dev/null 2>&1; echo $?`:

        bash ops/queue-check   exit 0   QUEUE OK (76 tasks)
        bash ops/check-pins    exit 0   PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
        PYTHON=$(command -v python) bash ops/test
                               exit 0   TESTS linux=50/50 ios=skipped failed=0 skipped=0
        bash ops/sane          exit 0   SANE OK

  Both `verify:` lines match the transcript pasted above verbatim. `check-pins` was red on its first run
  (`ok=8 failed=1`, P-SAFE-05) and that was **not** this branch: `.build` carried a Swift ModuleCache
  stamped with this worktree's previous path (`GitHub/wt/T-0082`), so `swift test --filter
  SolarFixtureTests` died in `could not build module 'vcruntime'`. `rm -rf
  .build/x86_64-unknown-windows-msvc/debug/ModuleCache` and the pin is green. Recorded because a reviewer
  who stopped at `failed=1` would have failed this PR for a stale cache.

  **RED DEMO, built from scratch rather than re-run from `.artifacts/`** (`.artifacts/rvw51-probe.sh`): a
  throwaway `git init` repo with a real bare `origin`, five expired-lease fixtures whose branches are only
  shapes `ops/claim` can produce, and the same fixtures replanted between runs.

        T-9001  branch task/T-9001, 0 commits ahead   the dead agent: README step 4 ran, then nothing
        T-9002  branch task/T-9002, 2 commits ahead   work waiting to merge
        T-9003  branch task/T-9002 (borrowed), no commit touching queue/*/T-9003-*
        T-9004  branch task/T-9002 (borrowed), one commit touching queue/*/T-9004-*
        T-9005  branch null

        RED   (ops/lib/queue.py at 33d5533, this PR's base)   exit 0   SWEEP done (5 moved)
              T-9001..T-9005 all SWEPT, all five exclusive locks RELEASED
        GREEN (ops/lib/queue.py at 7750ecc)                   exit 0   SWEEP done (3 moved, 2 kept)
              T-9001 SWEPT / T-9002 kept, lock held / T-9003 SWEPT / T-9004 kept, lock held / T-9005 SWEPT

  So the guard is not vacuous in either direction: the base loses two live tasks and their locks, and the
  fix still sweeps the abandoned-agent shape the first version of this guard had made unsweepable. The two
  fail-closed paths reproduce too — `PATH` without git gives `SWEEP REFUSED: git cannot read this repo`,
  exit 2, 0 moved; an unreachable `origin` gives `SWEEP REFUSED: git fetch origin failed`, exit 2, 0 moved;
  and `--no-fetch` restores the normal 3-moved/2-kept result.

  **On the live tree**, in a throwaway worktree cut from this branch (never the real one):
  `SWEEP done (2 moved, 43 kept)`. The two are T-0014 and T-0036 — both branches exist on origin, both are
  0 commits ahead of `origin/main`, and both worktrees are `git status --porcelain` empty. Genuinely
  abandoned claims, which is the outcome the brief asked for. The four borrowed tasks are held with the
  borrowed reason, as the entry above claims.

  **(medium) `_main_ref` is defined twice on the merged head, and it is this PR's copy that is dead.**
  `ops/lib/queue.py:424` (added here, built on the three-state `_git_out`) is shadowed by
  `ops/lib/queue.py:627` (added by T-0063, built on the two-state `_git`). Python keeps the later one.
  Measured, not inferred: replacing only the definition at :424 with `raise RuntimeError(...)` leaves the
  sweep byte-identical and never raises. The two are behaviourally equivalent today — both return the first
  ref `rev-parse --verify -q` accepts and `None` otherwise, and `cmd_sweep` refuses on `None` — so this is
  not a regression, but the three-state discipline `_git_out` is documented for is not what the base ref is
  actually read with. It is a clean merge with a semantic conflict: `8c63b29`, `0c301bc` and `09a3836` each
  have one `_main_ref`; two appear only at `7750ecc`, the PR #52 merge, committed 05:23:39 — nine seconds
  before PR #51 merged at 05:23:48, and five hours after the first review pass signed off on `09a3836`.

  **(medium) the borrowed-branch evidence query is cwd-sensitive and fails OPEN.**
  `_branch_has_work` runs `git log ... {base}..{ref} -- queue/*/<id>-*` with `cwd=ROOT`. A git pathspec is
  resolved against the current directory, so when `ROOT` is not the repository root the pattern matches
  nothing, `own` is empty, and the task is swept — owner cleared, exclusive lock released, no error, no
  refusal, because git itself succeeded. That is not hypothetical here: it is the exact harness this task's
  own RED/GREEN numbers came from — `.artifacts/sweep-probe.sh` copies `ops/lib` and `queue` to
  `$ROOT/.artifacts/sweeptest`, where `_git_usable()` passes (still inside the repo) and every pathspec
  silently misses. Measured on identical refs and identical fixtures: from a worktree root T-0072, T-0073,
  T-0074 and T-0076 are kept with the borrowed reason; from `.artifacts/liveprobe` all four are SWEPT.
  Shipped `ops/queue-sweep` execs at `git rev-parse --show-toplevel`, so the tool as invoked is safe — but
  the probe the evidence was gathered with is not, and the failure is silent. `:(top,glob)queue/*/<id>-*`
  would make the query independent of where it is run from.

  **(low) the line-count claim is stale.** The PR body and the first log entry say 653 -> 711. 711 is
  `37bdea3`; the last T-0082 code commit `0c301bc` is 791 and the merged head is 902.

  **(low) `gh pr diff 51` is no longer this task's diff.** task/T-0063 was merged into task/T-0082 after the
  first review, so the PR's 835/167 now includes `queue/README.md`, `_would_duplicate_on_merge` and four
  T-0063 queue files. A later reader of this PR is reading two tasks.

  **(low, systemic — not this PR's) `acceptance:` is empty in all 66 task files and nothing notices.**
  `queue/_schema/task.md` designates that field for "the exact command and the exact expected output line"
  and "the red run: what was broken on purpose and the non-zero exit it produced". Every task file in the
  queue has `acceptance: []`, and `ops/queue-check` prints `QUEUE OK (76 tasks)` over all of them. The
  schema's own red-demo record is a field with no floor, so a reviewer sent to "run the acceptance
  commands" has none to run and the red demo survives only as prose in `## Log`.

  **(low) `--no-fetch` is matched with `"--no-fetch" in argv`,** not through `_opts`, so `--nofetch` and
  `--no_fetch` silently fall through to a real fetch instead of erroring.

  Not re-raised, already filed: nothing executes `ops/lib/queue.py` in any tier of `ops/test` (T-0096,
  backlog on main), and the file is 902 lines against CLAUDE.md's 300-line cap, which P-SRC-02 checks for
  Swift only (T-0059, T-0103).
