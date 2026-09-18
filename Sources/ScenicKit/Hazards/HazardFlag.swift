import Foundation

/// One thing the route will do to the driver that they cannot see on the map.
///
/// The hazard strip is the safety half of this product. The PLAN's invariant table makes it an invariant -
/// *every `Route` has `hazards: [HazardFlag]`* - and the plan's risk table rates the failure it guards
/// against as *"sedan onto dirt/gated/closed road: medium likelihood, injury and liability blast radius."*
/// (The invariant is the plan's, not CLAUDE.md's; the PR #80 review was right that this said CLAUDE.md.
/// P-SAFE-02 is a plan row and is not yet transcribed into `pins/PINS.yaml`, so nothing mechanical reads it.)
///
/// A CLOSED enum on purpose. An open set, or a `String` reason, would let a future source of hazards reach
/// the UI without anyone deciding what the sentence says or where it sorts - and the strip is read
/// top-down, so a flag nobody placed is a flag nobody reads.
public enum HazardFlag: Equatable, Sendable {
    /// The route crosses an active closure. Carries its source because a closure the app cannot attribute
    /// is one the driver cannot verify, and "closed" with no provenance is the kind of warning people learn
    /// to click past.
    ///
    /// **`source` may be empty, and that is never a reason to suppress the flag.** The plan's closure blob
    /// is merged from two feeds (511 SF Bay and Caltrans LCS D4); a polygon that arrives without one named
    /// is a defect in the blob, not evidence that the road is open. The strip surfaces it anyway, at rank 0,
    /// and the caller decides what an unattributed closure reads like on screen. This is the one place a
    /// `String` payload is allowed to be blank, precisely because it is metadata about the hazard rather
    /// than the hazard itself.
    case closure(source: String, until: Date?)

    /// Positive evidence of a ford on the way. Not "might be wet" - the way is tagged `ford=yes`.
    case ford

    /// A gate on the way. It may be unlocked; it may not be. The driver decides, which is the point.
    case gate

    /// The route is out of mobile coverage for this long.
    ///
    /// MINUTES, not kilometres. The question a driver is actually asking is how long they are out of
    /// contact, and 8 km means nothing without knowing how fast that stretch is driven.
    case noCell(minutes: Int)

    /// Arrival falls after civil twilight.
    ///
    /// Load-bearing on exactly the roads this product sends people down: an unlit canyon road at dusk is a
    /// different drive from the same road at noon, and the route was chosen for being scenic rather than
    /// well-lit.
    case twilightArrival(at: Date)

    /// The route spends this far on ways with no `surface` tag.
    ///
    /// **Unknown is not unpaved.** The ETL gates on positive evidence only, so a way with no surface tag is
    /// not excluded - and most rural lanes have no surface tag. Flagging every one of them would train the
    /// driver to ignore the strip, which is why this appears only past `HazardStrip.surfaceUnknownMinimumKm`.
    case surfaceUnknown(km: Double)

    /// A fact the router reported that this version does not know how to classify.
    ///
    /// **The alternative to this case is silently dropping it**, and a hazard strip that quietly omits a
    /// ford is worse than no strip at all, because the driver has learned to trust it. Anything unrecognised
    /// surfaces as itself and sorts high, so a new tag from a future ETL reaches the screen as "something is
    /// here we do not understand" rather than as nothing.
    case unrecognised(String)
}

extension HazardFlag {
    /// Where this sits in the strip. Lower sorts first.
    ///
    /// **The ordering is the product.** A strip is read top-down and the first line is the one that gets
    /// read at all, so the flags sort by consequence rather than by the order the derivation happened to
    /// append them. A closure - the route does not go through - outranks a stretch of unknown surface,
    /// which is advisory.
    var severityRank: Int {
        switch self {
        case .closure:          return 0
        case .ford:             return 1
        case .gate:             return 2
        case .unrecognised:     return 3
        case .noCell:           return 4
        case .twilightArrival:  return 5
        case .surfaceUnknown:   return 6
        }
    }
}
