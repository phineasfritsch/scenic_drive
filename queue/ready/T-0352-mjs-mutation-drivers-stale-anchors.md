---
id: T-0352
title: Eleven Worker mutation drivers refuse before mutating (STALE anchors, red baselines) - measure whether their populations still run, and make every one run green from its documented directory
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/test/mutate/, ops/lib/, pins/PINS.yaml]
pins_affected: [P-PROC-06]
reviewer: null
depends_on: [T-0347]
verify: [ops/check-pins]
acceptance: []
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
