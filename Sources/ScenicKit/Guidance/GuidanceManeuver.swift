import Foundation

/// What the driver is being asked to do, in this product's own vocabulary.
///
/// **Deliberately not Ferrostar's type, and not GraphHopper's integer.** The root package is Linux-only and
/// `NavAdapter` is the sole importer of Ferrostar (CLAUDE.md), so the translation has to land on a type this
/// package owns. That is not merely a layering rule: it is what lets the mapping be tested on Linux, in
/// milliseconds, without a router or a navigation SDK anywhere near it.
///
/// Every case here is something a *driver* does. `GuidanceSign` is what the router *said*.
public enum GuidanceManeuver: Equatable, Sendable {
    /// Keep going. The road may change name; the driver does not act.
    case continueStraight

    /// Turn, with which way and how hard kept as separate axes so the adapter and the voice line can each use
    /// the part they need without re-parsing a fused name like `turnSharpLeft`.
    case turn(side: GuidanceSide, sharpness: GuidanceSharpness)

    /// Bear off at a fork without a junction turn.
    case keep(side: GuidanceSide)

    /// Reverse direction. `side` is `nil` when the router said `U_TURN_UNKNOWN` - it knows a U-turn is required
    /// but not which way it will be taken, and inventing a side would put a wrong word in a driver's ear.
    case uTurn(side: GuidanceSide?)

    /// Enter a roundabout. The exit number arrives on the instruction, not the sign.
    case enterRoundabout

    /// Leave a roundabout. GraphHopper declares this sign `for future use` and does not currently emit it;
    /// it is mapped anyway, because the day it starts being emitted must not be the day a driver hears nothing.
    case exitRoundabout

    /// Board a ferry. Not a turn, and worth its own case: the guidance UI and the ETA both behave differently.
    case ferry

    /// An intermediate waypoint on the planned route - one of the pinned scenic waypoints, in this product.
    case reachedWaypoint

    /// The destination.
    case arrive

    /// The router explicitly said it does not know. Distinct from a code we failed to decode: this is
    /// GraphHopper's own `UNKNOWN`, and it is honest information rather than an error.
    case routerSaidUnknown

    /// A step the router marked as one to skip entirely (GraphHopper's `IGNORE`).
    case ignore

    /// A public-transit leg. Declared by GraphHopper, never produced by a car profile, and mapped explicitly so
    /// that receiving one is a recognised - and reportable - condition instead of an unknown integer.
    ///
    /// This is the case that keeps the enum honest: the alternative is quietly folding transit into
    /// `continueStraight`, which would tell a driver to carry straight on at a point where the router thought
    /// they were boarding a train.
    case notApplicableToDriving
}

/// Which way. Its own type so that a mapping cannot silently swap `left` for a truthy value.
public enum GuidanceSide: Equatable, Sendable {
    case left
    case right
}

/// How hard. Ordered from gentlest to sharpest, but **not** `Comparable` by derivation - nothing in this
/// product needs to compare two turns, and a synthesised ordering would be an invariant nobody chose.
public enum GuidanceSharpness: Equatable, Sendable {
    case slight
    case normal
    case sharp
}
