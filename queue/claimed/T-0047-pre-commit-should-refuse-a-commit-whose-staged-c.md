---
id: T-0047
title: pre-commit should refuse a commit whose staged content is stale relative to the working tree
state: claimed
owner: agent/builder-8
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:57:35Z
lease_expires_at: 2026-09-07T19:57:35Z
worktree: ../wt/T-0047
branch: task/T-0047
exclusive: []
touches: [.githooks/pre-commit]
pins_affected: []
reviewer: agent/reviewer-28
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Six agents in one session have shipped a commit whose staged content was stale relative to the working tree,
every one of them the same shape:

    git mv queue/review/T-XXXX-....md queue/done/T-XXXX-....md   # stages the rename against the PRE-edit blob
    # ... edit the file: state: done, append findings ...
    git add <one path>                                            # a second path in the same command was wrong,
                                                                  # or the edit came after the mv and was never staged
    git commit                                                    # lands a pure rename, 0 insertions

`git status` shows a clean rename and says nothing is wrong. The reviewer's verdict, their `state: done`, and
their entire findings log are simply absent from the commit. Two agents caught it only because the task
instructions told them to run `git show HEAD:<path>` afterwards; the rest caught it by luck or not at all
(agent/reviewer-18's first PASS commit `43565bb` had to be repaired by `b2b79f3`; agent/reviewer-22's
`290a99a` by `54268e8`; agent/reviewer-20's by `7ece47a`).

An instruction that has to be repeated in every prompt is not a guard. This is mechanical and belongs in the
hook.

- In `.githooks/pre-commit`, for every path that is staged, compare the staged blob to the working-tree file.
  If they differ, the commit is about to record something other than what the author is looking at: refuse,
  name the paths, and say `git add <path>` fixes it.
- Consider whether this should be a refusal or a warning. Argue it in the log. A refusal is right if the
  legitimate cases are rare; the obvious legitimate case is a deliberate partial stage (`git add -p`), so say
  how someone does that on purpose - an env var like `ALLOW_PARTIAL_STAGE=1`, or exempting a path the author
  names.
- Demonstrate red: reproduce the exact `git mv` + edit + commit sequence and show the hook accepts it today,
  then refuses after the fix. Then show a deliberate partial stage still works by whatever route you chose.
- Check the interaction with the existing `touches:` and CRLF checks - both read `git show ":$f"`, i.e. the
  staged blob, which is correct and should stay that way.

Related: T-0039 fixes a different hole in the same hook (the `touches:` block being skipped for tasks in
`queue/done/`). Land that first if both are open; they touch the same file.

## Log
- 2026-09-07T16:57:35Z claimed by agent/builder-8; lease until 2026-09-07T19:57:35Z
- 2026-09-18T19:06:42Z **review FAIL** by `agent/rv-t0047` (reviewer != owner `agent/builder-8`), measured in a
  throwaway worktree detached at `origin/main` = `4d6698a`, hook read at that commit.

  **BLOCKING - nothing this task built is on `main`, and the bug it exists to stop is still live there.**
  `git merge-base --is-ancestor a137685 origin/main` -> NO; likewise `41f59ee` (the reviewer-28 symlink fix)
  and `24a46ec` (the PR #30 merge). `gh pr view 30 --json baseRefName` -> `task/T-0039`: PR #30 was merged on
  2026-09-08T11:24:30Z into the *stacked branch* `task/T-0039`, and `task/T-0039` had already landed on main
  the day before as `186d612`, so the child never followed. `git log --follow -- .githooks/pre-commit` on main
  lists 878ad07, b3218b6, 186d612, c78b90a, 0182f64, 7db9428, 8ce22c5, 4be058c, c986b2a, 6d0024f - and no
  T-0047 commit. `grep -rn ALLOW_PARTIAL_STAGE` over the whole tree at this head hits exactly one line: this
  task's own Brief. There is no check 4, no `-z` enumeration, no escape hatch, no pin. None of the task's
  original lines survive, because none of them ever arrived.

  **Driven red by name, in throwaway repos with `core.hooksPath` pointed at this head's hook.**
  - ATTACK 1, the Brief's own sequence (`git mv queue/review/X queue/done/X`, edit the file, `git commit`
    without re-adding): **rc=0**, the hook printed nothing, the commit landed as `1 file changed,
    0 insertions(+), 0 deletions(-) rename queue/{review => done}/T-9990-x.md (100%)`, and
    `git show HEAD:queue/done/T-9990-x.md` still reads `state: review` with the verdict line absent;
    `git status --short` afterwards ` M queue/done/T-9990-x.md`. The exact commit this task exists to make
    impossible, reproduced today.
  - ATTACK 2, staged then deleted from disk (PR #30 says this is "flagged distinctly"): **rc=0**, nothing
    printed, `git show HEAD:newfile.txt` returns content for a path `ls` reports as missing.
  - ATTACK 3, unstaged widening of `touches:` - the same staged-vs-working-tree family, and *not* covered by
    the reverted check either, since check 4 iterated staged paths only. With `touches: [ops/allowed.txt]`
    committed, staging `services/api/index.ts` is refused: `pre-commit: services/api/index.ts is outside
    T-9991 touches: [ops/allowed.txt ]`, rc=1 - the control proves the gate is alive. Now edit the
    *working-tree* task file to `touches: [ops/allowed.txt, services/]` and never stage it: the same commit
    is **rc=0**, while `git show HEAD:queue/claimed/T-9991-x.md` still records `touches: [ops/allowed.txt]`.
    The list that is enforced and the list that is recorded can differ. Worth its own task.
  - ATTACK 4 (bounded extra), non-ASCII staged path: `git diff --cached --name-only` prints
    `"caf\303\251-note.txt"` and the commit is **refused** - `pre-commit: cannot read the staged blob for
    "caf\303\251-note.txt", so it cannot be scanned; refusing rather than assuming` (T-0140's fail-closed
    branch). Closed, not open - but a legitimate commit is refused, and the `-z` enumeration this task wrote
    was the fix for it.
  - ATTACK 5 (bounded extra): `git commit --allow-empty` rc=0 and a pure rename rc=0. Correct, no false
    positive.

  **RECORDABLE.** (a) Systemic, not specific to this task: `4314bd4` (T-0048), `2f5d64d` (T-0051), `3854128`
  and `732cebe` are all absent from main by the same `--is-ancestor` test, and T-0048/T-0051 still sit in
  `queue/claimed/` - one stack of hook work, four commits, one survivor (T-0039). (b) `bash ops/queue-check`
  at this head prints `QUEUE OK (152 tasks)` while this file sits in `queue/claimed/` with
  `lease_expires_at: 2026-09-07T19:57:35Z`, eleven days expired and its PR merged into another branch: no gate
  in the set would ever have surfaced the loss. (c) PR #30's counts are stale (`QUEUE OK (43 tasks)`,
  `TESTS linux=50/50`) - expected, not blocking. (d) The work itself, on `origin/task/T-0047` (tip `05172d0`,
  file `queue/done/T-0047-...md`), reads as careful - object-id compare so `.gitattributes` normalization does
  not false-positive, symlink branch, path-scoped waiver, its own disclosed LOW symlink-newline gap - and is
  worth re-landing, but **not as a cherry-pick**: `.githooks/pre-commit` has been rewritten since by
  T-0137/T-0139/T-0140 (single temp-file blob scan that fails closed, merge-aware `touches:` with
  `--no-renames`), so check 4 and the `-z` enumeration must be re-applied on top of the current loop and
  demonstrated red again.

  **Not done:** `ops/check-pins` produced no output in ~9 minutes in the review worktree (it starts a Swift
  build under `.build/`) and was stopped, so PR #30's `PINS ok=9 ...` line was not re-run; `ops/test` was not
  run (needs `npm ci` in services/api). Neither could change the verdict - the subject code is not on main.
  Also for whoever reads this next: the shared checkout's `origin/main` ref moved from `4d6698a` to `0467cd7`
  mid-review (`--is-ancestor 0467cd7 4d6698a` -> NO, a divergent line); the hook at `0467cd7` has no
  stale-content check either (`grep -c` -> 0), so the finding is head-independent. Review worktree removed,
  scratch repos deleted, `git status --short` empty.
