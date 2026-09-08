---
id: T-0075
title: nothing checks the tree GitHub Actions actually tests, which for a stacked PR is not main
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:14:05Z
lease_expires_at: 2026-09-08T08:14:05Z
worktree: wt/T-0075
branch: task/T-0075
exclusive: []
touches: [ops/pr-ci-preflight]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**A `pull_request` run checks out `refs/pull/<n>/merge` — the PR's head merged into ITS BASE.** For a stacked
PR the base is another task branch, not `main`. Nothing in `ops/` looks at that tree, so a branch can be clean
against `main`, clean on its own, and still fail its own CI.

Measured. PR #32 is `task/T-0026 <- task/T-0025`:

    bash ops/queue-check on task/T-0026 alone          QUEUE OK (60 tasks)   exit 0
    bash ops/queue-check on main + task/T-0026         QUEUE OK (67 tasks)   exit 0
    bash ops/queue-check on refs/pull/32/merge         QUEUE CHECK FAIL      exit 1
      duplicate id T-0051: queue/claimed/... and queue/ready/...
      duplicate id T-0026: queue/done/...   and queue/claimed/...

and the real CI run agreed — `core` failed on `check-pins`, P-PROC-01, whose assertion is
`bash ops/queue-check >/dev/null`. A scratch pass over all 31 open PRs found **three** failing this way that
every other check called clean.

`ops/merge-rehearse` (T-0065) does not cover this and should not: it answers two different questions
(cumulative — do the branches collide with each other; `--pairwise` — does this branch break `main` alone).
Neither is the question CI asks. Hence a separate tool, per the one-type-per-file rule.

- `ops/pr-ci-preflight` — for every open PR, fetch `refs/pull/<n>/merge` and run the gates on it. Report per
  PR. Exit non-zero if any fails.
- **Do not trust GitHub's `mergeable` field.** Four PRs reported `mergeable=CONFLICTING` / `DIRTY` while
  `git merge` and `git merge-tree --write-tree` both produced a clean tree; GitHub's value was stale and only
  refreshed after a new commit on the head. So when the merge ref is missing, verify locally with
  `git merge-tree --write-tree "origin/<base>" "origin/<head>"` and report the difference between what GitHub
  claims and what git computes. A tool that reads a stale field and prints it as fact is the same defect as
  everything else in this queue.
- The gate to run first is `ops/queue-check`, because it is what caught all three, but the others belong too:
  `check-exec-bits`, `check-line-cap`, duplicate pin ids.
- Anchor on `refs/pull/<n>/merge` and the workflow's `on: pull_request` trigger, never on a comment.
- P-OPS-01 requires committed scripts to be 100755: `git update-index --chmod=+x ops/pr-ci-preflight`.
  `core.filemode` is false on this checkout, so git will not notice on its own.
- Red demonstration: the three PRs above, before they were repaired, are reachable from the reflog and from
  the branches' parent commits. If reconstructing them is impractical, construct the state synthetically —
  two task files for one id at two paths across a head and its base — and show the tool red, then green.

**Worth stating in the log rather than only fixing:** this is the third distinct "the thing we check is not
the thing that runs" finding in this repo — after `ops/check-pins` skipping every pin and reporting success,
and `ops/merge-rehearse` reporting a clean rehearsal having merged one branch of thirty-one.

## Log
- 2026-09-08 filed by agent/claude-opus-5 after a scratch pass over all 31 open PRs found three failing on
  the tree CI tests while passing every local check. The scratch script is at
  `.artifacts/check-pr-merges.sh` (gitignored) and is a starting point, not the deliverable.
- 2026-09-08T02:14:05Z claimed by agent/claude-opus-5; lease until 2026-09-08T08:14:05Z

- 2026-09-08 agent/claude-opus-5 — `ops/pr-ci-preflight` built. 163 lines, committed 100755.

  **The premise turned out to be stronger than the brief claimed, and the difference changes the design.**
  The brief said to fetch `refs/pull/<n>/merge` rather than reconstruct it. Reconstructing it does not merely
  risk being different — it *is* different, measured on PR #32's own merge commit `777a2ae`, whose parents are
  exactly `fc068e6` (base) and `d023009` (head):

        GitHub's refs/pull/32/merge kept FOUR paths      git's merge of the SAME two parents kept TWO
          queue/claimed/T-0026-...                         queue/claimed/T-0051-...
          queue/claimed/T-0051-...                         queue/done/T-0026-...
          queue/done/T-0026-...
          queue/ready/T-0051-...

  Local git resolved the `ready/ -> claimed/` and `claimed/ -> done/` moves by rename detection. GitHub's
  merge kept both sides and produced the duplicate. **Same parents, different trees.** So the control matters
  as much as the demonstration:

        RED    ops/pr-ci-preflight --tree 777a2ae
               777a2ae  GATES FAIL | queue-check: - duplicate id T-0026: queue/done/... and queue/claimed/...
               exit 1

        CONTROL  the same two parents merged locally with `git merge`
               QUEUE OK (60 tasks)

  A tool that reconstructs the merge would have passed PR #32 while its `core` job was failing on exactly
  that tree. That is why this fetches the ref instead, and the comment block at the top of the file records
  it so nobody "simplifies" the fetch away later.

  **GREEN, across the whole open backlog:**

        PR-CI PREFLIGHT: 29 ok, 2 failing gates, 0 genuinely conflicting, 0 stale on GitHub (of 31 open PRs)

        #41  task/T-0049  <- task/T-0044  GATES FAIL | exec-bits: P-OPS-01: wrong git file mode:
                                            ops/lib/merge_reason_cap_assert.py (script, should be 100755, is 100644)
        #17  task/T-0021  <- main         GATES FAIL | exec-bits: P-OPS-01: wrong git file mode:
                                            ops/lib/classify-checks.py (script, should be 100755, is 100644)

  **Those two are the tool working, not the tool failing.** They are the only two open PRs whose real CI is
  red, and they are red in CI for precisely these two lines — confirmed against the actual run logs. Both are
  the T-0036 ordering constraint (T-0036 reclassifies `ops/lib/*.py` as data; these two add such a file), and
  both go green once T-0036 merges. So the tool reproduces CI's verdict locally, in about a minute, without
  waiting for a run.

  **Three deliberate choices worth arguing with in review:**

  1. `ops/test` is NOT run. It needs `npm ci` and a swift toolchain and takes minutes; CI's `core` runs it
     anyway. This catches the half that is cheap AND that per-branch checking cannot see, which is the half
     that was actually going wrong.
  2. A missing merge ref is never reported as "conflicting" on GitHub's word alone. Four PRs here claimed
     `mergeable=CONFLICTING` while `git merge-tree --write-tree` produced a clean tree, and the value only
     refreshed after a new commit landed on the head. The tool cross-checks and says which of the two said
     what — `NO MERGE REF, but git merges it cleanly - GitHub is stale, push to refresh` versus
     `CONFLICTS (git agrees)`. Reading a stale field and printing it as fact is the defect this queue is full
     of.
  3. It asserts its own completeness: if the PR list has more entries than were accounted for, it exits 2
     with `INCOMPLETE` rather than reporting a clean run. Same guard, same reason, as the one
     `ops/merge-rehearse` grew after reporting "0 conflicts" having merged one branch of thirty-one.

  `git-bash` note: `gh`'s stdout carries CRLF, so the PR list is stripped of `\r` before any `rev-parse`. That
  is the bug that made `ops/merge-rehearse` silently skip thirty of thirty-one branches; it is not repeated
  here.

  Handing to review. The reviewer should run `--tree 777a2ae` themselves — the commit survives in the local
  object store even though GitHub has since recomputed the ref — and should re-run the whole pass rather than
  reading these numbers.

- 2026-09-08 — **the agent working this PR's critical hit the session limit mid-task; its work was preserved
  and then verified against the reviewer's own attacks.**

  216 insertions sat uncommitted in the worktree when the agent stopped. That is the [[T-0103]] failure mode
  seen from the other side, and the reason this entry exists at all. Committed as `wip` first, verified
  second.

  **The change is the right one.** `gates()` now takes each check's **exit status** as the verdict instead
  of grepping its wording:

        out="$(bash "$f" 2>&1)"; rc=$?     # a command substitution, not a pipeline: $? is this command's
        [[ $rc -eq 0 ]] || bad="$bad | ${f##*/} exit $rc: $(digest "$out")"

  That is the critical the review found and the rule [[T-0104]] states.

  **ATTACK_E — `ops/deploy` deleted** (the reviewer's construction, rebuilt with `git read-tree` /
  `update-index --force-remove` / `write-tree` / `commit-tree`):

        the check itself   bash ops/lib/check-exec-bits      exit 1
        pr-ci-preflight    --tree 0bce772                    exit 1

  The review recorded `gates clean, exit 0` for this tree.

  **ATTACK_B — the truncated .swift set, and the first construction of it was wrong.** Taking the first five
  `.swift` paths in tree order removed `Package.swift` and four under `Sources/`, leaving five under
  `Sources/`+`Tests/` — the floor is five, so `check-line-cap` exited **0** and the tree proved nothing.
  Recorded because a red whose precondition did not reproduce is not evidence, and reporting the preflight
  exit alone would have looked like one.

  Rebuilt against paths matching `^(Sources|Tests)/.*\.swift$`:

        the check itself   P-SRC-02: only 3 tracked .swift file(s) under Sources/ and Tests/ (expected >= 5).
                             An empty or truncated set must never read as 'no file exceeds 300 lines'.
                           exit 1
        pr-ci-preflight    a595e93  GATES FAIL | check-pins exit 1: ... P-SRC-02 ... only 3 tracked
                           .swift file(s) ...
                           exit 1

  **This is the strongest of the four**, because that guard's message — *"only N tracked .swift file(s)"* —
  is not one of the two strings the old regex looked for, so the old tool could not have seen it even in
  principle. It is now reported through the exit status, and the message appears only in the summary the
  operator reads.

  **Control** — the base tree, unmodified: `exit 0`.

  **Still open, and not to be mistaken for done:** the remaining highs and mediums of the PR #48 review are
  untouched, no task-log transcript was written by the agent that made the change, and ATTACK_A (`import
  SwiftUI` added to `Sources/`) and ATTACK_D (a path git cannot check out on Windows) have not been re-run.
  Two of four attacks verified is what this entry claims and no more.
