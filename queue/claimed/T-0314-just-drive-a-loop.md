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
- 2026-10-08T07:55:07Z RED then GREEN, code, guards, population, iOS CI. agent/claude-opus-5 (owner).
  RED: tests and code were written together, so RED is shown against STUBS of every shipping symbol the tests bind
  to (LoopSheet.startPlanning's gate, LoopSheet.clamp, LoopSheet.edit, LoopFailure.line, LoopRequestBody.validated,
  LoopReplyReader.read/error, LoopError.failure, ClientLoopPlanner.outcome, LoopHandoff.directions), applied by a
  throwaway script under .build/ and restored (Sources clean of edits after). `swift test --scratch-path
  .build/t314 --filter LoopSheetTests|LoopClientRequestTests|LoopClientOutcomeTests|LoopSheetGateTests|
  LoopHandoffTests`: `Test run with 17 tests in 5 suites failed ... with 139 issues`, exit 1, RED by name (16):
  every state x every event lands whole; P-SAFE-03: no loop ticket before the disclaimer is accepted, one after;
  the minutes dial is held to 10...180 at every bound, 45 by default; P-PRIV-05: the ticket carries the start cut
  to 2 dp on each axis, and the dial's minutes; every loop failure has its own calm line; the /loop request is
  exactly the whitelisted body, one coordinate at 2 dp, sent once; every bound: refused on the device with 0
  requests, or sent once exactly as written; every Worker answer is one typed outcome from one request; an
  unreachable Worker is routingOffline after exactly one attempt; every loop error is the sheet's failure of the
  same name; P-SAFE-03: no loop request is made before the disclaimer is accepted; a clean loop reaches the sheet
  as exactly its preview, with the device's retrace fraction; a loop the device finds retraced is not shown:
  noCleanLoop; a spent day and a refused loop reach the sheet as their failures; one URL from the start back to
  the start through the pins, in order; ten pins are refused, never cut to nine. Green under the stubs (1): the
  request table's own coverage meta-test. GREEN after restore (+HandoffSourceTests, LoopHandoff approved on the
  Handoff identifier whitelist): `Test run with 21 tests in 6 suites passed`, exit 0.
  APP (107b0d52): LoopScreen + LoopPreviewCard in FeaturePlanSheet (in-sheet content behind a second bottom-bar
  button "Just drive a loop", plan.loopTab); LiveLoopPlanner + UnreachableLoopPlanner in PlanAdapter; LoopLinks in
  FeatureScenicHome; PlanSheetScreen's init takes loopPlanner + loopLink and the shell passes
  `LiveLoopPlanner.make()` and `LoopLinks.url` (the frozen line re-typed in check-safety-disclaimer-frozen). The
  door is ONE line approved in DOORS_OPENERS: `Link("Open the loop in Apple Maps", destination: link)` in
  LoopPreviewCard.swift (-doors refused it by name first, and refused LoopScreen's `self.link = link` as a `.link`
  opener - the closure was renamed mapsURL rather than approved). LoopLinks.swift approved into PINNED_FEATURE;
  five new and two changed app/shell files and fifteen new Sources files re-approved by sha256 (PINNED_APP_SWIFT,
  PINNED_SHELL_DIGEST, [PINNED_ROOT_SOURCES]); no existing row reordered.
  GUARDS on 107b0d52: `bash ops/lib/check-safety-disclaimer` rc=0; `bash ops/lib/check-map-attribution` rc=0 (no
  new presentation: the loop is in-sheet content of the full-height plan sheet, so P-ATTR-01's whitelist is
  unchanged); `python ops/lib/check-store-links.py` rc=0; `bash ops/lib/check-line-cap` rc=0 (407 Swift files,
  none over 300; PlanSheetScreen.swift 199 lines); `python ops/lib/check-mutate-population.py` rc=0 (floor of 121
  holds; loopsheet.py in DRIVERS, its nine subjects in COVERED_FLOOR, six no-code modules allowlisted with
  reasons); `python ops/lib/check-pins-yaml.py` rc=0 (PINS.yaml untouched); `bash ops/queue-check` QUEUE OK (307).
  POPULATION at 107b0d52: `python ops/mutate/loopsheet.py --prove-floor` FLOOR PROOF OK 7 of 7; `python
  ops/mutate/loopsheet.py` - `population mutations=53 (floor 53) equivalent=1 (floor 1)`, BASELINE exit=0,
  `caught by the test that names it: 53 of 53 (wrong killer 0, trapped 0, compile-only 0, MISSED 0, skipped 0)`,
  E1 MISSED as required, `MUTATE OK caught=53/53 equivalent_caught=0`, exit 0. MISSED BEFORE / CAUGHT AFTER by
  name: `python ops/mutate/loopsheet.py --prove-vacuity --only 1,18,45` (the five test files replaced by empty
  suites) - `MISSED 1 a ticket without the disclaimer`, `MISSED 18 the latitude bound dropped`, `MISSED 45 the
  device's retrace check dropped`, `VACUITY PROOF OK ... MISSED=3 of 3`; in the full run `caught 1 ... by: P-SAFE-03:
  no loop ticket before the disclaimer is accepted, one after | every state x every event lands whole | P-SAFE-03:
  no loop request is made before the disclaimer is accepted`, `caught 18 ... by: every bound: refused on the device
  with 0 requests, or sent once exactly as written`, `caught 45 ... by: a loop the device finds retraced is not
  shown: noCleanLoop`.
  iOS CI on 107b0d52: ios-compile run 37741764271 success (2m30s), ios-screenshot run 37741768505 success (12m18s).
- 2026-10-08T08:01:35Z MERGE LAST, ACCEPTANCE re-quoted on the merged head. agent/claude-opus-5 (owner).
  MERGE: `git fetch origin`, origin/main 9cf2b986 (T-0312 PR #202 merged) merged into 6087adc2; one conflict, the
  DRIVERS line of ops/lib/mutate_population_table.py, resolved by union (loopsheet.py + main's shownhistory.py);
  the digest table and -pinned auto-merged and a full recomputation over the merged tree changed no row (main's
  SurpriseCard/SurpriseShownLog rows and this task's rows both stand). `git merge-base --is-ancestor origin/main
  HEAD` exit 0.
  ACCEPTANCE on 6087adc2:
  1. MEASURE then RULE FIRST: the 06:36:13Z entry (R1-R9) precedes all code (commit 0f07fd20 carries only it): the
     /loop wire (start at 2 dp, minutes 10...180, vehicle), the entry (in-sheet plan-sheet tab; the Surprise card's
     secondary action ruled to a follow-up, T-0312 then in flight), composition without a Package.swift edit, the
     tier (DAILY_LOOP_QUOTA anon/free 1; a 429 is a calm "today's loop" line, no retry).
  2. LoopClient: body by full equality ("the /loop request is exactly the whitelisted body, one coordinate at 2 dp,
     sent once" + every accepted bound row compares the whole PlanHTTPRequest); every Worker answer (200 incl.
     malformed and the 9/10-waypoint bound, 400, 404, 405, 422 region_unsupported/no_clean_loop/other, 429 with and
     without resets_at, 500, 502, 503 planning_paused/planning_unavailable, 504, 418) one typed outcome by a table of
     22 rows through LoopClient.loop, each from exactly one request; offline = routingOffline after one attempt (no
     retries; population 28 proves a retry is caught).
  3. LoopSheet transition table (6 states x 9 events, compared whole); the dial at Int.min, -1, 0, 9, 10, 11, 45,
     179, 180, 181, Int.max on the sheet and 9/10/180/181/Int.min/Int.max on the wire; P-SAFE-03 at transport count
     0 before acceptance through ClientLoopPlanner + CountingPlanTransport ("P-SAFE-03: no loop request is made
     before the disclaimer is accepted").
  4. LoopHandoff.url by full equality to AppleMapsDirections(source: start, destination: start, waypoints:).url()
     at 0, 1, 3, 9 pins (source == destination in the query), ten refused never truncated; the preview is in-sheet
     content of the full-height plan sheet (no new presentation; check-map-attribution rc=0, P-ATTR-01 unchanged);
     ios-compile + ios-screenshot success on 107b0d52 (above) and dispatched on 6087adc2 (ios-compile 37747096543,
     ios-screenshot 37747100835; this Log commit changes only this file); digests re-approved; population 53/53 with
     a literal floor, three MISSED before and CAUGHT by name after (entries 1, 18, 45, quoted above).
  GATES on 6087adc2: `swift test --scratch-path .build/t314 --filter
  ScenicAPIClientTests|LoopSheetTests|TripSheetTests|PlanSheetTests|HandoffTests` - `Test run with 199 tests in 36
  suites passed`, exit 0; `bash ops/lib/check-safety-disclaimer` rc=0; `bash ops/lib/check-map-attribution` rc=0;
  `python ops/lib/check-store-links.py` rc=0; `python ops/lib/check-mutate-population.py` rc=0 (floor of 123
  holds); `bash ops/lib/check-line-cap` rc=0 (442 Swift files, none over 300); `python ops/lib/check-pins-yaml.py`
  rc=0 (PINS.yaml untouched); `bash ops/queue-check` QUEUE OK (308 tasks).
  STILL OPEN (recorded, not faked): "here" as a loop start is not built - the app asks for no location (no usage
  string; T-0294 R4), so the start is a typed place (a location-permission task); the Surprise card's "Just drive a
  loop" secondary action is not built (SurpriseCard was T-0312's; now merged, a follow-up task); the app sends no
  x-scenic-account-token, so every loop is anon at one a day and paid "unlimited" is unreachable from the app; the
  preview has no map of its own (no new map surface, so P-ATTR-01 is unchanged).
