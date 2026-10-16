---
id: T-0363
title: The eight re-anchored Worker mutation populations (closures, config, crossing, isochrone, quota, region, tier, vehicle) run whole, and every MISSED entry they show after days of not running is closed or ruled EQUIVALENT with a witness
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T00:43:20Z
lease_expires_at: 2026-10-17T00:43:20Z
worktree: .worktrees/T-0363
branch: task/T-0363
exclusive: []
touches: [services/api/test/, services/api/test/mutate/, ops/lib/]
pins_affected: [P-PROC-06]
reviewer: agent/rv1-t0363
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
- 2026-10-16T02:58:33Z A2 isochrone whole (no --only), from services/api, alone: `population mutations=67 (floor 67) equivalent=1 subjects=8 tests=4` / `baseline green tests=28` / `RESULT caught=67 missed=0 trap=0 of 67` exit 0; MISSED/TRAP: none
- 2026-10-16T03:10:57Z A2 quota whole (no --only), from services/api, alone: `population mutations=58 (floor 58) equivalent=1 subjects=9 tests=5` / `baseline green tests=84` / `RESULT caught=58 missed=0 trap=0 of 58` exit 0; MISSED/TRAP: none
- 2026-10-16T03:31:11Z A2 region whole (no --only), from services/api, alone: `population mutations=68 (floor 68) equivalent=2 subjects=9 tests=8` / `baseline green tests=44` / `RESULT caught=67 missed=1 trap=0 of 68` exit 1; MISSED/TRAP: MISSED malformed-bearer-falls-to-header
- 2026-10-16T03:39:28Z A2 tier whole (no --only), from services/api, alone: `population mutations=26 (floor 26) equivalent=1 subjects=7 tests=5` / `baseline green tests=187` / `RESULT caught=26 missed=0 trap=0 of 26` exit 0; MISSED/TRAP: none
- 2026-10-16T03:43:17Z A2 vehicle whole (no --only), from services/api, alone: `population mutations=32 (floor 32) equivalent=1 subjects=4 tests=2` / `baseline green tests=5` / `RESULT caught=32 missed=0 trap=0 of 32` exit 0; MISSED/TRAP: none
- 2026-10-16T03:47:12Z A2 summary: 8 drivers run whole, 527 mutations, 526 CAUGHT, 1 MISSED (region
  malformed-bearer-falls-to-header), 0 TRAP; no baseline went red, so no re-run for load was needed.
- 2026-10-16T03:47:12Z A3 region malformed-bearer-falls-to-header: RULED EQUIVALENT - moved from MUTATIONS to regionMutants.mjs's
  EQUIVALENT table with its witness field (the mutant's regex is BEARER's language; since T-0322 B1, 25ef1f31,
  identifySession answers a non-matching authorization as null on every arm and identifyCaller maps SESSION_REJECTED
  to the unidentified bucket, so waitlist's userId is identical for every input). It went MISSED when T-0322 B1 made
  its fault the spec, i.e. while the driver could not run. Per R4 MIN_MUTATIONS 68 -> 67 in the same commit.
  `node test/mutate/regionMutants.mjs --prove-floor`: empty table / one short (66 below 67) / servedRegion
  unmutated / a new subject with none each REFUSED, `prove-floor real population: quiet`, rc=0.
- 2026-10-16T04:00:19Z A3 region re-run WHOLE on 1ec1926e (after the move), from services/api, alone: `population mutations=67
  (floor 67) equivalent=3 subjects=9 tests=8` / `baseline green tests=44` / `RESULT caught=67 missed=0 trap=0 of
  67` exit 0.
- 2026-10-16T04:02:09Z merged origin/main (9171fa71) as 062bb5f5. R6 (ruled on the merge): main's T-0362 (PR #250) changed
  src/plan.ts, planSweep.ts, search.ts, searchPlaces.ts and re-anchored region plan-gate-below-resolve /
  plan-gate-below-closures and tier plan-identify-unawaited; the A2 whole runs were on bf789086. On the merged head
  every entry of the eight drivers whose file is src/plan.ts, planSweep.ts, search.ts or searchPlaces.ts (18:
  closures 6, config 2, crossing 2, quota 2, region 5, tier 1; isochrone and vehicle 0) is re-run by --only
  (faster-verification-in-rounds); the other 509 entries' files are byte-identical to bf789086's. Bare gates on
  062bb5f5: check-mutate-population `P-PROC-06: every added module is covered or allowlisted; the floor of 165
  holds` rc=0; check-mutate-only `MUTATE-ONLY OK: 219 of 219 driver runs refused with exit 64 (59 drivers, ...)`
  rc=0; check-mutate-anchors `17 drivers, 1263 anchors, 0 stale` / `cwd arm: 17 drivers run from the repo root, 17
  reached their population line` rc=0; check-pins-yaml `PINS-YAML ok pins=50 fields=403` rc=0; check-exec-bits
  `P-OPS-01: 225 files, 23 required present, all modes correct` rc=0; queue-check `QUEUE OK (359 tasks)` rc=0.
- 2026-10-16T04:04:02Z merged head 3ae4da2f: closures --only=plan-no-closures,plan-no-hazard,plan-closures-before-kill,plan-closures-twice,plan-dropped-unreported,plan-whole-set from services/api: `baseline green tests=738` / `RESULT caught=6 missed=0 trap=0 of 6` exit 0; MISSED/TRAP: none
- 2026-10-16T04:04:43Z merged head 3ae4da2f: config --only=plan-load-intrinsic-patch-unpause,plan-request-time-stringify-unpause from services/api: `baseline green tests=48` / `RESULT caught=2 missed=0 trap=0 of 2` exit 0; MISSED/TRAP: none
- 2026-10-16T04:05:35Z merged head 3ae4da2f: crossing --only=plan-unchecked,plan-crosses-unreported from services/api: `baseline green tests=274` / `RESULT caught=2 missed=0 trap=0 of 2` exit 0; MISSED/TRAP: none
- 2026-10-16T04:06:30Z merged head 3ae4da2f: quota --only=plan-resolver-error-404,plan-deps-no-resolver from services/api: `baseline green tests=84` / `RESULT caught=2 missed=0 trap=0 of 2` exit 0; MISSED/TRAP: none
- 2026-10-16T04:09:04Z merged head 3ae4da2f: region --only=plan-gate-dropped,plan-gate-400,plan-gate-below-deps,plan-gate-below-resolve,plan-gate-below-closures from services/api: `baseline green tests=44` / `RESULT caught=5 missed=0 trap=0 of 5` exit 0; MISSED/TRAP: none
- 2026-10-16T04:09:31Z merged head 3ae4da2f: tier --only=plan-identify-unawaited from services/api: `baseline green tests=187` / `RESULT caught=1 missed=0 trap=0 of 1` exit 0; MISSED/TRAP: none
- 2026-10-16T04:20:23Z ACCEPTANCE re-quoted (pre-review). A1: measured above (527 MUTATIONS / 13 EQUIVALENT on bf789086). A2: all
  eight run whole, alone, from services/api - closures 133/133, config 84/84, crossing 59/59, isochrone 67/67, quota
  58/58, region 67 of 68 (1 MISSED), tier 26/26, vehicle 32/32 (RESULT lines quoted above as they landed); no
  baseline red. A3: the one MISSED (region malformed-bearer-falls-to-header) moved to EQUIVALENT with a witness
  field, floor 68 -> 67, `--prove-floor` rc=0, region re-run whole `RESULT caught=67 missed=0 trap=0 of 67`; on the
  merged head the 18 entries anchored in files main changed all CAUGHT (6+2+2+2+5+1 of 18). A4: cwd arm red
  (`CWD tier: ... ENOENT`, 16 of 17, rc=1) then green (17 of 17, rc=0), git status unchanged; green again on the
  merged head. A5: no test .ts file touched (the driver baselines above are the touched suites, all green); bare
  gates on 062bb5f5 all rc=0 (quoted above); wc -l: ops/lib/check-mutate-anchors.py 191,
  services/api/test/mutate/regionMutants.mjs 258, this file 108 before this entry - each <= 300.
- 2026-10-16T04:41:46Z review PASS by agent/rv1-t0363 (round 1, PR #248) on b1e62d3a, detached worktree
  .worktrees/rv1-t0363. Acceptance block unchanged since 2fe49e42 (before code fad911d1). No new test file, so no
  MISSED-by-name re-application; the one MISSED went EQUIVALENT. Witness checked by hand against sessionIdentity.ts:
  BEARER and the mutant regex accept the same language; a non-matching present authorization goes to legacy() with no
  secret or with IDENTITY_HEADERS "1", and to SESSION_REJECTED -> {unidentified, anon} with the flag closed, which is
  what null yields on each arm; only .userId is read. Applying malformed-bearer-falls-to-header by hand: waitlist +
  waitlistDedupe `Tests 10 passed (10)` (still MISSED, as ruled). Own mutant in waitlist.ts's day bucket
  (`.slice(0, 10)` -> `.slice(0, 13)` on handleWaitlist's day): `Tests 5 failed | 10 passed (15)`, RED. cwd arm with
  vehicleMutants.mjs's API set to process.cwd(): `0 stale` / `CWD vehicle: ... --only=vehicle-enables-rv never
  printed its population line - exit 1, Error: ENOENT ... rv1-t0363\src\vehicle.ts` / `16 reached`, rc=1; reverted,
  green. Bare gates on b1e62d3a: check-mutate-population rc=0, check-mutate-only `MUTATE-ONLY OK: 219 of 219` rc=0,
  check-pins-yaml `pins=50 fields=403` rc=0, check-exec-bits rc=0, queue-check `QUEUE OK (359 tasks)` rc=0,
  check-mutate-anchors `1263 anchors, 0 stale` / `17 reached` rc=0, git status empty. gh pr checks: core pass,
  pins-source-only pass. merge-base --is-ancestor origin/main (9171fa71) origin/task/T-0363 rc=0.
