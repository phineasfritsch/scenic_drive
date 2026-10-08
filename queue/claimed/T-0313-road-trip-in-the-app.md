---
id: T-0313
title: Road trip in the app - a TripClient for POST /trip, a road-trip sheet (destination, days, daily limits), a day-by-day itinerary preview, and per-day "Open in Apple Maps" with that day's pinned waypoints
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T04:26:07Z
lease_expires_at: 2026-10-09T04:26:07Z
worktree: .worktrees/T-0313
branch: task/T-0313
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, Sources/ScenicKit/, Tests/ScenicKitTests/, Sources/Handoff/, Tests/HandoffTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-SAFE-03, P-ATTR-01, P-PRIV-05]
reviewer: null
depends_on: [T-0268, T-0249, T-0294, T-0311]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: the shipped /trip request and response (services/api/src/trip.ts, tripRequest.ts, roadTrip.ts: one origin coordinate at 2 dp + a destination place id + days/limits + vehicle), the ScenicKit RoadTrip day splitter, how the app composes a new sheet without a Package.swift edit (as T-0294/T-0306 did) and with ScenicAPIClient imported only in PlanAdapter, and the free-vs-paid split (plan: preview free, full itinerary paid - read the T-0272 tier seam; if the app has no paid check yet, rule what the free preview shows)"
  - "TripClient: request body by full equality to a recomputation; every Worker answer (200, 400, 404 unknown_place, 422 region_unsupported, 429, 503 planning_paused/unavailable) mapped to one typed outcome by a table; no retries"
  - "A ScenicKit trip-sheet state machine (destination chosen -> planning -> itinerary | failed) with a full-equality transition table; the disclaimer gate still blocks the first plan (P-SAFE-03 - counting transport 0 before acceptance)"
  - "Per-day handoff builds one Apple Maps URL per day from that day's waypoints (Handoff AppleMapsDirections, <= 9 waypoints, the repeatable waypoint form) by full equality; a day with more stops than the URL allows is split by a ruled rule"
  - "The itinerary sheet is full-height or gets a typed whole-line P-ATTR-01 approval; ios-compile + ios-screenshot pass on the head; digests re-approved; a mutation population with a literal floor, three entries MISSED before and CAUGHT by name after"
---
## Brief

Plan, Features: "Road trip | A->B over N days, +40% scenic budget, day splitter, 2-4 stops/day, overnight town per
boundary | Preview free | Full itinerary, per-day handoff/navigation (paid)". The Worker /trip (T-0268) and the ScenicKit
day splitter (T-0249) are shipped; the app has no road-trip surface (grep RoadTrip under apps: none). Calm copy (memory
owner-route-intent).

## Log
- 2026-10-08T04:25:58Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M5 road trip UI).
- 2026-10-08T04:26:07Z claimed by agent/claude-opus-5; lease until 2026-10-09T04:26:07Z
- 2026-10-08T04:30:49Z MEASURE, then RULINGS before code. agent/claude-opus-5 (owner).
  MEASURED (services/api/src at 934d5e68): tripRequest.ts BODY_KEYS = ["origin", "destination", "days",
  "extra_budget_pct", "vehicle"], REQUIRED_KEYS origin/destination/days; origin {lat, lon} finite, in range, at most 2
  dp; destination {place} a PLACE_ID string; days a whole number in [MIN_TRIP_DAYS 1, MAX_TRIP_DAYS 5];
  extra_budget_pct optional, whole, [0, MAX_EXTRA_BUDGET_PCT 40], default 40; vehicle an enabled profile (T-0311).
  There is NO daily-limit field: tripPlanner.ts fixes MAX_DRIVE_MS_PER_DAY 21_600_000 (6 h) and MAX_METERS_PER_DAY
  482_803 (300 mi). trip.ts answers, in order: 503 planning_paused (KILL, before the body), 405 non-POST, 400
  invalid_request{detail}, 422 region_unsupported, 503 planning_unavailable (no deps, or the resolver threw), 404
  unknown_place, then under guardedPlan 429 quota_exhausted{resets_at}, 503 planning_paused (upstream paused), 422
  too_few_days{days, max_drive_s, max_distance_m}, 422 ceiling_breached{detail}, 500 {error: no_recorded_lambda},
  502 no_route{detail}, and 200 TripResult: view "preview"|"full", route{coordinates [lon, lat][], distance_m},
  eta_s, fastest_eta_s, ceiling_s, budget_s, extra_budget_pct, lambda, evaluations, eta_is_estimate true,
  places_searched false, days[{day, start{lat,lon}, end{lat,lon}, drive_s, distance_m, ceiling_s, stops (always []:
  planTrip passes no places), overnight {kind: "not_searched"}|null, leg {coordinates, eta_s, distance_m}|null}],
  plus an optional closures_hazard. `full` (one leg a day) is `who.tier === "paid"`, and T-0272's identify reads the
  tier ONLY from x-scenic-account-token; `grep -rln account-token Sources apps` = nothing, so every trip the app can
  make today is anon -> view "preview", every leg null. ScenicKit RoadTrip (T-0249) is the day splitter the Worker's
  roadTrip.ts ports; it needs the route's edges, which stay on the server, so the app never runs it - it reads the
  split from the answer. ScenicApp/Package.swift: FeaturePlanSheet = DesignSystem + ScenicKit + PlaceStore;
  FeatureScenicHome also has Handoff; PlanAdapter is the only target with ScenicAPIClient; root ScenicAPIClient
  depends on ScenicKit + PlaceStore, NOT Handoff. The plan sheet is the shell's full-height `.sheet(isPresented:
  $isPlanning)`, approved by whole line in check-map-attribution-sheet; the shell's lines are frozen in
  check-safety-disclaimer-frozen.
  - R1 WIRE: TripClient (ScenicAPIClient) POSTs `{origin{lat,lon}, destination{place}, days, extra_budget_pct,
    vehicle}` to base/trip with the same headers PlanClient sends (content-type, x-scenic-device), sorted keys; the
    origin is refused on the device unless at 2 dp (P-PRIV-05: the one coordinate), days outside 1...5 and a percent
    outside 0...40 are refused on the device with 0 requests; extra_budget_pct is ALWAYS sent (the driver's choice,
    never the server default by omission). One request per call, no retries (a transport throw is routingOffline).
  - R2 DAILY LIMITS: the wire has none and this task does not widen the Worker whitelist. The sheet offers days (1-5)
    and extra time (0-40 %, step 10) and states the Worker's fixed limits as copy ("up to 6 hours or 300 miles a
    day"); a too_few_days answer says to add a day.
  - R3 OUTCOMES, one table (TripReplyReader): 200 -> itinerary (decoded strictly; a bad body or a view other than
    preview/full is unexpectedResponse(200)); 400 invalid_request -> invalidRequest; 404 unknown_place ->
    unknownPlace; 422 region_unsupported -> regionUnsupported; 422 too_few_days -> tooFewDays; 422 ceiling_breached
    -> ceilingBreached; 429 quota_exhausted with a parseable resets_at -> quotaExhausted(resetsAt), else
    unexpectedResponse(429); 500 no_recorded_lambda -> planRefused; 502 no_route -> noRoute; 503 planning_paused ->
    planningPaused; 503 planning_unavailable and any other 5xx -> routingOffline; anything else
    unexpectedResponse(status). Each maps to one ScenicKit TripFailure with its own calm copy line.
  - R4 COMPOSITION, no Package.swift edit: ScenicKit/TripSheet/ holds the state machine TripSheet (idle, searching,
    chosen, planning(ticket), itinerary(ticket, TripItinerary), failed(ticket, TripFailure)), TripTicket, the
    protocol TripPlanning (RoutePlanning's shape), TripOutcome, TripItinerary(+Day) and TripFailure. ScenicAPIClient
    adds TripClient + ClientTripPlanner (TripPlanning); PlanAdapter adds LiveTripPlanner.make() - still the only
    importer of ScenicAPIClient. The trip surface is IN-SHEET content of the full-height plan sheet (a "Road trip"
    toolbar button, as T-0306's Saved), so no new presentation and P-ATTR-01's whitelist is unchanged. FeaturePlanSheet
    cannot see Handoff, so FeatureScenicHome (which already imports Handoff) exposes TripDayLinks.urls(_:) and the
    shell hands it to PlanSheetScreen as a closure (the surprise-card pattern); the frozen shell line is re-typed in
    check-safety-disclaimer-frozen. P-SAFE-03: TripSheet.startPlanning returns nil until the disclaimer is accepted,
    tested through ClientTripPlanner with a CountingPlanTransport at count 0.
  - R5 FREE vs PAID: the plan's row is "Preview free | Full itinerary, per-day handoff (paid)". The app has no paid
    check (R-measure: no account token on the wire), so RULED: the free preview shows the day-by-day list (day N,
    drive time, distance, an overnight stop at each boundary but the last, "places not searched yet"), the total ETA
    against the fastest with the estimate badge, and the safety line; the per-day "Open in Apple Maps" is offered
    ONLY for a day whose answer carries a leg (view full), and a preview says calmly that day-by-day handoff comes
    with the full itinerary. Nothing paid is unlocked on the device; the handoff is built and tested now and lights
    up when the token is sent (recorded as stillOpen, not faked).
  - R6 PER-DAY HANDOFF (Handoff TripDayHandoff): a day's path is its leg's coordinates. Pins: walking the path,
    the first vertex at or past each whole multiple of pinSpacingMeters = 20_000 of cumulative Geo.distanceMeters,
    never the first or last vertex. SPLIT RULE: while more than AppleMapsDirections.maxWaypoints (9) pins remain,
    emit a part with the next 9 as waypoints and the 10th as its destination, and that pin is the next part's
    source; the last part ends at the path's last vertex. So every part has <= 9 waypoints, parts chain end to start,
    and every pin is used once. A path of fewer than 2 points gives no part. Tested by full equality against
    AppleMapsDirections(source:destination:waypoints:).url() over hand-listed pins.
  - R7 PROOF: tests first, RED by name against stubs; population ops/mutate/tripsheet.py (+_mutations, _run) with a
    literal floor over TripSheet, TripReplyReader, TripRequestBody, ClientTripPlanner, TripDayHandoff; digests
    re-approved; ios-compile + ios-screenshot dispatched on the head.
