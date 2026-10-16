---
id: T-0373
title: ios-screenshot shoots the loop and trip regionUnsupported failure with "Count this area" and their waitlist card
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T07:22:19Z
lease_expires_at: 2026-10-17T07:22:19Z
worktree: .worktrees/T-0373
branch: task/T-0373
exclusive: []
touches: [.github/workflows/ios-screenshot.yml, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, queue/]
pins_affected: []
reviewer: null
depends_on: [T-0365]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0365 gave LoopScreen and RoadTripScreen the waitlist offer on regionUnsupported (`loop.failure.waitlist`,
`trip.failure.waitlist`, then the shared WaitlistCard), but no shot shows them: the shot list lives in
.github/workflows/ios-screenshot.yml, outside T-0365's touches (T-0365 R6). Add PlanRehearsalFixtures cases
(e.g. `loopRegion`, `tripRegion`, `loopWaitlist`, `tripWaitlist`: the failed sheet, and the card with an answer -
PlanRehearsal would need a per-tab waitlist answer the sub-screens read) and list them in the workflow's LIST and
plan-sheet case arm (and ops/lib/ios_screenshot_pinned.py if it pins the list). Acceptance: ios-screenshot success
with the new PNGs looked at, light and dark; the button reads "Count this area" and the card names what it sends.
Every apps/ios Swift edit re-approves its P-SAFE-03 digest.

## Log
- 2026-10-16T04:45:00Z filed by agent/claude-opus-5 from T-0365 R6 (ids checked on origin/main and every
  origin/task/* branch: highest T-0371).
- 2026-10-16T05:16:23Z renumbered T-0372 -> T-0373 by agent/claude-opus-5: main filed and claimed its own T-0372 (sane exit 4) after this was filed; this copy was unclaimed.
- 2026-10-16T07:22:19Z claimed by agent/claude-opus-5; lease until 2026-10-17T07:22:19Z
- 2026-10-16T07:25:09Z RULINGS (agent/claude-opus-5), measured before any code:
  - M1 the shot list: .github/workflows/ios-screenshot.yml CAPTURE step `LIST=` (light, dark) and the plan-sheet case
    arm `preview|nothingPretty|...|tripPaused)`; ops/lib/ios_screenshot_pinned.py CAPTURE_RUN is the same text, compared
    by equality (check-ios-compile-guardrails.py reads both). The only other reader of the names is
    PlanRehearsalFixtures.rehearsal(named:) (grep `loopPaused`: those three files only).
  - M2 the T-0365 shots (run 38858275055, downloaded to .artifacts/T-0373/t0365-shots): plan-loopPaused-light.png is the
    loop FORM - "Start / Topanga", "About 60 min of driving" stepper, the footer "You come back to where you started. One
    loop a day is free." and, in the last section, "Planning is resting for a moment. Try again in a little while.";
    plan-tripPaused-dark.png the trip form (Griffith Observatory, Leo Carrillo State Beach, 2 days, Up to 40%) with the
    same line in the last section. Below it ~900 pt of the sheet is empty, so nothing is clipped.
  - R1 (widening b, rv1-t0365 R3): NOT a rehearsal defect and not clipping. loopDegraded/tripDegraded never call
    startPlanning/finish: the state is `.chosen`, so LoopScreen/RoadTripScreen draw the `.idle, .chosen` form, whose
    `loop.degrade`/`trip.degrade` Text replaces Find a loop / Plan the road trip by design (T-0364 R3) - the line on
    screen is ConfigDegrade's notice, not `failure.line`, and the `.failed` branch (Try again, Change the loop/trip)
    was never on screen. No change to the paused rehearsals. The first shots of the `.failed` branch are R2's
    loopRegion/tripRegion, so Try again and Change are checked there (A4).
  - R2 (Brief) four cases: `loopRegion`/`tripRegion` - the sheet's own startPlanning + finish(.failure(.regionUnsupported))
    on the loop/trip rehearsal's places; `loopWaitlist`/`tripWaitlist` - the same failed sheet with
    PlanRehearsal.waitlist = .joined on tab .loop/.trip. No new per-tab field: `tab` + the existing `waitlist` are the
    per-tab answer; LoopScreen/RoadTripScreen seed their own showingWaitlist/waitlistAnswer @State from
    PlanRehearsal.atLaunch only when its tab is theirs (PlanSheetScreen's seeding is gated to tab .plan in the same
    diff, so one rehearsal answer seeds exactly one screen).
  - R3 (widening a, T-0362's address search): two cases `searchResults`/`searchNotice` - the plan sheet with Topanga
    chosen, searching the destination with the query "Pacific Coast Hwy Malibu" and a seeded PlaceSearchAnswer:
    `.places` (two address rows) and `.notice(...)`. PlanPlaceList's answer is private @State set only by a submit;
    it gains one `rehearsed: PlaceSearchAnswer?` seed (nil from every production call site) copied into `answer` on
    appear, and PlanSheetScreen seeds `query` and passes the seed from PlanRehearsal. FeaturePlanSheet may not import
    ScenicAPIClient (apps/ios Package.swift: DesignSystem, ScenicKit, PlaceStore), so PlaceSearchCopy.notPlannable
    cannot be referenced: the fixture carries the same literal and A4 checks the PNG's text equal to
    Sources/ScenicAPIClient/PlaceSearchCopy.swift's `notPlannable`. Address rows are fixture labels, not corpus rows
    (an address is never a corpus row); the rehearsal never plans, so their ids reach nothing.
  - R4 touches: every edit is under the declared touches (.github/workflows/ios-screenshot.yml,
    apps/ios/Packages/ScenicApp/Sources/, ops/lib/, queue/); no widening of touches needed. No root Sources/ change,
    so no root `swift test` is owed (ScenicKit untouched); the Apple package compiles only on ios-compile.
  - R5 AX5 pass unchanged (its LIST is the six layout shots; these are copy states already covered at default size).

### Acceptance (T-0373)
  A1 `PlanRehearsalFixtures.rehearsal(named:)` answers loopRegion, tripRegion, loopWaitlist, tripWaitlist,
     searchResults, searchNotice (grep quote); every file <= 300 lines (`bash ops/lib/check-line-cap`).
  A2 the workflow's light/dark LIST and its plan-sheet case arm name all six; ios_screenshot_pinned.py follows;
     `python ops/lib/ios_screenshot_pinned.py` and `python ops/lib/check-ios-compile-guardrails.py` exit 0.
  A3 every edited apps/ios Swift file's sha256 re-approved; `bash ops/lib/check-safety-disclaimer` exit 0.
  A4 ios-compile success and ios-screenshot success on task/T-0373 (run ids quoted); each of the 12 new PNGs
     (plan-<case>-light/dark) LOOKED AT with what it shows quoted: loopRegion/tripRegion the region line, a
     "Count this area" button, Try again and Change the loop/trip; loopWaitlist/tripWaitlist the card - "Count this
     area", the joined line and "What this sends: one rough area around your start ..."; searchResults the field
     with the query and the two address rows under "Addresses"; searchNotice the notPlannable line under "Addresses".
  A5 bare gates on the merged head: check-safety-disclaimer, ios_screenshot_pinned.py, check-mutate-population.py,
     check-line-cap, check-pins-yaml.py, queue-check.
