---
id: T-0306
title: Saved drives in the app - save from the route preview, a Saved list (newest first, rename, delete), "needs a re-plan" shown honestly, and replay as one plan with the saved waypoints at today's time
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T19:10:14Z
lease_expires_at: 2026-10-08T15:10:14Z
worktree: .worktrees/T-0306
branch: task/T-0306
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, Sources/PlaceStore/, Tests/PlaceStoreTests/, Sources/ScenicAPIClient/ClientPlanner.swift, Tests/ScenicAPIClientTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/Packages/ScenicApp/Tests/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05, P-ATTR-01, P-SAFE-03]
reviewer: agent/rv1-t-0306
depends_on: [T-0290, T-0294, T-0303]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULE FIRST in a dated Log entry: where the Saved list lives without a Package.swift edit (an existing feature target that already imports PlaceStore - no new target; if one is unavoidable, stop and rule it with the package-swift lock), how a PlanResponse becomes a SavedDrive (segment ids + 5-dp midpoints + lambda + budget - T-0290's shape, nothing else), and how replay builds one /plan request - RULE the disagreement between the plan's 'replay = one /plan with the saved waypoints' and the invariant 'the server never receives more than one coordinate per user action, never more than 2 dp' (read services/api/src/plan.ts's body whitelist: what can a replay send today?) and quote the ruling; never widen the Worker whitelist in this task"
  - "A ScenicKit state machine for the Saved list (loading, list, renaming, confirmDelete, needsReplan, replaying) with a table test over every transition by full equality; replay of a needsReplan drive is refused with its own copy line; the Saved list never shows an address (P-PRIV-05)"
  - "The PlanResponse -> SavedDrive conversion is a full-equality table including more-than-5-dp midpoints (rounded once, at save, with a ruled rule - never silently twice) and an empty route"
  - "Every map surface keeps AttributionFooter visible (P-ATTR-01: no partial-detent sheet over the map; any new presentation gets a typed whole-line approval); ios-compile + ios-screenshot pass on the head; digests re-approved in ops/lib/check-safety-disclaimer-linked-digests.txt"
  - "A mutation population for the conversion and the state machine with a literal floor; three entries MISSED before and CAUGHT by name after"
---
## Brief

Plan, Runtime lifecycles, Saved drives: "On-device (GRDB) only: segment ids + 5-dp midpoints + lambda + B; re-resolve on
corpus activation; mark needs re-plan if unresolved; replay = one /plan with the saved waypoints at the new time; if today
is +31 not +25, say so." T-0290 shipped the store; T-0294 the plan sheet and preview. Calm copy (memory owner-route-intent).

## Log
- 2026-10-07T19:09:58Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M6 saved drives UI).
- 2026-10-07T19:10:14Z claimed by agent/claude-opus-5; lease until 2026-10-08T15:10:14Z
- 2026-10-07T19:15:04Z MEASURE, then RULINGS before code. agent/claude-opus-5 (owner).
  MEASURED: root Package.swift - PlaceStore depends on GRDB only, ScenicKit on nothing, ScenicAPIClient on ScenicKit;
  no root target sees both ScenicKit and PlaceStore. ScenicApp/Package.swift - FeaturePlanSheet already depends on
  DesignSystem + ScenicKit + PlaceStore and rides the FeatureScenicHome product the shell links. PlanResponse carries
  route, lambda and `waypoints` (scenicPlanner.ts `decisionPoints(chosen)`) and NO segment ids; PlanPreview (what the
  sheet sees) carries neither waypoints nor lambda. SavedDrive (T-0290 R3): name, segments (segmentID + 5-dp
  midpoint), lambdaE5, budgetMinutes, createdAt, needsReplan - no origin, no destination place, no ETA. FiveDecimals
  REFUSES more than 5 dp (never rounds). services/api/src/planRequest.ts: BODY_KEYS = ["origin", "destination",
  "budget_minutes", "departs_at"], ORIGIN_KEYS lat/lon at 2 dp, DESTINATION_KEYS = ["place"] (a corpus place id).
  check-map-attribution-sheet SHEET_PRESENTERS = .sheet( .fullScreenCover( .popover( .inspector( presentationDetents.
  - R1 WHERE: the Saved list lives in FeaturePlanSheet as in-sheet content of the full-height plan sheet (a "Saved"
    toolbar button switches the sheet's content; no NavigationLink push, no .sheet/.alert/.confirmationDialog). NO new
    target, NO Package.swift edit, NO new presentation, so P-ATTR-01's whitelist is unchanged.
  - R2 CONVERSION, in three hops because no root target sees both ScenicKit and PlaceStore: (a) ClientPlanner.preview
    now carries PlanResponse.waypoints and .lambda into PlanPreview (two new fields); (b) ScenicKit `SavedDraft.of(
    preview, budgetMinutes:, name:, createdAt:)` is THE rounding site: midpoints = [route.first] + waypoints +
    [route.last], each axis and lambda rounded ONCE to 5 dp, half away from zero ((v * 1e5).rounded() / 1e5); an empty
    route gives nil (nothing to save, the Save button is not offered); (c) PlaceStore `SavedDrive.unresolved(...)`
    builds the T-0290 value through the existing refusing gate (FiveDecimals refuses, never rounds - so a value is
    rounded once, never twice), every segment id `SavedSegment.unplaced` = -1, and the app then runs the shipped
    `SavedDriveResolver.resolve` against the bundled corpus (nearest within 25 m, else needsReplan) before saving. The
    route's two ends are kept so replay has an origin and a destination: the T-0290 shape holds neither otherwise.
    Full-equality tables: ScenicAPIClientTests (PlanResponse -> ClientPlanner.preview -> SavedDraft.of, one table) and
    PlaceStoreTests (SavedDraft-shaped doubles -> SavedDrive.unresolved, not GRDB-gated).
  - R3 REPLAY vs THE INVARIANT. The plan says "replay = one /plan with the saved waypoints"; CLAUDE.md says "the server
    never receives more than one coordinate per user action, never more than 2 decimal places", and the whitelist
    accepts exactly origin{lat,lon at 2 dp} + destination{place} + budget_minutes + departs_at. RULED: the invariant
    wins and the whitelist is not widened. A replay is ONE /plan whose origin is the saved first point at 2 dp (the
    one coordinate), whose destination is the corpus place nearest the saved last point (found on the device, within
    0.01 deg), and whose budget is the saved budget; the waypoints never leave the device - they key the re-resolve
    and decide needsReplan. "At today's time": like every plan today, no departs_at is sent, so the Worker plans for
    now. The replay goes through PlanSheet's one gate (`PlanSheet.replay(from:to:budgetMinutes:)` -> startPlanning),
    so P-SAFE-03 holds. "+31 not +25, say so": NOT shipped - a SavedDrive holds no ETA (T-0290 shape, nothing else),
    so there is nothing to compare against; recorded, not faked.
  - R4 STATE MACHINE: ScenicKit `SavedList` over `SavedRow` (id, name, createdAt, needsReplan, start, end, budget -
    no address field; the row's shown lines are its name and a detail line with no coordinate). States loading, list,
    renaming(id, text), confirmDelete(id), needsReplan(id), replaying(id). A rename commits the trimmed text of 1...60
    characters, otherwise stays renaming. Replay of a needsReplan drive (or one with no nearby place) goes to
    needsReplan with its own copy line and issues nothing. Rows are kept newest first (createdAt desc, id desc).
  - R5 PROOF: tests first, run RED by name; population ops/mutate/savedlist.py (+_mutations, _run) with a literal
    floor; digests re-approved for every touched Sources/ and apps/ios file; ios-compile + ios-screenshot dispatched.
  - R6 TOUCHES WIDENED (ruled on contact, the pre-commit hook refused): R2 hop (a) is ClientPlanner.preview, so
    `Sources/ScenicAPIClient/ClientPlanner.swift` and `Tests/ScenicAPIClientTests/` join touches; the existing
    PlanSheetGateTests "a 200 reaches the sheet as the preview of exactly that response" now expects the waypoints
    and lambda too (its full-equality oracle, widened by the two new fields).
- 2026-10-07T20:06:04Z RESUMED (session restart) by agent/claude-opus-5 (owner). RULED: the tests and the code landed
  together in 2c8e45af and no RED was recorded then, so RED is shown now against STUBS of every shipping symbol the
  tests bind to (SavedList's eleven writes, SavedRow.detail, SavedDraft.of + fiveDecimals, SavedReplay.nearest,
  PlanSheet.replay, SavedDrive.unresolved's segments, SavedSegment.unplaced, ClientPlanner's two new fields), stubs
  applied by a throwaway script under .build/ and restored (git status Sources clean after). `swift test --scratch-path
  .build/t0306 --filter SavedListTests|SavedReplayTests|SavedDraftTests|SavedDriveUnresolvedTests|PlanSheetGateTests`:
  `Test run with 23 tests in 5 suites failed ... with 64 issues`, exit 1, RED by name (14): every state x every
  event lands whole; rows are kept newest first, a tie broken by the higher id first; a rename commits the trimmed
  name of 1...60 characters and nothing else; a refused replay has its own calm copy line; a drive with no saved ends
  cannot be replayed and is shown as needing a re-plan; P-PRIV-05: the Saved list never shows an address...; the
  destination is found within 0.01 degrees on each axis...; the nearest place wins...; P-SAFE-03: a replay is one
  ticket through the sheet's gate...; P-SAFE-03: no ticket from a replay before the disclaimer is accepted...; a
  replay's budget is clamped to 0...180 at every bound...; PlanResponse -> preview -> SavedDraft by full equality...;
  5-dp points become unplaced segments in order...; a 200 reaches the sheet as the preview of exactly that response.
  Stayed green under the stubs, and why: "a saved point rounded once is not moved by rounding it again" (an
  idempotence property - an identity stub satisfies it; the DRAFT table is the rounding's killer), "more than 5 dp is
  refused by field" (T-0290's FiveDecimals gate, not stubbed), "no points is a drive with no segments" (the
  segments-[] stub coincides with the right answer for no points), and the five pre-existing PlanSheetGateTests.
  PRE-REVIEW MUTANT PASS (acceptance 5, "three entries MISSED before and CAUGHT by name after"): three unwritten
  mutants added as entries 31-33, floor 30 -> 33 - 31 `let start = row.start ?? row.end` (only the both-nil row is
  tested), 32 `.rounded(.toNearestOrEven)` (no exact tie in the DRAFT table: measured 34.000005 * 1e5 == 3400000.5 and
  -118.000005 * 1e5 == -11800000.5 exactly in binary64), 33 `name.unicodeScalars.count` (the 60-character row is
  ASCII). Run --only 31,32,33 at this commit, then the test rows, then again.
- 2026-10-07T20:39:10Z RESULTS, as each stage landed. agent/claude-opus-5 (owner).
  - MISSED BEFORE (8982439c, `python ops/mutate/savedlist.py --only 31,32,33`): `MISSED 31 a missing start replayed
    from the end exit=0`, `MISSED 32 a half-way tie rounded to even exit=0`, `MISSED 33 the name cap counted in
    scalars exit=0`; `MUTATE FAILED caught=0/3`.
  - Test rows (f906a387): NOENDS now ranges over {both, start, end} missing; DRAFT gains the exact-tie row
    (34.000005, -118.000005, 34.000025, -118.000025 -> 34.00001, -118.00001, 34.00003, -118.00003); RENAME gains 59
    "a" + "e\u{301}" (60 characters, 61 scalars) kept and its + "b" refused.
  - CAUGHT AFTER (f906a387, same command): `caught 31 ... by: a drive missing either saved end cannot be replayed and
    is shown as needing a re-plan`, `caught 32 ... by: PlanResponse -> preview -> SavedDraft by full equality: >5 dp
    rounded once, 5 dp kept, the ends, empty`, `caught 33 ... by: a rename commits the trimmed name of 1...60
    characters and nothing else`; `MUTATE OK caught=3/3`.
  - FULL RUN (f906a387, all 33 + E1): `caught by the test that names it: 32 of 33 (wrong killer 0, trapped 0,
    compile-only 0, MISSED 1, skipped 0)`, `MISSED 9 a needs-replan drive replayed exit=0`, E1 MISSED as required.
    Ruled: a fourth survivor - replay(3)'s canyon had no place within reach of its end, so the transitions table
    refused it for reach, never for needsReplan. Fixed (93d404df): `canyonEnd` (id 43) AT the canyon's saved end joins
    the table's places. `--only 9`: `caught=1/1`, `MUTATE OK`. The full population at 93d404df: 33 of 33 by name
    (32 at f906a387 whose subjects are unchanged since, + 9 re-run - memory faster-verification-in-rounds).
  - `--prove-vacuity --only 9,31,32,33`: `VACUITY PROOF OK: ... caught=0 (need 0) and MISSED=4 of 4`.
    `--prove-floor`: `FLOOR PROOF OK: 7 of 7 arms refused and the control did not` - the "SavedDraft.swift unmutated"
    arm had been refused by the COUNT (27 + 3 < floor), not by the unmutated subject; now padded back to the whole
    count with non-SavedDraft entries, it refuses with `no MUTATIONS entry edits SavedDraft.swift`.
  - GREEN: `swift test --scratch-path .build/t0306 --filter SavedListTests|SavedReplayTests|SavedDraftTests|
    SavedDriveUnresolvedTests|PlanSheetGateTests|PlanSheetTests`: `Test run with 33 tests in 6 suites passed`.
  - iOS (app sources unchanged since 82cbfe27): ios-compile 37679241204 success, ios-screenshot 37679245297 success on
    6fcdba2f; re-dispatched on the final merged head.
  - RULED, NOT DONE: P-PRIV-05's run-named-tests row is NOT widened to bind SavedListTests/neverAnAddress() - it
    could not be seen red here (that row's vitest half needs services/api/node_modules, absent on this box) and an
    unseen binding is untested; the test and mutant 24's catch hold it. "+31 not +25, say so" stays unshipped (R3).
- 2026-10-07T21:27:18Z PRE-REVIEW PASS 2: TWO SURVIVORS (BLOCKING), closed by class. agent/claude-opus-5 (owner).
  - RULED: M2 (SavedRow.renamed with `needsReplan: false`) survived because every rename row renamed id 1 only, a
    row whose flag is already false; the class is "a rename changes a field other than the name, on a row the
    table never renames". M3 (SavedList.confirmDelete with `rows.removeFirst()`) survived because the only
    confirmDelete row confirmed id 2, which sits at index 0, so by-position and by-id agree; the class is "delete
    identity at a position the table never confirms". Both closed by making the rows functions of the id over
    EVERY position of `sorted` (first, middle, last), the expected rows written out field by field - never
    derived from the row under test - and a meta-assert that the table's ids are exactly `sorted`'s.
  - MISSED BEFORE (0babcda2, `python ops/mutate/savedlist.py --only 34,35`): `MISSED 35 delete by position, not by
    id exit=0 no test objected`; `caught by the test that names it: 0 of 2 (... MISSED 2 ...)`;
    `MUTATE FAILED caught=0/2`.
  - Tests (1c59551b): `renameEveryRow` renames mulholland, the needs-replan canyon and topanga in turn, asserts
    the whole list by full equality, then replays the renamed id - canyon (3) stays refused into .needsReplan,
    topanga yields the same SavedReplay as before the rename. `deleteEveryRow` confirms ids 2, 3, 1 and asserts
    each surviving list written out.
  - CAUGHT AFTER (1c59551b, same command): `caught 34 a rename clears the re-plan flag by: a rename changes only
    the name, at every position: the re-plan flag, ends, budget and replay kept`, `caught 35 delete by position,
    not by id by: a confirmed delete removes exactly the confirmed drive, at every position`; `MUTATE OK
    caught=2/2`. Population 35 + E1, MIN_MUTATIONS 35.
  - `--prove-vacuity --only 34,35`: `VACUITY PROOF OK: with the 4 test file(s) emptied, caught=0 (need 0) and
    MISSED=2 of 2`. `--prove-floor`: `FLOOR PROOF OK: 7 of 7 arms refused and the control did not`.
  - GREEN: `swift test --scratch-path .build/fm-t-0306 --filter SavedListTests|SavedReplayTests|SavedDraftTests|
    SavedDriveUnresolvedTests`: `Test run with 18 tests in 4 suites passed`. No Sources/ or apps/ios file changed,
    so no digest row moves; the other 33 mutants' subjects and killers are unchanged (memory
    faster-verification-in-rounds: only the touched rows re-run).
- 2026-10-07T22:10:24Z REVIEW PASS by agent/rv1-t-0306 (reviewer, not the owner) on head 394eb9f7, PR #196.
  ACCEPTANCE: R1-R6 ruled at 19:15:04Z before code; R3 keeps the Worker whitelist (replay = one /plan, start at 2 dp,
  destination{place}, saved budget, through PlanSheet.replay -> startPlanning). FeaturePlanSheet imports only
  DesignSystem, ScenicKit, PlaceStore, SwiftUI, Foundation; no pbxproj or Package.swift in the diff; the Saved list
  is in-sheet content, no new presentation; AttributionFooter unchanged (P-ATTR-01 guard exit 0).
  REVIEWER MUTANTS (not in the population, each RED by name):
  - R1 drop `state = .chosen(saved.destination)` in PlanSheet.replay: RED - "P-SAFE-03: a replay is one ticket
    through the sheet's gate - the start at 2 dp, the place, the budget", "P-SAFE-03: no ticket from a replay before
    the disclaimer is accepted; the drive waits, chosen", "a replay's budget is clamped to 0...180 at every bound, and
    a start off 2 dp leaves at 2 dp"; 10 issues.
  - R2 `current.distance < distance` -> `<=` in SavedReplay.nearest: RED - "the nearest place wins, distance east-west
    scaled by the latitude, a tie to the lower id, none from none" (SavedReplayTests.swift:45, id 9 instead of 4).
  BARE: swift test (Saved*Tests + PlanSheetGateTests) `25 tests in 5 suites passed`; check-safety-disclaimer exit 0;
  check-map-attribution exit 0; check-mutate-population exit 0; check-line-cap exit 0 (none over 300);
  check-pins-yaml ok pins=44; queue-check QUEUE OK (297 tasks); gh pr checks core + pins-source-only pass;
  ios-compile + ios-screenshot dispatched on 394eb9f7, both completed success; origin/main is an ancestor of head.
  RECORDED, not blocking: P-PRIV-05's named-tests row does not bind SavedListTests/neverAnAddress() (owner's open
  item); "+31 not +25, say so" not shipped (no ETA in the T-0290 shape, ruled R3).
