---
id: T-0126
title: ScenicKit Hazards: the strip that tells a driver what the route will do to them
state: review
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T18:07:49Z
lease_expires_at: 2026-09-08T20:07:49Z
worktree: .worktrees/T-0126
branch: task/T-0126
exclusive: []
touches: [Sources/ScenicKit/Hazards/, Tests/ScenicKitTests/, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The hazard strip is the one place the product tells a driver something they cannot see on the map, and it is
the safety half of the plan's risk table: *"Sedan onto dirt/gated/closed road - Med likelihood, injury and
liability blast radius."*

CLAUDE.md makes it a product invariant: **every `Route` has `hazards: [HazardFlag]`**, and P-SAFE-02 requires
the flags at three layers - ScenicKit, a golden fixture, and an XCUITest on `warning.*`. This is the first
of the three.

From the plan, the flags a V1 route can carry:

  * `surfaceUnknown(km:)` - the route spends distance on ways with no `surface` tag. Shown only past a
    threshold, because "unknown" is not "unpaved" and flagging every rural lane trains the driver to ignore
    the strip.
  * `gate` / `ford` - positive evidence of a physical obstruction on the way.
  * `closure(source:until:)` - from the 511/Caltrans feed, with its provenance, because a closure the app
    cannot attribute is one the driver cannot verify.
  * `noCell(minutes:)` - from the FCC BDC join. Minutes, not kilometres: the question a driver is actually
    asking is how long they are out of contact.
  * `twilightArrival(at:)` - arriving after civil twilight, which matters most on exactly the roads this
    product sends people down.

### What makes this more than an enum

**Ordering is the product.** A strip is read top-down and the first line is the one that gets read at all.
So the flags sort by consequence - a closure or a ford before a stretch of unknown surface - and that
ordering has to be pinned, not incidental to how the derivation happened to append them.

**Thresholds are safety decisions.** `surfaceUnknown` only appears past 2 km (the plan's number), and
`noCell` only past a duration worth naming. Both must be pinned against literals, not against the constants
they check - this repository has shipped that defect eleven times in one session and four of those were in
tests written to close a previous instance.

**A flag must never be silently dropped.** The derivation takes what the router reported and turns it into
flags; anything it cannot classify has to surface, not vanish. A hazard strip that quietly omits a ford is
worse than no strip, because the driver has learned to trust it.

Do:

1. `Sources/ScenicKit/Hazards/HazardFlag.swift` - a closed enum, one case per hazard above, `Equatable`
   and `Sendable`, with the payloads the UI needs to write a sentence.
2. `Sources/ScenicKit/Hazards/HazardStrip.swift` - derivation from a route's per-edge facts, ordering by
   consequence, and the thresholds.
3. Tests pinning: the order, each threshold at and either side of its boundary, that an unclassifiable input
   surfaces rather than disappears, and that a route with nothing wrong produces an empty strip rather than
   a reassuring flag.
4. `ops/mutate/hazards.py` in the shape of the existing five: built before a compile failure is believed, a
   catch requires a NAMED test, `trapped` reported separately, an `EQUIVALENT` list asserted the other way
   round, and `--prove-vacuity`.

**No `Package.swift` change**: `Sources/ScenicKit/Hazards/` is inside the existing target path.

**Not in scope**: the 511 feed, the FCC join, and the solar arithmetic. This is the type and the derivation;
each source is its own task, and inventing their formats here would be the fabrication this repository
exists to catch.

## Log
- 2026-09-08T18:07:49Z claimed by agent/claude-opus-5; lease until 2026-09-08T20:07:49Z
- 2026-09-08T19:05:00Z GREEN: `swift test --scratch-path .build-T0126` -> 29 tests in 4 suites passed (0.037 s). `bash ops/check-pins --source-only` -> `PINS ok=5 skipped=9 pending=0 expired=0 failed=0`. Line counts: HazardFlag 71, HazardStrip 106, HazardStripTests 152, ops/mutate/hazards.py 234 - all under the 300 cap.
- 2026-09-08T19:05:00Z `bash ops/test` FAILS, and NOT because of this task: `FAIL: services/api exists but vitest produced no report`. `services/api/node_modules` is absent in this worktree AND on main, so the Worker tier cannot run for anyone right now. That is already filed as T-0040 (claimed). The Linux Swift tier is green (29/4 above) and this task adds 13 tests to it. I did not raise floor_linux - a floor ratchet is the reviewer's, and it cannot be verified while ops/test cannot produce a total.
- 2026-09-08T19:05:00Z MUTATION HARNESS `ops/mutate/hazards.py`, 15 mutations, all caught BY A NAMED TEST: `caught by a named test: 15   trapped: 0   compile-only: 0   MISSED: 0   of 15`. Six move a NUMBER or a comparison direction (2.0 -> 0.1, 2.0 -> 50.0, `>` -> `>=` on surface, 5 -> 60, `>=` -> `>` on no-cell, `>` -> `>=` on twilight) because a reviewer found an earlier harness whose every mutation was structural, which is exactly where a suite is blind. Three permute `severityRank` (closure 0 -> 9, surfaceUnknown 6 -> 0, unrecognised 3 -> 8). The rest attack the two product claims: nothing is dropped (delete the `.unrecognised` loop; drop the dedup; report a ford as a gate; accept a sourceless closure) and a clean route stays empty (seed `out` with a reassuring flag).
- 2026-09-08T19:05:00Z EQUIVALENT MUTANT asserted the other way round: swapping the order of the independent `.ford`/`.gate` appends cannot change the output, since the stable sort restores ford(1) before gate(2). The harness reports it MISSED, which is the PASS - a catch there would mean a test had an opinion about how the code is written rather than what it does, and the way an agent satisfies such a demand is by anchoring on source text.
- 2026-09-08T19:05:00Z VACUITY PROOF: `ops/mutate/hazards.py --prove-vacuity` replaces HazardStripTests.swift with an empty suite and requires every mutation to go MISSED. Result `caught by a named test: 0 ... MISSED: 15 of 15`, `VACUITY PROOF OK`. Without this the harness could be measuring the Swift compiler.
- 2026-09-08T19:05:00Z RED (the harness itself, not just the code): deleted the ONE named test that pins the no-cell boundary, `func noCellThreshold()`, and re-ran. `HARNESS EXIT = 1`, with `MISSED: no-cell comparison strict, so exactly 5 minutes stops firing`. Honest detail worth the reviewer's attention: the sibling mutation `5 -> 60 minutes` stayed CAUGHT, because `orderedByConsequence` passes `noCellMinutes: 30` and would stop producing that flag at 60. So deleting one test cost exactly one mutation, the boundary one - which is the correct and non-flattering result, and evidence the harness measures assertions rather than files. Tests restored byte-identical (verified by comparing bytes, not by re-reading the diff).
- 2026-09-08T19:05:00Z THE DEFECT THIS REPOSITORY KEEPS SHIPPING was avoided deliberately and the reviewer should attack exactly this. The order is asserted in `orderedByConsequence` as a WRITTEN-OUT SEQUENCE of seven `flags[i] == ...` comparisons, never as `flags.map(\.severityRank).sorted()` or any expression that reads `severityRank` - deriving the expectation from the property under test would hold for any ordering the code happened to have. Both thresholds are written as literals (`== 2.0`, `== 5`) and then probed on BOTH sides of the boundary (1.9 / 2.0 / 2.1 and 4 / 5 / 6), so the constant and the comparison are each pinned independently. The three `severityRank` mutations and the two comparison-direction mutations all being caught is the mechanical evidence that this held.
- 2026-09-08T19:05:00Z ONE CONSTANT IS NOT FROM THE PLAN AND IS LABELLED SO. `surfaceUnknownMinimumKm = 2.0` is the plan's number, quoted at the declaration ("shown only if the route spends >2 km on such edges"). `noCellMinimumMinutes = 5` IS NOT: the plan specifies the FCC BDC join and the flag and leaves the threshold open. Its doc comment says so in as many words and says the 5 is chosen, so it is not mistaken later for a value handed down. Reviewer: this is the number to argue with.
- 2026-09-08T19:05:00Z `HazardFlag` is a CLOSED enum with no `String` escape hatch, and `.unrecognised(String)` is how a tag this version has no case for reaches the screen instead of vanishing. A strip that quietly omits a ford is worse than no strip, because the driver has learned to trust it. `.unrecognised` sorts at rank 3, above the three advisories, because nobody has judged it.
- 2026-09-08T19:05:00Z SCOPE HELD. No 511 feed, no FCC join, no solar arithmetic - `RouteFacts` is a plain value the caller fills, and inventing those formats here would be the fabrication this repository exists to catch. `Sources/ScenicKit/Hazards/` is inside the existing SwiftPM target path, so NO `Package.swift` edit and no `exclusive:` lock was needed. This is layer 1 of 3 for P-SAFE-02; the golden fixture and the `warning.*` XCUITest are separate tasks and the pin stays pending until they exist.
- 2026-09-08T19:05:00Z moved to review/. Reviewer must not be agent/claude-opus-5 (`ops/queue-check`).
