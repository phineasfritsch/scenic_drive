---
id: T-0360
title: On regionUnsupported the app offers "Notify me" and posts /waitlist once - a WaitlistClient, the PlanFailureAction gains the waitlist action, and the screen says what it sent
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-15T20:51:41Z
lease_expires_at: 2026-10-16T20:51:41Z
worktree: .worktrees/T-0360
branch: task/T-0360
exclusive: []
touches: [.github/workflows/ios-screenshot.yml, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05]
reviewer: agent/rv1-t0360
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Survey 2026-10-10 (M6 "region waitlist"): the Worker has /waitlist (T-0293, T-0296);
Sources/ScenicKit/PlanSheet/PlanFailureAction.swift says there is no waitlist screen, and apps/ios has no waitlist
code.

MEASURE FIRST: /waitlist's request and answers (quote the Worker; what it stores - at most one 2-dp cell), how
regionUnsupported reaches the plan sheet today. RULE the action, what is sent (never more than one coordinate at
2 decimals), idempotence (once per region per install), and the copy for each answer. Tests through the shipping
client (exact body equality, every answer) and the failure-action table. Every apps/ios Swift edit needs the
P-SAFE-03 digest re-approval; if refused, ship the Linux slice and say so.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (top-6).
- 2026-10-15T20:51:41Z claimed by agent/claude-opus-5; lease until 2026-10-16T20:51:41Z
- 2026-10-15T20:56:06Z MEASURED (agent/claude-opus-5), before any code:
  - /waitlist (services/api/src/waitlist.ts, routed by index.ts ROUTES["/waitlist"]; outside the quota and the
    kill switch). Non-POST -> 405 {"error":"POST only"}. Body not JSON -> 400 {"error":"invalid_request",
    "detail":"the body is not JSON"}. parseCell: the body must be a JSON object of EXACTLY one key `cell`, a string
    passing h3Res5.ts isResolution5Cell (15 lowercase hex digits, mode 1, res 5, base <= 121, digits) - else 400
    invalid_request with a detail. No DB, no usable SESSION_JWT_SECRET, or any D1 throw -> 503
    {"error":"waitlist_unavailable"}. Otherwise 200 {"waitlisted":true} - ALSO when this caller's cell was already
    counted today (the dedupe is silent). Any other path is 404 {"error":"not found"}.
  - What it stores: waitlist(cell, count, updated_at = UTC day) and waitlist_seen(tag, day), tag =
    HMAC(dayKey, who + "\n" + cell); who = identifyCaller's bucket: the Bearer session's sub, else deviceIdentity =
    the `x-scenic-device` header when it matches DEVICE_ID, else the shared UNIDENTIFIED_DEVICE bucket. So a client
    that omits x-scenic-device shares ONE count per cell per day with every other anonymous caller. No coordinate is
    ever accepted: the one location is one res-5 cell (~253 km^2).
  - regionUnsupported today: Worker 422 {"error":"region_unsupported"} -> PlanResponseReader (case (422,
    "region_unsupported"?)) -> PlanError.regionUnsupported -> PlanError.failure -> PlanSheetFailure.regionUnsupported
    -> PlanSheet state .failed(ticket, .regionUnsupported) -> PlanSheetScreen.planContent -> PlanFailureCard(copy:
    PlanFailureCopy.of(failure)) = line "Drives can't be planned from that start yet. Try a start in a region we
    cover." + action .changeStart ("Change the start") -> act -> searchFor(.start). The ticket in .failed carries
    `origin: Coordinate`, the start. No waitlist code exists in Sources/ or apps/ios.
  - The shell (apps/ios/ScenicDrive/ScenicDriveApp.swift, outside touches) builds `PlanSheetScreen(planner:
    LivePlanner.make(), ...)`. ScenicAPIClient does not depend on Telemetry (H3Cell); LiveSurpriseLedger already
    injects `cellOf:` from PlanAdapter. The ios-screenshot shot list lives in .github/workflows/ios-screenshot.yml,
    whose whole parsed text ops/lib/ios_screenshot_pinned.py pins.
- 2026-10-15T20:56:06Z RULED (agent/claude-opus-5):
  - R1 THE ACTION. PlanFailureAction gains `.joinWaitlist`, appended after `.close`. regionUnsupported's row becomes
    line "Drives can't be planned from that start yet. We can count this area toward where we go next." with
    action .joinWaitlist. Brief vs reality: the Brief's button words "Notify me" promise a notification nothing can
    deliver (no push, no account address; /waitlist keeps a count per cell and no person) - the button says
    "Count this area". Loop and Trip regionUnsupported keep their lines (their failures carry no action enum) - out
    of scope, noted for a follow-up.
  - R2 WHAT IS SENT. Exactly POST <base>/waitlist, headers exactly {content-type: application/json,
    x-scenic-device: <install id lowercased>} (the Worker's dedupe bucket; without it every anonymous phone shares one
    count), body exactly `{"cell":"<cell>"}`. The cell = cellOf(lat2, lon2), lat2/lon2 = the ticket's origin rounded
    to 2 decimals ((x * 100).rounded() / 100, half away from zero) - cellOf is H3Cell.containing in the app, injected
    (ScenicAPIClient cannot import Telemetry and Package.swift is serial-only). No coordinate leaves the device; the
    cell is a function of a 2-dp point. No bearer, no account token. A start that is not finite, or lat outside
    [-90, 90], or lon outside [-180, 180], or a cellOf result that is not 15 lowercase hex digits is refused on the
    device with ZERO requests.
  - R3 ONCE PER REGION PER INSTALL. "Region" = the res-5 cell. WaitlistMemory remembers a cell only after a 200
    {"waitlisted":true}; a remembered cell answers .alreadyJoined with zero requests; every other answer remembers
    nothing, so a later tap may send again. The app's memory: UserDefaults `waitlist.joined.cells.v1`, on device only.
    One call is at most one request - nothing is retried. The screen hides the button while a request is out.
  - R4 ANSWERS AND COPY (WaitlistAnswer, ScenicKit, each line compared whole):
    joined (200 waitlisted true): "This area is counted. We sent one rough area around your start, about 250 square
    kilometres - never the place itself." / alreadyJoined: "This phone already counted this area. Nothing new was
    sent." / refusedOnDevice: "That start couldn't be turned into an area, so nothing was sent." / unavailable (503,
    or the app has no https base): "The waitlist isn't taking requests right now, so this area wasn't counted. Try
    again later." / failed (any 200 not {"waitlisted":true}, 400, 404, 405, any other status): "That didn't go
    through, so this area wasn't counted." / offline (no reply): "No reply came back, so this area may not be
    counted. Try again with signal."
  - R5 WHERE. ScenicKit: WaitlistJoining, WaitlistAnswer. ScenicAPIClient: WaitlistClient (WaitlistJoining),
    WaitlistMemory, WaitlistReplyReader. App: PlanAdapter WaitlistRoutePlanner (RoutePlanning & WaitlistJoining) and
    DefaultsWaitlistMemory; LivePlanner.make() returns `any RoutePlanning & WaitlistJoining` so the shell's call
    compiles unchanged and its whitelisted TelemetryRoutePlanner line stays byte-identical; FeaturePlanSheet
    WaitlistCard; a DEBUG `-screen waitlist` rehearsal. Touches gain .github/workflows/ios-screenshot.yml (the shot).
  - R6 P-PRIV-05: WaitlistClientTests joins the row's swift bindings by name (named-tests.json + PINS.yaml note).
### Acceptance (T-0360)
  A1 `swift test --scratch-path .build/t0360 --filter "ScenicAPIClientTests.WaitlistClientTests|ScenicKitTests.(PlanFailureCopyTests|WaitlistAnswerTests)"`
     green; every WaitlistClientTests test drives WaitlistClient.joinWaitlist(near:) over CountingPlanTransport:
     (a) the whole PlanHTTPRequest EQUALS its recomputation for several starts; (b) every Worker answer (200 true,
     200 false, 200 {}, 200 not JSON, 400, 404, 405, 429, 500, 503, no reply) -> one WaitlistAnswer after exactly one
     request, memory written only on joined; (c) every coordinate bound: lat -90/90 and lon -180/180 exact accepted
     with cellOf receiving exactly the bound, nextUp/nextDown outside each refused with zero requests, NaN/+inf/-inf
     per field refused; (d) rounding: cellOf receives exactly the 2-dp values; (e) a cellOf result of nil, 14 or 16
     digits, an uppercase or a non-hex digit refused with zero requests; (f) once per cell: a second join of a joined
     cell is alreadyJoined with zero new requests, another cell sends, a failed cell sends again.
  A2 PlanFailureCopyTests: regionUnsupported -> .joinWaitlist with R1's line; titles end "Close", "Count this area".
     WaitlistAnswerTests: every case's line whole.
  A3 `python ops/lib/run-named-tests.py P-PRIV-05` green with WaitlistClientTests bound.
  A4 ops/mutate/waitlist.py: every mutant CAUGHT by its named killer, literal floor.
  A5 bare gates: check-safety-disclaimer, check-mutate-population, check-mutate-only, check-line-cap,
     check-pins-yaml, check-exec-bits, queue-check.
  A6 ios-compile success and ios-screenshot success on task/T-0360; plan-waitlist-light/-dark PNGs looked at.
- 2026-10-15T21:33:18Z WORK (agent/claude-opus-5):
  - RED first: WaitlistClientTests, WaitlistAnswerTests and the edited PlanFailureCopyTests were written before any
    Sources code; `swift build --build-tests` failed by name - "cannot find type 'WaitlistClient' in scope",
    "cannot find 'WaitlistAnswer' in scope", "cannot find type 'WaitlistMemory' in scope". Then green: "Test run with
    16 tests in 4 suites passed" (WaitlistClientTests 8 incl. 20 bound rows, 11 answer rows, 7 rounding rows,
    11 refused cells, 4 class bounds; WaitlistAnswerTests 2; PlanFailureCopyTests 4; PlanOfferCopyTests 2).
  - A4: `python ops/mutate/waitlist.py --prove-floor` "FLOOR PROOF OK: 7 of 7 arms refused and the control did not";
    `python ops/mutate/waitlist.py` "caught by the test that names it: 43 of 43 (wrong killer 0, trapped 0,
    compile-only 0, MISSED 0, skipped 0)", E1 and E2 MISSED as required, "MUTATE OK caught=43/43
    equivalent_caught=0". The range-after-rounding mutant (11) and each one-ulp widening (5-8) were caught by
    the bound table by name.
  - A3: `python ops/lib/run-named-tests.py P-PRIV-05` "passed=71/72" - every WaitlistClientTests binding passed; the
    one red is PlaceStoreTests.UserStorePrivacyTests/noColumnNamesAPlaceOrATrail() MISSING, GRDB-gated and known not
    to build on this Windows box (the pin's own note; CI's Linux core job runs it).
  - App: WaitlistRoutePlanner, DefaultsWaitlistMemory, LiveWaitlist (PlanAdapter), WaitlistCard (FeaturePlanSheet),
    PlanSheetScreen/PlanRehearsal/PlanRehearsalFixtures and LivePlanner edited; their P-SAFE-03 digests re-approved
    in ops/lib/check-safety-disclaimer-pinned (four new rows); the emit-site whitelist gains LiveWaitlist.swift's
    `import Telemetry` row ("P-PRIV-05 emit sites: ok - 33 lines approved"); LivePlanner's TelemetryRoutePlanner line
    unchanged.
  - A6: ios-compile run 38807997046 success; ios-screenshot run 38808002035 success. plan-waitlist-light.png and
    plan-waitlist-dark.png LOOKED AT: title "Count this area", the joined line whole, the muted "What this sends"
    line, the "Change the start" button, both themes legible, the toolbar and bottom bar intact.
  - Follow-up NOT filed (budget): LoopFailure/TripFailure regionUnsupported have no waitlist action (R1).
- 2026-10-15T22:13:36Z REVIEW PASS (agent/rv1-t0360, round 1) on f3e78b90, PR #245:
  - Acceptance committed before code (1738a071 precedes d38f27be/cfc8cef0). A1: the touched filter plus
    PlanSheetGateTests ran "Test run with 25 tests in 4 suites passed". A2: whole-row copy and title tables read.
  - Reviewer mutants, not in ops/mutate/waitlist_mutations.py, both RED by name: R1 longitude sent to cellOf
    unrounded (`cellOf(Self.twoDecimals(start.latitude), start.longitude)`) -> "The cell is computed from the
    start at two decimals, half away from zero" 6 of 7 rows failed (WaitlistClientTests.swift:120); R2
    regionUnsupported's action back to .changeStart -> "every PlanSheetFailure has its one copy line and one
    action" failed (PlanFailureCopyTests.swift:54). "Test run with 14 tests in 3 suites failed ... with 7 issues";
    restored with git checkout -- Sources.
  - Gates bare, all exit 0: check-safety-disclaimer, check-mutate-population ("floor of 157 holds"),
    check-mutate-only, check-line-cap (597 files), check-pins-yaml (pins=50), check-exec-bits, queue-check (354).
  - gh pr checks 245: core pass, pins-source-only pass. ios-compile 38807997046 success and ios-screenshot
    38808002035 success on cfc8cef0; cfc8cef0..f3e78b90 touches only PINS.yaml and this file. plan-waitlist-light
    and -dark PNGs looked at: they match the Log.
  - origin/main is an ancestor of origin/task/T-0360 (merge-base --is-ancestor exit 0).
