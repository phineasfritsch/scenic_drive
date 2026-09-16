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
/// ## What holds the invariant
///
/// There is no `GateReason` named for a motorway, and that is worth something - but it is **not** a
/// structural guarantee, and an early version of this comment claimed it was. A new branch can reuse
/// `.noAccess` and never touch the enum, which is how five reviews of PR #82 refused freeway geometry
/// eleven times between them with the whole suite green.
///
/// 1. **`ConsideredTags`.** `verdict` below - where every rule lives - is handed a `ConsideredTags`, not a
///    dictionary. That type answers `nil` for every key outside `consideredTagKeys`, at each read rather
///    than once up front, and keeps the raw tags behind a `private` property no rule can name. So a branch
///    keyed on `expressway`, on `foot`/`bicycle`, on `lanes`, on `maxspeed`, on `destination` or on `horse`
///    is dead code wherever it is typed in `verdict`, and a loop over a list of such keys is dead too.
/// 2. **`consideredTagKeys`.** The literal that type consults. Widening it is the one edit that revives
///    such a branch, and `theGateSetConsidersOnlyTheTagKeysItsOwnRulesAreWrittenOn` pins it as a
///    written-out literal, by name.
/// 3. **The behaviour pinned in `GatesInvariantTests`.** `irrelevantTagKeysCannotChangeADecision` piles
///    twenty-one keys no rule uses onto sixteen bases and requires the verdict not to move. That is what
///    covers the residual below, where a type cannot reach.
///
/// **What this shape replaced, and why.** `decide` used to take `allTags` and narrow it on its first line
/// into a local called `tags`. The fourth review of PR #82 showed that this was a naming convention rather
/// than a gate: `allTags` stayed in scope for the whole body, so `allTags["destination"]` - one identifier
/// longer than the inert form - refused every signed freeway ramp in OSM while the suite stayed green.
/// Measured, not remembered: with that branch on disk at 4b79342, `swift test` printed
/// `Test run with 37 tests in 6 suites passed`, exit 0, no named test objecting. This sentence used to end
/// "and `ops/mutate/gates.py` printing `37 of 37`, exit 0" - **struck in round 7**, because with a mutant on
/// disk the shipped harness prints `REFUSING: the subject is not what HEAD says it is` and exits 2 before it
/// builds anything, so that run cannot have happened. Four more survivors of that shape are in the corpus
/// now. Moving the narrowing into the accessor is what makes them `nil` instead of load-bearing.
///
/// ## The two residuals, stated rather than denied
///
/// 1. **A considered key with a freeway-relevant value.** `motor_vehicle`, `access`, `surface`, `smoothness`
///    and `highway` are all read by rules and all carried by real freeways, so a branch on one of them is
///    unaffected by everything above - `if let mv = tags["motor_vehicle"], mv != "yes"` refuses the
///    `motor_vehicle=designated` on motorroad geometry. No type closes this; only behaviour does, and
///    `freewayValuesOfConsideredKeysAreAllowed` is the pin.
/// 2. **A branch inside `decide` itself**, which still has the raw dictionary in scope because Swift gives
///    a function no way to drop its own parameter. Its body is one expression and holds no rule, but that
///    is a convention again, so it is pinned by behaviour rather than asserted: eleven corpus mutations put
///    a refusal exactly there, and `irrelevantTagKeysCannotChangeADecision` is what kills them. That test is
///    an enumeration of twenty-one keys - it covers the keys it names and no others, which is the honest
///    limit of this layer. Two of those keys, `sidewalk` and `int_ref`, are there because the sixth review
///    got a refusal past the list on each of them; a twenty-second key would do it again.
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
    /// somebody down for the view. Note that this is the *value* of `access`, and has nothing to do with the
    /// `destination` **key**, which carries the text on a freeway sign and is not read by any rule here.
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

    /// Every tag key a rule in `verdict` is written on, and nothing else.
    ///
    /// This is the enforcement of "hard gates are safety only", and `ConsideredTags` is what enforces it: a
    /// way is refused on the evidence of one of these ten keys or it is not refused at all, because a read
    /// of any other key answers `nil`. `foot`, `bicycle`, `expressway`, `lanes`, `maxspeed`, `toll`,
    /// `motorroad`, `oneway`, `destination`, `horse`, `moped`, `sidewalk` and `int_ref` are deliberately
    /// absent: `foot=no`, `bicycle=no`, `horse=no` and `sidewalk=no` are on essentially every motorway in
    /// OSM, `destination=<place>` and `int_ref=<number>` are on essentially every signed ramp, and a "be
    /// thorough about access tags" refactor that looped over them would exclude the entire freeway network.
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
    /// This is the whole public surface, and it holds **no rule**. Its one job is to put the tags behind
    /// `ConsideredTags` before anything can read them, so that `verdict` below cannot see a key no rule is
    /// written on. `tags` here is still the raw dictionary - see residual 2 in the type comment - so a
    /// refusal typed *in this function* would work; eleven mutations in `ops/mutate/gates_corpus.py` sit in
    /// exactly this position to keep that measured.
    public static func decide(_ tags: [String: String]) -> GateDecision {
        return verdict(ConsideredTags(tags))
    }

    /// Every gate rule, over tags that have already been narrowed to `consideredTagKeys`.
    ///
    /// The order the rules are tried in is the order of the reasons a person would want to hear first, and it
    /// only matters when a way trips more than one - `ops/route-autopsy` is specified to read whichever
    /// reason fires first, so the order is behaviour and `GatesOrderTests` pins every ordered pair of it.
    ///
    /// `tags` is a `ConsideredTags`, not a `[String: String]`, and that is load-bearing rather than tidy:
    /// no rule below can NAME the raw dictionary, so a rule keyed on a key outside the set is dead code
    /// however it is spelled - by an extra identifier, by a loop, or by deleting a line. That is an
    /// enumeration of the routes a rule takes, **not a proof**: `Mirror(reflecting:)` still reaches the
    /// stored property, measured in round 7, and behaviour rather than this type is what kills that one.
    /// `ConsideredTags` says so where the claim is made.
    private static func verdict(_ tags: ConsideredTags) -> GateDecision {
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
        // reviews of PR #82 did exactly that eleven times. What is different now is that a branch added
        // HERE can only read a key from `consideredTagKeys` by any ordinary spelling, because the raw tags
        // are not in this scope under any name; `expressway`, `foot`/`bicycle`, `lanes`, `maxspeed`,
        // `destination` and `horse` all answer `nil`. Reflection is the exception, and it is measured
        // rather than called impossible. The branches that still bite are the two residuals above.
        return .allowed
    }
}
