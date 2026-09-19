---
id: T-0190
title: services/routing - the request template carries the Worker's full clause set (the RESIDENTIAL anti-rat-run clause, plan line 108) and the five scenic_lambda_bands.json rows are asserted equal to customModel.ts's scenicBandMultipliers at MULTIPLIER_DECIMALS - red when either side moves
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [services/routing/profiles/car_scenic_request.json]
touches: [services/routing/, services/api/src/customModel.ts]
pins_affected: []
reviewer: null
depends_on: [T-0031]
verify: [ops/test, ops/check-pins]
acceptance:
  - "services/routing/profiles/car_scenic_request.json carries every priority clause services/api/src/customModel.ts's buildCustomModel emits, in order: the ${high}/${mid}/${low} band clauses AND 'road_class == RESIDENTIAL && scenic_score < 7 -> 0.5' (plan line 108); the closure clause stays the Worker's own and is named in the test as the deliberate difference; RED BY NAME first: a container-free test in tests/test_profiles_static.py that reads the TS clause list off buildCustomModel's source (anchored on the identifiers buildCustomModel / scenicBandMultipliers / MULTIPLIER_DECIMALS, never on a comment) and the JSON's priority list, red today (three clauses vs four), then green"
  - "the five rows of scenic_lambda_bands.json (lambda 0, 1, 2, 4, 8) asserted equal to 1/(1+0.5*lambda) and 1/(1+lambda) formatted at MULTIPLIER_DECIMALS=6 read off customModel.ts - a mutant that changes MULTIPLIER_DECIMALS or one JSON row is red by name; recorded in the Log which side is the source of truth (the Worker; the JSON is the oracle fixture)"
  - "the routed Vermont run (tests/test_lambda_monotone.py, existing WSL image and graph-cache, no rebuild) still green with the RESIDENTIAL clause in the template - the five T(lambda) durations quoted; if they move, say by how much and why (the residential demotion is a scenic-ranking term, not a safety gate)"
  - "services/routing pytest count line at the final commit; bash ops/check-pins --source-only and bash ops/queue-check bare"
---
## Brief

From the 22:13 panel (CODE lens, grounded; the band-source-of-truth ruling). The Worker's buildCustomModel is the
only code that ever sends the per-request scenic penalty (config.yml loads car_scenic_base.json alone); the routing
JSONs have no runtime consumer - `git grep scenic_lambda_bands -- services/api` is empty. The five band rows agree
with customModel.ts to the digit, but by hand, at five points, with nothing cross-checking them; and the Vermont
oracle (plan lines 89, 225) exercises a three-clause template while production sends four - the RESIDENTIAL
anti-rat-run demotion has never met a real graph. Filed as its own task rather than widened into PR #105's round-2
fix (PROCESS ruling 6: no new blocking class on a fix pass in flight). Lands after #105 merges; T-0182 (the owner's
LA drive from the CLI) should run over the model production sends.

## Log
- 2026-09-19T04:34:10Z filed by agent/claude-fable-5-1 from the 22:13 panel's grounded synthesis. Not started; after #105 merges.
