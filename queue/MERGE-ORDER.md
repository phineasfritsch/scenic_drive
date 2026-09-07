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
