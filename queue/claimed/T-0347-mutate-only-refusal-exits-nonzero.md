---
id: T-0347
title: Every ops/mutate driver's `--only` refusal ("names no entry of this population") exits non-zero, so a typo'd range (`--only 49-55`) can never read as a pass
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T19:46:46Z
lease_expires_at: 2026-10-10T03:46:46Z
worktree: .worktrees/T-0347
branch: task/T-0347
exclusive: []
touches: [ops/mutate/, ops/lib/, services/api/test/mutate/, pins/PINS.yaml]
pins_affected: [P-PROC-06]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "MEASURE first: every driver under ops/mutate/ (and services/api/test/mutate/*.mjs) and what each does on `--only` with an unparseable or empty selection (exit code, message); quote the table"
  - "Every driver exits non-zero (a distinct refusal code, ruled) when `--only` names no entry or does not parse; ranges either parse as ranges everywhere or are refused everywhere (ruled); one shared parser where the drivers already share code"
  - "A meta-check under ops/lib runs each driver with `--only 999999` and `--only 1-2x` and refuses unless every one exits non-zero, seen red (one driver reverted) then green"
---
## Brief

rv1-t0342 recordable 2 (PR #229): `ops/mutate/plansheet.py --only 49-55` prints "REFUSING TO RUN: --only names no
entry of this population" and still exits 0, so a range typo looks like a pass when only the exit code is read
(memory pipe-swallows-gate-exit-status is the same failure shape).

## Log
- 2026-10-09T17:29:06Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0342 recordable 2.
- 2026-10-09T19:46:46Z claimed by agent/claude-opus-5; lease until 2026-10-10T03:46:46Z
- 2026-10-09T19:59:02Z MEASURE (acceptance 1), on b048be30, by agent/claude-opus-5. Population: the 38 drivers of
  ops/lib/mutate_population_table.py DRIVERS plus the 17 services/api/test/mutate/*Mutants.mjs. EXECUTED only where
  the code reaches the `--only` decision before any build or mutation (.build-t0347/measure.py, run from the repo
  root, 2026-10-09T19:56:03Z); the rest are read from source and marked static, because running them would start a
  whole-population run.
  | driver(s) | `--only 999999` / `--only 1-2x` / `--only 49-55` | exit | line |
  |---|---|---|---|
  | accounttoken corpusfetch corpusota drive hazardcopy ledger loopsheet onboarding plansheet saveddrive savedlist segmentgeometry session shownhistory surprise traffic tripsheet (17, one shared `select` shape) | all three | 2 | `REFUSING TO RUN: --only names no entry of this population` |
  | autopsy.py | all three | 2 | `REFUSING: --only names no entry: 999999` (resp. `1-2x`, `49-55`) |
  | fallback.py, placeallow.py (argparse, substring) | all three | 1 | `--only matched nothing` (stderr) |
  | plan.py (substring) | static, line 256 | - | `selected = []` is never refused: the run goes on to build + baseline over zero mutations |
  | straightline.py, telemetry.py | static, lines 138/141 | - | read only `--only=`; `--only 999999` is IGNORED and the whole population runs; `--only=1-2x` is `int()` -> traceback exit 1; `--only=999999` runs zero mutations as a "PARTIAL RUN" |
  | budget extractadapter gates geometry guidance handoff hazards menu normalise retrace roadtrip routescore scenic_tags segmentscore surfacecoverage (15, no `--only` at all) | static | - | the flag is IGNORED and the whole population runs |
  | asn assert attest ledger siwa telemetry Mutants.mjs | `--only=999999`, `--only=1-2x` | 2 | `REFUSING: unknown --only id(s) 999999` |
  | closures config crossing isochrone quota region tier vehicle Mutants.mjs | `--only=999999`, `--only=1-2x` | 2 | `STALE <id>: anchor occurs 0 times in src/...` - an EARLIER gate decided; `--only` was never reached |
  | plan loop trip Mutants.mjs | `--only=999999` (plan), `--only 999999`/`1-2x` (loop, trip) | 2 | `REFUSING: the baseline is not green ()` - vitest ran first; `--only` never reached |
  | the 15 `--only=` mjs drivers | `--only 999999` (space form), static | - | IGNORED (`argv.find(a => a.startsWith("--only="))`); the whole population runs |
  RULINGS (before code). R1 Brief vs reality: `plansheet.py --only 49-55` exits 2 on b048be30, not 0 - the filed
  symptom does not reproduce (most likely an exit status read through a pipe; memory pipe-swallows-gate-exit-status).
  The fail-open shapes that DO exist are the table's: drivers that ignore a spelling and run the whole or a zero
  population (plan.py, straightline, telemetry, the 15 no-`--only` drivers, the 15 `--only=` mjs drivers), a
  partial miss passing (`--only 1,49-55` runs 1 and silently drops 49-55 in the 17 `select` drivers), and exit 2
  shared with every other refusal (floor, dirty tree, baseline, STALE), so the status cannot tell a typo from a
  broken baseline. The task proceeds on those. R2 the refusal code is 64 (sysexits EX_USAGE); no driver returns 64
  today (grep). The meta-check requires exactly 64 AND a `REFUSING TO RUN: ` line - stricter than "non-zero",
  because 2 is already non-zero and would make the red demonstration vacuous. R3 ranges are REFUSED everywhere: a
  token is an id (exact; a name fragment in fallback/placeallow/plan, whose populations are keyed by name text),
  never a range, so `49-55` is one unknown id; EVERY token must select at least one entry. R4 `--only A,B` and
  `--only=A,B` are both accepted everywhere, repeatable; a missing value, an empty token or any other `--only*`
  flag refuses 64; the parse is the FIRST statement of main, before floors, STALE anchors, baseline or build. R5 a
  driver with no `--only` refuses the flag (64) rather than ignoring it and running the whole population. R6 one
  parser per language: ops/mutate/mutate_only.py (every Python driver runs with ops/mutate on sys.path) and
  services/api/test/mutate/onlyIds.mjs (the mjs drivers share no code today - node: builtins only - so a shared
  module replaces five divergent inline shapes rather than adding a sixth). R7 touches widened by the owner to
  services/api/test/mutate/ (acceptance 2 and 3 name those drivers) and pins/PINS.yaml (P-PROC-06's assertion
  runs the meta-check; a check no pin runs is not enforced). R8 the meta-check's population is DRIVERS (whitelist,
  floor 38) plus `*Mutants.mjs` (glob, floor 17); it refuses if the tree's status changes during its run.
- 2026-10-09T20:25:23Z BUILT by agent/claude-opus-5. ops/mutate/mutate_only.py (`select_only`, `refuse_unsupported`,
  EXIT_ONLY_REFUSED = 64) and services/api/test/mutate/onlyIds.mjs (`onlyIds`) are the two parsers; all 38 DRIVERS
  and 17 mjs drivers call them as the first statement of main (the 15 no-`--only` Python drivers in their
  `__main__` block, before main). fallback/placeallow also get `allow_abbrev=False`, so argparse cannot take `--onl`
  as `--only` behind the parser's back. autopsy/fallback/placeallow keep each `--only` value whole (`split=False`):
  two autopsy entry names contain a comma. ops/lib/check-mutate-only.py is the meta-check, appended to P-PROC-06's
  assertion; besides the 110 driver runs it runs in-process parser controls (a real id, both spellings, no
  `--only`, a whole-value fragment) that must NOT refuse, so a parser refusing everything is not green.
  SEEN RED, one driver reverted at a time (`git show HEAD:<driver> > <driver>`, the fixed file kept aside and
  copied back, cmp-checked): 2026-10-09T20:11:54Z ops/mutate/plansheet.py reverted ->
  `NOT REFUSED: ops/mutate/plansheet.py --only 999999: exit 2 (need 64) - REFUSING TO RUN: --only names no entry of
  this population` (and the same for `--only 1-2x`), `MUTATE-ONLY FAILED: 108 of 110 driver runs refused with exit
  64 (55 drivers x 2 probes)`, exit 1; 2026-10-09T20:14:16Z services/api/test/mutate/vehicleMutants.mjs reverted ->
  `NOT REFUSED: services/api/test/mutate/vehicleMutants.mjs --only 999999: exit 2 (need 64) - STALE
  plan-vehicle-key-dropped: anchor occurs 0 times in src/planRequest.ts` (x2), `MUTATE-ONLY FAILED: 108 of 110`,
  exit 1. GREEN restored: `MUTATE-ONLY OK: 110 of 110 driver runs refused with exit 64 (55 drivers x 2 probes)`,
  exit 0. check-mutate-population.py exit 0 (`38 populations ... 0 added by this branch`); check-exec-bits
  `P-OPS-01: 202 files, 23 required present, all modes correct`.
  FINDING, out of scope, for the orchestrator: run from the repo root, 8 mjs drivers (closures config crossing
  isochrone quota region tier vehicle) refuse `STALE <id>: anchor occurs 0 times in src/...` and plan/loop/trip
  report a red baseline - not established here whether that is a cwd-relative read (the drivers may expect
  cwd services/api) or tables stale against src; it no longer decides an `--only` typo, which now refuses first.
