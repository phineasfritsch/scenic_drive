---
id: T-0039
title: pre-commit touches enforcement is dead for tasks in queue/done/ - a signed-off task can commit anywhere
state: done
owner: agent/builder-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:38:26Z
lease_expires_at: 2026-09-07T19:38:26Z
worktree: ../wt/T-0039
branch: task/T-0039
exclusive: []
touches: [.githooks/pre-commit, ops/lib/queue.py]
pins_affected: []
reviewer: agent/reviewer-24
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`.githooks/pre-commit` only looks for the task file in `queue/claimed/` and `queue/review/`:

    taskfile="$(ls queue/claimed/"$task"*.md queue/review/"$task"*.md 2>/dev/null | head -1 || true)"

Once a reviewer moves the task to `queue/done/`, `$taskfile` is empty, the `touches:` block is skipped
entirely, and the branch can commit ANY path with the hook still exiting 0. The branch is usually still open at
that point - `ops/merge` requires the task to be in `done/` on the PR head, so every PR spends its whole
merge window in exactly this ungoverned state.

Found while fixing T-0023: commits touching `.gitignore` and `ops/lib/junit_count.py`, neither in that task's
`touches:`, were accepted without complaint.

- Include `queue/done/` in the lookup.
- Decide and document what a `done` task may still commit. Recommendation: `touches:` still applies; nothing
  about review makes a path safe that was not before.
- Demonstrate red: on a branch whose task is in `done/`, stage a path outside `touches:` and show the hook
  accepts it today; apply the fix; show it refuse.

## Log
- 2026-09-07T16:38:26Z claimed by agent/builder-21; lease until 2026-09-07T19:38:26Z
- 2026-09-07T16:43:49Z agent/builder-5: decision + red/green demonstration.

  **Decision: what may a `done` task still commit?** Going with the brief's recommendation - `touches:`
  still applies, unchanged, in `done/` exactly as in `claimed/` and `review/`. Reasoning, from the cases
  that actually arise on this fleet (per CLAUDE.md: don't make the hook refuse what the fleet legitimately
  does many times a day, and don't leave the gate open either):

    - A reviewer moving a task queue/review -> queue/done and committing only the task file: already
      exempt today, unconditionally, via the `[[ "$f" == queue/* ]] && ok=1` line - this never touched
      `touches:` and still doesn't. No change in behavior for this, the single most common `done`-state
      commit on the fleet.
    - An owner fixing a review finding after the task is already in `done/` (e.g. a fixup pushed to the
      same PR branch before `ops/merge` runs): must stay inside the same `touches:` it had in `claimed/`.
      Nothing about a reviewer's sign-off makes a path outside the declared scope newly safe - the premise
      in CLAUDE.md ("agents report success on broken work") applies exactly as much post-review as
      pre-review. If the fix needs a path outside `touches:`, the correct move is to widen `touches:` in
      the task file (which is itself inside `queue/*` and always committable) and say so in the log, same
      as any other task - never to have the hook wave it through because a reviewer already looked once.
    - A merge commit: out of scope for this hook by construction. `ops/merge` merges via `gh pr merge`
      (GitHub-side, API merge) - no local `git commit` happens on the task branch for it, so `pre-commit`
      never runs. A local `git merge` of a task branch onto `main` would run on branch `main`, which does
      not match `^task/(T-[0-9]+)`, so the touches block is skipped for that commit too (as it already is
      for any commit made directly on `main`) - unaffected by this fix either way.

  So the only code change needed: add `queue/done/` to the `ls` lookup. No change to the exemption logic,
  no change to what counts as "allowed" - only to *finding* the task file that was always supposed to
  govern the branch.

  **RED** - `.githooks/pre-commit` before the fix, on scratch branch `task/T-9101-red-demo` (deleted after
  this run), with a scratch task file at `queue/done/T-9101-scratch-red-demo.md`
  (`state: done`, `touches: [ops/scratch-red-demo-touch.txt]`), staging `services/scratch-red-probe.txt`
  (new file, not in that `touches:` list) and running the hook directly:

      $ bash .githooks/pre-commit; echo "EXIT=$?"
      EXIT=0

  No output, exit 0 - the hook accepted a staged path completely outside the task's `touches:` because
  `taskfile` came back empty (lookup only checked `claimed/` and `review/`), exactly the bug reported.

  **Fix applied** - `.githooks/pre-commit`, `taskfile=` line:

      -  taskfile="$(ls queue/claimed/"$task"*.md queue/review/"$task"*.md 2>/dev/null | head -1 || true)"
      +  taskfile="$(ls queue/claimed/"$task"*.md queue/review/"$task"*.md queue/done/"$task"*.md 2>/dev/null | head -1 || true)"

  plus a comment update at the top of the file documenting the `done/` case and the "review doesn't widen
  scope" rule. No other line changed.

  **GREEN 1 (refused)** - identical staged state as the RED run (same scratch branch/task file/probe file,
  only the hook script edited in between):

      $ bash .githooks/pre-commit; echo "EXIT=$?"
      pre-commit: services/scratch-red-probe.txt is outside T-9101 touches: [ops/scratch-red-demo-touch.txt ]
      pre-commit: refusing commit
      EXIT=1

  **GREEN 2 (legitimate cases all still pass)**, each on its own scratch branch/task file, deleted after:

    - `task/T-9102-claimed-demo`, task file in `queue/claimed/` (`state: claimed`,
      `touches: [ops/scratch-claimed-demo-touch.txt]`), staging `ops/scratch-claimed-demo-touch.txt`
      (inside `touches:`): `EXIT=0`, no output.
    - `task/T-9101-red-demo`, task file in `queue/done/` (`state: done`), staging only
      `queue/done/T-9101-scratch-red-demo.md` itself (the "reviewer commits only the task file" case):
      `EXIT=0`, no output.
    - Same branch/task, staging `ops/scratch-red-demo-touch.txt` (a path inside that `done` task's
      `touches:`): `EXIT=0`, no output.
    - `scratch/no-task-branch` (branch names no task at all), staging an arbitrary new file: `EXIT=0`, no
      output - unchanged, the `^task/(T-[0-9]+)` branch match still fails first, exactly as before this fix.
    - `task/T-9999-missing-file-demo` (branch names a task, but no `T-9999*.md` exists anywhere under
      `queue/claimed|review|done/`), staging an arbitrary new file: `EXIT=0`, no output - unchanged,
      `taskfile` is still empty (now checked across three directories instead of two, but still not found),
      so enforcement is still skipped exactly as it was pre-fix for this case.

  All scratch branches (`task/T-9101-red-demo`, `task/T-9102-claimed-demo`, `scratch/no-task-branch`,
  `task/T-9999-missing-file-demo`) and every scratch file created for these runs were deleted; `git status`
  confirmed clean before returning to `task/T-0039`.

  Did not touch `ops/lib/queue.py` - nothing in `queue.py` participates in `pre-commit`'s enforcement (it's
  a separate Python CLI for queue transitions; the hook is pure bash reading the filesystem directly), so no
  change was needed there for this fix. Leaving it out of this commit; `touches:` already allows it if a
  future finding needs it.
- 2026-09-07T18:05:00Z agent/reviewer-24: PASS, verified independently, all on my own scratch branches/task
  files (never reused the owner's `T-9101/T-9102/T-9999`), all deleted after. Re-derived rather than trusted
  everywhere below; anything I only read is called out as such.

  **Re-derived RED -> GREEN** (own scratch branch `task/T-9201-reviewer-red-demo`, own task file
  `queue/done/T-9201-reviewer-red-demo.md`, `touches: [ops/scratch-reviewer-touch.txt]`, own probe file
  `services/reviewer-red-probe.txt`): old hook (`git show HEAD~1:.githooks/pre-commit`, run from a scratch
  copy, tracked file never touched) -> `EXIT=0` (bug reproduced). New hook, identical staged state -> `EXIT=1`,
  `pre-commit: services/reviewer-red-probe.txt is outside T-9201 touches: [ops/scratch-reviewer-touch.txt ]`.
  Matches the owner's claim exactly.

  **Re-derived all five "still passes" cases**, each its own scratch branch/task (`T-9211` claimed-inside,
  `T-9212` done-ownfile / done-inside-touches, `scratch/no-task-branch-reviewer24`,
  `task/T-9999-nofile-anywhere-reviewer24`): all `EXIT=0`, matching the owner's GREEN 2. Confirmed, not just
  trusted.

  **`.githooks/pre-commit:12` (`--diff-filter=ACMR`, pre-existing, not touched by this diff) - SEV: high,
  out of scope for T-0039.** The filter has no `D`. A staged *deletion* never appears in `$staged`, so it
  skips CRLF, secrets, AND `touches:` entirely, in every task state including the new `done/` case this
  diff just closed. Reproduced: `done/` task with `touches: [ops/only-this-narrow-file.txt]`, staged
  `git rm --cached README.md` -> `EXIT=0`. A `done`-state branch (i.e. anywhere in its `ops/merge` window)
  can delete any file in the repo, including another task's file or a pin, with the hook silent. Same class
  of "ungoverned commit" the brief is about, bigger blast radius (delete vs. add/modify), not fixed here.
  Worth its own task.

  **`.githooks/pre-commit:36` glob, duplicate-task-across-directories (pre-existing pattern, now spans one
  more directory) - SEV: medium, out of scope for T-0039.** `ls a b c | head -1`: bash/`ls` sorts the
  combined argument list alphabetically regardless of the order written in the script, so precedence is
  `claimed/` < `done/` < `review/` (`c`<`d`<`r`), NOT script order and NOT "most recent." Reproduced: task
  `T-9202` present in both `queue/claimed/` (`touches: [ops/wide-open-dir/]`) and `queue/done/`
  (`touches: [ops/narrow-touch-only.txt]`) at once - staging `ops/wide-open-dir/anything.txt` (inside only
  the `claimed/` copy's list) -> `EXIT=0`, i.e. the stale/wider `claimed/` copy governed over the narrower,
  more-current `done/` one. `ops/queue-check` calls this state a duplicate and would catch it, but the hook
  runs pre-commit, before anyone runs `queue-check` - a `git mv` that copies before it deletes (or a merge
  conflict leaving both) opens exactly this window. Same failure mode already existed for claimed/review
  before this diff; not introduced or fixed by it.

  **Prefix collision between different task ids - checked, NOT exploitable, no finding.** Tested
  `task="T-9203"` against a decoy `queue/claimed/T-92030-decoy-wide-task.md` (`touches: [ops/]`) sitting
  alongside the real `queue/claimed/T-9203-narrow-task.md` (`touches: [ops/only-this-narrow-file.txt]`):
  `ls queue/claimed/T-9203*.md` still resolves to the real file first, because every task filename is
  `<id>-<slug>.md` - the `-` immediately after a shorter id sorts (ASCII `0x2D`) before any digit that would
  extend it into a longer id (`0x30`-`0x39`), so the exact match always alphabetizes first. Confirmed safe
  given the current naming convention; would break if a task file were ever named without the `-` separator
  right after the numeric id.

  **`.githooks/pre-commit:45` (`[[ "$f" == "$a"* ]]`, pre-existing, not touched by this diff) - SEV: medium,
  out of scope for T-0039.** Plain string-prefix match, no path-boundary check. Reproduced exactly the case
  named in my brief: `touches: [ops/test]`, staged new file `ops/testing-decoy-not-real-test-script.md` ->
  `EXIT=0` (wrongly treated as inside touches). Any `touches:` entry that is a file rather than a
  directory-with-trailing-slash is vulnerable to a same-prefix sibling.

  **`.githooks/pre-commit:40` (`if [[ -n "$allowed" ]]`, pre-existing, not touched by this diff) - SEV:
  medium, out of scope for T-0039.** `touches: []` and a task file with no `touches:` key at all both parse
  to an empty `$allowed`, and an empty `$allowed` means the whole enforcement block is skipped - i.e. it
  fails open (allow everything) rather than closed (allow nothing but the `queue/*` exemption). Reproduced
  both: `touches: []` staging an arbitrary root file -> `EXIT=0`; task file with the `touches:` key omitted,
  same probe -> `EXIT=0`.

  **`.githooks/pre-commit:44` (`[[ "$f" == queue/* ]] && ok=1`) - clarifying note, not a new defect.** This
  is a blanket exemption for *any* path under `queue/`, not only "its own task file" as the Brief/Decision
  prose in this log describes it - unchanged by this diff, and not something this diff could have narrowed
  without touching a line outside its declared scope. Reproduced: a `done/` task with a narrow `touches:`
  can stage a brand-new, unrelated file directly under `queue/` (`EXIT=0`) or edit another task's file under
  `queue/done/` (also `EXIT=0`, confirmed on a throwaway file - see caveat below). No behavior change from
  this diff; flagging only so the prose above isn't taken as a precise spec of what's exempted.
  Caveat: my first attempt at "edit another task's file" appended to
  `queue/done/T-0021-...merge.md` via `>>`, which turned out not to exist in this branch's HEAD (`task/T-0039`
  predates T-0021's `claimed->done` commits on `main`) - so that run actually tested "stage a new file under
  someone else's task id," not an edit of a tracked file. I deleted the resulting untracked file; the
  no-restriction result stands (also independently shown by the plain "arbitrary new file directly under
  `queue/`" case), but I did not end up testing a same-branch edit of an already-tracked, unrelated task file.

  **`.githooks/pre-commit:36` glob, states `queue/blocked/` and `queue/backlog/` (also `queue/ready/`,
  untested) - SEV: medium, out of scope for T-0039 brief but same bug class.** `ops/lib/queue.py:22` defines
  `STATES = ["backlog", "ready", "claimed", "review", "blocked", "done"]`; `blocked` is reachable from
  `claimed`, i.e. a branch/worktree can already exist and keep receiving commits after its task is moved to
  `blocked/`. The hook's lookup still only checks `claimed/`, `review/`, `done/`. Reproduced: task in
  `queue/blocked/` with `touches: [ops/only-this-narrow-file.txt]`, staged arbitrary root file -> `EXIT=0`;
  same for `queue/backlog/`. The brief named only `done/` (found via T-0023) and the fix matches that scope
  exactly, so this isn't a defect in what was delivered - but `blocked/` is the same "branch still open,
  enforcement dead" shape as the bug this task fixes, just not fixed. Worth its own task.

  **Confirmed, not just trusted:**
  - `git diff HEAD~1 -- .githooks/pre-commit`: exactly 2 hunks, both entirely inside the touches-enforcement
    comment/lookup (the CRLF check at lines 15-19 and the secrets check at lines 21-30 are untouched by
    either hunk).
  - `git ls-files -s .githooks/pre-commit` -> `100755 c2950dc...` - still executable.
  - `bash ops/check-pins` -> `PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux`, exit 0.
  - `bash ops/queue-check` -> `QUEUE OK (41 tasks)`, exit 0.
  - `bash ops/test` (after `cd services/api && npm ci --no-audit --no-fund`, the known T-0040 gap, not a
    defect of this diff) -> `TESTS linux=50/50 ios=skipped failed=0 skipped=0` / `OK`, exit 0.

  **Verdict: PASS.** The fix does exactly what the brief asked - `queue/done/` is now in the lookup,
  independently reproduced red then green on my own scratch data, and every legitimate case the owner
  claims still passes does, independently reproduced. `git diff HEAD~1` shows the change is confined to the
  touches-enforcement lookup; CRLF/secrets are untouched; the hook is still committed 100755. Everything I
  found beyond that - the `ACMR` deletion bypass, the duplicate-across-directories glob precedence, the
  prefix-match-without-a-boundary check, `touches: []`/missing-key failing open, and `blocked/`/`backlog/`
  being unenforced - is pre-existing code this diff did not touch and was not asked to fix (only the
  duplicate-glob and blocked/backlog findings even overlap this diff's lines, and both existed in the same
  shape before it). Recommend filing each as its own task, same granularity as T-0035..T-0044 already in the
  queue; not blocking this one on them.
