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
- 2026-10-16T07:57:51Z WORK (agent/claude-opus-5): code c8d9cb50, merged origin/main a137f16c as 196e6b0e (the merge
  touches no apps/ios, digest or workflow file, so the CI runs below on c8d9cb50 shot the merged head's app tree).
  - M3 found while editing: ios_screenshot_pinned.py's SHOTS_LIST prove-red anchor was stale on main (it lacked
    `waitlist`, added by T-0360): `check-ios-compile-guardrails.py --prove-red` ended "PROVE-RED REFUSING: ... the
    mutation 'T-0324: the drive shot dropped' does not apply exactly once - its anchor is stale". SHOTS_LIST now
    equals the shipped LIST; the two rows anchored on " nothingPretty offered" / " preview nothingPretty offered loop
    trip saved" follow; two T-0373 rows added (the six dropped from LIST; the six dropped from the plan arm). After:
    "PROVE-RED OK: 96 mutations red, 6 legitimate spellings green over 2 workflows, 0 unexpected result(s)", both
    T-0373 rows `[red rc=1] ... steps[4].run: differs from the pinned value`.

### Acceptance (T-0373) - re-quoted on the merged head 196e6b0e
  A1 PASS. rehearsal(named:) cases: "loopRegion", "tripRegion", "loopWaitlist", "tripWaitlist", "searchResults",
     "searchNotice". wc -l: PlanRehearsalFixtures 202, PlanSheetScreen 266, LoopScreen 136, RoadTripScreen 141,
     PlanPlaceList 79, PlanRehearsal 45; check-line-cap "P-SRC-02: 674 Swift files tracked (...apps/ios=109), none
     over 300 lines" exit 0.
  A2 PASS. LIST (light, dark) "... update loopPaused tripPaused loopRegion tripRegion loopWaitlist tripWaitlist
     searchResults searchNotice legal"; plan arm "...|loopPaused|tripPaused|loopRegion|tripRegion|loopWaitlist|
     tripWaitlist|searchResults|searchNotice)"; ios_screenshot_pinned.py exit 0; check-ios-compile-guardrails.py
     "IOS-COMPILE-GUARDRAILS OK: ios-screenshot.yml equals the pinned workflow ..." exit 0.
  A3 PASS. Six rows re-approved in ops/lib/check-safety-disclaimer-pinned (LoopScreen, PlanPlaceList, PlanRehearsal,
     PlanRehearsalFixtures, PlanSheetScreen, RoadTripScreen; sed 's/\r$//' | sha256sum); check-safety-disclaimer
     exit 0 ("... LAST all 109 app .swift, then 326 root + pbxproj file(s) (-linked).").
  A4 PASS. ios-compile 38867768624 success (2m12s); ios-screenshot 38867771811 success (17m28s), 60 PNGs, downloaded
     to .artifacts/T-0373-shots. Looked at, light and dark each:
     - plan-loopRegion: title "Just drive a loop"; "Loops start inside the area we cover for now. We can count this
       area toward where we go next."; buttons "Count this area", "Try again", "Change the loop".
     - plan-tripRegion: "Plan a road trip"; "Road trips start inside the area we cover for now. We can count this area
       toward where we go next."; "Count this area", "Try again", "Change the trip".
     - plan-loopWaitlist / plan-tripWaitlist: headline "Count this area"; "This area is counted. We sent one rough area
       around your start, about 250 square kilometres - never the place itself."; footnote "What this sends: one
       rough area around your start, worked out from it rounded to two decimals. Never the start itself, and once
       per area from this phone."; the filled "Change the start" button (light: white on orange; dark: dark on
       light orange); titles "Just drive a loop" / "Plan a road trip".
     - plan-searchResults: "Plan a drive", toolbar "Saved" + "Back"; field "Pacific Coast Hwy Malibu"; footer "Press
       Search to look up a street address."; section "Addresses" with "29500 Pacific Coast Hwy, Malibu, CA 90265" and
       "30000 Pacific Coast Hwy, Malibu, CA 90265" (no corpus row matches the query, so that section draws nothing).
     - plan-searchNotice: the same field and footer; "Addresses" holding "Address search found places but can't plan
       to them right now." - equal to Sources/ScenicAPIClient/PlaceSearchCopy.swift `notPlannable`.
     R1 confirmed in the shots: the `.failed` branch draws Try again and Change on both tabs; the paused shots stay
     the form's degrade notice.
  A5 PASS on 196e6b0e, each bare: check-safety-disclaimer 0, ios_screenshot_pinned.py 0, check-ios-compile-guardrails
     0, check-mutate-population.py 0, check-line-cap 0, check-pins-yaml.py "PINS-YAML ok pins=51 fields=411" 0,
     queue-check "QUEUE OK (365 tasks)" 0.
