---
id: T-0022
title: ops/merge skips the review gate for branches not named task/T-nnnn (reviewer-7 finding)
state: review
owner: agent/builder-4
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T15:42:10Z
lease_expires_at: 2026-09-07T18:42:10Z
worktree: ../wt/T-0022
branch: task/T-0022
exclusive: []
touches: [ops/merge, queue/README.md, ops/lib/gh-stub-for-merge-tests]
pins_affected: []
reviewer: agent/reviewer-20
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/merge` gate 1 extracts a task id from the PR's head branch name with `grep -oE 'T-[0-9]{4}'` and, when
found, requires that task to be in `queue/done/` on the PR head (a reviewer signed it off). When the branch
name contains **no** task id, gate 1 prints `task (branch <name> names no task; skipping the review gate)` and
falls through to gate 2 unconditionally. So the review gate is only enforced for people who already followed the
`task/T-nnnn` naming convention; anyone (or anything - a script, a fat-fingered branch name, a deliberately
unconventional branch) merging from a differently-named branch gets zero review-gate coverage, silently. This is
exactly the "reviewer-7 finding" also flagged as a non-blocking observation in T-0016's own review log, which
suggested the fix implemented here: "make ops/merge refuse non-task/T-nnnn branches by default with an explicit
override flag."

### Decision

Fail closed. If the branch names no task, `ops/merge` now **refuses to merge** (exit 1) unless the caller passes
`--no-task-reason="<why this is safe>"` with a non-empty (post-trim) reason, in which case gate 1 is overridden
and the reason is echoed to stdout so it lands in the operator's terminal/CI log as an audit trail before the
merge proceeds to gate 2/3.

Alternatives considered and rejected:
- **A bare escape flag with no reason** (e.g. `--skip-task-gate`) - rejected. "Convenient must not be the same as
  unchecked": a flag that takes no argument is exactly as easy to alias/script into a habit as the current
  default-skip is, it just moves the unchecked path one keystroke later. Requiring a reason string forces a
  deliberate, legible decision each time, not a standing bypass.
- **Auto-allow based on branch-name heuristics** (e.g. treat `queue/*`, `revert-*`, `hotfix/*` as automatically
  exempt) - rejected. It would reintroduce exactly the same class of bug this task fixes: a convention-based
  bypass that's silent by default and gameable by naming a branch to match. It also needs to inspect *diff
  contents* to be honest about "queue-only," which is scope gate 1 (a task-id/review-signoff check) shouldn't
  own. GitHub's own default revert-branch naming (`revert-<pr>-task/T-nnnn`) already embeds the original task id,
  so `grep -oE 'T-[0-9]{4}'` finds it and gate 1 already passes such branches unchanged - no special case needed.
  A genuinely task-less revert, hotfix or queue-maintenance branch is exactly the legitimate case the reasoned
  override exists for.
- **Refusing outright with no override at all** - rejected. There are real no-task cases (a `queue:`-only
  maintenance branch, a hand-made revert, an emergency hotfix cut before a queue task exists for it) where
  requiring a `T-nnnn` task and a reviewer sign-off first would block legitimate, already-reviewed-by-a-human-PR
  work. An override that demands a reason satisfies "waiting must not become merging" (there is no default path
  that proceeds without an explicit decision) while still allowing the legitimate cases through, on the record.

`queue/README.md` step 7 previously implied the review gate applies unconditionally
("It refuses unless the task is in `done/` on the PR head..."), which was inaccurate while the no-task case
silently skipped it (T-0016's review flagged this wording gap too). After this fix the statement is true by
default; step 7 is updated to name the `--no-task-reason` override explicitly instead of leaving it undocumented.

### touches: widened

Original `touches: [ops/merge, queue/README.md]` didn't include a test fixture. The task's required demonstration
calls for exercising the fix against `ops/lib/gh-stub-for-merge-tests`, a deterministic `gh` double - but that
file does not exist on this branch's base (`main` @ f910f5f): it was created only on the not-yet-merged
`task/T-0021` branch (a sibling, in-flight task fixing `ops/merge` gate 2's polling behavior), never landed on
`main`. Since the required demonstration is not reproducible without it, and CLAUDE.md requires new checks to be
demonstrated red-then-green in the repo, I added `ops/lib/gh-stub-for-merge-tests` to `touches:` and committed a
copy of it (same `STUB_STATE`/`STUB_ROLLUP`/`STUB_FLIP`/`STUB_COUNT` knobs, same default `headRefName` answer of
`tmp/stub-no-task`, verbatim from T-0021's version) extended with the two new knobs gate 1's fix needs
(`STUB_HEAD_REF` to pick which branch name is under test, `STUB_DONE_NAMES` to fake `queue/done/` contents for
the task-branch case) - no existing knob's behavior changed. T-0021 did not touch gate 1 or this behavior, so
there is no functional overlap; the only collision risk is a future add/add conflict on this one fixture file
when T-0021 merges, which is a merge-order note for whoever lands second, not a masked bug.

## Log
- 2026-09-07T15:42:10Z claimed by agent/builder-4; lease until 2026-09-07T18:42:10Z
- 2026-09-07T16:05:00Z touches widened to add ops/lib/gh-stub-for-merge-tests (see Brief) - the required
  demonstration fixture doesn't exist on main yet; it only exists on the unmerged task/T-0021 branch.
- 2026-09-07T16:40:00Z Implemented the fix in `ops/merge` (gate 1 only; gate 2/3 untouched) and committed
  `ops/lib/gh-stub-for-merge-tests` (100755) as a test fixture, copied verbatim from `task/T-0021`'s version
  and extended with two new knobs (`STUB_HEAD_REF`, `STUB_DONE_NAMES`) so gate 1's task-branch path is
  reachable too. Setup: `gh` shadowed on `PATH` by a directory containing the stub
  (`ops/lib/gh-stub-for-merge-tests` copied to `<dir>/gh`, chmod +x), demonstrated with
  `ops/merge <pr> --dry-run`.

  RED — current (pre-fix) `ops/merge` on the stub's default no-task branch (`STUB_HEAD_REF` unset ->
  `tmp/stub-no-task`), run from `git show main:ops/merge`:
  ```
  $ bash <pre-fix ops/merge> 42 --dry-run
  task     (branch tmp/stub-no-task names no task; skipping the review gate)
  checks   total=2 pending=0 failed=[none] mergeState=CLEAN
  DRY RUN: every gate passed; would merge pr=42 task=none head=tmp/stub-no-task
  EXIT CODE: 0
  ```
  Confirms the bug as described: the review gate is silently skipped and the dry run reports every gate passed.

  GREEN 1 — same input, patched `ops/merge`, no override:
  ```
  $ bash ops/merge 42 --dry-run
  MERGE REFUSED: branch tmp/stub-no-task names no task (no T-nnnn), so the review gate can't check queue/done/ for it
    If this is really a no-task branch (queue-only maintenance, a revert, a hotfix), rerun with
    --no-task-reason="<why merging without a reviewed queue task is safe here>" to override, on the record.
  EXIT CODE: 1
  ```

  GREEN 2 — escape hatch with a reason succeeds; escape hatch present but reason empty/whitespace-only still
  refuses (can't be gamed by passing the flag with nothing in it):
  ```
  $ bash ops/merge 42 --dry-run --no-task-reason="queue-only maintenance branch, no source changes"
  task     branch tmp/stub-no-task names no task; review gate overridden on record: queue-only maintenance branch, no source changes
  checks   total=2 pending=0 failed=[none] mergeState=CLEAN
  DRY RUN: every gate passed; would merge pr=42 task=none head=tmp/stub-no-task
  EXIT CODE: 0

  $ bash ops/merge 42 --dry-run --no-task-reason=""
  MERGE REFUSED: branch tmp/stub-no-task names no task (no T-nnnn), so the review gate can't check queue/done/ for it
  ...
  EXIT CODE: 1

  $ bash ops/merge 42 --dry-run --no-task-reason="   "
  MERGE REFUSED: branch tmp/stub-no-task names no task (no T-nnnn), so the review gate can't check queue/done/ for it
  ...
  EXIT CODE: 1
  ```

  GREEN 3 — a normal `task/T-XXXX` branch still passes/fails gate 1 exactly as before (unchanged):
  ```
  $ STUB_HEAD_REF="task/T-9999" STUB_DONE_NAMES="T-9999-example-task.md" bash ops/merge 42 --dry-run
  task     T-9999 is in queue/done/ on task/T-9999
  checks   total=2 pending=0 failed=[none] mergeState=CLEAN
  DRY RUN: every gate passed; would merge pr=42 task=T-9999 head=task/T-9999
  EXIT CODE: 0

  $ STUB_HEAD_REF="task/T-9999" STUB_DONE_NAMES="" bash ops/merge 42 --dry-run
  MERGE REFUSED: T-9999 is not in queue/done/ on task/T-9999 - a reviewer has not signed it off
  EXIT CODE: 1
  ```

  Sanity — pre-existing stub knobs still work, unweakened (STUB_STATE, STUB_ROLLUP, STUB_FLIP, STUB_COUNT), run
  past gate 1 via `--no-task-reason` to isolate gate 2:
  ```
  $ STUB_STATE=DIRTY bash ops/merge 42 --dry-run --no-task-reason="sanity check"
  ... checks   total=2 pending=0 failed=[none] mergeState=DIRTY
  MERGE REFUSED: mergeStateStatus=DIRTY (want CLEAN)          # exit 1

  $ STUB_ROLLUP='[{"name":"core","c":"FAILURE"}]' bash ops/merge 42 --dry-run --no-task-reason="sanity check"
  ... checks   total=1 pending=0 failed=[core] mergeState=CLEAN
  MERGE REFUSED: failing checks: core                          # exit 1

  $ STUB_FLIP=1 STUB_COUNT=<scratch file> bash ops/merge 42 --dry-run --no-task-reason="sanity check"
  ... checks   total=0 pending=0 failed=[none] mergeState=UNKNOWN
  MERGE REFUSED: no checks reported at all - CI did not run for this PR   # exit 1
  ```
  Confirms this change adds no path that reaches `gh pr merge` while a check is not SUCCESS: gate 2/3 are
  byte-for-byte untouched, and every existing stub knob still exercises them exactly as before.

- 2026-09-07T17:05:00Z Full verification suite, all green:
  ```
  $ bash ops/check-pins
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
  EXIT: 0

  $ bash ops/queue-check
  QUEUE OK (34 tasks)
  EXIT: 0

  $ (cd services/api && npm ci --no-audit --no-fund)   # T-0040 env gap, not caused by this change
  added 85 packages in 9s

  $ bash ops/test
  TESTS linux=50/50 ios=skipped failed=0 skipped=0
  OK
  EXIT: 0
  ```
  `git ls-files -s ops/merge ops/lib/gh-stub-for-merge-tests` -> both `100755` (exec bit committed correctly on
  the new script, per CLAUDE.md/P-OPS-01).

  Note: GitHub Actions on this repo has been running zero-step, seconds-long jobs since ~15:11 UTC (spending
  limit on this private repo, filed separately) — not this task's concern; verified locally per instructions.
