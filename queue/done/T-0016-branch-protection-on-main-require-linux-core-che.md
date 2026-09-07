---
id: T-0016
title: Branch protection on main: require linux-core checks before merge
state: done
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T09:11:42Z
lease_expires_at: 2026-09-07T12:11:42Z
worktree: ../wt/T-0016
branch: task/T-0016
exclusive: []
touches: [.github/, ops/merge, queue/README.md]
pins_affected: []
reviewer: agent/reviewer-7
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

main was broken on 2026-09-07 by merging PR #6 while `gh` reported mergeStateStatus=UNSTABLE. The intended fix
was GitHub branch protection requiring the linux-core checks.

THAT IS NOT AVAILABLE: both `branches/main/protection` and `rulesets` return 403 "Upgrade to GitHub Pro or make
this repository public" - the repo is private on a free personal plan. Verified directly against the API.

So the gate lives in the repo instead: `ops/merge <pr> [--wait]` refuses unless
  (1) the PR's queue task is in queue/done/ on the PR head (a reviewer signed it off),
  (2) every check run has concluded and none failed,
  (3) mergeStateStatus is CLEAN,
  (4) at least one check actually reported (a PR with no CI at all is refused, not waved through).

HONEST LIMITATION, stated in the script itself: this is client-side and bypassable with `gh pr merge`. It makes
the safe path the easy path. Server-side enforcement needs GitHub Pro (~$4/mo) or a public repo - a decision for
the owner, recorded here rather than silently dropped.

## Log
- 2026-09-07T07:05:00Z raised backlog -> ready: main went red on 2026-09-07 because a PR was merged while checks were UNSTABLE. Until this exists, nothing mechanically stops that.
- 2026-09-07T09:11:42Z claimed by agent/claude-opus-5; lease until 2026-09-07T12:11:42Z
- 2026-09-07T09:30:00Z FINDING that changes the task: GitHub branch protection is NOT available here. `gh api repos/phineasfritsch/scenic_drive/branches/main/protection` and `.../rulesets` both return 403 "Upgrade to GitHub Pro or make this repository public". Private repo, free personal plan. Recorded rather than silently dropped; the owner's options are Pro (~$4/mo), a public repo, or the client-side gate built here.
- 2026-09-07T09:30:00Z GREEN: ops/merge 11 --dry-run with checks finished -> "checks total=2 pending=0 failed=[none] mergeState=CLEAN" then "DRY RUN: every gate passed", exit 0.
- 2026-09-07T09:30:00Z RED 1 (review gate): ops/merge 9 -> "T-0017 is not in queue/done/ on task/T-0017 - a reviewer has not signed it off", exit 1.
- 2026-09-07T09:30:00Z RED 2 (THE outage case): throwaway PR #11 on tmp/merge-probe, run while CI was still going -> "checks total=2 pending=2 failed=[none] mergeState=UNSTABLE" then "MERGE REFUSED: 2 check(s) still running", exit 1. UNSTABLE is exactly the state I merged PR #6 in when main broke.
- 2026-09-07T09:30:00Z RED 3 (bad input): nonexistent PR -> "MERGE REFUSED: PR 999 does not exist or is not readable", exit 1; no args -> usage, exit 2; unknown option -> exit 2.
- 2026-09-07T09:30:00Z SELF-CAUGHT during the demos: the first version did not check `gh pr view`'s output, so a nonexistent PR fell through the review gate ("branch names no task") before failing later for the wrong reason. Fixed to fail fast.
- 2026-09-07T09:30:00Z Added --dry-run so the green path is provable without merging a throwaway commit into main. Probe PR #11 closed, tmp/merge-probe deleted locally and on origin, worktree removed.
- 2026-09-07T09:30:00Z queue/README.md step 7 now mandates ops/merge over gh pr merge and states the bypassability limitation.
- 2026-09-07T09:30:00Z moved to review/, reviewer agent/reviewer-7
- 2026-09-07T10:05:00Z reviewed by agent/reviewer-7: PASS — re-ran everything, tried to break it, could not.
  (1) CENTRAL CLAIM re-verified directly: `gh api repos/phineasfritsch/scenic_drive/branches/main/protection`
  and `.../rulesets` both HTTP 403 `{"message":"Upgrade to GitHub Pro or make this repository public to enable
  this feature.","status":"403"}` - matches the owner's finding exactly; premise is real, not a workaround for
  inconvenience.
  (2a) `ops/merge 9` (task/T-0017, still review/) -> "T-0017 is not in queue/done/ on task/T-0017 - a reviewer
  has not signed it off", exit 1.
  (2b) `ops/merge 999` -> "MERGE REFUSED: PR 999 does not exist or is not readable", exit 1. `ops/merge` (no
  args) -> usage, exit 2. `ops/merge 9 --bogus` -> "unknown option: --bogus", exit 2.
  (2c) THE outage case, reproduced live: pushed throwaway branch tmp/merge-outage-probe (no T-nnnn, off
  origin/main 6b811ec) as PR #12, ran `ops/merge 12` while CI was mid-flight -> "checks total=2 pending=2
  failed=[none] mergeState=UNSTABLE" -> "MERGE REFUSED: 2 check(s) still running (use --wait to poll)", exit 1.
  This is exactly the state PR #6 was merged in when main broke. After both checks passed, `ops/merge 12
  --dry-run` -> "checks total=2 pending=0 failed=[none] mergeState=CLEAN" -> "DRY RUN: every gate passed", exit
  0. PR #12 closed, branch deleted local+origin, worktree removed.
  (2d) Read the --wait loop: attempt cap 40, `sleep 30` between polls, breaks to refusal (exit 1) once
  `attempt` stops being `-lt 40` — bounded at ~19.5 min, cannot spin forever.
  (3a) total=0 IS reachable after the loop and DOES exit 1, constructed for real: on a second probe PR (#13,
  branch tmp/merge-nochecks-probe) I cancelled the in-flight workflow run (`gh run cancel`) then deleted it
  (`gh api -X DELETE .../actions/runs/<id>`), leaving `statusCheckRollup` empty. `ops/merge 13` then reported
  "checks total=0 pending=0 failed=[none] mergeState=CLEAN" -> "MERGE REFUSED: no checks reported at all - CI
  did not run for this PR", exit 1 - the total>0 gate holds even when mergeStateStatus itself says CLEAN.
  PR #13 closed, branch deleted local+origin, worktree removed.
  (3b) Review gate (`ops/merge:34-43`) is filename-only via the contents API (`grep -q "^$task-"` against
  `queue/done/` listing) - it does not read frontmatter. But `ops/lib/queue.py:140-146` (invoked as the
  `queue-check` step of the `core` job in `.github/workflows/linux-core.yml`, which runs unconditionally on
  every `pull_request`, no path filter) rejects any file whose `state:` field doesn't match its directory or
  whose `reviewer:` is empty/self - so a forged `queue/done/T-xxxx-*.md` with `state: review` or missing
  reviewer would fail that CI check, which ops/merge's `failed` gate catches. Filename-only is sufficient given
  that defense in depth; content-only-in-CI is intentional, not an oversight.
  (3c) `mergeStateStatus` case only accepts CLEAN|HAS_HOOKS; everything else (including UNKNOWN, which the
  outage-case run also showed as an intermediate value before settling to UNSTABLE) falls to the default branch
  and refuses. Fails closed correctly.
  (3d) Verified empirically (standalone repro, not the live script) that when a `gh` call inside a `$(...)`
  capture fails and yields empty output, the downstream python `json.loads` raises, prints nothing, and the
  empty result flows into `[[ "$pending" -gt 0 ]]` / `[[ "$total" -gt 0 ]]` as a failed test rather than a
  script crash (no `-e`, so it doesn't abort) - the `if` branch for "still pending" is skipped, execution falls
  through to the `total -gt 0 ||` refusal, which fires. A failing `gh` call ends in "MERGE REFUSED: no checks
  reported at all", never a silent pass.
  (4) `bash ops/test` exit 0, `TESTS linux=50/50 ios=skipped failed=0 skipped=0`. `bash ops/check-pins` exit 0,
  `PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux`. `bash ops/queue-check` exit 0, `QUEUE OK (18
  tasks)`.
  (5) `git ls-files -s ops/merge` -> `100755`. queue/README.md steps renumbered 1-9 with no gaps or dupes; new
  step 7 documents `ops/merge` and states the client-side/bypassable limitation honestly (does not imply the
  hole is closed).
  One non-blocking observation, not grounds for FAIL: the review gate is skipped outright for any branch whose
  name has no `T-nnnn` (visibly logged each time - "branch X names no task; skipping the review gate" - and
  inherent to a task-branch-scoped review model, not a hidden bypass), and queue/README.md step 7's summary
  ("It refuses unless the task is in done/ on the PR head...") doesn't call out that this arm is conditional on
  the branch naming a task. Since the CI-green / mergeState=CLEAN / total>0 gates (the ones that actually
  address the 2026-09-07 outage) apply unconditionally regardless of branch name, this does not undermine the
  task's stated purpose. Suggested follow-up for whoever picks it up next: tighten the README wording, or make
  ops/merge refuse non-`task/T-nnnn` branches by default with an explicit override flag.
  All 3 probe PRs/branches/worktrees created during this review (#12 tmp/merge-outage-probe, #13
  tmp/merge-nochecks-probe) are closed/deleted/removed; `git status --short` in the T-0016 worktree is clean.
