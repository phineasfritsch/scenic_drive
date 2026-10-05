---
id: T-0264
title: P-COST-01 binds the shipped /isochrone KILL and reserve-before-call tests, so the third upstream route is pinned like /plan and /loop
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-COST-01, P-COST-04, P-PRIV-05]
reviewer: null
depends_on: [T-0261, T-0262]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/lib/named-tests.json binds T-0262's shipped-route tests: /isochrone KILL=1 503 before the body is read (P-COST-01), reserve before the one request (P-COST-01), 1 request per call / 0 on a hit (P-COST-04), the 2-dp start refusal (P-PRIV-05); each pin's prose updated by APPENDING (never rewriting dated text) and its counts corrected"
  - "each new binding RED by a one-line mutant of src/isochrone.ts (KILL ignored on the shipped route; reserve after the fetch; a second fetch; a 3-dp start accepted) quoted in the Log, then green; run-named-tests.py for the three pins exits 0"
---
## Brief

T-0262's stillOpen 1 / rv2 recordable: P-COST-01's statement is 'KILL=1 -> 0 upstream for every route in the router
table'; T-0261 bound /plan and /loop; /isochrone shipped after it and is unbound.

## Log
- 2026-10-05T17:36:29Z filed by agent/claude-opus-5 (orchestrator) after PR #150 (T-0262) merged.
