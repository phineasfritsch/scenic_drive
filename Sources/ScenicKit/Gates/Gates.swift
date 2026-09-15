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
/// ## What holds the invariant, in two layers
///
/// There is no `GateReason` named for a motorway, and that is worth something - but it is **not** a
/// structural guarantee, and an earlier version of this comment claimed it was. A new branch can reuse
/// `.noAccess` and never touch the enum, which is how the two reviews of PR #82 refused freeway geometry six
/// times between them with the whole suite green.
///
/// 1. **`consideredTagKeys`.** `decide` drops every tag key no rule below is written on, before any rule
///    runs. A branch keyed on `expressway`, on `foot`/`bicycle`, on `lanes` or on `maxspeed` - the four
///    shapes the second review got past the suite - is dead code the moment it is written, because the key it
///    reads is not in the dictionary the rules see. Widening this set is the visible half of that edit, and
///    `theGateSetConsidersOnlyTheTagKeysItsOwnRulesAreWrittenOn` pins it as a written-out literal.
/// 2. **The behaviour pinned in `GatesInvariantTests`.** `irrelevantTagKeysCannotChangeADecision` piles
///    sixteen keys no rule uses onto sixteen bases and requires the verdict not to move. That is what catches
///    the OTHER half of the edit - deleting the filter below and adding the branch in one go.
///
/// **What deleting the filter costs, measured rather than asserted.** On its own it changes no behaviour at
/// all: with the line gone the whole suite still passes. What objects is `ops/mutate/gates.py`, where six
/// mutations are ANCHORED on that line and report `SKIP ... anchor not found - harness is stale`, `0 of 6`,
/// exit 1. (An earlier draft of this comment said the `drop smoothness from consideredTagKeys` mutation went
/// MISSED instead. Run against a tree with the filter removed it stays caught, by the literal pin, exit 0 -
/// so that sentence was false and is gone rather than corrected further down.)
///
/// **The residual neither layer closes:** deleting the filter AND keying on a tag that neither the thirteen
/// companion sets in `GatesTests` nor the sixteen noise keys name. A refusal on `highway` itself - the one
/// considered key a freeway carries - is covered by the 52-way cross product.
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

    /// Every tag key a rule in `decide` is written on, and nothing else.
    ///
    /// This is the enforcement of "hard gates are safety only". A way is refused on the evidence of one of
    /// these ten keys or it is not refused at all, so a branch that reads any other key sees `nil` and can
    /// never fire. `foot`, `bicycle`, `expressway`, `lanes`, `maxspeed`, `toll`, `motorroad` and `oneway`
    /// are deliberately absent: `foot=no` and `bicycle=no` are on essentially every motorway in OSM, and a
    /// "be thorough about access tags" refactor that loops over them would otherwise exclude the entire
    /// freeway network.
    ///
    /// **This list fails toward `.allowed`, which is the right direction.** A genuinely new safety rule
    /// written on a key that is missing here does nothing until the key is added - the author's own test for
    /// their new rule goes red immediately and tells them. The opposite failure, a refusal that works the
    /// moment somebody types it, is the one this product cannot survive.
    public static let consideredTagKeys: Set<String> = [
        "surface", "highway", "tracktype", "smoothness", "access",
        "motor_vehicle", "barrier", "locked", "ford", "service",
    ]

    /// The verdict for a way with these OSM tags.
    ///
    /// The order the rules are tried in is the order of the reasons a person would want to hear first, and it
    /// only matters when a way trips more than one - `ops/route-autopsy` is specified to read whichever
    /// reason fires first, so the order is behaviour and `GatesOrderTests` pins every ordered pair of it.
    public static func decide(_ allTags: [String: String]) -> GateDecision {
        let tags = allTags.filter { consideredTagKeys.contains($0.key) }

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

        // Everything else is allowed - motorway and trunk included, deliberately and by omission. Omission
        // is not self-enforcing: a later edit can add a branch here as easily as it can invert one, and the
        // review of PR #82 did exactly that four more times. A branch added here can only read a key from
        // `consideredTagKeys`; the review's `expressway`, `foot`/`bicycle`, `lanes` and `maxspeed` branches
        // are all dead code in this position now, and deleting the filter to revive them is what
        // `irrelevantTagKeysCannotChangeADecision` is for.
        return .allowed
    }
}
