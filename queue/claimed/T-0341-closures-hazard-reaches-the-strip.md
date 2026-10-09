---
id: T-0341
title: closures_hazard reaches the app - a stale or unavailable closures snapshot, a dropped closure or a crossed closure on a plan, trip or loop answer is told to the driver in calm copy, not silently decoded away
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T11:49:42Z
lease_expires_at: 2026-10-09T21:49:42Z
worktree: .worktrees/T-0341
branch: task/T-0341
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-hazard-copy-sites.txt, ops/lib/check-hazard-copy-sites.py, ops/lib/named-tests.json, ops/lib/mutate-population-allowlist.json, ops/mutate/, queue/]
pins_affected: [P-SAFE-02, P-SAFE-03, P-SAFE-08]
reviewer: null
depends_on: [T-0339]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 CLOSURE COPY, WHOLE (full equality): HazardCopy.closureLines(for:) over the whole cross product state {fresh, stale, unavailable} x dropped {no, yes} x crosses {no, yes} (12 rows) EQUALS a list written out in HazardCopyTests independently of HazardCopy, each row a function of its variant: crosses line first, then the state line (none for fresh), then the dropped line, each line R2's sentence whole; fresh/no/no is the empty list."
  - "A2 EVERY WORKER SHAPE, EVERY ROUTE CARD, THROUGH THE SHIPPING ENTRY POINTS: over M1's 9 shapes (absent, fresh+dropped, fresh+crosses, fresh+both, stale, stale+dropped, stale+crosses, stale+both, unavailable) x {plan, trip, loop}, a 200 whose closures_hazard is that shape, sent through PlanClient.plan -> ClientPlanner.preview, TripClient.trip -> ClientTripPlanner.itinerary and LoopClient.loop -> ClientLoopPlanner.outcome, reads HazardCopy.lines(for:) EQUAL to the shape's expected list (a function of the shape); the plan's list is the closure lines then the run lines."
  - "A3 FAIL-CLOSED ON EVERY FIELD (rows as functions of input): over plan/trip/loop x {closures_hazard null, number, string, array; state removed, null, number, unknown spellings 'Fresh', 'STALE', ' stale', 'expired', ''; version removed, null, number; fetched_at removed, number, bool; dropped present as 0, -1, null, string; crosses present as [], null, string, [1]} the answer still decodes to a route (never a refusal) and reads R3's lines for that variant, whole - never the empty list; a meta-check asserts no variant's expected list is empty."
  - "A4 RED FIRST BY NAME: A1-A3's named tests land against a stub (closure readers that drop closures_hazard, closureLines returning []), the run is quoted with each named test failing; then the code lands and they are green."
  - "A5 EVERY ROUTE CARD SHOWS IT, ONLY THROUGH HAZARDCOPY: PlanPreviewCard (unchanged; its strip is HazardCopy.lines(for: preview)), TripItineraryCard and LoopPreviewCard render HazardCopy.lines(for:) of their model; check-hazard-copy-sites.py's IDENTIFIERS name the closures model (closures, ClosuresHazard, ClosuresState, ClosuresHazardReader) so a card line that reads it outside HazardCopy is refused by name, its --prove-red carries such rows, and check-hazard-copy-sites.txt approves exactly the new sites; the bare check-hazard-copy-sites guard and check-safety-disclaimer pass with the two card digests re-approved; shown RED once with a bypass."
  - "A6 SHOTS LOOKED AT: PlanRehearsalFixtures puts crosses on the plan preview, stale on the itinerary and unavailable on the loop; ios-compile and ios-screenshot green on the last commit touching apps/ios or Sources, and plan-preview, plan-trip and plan-loop shots are looked at and quoted."
  - "A7 POPULATION AND PINS: ops/mutate/hazardcopy_mutations.py gains closure mutants (each line softened, order changed, a condition dropped, the reader's fail-closed arms flipped) killed by the named test; floors raised to the shipped count; P-SAFE-08's named tests gain the A2/A3 Swift tests by name (run-named-tests.py P-SAFE-08 green)."
  - "A8 GATES: linked digests re-approved for every touched Sources file; touched suites green; bare guards check-safety-disclaimer and check-hazard-copy-sites; check-mutate-population, check-line-cap, check-pins-yaml, queue-check; origin/main fetched and merged last."
---
## Brief

T-0339 M2 (measured at bdb77ca6): the Worker adds `closures_hazard` {state: fresh|stale|unavailable, version,
fetched_at, dropped?, crosses?} to plan / trip / loop / isochrone 200s (services/api/src/closuresStore.ts:93) and no
Swift file reads it (grep closures_hazard over Sources and apps/ios: 0 hits). A plan built on a stale closures set, or
one that crosses a closure, looks identical to a fresh one on screen. MEASURE FIRST (every state and field the Worker
can send, every card that shows a route), RULE the copy into T-0339's HazardCopy table, then the acceptance: readers
fail-closed, one line per condition, whole-copy equality, shots looked at.

## Log
- 2026-10-09T08:33:30Z filed by agent/claude-opus-5 from T-0339 R4.
- 2026-10-09T11:49:42Z claimed by agent/claude-opus-5; lease until 2026-10-09T21:49:42Z
- 2026-10-09T11:54:27Z MEASURED (at e3567a6e, before any code).
  - M1 WHAT THE WORKER SENDS. services/api/src/closuresStore.ts: `ClosuresHazard {state: "fresh"|"stale"|
    "unavailable"; version: string; fetched_at: string|null; dropped?: number; crosses?: string[]}`.
    withClosuresHazard (:93-97): with dropped 0 and no crosses the key is ABSENT on a fresh snapshot and the
    snapshot's hazard otherwise (stale: {state, version, fetched_at: ISO string}; unavailable: {state, version
    "none", fetched_at null}); dropped > 0 adds `dropped` (a count), a non-empty crosses adds `crosses` (ids), and a
    fresh snapshot then carries state "fresh". Callers: plan.ts:129, trip.ts:108, loop.ts:86 (all three with
    picker.dropped() and picker.crosses()), isochrone.ts:80/86 (snapshot only). So the shapes are: absent;
    fresh+dropped; fresh+crosses; fresh+both; stale; stale+dropped; stale+crosses; stale+both; unavailable (an
    unavailable read has no set, so the picker has nothing to drop or cross).
  - M2 NO SWIFT READER. grep closures_hazard over Sources and apps/ios: 0 hits. PlanResponse, TripResponse and
    LoopResponse ignore the key. Two test bodies carry it: Tests/ScenicAPIClientTests/TripWire.swift:24 and
    LoopWire.swift:25, both `{"state":"fresh"}` - a shape the Worker never sends (no version, no fetched_at).
  - M3 ROUTE CARDS: PlanPreviewCard (strip = HazardCopy.lines(for: preview)), TripItineraryCard and LoopPreviewCard
    (no hazard line at all; T-0339 R4). Models: PlanPreview, TripItinerary, LoopPreview (Sources/ScenicKit), built by
    ClientPlanner.preview, ClientTripPlanner.itinerary, ClientLoopPlanner.outcome. All three cards are content
    pinned in ops/lib/check-safety-disclaimer-pinned (:244 loop, :251 plan, :259 trip); app sites naming HazardCopy
    are whitelisted in ops/lib/check-hazard-copy-sites.txt (3 PlanPreviewCard rows).
  - M4 OUT OF CARD SCOPE: /reroute (reroutePlanner.ts) sends no closures_hazard and PlanRerouter's reply is the drive
    screen, not a route card; the isochrone body (SurpriseIsochrone) draws reach, not a route. Neither is read here.
  - M5 PINS: P-SAFE-02 has no row in pins/PINS.yaml (grep: 0). P-SAFE-08 ("closure cron freshness <= 30 min; route
    never crosses an active closure polygon") runs ops/lib/run-named-tests.py P-SAFE-08, vitest only today.
- 2026-10-09T11:54:27Z RULINGS.
  - R1 MODEL (ScenicKit, Linux): `ClosuresState` {fresh, stale, unavailable} and `ClosuresHazard {state, dropped:
    Bool, crosses: Bool}` with `.clear` (fresh, no, no), each its own file under Sources/ScenicKit/Hazards/.
    PlanPreview, TripItinerary and LoopPreview gain `closures` (default .clear); PlanResponse, TripResponse and
    LoopResponse gain `closuresHazard`, read by one non-throwing reader `ClosuresHazardReader` (ScenicAPIClient).
  - R2 THE COPY, ruled into HazardCopy (calm, the meaning never softened):
    crosses "This route crosses a reported road closure - expect the road to be blocked and check before you drive";
    stale "Road closure reports may be out of date for this route - check for closures before you drive";
    unavailable "Road closures could not be checked for this route - check for closures before you drive";
    dropped "Not every reported road closure near this route was checked - check for closures before you drive".
    One line per condition, in that order (crosses, state, dropped); fresh adds no state line. The plan strip reads
    the closure lines and then the run lines; when any closure line shows, noneFlagged does not (the strip is not
    empty). Trip and loop cards show the closure lines in their first section, nothing when the list is empty.
  - R3 FAIL-CLOSED READER (the safest TRUE line, never silence, never a refusal to route - closuresStore.ts:8):
    key absent -> .clear (the Worker's fresh contract, M1). Present but null or not an object -> unavailable. state
    missing, not a string, or not exactly fresh|stale|unavailable -> unavailable. version not a string, or fetched_at
    missing or neither a string nor null -> unavailable (the record did not read). `dropped` PRESENT with any value
    -> dropped line; `crosses` PRESENT with any value -> crosses line (the Worker adds each key only to say so; a
    garbled value cannot un-say it). A whole object that does not read claims no crossing: "could not be checked" is
    the true line. Nothing in closures_hazard can fail the decode of the route.
  - R4 FIXTURES: TripWire/LoopWire's `{"state":"fresh"}` is not a Worker shape (M2) and under R3 reads unavailable;
    they become M1 shapes (trip: stale, loop: fresh+dropped) with expected values to match.
  - R5 PINS: no P-SAFE-02 row exists (M5), so nothing binds to it. P-SAFE-08 gains a swift section naming A2 and A3's
    tests: the driver being told a route crosses a closure, or that closures were not current, is the app half of
    "never crosses an active closure". P-SAFE-03 holds the cards (digests + check-hazard-copy-sites).
  - R6 POPULATION: the existing hazardcopy driver family takes the new mutants (subjects HazardCopy.swift and
    ClosuresHazardReader.swift; killers in HazardCopyTests and ClosuresHazardTests); no new driver.
  - R7 SCOPE: touches widened to the pinned digest table, the hazard-sites whitelist, named-tests.json, ops/mutate/
    and queue/ (each needed by A5-A8). /reroute and the isochrone are M4 - not read, not filed (not route cards).
- 2026-10-09T13:29:28Z RULINGS AMENDED (before review; the dated entries above are left as written).
  - R3a fetched_at must be a STRING; null reads unavailable too. The Worker sends null only with state unavailable
    (M1), so every Worker shape reads the same; a stale or fresh body with a null fetched_at now reads unavailable
    (fail-closed) instead of its state. A3 gains the row `fetched_at null` (28 variants per base).
  - R4a the two test bodies' `{"state":"fresh"}` were REMOVED rather than replaced (the key absent IS the Worker's
    fresh shape); the Worker shapes are carried by ClosuresHazardTests instead.
  - R7a touches gains ops/lib/mutate-population-allowlist.json: ClosuresHazard.swift and ClosuresState.swift are
    data types with no code (P-PROC-06 named both as added and unpopulated).
- 2026-10-09T13:29:28Z ACCEPTANCE RUN (origin/main fetched and merged: "Already up to date" at e3567a6e; head
  36030ee9 plus this Log commit, which touches no measured file).
  - A4 RED (b727007d, the stub: the reader returning .clear, closureLines and the trip/loop lines returning []):
    `swift test --filter "HazardCopyTests|ClosuresHazardTests"` "Test run with 8 tests in 2 suites failed ... with
    392 issues"; by name: "every closure condition reads its ruled lines, whole, on every route card" 44, "every
    Worker closures_hazard reads its ruled lines on the plan, trip and loop cards" 24 (the 8 shapes x 3 cards; the
    absent rows passed, as they must), "an unreadable closures_hazard reads the safest line on every card, never
    silence and never a refusal" 324 (3 x 4 x 27, every variant). T-0339's five tests passed throughout.
  - A1-A3 GREEN (192e5eae on; 165b0a94 for A3's 28th row): "Test run with 8 tests in 2 suites passed". Touched
    suites on the final head: `--filter "ScenicAPIClientTests|ScenicKitTests"` "Test run with 546 tests in 100
    suites passed", exit 0.
  - A5 the cards: TripItineraryCard and LoopPreviewCard render `HazardCopy.lines(for:)` of their model;
    PlanPreviewCard unchanged. Seen RED before approval: bare check-safety-disclaimer exit=1 "P-SAFE-03: the pinned
    render surface changed: ...LoopPreviewCard.swift content changed (sha256 911b88f5..., approved 1d73fc36...)",
    PlanRehearsalFixtures 88756130 -> cd5068c7, TripItineraryCard 466e7b20 -> b6021519; check-hazard-copy-sites
    "FAILED - 3 unapproved, 1 missing of 5 approved". Approved (diffs read: the 5-line ForEach per card and the
    three fixture closures): GREEN "P-SAFE-03 hazard copy: ok - 7 sites, every one approved, in 5 files" and bare
    check-safety-disclaimer exit=0. Line counts: HazardCopy.swift 142, ClosuresHazardReader.swift 38,
    ClosuresHazard.swift 17, ClosuresState.swift 10, ClosuresHazardTests.swift 163, HazardCopyTests.swift 212,
    TripItineraryCard.swift 78, LoopPreviewCard.swift 65.
  - A6 ios-compile 37929393692 success and ios-screenshot 37929398054 success on 192e5eae (the last apps/ios
    commit); re-run on 36030ee9 (after the reader change) ios-compile 37934422227 success, ios-screenshot
    37934430486 success. LOOKED AT (37929398054): plan-preview-light - two warning lines, "This route crosses a
    reported road closure - expect the road to be blocked and check before you drive" then "Local traffic only on
    part of this route - you may not be allowed through"; plan-trip-light - "Road closure reports may be out of
    date for this route - check for closures before you drive" under the estimate badge; plan-loop-dark - "Road
    closures could not be checked for this route - check for closures before you drive" under the retrace line.
    No raw key on any shot.
  - A7 `python ops/mutate/hazardcopy.py --only 24..44` "caught by the test that names it: 21 of 21 (wrong killer
    0, trapped 0, compile-only 0, MISSED 0, skipped 0)", "MUTATE OK caught=21/21"; `--prove-floor` "FLOOR PROOF
    OK: 7 of 7 arms refused and the control did not" (floor 44, test files 2). Entries 1-23 and E1 are T-0339's,
    unchanged, and were caught there; the full 45-entry run and --prove-vacuity were NOT re-run here (about 2 min
    a mutant). `run-named-tests.py P-SAFE-08` "NAMED P-SAFE-08 passed=836/836" (833 vitest + the 3 Swift names).
  - A8 check-mutate-population "every added module is covered or allowlisted; the floor of 147 holds" (refused
    first: ClosuresHazard.swift and ClosuresState.swift added and unpopulated - allowlisted, R7a); check-line-cap
    "536 Swift files tracked ... none over 300 lines"; check-pins-yaml "PINS-YAML ok pins=49 fields=395";
    queue-check "QUEUE OK (332 tasks)"; linked digests re-approved for the 13 touched Sources files (3 added).
- 2026-10-09T13:57:42Z PRE-REVIEW FINDING (3b)/(3c) and the A5 gap, closed by CLASS. RULING: the finding is right.
  A5 said "only through HazardCopy", but check-hazard-copy-sites.py IDENTIFIERS stopped at T-0339's model (hazards,
  PlanHazardRun, HazardCopy, HazardStrip, HazardFlag, Mirror). A card line that reads `.closures` spells none of
  those, so nothing guarded T-0341's model. The class is "the closures model reached by name outside HazardCopy".
  The fix widens the whitelist to that model and does not add a spelling blacklist: IDENTIFIERS gains `closures`,
  `ClosuresHazard`, `ClosuresState` and `ClosuresHazardReader` (the last has no apps/ site; it is the reader type,
  named so an apps/ import of it would be refused too). R9 touches gains ops/lib/check-hazard-copy-sites.py.
  A5's text now names the widened identifiers (the acceptance line was edited, no dated record was changed).
  - MISSED (four new RED_ROWS added, IDENTIFIERS not yet widened): `--prove-red` "GREEN a card reads closures
    beside the site ... sites=NOT NAMED exit=0", "GREEN the raw closures state reaches a Text ... NOT NAMED
    exit=0", "GREEN a helper takes the closures model ... NOT NAMED exit=0", "GREEN a helper spells the closures
    state ... NOT NAMED exit=0"; "PROVE-RED FAILED: 9 of 13 rows red by name, control 0". The first two rows are
    (3b) and (3c) verbatim, inserted right before TripItineraryCard's approved ForEach line.
  - Widened: the bare guard refused five existing sites by name, "FAILED - 5 unapproved, 0 missing of 7
    approved". Those were the `.accessibilityIdentifier("loop.closures")` / `("trip.closures")` literals on the
    Label inside each card's HazardCopy ForEach (both read), plus PlanRehearsalFixtures' three
    `closures: ClosuresHazard(...)` rows. All five are approved in check-hazard-copy-sites.txt.
  - CAUGHT (2026-10-09T13:58:12Z): bare "P-SAFE-03 hazard copy: ok - 12 sites, every one approved, in 5 files"
    exit 0; `--prove-red` "PROVE-RED OK: 13 of 13 rows red by name, control 0", every closures row "red ... sites=
    CAUGHT by name exit=1". I applied (3b) and (3c) as real edits to the worktree card and ran the bare guard:
    (3b) "REFUSED site not on the whitelist: ...TripItineraryCard.swift: Text(itinerary.closures.crosses ? "Road
    closed ahead" : "")", "FAILED - 1 unapproved, 0 missing of 12 approved" exit=1. (3c) "REFUSED ... Text("closures:
    \(itinerary.closures.state)")", same FAILED line, exit=1. Both edits were reverted with git checkout.
  - STILL BLIND (documented in the guard's docstring): String(describing:) or interpolation over a whole
    TripItinerary/LoopPreview reaches the closures model without spelling an identifier. P-SAFE-03's card digest
    is the backstop for that.
