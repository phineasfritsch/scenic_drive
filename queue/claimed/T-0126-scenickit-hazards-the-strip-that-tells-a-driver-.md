---
id: T-0126
title: ScenicKit Hazards: the strip that tells a driver what the route will do to them
state: claimed
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
