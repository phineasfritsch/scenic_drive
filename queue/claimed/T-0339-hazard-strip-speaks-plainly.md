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
  - "A7 APP RENDERS ONLY THE TABLE: PlanPreviewCard's strip renders HazardCopy.lines(for: preview) and HazardCopy.noneFlagged; grep over apps/ios/Packages/ScenicApp/Sources for 'run.kind' and 'run.value' prints nothing and HazardCopy is referenced only from PlanPreviewCard.swift."
  - "A8 POPULATION: ops/mutate/hazardcopy.py (registered in DRIVERS and COVERED_FLOOR) catches every mutation by a named test and its --prove-vacuity reports every mutation MISSED; floors equal the shipped population."
  - "A9 GATES: digests re-approved in ops/lib/check-safety-disclaimer-linked-digests.txt; check-mutate-population, check-line-cap, check-pins-yaml, queue-check, the bare safety-disclaimer-linked guard and swift test over the touched suites pass on the merged head; ios-compile success and ios-screenshot success on task/T-0339, with plan-preview (the strip reads R3's destination line), plan-trip and plan-loop looked at."
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
