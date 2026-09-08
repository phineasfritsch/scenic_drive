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


---

# Revision, 2026-09-08 (second): order is a constraint, and one rehearsal is not enough

The revision above rehearsed the backlog cumulatively and reported **27 merged, 3 conflicts, 25 gate
failures**. Two things were wrong with that number, and both are worth more than the corrected figure.

## 6. The exec-bits failures were an ORDERING constraint, not a mode error

Section 4 above says: *when `task/T-0036` lands, `check-exec-bits` fails because `classify-checks.py` is
100755 on T-0021 while T-0036 reclassifies `ops/lib/*.py` as 100644 data — fix with `git update-index
--chmod=-x`, per T-0041.*

**That is not what is happening, and the prescribed fix is already applied.** The file has been 100644 since
`b86a62e`. The failure direction is the opposite of the one recorded:

    merging task/T-0021 first:
      P-OPS-01: wrong git file mode:
        ops/lib/classify-checks.py (script, should be 100755, is 100644)

    merging task/T-0036 first, then task/T-0021:
      P-OPS-01: 25 files, 20 required present, all modes correct

T-0036 changes the *rule* — `ops/lib/*.py` are data, because they are only ever invoked as
`"$PY" ops/lib/x.py`. T-0021 adds a file the rule applies to. Whichever mode `classify-checks.py` carries,
**one of the two orders fails**: at 100644 it is correct after T-0036 and wrong before it; at 100755, correct
before and wrong after. There is no mode that is right in both orders, so this can only be fixed by ordering.

Nine of the twenty-five gate failures were this one constraint, re-reported against every branch that
followed T-0021. Both branches are based on `main`, so nothing in the PR graph orders them and the
rehearsal's topological sort fell back to alphabetical — T-0021 first, which is the wrong one.

**Encoded rather than written down.** `ops/merge-rehearse` now carries the constraint as an extra edge, since
"X must merge after Y" has the same shape as "X is based on Y" and the sort needs no special case:

    EDGES+=("task/T-0021 task/T-0036")

A constraint a human has to remember is one that gets forgotten. After it, the cumulative run reports
**28 of 31 merged, 3 conflicts, 4 gate failures** — the nine exec-bits failures gone, and the three conflicts
unchanged and still real.

## 7. A cumulative rehearsal cannot answer "does this branch break main"

The four remaining gate failures were all `duplicate id`. Checking them by merging each branch into `main`
**alone** gave a different and larger answer:

    task/T-0023        T-0032 T-0033 T-0038 T-0039
    task/T-0024        T-0032 T-0033
    task/T-0038        T-0032 T-0033
    task/T-0042        T-0032 T-0033
    task/T-0046        T-0032 T-0033
    task/T-0049        T-0049
    (task/T-0025, T-0027, T-0028, T-0029, T-0030, T-0040, T-0069: clean)

**Six branches break `main` on their own. The cumulative run named four, and two of those wrongly.**

- **It missed T-0042 and T-0046.** Both reintroduce `queue/ready/T-0032` and `T-0033`. By the time they
  merged, `task/T-0032` and `task/T-0033` had already merged and taken those paths with them, so the
  duplicate never appeared and both were reported *"merged, gates clean"*.
- **It blamed T-0025 for T-0024's defect.** A failure that no later branch repairs is still present at the
  next step, and the next, so cumulative mode re-reports it against every branch that follows the one that
  caused it.

Both directions are the same root cause: in cumulative mode the state under test is *everything merged so
far*, and a per-branch verdict read off it is not a per-branch verdict.

So `ops/merge-rehearse` now has two modes, and **both must be run** — each is blind exactly where the other
sees:

| Mode | Finds | Cannot see |
|---|---|---|
| `ops/merge-rehearse` (cumulative) | collisions BETWEEN branches: the ADD/ADD on `gh-stub-for-merge-tests`, the line-cap failure where the Dockerfile chain meets T-0058 — defects no single branch can produce | a defect a later branch happens to clean up |
| `ops/merge-rehearse --pairwise` | "this branch alone breaks `main`" — the question a reviewer is actually asking, and the only one whose answer does not depend on what merged first | a cross-branch collision, since it never holds two branches at once |

Cumulative mode also now marks a repeated failure `(INHERITED, unchanged by this branch)` instead of counting
it again, and `--pairwise` refuses to run at all if `main`'s own gates are red, because then every row
inherits main's failure and the run says nothing.

## 8. The six branches, repaired

The mechanism is the one section 2 describes, with a case that section missed: not only *moved* task files
but **files the branch itself created**. `task/T-0023` filed T-0038 and T-0039 into `queue/ready/`; `main`
later claimed them into `queue/claimed/`. That is an ADD/ADD across two different paths, so git keeps both
and rename detection has nothing to work with — there was no rename.

Repaired on all six by merging `origin/main` first, so the branch knows about the move, and only then
removing the copy at the path `main` no longer uses. Deleting without merging first just re-creates the
divergence. Verified after by re-merging each into `main` alone:

    task/T-0023        dups=none         QUEUE OK (67 tasks)
    task/T-0024        dups=none         QUEUE OK (67 tasks)
    task/T-0038        dups=none         QUEUE OK (67 tasks)
    task/T-0042        dups=none         QUEUE OK (67 tasks)
    task/T-0046        dups=none         QUEUE OK (67 tasks)
    task/T-0049        dups=none         QUEUE OK (66 tasks)

`ops/review` should make this class impossible to reach; that is **T-0063**, still open.

## 9. Correction to section 5: CI runs again

Section 4 hedged every trap with *"provided CI runs, which is T-0053"*. The repository is public with Actions
enabled as of 2026-09-07, branch protection requires `core` and `pins-source-only`, and both are green on
`main` (16 and 5 steps respectively). `enforce_admins` is deliberately **false**, because `ops/claim` pushes
the claim commit straight to `main` and a required-review rule would deadlock the queue. T-0053 can close.

## 10. The `gh-stub` conflict, resolved and executed rather than reasoned

Sections 1 and "The one real conflict" both describe this as three branches adding the same path with
different content. Measured, that is wrong in a way that makes it easier:

    task/T-0021   100755 blob 0002d211   ops/lib/gh-stub-for-merge-tests
    task/T-0022   100755 blob e00393e1
    task/T-0044   100755 blob e00393e1
    task/T-0049   100755 blob e00393e1

T-0022, T-0044 and T-0049 carry the **byte-identical** blob at the **same mode**, and git auto-resolves an
identical ADD/ADD. So there is **one** conflict, not three: T-0021's copy against the other three's. Once the
first of them merges, the rest are clean.

T-0022's copy is a strict superset — it adds `STUB_HEAD_REF` and `STUB_DONE_NAMES` and a
`contents/queue/done` case, and both new defaults reproduce T-0021's fixed behaviour exactly
(`${STUB_HEAD_REF:-tmp/stub-no-task}` against T-0021's literal `tmp/stub-no-task`). **Resolution: take
T-0022's copy** — as previously written, and now performed:

    reset --hard origin/main
    merge task/T-0036, task/T-0021              -> clean
    merge task/T-0022                           -> CONFLICT: ops/lib/gh-stub-for-merge-tests
      resolve to T-0022's copy                  -> e00393e1
    merge task/T-0044                           -> clean
    merge task/T-0049                           -> clean

and every gate run on the resolved tree:

    check-merge-reason-cap  P-OPS-02: ... (15 cases: ...)                    exit 0
    check-exec-bits         P-OPS-01: 27 files, 20 required present, all modes correct
    check-line-cap          P-SRC-02: 9 Swift files tracked, none over 300 lines
    queue-check             QUEUE OK (66 tasks)
    duplicate pin ids       none

`ops/lib/check-merge-reason-cap` is the **only executable caller** of the stub on any branch
(`git grep -l gh-stub` across all four: T-0021's and T-0022's uses are hand-run demonstrations recorded in
their task logs). It is T-0049's pin, it exercises the resolved stub, and it passes. That is the evidence
that the resolution satisfies both callers rather than whichever one the resolver was looking at.

**So the whole `ops/merge` chain has a proven order**, and it is not the one in "The order" above — T-0036
moved to the front because both T-0021 and T-0049 add an `ops/lib/*.py`:

    main -> T-0036 -> T-0021 -> T-0022 (resolve stub to T-0022's copy) -> T-0044 -> T-0049

`ops/merge-rehearse` derives the T-0036 edges itself now, by asking which branches add an `ops/lib/*.py`,
rather than carrying a list. The first version hard-coded `task/T-0021` because that was the branch that had
been measured; `--pairwise` then found `task/T-0049` failing identically on
`ops/lib/merge_reason_cap_assert.py`, which the hard-coded pair said nothing about.

## 11. Two things the merger must DO, not just check

**Set `pins/floor_linux_py.txt` when the ETL chain lands.** T-0071 split the single Linux test floor into one
file per tier — `floor_linux_swift.txt` (16), `floor_linux_ts.txt` (34), `floor_linux_py.txt` (**0**). It is 0
because the pytest tier does not exist on `main`. The moment the ETL chain merges, the tier appears with a
floor of zero, which is exactly the hole T-0071 was filed to close, for the suite that has the most tests in
it. Measure it on the merged tree and set it in the same commit:

    ops/test   ->   TESTS linux=N/M (swift=16/16 ts=34/34 py=<count>/0 ...)

`ops/test` now also fails a tier whose floor is positive but which did not run, so this cannot be set
optimistically and forgotten — but a floor of 0 is silent by design, and that is the one that needs a human.

**Merge `task/T-0036` before `task/T-0021`, `task/T-0049` and `task/T-0081`.** Not a preference — all three
fail CI today, on the real runs, for exactly this:

    #17 task/T-0021   core FAILURE   P-OPS-01: ops/lib/classify-checks.py (script, should be 100755, is 100644)
    #41 task/T-0049   core FAILURE   P-OPS-01: ops/lib/merge_reason_cap_assert.py (script, should be 100755, is 100644)
    #56 task/T-0081   core FAILURE   P-OPS-01: ops/lib/etl_mutation.py, ops/lib/etl_mutation_rules.py

T-0081 is the one that matters for the RULE rather than for the order: it did not exist when the rule was
written, and `ops/merge-rehearse` derives its edge anyway, by asking which branches add an `ops/lib/*.py`.
A hand-written list would have named T-0021 and stopped. Verified in a throwaway: `main` + T-0036 + T-0081
gives `P-OPS-01: 31 files, 20 required present, all modes correct`.

Both go green once T-0036 reclassifies `ops/lib/*.py` as data. `ops/pr-ci-preflight` (T-0075) predicts both
locally without waiting for a run, and `ops/merge-rehearse` derives the ordering edge itself by asking which
branches add an `ops/lib/*.py`.

## 12. State as of 2026-09-08

Actions is on and both jobs pass on `main`. Every open PR was reopened to force a run, since a PR opened while
Actions was disabled never gets one and `ops/merge` refuses a PR with no checks.

    ops/merge-rehearse              28 of 31 merged, 3 conflicts, 0 gate failures
    ops/merge-rehearse --pairwise   31 of 31 merged, 0 conflicts, 2 gate failures
    ops/pr-ci-preflight             29 ok, 2 failing gates, 0 conflicting, 0 stale   (of 31 open PRs)

The three conflicts are the one `gh-stub` ADD/ADD resolved in section 10; the two gate failures are T-0021 and
T-0049 above. Nothing else is red.

`ops/merge 21 --dry-run` reports **every gate passed** for T-0036, which is the branch the other two wait on.

## 13. The `pins/PINS.yaml` conflict must be resolved as a UNION, and taking a side is silent

`task/T-0023` and `task/T-0049` both add a pin, and they conflict on `pins/PINS.yaml`. **Resolving it by
taking either side drops the other's pin and nothing complains.** Executed, in that order, deliberately wrong
first:

    merge T-0036, then T-0023        -> P-OPS-01, P-OPS-02
    merge T-0049, `checkout --theirs pins/PINS.yaml`
                                     -> P-OPS-01, P-OPS-03        <- P-OPS-02 GONE, no error
    check-pins on that tree          -> failed=0

`check-pins` only reports ids it can *see*, which is the same blind spot the task-id census exists for on the
queue side. A pin that vanishes in a merge resolution is invisible to the tool whose whole job is pins.

**The correct resolution** keeps the merged-so-far file and appends only the other branch's own pin block:

    P-OPS-01, P-OPS-02, P-OPS-03
    PINS ok=11 skipped=0 pending=3 expired=0 failed=0        exit 0

So after resolving `pins/PINS.yaml` — or any conflict on it — run the pin census the same way the task census
is run after a conflicted merge:

    grep -E '^- id:' pins/PINS.yaml | sort | uniq -d      # must print nothing
    grep -cE '^- id:' pins/PINS.yaml                      # must not have gone DOWN

`ops/merge-rehearse` reports duplicate pin ids but cannot report a *missing* one, for the same reason: it
compares the tree against itself. The count is the check.

T-0057 is closed on this: the renumber to P-OPS-03 landed at `4fb4609`, and `check-pins` does detect a
duplicate id (`- P-SRC-01: duplicate id`, exit 1), which the task's brief said it did not.

## 14. The 2026-09-08 branches, and a dependency worth knowing before you start

Nine tasks shipped that day, plus three more in flight. They are **not** independent, and one chain is rooted
somewhere that cannot merge yet.

**Rooted on `main`, mergeable in any order once their gates pass:**

    #47 task/T-0071   per-tier test floors        #53 task/T-0083   the read-only SQL gate's Python mirror
    #48 task/T-0075   ops/pr-ci-preflight         #54 task/T-0060   the NTFS rules in CLAUDE.md
    #55 task/T-0065   ops/merge-rehearse

**The `queue.py` chain — five deep, and its root has no PR:**

    task/T-0068  (T-0073's fix)  ── no PR, not signed off ──┐
      #50 task/T-0070   duplicate WORK, not just id         │
        #51 task/T-0082   never sweep a live branch         │
          #52 task/T-0063   ops/review refuses a duplicate  │
            task/T-0087   usage lines, in flight            ┘

`task/T-0068` carries T-0073's round-two fix and is where `ops/lib/queue.py` grew to 615 lines. Each of the
four above was cut from its predecessor deliberately, to build on the newest `queue.py` rather than fork it —
but the consequence is that **none of them can merge until T-0068 does**, and T-0068 is not signed off: its
adversarial verification came back `holds = false`, and eleven evasions survived.

That is the right state — T-0068's fix is strictly better than what it replaced and is genuinely incomplete —
but it means four green PRs are parked behind one that is not ready. Two ways out, and the choice is the
owner's:

- **Sign off T-0068 as a partial improvement** with its open routes recorded (they are, verbatim, in its
  `## Log`), and merge the chain. [[T-0073]]'s remaining routes then continue as their own task.
- **Rebase #50 onto `main`.** The conflict is real but small: `cmd_check`'s duplicate-detection block sits
  beside T-0073's owner/reviewer normalisation, and both are additive.

**Two other chains from the same day**, both rooted on branches that are also unmerged and unsigned:

    task/T-0066 → task/T-0072 → task/T-0077 → task/T-0086     (pins.py, the ops shims, the environment)
    task/T-0071 → task/T-0079 → task/T-0085                    (the commit-msg hook and its ratchets)

`task/T-0071` is the exception in that list: it IS on `main` as #47, so that chain's root is mergeable.

**And the ordering rule from section 11 still binds all of it**: `task/T-0071` deletes `pins/floor_linux.txt`,
which fifteen branches modify, so it merges LAST among those — `ops/merge-rehearse` derives that edge itself
now and will print it.

## 15. The definitive rehearsal, 41 open PRs

    REHEARSAL (cumulative): 37 of 41 merged, 4 conflicts, 0 gate failures, 0 unresolvable

**Zero gate failures across the whole backlog.** Every duplicate task id, every mode error and every line-cap
breach that earlier rehearsals found is repaired. What remains is four conflicts, and all four are known, with
a written resolution:

    task/T-0022   ops/lib/gh-stub-for-merge-tests                 section 10 - take T-0022's copy
    task/T-0044   ops/lib/gh-stub-for-merge-tests                 same file, same resolution
    task/T-0049   ops/lib/gh-stub-for-merge-tests + PINS.yaml     section 10 and section 13 (UNION the pins)
    task/T-0071   ops/test + pins/floor_linux.txt                 section 11 - and it is deliberate

`task/T-0071`'s conflict is **not** a defect and must not be scheduled away. It deletes `pins/floor_linux.txt`
and fourteen branches modify it, so the delete/modify collision is the moment somebody has to set
`floor_linux_py` for the ETL suite that those fourteen branches bring. Merged any earlier it is fourteen
identical hand resolutions; merged last it is one, and that one is a question that needs answering.

**Both derived ordering rules fired, and the second one is why they are derived rather than listed:**

    ordering: task/T-0021 / T-0049 / T-0081 add an ops/lib/*.py, so each must follow task/T-0036
    ordering: task/T-0071 deletes pins/floor_linux.txt, which <14 branches> modify - T-0071 must follow them

`task/T-0081` did not exist when the first rule was written. A hand-maintained list would have named T-0021,
been corrected to add T-0049 when `--pairwise` found it, and been wrong again within a day.

**Also true, and not visible in this run:** the rehearsal does not run `ops/lib/check-lock-lifecycle` or
`ops/lib/check-brief-required`, and the first of those is currently RED on every branch carrying both
[[T-0073]]'s `MIN_TASKS` floor and [[T-0032]]'s fixture. A collision of exactly the shape this tool exists to
find is invisible to it. Filed as [[T-0091]]; until it lands, `0 gate failures` above means "0 of the four
gates this tool runs", not "0 gates fail".

## Re-run after a day of review fixes — the result did not move

The rehearsal above was recorded before an independent review round landed sixteen fixes across six
branches: `task/T-0082` (three commits, including a guard that had disabled the sweeper), `task/T-0063`,
`task/T-0060`, `task/T-0062`, `task/T-0086`, plus eleven queue commits on `main`. Re-run afterwards against
the refreshed refs:

    REHEARSAL (cumulative): 37 of 41 merged, 4 conflicts, 0 gate failures, 0 unresolvable

    task/T-0022  CONFLICT: ops/lib/gh-stub-for-merge-tests
    task/T-0044  CONFLICT: ops/lib/gh-stub-for-merge-tests
    task/T-0049  CONFLICT: ops/lib/gh-stub-for-merge-tests pins/PINS.yaml
    task/T-0071  CONFLICT: ops/test pins/floor_linux.txt

Diffing the per-branch outcome column of the two runs gives **no output**: every branch landed in the same
state, in the same order, with the same four conflicts. That is the useful result — it says a day of edits
to five branches and to `main` changed nothing about mergeability, so the resolutions written above are
still the resolutions.

It is worth being precise about what that does and does not license. It does NOT mean the fixes were
inert — `ops/lib/queue.py` grew on three branches and `CLAUDE.md` changed on one. It means none of those
edits touched a file another branch touches, which is the only thing this tool measures. The caveat above
still stands too: `0 gate failures` means zero of the four gates this tool runs, and
`ops/lib/check-lock-lifecycle` is not one of them ([[T-0091]]).

## The red PRs are three, not two, and they are one cause

Measured from the CI logs themselves, not from the rollup:

    PR #17  task/T-0021   P-OPS-01: ops/lib/classify-checks.py        (script, should be 100755, is 100644)
    PR #41  task/T-0049   P-OPS-01: ops/lib/merge_reason_cap_assert.py (script, should be 100755, is 100644)
    PR #56  task/T-0081   P-OPS-01: ops/lib/etl_mutation.py           (script, should be 100755, is 100644)
                          P-OPS-01: ops/lib/etl_mutation_rules.py     (script, should be 100755, is 100644)

Same pin, same sentence, three branches. Each adds an `ops/lib/*.py` that `main`'s P-OPS-01 still classifies
as a script; `task/T-0036` is the branch that reclassifies them, and after it merges all three are `merged,
gates clean` in the rehearsal above. **One merge turns every red PR in the repository green.** That is the
whole argument for the order at the top of this file, stated in the branches' own CI output.

It is also why no mode change is the fix: setting 100755 on those files makes them green today and red the
moment T-0036 lands, because then they are data. Whichever mode is chosen, one of the two merge orders must
fail — which is the constraint, not a bug in anyone's branch.

**A trap for anything that reads GitHub's rollup rather than the checks.** `statusCheckRollup` on PR #26
(`task/T-0024`) still carries a `FAILURE` entry from a superseded run, while `gh pr checks 26` reports
`core pass` / `pins-source-only pass`. A tool that counts failures in the rollup reports four red PRs where
three exist, and would refuse a branch that is green. `gh pr checks` — or the conclusion of the LATEST run
per check name — is the thing to read.
