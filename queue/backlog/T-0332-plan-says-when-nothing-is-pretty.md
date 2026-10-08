---
id: T-0332
title: /plan is honest when nothing pretty is reachable - the Worker scores the chosen route with RouteScore (parity with ScenicKit's, threshold 0.45) and answers a typed honest failure ("not much pretty within N minutes of this drive") with the +40 and all-back-roads offers, instead of presenting a dull route as scenic
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-PROD-01, P-SAFE-04]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Plan, Problem A step 3: "Honest failure = the chosen route has no scenic episode (RouteScore < 0.45) -> 'not much
pretty within 25 minutes of this drive' + offer +40 / 'all back roads' (a lambda=8 variant, shown with its real ETA)."
Measured 2026-10-08 by T-0327's owner (PR #213): ops/plan issues westwood-malibu +25 although RouteScore calls it an
honest failure (value 0.226 < 0.45, dud 0.500, about half its metres PCH trunk at score 0); ops/plan never consults
RouteScore. grep of services/api/src finds no RouteScore and no honest-failure path: the Worker's /plan answers the
bisection's route whatever it scores. Owner intent (memory owner-route-intent): Saddle Peak beats PCH; a dull
route sold as scenic is the failure this product exists to avoid.

MEASURE FIRST, then write the acceptance (CLAUDE.md): what /plan's answer and PlanError / PlanResult kinds carry today
(app copy for an honest failure may already exist from T-0294), what path details the Worker holds per edge
(scenic_score, distance) to compute RouteScore, how the TS score is held to ScenicKit's (a shared fixture through
both, full equality to 1e-9), how many fixtures in Tests/Fixtures and services/api/test fall each side of 0.45, and
whether the +40 / all-back-roads offers are one more request each (budget ceiling and P-COST-04's request cap).

## Log
- 2026-10-08T19:42:35Z filed by agent/claude-opus-5 (orchestrator) from T-0327's stillOpen finding.
