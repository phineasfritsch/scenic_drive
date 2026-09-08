import Foundation

/// A GraphHopper turn-instruction `sign`, exactly as GraphHopper defines it.
///
/// **These integers are not ours.** They are the constants declared in GraphHopper's own
/// `Instruction.java`, and the provenance is recorded in `GuidanceSign.source*` below rather than in a comment,
/// because comments get stripped and a pin may not be anchored on one. An agent writing this table from memory
/// would produce something *mostly* right, which is worse than something obviously wrong - the same trap the
/// solar work fell into when its first oracle turned out to disagree with the US Naval Observatory.
///
/// A **closed** enum on purpose. The plan makes an unmapped code a build failure - *"every GraphHopper sign
/// code maps; unknown fails build"* - and that is only true if adding a case forces every `switch` over this
/// type to be updated. An `Int` passed through to the UI would let a code nobody mapped arrive at a junction as
/// silence, which is the failure this type exists to prevent.
public enum GuidanceSign: Int, CaseIterable, Sendable {
    // Negative: left-hand and unknown manoeuvres.
    case unknown = -99
    case uTurnUnknown = -98
    case uTurnLeft = -8
    case keepLeft = -7
    /// GraphHopper marks this one `// for future use`; it is declared but not currently emitted.
    case leaveRoundabout = -6
    case turnSharpLeft = -3
    case turnLeft = -2
    case turnSlightLeft = -1

    case continueOnStreet = 0

    // Positive: right-hand manoeuvres and route events.
    case turnSlightRight = 1
    case turnRight = 2
    case turnSharpRight = 3
    case finish = 4
    case reachedVia = 5
    case useRoundabout = 6
    case keepRight = 7
    case uTurnRight = 8
    case ferry = 9

    // Public-transit legs. Declared by GraphHopper, never emitted by a car profile, and deliberately present
    // here so that receiving one is a *recognised* condition rather than an unknown integer. See
    // `GuidanceManeuver.notApplicableToDriving`.
    case ptStartTrip = 101
    case ptTransfer = 102
    case ptEndTrip = 103

    /// GraphHopper's `IGNORE`, declared as `Integer.MIN_VALUE`.
    ///
    /// Swift requires an enum raw value to be a literal, so this cannot be written as `Int(Int32.min)` the way
    /// the upstream declaration reads. A ten-digit literal is exactly the kind of number a typo hides in, so
    /// the test suite asserts `ignore.rawValue == Int(Int32.min)` rather than trusting the digits here. Note
    /// Java's `int` is 32-bit: on a 64-bit platform `Int.min` would be a completely different number.
    case ignore = -2_147_483_648
}

extension GuidanceSign {
    /// The upstream release these values were read from. A constant, not a comment, so a check can assert it.
    public static let sourceRelease = "11.0"

    /// The file within that release.
    public static let sourcePath = "web-api/src/main/java/com/graphhopper/util/Instruction.java"

    /// The commit the tag `11.0` resolves to, and the git blob id of that file at that commit. Recorded so the
    /// table can be re-derived from the exact bytes it was read from rather than from a moving branch.
    public static let sourceCommit = "69e50f6e2cfaf0a8e69752df9953ee5f1ac276a4"
    public static let sourceBlob = "1638c71bfd6537d9a57ad0f24fec334e2122eaab"

    /// `services/routing/` does not exist in this repository yet, so there is no pinned GraphHopper image to
    /// check this table against. When that task lands, the pinned version must equal `sourceRelease` - and if
    /// it does not, this table has to be re-derived rather than assumed still correct.
    ///
    /// This property exists so that assertion has an identifier to anchor on instead of prose.
    public static let requiresRoutingServiceVersion = sourceRelease
}
