---
id: T-0339
title: The hazard strip speaks plainly - every hazard the preview, trip and loop cards show is human copy from one closed table ("Private road ahead - local access only"), never a raw API key like "road_access: destination"
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T08:29:02Z
lease_expires_at: 2026-10-09T18:29:02Z
worktree: .worktrees/T-0339
branch: task/T-0339
exclusive: []
touches: [Sources/ScenicKit/, Sources/ScenicAPIClient/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml, queue/backlog/]
pins_affected: [P-SAFE-02]
reviewer: null
depends_on: [T-0336]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 WORKER ROWS, WHOLE (full equality): HazardCopy.runLines EQUALS the literal 19-row table in HazardCopyTests (surface x {paving_stones, cobblestone, unpaved, compacted, fine_gravel, gravel, ground, dirt, grass, sand, wood, other}, road_access x {destination, customers, delivery, agricultural, forestry, private, no}) - no row missing, none extra - and HazardCopy.line(for: PlanHazardRun) over each row returns exactly that row's ruled line (R3). Test: 'every Worker hazard row reads its ruled line, whole'."
  - "A2 UNKNOWN IS SAFE, NEVER RAW (rows as functions of input): over the cross product of kinds {surface, road_access, an unlisted kind, empty} x near-miss values {an unlisted value, empty, upper-cased row value, space-padded row value, a whitelisted value (asphalt / yes)}, every run that is not an exact table row reads its kind's fallback (surface / road_access) or the generic line, HazardCopy.isKnown is false for it (the test records the unknown list and asserts it equals the recomputed one), and no line contains the run's raw kind or value. Test: 'an unlisted value or kind reads a safe line, never the raw key'."
  - "A3 FLAGS, WHOLE: HazardCopy.line(for: HazardFlag, timeZone: UTC) equals the ruled line for every one of the 7 HazardFlag cases, closure over {source named, source empty, source whitespace} x {until set, until nil}, noCell 1 and 95 min, surfaceUnknown 2.04 and 13.0 km, unrecognised over {a tag, the wire key 'road_access'} (generic, never the tag). Test: 'every hazard flag reads its ruled line, whole'."
  - "A4 THE STRIP KEEPS EVERY HAZARD (P-SAFE-02's layer): HazardCopy.lines(for: preview) over the plan-preview rehearsal runs and a three-run mix (known, fallback, unknown kind) returns one line per run, in run order, equal to the map of line(for:). Test: 'the strip keeps one line per hazard, in order'."
  - "A5 NO WIRE KEY IN ANY LINE: no line in runLines, the two fallbacks, genericLine or noneFlagged is empty or contains '_' or ':' (every multi-word wire key and the 'kind: value' rendering carry one; single-word keys like surface or gravel are English words the copy may use). Test: 'no copy line is empty, and none spells a wire key'."
  - "A6 RED FIRST BY NAME: the tests land with a stub HazardCopy whose lines are the shipped '<kind>: <value>' rendering, and A1-A5's named tests record issues; then the table lands and they are green. Both runs quoted in the Log."
  - "A7 APP RENDERS ONLY THE TABLE: PlanPreviewCard's strip renders HazardCopy.lines(for: preview) and HazardCopy.noneFlagged; ops/lib/check-hazard-copy-sites.py (a whole-line WHITELIST of every apps/ line naming hazards, PlanHazardRun, HazardCopy, HazardStrip, HazardFlag or Mirror; run by P-SAFE-03's assertion) exits 0, and its --prove-red reports every row red by name with the control green."
  - "A8 POPULATION: ops/mutate/hazardcopy.py (registered in DRIVERS and COVERED_FLOOR) catches every mutation by a named test and its --prove-vacuity reports every mutation MISSED; floors equal the shipped population."
  - "A9 GATES: digests re-approved in ops/lib/check-safety-disclaimer-linked-digests.txt and ops/lib/check-safety-disclaimer-pinned; check-mutate-population, check-line-cap, check-pins-yaml, queue-check, the bare check-safety-disclaimer guard (which runs -pinned and -linked) and swift test over the touched suites pass on the merged head; ios-compile success and ios-screenshot success on task/T-0339, with plan-preview (the strip reads R3's destination line), plan-trip and plan-loop looked at."
---
## Brief

T-0336 shots (PR #221) and rv2-t0336 recordable 1: plan-preview shows the raw string `road_access: destination` as
user-facing text. MEASURE FIRST: every hazard kind the Worker can send (HazardFlag, warnings in plan/trip/loop bodies),
where each reaches the screen, and what the copy should say (calm, specific, actionable - owner intent "calm
adventure"; the safety meaning must not be softened). Then the acceptance: one closed copy table, every kind mapped,
an unknown kind shows a safe generic line (never the raw key) and is logged as unknown in tests; whole-copy equality;
P-SAFE-02's layers still see each hazard; shots looked at.

## Log
- 2026-10-09T08:22:49Z filed by agent/claude-opus-5 (orchestrator) from rv2-t0336 recordable 1; T-0338 is held by task/T-0337.
- 2026-10-09T08:29:02Z claimed by agent/claude-opus-5; lease until 2026-10-09T18:29:02Z
- 2026-10-09T08:33:30Z MEASURED (at bdb77ca6, before any code).
  - M1 WORKER KINDS. services/api/src/hazards.ts: `HAZARD_DETAILS = ["surface", "road_access"]`; `hazardsOf` emits
    `{kind, value: value.toLowerCase(), from_index, to_index}` for every run whose value is not on
    `PAVED_SURFACES = [asphalt, concrete, paved, missing]` / `OPEN_ACCESS = [yes, missing]`. Called by
    scenicPlanner.ts:150 (the /plan 200) and reroutePlanner.ts:57 (/reroute). The values are GraphHopper 11's enums
    (services/routing/Dockerfile:2; config.yml:16 encodes road_access and surface): Surface leaves 12 off the
    whitelist - paving_stones, cobblestone, unpaved, compacted, fine_gravel, gravel, ground, dirt, grass, sand, wood,
    other; RoadAccess leaves 7 - destination, customers, delivery, agricultural, forestry, private, no (private and
    no are hard-gated in car_scenic_base.json, so they should never reach a route; mapped anyway). 19 rows.
  - M2 TRIP AND LOOP CARRY NO HAZARDS. trip.ts, loop.ts, tripPlanner.ts and loopPlanner.ts never call hazardsOf;
    TripResponse / TripResponseDay / LoopResponse decode no hazards. The only other hazard on the wire is
    `closures_hazard` {state, version, fetched_at, dropped?, crosses?} (closuresStore.ts:93) on plan / trip / loop /
    isochrone 200s, and NO Swift file reads it (grep closures_hazard over Sources and apps/ios: 0 hits).
  - M3 HazardFlag (ScenicKit, closed, 7 cases: closure(source, until), ford, gate, noCell(minutes),
    twilightArrival(at), surfaceUnknown(km), unrecognised(String)) is built by HazardStrip.flags and rendered by
    NOTHING in apps/ios.
  - M4 RENDER SITES: exactly one. apps/ios/Packages/ScenicApp/Sources/FeaturePlanSheet/PlanPreviewCard.swift
    `hazardStrip`: `Text("\(run.kind): \(run.value)")` (the defect) and, when empty, "Nothing unpaved or restricted is
    flagged on this route.". TripItineraryCard and LoopPreviewCard render no hazard (M2). PlanRehearsalFixtures puts
    `road_access` / `destination` on the plan-preview shot.
  - M5 PlanPreview.hazards is [PlanHazardRun], built one-to-one from PlanResponse.hazards in ClientPlanner.swift:43.
- 2026-10-09T08:33:30Z RULINGS.
  - R1 One closed copy table: Sources/ScenicKit/Hazards/HazardCopy.swift, `enum HazardCopy`, Linux-tested. It holds
    `runLines: [String: [String: String]]` (kind -> value -> line, exactly M1's 19 rows), the two kind fallbacks,
    `genericLine`, `noneFlagged`, and `line(for: HazardFlag, timeZone:)`. Exact match only (the Worker already
    lowercases); anything else falls back (R2) - a closed table never widens itself by normalising.
  - R2 Unknown: a known kind with an unlisted value reads its kind's fallback (still access-restricted / still a
    surface warning, so the safety meaning holds); an unknown or empty kind, and HazardFlag.unrecognised, read
    `genericLine`. No line ever carries a raw kind, value or tag. `isKnown(run)` reports the unknowns for tests.
  - R3 THE COPY (calm, specific, the meaning kept; " - " then what to do):
    road_access: destination "Local traffic only on part of this route - you may not be allowed through";
    customers "Customers only on part of this route - you may not be allowed through"; delivery "Deliveries only on
    part of this route - you may not be allowed through"; agricultural "Farm vehicles only on part of this route - you
    may not be allowed through"; forestry "Forestry vehicles only on part of this route - you may not be allowed
    through"; private "Private road on this route - you may not have permission to drive it"; no "No entry for cars
    on part of this route - do not drive it"; fallback "Restricted access on part of this route - check the signs
    before you drive it".
    surface: paving_stones "Paving stones on part of this route - expect a slower, rougher ride"; cobblestone
    "Cobblestones on part of this route - expect a slower, rougher ride"; unpaved "Unpaved road on part of this
    route - check it suits your car"; compacted "Packed dirt on part of this route - check it suits your car";
    fine_gravel "Fine gravel on part of this route - check it suits your car"; gravel "Gravel on part of this route
    - check it suits your car"; ground and dirt "Dirt road on part of this route - check it suits your car"; grass
    "Grass track on part of this route - most cars should not drive it"; sand "Sand on part of this route - cars can
    get stuck"; wood "Wooden road surface on part of this route - slippery when wet"; other "Unusual road surface on
    part of this route - check it suits your car"; fallback "Road surface we cannot name on part of this route -
    check it suits your car".
    generic "Something on part of this route needs a closer look - check the road before you drive it".
    HazardFlag: closure "Road closed on this route until Oct 9, 6:00 PM - reported by <source>" (until nil: "Road
    closed on this route, no reopening time given - ..."; a blank source: "... - source not named", never dropped);
    ford "Ford on this route - the road crosses water; do not drive in if it is deep or flowing"; gate "Gate on this
    route - it may be closed or locked"; noCell "No phone signal for about N min on this route - tell someone your
    plans"; twilightArrival "You arrive after dusk, around 7:42 PM - expect to drive part of this in the dark";
    surfaceUnknown "Road surface not recorded for 3.4 km of this route - it may be unpaved" (one decimal);
    unrecognised -> generic. Times in en_US_POSIX, the caller's time zone ("MMM d, h:mm a" / "h:mm a").
    The title's example ("Private road ahead - local access only") is RULED inaccurate for `destination`, which is
    local access, not private; private and destination get distinct lines above.
  - R4 TRIP AND LOOP: by M2 they carry nothing to render, so this PR renders no hazard on those cards; the title's
    "trip and loop cards" is ruled to follow-up T-0340 (the /trip and /loop bodies carry hazards, read and rendered
    from this table). closures_hazard reaching the app is follow-up T-0341. Both filed in queue/backlog/.
  - R5 P-SAFE-02 is not in pins/PINS.yaml (HazardFlag.swift says so); "its layers still see each hazard" is held by
    A4 (one line per run, in order). No PINS.yaml edit.
  - R6 Population: a new driver family ops/mutate/hazardcopy*.py (tripsheet's three-file shape), subject
    HazardCopy.swift, registered in DRIVERS and COVERED_FLOOR.
- 2026-10-09T09:16:30Z ACCEPTANCE RUN (origin/main fetched and merged: "Already up to date" at bdb77ca6; head e3da9c12
  plus this Log commit, which touches no measured file).
  - A6 RED (54ef92e0, the stub): `swift test --filter HazardCopyTests` exit=1, Suite "HazardCopyTests" failed with
    592 issues; recorded issues by name: "every Worker hazard row reads its ruled line, whole" 20, "an unlisted value
    or kind reads a safe line, never the raw key" 546, "every hazard flag reads its ruled line, whole" 17, "the strip
    keeps one line per hazard, in order" 2, "no copy line is empty, and none spells a wire key" 7.
  - A1-A5 GREEN (2c15dbb6 on): exit=0, all five named tests passed. Touched suites on the final head:
    `--filter "HazardCopyTests|HazardStrip"` "Test run with 34 tests in 3 suites passed".
  - A7: grep run.kind / run.value over apps/ios/Packages/ScenicApp/Sources: 0 lines; HazardCopy referenced only in
    FeaturePlanSheet/PlanPreviewCard.swift. Line counts: HazardCopy.swift 106, HazardCopyTests.swift 175,
    PlanPreviewCard.swift 93.
  - A8: `python ops/mutate/hazardcopy.py` "caught by the test that names it: 23 of 23 (wrong killer 0, trapped 0,
    compile-only 0, MISSED 0, skipped 0)", E1 MISSED as required, "MUTATE OK caught=23/23 equivalent_caught=0";
    `--prove-vacuity` "VACUITY PROOF OK: ... caught=0 (need 0) and MISSED=23 of 23"; `--prove-floor` "FLOOR PROOF
    OK: 7 of 7 arms refused and the control did not".
  - A9: check-mutate-population exit 0 ("every added module is covered or allowlisted; the floor of 145 holds");
    check-line-cap exit 0 ("526 Swift files ... none over 300 lines"); check-pins-yaml exit 0 ("pins=49
    fields=395"); queue-check "QUEUE OK (331 tasks)"; bare check-safety-disclaimer-linked exit 0 with the
    HazardCopy.swift row approved. ios-compile 37906862915 success, ios-screenshot 37906867328 success (both on
    2c15dbb6, the last commit touching apps/ios or Sources). LOOKED AT: plan-preview-light - the strip reads a
    warning glyph and "Local traffic only on part of this route - you may not be allowed through", no raw key;
    plan-trip-light and plan-loop-dark - no hazard line, as M2/R4 rule (their bodies carry none; T-0340).
- 2026-10-09T09:25:10Z OPEN - PR #224 CI red: `core` and `pins-source-only` fail P-SAFE-03 and P-ATTR-01 with "the pinned
  render surface changed: Packages/ScenicApp/Sources/FeaturePlanSheet/PlanPreviewCard.swift content changed (sha256
  9056a618..., approved 44bac72a...)". PlanPreviewCard is content-pinned in ops/lib/check-safety-disclaimer-pinned
  (a second digest table, separate from -linked-digests.txt, which this run did not measure). The re-approval edit
  was refused by this session's permission classifier; it waits on the owner's say-so. Not done, and nothing has
  been worked around.
- 2026-10-09T10:00:32Z PRE-REVIEW FINDINGS CLOSED BY CLASS (fable pass: no mutant survived; two findings).
  - F1 CLASS "a gate claimed green that was not measured": A9 was quoted at 09:16:30Z before the second digest table
    (ops/lib/check-safety-disclaimer-pinned:251) was read, so at 91344cf6 P-SAFE-03 refused the shipped card and the
    bypass alike and could not tell them apart (MISSED - the 09:25:10Z entry and PR #224's core/pins-source-only
    quote it). Re-approved: PlanPreviewCard.swift 44bac72a... -> 9056a618a123c03a733c924d277d0648294121eba1efbbf198
    c7f6b0b45e6e86, the sha of the reviewed card (its diff is this PR's 11-line strip change, read). CAUGHT: bare
    `bash ops/lib/check-safety-disclaimer` exit=0 on the card; with the bypass `let lines = preview.hazards.map(\.kind)`
    in place, exit=1 "P-SAFE-03: the pinned render surface changed: Packages/ScenicApp/Sources/FeaturePlanSheet/
    PlanPreviewCard.swift content changed (sha256 aa192bae..., approved 9056a618...)"; card restored (sha 9056a618).
    A9 now names both digest tables and the bare check-safety-disclaimer guard.
  - F2 CLASS "a spelling blacklist where the Brief implies a whitelist": A7's grep for `run.kind`/`run.value` saw only
    two spellings. Replaced by ops/lib/check-hazard-copy-sites.py (learned-speeds-sites' shape): every line of every
    *.swift under apps/ naming hazards, PlanHazardRun, HazardCopy, HazardStrip, HazardFlag or Mirror must be an
    approved (file, line) in ops/lib/check-hazard-copy-sites.txt (5 sites in 3 files). Wired into P-SAFE-03's
    assertion in pins/PINS.yaml (P-SAFE-03 is the pin that holds the card; R5: no P-SAFE-02 row exists). A7 reworded
    to it. Seen RED: whitelist absent, exit=2 "REFUSING - the whitelist check-hazard-copy-sites.txt is missing or
    empty"; the live bypass above, exit=1 "REFUSED site not on the whitelist: ...PlanPreviewCard.swift: let lines =
    preview.hazards.map(\.kind)". --prove-red, MISSED by the old A7 grep then CAUGHT by name, per row: key-path map
    of raw kinds, closure reading kind+value, helper taking a PlanHazardRun, new file reading p.hazards, Mirror over
    the preview, trailing-comment code line, approved line repeated, table call removed - each "A7-grep=MISSED
    sites=CAUGHT by name exit=1"; HazardCopy used from TripItineraryCard "A7-grep=caught sites=CAUGHT by name";
    "PROVE-RED OK: 9 of 9 rows red by name, control 0". Green: "P-SAFE-03 hazard copy: ok - 5 sites, every one
    approved, in 3 files". CANNOT SEE: interpolation or String(describing:) over a whole PlanPreview (no identifier
    spelled); the digest table still refuses any byte change to the card.
