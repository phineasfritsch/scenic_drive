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
depends_on: [T-0209]
verify: [ops/test, ops/check-pins]
acceptance:
  - "services/routing/profiles/car_scenic_request.json carries every priority clause services/api/src/customModel.ts's buildCustomModel emits, in order: the ${high}/${mid}/${low} band clauses AND 'road_class == RESIDENTIAL && scenic_score < 7 -> 0.5' (plan line 108); the closure clause stays the Worker's own and is named in the test as the deliberate difference; RED BY NAME first: a container-free test in tests/test_profiles_static.py that reads the TS clause list off buildCustomModel's source (anchored on the identifiers buildCustomModel / scenicBandMultipliers / MULTIPLIER_DECIMALS, never on a comment) and the JSON's priority list, red today (three clauses vs four), then green"
  - "the five rows of scenic_lambda_bands.json (lambda 0, 1, 2, 4, 8) asserted equal to 1/(1+0.5*lambda) and 1/(1+lambda) formatted at MULTIPLIER_DECIMALS=6 read off customModel.ts - a mutant that changes MULTIPLIER_DECIMALS or one JSON row is red by name; recorded in the Log which side is the source of truth (the Worker; the JSON is the oracle fixture)"
  - "the routed Vermont run (tests/test_lambda_monotone.py, existing WSL image and graph-cache, no rebuild) still green with the RESIDENTIAL clause in the template - the five T(lambda) durations quoted; if they move, say by how much and why (the residential demotion is a scenic-ranking term, not a safety gate)"
  - "the four safety gates of car_scenic_base.json pinned by expression in tests/test_profiles_static.py (!car_access; road_access == PRIVATE || road_access == NO; the surface list; road_class == TRACK) - RED BY NAME first with priority: [] (today the whole routed suite is 9 passed with every gate deleted, because the Dockerfile bakes the profiles into the image and no test asserts the gates exist); this is P-SAFE-01's JSON half"
  - "test_profiles_static's _condition() distinguishes if from else_if: the second band written 'if' collapses the three-band model to two and today passes the container-free half (only the routed bite test sees it) - red by name, then green"
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
- 2026-09-19T04:46:33Z two bullets added by agent/claude-fable-5-1 from rv2-pr105's recordables on PR #105 (PASS, merged): (a) nothing asserts the base profile's four safety gates exist, and no routed test can see that file (Dockerfile COPY profiles; only /graph and /models mounted) - the reviewer's R2 ran the routed suite green with priority: []; (b) _condition() accepts 'if' where the plan wrote 'else_if', so a band collapse passes the container-free half. Both belong with the clause-set cross-check this task already owns.
- 2026-09-19T10:46:00Z depends_on: T-0031 -> T-0209 by agent/claude-fable-5-1 (03:13 panel, grounded): T-0031 is in done/ as a Vermont slice, so the queue read this task as unblocked while nothing builds the LA graph it needs; T-0209 is that graph.
