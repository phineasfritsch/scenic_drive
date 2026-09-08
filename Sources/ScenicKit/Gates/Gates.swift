import Foundation

/// The only place this product refuses a road outright.
///
/// ## The invariant
///
/// **A motorway is never gated.** CLAUDE.md lists it first among the product invariants not to
/// "optimize away":
///
/// > Motorway/trunk ways carry `scenic_score = 0`; they are penalized, **not** hard-excluded (freeway
/// > shoulders, scenic middle). Hard gates are safety only: unpaved (positive evidence), private/no access,
/// > track.
///
/// It has already failed once here: a whole-route freeway exclusion made the flagship Mountain View -> SF
/// fixture unroutable, and the plan records the fix. It is the easiest rule in this file to break by
/// improving it, because refusing motorways *looks* like what a scenic router should do, and every short
/// fixture still passes when it does. Every Bay Area commute over 15 km needs freeway shoulders around a
/// scenic middle - 280, then Cañada, then Skyline.
///
/// So there is no `GateReason` for a motorway, and `decide` has no branch that could grow one.
///
/// ## Positive evidence only
///
/// Every rule fires on a tag that is **present and says something**. None fires on a tag being absent. That
/// is not a convenience: most rural lanes carry no `surface` tag at all, and a gate on the absent case would
/// refuse the roads this product exists to find. The plan handles unsurveyed roads with a score multiplier
/// and a `surfaceUnknown` hazard flag - a note to the driver, not a refusal.
///
/// ## Not parity, yet
///
/// The plan's P-PROD-01 wants one fixture set driven through three implementations - this one,
/// `services/routing/profiles/*.json`, and the ETL - and asserts they agree. **Neither of the other two
/// exists in this repository yet.** This is the reference implementation, and it is not evidence that
/// anything else agrees with it.
public enum Gates {
    /// `surface` values that are positive evidence of an unpaved road. The plan's list, verbatim.
    public static let unpavedSurfaces: Set<String> = [
        "gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel",
    ]

    /// `access` values that forbid the public.
    ///
    /// `destination` is included on purpose: a way signed for destination traffic only is not a road to send
    /// somebody down for the view.
    public static let closedAccess: Set<String> = ["private", "no", "permit", "destination"]

    /// `tracktype` values at grade3 or worse. Written out rather than compared as strings, because "grade3"
    /// sorting below "grade2" is a property of the string encoding and not of the road.
    public static let refusedTracktypes: Set<String> = ["grade3", "grade4", "grade5"]

    /// `smoothness` values worse than intermediate, in OSM's own ordering.
    public static let refusedSmoothness: Set<String> = [
        "bad", "very_bad", "horrible", "very_horrible", "impassable",
    ]

    /// `service` values that are not roads anyone drives for pleasure.
    public static let refusedServiceValues: Set<String> = [
        "driveway", "parking_aisle", "drive-through", "emergency_access",
    ]

    /// The verdict for a way with these OSM tags.
    ///
    /// The order the rules are tried in is the order of the reasons a person would want to hear first, and it
    /// only matters when a way trips more than one.
    public static func decide(_ tags: [String: String]) -> GateDecision {
        if let surface = tags["surface"], unpavedSurfaces.contains(surface) {
            return .refused(.unpavedSurface)
        }
        if tags["highway"] == "track" { return .refused(.track) }
        if let t = tags["tracktype"], refusedTracktypes.contains(t) { return .refused(.track) }
        if let s = tags["smoothness"], refusedSmoothness.contains(s) { return .refused(.tooRough) }

        if let access = tags["access"], closedAccess.contains(access) { return .refused(.noAccess) }
        if tags["motor_vehicle"] == "no" { return .refused(.noAccess) }

        // A gate is only a refusal when it is recorded as LOCKED. An unlocked gate may be openable, and the
        // driver is the one who can see it - the hazard strip tells them it is there.
        if tags["barrier"] == "gate", tags["locked"] == "yes" { return .refused(.lockedBarrier) }

        if tags["ford"] == "yes" { return .refused(.ford) }

        if tags["highway"] == "service", let s = tags["service"], refusedServiceValues.contains(s) {
            return .refused(.serviceWay)
        }

        // Everything else is allowed - motorway and trunk included, deliberately and by omission rather than
        // by a branch, because a branch is something a later edit can invert.
        return .allowed
    }
}
