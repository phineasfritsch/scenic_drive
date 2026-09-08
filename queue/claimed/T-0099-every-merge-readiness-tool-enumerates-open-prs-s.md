---
id: T-0099
title: every merge-readiness tool enumerates open PRs, so eleven branches of work are invisible
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T07:46:38Z
lease_expires_at: 2026-09-08T10:46:38Z
worktree: null
branch: task/T-0099
exclusive: []
touches: [ops/merge-rehearse, ops/pr-ci-preflight]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**"37 of 41 merged, 0 gate failures" describes 41 of 52 branches. The other eleven have never been
rehearsed, and nobody noticed because both tools ask GitHub for pull requests instead of asking git for
branches.**

    ops/merge-rehearse:76   mapfile -t EDGES < <(gh pr list --state open --limit 200 ...)
    ops/pr-ci-preflight     same source, by construction - it gates PR CI

Measured on 2026-09-08: 62 `origin/task/*` refs exist, 41 have an open PR, and **eleven carry commits ahead
of `main` with no PR at all**:

    task/T-0069   59 commits      task/T-0086   15 commits      task/T-0078    2 commits
    task/T-0029   55 commits      task/T-0068   11 commits      task/T-0057    1 commit
    task/T-0087   28 commits      task/T-0077    8 commits
    task/T-0085    9 commits      task/T-0066    5 commits
    task/T-0079    5 commits

Ten of the eleven hold a task in `queue/claimed/` on their own head — live, owned work. `task/T-0087` alone
is the `_opts` rewrite that closes [[T-0084]] and two other overclaimed routes; `task/T-0086` is the
environment seal; `task/T-0077` is one of the two branches [[T-0093]] depends on. **None of it has ever been
merged even in rehearsal**, so nothing in this repository knows whether it collides with the 41 that have.

**Why this is the repository's own recurring defect and not an oversight.** The tool measures the set it can
see and reports a number about "the backlog". A reader — including the author, in a status report published
today — takes `37 of 41` as merge readiness. It is merge readiness *of the branches with PRs*. That is the
same shape as a floor that guards a different list than the one it names ([[T-0058]]), a guard whose
expected value comes from the thing it checks, and a suite that reports OK having inspected nothing. The
count was never wrong; the noun it was attached to was.

**`task/T-0057` is a second finding sitting inside the first.** Its task is in `queue/ready/` — unclaimed —
while a branch with a commit exists for it. Work started without a claim, so the compare-and-swap that makes
this queue safe never happened and a second agent could claim T-0057 tomorrow.

Do:

1. Enumerate **branches**, not PRs: `git for-each-ref refs/remotes/origin/task/*` filtered to those ahead of
   `origin/main`. The PR list stays useful for the *ordering* edges (`baseRefName` says what is stacked on
   what) and for CI state, but it must not decide what gets rehearsed.
2. Report the two populations separately, because they mean different things:
   `41 with a PR, 11 without` — a branch with no PR has no CI result at all, so a clean rehearsal of it says
   only that it merges, not that it passes.
3. **Vacuity guard for the enumeration itself:** if the branch set is smaller than the PR set, fail. That is
   the exact condition that would have caught this, and it is cheap.
4. `ops/pr-ci-preflight` cannot gate what has no PR — say so in its own output rather than leaving a reader
   to assume its denominator is the backlog.

Then re-run the cumulative rehearsal over all 52 and record the real number in `queue/MERGE-ORDER.md`,
replacing the one that is there.

**Do not "fix" this by opening eleven pull requests.** That hides the tool defect behind a one-time cleanup,
and the next branch without a PR is invisible again. Open them if the work is ready, but land the
enumeration fix either way.

## Log
- 2026-09-08T07:46:38Z claimed by agent/claude-opus-5; lease until 2026-09-08T10:46:38Z

- 2026-09-08 — **branches, not pull requests — and the first run of the fix broke the tool in two more
  places, both of which are now closed.**

  **The enumeration.** `ops/merge-rehearse:76` built its branch list from `gh pr list --state open`, so a
  ref ahead of `main` with no PR was never rehearsed and never counted:

        branches: 55 to rehearse = 44 with an open PR + 11 with none
        no-PR branch: task/T-0069 (59 commit(s)) - rehearsed here, but it has NO CI result anywhere
        no-PR branch: task/T-0029 (55 commit(s)) - ...
        ... nine more

  PRs still supply the ordering — `baseRefName` is the only place that says what is stacked on what — and
  they are the only source of CI state. They no longer decide what gets rehearsed. The derived ordering rule
  picked up `task/T-0080` on its own the moment its PR existed, which is the argument for deriving rather
  than listing, made again without being asked.

  **DEFECT 1, mine, found by demanding a red run for the guard I had just written.** The vacuity guard
  compared the unique heads in `EDGES` against the unique PR heads — but `EDGES` *starts* as the PR list, so
  that count can never fall below it. Pointing the ref query at an empty namespace added nothing, the guard
  passed, and the tool rehearsed 44 branches while printing a total. **A guard whose expected value comes
  from the thing it checks: the defect this entire task is about, written into the check for it.** It now
  counts refs and PR heads in the same namespace independently:

        RED   (guard as first written, ref query aimed at an empty namespace)  -> ran anyway
        GREEN REHEARSAL REFUSED: git lists 0 ref(s) under refs/remotes/origin/task/ but GitHub reports
                49 open PR head(s) in that namespace. ...                          real exit 2

  **DEFECT 2, also mine, and it invalidated an entire run.** `$SCRATCH` is a FIXED path and this script's
  first act is `git worktree remove --force "$SCRATCH"`. I started a copy of the script (to demo the guard
  above) while a real run was in flight; the copy deleted the live run's worktree, and from that moment
  every remaining branch answered from a directory that was no longer a worktree. The run reported:

        REHEARSAL (cumulative): 10 of 55 merged, 12 conflicts, 3 gate failures, 33 unresolvable
        task/T-0045   UNRESOLVABLE: no origin/task/T-0045      <- exists; 7a93410

  **None of that was true**, and it is the second time this tool has printed a confident summary of nothing
  (the first was the CRLF truncation the merge loop already documents). Two fixes:

  - **A lock.** `set -o noclobber` + `>` is the shell's compare-and-swap. A second run now refuses:

            REHEARSAL REFUSED: another run holds .../\.artifacts/merge-rehearse.lock
              pid=78104 started=2026-09-08T09:14:45Z
              This tool deletes and recreates one fixed scratch worktree, so two runs destroy each other's.
            real exit 2

    and the first run survives, which is exactly what would have saved the corrupted one.
  - **Three answers, not two.** `git rev-parse --verify origin/$b` failing was read as "that branch does not
    exist". The third answer — *git cannot answer at all* — is what happened, and it is now separated with
    `git rev-parse --git-dir`. The run ABORTS and says every row below is not a measurement, instead of
    counting 33 healthy refs as missing.

  `ops/pr-ci-preflight` cannot gate what has no PR, so it now says how many branches it did not cover rather
  than leaving its denominator to be read as the backlog.

  **Cost worth recording:** the pair loop that derives delete/modify edges is O(n²) shell with process
  substitution. At 44 branches it took minutes; at 55, with eleven branches that all delete
  `pins/floor_linux.txt`, it took far longer than the merging did. That is a real cost of this fix, not a
  reason to reverse it.

- 2026-09-08 — **review of PR #67 FAILED the task on three findings. All three reproduced, all three fixed,
  each demonstrated red then green. Fixer, not reviewer: the queue state is unchanged.**

  Reviewer's findings: https://github.com/phineasfritsch/scenic_drive/pull/67#issuecomment-5585591023

  **FINDING 1 — the vacuity guard did not guard the enumeration. REPRODUCED, then fixed.**
  The enumeration read refs at one line and the guard ran its OWN SECOND COPY of that same query at another,
  so it measured whether the query CAN return refs, never whether the loop consuming it DID. Reproduced with
  three truncated copies of the script (`.artifacts/t99probe/mkprobe.py`), identical except at those two
  lines, each stopping after the `branches:` line so the guard's verdict is the only thing measured; exit
  codes taken with no pipe in between:

        PRE-FIX
        PROBE B  only the ENUMERATION's query aimed at refs/remotes/origin/zzznope/*
                 branches: 35 to rehearse = 35 with an open PR + 0 with none        REAL EXIT = 0
        PROBE D  enumeration deleted outright: `done < /dev/null` - the pre-fix state itself
                 branches: 35 to rehearse = 35 with an open PR + 0 with none        REAL EXIT = 0
        PROBE C  BOTH queries aimed at the empty namespace (the old log's own red demo)
                 REHEARSAL REFUSED: git lists 0 ref(s) ...                          REAL EXIT = 2

  `+ 0 with none` is not a missing number, it is a false one — 31 branches were ahead of main with no PR at
  that moment. The guard was red only for a fault that hit its own private copy. The reviewer is right, and
  the log entry above this one is wrong where it presents that guard as the fix.

  The guard now reads **what the loop produced**. `SEEN_REFS` is appended to inside the loop body, so it is
  the enumeration's own output; `PR_HEADS` comes from GitHub, an independent source. Two floors, both on the
  population actually examined: the loop must have consumed at least one ref, and every open PR head under
  `task/` must be among the refs it consumed, **by name**.

        POST-FIX (same probes, regenerated from the fixed script)
        PROBE A  unmodified
                 branches: 67 to rehearse = 36 with an open PR + 31 with none       REAL EXIT = 0
        PROBE B  enumeration aimed at the empty namespace
                 REHEARSAL REFUSED: the branch enumeration consumed 0 ref(s) while GitHub reports 35 open
                 PR edge(s). ...                                                    REAL EXIT = 2
        PROBE D  `done < /dev/null`
                 REHEARSAL REFUSED: the branch enumeration consumed 0 ref(s) ...    REAL EXIT = 2
        PROBE E  enumeration aimed at refs/remotes/origin/task/T-00[0-3]* - a PARTIAL loss, 27 refs seen,
                 so the vacuity floor does NOT fire and the old count-based guard stays green here too
                 (its own full query still returns all 80 task refs, comfortably >= 37)
                 REHEARSAL REFUSED: the branch enumeration consumed 27 ref(s) under
                 refs/remotes/origin/task/, and 32 of GitHub's 37 open PR head(s) in that namespace were
                 not among them:  task/T-0040 task/T-0041 task/T-0043 ...           REAL EXIT = 2

  **FINDING 2 — the lock was per-worktree; the resource is repo-global. REPRODUCED, then fixed.**
  `LOCK` was `$ROOT/.artifacts/merge-rehearse.lock`, a different file in every worktree, while `$SCRATCH` is
  `$ROOT/../wt/_rehearsal` — the same directory for every worktree under `.worktrees/` — and `$BRANCH` is one
  branch in one shared `.git`. Reproduced with a probe built out of the script's own lock-acquisition and
  scratch-setup lines (`.artifacts/t99probe/mklockprobe.py`), resource names suffixed so the probe could not
  collide with a real rehearsal:

        PRE-FIX
        holder, from .worktrees/T-0099            LOCK=.worktrees/T-0099/.artifacts/...-t99probe.lock
        second run, SAME worktree                 REFUSED by the lock                REAL EXIT = 2  (control)
        second run, from .worktrees/_t99fixprobe  LOCK ACQUIRED, shared scratch deleted and recreated
                                                                                     REAL EXIT = 0
        the holder, still holding its own lock    my scratch worktree is GONE        REAL EXIT = 9

  That is the disaster the lock was written for, reproduced with the lock in place. The lock now lives beside
  the resource: `git rev-parse --git-common-dir`, resolved by ENTERING it (the only test that separates
  "usable" from "printable" — from WSL against a Windows checkout git prints a path no Linux shell can use,
  T-0055), and the script REFUSES rather than falling back to a private lock if that directory is unusable.
  One path from everywhere: `.worktrees/T-0099`, `.worktrees/_t99fixprobe` and the main checkout all resolve
  to `/c/.../scenic_drive/.git`. The lock file now also records the holder's worktree.

        POST-FIX
        holder, from .worktrees/T-0099            LOCK=/c/.../scenic_drive/.git/...-t99probe.lock
        second run, from .worktrees/_t99fixprobe  REHEARSAL REFUSED: another run holds ...
                                                    pid=209192 started=... worktree=.../T-0099
                                                                                     REAL EXIT = 2
        the holder                                my scratch worktree is still there REAL EXIT = 0

  **FINDING 3 — `NOT COVERED` subtracted two differently-scoped populations. REPRODUCED, then fixed.**
  `_norepo` counted ahead-of-main refs under `task/`; `want` was every open PR in ANY namespace. Running the
  block verbatim with `want` varied, against a true set difference computed independently:

        PRE-FIX   TRUE no-PR count (set difference) = 31
        want=35 (today)                                   NOT COVERED: 31    correct - by coincidence
        want=36 (one open PR outside task/; demo/T-0085-fp and demo/T-0085-real exist here)
                                                          NOT COVERED: 30    understated by one
        want=67 or 68 (PRs left open on branches no longer ahead of main)
                                                          *** the block prints NOTHING ***

  An absent `NOT COVERED` line reads as "everything is covered" — a guard with no floor, indistinguishable
  from a guard that looked at nothing. It is now a set difference by name against the PR head list (the way
  `merge-rehearse` already did it), it always prints, and it has a floor on the population it examined:

        POST-FIX (block lifted verbatim into a harness, `.artifacts/t99probe/mkf3.py`)
        GREEN  real ref pattern
               NOT COVERED: 31 of the 80 branch(es) under refs/remotes/origin/task/ are ahead of main
               with no open PR ...                                                   REAL EXIT = 0
        RED    ref query aimed at refs/remotes/origin/zzznope/*
               NOT COVERED: UNKNOWN - the branch query examined 0 ref(s) ...          REAL EXIT = 2

  **Also fixed, from the reviewer's smaller notes:** `$want` (from the sort) and `$n_all` (from the
  enumeration) were the two sides of a printed equation and nothing asserted they agree. They are asserted
  now, and a mismatch makes the run exit 1.

        GREEN  n_all=67 want=67   REHEARSAL (cumulative): 67 of 67 merged, ...        REAL EXIT = 0
        RED    n_all=67 want=66   MISCOUNT: the enumeration produced 67 branch(es) and the sort produced
                                  66. ...                                             REAL EXIT = 1

  **verify:** `bash ops/check-pins` -> `PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux`,
  real exit 0. `bash ops/test` -> **real exit 1**, `FAIL: services/api exists but vitest produced no report`
  — `services/api/node_modules` is absent in this worktree and this branch changes nothing under `services/`
  or `ops/test` (`git diff --name-only -- services/ ops/test` = 0 files). The reviewer recorded the same
  failure at d56732e before any of these changes existed. Environment, not this branch, and it is still red.
  Also `bash ops/sane` -> `SANE OK` exit 0, `bash ops/queue-check` -> `QUEUE OK (91 tasks)` exit 0,
  `bash -n` clean on both scripts.

  **Not done, deliberately:** a full `ops/merge-rehearse` run over all 67 branches. It takes the repo-global
  lock for a long time on a box where other agents are working, and the brief's last step (record the number
  in `queue/MERGE-ORDER.md`) targets a file that exists only on `task/T-0045` — not on main, not on this
  branch, and outside `touches:`. The enumeration and both guards were exercised against live refs and the
  live PR list by probe A above; the summary assertion by the lifted-block probe.

  **Still true and not fixed here:** `ops/merge-rehearse` is 659 lines against CLAUDE.md's 300-line cap.
  `ops/lib/check-line-cap` only scans `*.swift`, so nothing catches it; T-0059 is filed for the same class on
  `ops/lib/queue.py`. Splitting this script is a change to files outside `touches:` and is its own task.
  `ops/pr-ci-preflight`'s `gates()` still decides pass/fail by grepping failure wording rather than reading
  exit codes — pre-existing, named by the reviewer, and also its own task.

- 2026-09-08 — **second review (FAIL at 152a37f): reproduced both open findings, fixed both, and found one
  more attack of my own that survived the first version of the fix.** Reviewer `agent/reviewer-final-pr67`
  closed prior findings 2 and 3 and the `$want`/`$n_all` note. Prior finding 1 was still open, and the same
  hole was in the fix for finding 3. Both reproduced by running the code before changing anything.

  Method throughout: truncated copies of the real scripts generated from the file by
  `.artifacts/fix67c/mkprobe.py` (merge-rehearse, truncated after the `branches:` line so the guard's verdict
  is the only thing measured) and `.artifacts/fix67c/mkf3.py` (the `NOT COVERED` block of pr-ci-preflight
  lifted verbatim into a harness that supplies `PRS`/`want` the way the script does). Each probe differs from
  the unmodified copy by ONE line except where noted. Exit codes taken with no pipe in between. The ref and
  PR counts drift between runs — other agents push while this runs — so read the shapes, not the absolutes.

  **REPRODUCED, using the reviewer's own generator (`.artifacts/rvw67b/mkprobe.py`, `mkf3.py`) at 152a37f
  with nothing of mine applied:**

        merge-rehearse  A  unmodified              69 to rehearse = 38 with an open PR + 31 with none  EXIT 0
                        F  line 188 only, the ahead-of-main question unanswerable
                                                   38 to rehearse = 38 with an open PR + 0 with none   EXIT 0
                        G  lines 190-191 removed, the enumeration's output deleted
                             31 `no-PR branch:` lines printed, then
                                                   38 to rehearse = 38 with an open PR + 0 with none   EXIT 0
        pr-ci-preflight f3_green                   NOT COVERED: 31 of the 85 ...                       EXIT 0
                        f3_ahead_unanswerable      NOT COVERED: 0 of the 85 ...                        EXIT 0

  Both reviewers were right. `SEEN_REFS` was appended to at the TOP of the loop body, ahead of both
  `continue`s, so it recorded the loop's INPUT; the enumeration's OUTPUT is the `EDGES+=` append, and nothing
  was a floor on that. `_refs` in pr-ci-preflight counted refs WALKED while `_nopr` is the number in the
  sentence. Third and fourth versions of the same mistake, at successively shorter distances from the code.

  **The fix — the loop partitions its input, and "git could not answer" is one of the buckets.** Every ref
  the enumeration consumes lands in exactly one of `CLS_PR` / `CLS_ADD` / `CLS_BEHIND` / `CLS_UNKNOWN`, and
  the only way out of the run is a positive answer from a `git rev-list` that EXITED 0. `origin/main` is no
  longer written out literally with `|| echo 0` behind it: `$MAINREF` is resolved once, before anything is
  measured against it, and if neither `origin/main` nor `main` resolves the run refuses instead of answering
  "0 commits ahead" for every branch. (That resolution used to live 200 lines below the enumeration, which
  is the contradiction the reviewer pointed at: the script allowed for `origin/main` being absent in one
  place and assumed it in another.) Four checks then read the loop's decisions, not its input:

        UNKNOWN      any ref the ahead-of-main comparison could not answer for  -> refuse
        PARTITION    consumed == decided-about                                  -> refuse
        ANCESTRY     every ref dropped as "not ahead" must be contained in $MAINREF, asked the other way
                     round with `git merge-base --is-ancestor`                  -> refuse
        OUTPUT       every consumed ref must be in EDGE_HEADS (the EDGES array the sort and the merge loop
                     actually receive) or positively behind $MAINREF            -> refuse
        SPLIT        n_all (EDGES) == n_pr (GitHub) + n_extra (CLS_ADD)         -> refuse

  Being honest about what each one is worth: PARTITION is a structural regression guard, not a property —
  every path through the loop body adds one to exactly one bucket, so it can only fail when a future edit
  adds an exit that classifies nothing (probes G2/G3/H). ANCESTRY and OUTPUT are the ones that measure
  something the loop could get wrong: ANCESTRY asks a second, differently-implemented git question about
  the one answer that removes a branch from the run, and OUTPUT's expected side is the consumed refs minus
  the positively-excluded ones while its measured side is the EDGES array itself.

  OUTPUT is the one that closes finding 1: its expected side is `SEEN_REFS` minus the positively-excluded
  refs, and its measured side is the EDGES array itself, so nothing inside the append branch can make it
  green by being deleted.

  **RED, then GREEN — `ops/merge-rehearse`, eleven probes (`.artifacts/fix67c/out_*.txt`). Every one of the
  seven checks is red here for its OWN reason, not merely as part of an overall red — that distinction is
  what failed the last two rounds:**

        A   unmodified                          branches: 69 to rehearse = 38 + 31            REAL EXIT = 0
        B   ref query -> zzznope/*              REFUSED: enumeration consumed 0 ref(s)        REAL EXIT = 2
        D   `done < /dev/null`                  REFUSED: enumeration consumed 0 ref(s)        REAL EXIT = 2
        E   ref query -> task/T-00[0-3]*        REFUSED: consumed 28, 32 of GitHub's 38 open PR head(s)
                                                  were not among them                         REAL EXIT = 2
        F   ahead-of-main unanswerable          REFUSED: 47 of the 85 ref(s) consumed could not be
              (the probe that was GREEN before)   compared against origin/main                REAL EXIT = 2
        F2  the old `|| echo 0` swallow put back, so the failure becomes a valid 0 and the ref is dropped
            as "not ahead" — my own attack; it survived every check above and this is why ANCESTRY exists
                                                REFUSED: 31 of the 47 ref(s) dropped as 'not ahead of
                                                  origin/main' are not contained in origin/main either
                                                                                              REAL EXIT = 2
        G   `EDGES+=` removed, ONE line         REFUSED: 31 of the 85 ref(s) consumed are neither in the
              (the probe that was GREEN before)   branch list it produced nor positively behind origin/main
                                                                                              REAL EXIT = 2
        G2  whole add branch removed (append + bookkeeping), i.e. the pre-fix tool exactly
                                                REFUSED: consumed 85 ref(s) and decided about 54
                                                                                              REAL EXIT = 2
        G3  bookkeeping removed, append kept    REFUSED: consumed 85 and decided about 54      REAL EXIT = 2
        H   a bare `continue` added, so one ref leaves the loop with no decision
                                                REFUSED: consumed 85 and decided about 54      REAL EXIT = 2
        I   one branch that HAS an open PR is not recognised as one, so it is appended to EDGES a second
            time. `sort -u` hides the duplicate from n_all, the ref IS in EDGE_HEADS, the partition still
            sums and the ancestry bucket is untouched — every other check stays green and only the SPLIT
            equation can see it. Added because SPLIT had not yet been red for its own reason.
                                                REFUSED: the branch list holds 70 head(s), and the
                                                  enumeration accounts for 39 with an open PR + 32 without
                                                  = 71                                         REAL EXIT = 2
              (A re-run alongside I: 70 to rehearse = 39 with an open PR + 31 with none        REAL EXIT = 0)

  Which check each probe fires, so none of them is riding on another's red:
  `n_seen==0` <- B, D · `missing PR heads` <- E · `UNKNOWN` <- F · `PARTITION` <- G2, G3, H ·
  `ANCESTRY` <- F2 · `OUTPUT` <- G · `SPLIT` <- I.

  **RED, then GREEN — `ops/pr-ci-preflight`, the new finding:**

        f3_green   unmodified                   NOT COVERED: 31 of the 85 branch(es) ...      REAL EXIT = 0
        f3_empty   ref query -> zzznope/*       NOT COVERED: UNKNOWN - examined 0 ref(s)      REAL EXIT = 2
        f3_ahead_unanswerable                   NOT COVERED: UNKNOWN - 48 of the 86 branch(es) could not be
              (the probe that was GREEN before)   compared against origin/main                REAL EXIT = 2
        f3_old_echo0  the swallow put back      NOT COVERED: UNKNOWN - 32 ref(s) counted as 'not ahead of
                                                  origin/main' are not contained in origin/main either
                                                                                              REAL EXIT = 2
        f3_undecided  a bare `continue`         NOT COVERED: UNKNOWN - 86 walked, 55 decided  REAL EXIT = 2

  All four of that block's checks fire for their own reason: `_refs==0` <- f3_empty · `UNKNOWN` <-
  f3_ahead_unanswerable · `ANCESTRY` <- f3_old_echo0 · `PARTITION` <- f3_undecided.

  **verify:** `bash ops/check-pins` -> `PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux`, real
  exit 0. `bash ops/sane` -> `SANE OK`, real exit 0. `bash ops/queue-check` -> `QUEUE OK (91 tasks)`, real
  exit 0. `bash -n` clean on both scripts. `bash ops/test` -> **real exit 1**,
  `FAIL: services/api exists but vitest produced no report`. `services/api/node_modules` does not exist in
  this checkout and `git diff origin/main...HEAD --name-only` lists nothing under `services/` or `ops/test`.
  Both reviewers recorded the same failure, one of them before any of this branch's changes existed.
  Environment, not this branch, and still red.

  **Named and NOT fixed here, so the next reader does not have to find them again:**
  - `ops/merge-rehearse` is now **735 lines** against CLAUDE.md's 300-line cap (`ops/lib/check-line-cap`
    only scans `*.swift`, so nothing catches it). This branch is what took it past 300 and these checks add
    a further 19 net. Splitting it needs a new file under `ops/lib/`, which is outside `touches:`.
  - `ops/merge-rehearse:344` computes the derived ordering edges from
    `git diff --no-renames --name-status "origin/main...origin/$h" 2>/dev/null` and swallows a failure into
    an empty `$ns`, which yields no derived edges rather than an error — the same silent-swallow shape as
    the one closed above, in the ordering section rather than the enumeration. It is inside `touches:` but
    outside these findings, and I am not changing it without a red demonstration of its own.
  - `ops/pr-ci-preflight`'s `gates()` still decides pass/fail by grepping failure wording rather than
    reading exit codes. Pre-existing, named by both reviewers, its own task.
  - The brief's last step (record the real number in `queue/MERGE-ORDER.md`) is still not done: that file
    exists only on `task/T-0045` and is outside `touches:`.
  - A full `ops/merge-rehearse` run over all 70 branches was not made, and neither was a partial one carried
    through the topological sort. I started the latter (`.artifacts/fix67c/S_through_sort.sh`, truncated
    before the scratch worktree is created, printing `n_all` against the sort's `want`); after ~40 minutes
    it was still inside the derived-ordering-edge loop — 70 three-dot `git diff`s — holding the repo-global
    lock on a box other agents share, so I killed it, removed its lock file and confirmed no scratch
    worktree or `tmp/merge-rehearse` branch was left behind. **So I have not seen the enumeration's output
    reach the sort in a live run.** What I can say instead: `n_all` and `n_extra` are computed to the same
    values as before (`n_all` is the same `awk | sort -u` expression via `$EDGE_HEADS`; `n_extra` is the
    size of `CLS_ADD`, which is appended to on exactly the line that used to increment the counter), no
    variable read after the enumeration was removed, `set -u` is on and every probe above runs the real
    script through line 317 without an unbound-variable error. The `n_all` vs `want` assertion itself is
    unchanged on this branch and was verified red-then-green by the second reviewer at 152a37f.
    Incidentally, the lock did its job while all this was going on: probe I refused with
    `another run holds .git/merge-rehearse.lock ... worktree=.../T-0099` until the stuck run was cleared.

  Queue state untouched: I am the fixer, not the reviewer.
