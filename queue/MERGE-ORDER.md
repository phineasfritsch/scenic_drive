# Merge order for the open PR backlog

GitHub Actions stopped executing at about 15:11 UTC on 2026-09-07 — a run reports *"recent account payments
have failed or your spending limit needs to be increased"* — so every job on every branch, including `main`,
completes in 3–6 seconds with zero steps and no downloadable log. `ops/merge` correctly refuses to merge a PR
whose checks are not green, so nothing has merged since. Twelve PRs accumulated behind that, four of them
stacked on each other.

This file is the order to merge them in when Actions runs again, and why. It is not a suggestion about
priority — it is about which diffs would silently lose each other if merged in the wrong order.

**Nothing here bypasses a gate.** Every merge still goes through `ops/merge <n> --wait`, which requires the
task in `queue/done/` on the PR head and every check SUCCESS. If a PR does not go green after its base lands,
that is a real finding, not an excuse to force it.

## The dependency facts

Branch-to-branch file overlaps outside `queue/` (`git diff --name-only origin/main...origin/task/X`):

| File | Branches that change it |
|---|---|
| `ops/merge` | T-0021, T-0022, T-0044 |
| `ops/lib/gh-stub-for-merge-tests` | T-0021, T-0022 (both ADD it; it is not on `main`) |
| `ops/lib/check-line-cap` | T-0035, T-0037 |
| `ops/lib/junit_count.py` | T-0023 (content), T-0036 (mode only), T-0042 (content) |
| `ops/lib/check-failure-naming` | T-0023 (adds), T-0042 (extends) |
| `pins/PINS.yaml` | T-0014 (P-COST-02), T-0023 (P-OPS-02) |
| `services/etl/**` | T-0023, T-0038, T-0024 |
| `.githooks/pre-commit` | T-0039 only |
| `services/api/**` | T-0014 only |
| `ops/lib/check-exec-bits` | T-0036 only |
| `ops/sane`, `ops/etl-extract` | T-0024 only |

Stacked PRs (base is another task branch, not `main`): #20 T-0037→T-0035, #23 T-0038→T-0023,
#25 T-0044→T-0022, #26 T-0024→T-0038, #27 T-0042→T-0023. GitHub retargets a stacked PR to `main`
automatically when its base branch merges and is deleted; check that it did rather than assuming.

## The one real conflict

`ops/lib/gh-stub-for-merge-tests` is ADDed by both T-0021 and T-0022, so whichever merges second conflicts on
that path. agent/reviewer-20 resolved this in advance with `git merge-tree --write-tree` and reported:

- `ops/merge` itself merges **cleanly** — T-0021 changes gate 2 (polling), T-0022 changes gate 1 (the review
  gate). Different hunks.
- The stub conflicts ADD/ADD, and **T-0022's copy is a strict superset**: its `STUB_FLIP` block is
  byte-identical to the version accepted on T-0021 after two prior reviewers rejected wrong ones, plus two new
  knobs (`STUB_HEAD_REF`, `STUB_DONE_NAMES`).

**Resolution: take T-0022's copy.** Verify that byte-identity again at merge time rather than trusting this
paragraph — `diff <(git show origin/task/T-0021:ops/lib/gh-stub-for-merge-tests) <(git show
origin/task/T-0022:ops/lib/gh-stub-for-merge-tests)` — because a fix landing on either branch between now and
then invalidates it. That file has a history of being "fixed" into testing something narrower than it claims.

## The order

Independent of everything else; merge in any order, first:

1. **#24 T-0039** — `.githooks/pre-commit` only. Merge this FIRST for its own sake: until it lands, every PR
   below is in the window it fixes, where a branch whose task sits in `queue/done/` can commit any path with
   the hook exiting 0.
2. **#18 T-0014** — `services/api/**` plus one pin. Only `pins/PINS.yaml` overlaps anything, and it edits
   P-COST-02 while T-0023 edits P-OPS-02; different blocks of the file.
3. **#19 T-0035** → then **#20 T-0037** (retarget to `main`). Same file, correct order already enforced by the
   stack: T-0037 contains T-0035's `awk` fix as an ancestor.

The `ops/merge` chain, in this order:

4. **#17 T-0021** — brings `ops/lib/classify-checks.py` and the accepted stub.
5. **#22 T-0022** — conflicts on the stub; resolve in T-0022's favour per above. `ops/merge` itself
   auto-merges.
6. **#25 T-0044** (retarget to `main`) — sanitises the `--no-task-reason` audit line that T-0022 introduced.

Then:

7. **#21 T-0036** — `ops/lib/check-exec-bits` plus the mode flip on four `ops/lib/*.py` files.
   agent/reviewer-19 performed the T-0036 + T-0023 merge in a scratch worktree: clean, with
   `junit_count.py` ending up with T-0023's content AND T-0036's 100644 mode. After this lands, **T-0041**
   becomes actionable — it adds `classify-checks.py`, `gh-stub-for-merge-tests` and `check-failure-naming` to
   `REQUIRED`, which is only possible once steps 4–5 and 8 have put those files on `main`.

The ETL chain, in this order:

8. **#14 T-0023** — the ETL skeleton, `ops/test`'s failure naming, pin P-OPS-02, the CI artifact fix.
9. **#27 T-0042** and **#23 T-0038** (both retarget to `main`) — order between these two does not matter.
   Both branch from T-0023 and their own changes are disjoint: T-0042 touches `junit_count.py` and
   `check-failure-naming`; T-0038 touches `Dockerfile`, `test_dockerfile.py` and `test_manifest.py`.
10. **#26 T-0024** (retarget to `main`) — must come after T-0038, whose pinned image every osmium call in it
    runs inside.

## After the last merge

- Run `bash ops/sane` and `bash ops/check-pins` on `main`, not just on the branches. Several pins gained real
  assertions in this batch (P-COST-02, P-OPS-02) and one gained a first user of exit code 4 (`ops/sane`
  region bounds).
- `pins/floor_linux.txt` is raised by the ETL chain. Confirm the floor on `main` matches what `ops/test`
  actually reports there, and that it was raised rather than lowered.
- Re-check the follow-up tasks that were blocked on these merges: T-0041 (REQUIRED list), T-0046 (the pip
  check's scope boundary).
- **Close T-0034, which is about to come back from the dead.** Commit `69139c1` is titled "close T-0034 as
  superseded by T-0021" and its diff touches exactly one file: T-0035's. The close never happened. T-0034 is
  still in `queue/ready/` on `task/T-0023`, so merging that branch ADDS it back to `main` — a task the fleet
  was told is dead, returned to the ready pool. After step 8, delete it and say why in the commit.
- **The PR count is larger than this list.** These twelve were open when the order was derived; T-0045, T-0046,
  T-0047, T-0024, T-0025 and others have opened since. Before merging anything, re-run the two commands at the
  top of this file against the CURRENT branch set rather than trusting the table — the same instruction this
  file gives about the stub conflict, for the same reason.

## What this file taught, which is worth more than the order

Four separate task files (T-0032, T-0033, T-0038, T-0039) were filed on `task/T-0023` and were therefore
unreachable from `main` and unclaimable for as long as that branch was blocked. A follow-up that only exists
on a branch nobody can merge is not in the queue; it is a note. File follow-ups on `main` directly, or land a
byte-identical copy there the same day.

---

# Revision, 2026-09-08: rehearsed rather than reasoned

Everything above was derived from file overlaps. It covered twelve PRs. There are now **twenty-nine**, and
the order has been checked by actually doing it: all thirty branches merged into a throwaway in dependency
order, with `queue-check`, `check-exec-bits`, `check-line-cap` and a duplicate-pin-id scan run after each
merge. Result: **27 merged, 3 conflicts, 25 gate failures.**

That rehearsal is the only thing that can see this class of problem. Every branch passes its own gates; the
failures exist only in the merged tree, so no per-branch CI could ever report them.

## 1. The conflict that is still real

    ops/lib/gh-stub-for-merge-tests    ADD/ADD across task/T-0022, task/T-0044, task/T-0049

Predicted by agent/reviewer-20 and confirmed. The three branches each add the same path with different
content. Whoever merges the second of them resolves it by hand, and must check that the resolved stub still
satisfies BOTH callers - `ops/lib/check-merge-reason-cap` (T-0049's pin) and T-0022's merge-gate
demonstrations - rather than whichever one they happened to be looking at.

## 2. The duplicate every branch had, and none could see

`main` said `queue/claimed/<id>`; each branch said `queue/review/<id>` or `queue/done/<id>`. On merge both
survived and `queue-check` failed on the merged result while passing on the branch and on main separately.
**All thirty branches had it.**

Structural, not carelessness: `ops/claim` moves `ready -> claimed` on MAIN, but worktrees here are created
from other task branches in order to stack them, and those bases predate the claim - so the branch never
contains `claimed/<id>` and has nothing to delete. Add-then-remove in one commit does not help either,
because git compares trees against the merge base and the base never had the file.

Fixed on twenty-five branches by merging `origin/main` into each - which brings the file in - and then
deleting it, so the deletion is recorded against a base that has it. Two refinements the first pass missed:

- A **stacked** branch carries its ancestors' task files too, so it duplicates all of them, not just its own.
  `task/T-0032` failed on T-0056, `task/T-0040` on T-0039, `task/T-0048` on T-0051.
- Where the task file was moved with `git mv`, rename detection resolves the merge correctly and there is
  nothing to fix. Only the copies created by writing a new file are affected.

**Still outstanding** - the five worktrees that had agents writing in them when this ran, and which must get
the same treatment before their PRs merge:

    task/T-0025   task/T-0027   task/T-0028   task/T-0030   task/T-0049

`ops/review` should make this impossible to forget; filed as **T-0063**.

## 3. Two tasks that exist on no branch but their own

    T-0034  ops/merge is fail-open on unknown check conclusions   - on 13 branches, absent from main
    T-0054  README points at a NOTICE file that does not exist    - on task/T-0027 only

Neither is lost - they arrive when their branches merge. But T-0034 was **nearly** dropped: merging main into
`task/T-0033` produced a rename/delete conflict, because git paired a deleted `T-0033` task file with the
`T-0034` one by content similarity and reported T-0034 as "deleted in origin/main". Main never had it. Taking
git's suggested resolution would have silently removed a filed task.

**So: after every conflicted merge in this window, run**

    git ls-tree -r --name-only HEAD | grep -oE 'T-[0-9]+' | sort -u

and confirm no id present before the merge is missing after it. A dropped task file is invisible to
`queue-check`, which only ever complains about ids it can see.

## 4. Traps that fire on specific merges

| When | What happens | Fix |
|---|---|---|
| `task/T-0036` lands | `check-exec-bits` fails: `ops/lib/classify-checks.py` is 100755 on T-0021 while T-0036 reclassifies `ops/lib/*.py` as 100644 data | `git update-index --chmod=-x`, per **T-0041** |
| the Dockerfile chain meets `task/T-0058` | `check-line-cap` fails: `services/etl/tests/test_dockerfile.py` is 436 lines | already exempted in T-0058, pointing at **T-0062** which splits it |
| the second of `task/T-0023` / `task/T-0049` lands | two different pins both numbered `P-OPS-02` | renumber T-0049's to P-OPS-03; `check-pins` catches it, so it cannot be forgotten - see **T-0057** |

None of these is silent. `check-pins` and `check-exec-bits` both refuse, so the merged `main` goes red rather
than quietly wrong - **provided CI runs**, which is T-0053. That correction matters: two of these were
originally filed as silent-corruption risks and they are not.

## 5. Signoff state, which gates the order more than dependencies do

`ops/merge` requires the task in `queue/done/` on the PR head. As of this revision **14 branches are signed
off** - T-0014, T-0021, T-0022, T-0023, T-0024, T-0026, T-0035, T-0036, T-0037, T-0038, T-0039, T-0042,
T-0044, T-0047 - and the rest are still in review. Merge the signed-off set first, in the dependency order
above; the others cannot merge yet regardless of what this file says.

