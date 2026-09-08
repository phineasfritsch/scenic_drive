---
id: T-0063
title: ops/review must handle main's stale claimed copy, or every branch duplicates on merge
state: review
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T03:35:43Z
lease_expires_at: 2026-09-08T09:35:43Z
worktree: wt/T-0063
branch: task/T-0063
exclusive: []
touches: [ops/lib/queue.py, ops/lib/check-review-remedy, queue/README.md]
pins_affected: []
reviewer: agent/reviewer-pr52
depends_on: [T-0032]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**All thirty open branches duplicate their own task file on merge, and not one of them can see it.**

`main` says `queue/claimed/<id>`, the branch says `queue/review/<id>` or `queue/done/<id>`, and on merge BOTH
survive:

    QUEUE CHECK FAIL
     - duplicate id T-0039: queue/claimed/T-0039-...md and queue/ready/T-0039-...md

`ops/queue-check` passes on the branch. It passes on main. Only the merged result fails - so no per-branch CI
could ever have caught it, and it cascades: once one duplicate exists every later merge reports the same one,
which masks the rest.

**The cause is structural, not carelessness.** `ops/claim` moves `ready/ -> claimed/` on MAIN. Worktrees here
are created from OTHER task branches in order to stack them, and those bases predate the claim - so the branch
never contains `claimed/<id>` and has nothing to delete. Writing the review copy on the branch cannot remove a
file the branch does not have. Add-then-remove in one commit does not help either: git compares trees against
the merge base, and the base never had the file.

The manual fix, verified on `task/T-0052` and then applied across the idle branches: `git merge origin/main`
to bring `claimed/<id>` in, then `git rm` it, so the deletion is recorded against a base that has the file.

**Make it impossible to forget.** T-0032 added `queue.py review <id> --reviewer <name>` (wrapped as
`ops/review`) precisely so the claimed -> review transition has one home instead of being a habit. This
belongs there:

- `ops/review` should refuse, or fix, the case where the task also exists in another queue directory
  reachable from `origin/main`. Decide which - refusing is safer and teaches the rule; fixing silently is
  friendlier and risks hiding a genuine duplicate somebody created another way.
- Whatever it does, `ops/review` must leave the branch in a state where MERGING it does not produce a
  duplicate. That is the actual acceptance test, and it cannot be checked by running `queue-check` on the
  branch - it needs a rehearsal merge against main.
- The same applies to the review -> done transition a reviewer performs. There is no `ops/done` yet.
- Document the rule in `queue/README.md` next to the claim protocol, because until `ops/review` is merged
  every agent is doing this by hand.

**Demonstrate red properly.** On the branch, `queue-check` passes. Merge the branch into a throwaway copy of
main and show `queue-check` failing there; then run the fixed transition and show the same merge clean. A
demonstration that only runs `queue-check` on the branch proves nothing about this bug, which is the whole
point of it.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from a full merge rehearsal: thirty branches merged into a throwaway
  in dependency order with the gates run after each. The same rehearsal found an ADD/ADD conflict on
  ops/lib/gh-stub-for-merge-tests across T-0022/T-0044/T-0049, the exec-bits trap T-0041 predicted, and a
  436-line test file (T-0062) that no single branch could see.
- 2026-09-08T03:35:43Z claimed by agent/claude-opus-5; lease until 2026-09-08T09:35:43Z

- 2026-09-08 agent/claude-opus-5 — `ops/review` now refuses a branch that would duplicate on merge, and the
  first version of this guard DID NOT FIRE, which is the useful part of this entry.

  **RED**, reproduced in a throwaway git repo shaped exactly like the real failure — `main` claims
  `ready/ -> claimed/`, the branch is cut from a base that predates that claim, the branch writes the file at
  `claimed/` itself. Unpatched `ops/review`:

        T-9991 -> queue/review/T-9991-a-stacked-task.md  reviewer=agent/other      exit 0
        merged tree holds: queue/claimed/... queue/ready/... queue/review/...
        QUEUE CHECK FAIL - 2 tasks share one brief

  Three copies. `queue-check` passes on the branch, passes on main, fails only on the merge.

  **THE FIRST GUARD WAS WRONG AND I PROVED IT RATHER THAN SHIPPING IT.** It asked *"does the branch's working
  tree hold main's path?"* It does — the branch WROTE the file there — so the check found nothing stale and
  allowed the transition, producing the identical three-copy merge. The question was wrong, not the code:
  **the two copies share no history at that path**, so git keeps both regardless of what the working tree
  looks like.

  **The right question is about history**, and the brief said so all along: *"it needs a rehearsal merge
  against main."* A branch can delete a file only by recording a deletion against a base that HAS it, so:

        commit = git rev-list -1 <main> -- <path>
        git merge-base --is-ancestor $commit HEAD

  If the branch does not contain the commit that put the file at that path, it has no deletion to record and
  the merge re-adds main's copy every time. **GREEN:**

        T-9991: main holds this task where this branch cannot delete it:
            queue/claimed/T-9991-a-stacked-task.md
        This branch does not contain the commit that put the file there, so it has no deletion to record.
        ...
            git merge origin/main
            git rm queue/claimed/T-9991-a-stacked-task.md
        exit 1   — nothing moved

  **CONTROL, and it matters as much as the fix**, because a guard that only ever refuses is an outage rather
  than a repair. The branch does what the refusal says, then reviews:

        merged main; branch now holds: queue/claimed/T-9991-a-stacked-task.md
        T-9991 -> queue/review/T-9991-a-stacked-task.md   exit 0
        merged back into main cleanly
        copies of T-9991 in the merged tree: 1            CONTROL PASSES

  **Refused rather than silently repaired**, per the brief's own framing. `git merge origin/main` inside a
  state transition is a history-changing act hidden in a rename, and the same code would swallow a genuine
  duplicate created some other way. The refusal costs one run and teaches the rule once.

  Fails closed, consistently with [[T-0082]]: `_git` returns `ok=False` both for a failed command and for a
  git that cannot run, and `_would_duplicate_on_merge` returns `None` — "could not ask" — which the caller
  refuses on. From WSL against this Windows checkout that is a live state, not a hypothetical.

  `ops/lib/queue.py` is now **788 lines**, from 711. Fourth growth in one session while [[T-0059]] waits,
  blocked because six unmerged branches hold the file. That is no longer a footnote: the file has grown 90%
  past its exemption in a day, and every increment was a real defect that could not wait for a merge that has
  not come.

- 2026-09-08 agent/claude-opus-5 — **an independent reviewer of PR #52 returned FAIL with four findings. Three
  are code and are fixed here; the fourth is scope and is acknowledged.**

  **HIGH — the remediation this guard printed was destructive.** It printed `git rm <main's path>` without
  ever comparing main's path to the branch's own, and in the shape the docstring is written for they are the
  SAME file. Following the two printed commands verbatim deleted the branch's only copy of its task file,
  work log and all, after which the instructed re-run printed `T-9991 not found`, exit 1. **My control merged
  main and stopped — it never ran the second command I told people to run**, which is exactly why the trap
  survived my own testing. It now prints only

        git merge origin/main        # resolve the add/add on the task file, keeping YOUR copy

  and emits a `git rm` only for a path the branch does not hold, where the merge really would re-add it.
  After the merge the branch CONTAINS main's commit, so `ops/review`'s own `git mv` records a proper rename
  and nothing needs removing.

  **HIGH — it failed OPEN on a stale `origin/main`.** Nothing fetched and nothing warned, so a branch reviewed
  against a week-old ref was allowed and duplicated anyway. It does not fetch now either — a state transition
  that reaches the network is one people stop running, and `_ids_in_refs` shows what that costs — but it names
  the ref and commit its answer is about:

        (checked against refs/heads/main at bfd2b1e; run `git fetch origin` first if that is stale -
         this guard cannot see a claim pushed since)

  **MEDIUM — the query was wrong, and refused branches that were fine.** `git rev-list -1 <ref> -- <path>`
  returns the commit that LAST TOUCHED the path, not the one that created it. So a branch that genuinely
  contained the creating commit was refused the moment main appended a log line to that same file — which
  `ops/queue-sweep`, `ops/lock` and any hand edit do routinely — with a message stating something factually
  false. Now `git log --diff-filter=A --format=%H -1`. Probed:

        branch contains the creating commit; main last touched the file more recently
        -> T-9992 -> queue/review/T-9992-x.md  reviewer=agent/other        (allowed, correctly)

  **And a mistake inside the fix, caught by running the probe rather than trusting the command:** `git
  rev-list` does not accept `--diff-filter` at all. It exits with a usage message, which `_git` reports as
  "cannot answer", which this function turns into a refusal for **every** branch. The first version of this
  fix would have broken `ops/review` completely. `git log` takes the flag; `rev-list` does not.

  Control after all three: the legitimate flow still passes and the merge still yields exactly one copy.

  **MEDIUM, not fixed, acknowledged:** two of the brief's four bullets were not delivered and the PR body did
  not say so. `queue/README.md` is in this task's `touches:` and is untouched, and there is still no
  `ops/done` for the review -> done transition the brief names. Both are real omissions; recording them here
  rather than quietly leaving the brief looking satisfied.

- 2026-09-08 agent/claude-opus-5 — **this change had silently broken `ops/lib/check-lock-lifecycle`, and
  nothing reported it.** Found by the T-0087 fix agent, which noticed the check was already red while working
  nearby. Two of its three failures were mine and are fixed here.

        task/T-0032   LOCK LIFECYCLE OK     exit 0     <- where the check was written
        task/T-0063   LOCK LIFECYCLE FAIL   exit 1
        task/T-0087   LOCK LIFECYCLE FAIL   exit 1

  **The cause: three different facts collapsed into one.** `check-lock-lifecycle` copies `queue.py` into a
  `mktemp -d` and runs it there, so `ROOT` is not a git worktree at all. My guard treated that the same as
  "git cannot answer" and refused, which meant `ops/review` never reached the lock release:

        FAIL: review did not release the lock
        FAIL: review refused a task that holds no locks

  They are not the same fact and only one is a hazard:

        ROOT is not a git worktree          -> there will never be a merge. Nothing to protect.   ALLOW
        ROOT is a worktree, no main ref     -> no copy on main to duplicate against.              ALLOW
        ROOT is a worktree, git cannot read -> the answer is unknown.                             REFUSE

  The third is real on this checkout: from WSL a Windows worktree's `.git` names a path WSL's git cannot
  follow, so git fails on a tree that genuinely has a main. Keeping that refusal is the point of the guard;
  collapsing the first case into it was the defect. Both FAIL lines are gone, and the probe confirms the guard
  still refuses the branch it exists for.

  **The third failure is NOT mine and is a cross-task collision worth its own task.** `queue-check` now
  reports `only 1 task(s) visible, floor is 40` inside the fixture — [[T-0073]]'s `MIN_TASKS` floor, added in
  round two, against a throwaway tree with one task. `check-lock-lifecycle` came from [[T-0032]] and predates
  that floor, so it passes on `task/T-0032` and fails on every branch carrying both. Neither task is wrong on
  its own; together they are. Filed separately — `ops/lib/check-lock-lifecycle` is not in this task's
  `touches:` and reaching outside it to make a red check green would be the exact move this repo forbids.

  **And a gap in my own tooling, which this exposes:** `ops/merge-rehearse` (T-0065) runs `queue-check`,
  `check-exec-bits`, `check-line-cap` and a pin-id scan after each merge — it does **not** run
  `check-lock-lifecycle` or `check-brief-required`, so a collision of exactly this shape is invisible to the
  rehearsal that exists to find collisions. Recorded against T-0065.

- 2026-09-08 — **the reviewer of PR #52's second [medium]: two of the brief's four bullets were never
  delivered, and the PR body did not say so.**

  `queue/README.md` is in this task's `touches:` and the brief names it explicitly — *"Document the rule in
  `queue/README.md` next to the claim protocol, because until `ops/review` is merged every agent is doing
  this by hand"* — and the branch did not touch it:

        $ git diff origin/main...origin/task/T-0063 --name-status -- queue/README.md
        (no output)

  Now delivered: step 6 carries the stale-`claimed/`-copy rule, the merge-then-`ops/review` repair, and the
  explicit warning never to `git rm` a path this branch also holds (that was the destructive remedy the same
  reviewer found as finding 1). Written next to the claim protocol, as the brief asked.

  **`ops/done` is NOT delivered, and this says so rather than leaving it implied.** `grep -n "def cmd_" `
  shows no `cmd_done`; the `review/ -> done/` transition is still a hand `git mv`, with the same
  stale-copy exposure `ops/review` exists to close on the other transition. Filed as its own task
  (see `queue/backlog/`), because shipping it here would widen `touches:` past what this PR was reviewed
  against.

        $ ops/queue-check
        QUEUE OK (76 tasks)

- 2026-09-08 — **reviewed by `agent/reviewer-pr52` (PR #52): pass with findings.** Recorded here because the review
  itself lived only in a gitignored scratch directory, and because this task had an open PR while its own
  file still said `state: claimed` / `reviewer: null` — the exact blindness [[T-0094]] was filed for.

  The reviewer's own summary, verbatim:

  > The mechanism works and the author's red/green/control all reproduce independently: with the unpatched queue.py the transition succeeds and the merged tree carries two copies with `duplicate id T-9991` from queue-check; with the patch it exits 1 and nothing moves; repaired, it exits 0 and the merge yields exactly one copy. The 711 -> 788 line figure is exact, the fail-closed-on-broken-git claim holds, and applied to all 60 real origin/task/* branches the guard allows 58, refuses 1 true positive (T-0029), and does not refuse its own branch.\n\nIt still should not merge as written. The remediation it prints is destructive in the shape its own docstring is written for: main's path and the branch's path are the same file there, so `git rm <path>` deletes the branch's copy and its work log, and the instructed \"then run this again\" prints `T-9991 not found`, exit 1. The author's control merged main and stopped — it never ran the second printed command, which is why the trap was not seen. Two further defects: the guard reads whatever origin/main happens to be (nothing in ops/ fetches, and it never warns, unlike `_ids_in_refs()` twenty lines up) so it fails OPEN on a stale ref and lets the duplication through; and `rev-list -1` asks about the last commit to touch the path rather than the one that created it, which refuses a legitimate branch with a message that is false whenever main touched the task file after the branch's merge point. All four are measured, with the counterfactual run for each. Fixes are small — compare main's path against the branch's before printing `git rm`, fetch-or-warn before reading the ref, and test ancestry of the creating commit — but as shipped an agent following the tool's own instructions loses work it cannot recover from within the tool.

  **7 findings (2 high, 2 medium, 3 low), and 5 overclaims quoted back:**

  - `[high]` ops/lib/queue.py:661-663
  - `[high]` ops/lib/queue.py:568-573
  - `[medium]` ops/lib/queue.py:578
  - `[medium]` queue/README.md
  - `[low]` ops/lib/queue.py:562, ops/lib/queue.py:665
  - `[low]` ops/lib/queue.py:1
  - `[low]` ops/lib/queue.py:537-544

  Every `critical`, `high` and `medium` above is fixed on this branch, each with its own red-then-green
  transcript in the entries above this one. The `low` items are recorded rather than silently dropped;
  where one was substantive it was fixed and says so.

- 2026-09-08 agent/claude-opus-5 — **a second independent reviewer of PR #52 returned FAIL on two `[high]`
  findings. I reproduced both on the branch they were measured on before changing anything, and both are
  fixed here. Two `[low]` figures in the PR body were wrong; both are re-measured below.**

  **HIGH 1 — the printed remedy still destroyed the task file.** The previous round replaced `git rm` with
  `elsewhere = [m for m in dup if not (ROOT / m).exists()]`: does the branch hold main's path *right now*.
  That question is asked one merge too early. `git rm` runs AFTER the `git merge origin/main` printed on the
  line above it, and when main reached its path by a RENAME — what `ops/claim`, `ops/queue-sweep` and every
  hand `git mv` produce — the merge resolves the rename and the two paths collapse onto ONE file.

  Reproduced on `origin/task/T-0029`, the only branch in this repo where the guard actually fires, in a
  throwaway worktree under `.artifacts/`, with this branch's `queue.py` copied in:

        $ python ops/lib/queue.py review T-0029 --reviewer agent/reviewer-34
        T-0029: main holds this task where this branch cannot delete it:
            queue/blocked/T-0029-composite-scenic-score-rank-order-fixture-set-th.md
            git merge origin/main
            git rm queue/blocked/T-0029-composite-scenic-score-rank-order-fixture-set-th.md
        exit 1

        $ git merge origin/main                     MERGE_EXIT=0   (no conflict)
        $ git ls-files queue/ | grep T-0029
        queue/blocked/T-0029-...md                  <- the claimed/ copy is GONE; it is the same file
        $ git rm queue/blocked/T-0029-...md         RM_EXIT=0
        $ git ls-files queue/ | grep -c T-0029      0
        $ python ops/lib/queue.py review T-0029 --reviewer agent/reviewer-34
        T-0029 not found                            exit 1

  **HIGH 2 — and dropping the destructive line was not enough: the remedy was a dead end for its only live
  case.** Same worktree, merge only, nothing removed:

        $ git merge origin/main                     exit 0
        $ python ops/lib/queue.py review T-0029 --reviewer agent/reviewer-34
        T-0029 is in blocked/, not claimed/         exit 1
        $ bash ops/queue-check                      QUEUE OK (104 tasks)

  Main had re-stated T-0029 as `blocked/` (79dd0ff, blocked on T-0030) and main's content wins the merge, so
  no sequence of the printed commands reaches `review/`.

  **THE FIX: the remedy is now derived from a REHEARSED merge, never from the pre-merge working tree.**
  `_paths_after_merge` runs `git merge-tree --write-tree HEAD <main ref>` — which writes the merge result to
  the object store and touches neither the index nor the working tree, so the guard stays read-only — and
  lists the paths under `queue/` that carry the id in the tree the merge would ACTUALLY produce. Three
  shapes, three different truths, and only the merged tree separates them:

        merged tree holds 1 path, in claimed/   -> nothing to remove; merge and run this again
        merged tree holds 1 path, elsewhere     -> main re-stated the task. Say so. Print NO command:
                                                   ops/review takes claimed/ only, ops/claim takes ready/
                                                   only, and inventing a sequence that edits main's stated
                                                   state is the silent repair this guard refuses to make.
        merged tree holds 2+ paths              -> a genuine second copy survives; `git rm` the ones that
                                                   are not this branch's own path

  On `origin/task/T-0029` today, unchanged worktree, patched `queue.py`:

        exit 1, and the whole remedy is now:
            git merge origin/main        # resolve the task file, keeping YOUR copy
        The merge collapses both paths onto ONE file, queue/blocked/T-0029-...md,
        so there is nothing to `git rm` here - deleting it would delete your only copy.
        But main has re-stated T-0029 as blocked/, and that is a disagreement about the
        work, not about the merge: ... Settle it on main first ...

  No `git rm`. The rehearsal's prediction was checked against the real thing: `git merge-tree --write-tree`
  named `queue/blocked/T-0029-...md` and one path, which is exactly what `git merge origin/main` then
  produced.

  **THE FLOOR, on the population the rehearsal actually examines.** An empty result from the rehearsal is
  not "nothing to clean up" — this branch holds a copy (`cmd_review` is standing on it) and `dup` says main
  holds another, so the merged tree MUST carry at least one path for the id. Zero means the rehearsal
  examined nothing, and advice derived from an empty population is advice derived from nothing, which is
  how the destructive `git rm` came to be printed in the first place. Empty refuses and prints no command.

  **`git merge origin/main` was also hard-coded** while `_main_ref()` falls back to `refs/heads/main`, so in
  a checkout without an `origin` the first line of the remedy simply failed. It now names the ref it read.

  **NEW CHECK: `ops/lib/check-review-remedy`** — it RUNS every `git` line the refusal prints, verbatim and
  in order, and fails if the task file does not survive them. Nothing did that before, which is exactly why
  a remedy that deleted a task file passed two rounds of review. Four cases: `1/rename` (T-0029's shape),
  `2/stacked` (the control: refuse, follow the remedy, review succeeds, the merge leaves one copy),
  `3/second-copy` (a real duplicate, where `git rm` is right and must be printed), `4/empty` + `4/unreadable`
  (the floor). Fixtures are real git repos with a self-pointing `origin` remote, because a fixture where the
  printed remedy cannot RUN cannot show that running it destroys anything.

  **RED — the check against this branch's previous `queue.py` (93f1deb), `QUEUE_PY=` pointed at it:**

        FAIL: 1/rename: the printed remedy DESTROYED the task file (1 copy -> 0)
            ran:     git merge origin/main
            ran:     git rm queue/blocked/T-9201-rename-shape.md
        FAIL: 1/rename: the refusal did not name main's state; second run said: T-9201 not found
        ok: 2/stacked - refused, the remedy works, and the merge leaves exactly one copy
        ok: 3/second-copy - git rm printed for main's path only, and the remedy works
        FAIL: 4/empty: a git rm was printed from an empty rehearsal - guessed, not measured
        FAIL: 4/unreadable: a git rm was printed from an empty rehearsal - guessed, not measured
        REVIEW REMEDY FAIL                                                        exit 1

  **GREEN — the same check against the fixed `queue.py`:**

        ok: 1/rename - refused, no git rm printed, and the file survives the printed remedy (1 copy)
        ok: 1/rename - the refusal names main's blocked/ instead of printing a sequence that cannot work
        ok: 2/stacked - refused, the remedy works, and the merge leaves exactly one copy
        ok: 3/second-copy - git rm printed for main's path only, and the remedy works
        ok: 4/empty - an empty rehearsal refuses and prints no deletion
        ok: 4/unreadable - an empty rehearsal refuses and prints no deletion
        REVIEW REMEDY OK (4 cases)                                                exit 0

  **THE FLOOR SEEN RED ON ITS OWN.** One character of the fix removed — `if not after:` weakened to
  `if after is None:`, so it still handles "could not ask" but no longer handles "asked and got nothing",
  which is the vacuity bug in its pure form. Only the empty case fails, and it fails with visible nonsense:

        ok: 1/rename ...  ok: 2/stacked ...  ok: 3/second-copy ...
        FAIL: 4/empty: the refusal did not say the rehearsal came back empty:
              Then stop and look: after the merge T-9201 lives at , none of them the
        ok: 4/unreadable - an empty rehearsal refuses and prints no deletion
        REVIEW REMEDY FAIL                                                        exit 1

  Restored: `REVIEW REMEDY OK (4 cases)`, exit 0.

  **`touches:` WIDENED, deliberately, and said out loud.** `ops/lib/check-review-remedy` is a new path and
  the pre-commit hook would have rejected it, so `touches:` now reads
  `[ops/lib/queue.py, ops/lib/check-review-remedy, queue/README.md]`. The alternative was to ship a fix for a
  destructive remedy with no check that executes it, and that is what let this defect through twice.
  Committed executable (`git update-index --chmod=+x`) per CLAUDE.md; `check-exec-bits` covers it.

  **`queue/README.md`** now says path equality before a merge is not file identity after it, that
  `ops/review` rehearses the merge, and that main may have re-stated your task while you worked.

  **The two `[low]` figures, re-measured.**

        ops/lib/queue.py    fde9726 (base) 711    93f1deb 822    this commit 898
        the PR body said "711 -> 788"; 788 was true when that Log entry was written, not now.

        origin/task/* branches today: 80.  28 reach the guard at all (the other 52 return earlier, at
        `state != "claimed"`).  27 allowed, 1 refused: T-0029 - still the single live case, still the
        rename case.  The PR body's "60 branches ... allows 58, refuses 1" is stale.

  **`verify:` as run on this branch, after `rm -rf .build` (the previous reviewer showed a stale
  ModuleCache):**

        bash ops/check-pins        exit 0   PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
        bash ops/test              exit 1   Swift: "Test run with 16 tests in 3 suites passed", then
                                            "FAIL: services/api exists but vitest produced no report"
        bash ops/queue-check       exit 0   QUEUE OK (76 tasks)
        bash ops/lib/check-review-remedy   exit 0   REVIEW REMEDY OK (4 cases)
        bash ops/lib/check-exec-bits / check-line-cap / check-brief-required   exit 0

  **`ops/test` is red and I ran the counterfactual rather than calling it environmental.** From the MAIN
  checkout, not this worktree: `services/api/node_modules` is absent there too, and the identical step

        $ cd services/api && npx vitest run --reporter=json --outputFile=<elsewhere>/vitest-on-main.json
        npx exit=1 ; no report file written

  fails the same way. It is not attributable to this diff, which touches no TypeScript — but it is red, and
  it stays named here rather than being written off.

- 2026-09-08 agent/claude-opus-5 — **round 4 (`agent/reviewer-final-pr52`) returned FAIL on two `[medium]`
  findings, both inside `ops/lib/check-review-remedy` — the check this task added last round. Both are the
  repository's signature defect one level up: an assertion that is true whether or not the property it names
  holds. Both reproduced before anything changed; both fixed; each replacement assertion demonstrated red on
  its own, for its own reason, with every other assertion in the file still green.**

  **MEDIUM 1 — the only assertion in the repo that executes prior `[high]` #2 could not fail.**
  `ops/lib/check-review-remedy:126`:

        elif grep -q "blocked" "$out" && grep -q "not claimed/" "$out2"; then
          say "ok: 1/rename - the refusal names main's blocked/ instead of printing a sequence that cannot work"

  `$out` is the refusal, and the refusal lists main's path — `queue/blocked/T-9201-rename-shape.md` — five
  lines above the remedy, so `grep -q blocked` is satisfied by the fixture's own path string on **every**
  output the guard can produce. `$out2` is a second `review` run, which returns at `state != "claimed"`
  before the guard is reached at all, so it reports where the merge left the file and says nothing about
  what was printed. Neither operand looks at the sentence the case exists for.

  REPRODUCED, with a one-line mutant of this branch's `queue.py` — `after = [p.relative_to(ROOT).as_posix()]`,
  the rehearsal that never rehearses, which is precisely the shape round 3 was failed for. Rebuilding this
  check's own `1/rename` fixture (`.artifacts/t63fix2/probe-case1.sh`) and printing `$out` verbatim:

        | T-9201: main holds this task where this branch cannot delete it:
        |     queue/blocked/T-9201-rename-shape.md          <- satisfies grep -q "blocked"
        |     ...
        |     git merge origin/main        # resolve the task file, keeping YOUR copy
        | The merge collapses both paths onto ONE file, queue/claimed/T-9201-rename-shape.md,
        | so there is nothing to `git rm` here - deleting it would delete your only copy.
        | Then run this again. (T-0063; this repair was applied by hand to eleven branches.)

            grep -q blocked $out            -> 0   (satisfied — by the path listing, not by the guard)
            grep -q 'has re-stated' $out    -> 1   (the disagreement was never named)
            grep -qi 'run this again' $out  -> 0   (the impossible sequence WAS printed)
            grep -q 'not claimed/' $out2    -> 0   (satisfied — by the early return, four lines into cmd_review)

  Following it: `git merge origin/main` exit 0, then `T-9201 is in blocked/, not claimed/`. A dead end — and
  the check printed `ok: 1/rename - the refusal names main's blocked/ ...`. The run went red overall, but via
  `3/second-copy` and `4/empty`, which are about other shapes.

  **FIX.** Anchor on the disagreement sentence itself and on the ABSENCE of the re-run instruction:

        elif ! grep -q "has re-stated T-9201 as blocked/" "$out"; then   bad ...
        elif grep -qi "run this again" "$out"; then                      bad ...
        elif ! grep -q "not claimed/" "$out2"; then                      bad ...
        else say "ok: 1/rename - the refusal names main's re-stated blocked/ and prints no re-run that cannot work"

  **RED, each operand on its own.** `QUEUE_PY=<mutant> bash ops/lib/check-review-remedy`:

        mutant A — `after = [p.relative_to(ROOT).as_posix()]` (the rehearsal never rehearses)
        FAIL: 1/rename: the refusal never named main's re-stated blocked/; it ended: Then run this
              again. (T-0063; this repair was applied by hand to eleven branches.)          exit 1

        mutant D — one added line in the disagreement branch: print("Then run this again.")
        ok: 1/rename - refused, no git rm printed, and the file survives the printed remedy (1 copy)
        FAIL: 1/rename: the refusal said to run it again, and re-running cannot reach review/: Then run this again.
        ok: 2/stacked ...   ok: 3/second-copy ...   ok: 4/empty ...   ok: 4/unreadable ...
        REVIEW REMEDY FAIL                                                                  exit 1

  Mutant D is the isolated red: one line added to `queue.py`, everything else in the file green, and the
  only assertion that fires is the one being demonstrated. The old assertion passed both mutants.

  **MEDIUM 2 — the floor on this check's own population counted increments, not assertions.**
  `ops/lib/check-review-remedy:236-239`:

        if [[ $cases -ne 4 ]]; then
          bad "only $cases case(s) executed, expected 4 - a check that ran nothing still prints OK"

  Every assignment to `cases` is unconditional top-level straight-line code — `cases=0`, then four
  `cases=$((cases + 1))` — with no `set -e`, no `continue` and no early `exit` between them. Reaching the
  test at all makes `$cases` exactly 4, so the branch could never be taken. It counted case blocks ENTERED,
  not assertions EXECUTED.

  REPRODUCED. Case 4's loop header emptied to `for mode in ; do`, with `QUEUE_PY` pointed at the
  `if after is None:` regression that **only case 4 detects**:

        $ QUEUE_PY=<if-after-is-None mutant> bash <check with case 4's loop emptied>
        ok: 1/rename ...  ok: 1/rename ...  ok: 2/stacked ...  ok: 3/second-copy ...
        REVIEW REMEDY OK (4 cases)                                                          exit 0

  Zero of case 4's assertions ran, a live regression was present, and the check printed a green verdict and
  a case count it does not measure — its own `bad` string happening.

  **FIX.** `verdicts` is incremented inside `say()` and `bad()`, so it counts verdicts actually emitted —
  the population that decides the exit code — and the floor is asserted on that:

        VERDICTS_EXPECTED=6   # 1/rename x2, 2/stacked, 3/second-copy, 4/empty, 4/unreadable
        if [[ $verdicts -ne $VERDICTS_EXPECTED ]]; then
          bad "$verdicts assertion(s) reached a verdict, expected $VERDICTS_EXPECTED - ..."

  **RED — the identical scenario that printed OK above:**

        $ QUEUE_PY=<if-after-is-None mutant> bash <check with case 4's loop emptied>
        ok: 1/rename ...  ok: 1/rename ...  ok: 2/stacked ...  ok: 3/second-copy ...
        FAIL: 4 assertion(s) reached a verdict, expected 6 - a check that ran nothing still prints OK
        REVIEW REMEDY FAIL                                                                  exit 1

  And with the **unmutated** `queue.py`, same emptied loop — the floor is about population, not subject, so
  it fires there too: same four `ok:` lines, same `FAIL: 4 assertion(s) reached a verdict, expected 6`,
  exit 1. `cases` is kept only for the summary line and is documented in place as saying nothing more than
  "control reached the bottom".

  Control, so the floor is not masking a case that stopped working: the intact fixed check against the same
  `if after is None:` mutant still catches it where it should — `FAIL: 4/empty: the refusal did not say the
  rehearsal came back empty: Then stop and look: after the merge T-9201 lives at , none of them the`,
  six verdicts, exit 1.

  **GREEN — fixed check, unmutated `queue.py`:**

        ok: 1/rename - refused, no git rm printed, and the file survives the printed remedy (1 copy)
        ok: 1/rename - the refusal names main's re-stated blocked/ and prints no re-run that cannot work
        ok: 2/stacked - refused, the remedy works, and the merge leaves exactly one copy
        ok: 3/second-copy - git rm printed for main's path only, and the remedy works
        ok: 4/empty - an empty rehearsal refuses and prints no deletion
        ok: 4/unreadable - an empty rehearsal refuses and prints no deletion
        REVIEW REMEDY OK (4 cases, 6 assertions)                                            exit 0

  `queue.py` is not touched this round: both findings were about the check, and round 4 reproduced both
  `[high]` fixes closed on `origin/task/T-0029` independently. `touches:` is unchanged.

  **`verify:` as run on this branch at this commit:**

        bash ops/check-pins        exit 0   PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
        bash ops/test              exit 1   Swift "Test run with 16 tests in 3 suites passed", then
                                            "FAIL: services/api exists but vitest produced no report"
        bash ops/queue-check       exit 0   QUEUE OK (76 tasks)
        bash ops/lib/check-review-remedy    exit 0   REVIEW REMEDY OK (4 cases, 6 assertions)
        bash ops/lib/check-exec-bits        exit 0   27 files, 15 required present, all modes correct
        bash ops/lib/check-line-cap         exit 0   9 Swift files tracked, none over 300 lines
        bash ops/lib/check-brief-required   exit 0   BRIEF CHECK OK
        bash ops/lib/check-lock-lifecycle   exit 1   one failure, the pre-existing MIN_TASKS collision
                                                     (T-0091): "only 1 task(s) visible, floor is 40"

  `ops/test` is red and stays named: `services/api/node_modules` is absent in the **main** checkout as well
  as here (`ls -d services/api/node_modules` -> "No such file or directory" in both), so vitest writes no
  report either place. This diff is one bash file and touches no TypeScript, but the red is not written off.

  **Left open, not fixed here, and not filed from this branch.** Round 4 recorded that
  `ops/lib/check-review-remedy` is run by nothing — absent from `pins/PINS.yaml`, `ops/test`, `ops/sane` and
  `.github/workflows/linux-core.yml`. Pinning it needs `pins/PINS.yaml`, outside this task's `touches:`, and
  the highest id visible on this branch is T-0082 while `origin/main` is at T-0120, so `ops/new-task` here
  would mint an id main already uses — the duplicate-id collision this very task exists to prevent. It
  belongs to a task filed from `main`.
