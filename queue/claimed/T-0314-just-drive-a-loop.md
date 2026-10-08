---
id: T-0314
title: "Just drive a loop" in the app - a LoopClient for POST /loop, a loop sheet (start = here or a typed place, minutes dial), a preview of the loop with its retrace check, and handoff to Apple Maps with the loop's pinned waypoints
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T06:32:56Z
lease_expires_at: 2026-10-09T06:32:56Z
worktree: .worktrees/T-0314
branch: task/T-0314
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, Sources/ScenicKit/, Tests/ScenicKitTests/, Sources/Handoff/, Tests/HandoffTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-SAFE-03, P-ATTR-01, P-PRIV-05]
reviewer: null
depends_on: [T-0252, T-0294, T-0310, T-0311]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: the shipped /loop request/response (services/api/src/loop.ts, loopRequest.ts: one start coordinate at 2 dp, minutes, vehicle), where the 'Just drive a loop' entry lives (the Surprise card's secondary action per the plan's UI list, and/or the home), how it composes without a Package.swift edit, and the free tier (plan: Loop 1/day free, unlimited paid - read the T-0272 tier seam; rule what the app shows when the Worker answers 429)"
  - "LoopClient: request body by full equality to a recomputation (one coordinate, 2 dp, minutes, vehicle); every Worker answer (200, 400, 422 region_unsupported, 429, 503 planning_paused/unavailable) mapped to one typed outcome by a table; no retries"
  - "A ScenicKit loop-sheet state machine with a full-equality transition table; the minutes dial bounded by the Worker's range at every bound (memory range-checks-every-bound); the disclaimer gate still blocks the first plan (P-SAFE-03 - counting transport 0 before acceptance)"
  - "Loop handoff builds one Apple Maps URL that starts and ends at the start with the loop's pinned waypoints (<= 9) by full equality; the preview sheet is full-height or gets a typed whole-line P-ATTR-01 approval; ios-compile + ios-screenshot pass; digests re-approved; a mutation population with a literal floor, three entries MISSED before and CAUGHT by name after"
---
## Brief

Plan, Features: "Loop | 'Just drive 45 minutes and come back' | 1/day free | Unlimited"; UI: the Surprise card offers
`Take me there` / `Just drive a loop`. The Worker /loop (T-0252) is shipped with the retrace check; the app has no loop
surface. Calm copy (memory owner-route-intent).

## Log
- 2026-10-08T05:02:38Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M5 loop UI).
- 2026-10-08T06:32:56Z claimed by agent/claude-opus-5; lease until 2026-10-09T06:32:56Z
- 2026-10-08T06:36:13Z MEASURE, then RULINGS before code. agent/claude-opus-5 (owner).
  MEASURED (services/api/src at 0d502f5f): loopRequest.ts BODY_KEYS = ["start", "minutes", "vehicle"],
  REQUIRED_KEYS start/minutes, START_KEYS lat/lon; start {lat, lon} finite, in [-90, 90] / [-180, 180], at most 2 dp
  (ORIGIN_DECIMALS); minutes any finite number in [MIN_LOOP_MINUTES 10, MAX_LOOP_MINUTES 180] (not required whole);
  vehicle optional, an enabled profile (vehicleProblem). loop.ts answers, in order: 503 planning_paused (KILL, before
  the body), 405 {error: "POST only"}, 400 invalid_request{detail} (not JSON, or the whitelist), 422
  region_unsupported, 503 planning_unavailable (no deps), then under the guarded plan 429 quota_exhausted{resets_at}
  (UpstreamPaused with a quota verdict), 503 planning_paused (upstream paused), 422 no_clean_loop{retrace_fraction}
  (LoopFailure: three attempts all over the retrace limit), 502 no_route{detail}, and 200 LoopResult (loopPlanner.ts):
  route{coordinates [lon, lat][], distance_m}, duration_s, retrace_fraction, attempts, seed, target_distance_m,
  minutes, eta_is_estimate true, waypoints {lat, lon}[] (decisionPoints, limit MAX_WAYPOINTS 9), apple_maps_url
  (appleMapsUrl(start, start, waypoints)), plus an optional closures_hazard. The retrace limit is retrace.ts
  MAX_RETRACE_FRACTION 0.15 inclusive = ScenicKit RetraceDetector.maxRetraceFraction (Sources/ScenicKit/Loop). TIER
  (T-0272/T-0256): quota.ts DAILY_LOOP_QUOTA = {anon: 1, free: 1, paid: DAILY_PLAN_QUOTA.paid (200)}, and the tier is
  read only from x-scenic-account-token, which the app never sends (T-0313 measured `grep -rln account-token Sources
  apps` = nothing) - so every loop the app makes is anon, one a day. APP: no loop surface (`grep -rln "Loop"
  apps/ios/Packages/ScenicApp/Sources` = nothing loop-shaped); the plan sheet already hosts the road trip as in-sheet
  content (T-0313 R4) behind a bottom-bar button; SurpriseCard (FeatureSurpriseMe) is in T-0312's in-flight touches;
  the app has no NSLocationWhenInUseUsageDescription and T-0294 R4 ruled the plan sheet asks for no location.
  - R1 WIRE: LoopClient (ScenicAPIClient) POSTs `{minutes, start{lat, lon}, vehicle}` (sorted keys) to base/loop with
    PlanClient's headers (content-type, x-scenic-device). The start is refused on the device unless in range and at 2
    dp (P-PRIV-05: the ONE coordinate), minutes outside 10...180 refused, a vehicle not enabled refused, no install id
    refused - each with 0 requests. The app sends whole minutes (an Int); vehicle is ALWAYS sent. One request per
    call, no retries; a transport throw is routingOffline.
  - R2 OUTCOMES, one table (LoopReplyReader): 200 -> the loop (decoded strictly: [lon, lat] pairs of length 2,
    waypoints {lat, lon} at most 9 - more is unexpectedResponse(200), never truncated); 400 invalid_request ->
    invalidRequest(detail); 422 region_unsupported -> regionUnsupported; 422 no_clean_loop -> noCleanLoop; 429
    quota_exhausted with a parseable resets_at -> quotaExhausted(resetsAt), else unexpectedResponse(429); 502 no_route
    -> noRoute; 503 planning_paused -> planningPaused; 503 planning_unavailable and any other 5xx -> routingOffline;
    anything else (405 included) -> unexpectedResponse(status). Each maps to one ScenicKit LoopFailure with its own
    calm line.
  - R3 ENTRY + COMPOSITION, no Package.swift edit: the plan puts "Just drive a loop" on the Surprise card as its
    secondary action, but SurpriseCard is T-0312's in flight and a card action would open a second presentation from
    the home. RULED: the loop is IN-SHEET content of the full-height plan sheet, behind a second bottom-bar button
    "Just drive a loop" (accessibility id plan.loopTab) beside "Plan a road trip" - no new presentation, P-ATTR-01's
    whitelist unchanged. The Surprise card's secondary action is recorded STILL OPEN (a follow-up after T-0312
    lands). Files: ScenicKit/LoopSheet/ (LoopSheet, LoopSheetState, LoopTicket, LoopPlanning, LoopOutcome,
    LoopPreview, LoopFailure); ScenicAPIClient LoopClient, LoopRequestBody, LoopReplyReader, LoopError, LoopRefusal,
    LoopResponse, ClientLoopPlanner; PlanAdapter LiveLoopPlanner + UnreachableLoopPlanner (still the only importer of
    ScenicAPIClient); Handoff LoopHandoff; FeatureScenicHome LoopLinks (it already sees Handoff), handed to
    PlanSheetScreen by the shell as a closure (the TripDayLinks pattern; the frozen shell line re-typed);
    FeaturePlanSheet LoopScreen + LoopPreviewCard.
  - R4 START: "here" needs a location permission the app does not ask for (no usage string; T-0294 R4). RULED: the
    loop starts at a typed place from the bundled corpus (PlanPlaceList, the start field); "here" is NOT built and is
    recorded STILL OPEN (a location-permission task: Info.plist string + privacy review). LoopSheet cuts the start to
    2 dp before any ticket exists (P-PRIV-05).
  - R5 DIAL: LoopSheet.minuteRange = 10...180 (MIN/MAX_LOOP_MINUTES), default 45 (the plan's "45 minutes"), clamped at
    init and on set, frozen while planning; the UI steps by 5. Every bound tested (Int.min, 9, 10, 11, 179, 180, 181,
    Int.max) on the sheet and on LoopRequestBody (9 and 181 refused with 0 requests, 10 and 180 sent whole).
  - R6 PREVIEW + RETRACE CHECK: the preview shows the loop's drive time against the dial, its distance, the estimate
    badge, and its retrace check. The device re-runs the check: ClientLoopPlanner measures the returned path with
    ScenicKit RetraceDetector.retraceFraction; a path it cannot measure or finds over maxRetraceFraction is not shown -
    .failure(.noCleanLoop) (the plan: a loop that fails the retrace check is not shown; now held on both sides).
    LoopPreview carries the path, the waypoints, duration, distance, the device-measured fraction and the estimate flag.
  - R7 FREE TIER: one loop a day (anon = free = 1; the app is always anon). The form says "One loop a day is free." A
    429 is LoopFailure.quotaExhausted: "That was today's loop. Another one opens up tomorrow." No retry, no paywall push.
  - R8 HANDOFF (Handoff LoopHandoff): url(start:waypoints:) is AppleMapsDirections(source: start, destination: start,
    waypoints: waypoints).url() - the start is the ticket's 2-dp start, the coordinate the Worker planned from
    (loop.ts: appleMapsUrl(start, start, waypoints)); more than 9 waypoints throws (AppleMapsDirections), never
    truncated. The Worker's apple_maps_url is not read: the device builds the URL it opens. The door is ONE Link line
    in LoopPreviewCard, approved by whole line in DOORS_OPENERS; it is drawn only in the .preview state, which only a
    ticket reaches, which LoopSheet issues only after the disclaimer is accepted (P-SAFE-03).
  - R9 PROOF: tests first, RED by name against stubs; population ops/mutate/loopsheet.py (+_mutations, _run) with a
    literal floor over LoopSheet, LoopFailure, LoopRequestBody, LoopReplyReader, LoopError, LoopClient,
    LoopResponse, ClientLoopPlanner, LoopHandoff; digests re-approved; ios-compile + ios-screenshot on the head.
