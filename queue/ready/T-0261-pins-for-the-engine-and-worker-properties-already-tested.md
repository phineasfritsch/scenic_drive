---
id: T-0261
title: PINS rows for the properties the engine and Worker already test but no pin registers - P-SAFE-01, P-SAFE-04, P-PRIV-05, P-COST-01, P-COST-04, P-PROD-02 - each bound to the named tests, each seen red
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [pins/PINS.yaml, ops/lib/]
pins_affected: [P-SAFE-01, P-SAFE-04, P-PRIV-05, P-COST-01, P-COST-04, P-PROD-02]
reviewer: null
depends_on: [T-0248, T-0252, T-0253]
verify: [ops/test, ops/check-pins]
acceptance:
  - "pins/PINS.yaml gains one row per id with statement (the plan's own wording, plan Pins table), why_no_test_catches_it, anchor, runs_on: [linux], owner, added; each assertion runs the EXISTING tests that prove it by NAME (vitest -t / file filters under services/api, swift test --filter for Surprise/LambdaSearch suites) through one small ops/lib runner that FAILS if the named tests are missing, skipped or zero (a filter that matches nothing must be red, never a vacuous green)"
  - "each new row is seen RED by a one-line mutant of the shipping code it protects (e.g. quota reserved after the upstream call for P-COST-01, a 3-dp origin accepted for P-PRIV-05, the ceiling read from the scenic ETA for P-SAFE-04, a request beyond the cap for P-COST-04, a client custom_model touching road_access accepted for P-SAFE-01, the seed ignoring the date for P-PROD-02), quoted in the Log with the runner's output, then green; and once with the named test renamed (the runner refuses by name)"
  - "'bash ops/check-pins --source-only' (or CI's pins-source-only as the run of record on this box) prints the six ids ok; P-COST-03's VPS half stays unregistered and is named in why_no_test_catches_it of P-COST-01 as out of scope"
---
## Brief

T-0248 stillOpen 3, T-0252, T-0253 stillOpen 1 and T-0256: the Worker and the engine ship tests for six plan pins
(Pins table: P-SAFE-01 profile gates + Worker rejection of road_access/surface models; P-SAFE-04 budget ceiling;
P-PRIV-05 one coordinate, 2 dp; P-COST-01 quota before every VPS call and KILL=1 -> 0 upstream; P-COST-04 requests
per plan <= 12/3/12; P-PROD-02 Surprise reproducible per (user, day, seed) and >= 90% distinct) but pins/PINS.yaml
registers none of them, so ops/check-pins cannot say they hold and M6's exit (P-COST/P-PRIV green) has nothing to
read. Anchor on test names and shipping symbols, never comments (CLAUDE.md).

## Log
- 2026-10-05T14:46:01Z filed by agent/claude-opus-5 (orchestrator) after PR #144 (T-0253) merged.
