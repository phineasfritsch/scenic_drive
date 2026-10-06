---
id: T-0273
title: FeatureSurpriseMe - the Surprise card on the home screen, picking from the bundled fallback corpus with Surprise.pick, showing name, hook, round-trip estimate, golden-hour line and four 'not this' buttons, with Open in Apple Maps
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T04:52:41Z
lease_expires_at: 2026-10-06T18:52:41Z
worktree: .worktrees/T-0273
branch: task/T-0273
exclusive: [package-swift]
touches: [apps/ios/Packages/ScenicApp/Package.swift, Sources/PlaceStore/, Tests/PlaceStoreTests/, ops/mutate/, apps/ios/Packages/ScenicApp/Sources/FeatureSurpriseMe/, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, apps/ios/ScenicDrive/, Sources/ScenicKit/Surprise/, Tests/ScenicKitTests/, .github/workflows/ios-screenshot.yml, ops/lib/, pins/PINS.yaml]
pins_affected: [P-PROD-02, P-PROD-03, P-ATTR-01, P-SAFE-03]
reviewer: null
depends_on: [T-0270, T-0271, T-0263]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a new Apple target FeatureSurpriseMe (imports DesignSystem, ScenicKit, PlaceStore only; added to the FeatureScenicHome LIBRARY PRODUCT's targets so no pbxproj edit) opens apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite read-only through PlaceStore, maps places to SurpriseCandidate, and calls Surprise.pick with an OFFLINE reach (ruled: straight-line distance x a ruled road factor / a ruled speed, labelled 'estimate' on the card; the /isochrone reach replaces it when the client exists) - the mapping and the offline reach are Linux-tested in ScenicKit by full equality"
  - "the card shows the place name, its class, the round-trip minutes with the estimate badge, the golden-hour line from SurpriseReason when present, Open in Apple Maps (through the same safety-disclaimer gate as home - P-SAFE-03's whitelist extended, never bypassed) and four 'not this' buttons feeding SurpriseFeedback; the attribution footer stays visible; every control has an accessibility identifier"
  - "ios-compile and ios-screenshot dispatched GREEN on the branch with a '-screen surprise' shot in both themes, downloaded and described in the Log; the P-SAFE-03 / P-ATTR-01 guards updated by whitelist and seen red by a mutant (the card's Apple Maps button bypassing the gate)"
---
## Brief

M5 'Surprise card: hook, golden-hour line, round-trip + return leg, Take me there / Just drive a loop, 4 not-this'.
The engine (T-0253), the Swift reach port (T-0263) and the bundled corpus (T-0270) are merged; T-0271 shows how a new
Apple target ships through the FeatureScenicHome product without the xcodeproj lock. Places only carry name + class
today, so the hook line is ruled from class (no curation prose yet - T-0183).

## Log
- 2026-10-06T03:35:41Z filed by agent/claude-opus-5 (orchestrator) after PR #161 (T-0270) merged; starts when T-0271 releases package-swift.
- 2026-10-06T04:50:07Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0271 (#162) merged and released package-swift; copy its Entitlements-in-the-FeatureScenicHome-product shape and its frozen-block/digest updates.
- 2026-10-06T04:52:41Z claimed by agent/claude-opus-5; lease until 2026-10-06T18:52:41Z
- 2026-10-06T05:07:47Z RULINGS, before any code (author rule). agent/claude-opus-5.
  - R1 TOUCHES. PlaceStore can open the fallback read-only (`init(path:)`, the reader's gate) but has no way to
    ENUMERATE places: its API is `search(query:limit:)` (FTS prefix tokens, never empty) and segment reads. The
    acceptance says the corpus is read "through PlaceStore", so this task adds ONE reader,
    `PlaceStore.places(in: BoundingBox) -> [Place]` over `places_rtree` (columns id, min_lon, max_lon, min_lat,
    max_lat - measured with PRAGMA table_info on the committed file), place_id ascending, same Place rows as
    search. `touches:` gains Sources/PlaceStore/, Tests/PlaceStoreTests/ (its full-equality test over the committed
    fallback, Linux CI only - Windows skips PlaceStore, T-0175 R2) and ops/mutate/ (CLAUDE.md: a new numeric module
    ships its population). Nothing else outside the filed list.
  - R2 OFFLINE REACH (ScenicKit, SurpriseOfflineReach). round trip minutes =
    ceil(2 x Geo.distanceMeters(origin, place) x roadFactor / averageMetersPerMinute), roadFactor = 1.4 (canyon and
    surface-street circuity), averageMetersPerMinute = 750 (45 km/h, no traffic data), budgetMinutes = 120, origin =
    Westwood (34.0689, -118.4452) - the app holds no location (feature targets never import CoreLocation; no
    permission flow yet), so the card says "from Westwood". The card labels every number "estimate - no traffic
    data". MEASURED on the committed corpus-fallback.sqlite (sha256 05c3a19c...7e936d) with a Python port of
    Geo.distanceMeters in the same expression order: 1334 places (beach 56, cafe 50, garden 150, museum 150, park
    400, peak 187, town 104, trailhead 99, viewpoint 102, waterfall 36; 0 unnamed), 695 within 120 min, nearest 2,
    median 117; Saddle Peak 19355.600628473057 m -> 73, Zuma Beach 35647.27517192058 m -> 134, Inspiration Point
    (n/1350996499) 46127.89404259852 m -> 173. Bounds (largest double still at k, next double at k+1): k=1
    267.8571428571429 / 267.85714285714295, k=60 16071.428571428572 / 16071.428571428574, k=120
    32142.857142857145 / 32142.85714285715; 0 m -> 0. The /isochrone reach (T-0263) replaces it when the client
    exists: same SurpriseReach type, so Surprise.pick does not change.
  - R3 MAPPING (ScenicKit, SurprisePlaceClass + SurprisePlaceMapping), corpus row -> SurpriseCandidate. id =
    String(place_id); name = the row's name (nil or empty -> no candidate); coordinate = E7 / 1e7; class -> the
    ten corpus classes, an unknown class -> no candidate (never a guess). corridor = the 0.1 degree cell
    "\(latE7 / 1_000_000):\(lonE7 / 1_000_000)" (truncating division; no corridor data exists yet). brand nil
    (placeallow already refused 788 chains), quality 50 for every place (no notability signal - T-0270 open item 2),
    approachScore 0, lit false, unpaved false and privateApproach false (no positive evidence; access=private rows
    were refused upstream). Class table (category, label, dwell, hours, hook):
    viewpoint -> viewpoint, "Viewpoint", 20, open-air, "Pull over for a long view."
    peak -> viewpoint, "Peak", 45, open-air, "A high point with the basin below."
    waterfall -> trailhead, "Waterfall", 60, open-air, "A waterfall, if the season's been wet."
    beach -> beach, "Beach", 60, open-air, "Sand underfoot and a long horizon."
    trailhead -> trailhead, "Trailhead", 60, open-air, "Park the car and walk a while."
    museum -> museum, "Museum", 90, 10:00-17:00 assumed, "Something to look at, out of the sun."
    cafe -> cafe, "Cafe", 30, 07:00-18:00 assumed, "A slow cup somewhere new."
    garden -> garden, "Garden", 60, 09:00-17:00 assumed, "Planted paths and some shade."
    park -> park, "Park", 45, open-air, "Green space to stretch your legs."
    town -> town, "Town", 60, open-air, "A small main street to wander."
    Open-air = hoursExempt; the three assumed windows are conservative until opening_hours reaches the corpus.
  - R4 THE GATE, without FeatureSurpriseMe importing FeatureScenicHome. The card never sees the acknowledgement: it
    takes `onOpenInMaps: (Coordinate) -> Void`. The HOME owns the opener: `openSurprise(_:)` builds a SECOND
    GatedHandoffButton( with the same pass-through `isSafetyDisclaimerAcknowledged: isSafetyDisclaimerAcknowledged`
    and `onBlocked: { isShowingDisclaimer = true }`, and calls its `attempt()` (the failure card's retry does the
    same). GatedHandoffButton gains `var place: Coordinate? = nil` (the first construction is unchanged) and its ONE
    `SkylineHandoff.open(` call passes it; SkylineHandoff.open gains `place: Coordinate? = nil` and opens
    AppleMapsDirections(destination: place) when set. The home exposes a slot `surprise:` (a builder handed the
    gated opener and the last failure, returning AnyView); the SHELL composes it with SurpriseCard - the shell
    imports both, no feature imports another. P-SAFE-03 is EXTENDED by whitelist, never bypassed: (iv)
    GatedHandoffButton( exactly TWICE, both in ScenicHomeScreen.swift; (v) the identifier set ScenicHomeScreen.swift
    (4) -> (6) (the second pass-through's label and value); -pinned gains Sources/FeatureSurpriseMe as a second
    pinned file set with approved digests (the card cannot open a URL, add a file, or shadow a name without a
    reviewed digest); -frozen's chips list, the shell block and the body's ABOVE line move deliberately.
    --prove-red gains rows: the card's Apple Maps button opening a URL itself (THE acceptance's mutant), the shell
    handing the card its own opener, the second construction passing `true`, a file added to FeatureSurpriseMe.
  - R5 WHERE THE CARD LIVES ON HOME. Inline, inside the chip band's material, under the drive picker, toggled by a
    44 pt "sparkles" square beside the gear (`home.surprise`). NOT a sheet: check-map-attribution-sheet (h4) allows
    one presentation over the map, and a sheet over the home could not present the disclaimer sheet on a refused
    tap. chipBandBottom is still measured on the band, so the map's covered edge follows the card. The credit and
    the home sheet are untouched: the footer stays visible. `-screen surprise` opens the card at launch, read in
    FeatureScenicHome/SurpriseSlot.swift under `#if DEBUG`; LaunchScreen maps an unknown value to `.home`, so
    Settings stays closed and Entitlements (frozen) is not edited.
  - R6 CONTEXT. userId "on-device", today's civil date and minute in TimeZone.current, its UTC offset, redFlag false
    (no fire-weather feed exists - filter 7 is inert offline, recorded), seed 0; history lives for the session in
    the card (persisting it is a follow-up): each not-this button appends SurpriseFeedback (tooFar / notMyThing /
    beenThere / wrongTime with the pick's round trip and today) and the card re-picks.
  - R7 COPY. Name (title3), class label with an SF Symbol, the hook, "About N min round trip from Westwood" plus
    the badge "estimate - no traffic data", the golden-hour line when SurpriseReason has one, Open in Apple Maps
    (primary fill), "Not this:" Too far / Not my thing / Been there / Wrong time; empty state "Nothing within reach
    right now." Orange only on symbols and the button fill. Identifiers surprise.card, surprise.name, surprise.class,
    surprise.hook, surprise.roundTrip, surprise.estimate, surprise.goldenHour, surprise.failure,
    surprise.openInAppleMaps, surprise.notThis.<reason>, surprise.empty, home.surprise.
  - R8 P-ATTR-01. The card is not a map surface (no MapView(, no styleURL:); the footer, the credit band and the
    sheet are not edited. P-ATTR-01 shares -frozen and -pinned, so it moves with R4's data and nothing else.
  - R9 SCREENSHOTS. The capture loop gains `surprise` per appearance (SCREEN=surprise, NAME=surprise-$LOOK);
    ios_screenshot_pinned.py's CAPTURE_RUN moves with it.
  - R10 POPULATION. SurpriseOfflineReach and SurprisePlaceMapping are numeric. Their entries live in a new data file
    ops/mutate/surprise_offline_mutations.py, appended to surprise_mutations.MUTATIONS (surprise_mutations.py is at
    273 lines); MIN_MUTATIONS rises to the literal new total and the run's FILTER gains the two new suites.
- 2026-10-06T08:51:32Z BUILD, agent/claude-opus-5.
  - SCENICKIT RED FIRST (05:11:27Z): the two suites written before any source; `swift build --build-tests` refused
    them by name - `cannot find 'SurprisePlaceMapping' in scope`, `cannot find 'SurpriseOfflineReach' in scope`,
    `cannot find 'SurprisePlaceClass' in scope`. GREEN after the three files: `Test run with 9 tests in 2 suites
    passed` (10 class rows, 7 bound rows, 4 corridor-edge rows, 5 no-candidate rows, the reach by full equality, the
    mapped Saddle Peak as Surprise.pick's whole SurprisePick). On the merged head e9fde98, with the origin test added:
    `Test run with 10 tests in 2 suites passed` (Surprise offline reach, Surprise place mapping).
  - POPULATION (R10): `python ops/mutate/surprise.py --only 95,...,123` on 9ab6a20: `caught by the test that names
    it: 29 of 29 (wrong killer 0, trapped 0, compile-only 0, MISSED 0, skipped 0)` / `MUTATE OK caught=29/29`, rc=0,
    e.g. `101 the reach reports the ruled budget, not the one handed in by: the budget handed in is the budget handed
    out...`, `104 the reach measured from Westwood, not the origin handed in by: the reach is measured from the origin
    handed in, not from Westwood`, `109 an empty name kept by: an unnamed row, an empty name and a class outside the
    ten give no candidate`, `122 a label respelled by: the ten classes are ... with the ruled labels`. --prove-floor:
    `FLOOR PROOF OK: 7 of 7 arms refused`. P-PROC-06: `every added module is covered or allowlisted; the floor of 67
    holds`. The 94 earlier entries were not re-run (their subjects are unchanged).
  - PLACESTORE: Tests/PlaceStoreTests/PlaceStorePlacesInBoxTests.swift (six Saddle Peak box rows by full equality,
    the whole-world box = 1334 rows with the measured per-class counts, an ocean box = []) is Linux-only (Windows skips
    PlaceStore, T-0175 R2); NOT seen run on this box - CI core runs it on the PR.
  - P-SAFE-03 / P-ATTR-01 (R4): tracked tree on 95e54b7 `bash ops/lib/check-safety-disclaimer` exit 0 (35m27s): `...
    isSafetyDisclaimerAcknowledged at .../GatedHandoffButton.swift(2) .../ScenicHomeScreen.swift(6) ... LAST 18 feature
    file(s) and AttributionFooter.swift pinned`. `bash ops/lib/check-map-attribution` exit 0 (51m55s). PROVE-RED, the
    touched rows only (owner round rule; a copy of the table holding them, .build/t0273/psafe-rows): `the
    acknowledgement no longer passed to the button 1 yes`, `a second call site in the app shell 1 yes` (row 9's sed
    re-anchored: since T-0271 the shell has no `ScenicHomeScreen()` and the row changed nothing), `a second button
    beside the real one 1 yes` (now `constructed exactly twice`), `T-0273 the Surprise card opens Apple Maps itself 1
    yes` (THE acceptance's mutant: `onOpenInMaps(candidate.coordinate)` -> `openURL(...)`, refused as `SurpriseCard.swift
    content changed`), `T-0273 the shell hands the card its own opener 1 yes`. Rows 32 (the Surprise construction
    passing true) and 33 (a file beside the card) were still running at this entry - see OPEN.
  - P-STORE-01: `python ops/lib/check-store-links.py` exit 0; `--prove-red: 33/33 rows as required`.
  - LINE CAP: check-line-cap REFUSED ScenicHomeScreen.swift at 318 lines; 1f3b5c1 moves the toggle to
    FeatureScenicHome/SurpriseToggle.swift (297 lines) and re-approves its digest and the new file in -pinned. wc -l:
    SurpriseCard 177, SurpriseDeck 57, SurpriseNotThis 55, SurpriseSlot 24, SurpriseToggle 34, GatedHandoffButton 117,
    SkylineHandoff 97, SurpriseOfflineReach 37, SurprisePlaceMapping 39, check-safety-disclaimer 300,
    check-safety-disclaimer-pinned 141, surprise_mutations.py 278, surprise_offline_mutations.py 83.
  - iOS: ios-compile 37420304691 on 95e54b7 success (FeatureSurpriseMe and GRDB compiled into the app);
    ios-screenshot 37421111076 on 95e54b7 success, 12 PNGs. LOOKED AT: surprise-light - the chip band holds Saddle Peak /
    Westwood loop / SF Peninsula, an orange sparkles square (filled while open) and the gear; under it, inside the
    same material, a white card: orange tree symbol + "Park", "Calas Park" (title), "Green space to stretch your
    legs.", orange clock + "About 120 min round trip from Westwood" with the outlined badge "estimate · no traffic
    data", the orange "Open in Apple Maps" bar, "Not this one?" and four 44 pt outlined buttons Too far / Not my thing /
    Been there / Wrong time. No golden-hour line (the CI clock is ~06:00 UTC; sunset was outside the visit). The map,
    the credit pill "(c) MapLibre · Natural Earth · (c) OpenStreetMap contributors" and the collapsed home sheet
    (title, three menu chips, "Conditions change. Verify locally.", Open in Apple Maps) are all visible below the card.
    surprise-dark - the same on the navy surface, orange lighter, text light. home-light-collapsed - the card closed:
    the outline sparkles square beside the gear, the map as before. ios-compile 37432844878 on the merged head e9fde98
    (SurpriseToggle split) success; no screenshot re-run for that move (the toggle's code is the same view).
  - OBSERVED, recorded for a follow-up, not changed: with every quality equal, Surprise.pick's minutes/budget term
    makes the pick the place nearest the 120-minute ceiling (Calas Park at exactly 120) - the far edge of reach, not a
    calm nearby surprise. The selector (T-0253) is unchanged here; a tie-break or budget ruling is its own task.
  - OPEN: P-SAFE-03 prove-red rows 32-33 and the final P-SAFE-03 / P-ATTR-01 runs on the merged head e9fde98 were still
    running on this loaded box when this entry was written; the PlaceStore test is seen on CI only; the 8-row-tall card
    at AX Dynamic Type sizes is not screenshotted and may push the map off screen; P-PROD-03 (pins_affected) does not
    exist in pins/PINS.yaml; the -pinned echo's file count now sums both modules (18 = 16 + 3 - shown under one label).
