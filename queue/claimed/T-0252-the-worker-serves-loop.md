---
id: T-0252
title: the Worker serves POST /loop - "just drive 45 minutes and come back": one round_trip request (lambda 2, seeded by user+date), the anti-retrace check ported from ScenicKit RetraceDetector, at most 2 retries, quota first, kill switch honoured
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T09:05:18Z
lease_expires_at: 2026-10-05T19:05:18Z
worktree: .worktrees/T-0252
branch: task/T-0252
exclusive: []
touches: [services/api/src/, services/api/test/, Tests/ScenicKitTests/LoopRetraceParityTests.swift, Tests/Fixtures/t0252/]
pins_affected: [P-COST-01, P-COST-04, P-PRIV-05, P-SAFE-01]
reviewer: null
depends_on: [T-0248]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULED in the Log before code from the plan's Problem B: request shape (start as one coordinate at <= 2 dp, minutes), round_trip.distance = v_eff * T_loop, the seed from (user, date), lambda 2, the custom model from buildCustomModel; the retrace check is a byte-faithful port of Sources/ScenicKit/Loop (25 m cells, heading delta > 150 deg, < 15% of length) - a shared fixture proves the TS port and the Swift original give the SAME verdict and fraction on at least 5 recorded loops (exact equality)"
  - "quota decremented before any upstream call; KILL=1 -> 503 with zero upstream calls; at most 3 upstream requests per loop (P-COST-04) - reseed then areas on retraced edges, max 2 retries - each by a counting-fake test by name"
  - "the response carries geometry, duration, the retrace fraction and the Apple Maps URL; vitest count quoted; the new module's mutation population with a literal floor (the same vitest-driven form T-0248 ruled)"
---
## Brief

Milestone survey 2026-10-04: M5 loop has the engine (ScenicKit Loop/RetraceDetector) but no endpoint. Same shape as /plan (T-0248).

## Log
- 2026-10-05T09:04:49Z filed by agent/claude-opus-5 (orchestrator) after PR #139 (T-0248) merged.
- 2026-10-05T09:05:18Z claimed by agent/claude-opus-5; lease until 2026-10-05T19:05:18Z
- 2026-10-05T09:09:06Z **RULED before code** (agent/claude-opus-5, owner). Plan Problem B (:122-123) reads in full: "`round_trip` with `round_trip.distance = v_eff*T_loop`, seed from (user, date), lambda=2. Our anti-retrace check (25 m cells, heading delta>150 deg, <15% of length); on failure reseed, then `areas` on retraced edges; max 2 retries." Every gap between that sentence, the Brief and the code is ruled here.
  - **R1 request (P-PRIV-05).** `POST /loop {start:{lat,lon}, minutes}` - a WHITELIST at every level (the planRequest.ts shape: any other key is refused, so a second coordinate has no name to ride in under). `start` is the ONE coordinate, each component through planRequest's `atMostTwoDecimals` (rounded on the device). `minutes` is a finite number in [MIN_LOOP_MINUTES=10, MAX_LOOP_MINUTES=180]; 10 because a round_trip under ~7 km is the driveway and back.
  - **R2 distance.** The plan names `v_eff` and never defines it. Ruled `V_EFF_KMH = 40` (a winding back-road average; car_scenic is slower than car_fast by design), `round_trip.distance = Math.round(minutes * V_EFF_KMH * 1000 / 60)` metres: 45 min -> 30000 m. Tuning it is a measurement task once the box serves round_trip, not an acceptance here.
  - **R3 seed.** FNV-1a 32-bit over the UTF-8 of `${userId}|${dayKey(now)}` (quota.ts's UTC day). Same user, same UTC day -> the same loop. The reseed is `(seed + 1) >>> 0`.
  - **R4 lambda 2.** `custom_model = buildCustomModel(2, closures)` - closures null on attempts 1 and 2 - and every model passes `rejectCustomModel` before it is sent (/plan's `route()` shape; P-SAFE-01). The request: one point `[[lon,lat]]`, profile car_scenic, `algorithm: round_trip`, `round_trip.distance`, `round_trip.seed`, `points_encoded:false`, `instructions:false`, `ch.disable:true`, details = ROUTE_DETAILS.
  - **R5 retries (P-COST-04: at most 3 requests).** Attempt 1 seed s. Not acceptable -> attempt 2 seed s+1. Not acceptable -> attempt 3 seed s+1 with `areas`: buildCustomModel's closure squares (half-side AREA_HALF_SIDE_M=30) around attempt 2's RETRACED samples, skipping those within START_CLEARANCE_M=300 of the start (the stem out of your own street cannot be avoided, and an area over the start point would make the router refuse), thinned to >= AREA_SPACING_M=100 apart and capped at MAX_CLOSURE_POLYGONS (50). If nothing survives the clearance, attempt 3 would be attempt 2 again, so it is NOT sent. Still not acceptable -> 422 `no_clean_loop` with the least-retraced fraction. A router refusal on any attempt -> 502 `no_route` (/plan's mapping).
  - **R6 the port.** services/api/src/retrace.ts is RetraceDetector.swift + Geo.distanceMeters/initialBearingDegrees in the same constants (25, 2x25 index cell, 150, 0.15 inclusive, 2 samples per cell, 111_132, 111_320, 6_371_008.8) and the same order of float operations; `.rounded(.down)` -> Math.floor, `.rounded(.up)` -> Math.ceil, `truncatingRemainder` -> `%` (both fmod). One addition the Swift lacks: the scan also returns the retraced SAMPLE points, used only for R5's areas; the fraction comes from the same accumulator.
  - **R7 the shared fixture.** No round_trip recording exists (the box does not serve round_trip yet), so `Tests/Fixtures/t0252/loops.json` carries SYNTHETIC loops (square, out-and-back, lollipop, figure-eight crossing, parallel streets, a partial retrace) plus two built from the RECORDED t0221 santa-monica-topanga geometry (scenic out + fastest back; scenic out and the same road back). Coordinates are INTEGER microdegrees divided by 1e6 on both sides, so neither side's decimal parser is in the comparison. The expected fraction is the IEEE-754 bit pattern (hex) plus the verdict, RECORDED FROM THE SWIFT ORIGINAL (its failure message on a placeholder), and both the Swift test and the TS test assert those bits: identical by exact equality. Known risk, ruled if it lands: ucrt and V8 libm could differ by an ulp in sin/cos/asin/atan2.
  - **R8 spend (P-COST-01).** `guardedPlan` gains an optional budget (default PLAN_UPSTREAM_COST, so /plan is byte-unchanged); /loop reserves LOOP_UPSTREAM_COST=3 and its `call` refuses a 4th before fetchImpl. KILL=1 -> 503 before the body is read. GAP, recorded not hidden: the tier table's separate "Loop 1/day free" is not implemented - Counters has no kind - so a loop counts as one plan against the daily plan allowance; filed as follow-up.
  - **R9 response.** `{route:{coordinates,distance_m}, duration_s, retrace_fraction, attempts, target_distance_m, minutes, eta_is_estimate:true, waypoints, apple_maps_url}`; the URL is `appleMapsUrl(start, start, decisionPoints(chosen))` - source and destination both the 2 dp start.
  - **R10 wiring + touches.** ROUTES["/loop"] with loopDepsFromEnv -> null -> 503 planning_unavailable (no production router/counters yet, as /plan). touches: widened to the Swift parity test and Tests/Fixtures/t0252/ because the acceptance demands the Swift side of the shared fixture. Mutation population: services/api/test/mutate/loopMutants.mjs, the planMutants.mjs form, literal floor, subjects retrace.ts, loopRequest.ts, loopPlanner.ts, loop.ts.
