---
id: T-0335
title: /trip, /loop and the isochrone planner are honest when nothing pretty is reachable - score the route they would ship with routeScore.ts (T-0332) and refuse below 0.45, or rule in the Log why a planner is exempt
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, ops/lib/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-SAFE-04]
reviewer: null
depends_on: [T-0332]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0332 R6 (owner ruling) scoped the honest failure to POST /plan's fresh plans (reroutes exempt). tripPlanner.ts,
loopPlanner.ts and isochronePlanner.ts each ship a route without consulting RouteScore; grep of services/api/src for
routeScoreOf finds only scenicPlanner.ts. MEASURE FIRST: what each planner returns, which recorded fixtures each test
suite drives (and their RouteScore, via Tests/Fixtures/t0332/oracle.py's reading), and whether a loop or a surprise
destination should refuse or re-pick (a Surprise Me that answers "nothing pretty" may be worse than a re-roll within
the same request cap, P-COST-04). Then the acceptance: whole-answer equality through each handler, the population
MISSED before / CAUGHT after by test name.

## Log
- 2026-10-08T21:58:00Z filed by agent/claude-opus-5 (T-0332 owner) from T-0332 R6.
