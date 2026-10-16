---
id: T-0365
title: Loop and Trip sheets offer "Count this area" on regionUnsupported through the same WaitlistClient, once per cell per install
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T03:59:15Z
lease_expires_at: 2026-10-17T03:59:15Z
worktree: .worktrees/T-0365
branch: task/T-0365
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0360]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0360 (PR #245) R1 gave the plan sheet's regionUnsupported failure the `.joinWaitlist` action ("Count this area"),
backed by ScenicAPIClient's WaitlistClient (one res-5 cell from the start rounded to 2 dp, once per cell per
install, six answers each with its line). Loop and Trip were ruled out of scope there: LoopFailure and TripFailure
still offer no waitlist on their regionUnsupported failures (rv1-t0360 recordable 2).

MEASURE FIRST: how regionUnsupported reaches LoopFailure / TripFailure today and what start each carries. RULE the
action and copy (reuse PlanFailureAction.joinWaitlist and WaitlistAnswer lines; the same WaitlistMemory so a cell
joined from any sheet is joined once). Tests: the failure-copy tables for Loop and Trip gain the row (whole-line
equality); a cross-sheet row that a cell joined from Plan answers alreadyJoined from Loop with zero requests. Every
apps/ios Swift edit needs the P-SAFE-03 digest re-approval; if refused, ship the Linux slice and say so.

## Log
- 2026-10-15T22:30:00Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0360 recordable 2 / T-0360 R1.
- 2026-10-16T03:59:15Z claimed by agent/claude-opus-5; lease until 2026-10-17T03:59:15Z
- 2026-10-16T04:03:05Z MEASURE + RULE (agent/claude-opus-5), before any code:
  - M1 how regionUnsupported reaches the sheets: the Worker answers 422 `region_unsupported` on /loop at exactly one
    site, services/api/src/loop.ts:74 `if (!inServedRegion(request.start))`, and on /trip at exactly one,
    trip.ts:83 `if (!inServedRegion(request.origin))` (grep over src/loop*.ts and src/trip*.ts: no other site, the
    planners never send it). LoopReplyReader.swift:21 / TripReplyReader.swift:23 read (422, "region_unsupported")
    as LoopError/TripError.regionUnsupported, LoopError.swift:27 / TripError.swift:28 map it to
    LoopFailure/TripFailure.regionUnsupported. No ScenicKit code makes either on the device.
  - M2 the start each carries: the coordinate the Worker judged is the request's start, which is the ticket's -
    `LoopTicket.start` (LoopSheet.startPlanning cuts it to 2 dp) and `TripTicket.origin` (TripSheet cuts it to 2 dp).
    The failed state keeps that ticket: `LoopSheetState.failed(LoopTicket, LoopFailure)`,
    `TripSheetState.failed(TripTicket, TripFailure)`.
  - M3 the screens today: LoopScreen and RoadTripScreen show `failure.line` + "Try again" + "Change the loop/trip";
    neither holds a WaitlistJoining. PlanSheetScreen holds `planner: any RoutePlanning & WaitlistJoining &
    PlaceSearching` (the shell's one LivePlanner, whose WaitlistClient carries DefaultsWaitlistMemory) and builds
    both sub-screens itself, so the same joiner can be handed down with no shell change and no new target dependency.
  - M4 the failure-copy tables the Brief names do not exist for Loop/Trip: LoopSheetTests/TripSheetTests only check
    the lines are distinct and calm. They are created here, whole-line, over allCases.
  - R1 action: LoopFailure and TripFailure gain `waitlistAction: PlanFailureAction?` - an exhaustive switch,
    `.joinWaitlist` for regionUnsupported, nil for every other case. The button's words are
    `PlanFailureAction.joinWaitlist.title` ("Count this area"); the two existing buttons stay.
  - R2 copy: the regionUnsupported lines gain the plan sheet's second sentence (T-0360 R1):
    Loop "Loops start inside the area we cover for now. We can count this area toward where we go next."
    Trip "Road trips start inside the area we cover for now. We can count this area toward where we go next."
    Every other line is unchanged. The answer is WaitlistAnswer.line on the unchanged WaitlistCard.
  - R3 the start, one binding per sheet: `LoopSheet.waitlistStart`, `TripSheet.waitlistStart` and
    `PlanSheet.waitlistStart` (Coordinate?) - the failed ticket's start/origin iff the failure offers
    `.joinWaitlist` (Loop/Trip: `waitlistAction`; Plan: `PlanFailureCopy.of(failure).action`), else nil. Each screen
    joins only through it. PlanSheetScreen moves from "any failed ticket's origin" to it; that path was reachable only
    from the .joinWaitlist action, so the plan's behaviour is unchanged. Privacy unchanged (Brief): WaitlistClient is
    still the only sender, one res-5 cell from the 2-dp start, never a coordinate.
  - R4 one memory: LoopScreen and RoadTripScreen take `waitlist: any WaitlistJoining`, which PlanSheetScreen passes as
    its own `planner` - the same WaitlistClient, the same DefaultsWaitlistMemory, so a cell joined from any sheet is
    joined once per install. Each sub-screen keeps its own showing/answer state, cleared on edit/try again/search.
  - R5 touches: the cross-sheet row needs ScenicAPIClient's WaitlistClient, which ScenicKitTests does not depend on
    (Package.swift is serial-only and not touched); it lives in Tests/ScenicAPIClientTests/, added to `touches:` by
    this ruling (not a serial-only path). It is bound by name under P-PRIV-05 in ops/lib/named-tests.json.
  - R6 shots: the shot list is .github/workflows/ios-screenshot.yml, outside touches; no new loop/trip waitlist shot
    in this task. ios-screenshot must stay success and the existing loop, trip and waitlist PNGs are looked at.
  - R7 mutants: no Sources/ file is added, so P-PROC-06 asks no new population; the loopsheet and tripsheet
    populations gain the new lines' mutants (action dropped, start ungated, raw start, line reworded) with raised
    literal floors, run with `--only`.

### Acceptance (T-0365)
  A1 `swift test --jobs 4 --scratch-path .build/t0365 --filter "ScenicKitTests.(LoopSheetTests|TripSheetTests|PlanWaitlistStartTests)|ScenicAPIClientTests.WaitlistAcrossSheetsTests"`
     green, with: (a) LoopSheetTests `every loop failure's line and waitlist action, whole` and TripSheetTests
     `every trip failure's line and waitlist action, whole` - every case's (line, waitlistAction) EQUAL to a literal
     row, the table's keys equal to allCases; regionUnsupported's row is R2's line with .joinWaitlist, every other
     row nil; (b) LoopSheetTests/TripSheetTests `the waitlist start is the failed ticket's 2-dp start only on
     regionUnsupported` - every failure x two starts (pier, ojai): waitlistStart == the ticket's start for
     regionUnsupported, nil otherwise, and nil in every non-failed state; (c) PlanWaitlistStartTests the same over
     every PlanSheetFailure; (d) WaitlistAcrossSheetsTests `a cell joined from one sheet is alreadyJoined from every
     other with zero requests` - Plan, Loop, Trip x Plan, Loop, Trip, each pair through one WaitlistClient and one
     MemoryWaitlist, joining from each sheet's waitlistStart: the first is joined with exactly the one recomputed
     request, the second alreadyJoined, the transport's requests still exactly that one; cellOf asked with the 2-dp
     start each time.
  A2 RED first: (a)-(d) written before waitlistAction/waitlistStart exist - the build fails naming them.
  A3 `python ops/lib/run-named-tests.py P-PRIV-05` green with WaitlistAcrossSheetsTests bound.
  A4 `python ops/mutate/loopsheet.py --only <new ids>` and `python ops/mutate/tripsheet.py --only <new ids>`: every
     new mutant CAUGHT by its named killers; floors raised.
  A5 bare gates: check-safety-disclaimer (digests re-approved), check-mutate-population, check-mutate-only,
     check-telemetry-emit-sites, check-line-cap, check-pins-yaml, check-exec-bits, queue-check.
  A6 ios-compile success and ios-screenshot success on task/T-0365; plan-loop, plan-trip and plan-waitlist PNGs
     looked at.
