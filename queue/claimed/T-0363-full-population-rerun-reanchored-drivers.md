---
id: T-0363
title: The eight re-anchored Worker mutation populations (closures, config, crossing, isochrone, quota, region, tier, vehicle) run whole, and every MISSED entry they show after days of not running is closed or ruled EQUIVALENT with a witness
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T00:43:20Z
lease_expires_at: 2026-10-17T00:43:20Z
worktree: .worktrees/T-0363
branch: task/T-0363
exclusive: []
touches: [services/api/test/, services/api/test/mutate/, ops/lib/]
pins_affected: [P-PROC-06]
reviewer: null
depends_on: [T-0352]
verify: [ops/check-pins]
acceptance:
  - "A1 MEASURE (quoted in the Log before code): the eight drivers' populations on the branch base - MUTATIONS, EQUIVALENT and MIN_MUTATIONS each, imported from the driver's own exports"
  - "A2 Each of closures, config, crossing, isochrone, quota, region, tier, vehicle run WHOLE (no --only), alone on the box, from services/api: `baseline green tests=N` and its `RESULT caught=k missed=m trap=t of n` line quoted into the Log as it lands (a red baseline under load re-run alone and said so)"
  - "A3 Every MISSED or TRAP entry of A2 is closed: either a test under services/api/test/ that catches it by name (`--only=<id>` MISSED before the test, CAUGHT after, both RESULT lines quoted) or the entry moved to its driver's EQUIVALENT table with a witness field naming why no test can tell it apart (never prose in this file); the driver's floor arms still pass (`--prove-floor` exit 0)"
  - "A4 ops/lib/check-mutate-anchors.py gains a cwd arm: every whitelisted driver is run from the REPO ROOT with `--only=<its first MUTATIONS id>` and must print its `population mutations=` line (printed only after the driver has read every anchored file through its own path resolution and checked src/ clean), the process tree killed there before any baseline or mutant; a driver that does not reach the line is named and the check exits 1. Seen RED with a cwd-relative API (`process.cwd()`) applied to one driver, naming that driver, then GREEN; the tree's git status is identical before and after"
  - "A5 Final head (after merging origin/main last): every test file touched passes under vitest; bare check-mutate-population, check-mutate-only, check-mutate-anchors, check-pins-yaml, `bash ops/lib/check-exec-bits`, `bash ops/queue-check` each exit 0; every touched file <= 300 lines (wc -l quoted)"
---
## Brief

T-0352 (PR #240) found that 15 entries across eight `*Mutants.mjs` drivers had gone stale between 2026-10-06 and
2026-10-09, and that each driver stops at its first stale entry, so none of those eight populations (about 470
entries) was applied for one to four days. T-0352 re-anchored the 15 and ran only those by name (owner stillOpen 1).
Whether any OTHER entry turned MISSED while its driver could not run is unmeasured.

Run each of the eight drivers whole, one at a time, alone on the box (a red baseline under load is environment:
re-run alone and say so). For every MISSED entry: add the test that catches it by name (MISSED before, CAUGHT after
with `--only`), or rule it EQUIVALENT in the population with a witness, never prose (CLAUDE.md). Also from
fm-t0352: a driver regressed to cwd-relative paths is caught only by running it from the repo root - add one arm to
check-mutate-anchors (or check-mutate-only) that runs one `--only` per driver from the repo root and requires the
driver to find its own files, shown red with that mutant then green.

## Log
- 2026-10-10T05:10:00Z filed by agent/claude-opus-5 (orchestrator) from T-0352 owner stillOpen 1 and fm-t0352's
  recordable.
- 2026-10-10T05:52:32Z renumbered T-0362 -> T-0363 by agent/claude-opus-5 (orchestrator): task/T-0359 filed T-0362 (plan-sheet address search wiring) concurrently.
- 2026-10-16T00:43:20Z claimed by agent/claude-opus-5; lease until 2026-10-17T00:43:20Z
- 2026-10-16T00:46:26Z A1 MEASURE on bf789086 (node import of each driver's MUTATIONS / EQUIVALENT / MIN_MUTATIONS):
  closures 133/1/133, config 84/1/84, crossing 59/5/59, isochrone 67/1/67, quota 58/1/58, region 68/2/68, tier
  26/1/26, vehicle 32/1/32 - 527 MUTATIONS and 13 EQUIVALENT in all (every table sits exactly at its floor).
- 2026-10-16T00:46:26Z RULINGS before code.
  R1 population: the Brief's "about 470 entries" is stale; the measured population is 527 mutations (A1) and A2/A3
  range over those 527.
  R2 cwd arm placement: check-mutate-anchors.py, not check-mutate-only.py - it already whitelists the 17 drivers and
  imports their tables, so `--only=<first id>` comes from the driver's own export. check-mutate-only's probes already
  run from the repo root, but every one is refused by onlyIds before any file is read, so they cannot see a
  cwd-relative path. The arm covers all 17 drivers, not only the eight (the Brief says one per driver).
  R3 cwd arm depth: it stops at the `population mutations=` line. Every driver prints it after the STALE pass (which
  reads every anchored src file via join(API, file)) and after `git status -- src` with cwd API, and before the
  baseline; killing the tree there means the gate never runs vitest and never mutates. What it does NOT see: the
  vitest child's cwd and TESTS paths (spawned with cwd API) - those are exercised only by a run that reaches the
  baseline, i.e. A2. Recorded, not closed here.
  R4 floors: an entry ruled EQUIVALENT leaves MUTATIONS below its literal MIN_MUTATIONS; the floor is then lowered by
  exactly the number moved, in the same commit, and the move is named in the Log.
  R5 environment: drivers run one at a time, nothing else of mine on the box; a red baseline is re-run alone first.
- 2026-10-16T00:59:45Z A4 cwd arm (fad911d1), demonstrated in a throwaway detached worktree of fad911d1 (.worktrees/T-0363-cwd, no
  node_modules, so no driver there could start vitest while this worktree's A2 chain runs). GREEN:
  `check-mutate-anchors: 17 drivers, 1263 anchors, 0 stale` / `check-mutate-anchors: cwd arm: 17 drivers run from
  the repo root, 17 reached their population line` rc=0, git status empty. RED with tierMutants.mjs's API set to
  `process.cwd()`: `check-mutate-anchors: 17 drivers, 1263 anchors, 0 stale` (the anchor arm cannot see it) /
  `CWD tier: run from the repo root with --only=tier-case-sensitive never printed its population line - exit 1,
  Error: ENOENT: no such file or directory, open '...\.worktrees\T-0363-cwd\src\accountTier.ts'` / `cwd arm: 17
  drivers run from the repo root, 16 reached their population line` rc=1; the same mutant run from services/api
  printed `population mutations=26 (floor 26) equivalent=1 subjects=7 tests=5 ONLY=1` (it works from there, which
  is why only the repo-root run sees it). Mutant reverted with git checkout: GREEN again, 17 of 17, rc=0, git status
  empty.
- 2026-10-16T01:51:37Z A2 closures whole (no --only), from services/api, alone: `population mutations=133 (floor 133) equivalent=1 subjects=14 tests=7` / `baseline green tests=738` / `RESULT caught=133 missed=0 trap=0 of 133` exit 0; MISSED/TRAP: none
- 2026-10-16T02:20:00Z A2 config whole (no --only), from services/api, alone: `population mutations=84 (floor 84) equivalent=1 subjects=2 tests=10` / `baseline green tests=48` / `RESULT caught=84 missed=0 trap=0 of 84` exit 0; MISSED/TRAP: none
- 2026-10-16T02:44:35Z A2 crossing whole (no --only), from services/api, alone: `population mutations=59 (floor 59) equivalent=5 subjects=9 tests=6` / `baseline green tests=274` / `RESULT caught=59 missed=0 trap=0 of 59` exit 0; MISSED/TRAP: none
