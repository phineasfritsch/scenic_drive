---
id: T-0352
title: Eleven Worker mutation drivers refuse before mutating (STALE anchors, red baselines) - measure whether their populations still run, and make every one run green from its documented directory
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-10T02:46:21Z
lease_expires_at: 2026-10-10T08:46:21Z
worktree: .worktrees/T-0352
branch: task/T-0352
exclusive: []
touches: [services/api/test/mutate/, ops/lib/, pins/PINS.yaml]
pins_affected: [P-PROC-06]
reviewer: null
depends_on: [T-0347]
verify: [ops/check-pins]
acceptance:
  - "A1 MEASURE (quoted in the Log before code): each of the eleven drivers run with no --only from services/api AND from the repo root prints the same first refusal line; for every not-exactly-once anchor, whether its text occurs anywhere in src/ today and which commit staled it"
  - "A2 Every one of the 15 stale entries is re-anchored on today's source, keeping its id and its fault; `node test/mutate/<d>Mutants.mjs --only=<ids>` from services/api prints `baseline green` and `RESULT caught=k missed=0 trap=0 of k` with each re-anchored id CAUGHT by a named test, for all eight stale drivers; one of them is also run from the repo root with the same RESULT"
  - "A3 plan/loop/trip: each run ALONE from both cwds reaches `baseline green tests=N` (the T-0347 red was the box, ruled from the measurement); re-quoted on the final head"
  - "A4 ops/lib/check-mutate-anchors.py: a literal DRIVERS whitelist equal to the set of services/api/test/mutate/*Mutants.mjs (an unlisted driver or a listed-but-missing one refuses), a literal floor, and every MUTATIONS+EQUIVALENT anchor of every driver occurring exactly once in its own file today (every stale entry named, not the first); exit 0 green, 1 stale, 2 could not run. Seen RED on the pre-fix tree naming all 15 stale entries and RED on an unlisted driver, then GREEN"
  - "A5 P-PROC-06's assertion runs check-mutate-anchors.py; `python ops/lib/check-pins-yaml.py` exits 0"
  - "A6 Final head (after merging origin/main last): bare check-mutate-population, check-mutate-only, check-mutate-anchors, check-pins-yaml, `bash ops/lib/check-exec-bits`, `bash ops/queue-check` each exit 0; every touched file <= 300 lines (wc -l quoted)"
---
## Brief

T-0347's owner (PR #233 stillOpen 3) ran every `*Mutants.mjs` driver from the repo root while proving the `--only`
refusal and saw eight refuse with `STALE <name>: anchor occurs 0 times in src/...` (closures, config, crossing,
isochrone, quota, region, tier, vehicle) and three refuse with "baseline is not green" (plan, loop, trip). Nobody
established whether the drivers only run from `services/api` (a cwd assumption, harmless) or whether their mutation
tables went stale against `src/` (every mutant in them silently stopped being applied - a P-PROC-06 population that
counts entries it can no longer run).

MEASURE FIRST: run each of the eleven from `services/api` and from the repo root with no `--only`, quote the first
refusal line of each, and for every STALE line say whether the anchor text exists anywhere in `src/` today (moved,
renamed or deleted). Then rule per driver: cwd-only (make the driver resolve paths from its own file, so either cwd
works) or stale table (re-anchor each entry on today's source, each re-anchored entry shown CAUGHT by name). If any
population is stale, add a meta-check (in ops/lib, beside check-mutate-only) that every driver's anchors occur exactly
once in today's source, demonstrated red on a stale anchor then green.

## Log
- 2026-10-09T23:05:00Z filed by agent/claude-opus-5 (orchestrator) from T-0347 owner stillOpen 3 (PR #233).
- 2026-10-10T02:46:21Z claimed by agent/claude-opus-5; lease until 2026-10-10T08:46:21Z
- 2026-10-10T03:02:41Z MEASURE (A1), on a16d2a98, node_modules junctioned from a matching package-lock install.
  Each driver with no --only, first line, from services/api and from the repo root (identical in every row):
  closures `STALE plan-no-closures: anchor occurs 0 times in src/plan.ts`; config `STALE
  session-authenticated-stringify-unpause: anchor occurs 0 times in src/sessionIdentity.ts`; crossing `STALE
  plan-unchecked: anchor occurs 0 times in src/plan.ts`; isochrone `STALE cache-key-no-version: anchor occurs 0 times
  in src/reachCache.ts`; quota `STALE do-daily-inclusive: anchor occurs 0 times in src/QuotaCounter.ts`; region `STALE
  loop-gate-below-closures: anchor occurs 0 times in src/loop.ts`; tier `STALE plan-identify-unawaited: anchor occurs 0
  times in src/plan.ts`; vehicle `STALE plan-vehicle-key-dropped: anchor occurs 0 times in src/planRequest.ts`.
  plan / loop / trip, each ALONE (a wrapper killed the driver at `baseline green` and restored src; src clean after):
  plan `population mutations=68 (floor 68) equivalent=2 subjects=10 tests=10` then `baseline green tests=217` (both
  cwds); loop `mutations=47 (floor 47) equivalent=3` then `baseline green tests=57` (both); trip `mutations=103 (floor
  103) equivalent=5` then `baseline green tests=143` (both).
  Every anchor of all 17 drivers (MUTATIONS + EQUIVALENT) counted in its own file, not just the first STALE: 15 entries
  in 8 drivers occur 0 times, and NONE of the 15 texts occurs in any src/**/*.ts file today (`elsewhere=[]` for all):
  closures 3 (plan-no-closures, plan-no-hazard, plan-whole-set; staled by ac239f38 T-0319 2026-10-08); config 1
  (session-authenticated-stringify-unpause; 25ef1f31 T-0322 2026-10-08); crossing 2 (plan-unchecked ac239f38;
  trip-unchecked 2533714b T-0316 2026-10-07); isochrone 2 (cache-key-no-version, iso-hit-echoes-limit; a8fe74b4 T-0276
  2026-10-06); quota 3 (do-daily-inclusive, do-daily-step-2 35994a47 T-0279 2026-10-06; plan-deps-no-resolver
  ac239f38); region 2 (loop-gate-below-closures, trip-gate-below-closures; b1ec6d39 T-0333 2026-10-09); tier 1
  (plan-identify-unawaited ac239f38); vehicle 1 (plan-vehicle-key-dropped ac239f38). The other 9 drivers (plan, loop,
  trip, asn, assert, attest, ledger, siwa, telemetry): 0 not-exactly-once.
- 2026-10-10T03:02:41Z RULINGS before code.
  R1 cwd: NOT the defect. Every driver already resolves API from `import.meta.url` and the first line is identical from
  both cwds; no path change is made (the Brief's "cwd-only" branch is ruled out by the measurement).
  R2 stale tables: 8 populations have been unrunnable since 2026-10-06..09 - the driver refuses at the first STALE, so
  every entry in them, not only the 15, stopped being applied. Each of the 15 is re-anchored on today's equivalent code
  with its id and its fault kept (the code moved: reroute split plan.ts's planScenic call, closures hazard wraps the
  isochrone hit, reserveDaily takes `amount`, the session_rejected line sits between identify and closures, BODY_KEYS
  grew reroute/back_roads, the cache key grew closuresVersion, identifySession gained the IDENTITY_HEADERS arm).
  R3 plan/loop/trip: their baselines are green alone from both cwds today, so T-0347's "baseline is not green" was the
  box (its owner ran the drivers back to back with other vitest runs on the shared box); no code change.
  R4 meta-check scope: the 17 services/api/test/mutate/*Mutants.mjs drivers (one table shape: exported MUTATIONS and
  EQUIVALENT of {id, file, find}). The Python ops/mutate drivers already refuse a stale site at run time and have one
  table shape each; extending the meta-check to them is a separate task, not this one.
  R5 verification depth (faster-verification-in-rounds): the re-anchored entries are run by name with --only (which
  also proves each driver's baseline green); the full populations of the eight drivers are NOT re-run here (~800
  vitest runs on a shared box). Whether any OTHER entry of those eight went MISSED while the drivers could not run is
  stated as open in the PR, not claimed.
- 2026-10-10T03:22:21Z CHECK FIRST, then fix (A4). ops/lib/check-mutate-anchors.py written before any re-anchor and run
  on the pre-fix tree (a21cb8b3 + the new file): exit 1, every stale entry named - `STALE closures plan-no-closures`,
  `plan-no-hazard`, `plan-whole-set`, `STALE config session-authenticated-stringify-unpause`, `STALE crossing
  plan-unchecked`, `trip-unchecked`, `STALE isochrone cache-key-no-version`, `iso-hit-echoes-limit`, `STALE quota
  do-daily-inclusive`, `do-daily-step-2`, `plan-deps-no-resolver`, `STALE region loop-gate-below-closures`,
  `trip-gate-below-closures`, `STALE tier plan-identify-unawaited`, `STALE vehicle plan-vehicle-key-dropped` (each
  `anchor occurs 0 times in src/...`), last line `check-mutate-anchors: 17 drivers, 1263 anchors, 15 stale`.
  Whitelist arms: an untracked copy at services/api/test/mutate/zzzMutants.mjs -> exit 2 `driver(s) not in the DRIVERS
  whitelist: zzz; listed but not on disk: none: REFUSING`; vehicleMutants.mjs git-mv'd away -> exit 2 `... listed but
  not on disk: vehicle: REFUSING`; both restored. The counter reads bytes (not Python's newline-translating
  read_text), so it counts exactly what the driver's readFileSync sees.
  After the re-anchor (2508eb72): exit 0 `check-mutate-anchors: 17 drivers, 1263 anchors, 0 stale`.
- 2026-10-10T03:22:21Z RE-ANCHORED ENTRIES BY NAME (A2), each driver run alone with --only from services/api:
  closures `baseline green tests=738`, CAUGHT plan-no-closures, plan-no-hazard, plan-whole-set, `RESULT caught=3
  missed=0 trap=0 of 3`; config first run `REFUSING: the baseline is not green (loading the shipped worker leaves
  every global, intrinsic and prototype the /config answer runs on untouched)` - test/configAnswerPath.test.ts then
  passed alone (3 passed) and the driver re-run alone printed `baseline green tests=48`, CAUGHT
  session-authenticated-stringify-unpause, `RESULT caught=1 missed=0 trap=0 of 1` (ruled box: the same file, nothing
  changed between the runs); crossing `baseline green tests=274`, CAUGHT plan-unchecked, trip-unchecked, `RESULT
  caught=2 ... of 2`; isochrone `baseline green tests=28`, CAUGHT cache-key-no-version (its failures include `the cache
  key is the start at 2 dp, the minutes bucket, the UTC day and the graph ver...`), iso-hit-echoes-limit, `RESULT
  caught=2 ... of 2`; quota `baseline green tests=84`, CAUGHT do-daily-inclusive, do-daily-step-2,
  plan-deps-no-resolver, `RESULT caught=3 ... of 3`; region `baseline green tests=44`, CAUGHT loop-gate-below-closures,
  trip-gate-below-closures, `RESULT caught=2 ... of 2`; tier `baseline green tests=187`, CAUGHT plan-identify-unawaited,
  `RESULT caught=1 ... of 1`; vehicle `baseline green tests=5`, CAUGHT plan-vehicle-key-dropped, `RESULT caught=1
  missed=0 trap=0 of 1 (--only)` - from services/api AND from the repo root, identical.
  15 of 15 re-anchored entries CAUGHT; every one names a failing test.
