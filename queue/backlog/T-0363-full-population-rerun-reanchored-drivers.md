---
id: T-0363
title: The eight re-anchored Worker mutation populations (closures, config, crossing, isochrone, quota, region, tier, vehicle) run whole, and every MISSED entry they show after days of not running is closed or ruled EQUIVALENT with a witness
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/test/, services/api/test/mutate/, ops/lib/]
pins_affected: [P-PROC-06]
reviewer: null
depends_on: [T-0352]
verify: [ops/check-pins]
acceptance: []
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
